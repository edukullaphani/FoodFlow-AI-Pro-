from datetime import datetime
import sqlite3
from collections import defaultdict
import os


def get_item_effectiveness():
    """
    Fetch historical effectiveness scores from evaluation table.
    """
    # Get DB_PATH from scripts.db
    from scripts.db import DB_PATH
    
    if not os.path.exists(DB_PATH):
        return {}
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT item, effectiveness FROM evaluation
    """)
    
    scores = defaultdict(int)
    
    for item, eff in cursor.fetchall():
        if eff == "good":
            scores[item] += 1
        elif eff == "bad":
            scores[item] -= 1
    
    conn.close()
    return scores

def evaluate_day(previous_state, current_state, decisions, analysis):
    """
    Evaluate the effectiveness of AI decisions.
    
    Args:
        previous_state: State before decisions.
        current_state: State after decisions/usage.
        decisions: Decisions taken for each item.
        analysis: Analysis results including 'at_risk' items.
        
    Returns:
        List of evaluation records.
    """
    records = []
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # We need to handle items that might be in previous or current state
    all_items = set(previous_state.keys()) | set(current_state.keys())
    
    for item in all_items:
        # Handle missing items safely
        prev_item_data = previous_state.get(item, {"stock": 0})
        curr_item_data = current_state.get(item, {"stock": 0})
        
        stock_before = prev_item_data.get("stock", 0)
        stock_after = curr_item_data.get("stock", 0)
        
        # Get decision for item
        item_decision = decisions.get(item, {})
        decision = item_decision.get("action", "none")
        
        before = stock_before
        after = stock_after
        change = before - after
        
        # --- Effectiveness Logic ---
        # Dynamic threshold scales by available stock so low-stock items can still score "good".
        use_now_threshold = min(3, max(1, stock_before))
        reduction_ratio = (change / stock_before) if stock_before > 0 else 0
        
        if decision == "use_now":
            if change >= use_now_threshold or reduction_ratio >= 0.30:
                effectiveness = "good"
            else:
                effectiveness = "bad"
        elif decision == "monitor":
            if change >= 1:
                effectiveness = "good"
            else:
                effectiveness = "neutral"
        elif decision == "safe":
            if change == 0:
                effectiveness = "good"
            else:
                effectiveness = "neutral"
        else:
            effectiveness = "neutral"
        
        print(f"[EVAL] {item}: {decision}, change={change}, result={effectiveness}")
        
        # Estimate waste as extra depletion beyond expected minimum operational usage.
        # This keeps current schema while making the value less trivially equal to change.
        expected_usage = 1 if decision in ("use_now", "monitor") else 0
        waste = max(0, change - expected_usage)
            
        records.append({
            "date": date_str,
            "item": item,
            "decision": decision,
            "stock_before": stock_before,
            "stock_after": stock_after,
            "waste": waste,
            "effectiveness": effectiveness
        })
        
    return records
