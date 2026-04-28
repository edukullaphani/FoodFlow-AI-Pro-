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
    last_error = None
    
    for attempt in range(2):
        try:
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            # Extract content safely - try content first, then reasoning
            message = response.choices[0].message
            content = message.content
            
            if content is None or (isinstance(content, str) and not content.strip()):
                # Try reasoning as fallback
                content = message.reasoning
            
            if content is None or (isinstance(content, str) and not content.strip()):
                # Empty response - retry
                print(f"Retry attempt: {attempt + 1} - empty response", flush=True)
                last_error = "Empty response"
                continue
            
            content = content.strip()
            import sys
            print(f"[DEBUG LLM]: {content[:200]}...", flush=True)
            return content
            
        except Exception as e:
            last_error = str(e)
            print(f"Retry attempt: {attempt + 1} - {str(e)}", flush=True)
            continue
    
    # All retries failed
    print(f"Using fallback response after retries", flush=True)
    return f"[LLM ERROR]: Failed after retries - {last_error}"