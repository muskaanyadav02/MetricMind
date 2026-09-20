from semantic_client import execute_query


query = {
    "metric": "Revenue",
    "dimension": "Category",
    "operation": "total",
    "filters": {},
}


print("Testing semantic client...", flush=True)

try:
    result = execute_query(query)

    print("Cube query executed successfully.", flush=True)
    print("Data:")
    print(result["data"])

except Exception as e:
    print("Error:", e, flush=True)