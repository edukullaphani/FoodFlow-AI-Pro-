from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)


def generate(prompt: str, max_tokens: int = 500) -> str:
    try:
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM ERROR]: {str(e)}"