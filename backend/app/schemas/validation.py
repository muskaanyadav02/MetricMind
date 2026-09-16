"""Validation schemas.

The existing ``MetricValidator`` and ``DataValidator`` return three mutually
incompatible shapes (a ``(bool, str)`` tuple, a five-key dict, and a two-key
dict). :class:`ValidationReport` is the single normalised shape the backend
exposes, and it records which checks actually ran so a caller is never told a
check passed when it was in fact skipped.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.semantic import GovernedQuery

ValidationStatus = Literal["PASS", "FLAGGED", "FAIL", "SKIPPED", "ERROR"]


class SchemaValidationResult(BaseModel):
    """Normalised result of ``MetricValidator.validate_agent_query``."""

    is_valid: bool
    message: str
    validator: str = "MetricValidator.validate_agent_query"


class DataValidationResult(BaseModel):
    """Normalised result of ``DataValidator.validate_cube_output``."""

    status: str = Field(description="PASS, FLAGGED or FAIL, as reported by DataValidator.")
    row_count: int = 0
    null_count: int = 0
    invalid_discount_detected: bool = False
    negative_sales_detected: bool = False
    reason: Optional[str] = Field(default=None, description="Populated for the FAIL shape.")
    raw: Dict[str, Any] = Field(default_factory=dict, description="Unmodified validator output.")
    validator: str = "DataValidator.validate_cube_output"


class SkippedCheck(BaseModel):
    """A check that did not run, and why."""

    check: str
    reason: str


class ValidationReport(BaseModel):
    """The backend's single validation shape."""

    is_valid: bool
    status: ValidationStatus
    schema_validation: Optional[SchemaValidationResult] = None
    data_validation: Optional[DataValidationResult] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks_applied: List[str] = Field(default_factory=list)
    checks_skipped: List[SkippedCheck] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ValidateQueryRequest(BaseModel):
    """Body for POST /validate/query."""

    model_config = ConfigDict(extra="forbid")

    payload: GovernedQuery


class ValidateQueryResponse(BaseModel):
    """Response for POST /validate/query."""

    report: ValidationReport
    compiled_sql_preview: Optional[str] = Field(
        default=None,
        description="The governed SQL the payload compiles to. Identifiers only; no client input.",
    )
    compiled_parameters: List[Any] = Field(default_factory=list)


class ValidateDataRequest(BaseModel):
    """Body for POST /validate/data.

    Note there is deliberately no field that accepts SQL.
    """

    model_config = ConfigDict(extra="forbid")

    data: List[Dict[str, Any]] = Field(description="Rows to audit, as returned by a query.")
    members: Optional[List[str]] = Field(
        default=None,
        description="Optional member names to use as column keys when auditing the rows.",
    )


class ValidateDataResponse(BaseModel):
    """Response for POST /validate/data."""

    report: ValidationReport


__all__ = [
    "ValidationStatus",
    "SchemaValidationResult",
    "DataValidationResult",
    "SkippedCheck",
    "ValidationReport",
    "ValidateQueryRequest",
    "ValidateQueryResponse",
    "ValidateDataRequest",
    "ValidateDataResponse",
]
