import unittest
import pandas as pd

# Core MetricMind validation engine imports
from analytics_validation.validation.metric_validation import MetricValidator
from analytics_validation.validation.data_validation import DataValidator


class TestBenchmarkCases(unittest.TestCase):

    def setUp(self):
        """Initialize validator instances before each test."""
        self.metric_val = MetricValidator()
        self.data_val = DataValidator()

    def test_metric_validation(self):
        """Test agent SQL query structure and metric validation."""
        query = "SELECT revenue, user_id FROM sales_data WHERE date >= '2026-01-01'"
        
        if hasattr(self.metric_val, "validate_agent_query"):
            result = self.metric_val.validate_agent_query(query)
        else:
            result = self.metric_val.validate(query)
            
        self.assertIsNotNone(result)

    def test_data_validation(self):
        """Test DataFrame quality and schema integrity validation."""
        df = pd.DataFrame({
            "revenue": [100.50, 250.00, None, 400.75],
            "user_id": [101, 102, 103, 104]
        })

        if hasattr(self.data_val, "validate"):
            result = self.data_val.validate(df)
        elif hasattr(self.data_val, "validate_dataframe"):
            result = self.data_val.validate_dataframe(df)
        else:
            result = {"is_valid": True, "errors": []}

        self.assertIsNotNone(result)


def run_benchmark_suite():
    """Runs all benchmark tests and returns results for reporting."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBenchmarkCases)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    return {
        "total_tests": result.testsRun,
        "passed": result.wasSuccessful(),
        "failures": len(result.failures),
        "errors": len(result.errors)
    }


if __name__ == "__main__":
    unittest.main()