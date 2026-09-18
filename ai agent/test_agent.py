from agent import process_question

questions = [
    "Which category made the most profit?",
    "Show sales by country",
    "Compare quantity by region",
    "Which category had the highest profit in 2014?",
    "Show total sales by country in 2014",
    "What region had the lowest quantity?",
    "What is the average sales by market?",
    "Show customer happiness by country",
    "Show me the best products",
    "Which is the best category?",
    "Show me the best products by profit",
    "Show me European sales",
]

for question in questions:
    result = process_question(question)

    print("\nQuestion:", question)
    print("Structured Query:", result["query"])
    print("Validation:", result["validation"])
    print("Agent Response:", result["response"])

    if "semantic_result" in result:
        print("Semantic Result:", result["semantic_result"])