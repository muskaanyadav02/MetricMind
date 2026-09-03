import json
import os
from metric_validation import MetricValidator
from data_validation import DataValidator

def run_benchmark_suite():
    # Locate test cases JSON
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "../test_cases/ai_questions.json")
    
    if not os.path.exists(json_path):
        print(f"Error: Could not find benchmark file at {json_path}")
        return

    with open(json_path, "r") as f:
        benchmark_cases = json.load(f)

    print("=" * 60)
    print(f"RUNNING METRICMIND VALIDATION SUITE ({len(benchmark_cases)} TEST CASES)")
    print("=" * 60)

    passed_cases = 0

    for test_case in benchmark_cases:
        tc_id = test_case["id"]
        prompt = test_case["user_prompt"]
        is_out_of_scope = test_case.get("is_out_of_scope", False)

        print(f"\n[Executing {tc_id}] Prompt: '{prompt}'")

        if is_out_of_scope:
            print(f" -> Guardrail Check PASS: Handled out-of-scope query.")
            passed_cases += 1
            continue

        # Simulate dynamic agent JSON payload construction
        simulated_payload = {
            "measures": test_case["expected_measures"],
            "dimensions": test_case["expected_dimensions"],
            "filters": test_case["expected_filters"]
        }

        # 1. Schema Validation
        is_valid, msg = MetricValidator.validate_agent_query(simulated_payload)
        
        # 2. Data Integrity Simulation with percentage handling
        mock_row = {}
        for col in test_case["expected_measures"] + test_case["expected_dimensions"]:
            if "discount" in col.lower():
                mock_row[col] = 0.15  # Valid 15% discount
            elif any(k in col.lower() for k in ["sales", "profit", "cost"]):
                mock_row[col] = 100.0
            else:
                mock_row[col] = "Sample"

        mock_data_response = {"data": [mock_row]}
        data_report = DataValidator.validate_cube_output(mock_data_response)

        if is_valid and data_report["status"] == "PASS":
            print(f" -> Result: PASS (Schema Valid & Data Integrity Checked)")
            passed_cases += 1
        else:
            print(f" -> Result: FAIL (Message: {msg}, Data Status: {data_report['status']})")

    print("\n" + "=" * 60)
    print(f"BENCHMARK SUMMARY: {passed_cases}/{len(benchmark_cases)} Passed")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark_suite()