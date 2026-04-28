import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "action": "maintain_stock",
    "reason": "fallback due to parsing error",
    "confidence": "low"
}

VALID_ACTIONS = ["reduce_stock", "increase_stock", "maintain_stock"]
VALID_CONFIDENCE = ["low", "medium", "high"]


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for decision agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    action = data.get("action")
    if action not in VALID_ACTIONS:
        action = "maintain_stock"
    reason = data.get("reason")
    if not isinstance(reason, str):
        reason = "fallback reason"
    confidence = data.get("confidence")
    if confidence not in VALID_CONFIDENCE:
        confidence = "low"
    return {"action": action, "reason": reason, "confidence": confidence}


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
    with open("prompts/decision_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals,hypothesis,simulation):
    template = load_prompt()
    prompt = template.format(signals=signals,
                             hypothesis=hypothesis, 
                             simulation=simulation
                             )
    response = generate(prompt, max_tokens=600)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data