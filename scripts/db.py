import sqlite3
import json
import os
from datetime import datetime
from itertools import combinations

DB_PATH = "data/foodflow.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item TEXT PRIMARY KEY,
        stock INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        quantity INTEGER,
        expiry_date TEXT,
        added_date TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        date TEXT,
        stock INTEGER,
        change INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        signals TEXT,
        analysis TEXT,
        decisions TEXT,
        menu_actions TEXT,
        explanation TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        item TEXT,
        decision TEXT,
        stock_before INTEGER,
        stock_after INTEGER,
        waste INTEGER,
        effectiveness TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS item_catalog (
        item TEXT PRIMARY KEY,
        category TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dish TEXT,
        ingredients TEXT,
        category TEXT,
        active INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dish_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dish TEXT,
        quantity INTEGER,
        date TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def add_batch(item, quantity, expiry_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    added_date = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("INSERT INTO inventory_batches (item, quantity, expiry_date, added_date) VALUES (?, ?, ?, ?)",
                   (item, quantity, expiry_date, added_date))
    
    cursor.execute("SELECT stock FROM inventory WHERE item = ?", (item,))
    row = cursor.fetchone()
    if row:
        new_stock = row[0] + quantity
        cursor.execute("UPDATE inventory SET stock = ? WHERE item = ?", (new_stock, item))
    else:
        new_stock = quantity
        cursor.execute("INSERT INTO inventory (item, stock) VALUES (?, ?)", (item, new_stock))
    
    cursor.execute("INSERT INTO inventory_history (item, date, stock, change) VALUES (?, ?, ?, ?)",
                   (item, added_date, new_stock, quantity))
    
    conn.commit()
    conn.close()

def consume_stock(item, quantity):
    if quantity <= 0:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, quantity FROM inventory_batches WHERE item = ? AND quantity > 0 ORDER BY expiry_date ASC", (item,))
    batches = cursor.fetchall()
    
    remaining_to_consume = quantity
    total_consumed = 0
    
    for batch_id, batch_qty in batches:
        if remaining_to_consume <= 0:
            break
            
        if batch_qty <= remaining_to_consume:
            cursor.execute("UPDATE inventory_batches SET quantity = 0 WHERE id = ?", (batch_id,))
            remaining_to_consume -= batch_qty
            total_consumed += batch_qty
        else:
            cursor.execute("UPDATE inventory_batches SET quantity = quantity - ? WHERE id = ?", (remaining_to_consume, batch_id,))
            total_consumed += remaining_to_consume
            remaining_to_consume = 0

    cursor.execute("SELECT stock FROM inventory WHERE item = ?", (item,))
    row = cursor.fetchone()
    if row:
        new_stock = max(0, row[0] - total_consumed)
        cursor.execute("UPDATE inventory SET stock = ? WHERE item = ?", (new_stock, item))
        
        now_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO inventory_history (item, date, stock, change) VALUES (?, ?, ?, ?)",
                       (item, now_str, new_stock, -total_consumed))
    
    conn.commit()
    conn.close()

def get_inventory_state():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT item, stock FROM inventory")
    items = cursor.fetchall()
    
    state = {}
    for item_name, stock in items:
        cursor.execute("SELECT quantity, expiry_date FROM inventory_batches WHERE item = ? AND quantity > 0 ORDER BY expiry_date ASC", (item_name,))
        batches = [{"quantity": q, "expiry_date": e} for q, e in cursor.fetchall()]
        state[item_name] = {
            "stock": stock,
            "batches": batches
        }
    
    conn.close()
    return state

def get_history(item, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT change FROM inventory_history WHERE item = ? ORDER BY id DESC LIMIT ?", (item, limit))
    history = [row[0] for row in cursor.fetchall()]
    conn.close()
    return history

def save_run(state):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
    INSERT INTO runs (timestamp, signals, analysis, decisions, menu_actions, explanation)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        json.dumps(state.get("signals", {})),
        json.dumps(state.get("analysis", {})),
        json.dumps(state.get("decisions", {})),
        json.dumps(state.get("menu_actions", {})),
        json.dumps(state.get("explanation", {}))
    ))
    
    conn.commit()
    conn.close()


def load_runs(limit=10):
    """Load recent runs from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, signals, analysis, decisions, menu_actions, explanation
        FROM runs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    runs = []
    for row in rows:
        runs.append({
            "id": row[0],
            "timestamp": row[1],
            "signals": json.loads(row[2]) if row[2] else {},
            "analysis": json.loads(row[3]) if row[3] else {},
            "decisions": json.loads(row[4]) if row[4] else {},
            "menu_actions": json.loads(row[5]) if row[5] else {},
            "explanation": json.loads(row[6]) if row[6] else {}
        })
    return runs

def save_evaluation(records):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for record in records:
        cursor.execute("""
        INSERT INTO evaluation (date, item, decision, stock_before, stock_after, waste, effectiveness)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record["date"],
            record["item"],
            record["decision"],
            record["stock_before"],
            record["stock_after"],
            record["waste"],
            record["effectiveness"]
        ))
    
    conn.commit()
    conn.close()

def get_item_category(item):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category FROM item_catalog WHERE item = ?", (item,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Unknown"

def get_menu():
    """Get active menu items."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT dish, ingredients FROM menu WHERE active = 1")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"dish": d, "ingredients": json.loads(i)}
        for d, i in rows
    ]

def consume_dish(dish, quantity=1):
    """Consume ingredients for a dish order."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT ingredients FROM menu WHERE dish = ?", (dish,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return
    
    ingredients = json.loads(row[0])
    
    for item in ingredients:
        consume_stock(item, quantity)

def log_dish_orders(order_log):
    """Log dish orders to dish_orders table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    
    for dish, qty in order_log.items():
        cursor.execute(
            "INSERT INTO dish_orders (dish, quantity, date) VALUES (?, ?, ?)",
            (dish, qty, date)
        )
    
    conn.commit()
    conn.close()


def _normalize_ingredients(ingredients):
    if not isinstance(ingredients, list):
        return []
    cleaned = []
    for item in ingredients:
        if isinstance(item, str):
            token = item.strip().lower()
            if token:
                cleaned.append(token)
    return cleaned


def _parse_dish_spec(spec):
    """Accept either a plain dish string or 'Dish Name (a, b, c)'."""
    if isinstance(spec, dict):
        dish_name = str(spec.get("dish", "")).strip()
        ingredients = _normalize_ingredients(spec.get("ingredients", []))
        return dish_name, ingredients
    if not isinstance(spec, str):
        return "", []

    text = spec.strip()
    if not text:
        return "", []

    if "(" in text and text.endswith(")"):
        dish_name, raw_ingredients = text.rsplit("(", 1)
        ingredients = [p.strip().lower() for p in raw_ingredients[:-1].split(",") if p.strip()]
        return dish_name.strip(), ingredients
    return text, []


def apply_menu_actions(menu_actions, decisions, signals_dict):
    """Apply menu optimization output to the menu table.

    Rules:
    - Add only dishes that can be made from currently available items.
    - Prioritize dishes containing use_now ingredients.
    - Deactivate dishes using only safe ingredients.
    - Create additional use-up dish variants from use_now ingredients.
    """
    menu_actions = menu_actions or {}
    decisions = decisions or {}
    signals_dict = signals_dict or {}

    use_now_items = {item for item, val in decisions.items() if isinstance(val, dict) and val.get("action") == "use_now"}
    safe_items = {item for item, val in decisions.items() if isinstance(val, dict) and val.get("action") == "safe"}
    monitor_items = {item for item, val in decisions.items() if isinstance(val, dict) and val.get("action") == "monitor"}
    available_items = {item for item, sig in signals_dict.items() if isinstance(sig, dict) and sig.get("stock", 0) > 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, dish, ingredients, active FROM menu")
    rows = cursor.fetchall()
    existing = {}
    for dish_id, dish, ingredients_json, active in rows:
        try:
            ingredients = _normalize_ingredients(json.loads(ingredients_json))
        except Exception:
            ingredients = []
        existing[dish] = {
            "id": dish_id,
            "ingredients": ingredients,
            "active": int(active),
        }

    added = 0
    reactivated = 0
    removed = 0

    # 1) Remove explicit dishes and safe-only dishes.
    remove_names = set(menu_actions.get("remove_dishes", []))
    for dish_name, info in existing.items():
        ingredients = info["ingredients"]
        remove_for_safety = bool(ingredients) and all(item in safe_items for item in ingredients)
        if dish_name in remove_names or remove_for_safety:
            if info["active"] == 1:
                cursor.execute("UPDATE menu SET active = 0 WHERE id = ?", (info["id"],))
                removed += 1

    # 2) Add LLM suggested dishes if feasible and use-now focused.
    for suggestion in menu_actions.get("add_dishes", []):
        dish_name, ingredients = _parse_dish_spec(suggestion)
        if not dish_name:
            continue

        if ingredients:
            if not set(ingredients).issubset(available_items):
                continue
            if use_now_items and not set(ingredients).intersection(use_now_items):
                continue

        if dish_name in existing:
            if existing[dish_name]["active"] == 0:
                cursor.execute("UPDATE menu SET active = 1 WHERE id = ?", (existing[dish_name]["id"],))
                reactivated += 1
            continue

        ingredients_to_store = ingredients if ingredients else sorted(list(use_now_items))[:3]
        if not ingredients_to_store:
            continue
        cursor.execute(
            "INSERT INTO menu (dish, ingredients, category, active) VALUES (?, ?, ?, 1)",
            (dish_name, json.dumps(ingredients_to_store), "dynamic"),
        )
        added += 1
        existing[dish_name] = {"id": cursor.lastrowid, "ingredients": ingredients_to_store, "active": 1}

    # 3) Generate additional use-up variants from use_now/monitor items.
    ranked_use_now = sorted(
        [i for i in use_now_items if i in available_items],
        key=lambda item: signals_dict.get(item, {}).get("stock", 0),
        reverse=True,
    )
    support_items = [i for i in monitor_items if i in available_items and i not in ranked_use_now]
    candidate_pool = ranked_use_now + support_items

    generated_specs = []
    for pair in combinations(ranked_use_now[:6], 2):
        fill = []
        for item in candidate_pool:
            if item not in pair:
                fill.append(item)
            if len(fill) == 1:
                break
        ingredients = [pair[0], pair[1]] + fill
        generated_specs.append(ingredients[:3])
        if len(generated_specs) >= 8:
            break

    for idx, ingredients in enumerate(generated_specs, start=1):
        if not set(ingredients).issubset(available_items):
            continue
        dish_name = f"Use-Up Special {idx}: " + " + ".join(item.replace("_", " ").title() for item in ingredients)
        if dish_name in existing:
            if existing[dish_name]["active"] == 0:
                cursor.execute("UPDATE menu SET active = 1 WHERE id = ?", (existing[dish_name]["id"],))
                reactivated += 1
            continue
        cursor.execute(
            "INSERT INTO menu (dish, ingredients, category, active) VALUES (?, ?, ?, 1)",
            (dish_name, json.dumps(ingredients), "dynamic"),
        )
        added += 1

    conn.commit()
    conn.close()

    return {
        "added": added,
        "reactivated": reactivated,
        "removed": removed,
        "use_now_items": len(use_now_items),
    }
