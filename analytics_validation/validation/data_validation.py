import pandas as pd

class DataValidator:
    @staticmethod
    def validate_cube_output(cube_json_response: dict) -> dict:
        """
        Parses Cube REST API response into Pandas and audits real Superstore columns.
        """
        data = cube_json_response.get("data", [])
        if not data:
            return {"status": "FAIL", "reason": "Empty dataset returned from Cube API."}

        df = pd.DataFrame(data)
        null_count = int(df.isnull().sum().sum())

        invalid_discount = False
        negative_sales = False

        # Convert numeric columns safely and audit bounds
        for col in df.columns:
            # Check discount bounds (0.0 to 1.0)
            if "discount" in col.lower():
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if ((numeric_col < 0.0) | (numeric_col > 1.0)).any():
                    invalid_discount = True

            # Check for negative sales (ignoring text columns like Sales.Region)
            if "sales" in col.lower() and not any(text_key in col.lower() for text_key in ["region", "mode", "category", "city", "country", "name"]):
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if (numeric_col < 0.0).any():
                    negative_sales = True

        has_issues = (null_count > 0) or invalid_discount or negative_sales

        return {
            "status": "FLAGGED" if has_issues else "PASS",
            "row_count": len(df),
            "null_count": null_count,
            "invalid_discount_detected": invalid_discount,
            "negative_sales_detected": negative_sales
        }

if __name__ == "__main__":
    sample_response = {
        "data": [
            {"Sales.Region": "APAC", "Sales.Sales": 1500.50, "Sales.Discount": 0.20},
            {"Sales.Region": "Europe", "Sales.Sales": 2300.00, "Sales.Discount": 0.15}
        ]
    }
    report = DataValidator.validate_cube_output(sample_response)
    print("Data Integrity Report:", report)