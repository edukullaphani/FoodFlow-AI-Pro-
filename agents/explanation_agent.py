import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "explanation": "Unable to generate explanation"
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for explanation agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    explanation = data.get("explanation")
    if not isinstance(explanation, str) or not explanation:
        return FALLBACK_DICT
    return {"explanation": explanation}


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
    with open("prompts/explanation_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(decision, signals):
    # Handle decision as dict (now returns dict with action, reason, confidence)
    if isinstance(decision, dict):
        decision_action = decision.get("action", "")
        decision_reason = decision.get("reason", "")
        decision_str = f"action: {decision_action}, reason: {decision_reason}"
    else:
        decision_str = str(decision)

    template = load_prompt()
    prompt = template.format(
        decision=decision_str,
        item=signals.get("item", "unknown"),
        consumption_rate=signals.get("consumption_rate", 0),
        days_to_expiry=signals.get("days_to_expiry", 0),
        trend=signals.get("trend", "unknown")
    )
    response = generate(prompt, max_tokens=2000)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data