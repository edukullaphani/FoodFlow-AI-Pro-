import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "strategies": []
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for strategy agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    strategies = data.get("strategies")
    if not isinstance(strategies, list):
        return FALLBACK_DICT
    validated = [s for s in strategies if isinstance(s, str)]
    return {"strategies": validated}


def extract_json(text: str) -> dict:
    """Extract JSON from text that may contain extra content."""
    text = text.strip()
    if text.startswith("[LLM ERROR]"):
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def load_prompt():
    with open("prompts/strategy_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(decision, signals):
    template = load_prompt()
    prompt = template.format(
        decision=decision["action"] if isinstance(decision, dict) else decision,
        signals=signals
    )
    response = generate(prompt)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data