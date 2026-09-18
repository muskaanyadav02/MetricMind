import json
import requests
import jwt


API_SECRET = "metricmind-local-development-secret-2026"

url = "http://localhost:4000/cubejs-api/v1/load"

query = {
    "measures": ["FactSales.revenue"],
    "timeDimensions": [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "year",
        }
    ],
    "limit": 20,
}

token = jwt.encode(
    {},
    API_SECRET,
    algorithm="HS256",
)

headers = {
    "Authorization": token,
}

print("Testing Cube API...", flush=True)

try:
    response = requests.get(
        url,
        params={"query": json.dumps(query)},
        headers=headers,
    )

    print("Status:", response.status_code)
    print("Response:")
    print(response.text)

except Exception as e:
    print("Error:", e)