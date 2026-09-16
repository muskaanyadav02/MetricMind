from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


PROMPT_FILE = Path(__file__).parent / "prompts" / "llm_system_prompt.txt"

system_prompt = PROMPT_FILE.read_text(encoding="utf-8")


llm = ChatOllama(
    model="llama3.1:latest",
    temperature=0,
)


def ask_llm(question: str) -> str:
    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    )

    return response.content


if __name__ == "__main__":
    question = "Which category has the highest profit in 2024?"

    print("Sending question through LangChain...", flush=True)

    try:
        answer = ask_llm(question)

        print("\nLlama response:", flush=True)
        print(answer, flush=True)

    except Exception as e:
        print("\nError:", e, flush=True)