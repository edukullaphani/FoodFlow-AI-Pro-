import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "scenarios": []
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for simulation agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        return FALLBACK_DICT
    validated = []
    for item in scenarios:
        if isinstance(item, dict):
            name = item.get("name")
            risk = item.get("risk")
            description = item.get("description")
            if isinstance(name, str) and isinstance(risk, str) and isinstance(description, str):
                validated.append({"name": name, "risk": risk, "description": description})
    return {"scenarios": validated}


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
    with open("prompts/simulation_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals, hypothesis):
    template = load_prompt()
    prompt = template.format(
        signals=signals,
        hypothesis=hypothesis
    )
    response = generate(prompt)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data