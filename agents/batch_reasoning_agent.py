import json
import re
from utils.llm_client import generate


FALLBACK_DICT = {
    "insights": "Unable to generate batch reasoning",
    "item_context": {}
}


def validate_output(data: dict) -> dict:
    """Validate and enforce schema for batch reasoning agent output."""
    if not isinstance(data, dict):
        return FALLBACK_DICT
    insights = data.get("insights")
    if not isinstance(insights, str) or not insights:
        return FALLBACK_DICT
    item_context = data.get("item_context", {})
    if not isinstance(item_context, dict):
        item_context = {}
    return {"insights": insights, "item_context": item_context}


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
    with open("prompts/batch_reasoning_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals_dict: dict, inventory_analysis: dict):
    """Run batch reasoning across all items.
    
    Args:
        signals_dict: Dict mapping item_name -> {stock, consumption_rate, days_to_expiry, trend}
        inventory_analysis: Output from analyze_inventory() with at_risk, overstock, safe lists
    
    Returns:
        Dict with insights and item_context
    """
    # Build summary of all items for batch processing
    items_summary = []
    for item_name, signals in signals_dict.items():
        status = "unknown"
        if item_name in inventory_analysis.get("at_risk", []):
            status = "at_risk"
        elif item_name in inventory_analysis.get("overstock", []):
            status = "overstock"
        elif item_name in inventory_analysis.get("safe", []):
            status = "safe"
        
        items_summary.append({
            "item": item_name,
            "stock": signals.get("stock", 0),
            "consumption_rate": signals.get("consumption_rate", 0),
            "days_to_expiry": signals.get("days_to_expiry", 0),
            "trend": signals.get("trend", "unknown"),
            "status": status
        })
    
    template = load_prompt()
    prompt = template.format(
        signals_dict=signals_dict,
        inventory_analysis=inventory_analysis,
        items_summary=items_summary
    )
    response = generate(prompt)

    data = extract_json(response)
    if data is None:
        data = FALLBACK_DICT

    data = validate_output(data)
    return data