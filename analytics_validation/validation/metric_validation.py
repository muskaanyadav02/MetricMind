import jsonschema

# Cube REST API payload contract
CUBE_SCHEMA = {
    "type": "object",
    "properties": {
        "measures": {"type": "array", "items": {"type": "string"}},
        "dimensions": {"type": "array", "items": {"type": "string"}},
        "filters": {"type": "array"}
    },
    "required": ["measures"]
}

class MetricValidator:
    @staticmethod
    def validate_agent_query(payload: dict) -> tuple[bool, str]:
        """Validates if the AI agent created a valid Cube JSON payload."""
        try:
            jsonschema.validate(instance=payload, schema=CUBE_SCHEMA)
            return True, "Valid Payload"
        except jsonschema.ValidationError as e:
            return False, f"Validation Error: {e.message}"

# Simple test run when executing this script directly
if __name__ == "__main__":
    sample_payload = {
        "measures": ["Sales.margin"],
        "dimensions": ["Sales.region"]
    }
    is_valid, message = MetricValidator.validate_agent_query(sample_payload)
    print(f"Validation Test Output: {message}")