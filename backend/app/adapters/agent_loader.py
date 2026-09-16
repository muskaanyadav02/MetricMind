"""Adapter over the existing local AI agent.

Why this is written the way it is
---------------------------------
The AI agent lives in a directory literally named ``ai agent`` (with a space) and
is a set of plain modules rather than an installable package:

* ``ai agent/query_builder.py`` starts with ``from schema import METRICS, DIMENSIONS``,
  so it only imports when ``ai agent/`` is importable.
* A directory name containing a space is not a valid Python identifier, so
  ``import ai agent`` is a syntax error and ``importlib.import_module`` cannot
  address it.

The instruction for this stage was explicit: do not rename or move that
directory. So this adapter loads the modules by *file path* with
``importlib.util.spec_from_file_location`` and temporarily publishes the agent's
own ``schema`` module under the name ``schema`` while ``query_builder`` is
executing, restoring whatever was there before.

Nothing about the agent's output is reshaped here. :meth:`LocalAgentAdapter.interpret`
returns the agent's dictionary exactly as produced, and the translation into a
governed query happens explicitly in ``services/query_service.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterator, List, Optional

from app.core.errors import AgentError, AgentUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Directory name is taken verbatim from the repository and must not be changed.
AGENT_DIR_NAME = "ai agent"
AGENT_SCHEMA_FILENAME = "schema.py"
AGENT_QUERY_BUILDER_FILENAME = "query_builder.py"

# Unique module names, to avoid colliding with any installed package.
_SCHEMA_MODULE_NAME = "_metricmind_local_agent_schema"
_QUERY_BUILDER_MODULE_NAME = "_metricmind_local_agent_query_builder"


def resolve_agent_dir() -> Path:
    """Absolute path to the ``ai agent`` directory.

    ``__file__`` is ``<repo>/backend/app/adapters/agent_loader.py``, so
    ``parents[3]`` is the repository root.
    """
    return Path(__file__).resolve().parents[3] / AGENT_DIR_NAME


def _exec_module(module_name: str, path: Path) -> ModuleType:
    """Load a module from an explicit file path."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AgentUnavailableError(f"Could not create an import spec for '{path.name}'.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


@contextmanager
def _temporary_module_aliases(aliases: Dict[str, ModuleType]) -> Iterator[None]:
    """Publish modules under alternate names, restoring prior state afterwards."""
    sentinel = object()
    previous = {name: sys.modules.get(name, sentinel) for name in aliases}
    sys.modules.update(aliases)
    try:
        yield
    finally:
        for name, original in previous.items():
            if original is sentinel:
                sys.modules.pop(name, None)
            else:  # pragma: no cover - only hit if something else claimed the name
                sys.modules[name] = original


@lru_cache(maxsize=1)
def load_query_builder_module() -> ModuleType:
    """Load and cache the agent's ``query_builder`` module.

    Raises :class:`AgentUnavailableError` when the module is absent or fails to
    import. The exception is not cached, so a fixed checkout recovers without a
    process restart.
    """
    agent_dir = resolve_agent_dir()
    query_builder_path = agent_dir / AGENT_QUERY_BUILDER_FILENAME
    schema_path = agent_dir / AGENT_SCHEMA_FILENAME

    if not query_builder_path.is_file():
        raise AgentUnavailableError(
            f"AI agent module not found at '{AGENT_DIR_NAME}/{AGENT_QUERY_BUILDER_FILENAME}'."
        )
    if not schema_path.is_file():
        raise AgentUnavailableError(
            f"AI agent module not found at '{AGENT_DIR_NAME}/{AGENT_SCHEMA_FILENAME}'."
        )

    try:
        agent_schema = _exec_module(_SCHEMA_MODULE_NAME, schema_path)
        with _temporary_module_aliases({"schema": agent_schema}):
            return _exec_module(_QUERY_BUILDER_MODULE_NAME, query_builder_path)
    except AgentUnavailableError:
        raise
    except Exception as exc:  # pragma: no cover - depends on the agent's state
        logger.exception("Failed to import the local AI agent")
        raise AgentUnavailableError("The AI agent module could not be imported.") from exc


class LocalAgentAdapter:
    """Thin, honest wrapper around the current rule-based agent.

    The agent is *not* an LLM at this commit - ``query_builder.build_query`` is
    deterministic keyword matching. This adapter therefore does not pretend an
    LLM exists; it exposes exactly the agent's own behaviour.
    """

    name = "local-rule-based-agent"

    @property
    def available(self) -> bool:
        """True when the agent module can be loaded."""
        return self.availability_detail is None

    @property
    def availability_detail(self) -> Optional[str]:
        """``None`` when available, otherwise a client-safe reason."""
        try:
            load_query_builder_module()
        except AgentUnavailableError as exc:
            return exc.message
        return None

    @property
    def declared_metrics(self) -> List[str]:
        """Metrics the agent will recognise, quoted from ``ai agent/schema.py``."""
        try:
            module = load_query_builder_module()
            schema = sys.modules.get(_SCHEMA_MODULE_NAME)
            if schema is not None:
                return list(getattr(schema, "METRICS", []))
            return list(getattr(module, "METRICS", []))
        except AgentUnavailableError:
            return []

    @property
    def declared_dimensions(self) -> List[str]:
        """Dimensions the agent will recognise, quoted from ``ai agent/schema.py``."""
        try:
            module = load_query_builder_module()
            schema = sys.modules.get(_SCHEMA_MODULE_NAME)
            if schema is not None:
                return list(getattr(schema, "DIMENSIONS", []))
            return list(getattr(module, "DIMENSIONS", []))
        except AgentUnavailableError:
            return []

    def interpret(self, question: str) -> Dict[str, object]:
        """Run the agent and return its output unchanged.

        The returned dict has the agent's own keys: ``question``, ``metric``,
        ``dimension``, ``filters``, ``operation`` and ``ambiguity``.
        """
        if not isinstance(question, str) or not question.strip():
            raise AgentError("A non-empty question is required.")

        try:
            module = load_query_builder_module()
        except AgentUnavailableError:
            raise

        build_query = getattr(module, "build_query", None)
        if build_query is None:
            raise AgentError("The AI agent does not expose a build_query function.")

        try:
            result = build_query(question)
        except Exception as exc:  # pragma: no cover - depends on the agent's state
            logger.exception("The AI agent failed to interpret the question")
            raise AgentError("The AI agent could not interpret the question.") from exc

        if not isinstance(result, dict):
            raise AgentError("The AI agent returned an unexpected payload.")

        # Preserve the agent's contract exactly; add nothing, drop nothing.
        return dict(result)


_AGENT_ADAPTER = LocalAgentAdapter()


def get_agent_adapter() -> LocalAgentAdapter:
    """FastAPI dependency returning the process-wide agent adapter."""
    return _AGENT_ADAPTER


__all__ = [
    "LocalAgentAdapter",
    "get_agent_adapter",
    "load_query_builder_module",
    "resolve_agent_dir",
    "AGENT_DIR_NAME",
]
