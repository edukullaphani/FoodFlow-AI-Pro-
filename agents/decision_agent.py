"""Decision agent - rule-based, no LLM required."""

from typing import Dict


FALLBACK_DECISION = {
    "action": "safe",
    "reason": "default fallback",
    "confidence": "low"
}


def run(signals_dict: dict, inventory_analysis: dict, reasoning: dict = None) -> dict:
    """Make decisions for all items based on inventory analysis.
    
    Args:
        signals_dict: Dict mapping item_name -> {stock, consumption_rate, days_to_expiry, trend}
        inventory_analysis: Output from analyze_inventory() with at_risk, overstock, safe lists
        reasoning: Optional output from batch_reasoning_agent (not used in rule-based mode)
    
    Returns:
        Dict mapping item -> {action, reason, confidence}
    """
    decisions = {}
    
    at_risk_items = set(inventory_analysis.get("at_risk", []))
    overstock_items = set(inventory_analysis.get("overstock", []))
    
    for item_name in signals_dict.keys():
        if item_name in at_risk_items:
            decisions[item_name] = {
                "action": "use_now",
                "reason": "Item at risk - low days to expiry",
                "confidence": "high"
            }
        elif item_name in overstock_items:
            decisions[item_name] = {
                "action": "monitor",
                "reason": "Overstocked with low consumption rate",
                "confidence": "medium"
            }
        else:
            decisions[item_name] = {
                "action": "safe",
                "reason": "Item status normal",
                "confidence": "high"
            }
    
    return decisions