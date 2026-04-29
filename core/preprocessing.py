from datetime import datetime
from scripts.db import get_history

def build_signals(inventory_state):
    signals_dict = {}
    today = datetime.now()
    
    for item, data in inventory_state.items():
        stock = data["stock"]
        batches = data["batches"]
        
        nearest_expiry_date = None
        days_to_expiry = 999
        
        if batches:
            nearest_expiry_date = min(b["expiry_date"] for b in batches)
            expiry_dt = datetime.strptime(nearest_expiry_date, "%Y-%m-%d")
            days_to_expiry = (expiry_dt - today).days
            
        # derived from history (simple absolute average of changes)
        history = get_history(item)
        if history:
            consumption_rate = sum(abs(x) for x in history if x < 0) / max(1, len([x for x in history if x < 0]))
            
            # Trend logic
            recent = history[:3]
            if len(recent) >= 2:
                # if recent consumption (negative values) is getting more negative, consumption is increasing
                recent_usage = [abs(x) for x in recent if x < 0]
                if len(recent_usage) >= 2:
                    if recent_usage[0] > recent_usage[-1]:
                        trend = "increasing"
                    elif recent_usage[0] < recent_usage[-1]:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            consumption_rate = 0.0
            trend = "stable"
            
        signals_dict[item] = {
            "stock": stock,
            "days_to_expiry": max(0, days_to_expiry),
            "consumption_rate": float(consumption_rate),
            "trend": trend
        }
    
    return signals_dict

def analyze_inventory(signals_dict):
    analysis = {
        "at_risk": [],
        "overstock": [],
        "safe": []
    }
    
    threshold_stock = 10
    
    for item, stats in signals_dict.items():
        # at_risk: days_to_expiry <= 2 AND stock > threshold
        if stats["days_to_expiry"] <= 2 and stats["stock"] > 0:
            analysis["at_risk"].append(item)
        
        # overstock: stock high AND consumption_rate low
        elif stats["stock"] > threshold_stock * 2 and stats["consumption_rate"] < threshold_stock / 5:
            analysis["overstock"].append(item)
        
        else:
            analysis["safe"].append(item)
            
    return analysis
