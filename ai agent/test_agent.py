from query_builder import build_query

questions = [
    "Which category made the most profit?",
    "Show sales by country",
    "Compare quantity by region"
]

for question in questions:
    print(build_query(question))