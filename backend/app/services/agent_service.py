"""Agent service: runs the local AI agent and normalises its output.

The agent's dictionary is preserved verbatim on
:attr:`AgentInterpretation.raw` and surfaced to clients as
``evidence.agent_output``.

This service only reads from the agent's payload. It does not rewrite
or invent values that the agent did not produce.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.adapters.agent_loader import LocalAgentAdapter, get_agent_adapter
from app.core.logging import get_logger
from app.schemas.chat import AmbiguityInfo

logger = get_logger(__name__)


class AgentInterpretation(BaseModel):
    """Normalised view of one agent invocation."""

    question: str

    raw: Dict[str, Any] = Field(
        default_factory=dict,
        description="The agent's output dictionary, unmodified.",
    )

    metric: Optional[str] = Field(
        default=None,
        description="Metric name as the agent named it.",
    )

    dimension: Optional[str] = Field(
        default=None,
        description="Dimension name as the agent named it.",
    )

    operation: Optional[str] = Field(
        default=None,
        description="Operation as the agent named it.",
    )

    year: Optional[int] = Field(
        default=None,
        description="Year filter extracted by the agent.",
    )

    market: Optional[str] = Field(
        default=None,
        description="Market filter extracted by the agent.",
    )

    ambiguity: AmbiguityInfo = Field(
        default_factory=AmbiguityInfo,
    )


class AgentService:
    """Service wrapper around the AI agent adapter."""

    def __init__(
        self,
        adapter: Optional[LocalAgentAdapter] = None,
    ) -> None:
        self._adapter = adapter or get_agent_adapter()

    @property
    def adapter(self) -> LocalAgentAdapter:
        return self._adapter

    @property
    def available(self) -> bool:
        return self._adapter.available

    @property
    def availability_detail(self) -> Optional[str]:
        return self._adapter.availability_detail

    @property
    def declared_metrics(self) -> List[str]:
        return self._adapter.declared_metrics

    @property
    def declared_dimensions(self) -> List[str]:
        return self._adapter.declared_dimensions

    def interpret(self, question: str) -> AgentInterpretation:
        """Run the agent and normalise its output.

        Raises:
            AgentError or AgentUnavailableError on failure.
        """

        raw = self._adapter.interpret(question)

        # Extract ambiguity information.
        raw_ambiguity = raw.get("ambiguity")

        if isinstance(raw_ambiguity, dict):
            ambiguity = AmbiguityInfo(
                ambiguous=bool(
                    raw_ambiguity.get("ambiguous", False)
                ),
                reason=raw_ambiguity.get("reason"),
                possible_metrics=list(
                    raw_ambiguity.get("possible_metrics") or []
                ),
            )
        else:
            ambiguity = AmbiguityInfo()

        # Extract filters produced by the agent.
        raw_filters = raw.get("filters")

        year: Optional[int] = None
        market: Optional[str] = None

        if isinstance(raw_filters, dict):

            # Year filter.
            candidate_year = raw_filters.get("Year")

            if (
                isinstance(candidate_year, int)
                and not isinstance(candidate_year, bool)
            ):
                year = candidate_year

            # Market filter.
            candidate_market = raw_filters.get("Market")

            if (
                isinstance(candidate_market, str)
                and candidate_market.strip()
            ):
                market = candidate_market.strip()

        # Extract core semantic fields.
        metric = raw.get("metric")
        dimension = raw.get("dimension")
        operation = raw.get("operation")

        return AgentInterpretation(
            question=question,
            raw=raw,
            metric=metric if isinstance(metric, str) else None,
            dimension=(
                dimension
                if isinstance(dimension, str)
                else None
            ),
            operation=(
                operation
                if isinstance(operation, str)
                else None
            ),
            year=year,
            market=market,
            ambiguity=ambiguity,
        )


def get_agent_service() -> AgentService:
    """FastAPI dependency returning the agent service."""

    return AgentService()


__all__ = [
    "AgentInterpretation",
    "AgentService",
    "get_agent_service",
]