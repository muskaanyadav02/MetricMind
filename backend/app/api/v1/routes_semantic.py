"""Governed metric and dimension catalogue endpoints.

These make the semantic layer inspectable. They are what the planned frontend
"Evidence and Confidence Panel" reads to show which metrics and dimensions exist,
and they expose the governance gaps found in Stage 1 rather than hiding them.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.common import ErrorResponse
from app.schemas.semantic import DimensionCatalogResponse, MetricCatalogResponse
from app.services.metric_service import (
    DIMENSION_GOVERNANCE_NOTES,
    METRIC_DICTIONARY_DOC,
    METRIC_GOVERNANCE_NOTES,
    GovernedRegistry,
    get_metric_service,
)

router = APIRouter(tags=["semantic"])


@router.get(
    "/metrics",
    response_model=MetricCatalogResponse,
    summary="List the governed business metrics",
    description=(
        "Returns the eight governed metrics defined in docs/metric_dictionary.md, "
        "with the exact formula each is computed from. Formulas are quoted from that "
        "document; none are invented here."
    ),
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal error, rendered in the standard error envelope (internal_error).",
        },
    },
)
def list_metrics(
    registry: GovernedRegistry = Depends(get_metric_service),
) -> MetricCatalogResponse:
    metrics = registry.metrics
    return MetricCatalogResponse(
        metrics=metrics,
        count=len(metrics),
        source_document=METRIC_DICTIONARY_DOC,
        notes=list(METRIC_GOVERNANCE_NOTES),
    )


@router.get(
    "/dimensions",
    response_model=DimensionCatalogResponse,
    summary="List the governed dimensions",
    description=(
        "Returns the dimensions the backend will accept. Geographic and time dimensions "
        "are governed by docs/metric_dictionary.md; categorical dimensions come from the "
        "physical dbt marts and are returned with governed=false."
    ),
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Unexpected internal error, rendered in the standard error envelope (internal_error).",
        },
    },
)
def list_dimensions(
    registry: GovernedRegistry = Depends(get_metric_service),
) -> DimensionCatalogResponse:
    dimensions = registry.dimensions
    return DimensionCatalogResponse(
        dimensions=dimensions,
        count=len(dimensions),
        governed_count=registry.governed_dimension_count,
        notes=list(DIMENSION_GOVERNANCE_NOTES),
    )


__all__ = ["router"]
