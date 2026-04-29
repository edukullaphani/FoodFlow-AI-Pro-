def analyze_inventory(signals_dict: dict) -> dict:
    """Analyze inventory status across all items.
    
    Args:
        signals_dict: Dict mapping item_name -> {
            "stock": int,
            "consumption_rate": float,
            "days_to_expiry": int,
            "trend": str
        }
    
    Returns:
        Dict with at_risk, overstock, and safe item lists
    """
    at_risk = []
    overstock = []
    safe = []
    
    for item_name, signals in signals_dict.items():
        stock = signals.get("stock", 0)
        consumption_rate = signals.get("consumption_rate", 0)
        days_to_expiry = signals.get("days_to_expiry", 999)
        
        # Rule: at_risk - days_to_expiry <= 2 AND stock high
        if days_to_expiry <= 2 and stock > 0:
            at_risk.append(item_name)
        # Rule: overstock - stock high AND consumption_rate low
        elif stock > 50 and consumption_rate < 5:
            overstock.append(item_name)
        # Rule: safe - everything else
        else:
            safe.append(item_name)
    
    return {
        "at_risk": at_risk,
        "overstock": overstock,
        "safe": safe
    }