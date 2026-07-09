import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ai_response(conversation_history: list, system_prompt: str = None) -> str:
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    messages += [
        {"role": "assistant" if msg["role"] == "model" else "user", "content": msg["content"]}
        for msg in conversation_history
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    return response.choices[0].message.content or "Sorry, I got a bit lost there — could you say that again?"