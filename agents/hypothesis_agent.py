import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "hypothesis": "Unable to generate hypothesis"
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for hypothesis agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    hypothesis = data.get("hypothesis")
    if not isinstance(hypothesis, str) or not hypothesis:
        return FALLBACK_DICT
    return {"hypothesis": hypothesis}


def extract_json(text: str) -> dict:
    """Extract JSON from text that may contain extra content."""
    text = text.strip()
    # Check for LLM error
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
    with open("prompts/hypothesis_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals):
    template = load_prompt()
    prompt = template.format(signals=signals)
    response = generate(prompt)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data