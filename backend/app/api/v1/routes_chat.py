"""Chat endpoint: the end-to-end governed question flow.

    question
      -> agent adapter                     (adapters/agent_loader.py)
      -> governed semantic query           (services/query_service.translate_agent_output)
      -> validation                        (services/validation_service)
      -> warehouse query                   (adapters/warehouse.py)
      -> result validation                 (services/validation_service)
      -> structured response

Two behaviours are worth calling out:

* When the agent cannot identify a governed metric, or flags the question as
  ambiguous, the endpoint returns ``status: "ambiguous" | "unsupported"`` with an
  explanation. It never falls back to generating SQL from the free-form question.
* Answer prose is produced by :func:`~app.services.query_service.summarize_result`,
  which is template-based. The current agent has no language model, so the
  response records ``evidence.answer_generation = "deterministic"`` instead of
  presenting generated text as an AI answer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.core.errors import ValidationFailedError
from app.core.logging import get_logger
from app.schemas.chat import (
    AmbiguityInfo,
    ChatQueryRequest,
    ChatQueryResponse,
    SupportingEvidence,
)
from app.schemas.semantic import GovernedQuery
from app.schemas.validation import ValidationReport
from app.services.agent_service import AgentInterpretation, AgentService, get_agent_service
from app.services.query_service import (
    QueryService,
    get_query_service,
    summarize_result,
    translate_agent_output,
)
from app.services.validation_service import ValidationService, get_validation_service

logger = get_logger(__name__)

router = APIRouter(tags=["chat"])


def _build_evidence(
    interpretation: AgentInterpretation,
    *,
    governed_metric: Optional[str] = None,
    metric_formula: Optional[str] = None,
    dimensions: Optional[List[str]] = None,
    governed_query: Optional[GovernedQuery] = None,
    source_model: Optional[str] = None,
    row_count: int = 0,
    validation: ValidationReport,
    translation_notes: List[str],
) -> SupportingEvidence:
    return SupportingEvidence(
        question=interpretation.question,
        interpreted_metric=interpretation.metric,
        governed_metric=governed_metric,
        metric_formula=metric_formula,
        interpreted_dimension=interpretation.dimension,
        dimensions=list(dimensions or []),
        filters=list(governed_query.filters) if governed_query else [],
        governed_query=governed_query,
        source_model=source_model,
        row_count=row_count,
        validation=validation,
        agent_output=interpretation.raw,
        translation_notes=translation_notes,
        answer_generation="deterministic",
    )


def _skipped_validation(reason: str) -> ValidationReport:
    """A report for the paths where no query was executed."""
    return ValidationReport(
        is_valid=False,
        status="SKIPPED",
        notes=[reason],
    )


@router.post(
    "/chat/query",
    response_model=ChatQueryResponse,
    summary="Ask a governed business question",
    description=(
        "Interprets the question with the local AI agent, translates the result into a "
        "governed query built only from the governed metric and dimension registry, runs "
        "it against the warehouse, and returns the data plus the evidence needed to audit "
        "the answer. Unknown or ambiguous questions return status 'unsupported' or "
        "'ambiguous' rather than a guessed query."
    ),
    responses={
        422: {"description": "The question could not be supported, or the request payload was invalid."},
        502: {"description": "The warehouse returned an error."},
        503: {"description": "The warehouse is not configured, or the agent module is unavailable."},
        504: {"description": "The warehouse query timed out."},
    },
)
def chat_query(
    request: ChatQueryRequest,
    agent: AgentService = Depends(get_agent_service),
    query_service: QueryService = Depends(get_query_service),
    validation: ValidationService = Depends(get_validation_service),
    settings: Settings = Depends(get_settings),
) -> ChatQueryResponse:
    interpretation = agent.interpret(request.question)
    registry = query_service.registry

    requested_limit = request.limit or settings.default_result_rows

    outcome = translate_agent_output(
        interpretation,
        registry,
        default_limit=requested_limit,
        max_limit=settings.max_result_rows,
    )

    # -- Not executable: report why, with full evidence of what was understood.
    if outcome.status != "ok" or outcome.governed_query is None:
        return ChatQueryResponse(
            status="ambiguous" if outcome.status == "ambiguous" else "unsupported",
            answer=None,
            message=outcome.message,
            ambiguity=outcome.ambiguity,
            evidence=_build_evidence(
                interpretation,
                validation=_skipped_validation(
                    "No governed query was executed, so no data validation was performed."
                ),
                translation_notes=outcome.notes,
            ),
            data=[],
        )

    governed_query = outcome.governed_query
    metric_name = governed_query.measures[0] if governed_query.measures else None
    metric_definition = registry.find_metric(metric_name)

    # -- Pre-execution validation of the governed payload.
    schema_report = validation.validate_governed_query(governed_query)
    if not schema_report.is_valid:
        raise ValidationFailedError(
            "The governed query failed schema validation and was not executed.",
            details=[
                {"field": "measures", "message": schema_report.errors[0]}
                if schema_report.errors
                else {"field": "measures", "message": "Governed payload is invalid."}
            ],
        )

    # -- Execution. Raises ConfigurationError (503) when unconfigured, and
    #    WarehouseTimeoutError (504) / WarehouseError (502) on failure.
    execution = query_service.execute(governed_query)

    # -- Post-execution validation of the returned rows.
    data_report = validation.validate_rows(
        execution.result.rows, columns=execution.result.columns
    )
    combined_report = validation.combine(schema_report, data_report)

    rows: List[Dict[str, Any]] = execution.result.rows
    answer = summarize_result(metric_name, rows, governed_query.dimensions)

    if combined_report.status == "ERROR":
        logger.warning("Validation reported an error for question: %s", interpretation.question)

    return ChatQueryResponse(
        status="answered",
        answer=answer,
        message=None,
        ambiguity=outcome.ambiguity,
        evidence=_build_evidence(
            interpretation,
            governed_metric=metric_name,
            metric_formula=metric_definition.formula if metric_definition else None,
            dimensions=governed_query.dimensions,
            governed_query=governed_query,
            source_model=execution.result.source_model or execution.plan.source_model,
            row_count=execution.result.row_count,
            validation=combined_report,
            translation_notes=outcome.notes,
        ),
        data=rows,
    )


__all__ = ["router"]
