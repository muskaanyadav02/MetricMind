from agent import process_question


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
    result = process_question(question)

    print("\nQuestion:", question)
    print("Structured Query:", result["query"])
    print("Validation:", result["validation"])
    print("Agent Response:", result["response"])