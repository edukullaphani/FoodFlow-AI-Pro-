import sqlite3
import random
import json
import os
import sys
from datetime import datetime, timedelta

# Ensure project root is in path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.db import init_db, add_batch, consume_stock, get_menu, consume_dish, log_dish_orders, DB_PATH

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory")
    cursor.execute("DELETE FROM inventory_batches")
    cursor.execute("DELETE FROM inventory_history")
    cursor.execute("DELETE FROM runs")
    cursor.execute("DELETE FROM item_catalog")
    cursor.execute("DELETE FROM menu")
    cursor.execute("DELETE FROM dish_orders")
    conn.commit()
    conn.close()

def seed_database():
    init_db()
    clear_db()
    
    # Item catalog
    catalog = {
        "tomato": "vegetable", "zucchini": "vegetable", "eggplant": "vegetable", "spinach": "vegetable",
        "mushroom": "vegetable", "bell_pepper": "vegetable", "carrot": "vegetable", "celery": "vegetable",
        "onion": "vegetable", "garlic": "vegetable", "leek": "vegetable",
        "basil": "herb", "oregano": "herb", "parsley": "herb", "rosemary": "herb", "thyme": "herb",
        "mozzarella": "dairy", "parmesan": "dairy", "ricotta": "dairy",
        "burrata": "dairy", "gorgonzola": "dairy", "mascarpone": "dairy", "cream": "dairy",
        "chicken": "protein", "ground_beef": "protein", "italian_sausage": "protein",
        "shrimp": "protein", "fish": "protein", "pancetta": "protein",
        "prosciutto": "protein", "bacon": "protein", "clams": "protein",
        "fresh_pasta": "prepared", "gnocchi": "prepared", "pesto": "prepared",
        "lasagna_sheets": "prepared", "ravioli": "prepared", "tortellini": "prepared",
        "olive_oil": "pantry", "dry_pasta": "pantry", "tomato_sauce": "pantry",
        "sugar": "pantry", "balsamic_vinegar": "pantry"
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for item, category in catalog.items():
        cursor.execute(
            "INSERT OR IGNORE INTO item_catalog (item, category) VALUES (?, ?)",
            (item, category)
        )
    conn.commit()
    conn.close()
    
    # Menu seeding
    MENU = [
    # 🥗 Appetizers
    {"dish": "Caprese Salad", "ingredients": ["tomato","mozzarella","basil","olive_oil"], "category": "appetizer"},
    {"dish": "Bruschetta", "ingredients": ["bread","tomato","basil","olive_oil"], "category": "appetizer"},
    {"dish": "Garlic Bread", "ingredients": ["bread","garlic","butter","oregano"], "category": "appetizer"},
    {"dish": "Stuffed Mushrooms", "ingredients": ["mushroom","ricotta","parsley"], "category": "appetizer"},
    {"dish": "Garlic Herb Mushrooms", "ingredients": ["mushroom","garlic","parsley","thyme"], "category": "appetizer"},
    {"dish": "Balsamic Roasted Vegetables", "ingredients": ["zucchini","eggplant","bell_pepper","onion","balsamic_vinegar","olive_oil"], "category": "appetizer"},
    {"dish": "Herb Roasted Vegetables", "ingredients": ["zucchini","carrot","bell_pepper","rosemary","thyme","olive_oil"], "category": "appetizer"},
    {"dish": "Prosciutto Herb Plate", "ingredients": ["prosciutto","rosemary"], "category": "appetizer"},

    # 🍲 Soups
    {"dish": "Tomato Basil Soup", "ingredients": ["tomato","basil","garlic"], "category": "soup"},
    {"dish": "Creamy Mushroom Soup", "ingredients": ["mushroom","cream","butter","garlic"], "category": "soup"},
    {"dish": "Vegetable Soup", "ingredients": ["carrot","celery","onion","tomato"], "category": "soup"},
    {"dish": "Chicken Herb Soup", "ingredients": ["chicken","carrot","celery","onion","parsley"], "category": "soup"},
    {"dish": "Seafood Soup", "ingredients": ["fish","shrimp","garlic","tomato"], "category": "soup"},
    {"dish": "Leek & Cream Soup", "ingredients": ["leek","cream","butter"], "category": "soup"},

    # 🍝 Main
    {"dish": "Spaghetti Aglio e Olio", "ingredients": ["dry_pasta","garlic","olive_oil"], "category": "main"},
    {"dish": "Pasta al Pomodoro", "ingredients": ["dry_pasta","tomato_sauce","basil"], "category": "main"},
    {"dish": "Mushroom Cream Pasta", "ingredients": ["fresh_pasta","mushroom","cream","butter"], "category": "main"},
    {"dish": "Pesto Pasta", "ingredients": ["fresh_pasta","pesto"], "category": "main"},
    {"dish": "Lasagna", "ingredients": ["lasagna_sheets","ground_beef","tomato_sauce","mozzarella"], "category": "main"},
    {"dish": "Ravioli Ricotta Spinach", "ingredients": ["ravioli","ricotta","spinach"], "category": "main"},
    {"dish": "Tortellini Cream Sauce", "ingredients": ["tortellini","cream","parmesan","butter"], "category": "main"},
    {"dish": "Chicken Alfredo", "ingredients": ["chicken","cream","parmesan","butter"], "category": "main"},
    {"dish": "Shrimp Garlic Pasta", "ingredients": ["shrimp","dry_pasta","garlic","olive_oil"], "category": "main"},
    {"dish": "Clam Pasta", "ingredients": ["clams","dry_pasta","garlic","olive_oil"], "category": "main"},
    {"dish": "Vegetable Pasta", "ingredients": ["zucchini","eggplant","bell_pepper","onion","olive_oil"], "category": "main"},
    {"dish": "Gnocchi Pesto", "ingredients": ["gnocchi","pesto"], "category": "main"},
    {"dish": "Sausage Pasta", "ingredients": ["italian_sausage","dry_pasta","tomato_sauce"], "category": "main"},
    {"dish": "Pancetta Pasta", "ingredients": ["pancetta","dry_pasta","garlic"], "category": "main"},
    {"dish": "Herb Butter Chicken", "ingredients": ["chicken","butter","rosemary","thyme"], "category": "main"},

    # 🍰 Desserts
    {"dish": "Mascarpone Cream", "ingredients": ["mascarpone","sugar","cream"], "category": "dessert"},
    {"dish": "Sweet Ricotta Cream", "ingredients": ["ricotta","sugar","milk"], "category": "dessert"},
    {"dish": "Simple Custard", "ingredients": ["eggs","milk","sugar"], "category": "dessert"},
    {"dish": "Butter Cake Base", "ingredients": ["flour","butter","sugar","eggs"], "category": "dessert"}
    ]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu")
    for dish in MENU:
        cursor.execute(
            "INSERT INTO menu (dish, ingredients, category, active) VALUES (?, ?, ?, 1)",
            (dish["dish"], json.dumps(dish["ingredients"]), dish["category"])
        )
    conn.commit()
    conn.close()
    
    # Get items from catalog
    items = list(catalog.keys())
    
    today = datetime.now()
    
    # Initial batches
    for item in items:
        num_batches = random.randint(1, 3)
        for _ in range(num_batches):
            qty = random.randint(20, 100)
            expiry = (today + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
            add_batch(item, qty, expiry)
    
    # Simulate past 7 days with dish-based consumption
    for d in range(7, 0, -1):
        sim_date = (today - timedelta(days=d)).strftime("%Y-%m-%d")
        
        menu = get_menu()
        order_log = {}
        
        num_orders = random.randint(10, 30)
        for _ in range(num_orders):
            dish = random.choice(menu)["dish"]
            
            if dish not in order_log:
                order_log[dish] = 0
            
            order_log[dish] += 1
            consume_dish(dish, 1)
        
        log_dish_orders(order_log)
        
        # Restock logic (30% chance)
        for item in items:
            if random.random() < 0.30:
                restock_qty = random.randint(10, 50)
                expiry = (today + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
                add_batch(item, restock_qty, expiry)
    
    # Final summary
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    total_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory_batches")
    total_batches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM inventory_history")
    total_history = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dish_orders")
    total_orders = cursor.fetchone()[0]
    
    conn.close()

    print(f"Total items: {total_items}")
    print(f"Total batches: {total_batches}")
    print(f"Total history records: {total_history}")
    print(f"Total dish orders: {total_orders}")

if __name__ == "__main__":
    seed_database()
