import streamlit as st
import sqlite3
import pandas as pd
import json

from scripts.db import DB_PATH


def load_inventory():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM inventory", conn)
    conn.close()
    return df


def load_orders():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM dish_orders", conn)
    conn.close()
    return df


def load_evaluation():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM evaluation", conn)
    conn.close()
    return df


def load_runs(limit=20):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, timestamp, signals, analysis, decisions, menu_actions, explanation
        FROM runs
        ORDER BY id DESC
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(limit,))
    conn.close()
    return df


def load_menu():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT dish, ingredients, category, active FROM menu", conn)
    conn.close()
    return df


def parse_json_field(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def normalize_decisions(decisions):
    normalized = {}
    if not isinstance(decisions, dict):
        return normalized
    for item, val in decisions.items():
        if isinstance(val, dict):
            normalized[item] = val.get("action", "safe")
        elif isinstance(val, str):
            normalized[item] = val
        else:
            normalized[item] = "safe"
    return normalized


def build_action_table(decisions):
    decision_map = normalize_decisions(decisions)
    rows = [{"item": item, "action": action} for item, action in decision_map.items()]
    if not rows:
        return pd.DataFrame(columns=["item", "action"])
    df = pd.DataFrame(rows)
    return df.sort_values(by=["action", "item"]).reset_index(drop=True)


def build_inventory_priority_table(inventory_df, decisions):
    decision_map = normalize_decisions(decisions)
    if inventory_df.empty:
        return pd.DataFrame(columns=["item", "stock", "action"])
    table = inventory_df.copy()
    table["action"] = table["item"].map(lambda x: decision_map.get(x, "safe"))
    action_rank = {"use_now": 0, "monitor": 1, "safe": 2}
    table["priority_rank"] = table["action"].map(lambda a: action_rank.get(a, 3))
    table = table.sort_values(by=["priority_rank", "stock"], ascending=[True, False])
    return table[["item", "stock", "action"]].reset_index(drop=True)


def build_effectiveness_summary(eval_df):
    if eval_df.empty:
        return pd.DataFrame(columns=["effectiveness", "count"])
    return (
        eval_df.groupby("effectiveness")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )


def parse_ingredients(ingredients_value):
    if isinstance(ingredients_value, list):
        return ingredients_value
    if isinstance(ingredients_value, str):
        try:
            parsed = json.loads(ingredients_value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return []
    return []


def build_signals_table(signals):
    """Convert signals dict to a DataFrame table."""
    if not signals or not isinstance(signals, dict):
        return pd.DataFrame(columns=["item", "signal_type", "value"])
    rows = []
    for item, value in signals.items():
        signal_type = "unknown"
        val = ""
        if isinstance(value, dict):
            signal_type = value.get("type", "dict")
            val = str(value)
        elif isinstance(value, (str, int, float)):
            signal_type = "value"
            val = str(value)
        rows.append({"item": item, "signal_type": signal_type, "value": val})
    return pd.DataFrame(rows).sort_values("item").reset_index(drop=True)


def build_menu_actions_table(menu_actions):
    """Convert menu_actions dict to a DataFrame table."""
    if not menu_actions or not isinstance(menu_actions, dict):
        return pd.DataFrame(columns=["action_type", "dish_name"])
    rows = []
    # menu_actions has keys: add_dishes, remove_dishes, modify_dishes
    for action_type, dish_list in menu_actions.items():
        if isinstance(dish_list, list):
            for dish in dish_list:
                rows.append({"action_type": action_type, "dish_name": str(dish)})
        elif isinstance(dish_list, str):
            rows.append({"action_type": action_type, "dish_name": dish_list})
    if not rows:
        return pd.DataFrame(columns=["action_type", "dish_name"])
    return pd.DataFrame(rows).sort_values("action_type").reset_index(drop=True)


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FoodFlow Operations",
    layout="wide"
)

# --- UTILITY-FIRST STYLING (SQUARE CORNERS) ---
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: Arial, sans-serif;
    }
    * {
        border-radius: 0 !important;
    }
    div[data-baseweb="select"] > div,
    div[data-testid="stMetric"],
    div[data-testid="stDataFrame"],
    div.stButton > button,
    .stAlert {
        border-radius: 0 !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- LOAD DATA ---
inventory_df = load_inventory()
orders_df = load_orders()
eval_df = load_evaluation()
runs_df = load_runs()
menu_df = load_menu()

# --- HEADER ---
st.title("FoodFlow Operations Dashboard")
st.caption("Operational view for kitchen, inventory, and manager decisions")

# --- RUN SELECTOR ---
run_list = runs_df["id"].tolist() if not runs_df.empty else []
if not run_list:
    st.warning("No pipeline runs found yet. Run `python -m app.main` first.")
    selected_run_id = None
else:
    selected_run_id = st.selectbox(
        "Select operational run",
        options=run_list,
        format_func=lambda run_id: f"Run {run_id}",
        index=0
    )

# --- PARSE SELECTED RUN DATA ---
if selected_run_id:
    selected_row = runs_df[runs_df["id"] == selected_run_id].iloc[0]
    selected_signals = parse_json_field(selected_row["signals"])
    selected_analysis = parse_json_field(selected_row["analysis"])
    selected_decisions = parse_json_field(selected_row["decisions"])
    selected_menu_actions = parse_json_field(selected_row["menu_actions"])
    selected_explanation = selected_row["explanation"] if selected_row["explanation"] is not None else ""
else:
    selected_signals = {}
    selected_analysis = {}
    selected_decisions = {}
    selected_menu_actions = {}
    selected_explanation = ""

# ============================================================
# SECTION 1: LLM OUTPUTS (TOP - PRIORITY DISPLAY)
# ============================================================
st.markdown("---")
st.header("🤖 AI/LLM Outputs")

# --- EXPLANATION (Most Important) ---
st.subheader("📝 Operational Explanation")
if selected_explanation:
    if isinstance(selected_explanation, str):
        st.info(selected_explanation)
    else:
        st.info(str(selected_explanation))
else:
    st.info("No explanation available for selected run.")

# --- AI DECISIONS ---
st.subheader("🎯 AI Decisions")
if selected_decisions:
    decision_df = build_action_table(selected_decisions)
    st.dataframe(decision_df, use_container_width=True, hide_index=True)
else:
    st.info("No decisions available for selected run.")

# --- MENU ACTIONS ---
st.subheader("🍽️ Menu Optimization Actions")
if selected_menu_actions:
    menu_actions_df = build_menu_actions_table(selected_menu_actions)
    st.dataframe(menu_actions_df, use_container_width=True, hide_index=True)
else:
    st.info("No menu actions available for selected run.")

# --- SIGNALS ---
# st.subheader("📡 Inventory Signals")
# if selected_signals:
#     signals_df = build_signals_table(selected_signals)
#     st.dataframe(signals_df, use_container_width=True, hide_index=True)
# else:
#     st.info("No signals available for selected run.")

# ============================================================
# SECTION 2: KPI METRICS
# ============================================================
st.header("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Inventory Items", len(inventory_df))

col2.metric(
    "Total Orders Logged",
    int(orders_df["quantity"].sum()) if not orders_df.empty else 0
)

col3.metric(
    "Bad Outcomes",
    len(eval_df[eval_df["effectiveness"] == "bad"]) if not eval_df.empty else 0
)

col4.metric(
    "Good Outcomes",
    len(eval_df[eval_df["effectiveness"] == "good"]) if not eval_df.empty else 0
)

st.markdown("---")

# ============================================================
# SECTION 3: DATA TABLES & VISUALIZATIONS
# ============================================================
st.header("📦 Inventory Data")

ops_left, ops_right = st.columns([1.4, 1])

with ops_left:
    st.subheader("Inventory Action Queue")
    queue_df = build_inventory_priority_table(inventory_df, selected_decisions)
    st.dataframe(queue_df, use_container_width=True, hide_index=True)

    st.subheader("Top Dishes by Orders")
    if orders_df.empty:
        st.info("No dish orders available.")
    else:
        orders_summary = (
            orders_df.groupby("dish")["quantity"]
            .sum()
            .reset_index()
            .sort_values("quantity", ascending=False)
            .head(15)
        )
        st.dataframe(orders_summary, use_container_width=True, hide_index=True)

with ops_right:
    st.subheader("Evaluation Outcomes")
    eff_summary = build_effectiveness_summary(eval_df)
    if eff_summary.empty:
        st.info("No evaluation data available.")
    else:
        st.bar_chart(eff_summary.set_index("effectiveness")["count"])

    st.subheader("Menu Status")
    if menu_df.empty:
        st.info("No menu records available.")
    else:
        menu_df = menu_df.copy()
        menu_df["is_active"] = menu_df["active"].apply(lambda x: "yes" if int(x) == 1 else "no")
        menu_df["ingredient_count"] = menu_df["ingredients"].apply(lambda x: len(parse_ingredients(x)))
        st.dataframe(
            menu_df[["dish", "category", "is_active", "ingredient_count"]],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Selected Run Buckets")
    at_risk_count = len(selected_analysis.get("at_risk", [])) if isinstance(selected_analysis, dict) else 0
    overstock_count = len(selected_analysis.get("overstock", [])) if isinstance(selected_analysis, dict) else 0
    safe_count = len(selected_analysis.get("safe", [])) if isinstance(selected_analysis, dict) else 0
    b1, b2, b3 = st.columns(3)
    b1.metric("At Risk", at_risk_count)
    b2.metric("Overstock", overstock_count)
    b3.metric("Safe", safe_count)

st.markdown("---")

# ============================================================
# SECTION 4: INVENTORY ANALYSIS (AT THE END)
# ============================================================
st.header("🔍 Inventory Analysis")

col_analyze_1, col_analyze_2 = st.columns(2)
with col_analyze_1:
    if selected_analysis:
        at_risk = selected_analysis.get("at_risk", [])
        overstock = selected_analysis.get("overstock", [])
        
        st.markdown("**At Risk Items:**")
        st.write(at_risk if at_risk else "None")
        
        st.markdown("**Overstock Items:**")
        st.write(overstock if overstock else "None")
    else:
        st.info("No analysis data available.")

with col_analyze_2:
    if selected_analysis:
        safe_items = selected_analysis.get("safe", [])
        
        st.markdown("**Safe Items:**")
        st.write(safe_items if safe_items else "None")
    else:
        st.info("No analysis data available.")