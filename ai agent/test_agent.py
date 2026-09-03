from query_builder import build_query
from validator import validate_query

questions = [
    "Which category made the most profit?",
    "Show sales by country",
    "Compare quantity by region",
    "Which category had the highest profit in 2024?",
    "Show total sales by country in 2023",
    "What region had the lowest quantity?",
    "What is the average sales by market?",
    "Show customer happiness by country",
    "Show me the best products",
    "Which is the best category?",
    "Show me the best products by profit"
]


for question in questions:
    query = build_query(question)
    validation = validate_query(query)

    print("\nQuestion:", question)
    print("Structured Query:", query)
    print("Validation:", validation)