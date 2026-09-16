from pathlib import Path
from ollama import chat


PROMPT_FILE = Path(__file__).parent / "prompts" / "llm_system_prompt.txt"

system_prompt = PROMPT_FILE.read_text(encoding="utf-8")

question = "Which category has the highest profit in 2024?"

print("Sending question to Llama 3.1...", flush=True)

try:
    response = chat(
        model="llama3.1:latest",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    print("\nLlama response:", flush=True)
    print(response.message.content, flush=True)

except Exception as e:
    print("\nError:", e, flush=True)