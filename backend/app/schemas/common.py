"""Shared response models: the error envelope and health payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """A single field-level or contextual detail attached to an error."""

    model_config = ConfigDict(extra="allow")

    field: Optional[str] = Field(default=None, description="Field or component the detail relates to.")
    message: str = Field(description="Human-readable description.")
    type: Optional[str] = Field(default=None, description="Machine-readable detail kind.")


class ErrorBody(BaseModel):
    """The body of an error response."""

    code: str = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Client-safe message. Never contains credentials.")
    details: List[ErrorDetail] = Field(default_factory=list)
    correlation_id: Optional[str] = Field(
        default=None, description="Server log correlation id, for support requests."
    )


class ErrorResponse(BaseModel):
    """The single error envelope used by every endpoint."""

    error: ErrorBody


class WarehouseSummary(BaseModel):
    """Non-secret description of the configured warehouse."""

    backend: str
    database: str
    schema_name: str = Field(serialization_alias="schema", alias="schema")
    configured: bool
    missing_settings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class HealthResponse(BaseModel):
    """Health and configuration summary. Contains no secrets."""

    status: str = Field(description="'ok' when dependencies are ready, otherwise 'degraded'.")
    service: str
    version: str
    agent_available: bool
    agent_detail: Optional[str] = None
    agent_declared_metrics: List[str] = Field(default_factory=list)
    agent_declared_dimensions: List[str] = Field(default_factory=list)
    warehouse: WarehouseSummary
    governed_metric_count: int
    governed_dimension_count: int


class CatalogCount(BaseModel):
    """Row count for a catalogue response."""

    count: int
    extra: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ErrorDetail",
    "ErrorBody",
    "ErrorResponse",
    "WarehouseSummary",
    "HealthResponse",
    "CatalogCount",
]
