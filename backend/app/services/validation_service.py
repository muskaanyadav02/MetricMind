"""Validation service: normalises the existing validators into one report.

What this deliberately does NOT do
----------------------------------
It does not call ``ai agent/validator.py::validate_agent_output``. Stage 1
inspection found that function always reports success:

* it calls ``MetricValidator.validate_agent_query``, which returns a
  ``(bool, str)`` **tuple**, then guards the result with
  ``isinstance(result, dict)`` - so the tuple is discarded and the schema check
  silently evaluates to ``True``;
* it probes ``DataValidator`` for ``validate_dataframe`` / ``validate``, neither
  of which exists, and falls through to a hardcoded ``{"is_valid": True}``.

Wrapping that would mean returning "validation passed" without validating
anything. Instead this service calls the validators' *actual* public methods and
normalises their three different return shapes.

What it does about the heuristics it cannot use
-----------------------------------------------
``DataValidator.validate_cube_output`` only inspects columns whose lowercased
name contains ``discount`` (bounds 0..1) or ``sales`` (non-negative). Governed
measure columns are named ``Revenue``, ``Profit``, ``Profit Margin``, ``Orders``,
``Customers``, ``Quantity Sold``, ``Shipping Cost`` and ``Average Order Value`` -
none of which match. Rather than renaming columns to make the checks fire, the
report lists those two checks under ``checks_skipped`` with the reason, so no
caller can be told they ran when they did not. Callers who genuinely want the
heuristics exercised can pass ``members`` to map row keys onto Cube-style member
names (e.g. ``Sales.Revenue``), which is the input shape the validator documents.
"""

from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Sequence

from app.core.logging import get_logger
from app.schemas.semantic import GovernedQuery
from app.schemas.validation import (
    DataValidationResult,
    SchemaValidationResult,
    SkippedCheck,
    ValidationReport,
)
from app.services.query_service import build_cube_payload

logger = get_logger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATION_DIR = _REPO_ROOT / "analytics_validation" / "validation"

_METRIC_VALIDATION_FILE = _VALIDATION_DIR / "metric_validation.py"
_DATA_VALIDATION_FILE = _VALIDATION_DIR / "data_validation.py"

_METRIC_VALIDATION_MODULE = "_metricmind_metric_validation"
_DATA_VALIDATION_MODULE = "_metricmind_data_validation"

# Mirrors the blocklist inside DataValidator.validate_cube_output, which skips
# any 'sales'-containing column whose name also contains one of these words.
_SALES_NAME_BLOCKLIST = ("region", "mode", "category", "city", "country", "name")


def _load_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Load a standalone module by file path.

    Both validator modules are self-contained (they import only ``jsonschema``
    and ``pandas``), so they can be loaded without putting the repository root on
    ``sys.path``.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create an import spec for '{path}'.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


@lru_cache(maxsize=1)
def load_metric_validation_module() -> ModuleType:
    """Load ``analytics_validation/validation/metric_validation.py``."""
    return _load_module_from_path(_METRIC_VALIDATION_MODULE, _METRIC_VALIDATION_FILE)


@lru_cache(maxsize=1)
def load_data_validation_module() -> ModuleType:
    """Load ``analytics_validation/validation/data_validation.py``."""
    return _load_module_from_path(_DATA_VALIDATION_MODULE, _DATA_VALIDATION_FILE)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------
def _normalize_schema_result(raw: Any) -> SchemaValidationResult:
    """Normalise ``MetricValidator.validate_agent_query``'s ``(bool, str)`` tuple.

    The tuple shape is the *documented, actual* contract at
    ``analytics_validation/validation/metric_validation.py``. A dict is also
    tolerated so a future refactor of that module does not break this adapter.
    """
    if isinstance(raw, tuple) and len(raw) == 2:
        is_valid, message = raw
        return SchemaValidationResult(is_valid=bool(is_valid), message=str(message))
    if isinstance(raw, dict):
        return SchemaValidationResult(
            is_valid=bool(raw.get("is_valid", raw.get("valid", False))),
            message=str(raw.get("message", "Validation completed.")),
        )
    # Anything else means the validator's contract changed under us. Fail loudly
    # rather than assuming success.
    return SchemaValidationResult(
        is_valid=False,
        message=f"Unrecognised validator result of type {type(raw).__name__}.",
    )


def _normalize_data_result(raw: Any) -> tuple[DataValidationResult, bool]:
    """Normalise ``DataValidator.validate_cube_output``'s two dict shapes.

    Returns the normalised result and whether it represents an empty-dataset
    FAIL.
    """
    if not isinstance(raw, dict):
        return (
            DataValidationResult(
                status="FAIL",
                reason=f"Unrecognised validator result of type {type(raw).__name__}.",
                raw={"repr": repr(raw)},
            ),
            True,
        )

    if "reason" in raw and "row_count" not in raw:
        # The empty-dataset shape: {"status": "FAIL", "reason": "..."}
        return (
            DataValidationResult(
                status=str(raw.get("status", "FAIL")),
                reason=str(raw.get("reason", "")),
                raw=raw,
            ),
            True,
        )

    return (
        DataValidationResult(
            status=str(raw.get("status", "PASS")),
            row_count=int(raw.get("row_count", 0) or 0),
            null_count=int(raw.get("null_count", 0) or 0),
            invalid_discount_detected=bool(raw.get("invalid_discount_detected", False)),
            negative_sales_detected=bool(raw.get("negative_sales_detected", False)),
            raw=raw,
        ),
        False,
    )


def _columns_matching_heuristics(columns: Sequence[str]) -> Dict[str, List[str]]:
    """Report which result columns DataValidator's heuristics would inspect."""
    discount_columns = [name for name in columns if "discount" in name.lower()]
    sales_columns = [
        name
        for name in columns
        if "sales" in name.lower() and not any(word in name.lower() for word in _SALES_NAME_BLOCKLIST)
    ]
    return {"discount": discount_columns, "sales": sales_columns}


def _apply_member_mapping(
    rows: Sequence[Dict[str, Any]], members: Optional[Sequence[str]]
) -> List[Dict[str, Any]]:
    """Optionally rename row keys to Cube-style member names before auditing."""
    if not members:
        return [dict(row) for row in rows]
    mapped: List[Dict[str, Any]] = []
    for row in rows:
        keys = list(row.keys())
        mapped_row: Dict[str, Any] = {}
        for index, key in enumerate(keys):
            mapped_row[members[index] if index < len(members) else key] = row[key]
        mapped.append(mapped_row)
    return mapped


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class ValidationService:
    """Wraps the repository's validators behind one report shape."""

    def validate_governed_query(self, governed_query: GovernedQuery) -> ValidationReport:
        """Validate a governed query by rendering it as a Cube payload.

        This is the same payload the future Cube adapter will send, so the check
        remains meaningful after the semantic layer lands.
        """
        payload = build_cube_payload(governed_query)
        try:
            module = load_metric_validation_module()
            raw = module.MetricValidator.validate_agent_query(payload)
        except Exception as exc:
            logger.exception("MetricValidator could not be executed")
            return ValidationReport(
                is_valid=False,
                status="ERROR",
                errors=["The schema validator could not be executed."],
                notes=[f"MetricValidator unavailable: {type(exc).__name__}."],
            )

        schema_result = _normalize_schema_result(raw)
        errors = [] if schema_result.is_valid else [schema_result.message]

        return ValidationReport(
            is_valid=schema_result.is_valid,
            status="PASS" if schema_result.is_valid else "FAIL",
            schema_validation=schema_result,
            errors=errors,
            checks_applied=["MetricValidator.validate_agent_query (Cube payload schema)"],
        )

    def validate_rows(
        self,
        rows: Sequence[Dict[str, Any]],
        *,
        columns: Optional[Sequence[str]] = None,
        members: Optional[Sequence[str]] = None,
    ) -> ValidationReport:
        """Audit result rows with ``DataValidator.validate_cube_output``."""
        audited = _apply_member_mapping(rows, members)
        column_names = (
            list(columns)
            if columns
            else (list(audited[0].keys()) if audited else [])
        )

        try:
            module = load_data_validation_module()
            # DataValidator documents its input as a Cube REST API response.
            raw = module.DataValidator.validate_cube_output({"data": audited})
        except Exception as exc:
            logger.exception("DataValidator could not be executed")
            return ValidationReport(
                is_valid=False,
                status="ERROR",
                errors=["The data validator could not be executed."],
                notes=[f"DataValidator unavailable: {type(exc).__name__}."],
            )

        data_result, is_empty_failure = _normalize_data_result(raw)

        errors: List[str] = []
        warnings: List[str] = []
        checks_applied = ["DataValidator.validate_cube_output (row count, null count)"]
        checks_skipped: List[SkippedCheck] = []
        notes: List[str] = []

        if is_empty_failure:
            message = data_result.reason or "The validator reported an empty dataset."
            errors.append(message)
            return ValidationReport(
                is_valid=False,
                status="FAIL",
                data_validation=data_result,
                errors=errors,
                checks_applied=["DataValidator.validate_cube_output (empty dataset guard)"],
                checks_skipped=[
                    SkippedCheck(
                        check="null_count / discount / negative sales",
                        reason="DataValidator returns early when the dataset is empty.",
                    )
                ],
                notes=notes,
            )

        heuristic_columns = _columns_matching_heuristics(column_names)

        if heuristic_columns["discount"]:
            checks_applied.append("DataValidator discount bounds check (0.0 - 1.0)")
        else:
            checks_skipped.append(
                SkippedCheck(
                    check="DataValidator discount bounds check (0.0 - 1.0)",
                    reason=(
                        "No result column name contains 'discount'. Governed metric columns are "
                        "named after governed metrics, so this heuristic does not match them."
                    ),
                )
            )

        if heuristic_columns["sales"]:
            checks_applied.append("DataValidator non-negative sales check")
        else:
            checks_skipped.append(
                SkippedCheck(
                    check="DataValidator non-negative sales check",
                    reason=(
                        "No result column name contains 'sales' outside its blocklist. Governed "
                        "metric columns are named after governed metrics (e.g. 'Revenue'), so this "
                        "heuristic does not match them."
                    ),
                )
            )

        checks_skipped.append(
            SkippedCheck(
                check="Referential integrity / accepted values",
                reason=(
                    "No relationships or accepted_values tests exist in the dbt project "
                    "(Stage 1 finding), and DataValidator implements neither."
                ),
            )
        )

        if data_result.null_count > 0:
            warnings.append(
                f"{data_result.null_count} null value(s) were found in the returned rows."
            )
        if data_result.invalid_discount_detected:
            warnings.append("DataValidator flagged discount values outside 0.0 - 1.0.")
        if data_result.negative_sales_detected:
            warnings.append("DataValidator flagged negative sales values.")

        is_valid = data_result.status != "FAIL"
        status = "FLAGGED" if (data_result.status == "FLAGGED" or warnings) else "PASS"

        notes.append(
            "Validation covers the rows returned by this query, not the whole warehouse table."
        )
        if not members and not (heuristic_columns["discount"] or heuristic_columns["sales"]):
            notes.append(
                "DataValidator's discount and negative-sales heuristics did not match any "
                "returned column; see checks_skipped. They are reported as skipped rather than "
                "as passed."
            )

        return ValidationReport(
            is_valid=is_valid,
            status=status,
            data_validation=data_result,
            errors=errors,
            warnings=warnings,
            checks_applied=checks_applied,
            checks_skipped=checks_skipped,
            notes=notes,
        )

    def combine(self, schema_report: ValidationReport, data_report: ValidationReport) -> ValidationReport:
        """Merge the pre-execution and post-execution reports into one."""
        errors = [*schema_report.errors, *data_report.errors]
        warnings = [*schema_report.warnings, *data_report.warnings]
        checks_applied = [*schema_report.checks_applied, *data_report.checks_applied]
        checks_skipped = [*schema_report.checks_skipped, *data_report.checks_skipped]
        notes = [*schema_report.notes, *data_report.notes]

        is_valid = schema_report.is_valid and data_report.is_valid

        if "ERROR" in (schema_report.status, data_report.status):
            status = "ERROR"
        elif not is_valid:
            status = "FAIL"
        elif "FLAGGED" in (schema_report.status, data_report.status):
            status = "FLAGGED"
        else:
            status = "PASS"

        return ValidationReport(
            is_valid=is_valid,
            status=status,
            schema_validation=schema_report.schema_validation,
            data_validation=data_report.data_validation,
            errors=errors,
            warnings=warnings,
            checks_applied=checks_applied,
            checks_skipped=checks_skipped,
            notes=notes,
        )


_VALIDATION_SERVICE = ValidationService()


def get_validation_service() -> ValidationService:
    """FastAPI dependency returning the validation service."""
    return _VALIDATION_SERVICE


__all__ = [
    "ValidationService",
    "get_validation_service",
    "load_metric_validation_module",
    "load_data_validation_module",
]
