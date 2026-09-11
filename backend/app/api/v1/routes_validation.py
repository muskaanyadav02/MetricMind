"""Validation endpoints.

These expose the repository's existing validators over HTTP, normalised into the
backend's single :class:`~app.schemas.validation.ValidationReport` shape. They are
deliberately honest about which checks ran: every report carries
``checks_applied`` and ``checks_skipped``, so a caller can never read "PASS" and
assume a check executed that in fact could not apply.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.errors import ValidationFailedError
from app.core.logging import get_logger
from app.schemas.validation import (
    ValidateDataRequest,
    ValidateDataResponse,
    ValidateQueryRequest,
    ValidateQueryResponse,
    ValidationReport,
)
from app.services.query_service import QueryService, get_query_service
from app.services.validation_service import ValidationService, get_validation_service

logger = get_logger(__name__)

router = APIRouter(tags=["validation"])


@router.post(
    "/validate/query",
    response_model=ValidateQueryResponse,
    summary="Validate a governed query payload",
    description=(
        "Runs the repository's MetricValidator against a governed query, rendered in the "
        "Cube.dev payload shape. Returns the normalised report plus the SQL the payload "
        "would compile to. The payload may only reference governed metrics and "
        "dimensions; unknown names are reported rather than executed."
    ),
)
def validate_query(
    request: ValidateQueryRequest,
    query_service: QueryService = Depends(get_query_service),
    validation: ValidationService = Depends(get_validation_service),
) -> ValidateQueryResponse:
    report = validation.validate_governed_query(request.payload)

    compiled_sql = None
    parameters = []
    if report.is_valid:
        try:
            plan = query_service.compile(request.payload)
            compiled_sql = plan.sql
            parameters = list(plan.parameters)
        except ValidationFailedError as exc:
            # The payload passed the JSON schema but names something the governed
            # registry does not know about.
            report = report.model_copy(
                update={
                    "is_valid": False,
                    "status": "FAIL",
                    "errors": [*report.errors, exc.message],
                }
            )

    return ValidateQueryResponse(
        report=report,
        compiled_sql_preview=compiled_sql,
        compiled_parameters=parameters,
    )


@router.post(
    "/validate/data",
    response_model=ValidateDataResponse,
    summary="Validate a set of result rows",
    description=(
        "Runs the repository's DataValidator against rows supplied in the body. "
        "The audit covers the supplied rows only. Optional 'members' renames row keys to "
        "Cube-style member names before auditing, which is required for DataValidator's "
        "discount and negative-sales heuristics to match at all."
    ),
)
def validate_data(
    request: ValidateDataRequest,
    validation: ValidationService = Depends(get_validation_service),
) -> ValidateDataResponse:
    if not request.data:
        return ValidateDataResponse(
            report=ValidationReport(
                is_valid=False,
                status="FAIL",
                errors=["No rows were supplied for validation."],
                checks_applied=[],
                checks_skipped=[],
            )
        )

    columns = list(request.data[0].keys())
    report = validation.validate_rows(
        request.data, columns=columns, members=request.members
    )
    return ValidateDataResponse(report=report)


__all__ = ["router"]
