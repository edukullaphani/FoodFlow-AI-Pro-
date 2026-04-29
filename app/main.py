from services.graph_pipeline import run_graph_pipeline
from datetime import datetime
import random
from scripts.db import add_batch, get_inventory_state

if __name__ == "__main__":
    csv_path = "data/sample.csv"
    
    NUM_DAYS = 5
    
    for day in range(1, NUM_DAYS + 1):
        print(f"\n========== DAY {day} ==========\n")
        
        result = run_graph_pipeline(csv_path)
        
        print("[EXPLANATION]")
        print(result.get("explanation"))
        
        print("\n[TOP ORDERS]")
        orders = result.get("orders", {})
        sorted_orders = sorted(orders.items(), key=lambda x: x[1], reverse=True)
        
        for dish, qty in sorted_orders[:5]:
            print(f"{dish}: {qty}")
        
        # Optional: Simulate daily restock
        inventory_state = get_inventory_state()
        if random.random() < 0.5 and inventory_state:
            sample_items = list(inventory_state.keys())[:5]
            
            for item in sample_items:
                restock_qty = random.randint(5, 20)
                expiry = datetime.now().strftime("%Y-%m-%d")
                add_batch(item, restock_qty, expiry)