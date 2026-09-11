"""Health and configuration endpoints.

The health response is designed to be safe to expose: it reports *whether*
things are configured and *which* environment settings are missing, but never
their values, and never an account name, user or connection string.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.adapters.warehouse import WarehouseAdapter, get_warehouse
from app.config import Settings, get_settings
from app.schemas.common import HealthResponse, WarehouseSummary
from app.services.agent_service import AgentService, get_agent_service
from app.services.metric_service import GovernedRegistry, get_metric_service

router = APIRouter(tags=["health"])


def _build_health_response(
    agent: AgentService,
    warehouse: WarehouseAdapter,
    registry: GovernedRegistry,
    settings: Settings,
) -> HealthResponse:
    agent_available = agent.available
    warehouse_ready = warehouse.is_configured()

    # "ok" means every dependency is usable. Missing Snowflake credentials make
    # this "degraded" rather than an error: the app is expected to run and be
    # testable without a warehouse.
    status = "ok" if (agent_available and warehouse_ready) else "degraded"

    return HealthResponse(
        status=status,
        service=settings.app_name,
        version=settings.app_version,
        agent_available=agent_available,
        agent_detail=agent.availability_detail,
        agent_declared_metrics=agent.declared_metrics,
        agent_declared_dimensions=agent.declared_dimensions,
        warehouse=WarehouseSummary(
            backend=warehouse.name,
            database=settings.snowflake_database,
            schema_name=settings.snowflake_schema,
            configured=warehouse_ready,
            missing_settings=warehouse.missing_settings(),
        ),
        governed_metric_count=len(registry.metrics),
        governed_dimension_count=len(registry.dimensions),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and configuration summary",
    description=(
        "Reports service status, whether the AI agent module loaded, whether the "
        "warehouse is configured, and the size of the governed registry. "
        "Contains no credentials. Always returns 200; check the 'status' field."
    ),
)
def health(
    agent: AgentService = Depends(get_agent_service),
    warehouse: WarehouseAdapter = Depends(get_warehouse),
    registry: GovernedRegistry = Depends(get_metric_service),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    return _build_health_response(agent, warehouse, registry, settings)


def top_level_health(
    agent: AgentService = Depends(get_agent_service),
    warehouse: WarehouseAdapter = Depends(get_warehouse),
    registry: GovernedRegistry = Depends(get_metric_service),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Same payload as ``/api/v1/health``, mounted at ``/health`` for local dev."""
    return _build_health_response(agent, warehouse, registry, settings)


__all__ = ["router", "top_level_health"]
