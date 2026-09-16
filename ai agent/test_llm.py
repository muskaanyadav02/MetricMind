from ollama import chat

print("Connecting to Llama 3.1...", flush=True)

try:
    response = chat(
        model="llama3.1:latest",
        messages=[
            {
                "role": "user",
                "content": "Say hello in one short sentence."
            }
        ]
    )

    print("Response received:", flush=True)
    print(response.message.content, flush=True)

except Exception as e:
    print("Error:", e, flush=True)