import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "add_dishes": [],
    "remove_dishes": [],
    "modify_dishes": []
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for menu optimization agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    
    add_dishes = data.get("add_dishes", [])
    if not isinstance(add_dishes, list):
        add_dishes = []
    
    remove_dishes = data.get("remove_dishes", [])
    if not isinstance(remove_dishes, list):
        remove_dishes = []
    
    modify_dishes = data.get("modify_dishes", [])
    if not isinstance(modify_dishes, list):
        modify_dishes = []
    
    return {
        "add_dishes": add_dishes,
        "remove_dishes": remove_dishes,
        "modify_dishes": modify_dishes
    }


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
    with open("prompts/menu_optimization_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def load_menu():
    """Load menu data from menu.json."""
    try:
        with open("data/menu.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def normalize_decisions(decisions):
    normalized = {}
    for item, dec in decisions.items():
        if isinstance(dec, dict):
            normalized[item] = dec
        elif isinstance(dec, list) and len(dec) > 0:
            normalized[item] = {"action": dec[0]}
        elif isinstance(dec, str):
            normalized[item] = {"action": dec}
        else:
            normalized[item] = {"action": "safe"}
    return normalized


def run(analysis: dict, decisions: dict, menu: list = None):
    """Run menu optimization based on inventory decisions.
    
    Args:
        analysis: Analysis dict with at_risk/overstock/safe lists
        decisions: Dict mapping item -> {action, reason, confidence}
        menu: Optional menu list from menu.json
    
    Returns:
        Dict with add_dishes, remove_dishes, modify_dishes
    """
    if menu is None:
        menu = load_menu()
    
    decisions = normalize_decisions(decisions)
    at_risk_items = analysis.get("at_risk", []) if isinstance(analysis, dict) else []
    
    # Extract items needing action
    items_needing_use = [item for item, dec in decisions.items() 
                         if dec.get("action") == "use_now"]
    items_needing_monitor = [item for item, dec in decisions.items() 
                             if dec.get("action") == "monitor"]
    
    template = load_prompt()
    prompt = template.format(
        at_risk_items=at_risk_items,
        items_needing_use=items_needing_use,
        items_needing_monitor=items_needing_monitor,
        decisions=decisions,
        menu=menu
    )
    response = generate(prompt)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data