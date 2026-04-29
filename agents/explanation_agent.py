import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "explanation": "Unable to generate system-level explanation"
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


def run(analysis: dict, decisions: dict, menu_actions: dict):
    """Run system-level explanation.
    
    Args:
        analysis: Output from inventory analysis {at_risk, overstock, safe}
        decisions: Dict mapping item -> {action, reason, confidence}
        menu_actions: Output from menu optimization {add_dishes, remove_dishes, modify_dishes}
    
    Returns:
        Dict with system-level explanation
    """
    # Build decision summary
    decision_summary = []
    for item, dec in decisions.items():
        decision_summary.append(f"{item}: {dec.get('action', 'unknown')}")
    
    # Build menu action summary
    menu_summary = []
    if menu_actions.get("add_dishes"):
        menu_summary.append(f"Add: {menu_actions['add_dishes']}")
    if menu_actions.get("remove_dishes"):
        menu_summary.append(f"Remove: {menu_actions['remove_dishes']}")
    if menu_actions.get("modify_dishes"):
        menu_summary.append(f"Modify: {menu_actions['modify_dishes']}")
    
    template = load_prompt()
    prompt = template.format(
        analysis=analysis,
        decisions=decision_summary,
        menu_actions=menu_summary,
        at_risk_count=len(analysis.get("at_risk", [])),
        overstock_count=len(analysis.get("overstock", [])),
        safe_count=len(analysis.get("safe", []))
    )
    response = generate(prompt, max_tokens=2000)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data