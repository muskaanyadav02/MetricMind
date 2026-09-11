"""Chat schemas.

``ChatQueryRequest`` sets ``extra="forbid"``. That is the mechanism which makes
it impossible to smuggle a ``sql`` (or any other unexpected) field through the
public API: an unknown key is rejected with a 422 before any handler runs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.semantic import GovernedQuery, QueryFilter
from app.schemas.validation import ValidationReport

MAX_QUESTION_LENGTH = 500


class ChatQueryRequest(BaseModel):
    """Body for POST /chat/query."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=3,
        max_length=MAX_QUESTION_LENGTH,
        description="A natural-language business question.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Reserved for conversation context. Not used in v1.",
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum rows to return. Capped by the server's max_result_rows.",
    )


class AmbiguityInfo(BaseModel):
    """Normalised ambiguity report from the AI agent."""

    ambiguous: bool = False
    reason: Optional[str] = None
    possible_metrics: List[str] = Field(default_factory=list)


class SupportingEvidence(BaseModel):
    """Everything the frontend needs for the planned Evidence/Confidence panel."""

    question: str
    interpreted_metric: Optional[str] = Field(
        default=None, description="Metric as named by the AI agent, e.g. 'Sales'."
    )
    governed_metric: Optional[str] = Field(
        default=None, description="Governed metric name it resolved to, e.g. 'Revenue'."
    )
    metric_formula: Optional[str] = Field(default=None, description="Governed formula.")
    interpreted_dimension: Optional[str] = Field(default=None)
    dimensions: List[str] = Field(default_factory=list)
    filters: List[QueryFilter] = Field(default_factory=list)
    governed_query: Optional[GovernedQuery] = Field(
        default=None, description="The governed query actually executed (or that would be)."
    )
    source_model: Optional[str] = Field(
        default=None, description="Qualified dbt mart the data came from."
    )
    row_count: int = 0
    validation: ValidationReport
    agent_output: Dict[str, Any] = Field(
        default_factory=dict,
        description="The AI agent's output, preserved verbatim rather than reshaped.",
    )
    translation_notes: List[str] = Field(
        default_factory=list,
        description="Explicit record of every interpretation made while translating agent output.",
    )
    answer_generation: str = Field(
        default="deterministic",
        description="How the answer text was produced. 'deterministic' means no LLM was called.",
    )


class ChatQueryResponse(BaseModel):
    """The structured chat response."""

    status: Literal["answered", "ambiguous", "unsupported"]
    answer: Optional[str] = Field(
        default=None, description="Answer text. Deterministic when no LLM is configured."
    )
    message: Optional[str] = Field(
        default=None, description="Why the question could not be answered, when status is not 'answered'."
    )
    ambiguity: AmbiguityInfo = Field(default_factory=AmbiguityInfo)
    evidence: SupportingEvidence
    data: List[Dict[str, Any]] = Field(default_factory=list)


__all__ = [
    "MAX_QUESTION_LENGTH",
    "ChatQueryRequest",
    "AmbiguityInfo",
    "SupportingEvidence",
    "ChatQueryResponse",
]
