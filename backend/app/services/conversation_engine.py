import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_response(conversation_history: str, system_prompt: str = None) -> str:
    contents = [
        {"role": msg["role"],"parts":[{"text": msg["content"]}]}
        for msg in conversation_history
    ]
    config = types.GenerateContentConfig(system_instruction=system_prompt) if system_prompt else None

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )
    return response.text