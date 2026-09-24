"""Adapter over the local MetricMind AI agent.

The AI agent lives in a directory literally named ``ai agent``.
This adapter loads the agent by file path while temporarily making
the agent directory importable so its internal modules can resolve.

The adapter calls the LLM-powered interpretation layer only.
Execution through Cube remains the responsibility of the backend
query service.
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

# The directory name is part of the existing repository structure.
AGENT_DIR_NAME = "ai agent"
AGENT_SCHEMA_FILENAME = "schema.py"
AGENT_FILENAME = "agent.py"

_SCHEMA_MODULE_NAME = "_metricmind_local_agent_schema"
_AGENT_MODULE_NAME = "_metricmind_local_agent"


def resolve_agent_dir() -> Path:
    """Return the absolute path to the ``ai agent`` directory."""

    return Path(__file__).resolve().parents[3] / AGENT_DIR_NAME


def _exec_module(
    module_name: str,
    path: Path,
) -> ModuleType:
    """Load a Python module from an explicit file path."""

    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if spec is None or spec.loader is None:
        raise AgentUnavailableError(
            f"Could not create an import spec for '{path.name}'."
        )

    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise

    return module


@contextmanager
def _temporary_module_aliases(
    aliases: Dict[str, ModuleType],
) -> Iterator[None]:
    """Temporarily publish modules under the names expected by the agent."""

    sentinel = object()

    previous = {
        name: sys.modules.get(name, sentinel)
        for name in aliases
    }

    sys.modules.update(aliases)

    try:
        yield

    finally:

        for name, original in previous.items():

            if original is sentinel:
                sys.modules.pop(name, None)

            else:
                sys.modules[name] = original


@lru_cache(maxsize=1)
def load_agent_module() -> ModuleType:
    """Load and cache the LLM-powered local agent."""

    agent_dir = resolve_agent_dir()

    agent_path = agent_dir / AGENT_FILENAME
    schema_path = agent_dir / AGENT_SCHEMA_FILENAME

    if not agent_path.is_file():

        raise AgentUnavailableError(
            f"AI agent module not found at "
            f"'{AGENT_DIR_NAME}/{AGENT_FILENAME}'."
        )

    if not schema_path.is_file():

        raise AgentUnavailableError(
            f"AI agent schema not found at "
            f"'{AGENT_DIR_NAME}/{AGENT_SCHEMA_FILENAME}'."
        )

    try:

        agent_schema = _exec_module(
            _SCHEMA_MODULE_NAME,
            schema_path,
        )

        # The AI agent's modules use plain imports such as:
        # from schema import ...
        #
        # Temporarily add the agent directory to sys.path so
        # query_builder, validator, semantic_client and llm_agent
        # can resolve normally when agent.py is loaded.

        agent_dir_string = str(agent_dir)

        previous_path = list(sys.path)

        if agent_dir_string not in sys.path:
            sys.path.insert(
                0,
                agent_dir_string,
            )

        try:

            with _temporary_module_aliases(
                {
                    "schema": agent_schema,
                }
            ):

                return _exec_module(
                    _AGENT_MODULE_NAME,
                    agent_path,
                )

        finally:

            sys.path[:] = previous_path

    except AgentUnavailableError:
        raise

    except Exception as exc:

        logger.exception(
            "Failed to import the local AI agent"
        )

        raise AgentUnavailableError(
            "The AI agent module could not be imported."
        ) from exc


class LocalAgentAdapter:
    """Wrapper around the LLM-powered local AI agent."""

    name = "local-llama-agent"

    @property
    def available(self) -> bool:
        """Return True when the agent can be loaded."""

        return self.availability_detail is None

    @property
    def availability_detail(self) -> Optional[str]:
        """Return a client-safe availability error, if any."""

        try:

            load_agent_module()

        except AgentUnavailableError as exc:

            return exc.message

        return None

    @property
    def declared_metrics(self) -> List[str]:
        """Return the governed metrics from the AI-agent schema."""

        try:

            module = load_agent_module()

            schema = sys.modules.get(
                _SCHEMA_MODULE_NAME
            )

            if schema is not None:

                return list(
                    getattr(
                        schema,
                        "METRICS",
                        [],
                    )
                )

            return list(
                getattr(
                    module,
                    "METRICS",
                    [],
                )
            )

        except AgentUnavailableError:

            return []

    @property
    def declared_dimensions(self) -> List[str]:
        """Return the governed dimensions from the AI-agent schema."""

        try:

            module = load_agent_module()

            schema = sys.modules.get(
                _SCHEMA_MODULE_NAME
            )

            if schema is not None:

                return list(
                    getattr(
                        schema,
                        "DIMENSIONS",
                        [],
                    )
                )

            return list(
                getattr(
                    module,
                    "DIMENSIONS",
                    [],
                )
            )

        except AgentUnavailableError:

            return []

    def interpret(
        self,
        question: str,
    ) -> Dict[str, object]:
        """Interpret a question using Llama without executing the query."""

        if not isinstance(
            question,
            str,
        ) or not question.strip():

            raise AgentError(
                "A non-empty question is required."
            )

        try:

            module = load_agent_module()

        except AgentUnavailableError:

            raise

        interpret_function = getattr(
            module,
            "_build_llm_query",
            None,
        )

        if interpret_function is None:

            raise AgentError(
                "The AI agent does not expose "
                "the LLM interpretation function."
            )

        try:

            result = interpret_function(
                question
            )

        except Exception as exc:

            logger.exception(
                "The LLM-powered AI agent failed "
                "to interpret the question"
            )

            raise AgentError(
                "The AI agent could not interpret the question."
            ) from exc

        if not isinstance(
            result,
            dict,
        ):

            raise AgentError(
                "The AI agent returned an unexpected payload."
            )

        # Preserve the agent's structured query exactly.
        return dict(result)


_AGENT_ADAPTER = LocalAgentAdapter()


def get_agent_adapter() -> LocalAgentAdapter:
    """Return the process-wide agent adapter."""

    return _AGENT_ADAPTER


__all__ = [
    "LocalAgentAdapter",
    "get_agent_adapter",
    "load_agent_module",
    "resolve_agent_dir",
    "AGENT_DIR_NAME",
]