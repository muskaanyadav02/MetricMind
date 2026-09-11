import sys
from pathlib import Path
import pandas as pd

# 1. Resolve project root path dynamically
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 2. Import core MetricMind validation engines
from analytics_validation.validation.metric_validation import MetricValidator
from analytics_validation.validation.data_validation import DataValidator


def validate_agent_output(generated_query: str, result_df: pd.DataFrame) -> dict:
    """
    Validates agent-generated semantic queries and output DataFrames.
    Returns a dictionary containing validation status and errors.
    """
    metric_val = MetricValidator()
    data_val = DataValidator()

    # 3. Call validate_agent_query directly
    schema_results = metric_val.validate_agent_query(generated_query)

    # 4. Validate Data Quality
    data_results = {}
    if hasattr(data_val, "validate_dataframe"):
        data_results = data_val.validate_dataframe(result_df)
    elif hasattr(data_val, "validate"):
        data_results = data_val.validate(result_df)
    else:
        data_results = {"is_valid": True, "errors": []}

    # Normalize response format
    schema_valid = schema_results.get("is_valid", True) if isinstance(schema_results, dict) else True
    data_valid = data_results.get("is_valid", True) if isinstance(data_results, dict) else True

    return {
        "is_valid": schema_valid and data_valid,
        "schema_errors": schema_results.get("errors", []) if isinstance(schema_results, dict) else [],
        "data_errors": data_results.get("errors", []) if isinstance(data_results, dict) else []
    }


if __name__ == "__main__":
    # 5. Executable test block with mock inputs
    mock_query = "SELECT revenue, user_id FROM sales_data WHERE date >= '2026-01-01'"
    mock_dataframe = pd.DataFrame({
        "revenue": [100.50, 250.00, None, 400.75],
        "user_id": [101, 102, 103, 104]
    })

    print("Executing Real-Time Guardrail Validation...")
    results = validate_agent_output(mock_query, mock_dataframe)

    print("\n--- Validation Results ---")
    print(f"Overall Valid : {results['is_valid']}")
    print(f"Schema Errors : {results['schema_errors']}")
    print(f"Data Errors   : {results['data_errors']}")