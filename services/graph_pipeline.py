import pandas as pd
from langgraph.graph import StateGraph, END
from typing import TypedDict

from core.data_processor import load_data
from core.inventory_analysis import analyze_inventory
from agents.batch_reasoning_agent import run as run_batch_reasoning
from agents.explanation_agent import run as run_explanation
from agents.menu_optimization_agent import run as run_menu_optimization
from scripts.db import init_db, get_inventory_state, save_run, save_evaluation, get_menu, consume_dish, log_dish_orders, apply_menu_actions
import random
from core.evaluation import evaluate_day, get_item_effectiveness
from core.preprocessing import build_signals


class AgentState(TypedDict):
    signals: dict
    analysis: dict
    reasoning: dict
    decisions: dict
    menu_actions: dict
    explanation: dict


def batch_reasoning_node(state: AgentState) -> AgentState:
    reasoning = run_batch_reasoning(state["signals"], state["analysis"])
    state["reasoning"] = reasoning
    return state


def decision_node(state: AgentState) -> AgentState:
    analysis = state["analysis"]
    decisions = {}
    
    # --- Adaptive Learning ---
    scores = get_item_effectiveness()

    for item in state["signals"]:
        base_decision = "safe"
        
        if item in analysis.get("at_risk", []):
            base_decision = "use_now"
        elif item in analysis.get("overstock", []):
            base_decision = "monitor"
        
        # Escalate near-expiry items to use_now even if currently overstock/monitor.
        # This increases proactive turnover and reduces expiry risk.
        item_signals = state["signals"].get(item, {})
        days_to_expiry = item_signals.get("days_to_expiry", 999)
        if days_to_expiry <= 2:
            base_decision = "use_now"
        
        # --- ADAPTIVE ADJUSTMENT ---
        score = scores.get(item, 0)
        
        if score < -2:
            # downgrade bad-performing decisions
            base_decision = "monitor"
        
        elif score > 3:
            # reinforce good decisions
            base_decision = "use_now"
        
        decisions[item] = {"action": base_decision}

    # Debug check
    for item, val in decisions.items():
        if not isinstance(val, dict):
            raise ValueError(f"Decision for {item} is not dict: {val}")

    state["decisions"] = decisions
    return state


def menu_optimization_node(state: AgentState) -> AgentState:
    current_menu = get_menu()
    menu_actions = run_menu_optimization(
        state["analysis"],
        state["decisions"],
        current_menu,
    )
    state["menu_actions"] = menu_actions
    return state


def explanation_node(state: AgentState) -> AgentState:
    explanation = run_explanation(
        state["analysis"],
        state["decisions"],
        state["menu_actions"]
    )

    # Flatten explanation if returned as dict
    if isinstance(explanation, dict):
        explanation = explanation.get("explanation", "")

    state["explanation"] = explanation
    return state


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("reasoning", batch_reasoning_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("menu", menu_optimization_node)
    workflow.add_node("explanation", explanation_node)

    workflow.set_entry_point("reasoning")

    workflow.add_edge("reasoning", "decision")
    workflow.add_edge("decision", "menu")
    workflow.add_edge("menu", "explanation")
    workflow.add_edge("explanation", END)

    return workflow.compile()


def get_weighted_menu(menu, decisions):
    """
    Assign weights to dishes based on decision priority.
    """
    weighted = []

    for dish in menu:
        ingredients = dish["ingredients"]

        weight = 1  # default

        for item in ingredients:
            action = decisions.get(item, {}).get("action")

            if action == "use_now":
                weight += 3
            elif action == "monitor":
                weight += 1
            elif action == "safe":
                weight -= 0.2

        # Prevent zero or negative weights
        weight = max(weight, 0.1)

        weighted.append((dish, weight))

    return weighted


def weighted_choice(weighted_menu):
    dishes = [d["dish"] for d, _ in weighted_menu]
    weights = [w for _, w in weighted_menu]

    return random.choices(dishes, weights=weights, k=1)[0]


def run_graph_pipeline(csv_path=None):
    # Initialize DB Layer
    init_db()
    
    # Get current state
    inventory_state = get_inventory_state()
    
    # Handle empty DB by loading CSV if provided
    if not inventory_state and csv_path:
        from scripts.db import add_batch
        df = load_data(csv_path)
        for _, row in df.iterrows():
            add_batch(row['item'], row['consumption'], row['expiry_date'])
        inventory_state = get_inventory_state()

    # Preprocessing
    signals_dict = build_signals(inventory_state)
    analysis = analyze_inventory(signals_dict)
    
    initial_state: AgentState = {
        "signals": signals_dict,
        "analysis": analysis,
        "reasoning": {},
        "decisions": {},
        "menu_actions": {},
        "explanation": {}
    }
    
    graph = build_graph()
    result = graph.invoke(initial_state)
    decisions = result.get("decisions", {})
    menu_actions = result.get("menu_actions", {})
    menu_apply_summary = apply_menu_actions(menu_actions, decisions, signals_dict)
    result["menu_apply_summary"] = menu_apply_summary
    
    # --- Simulation Layer ---
    menu = get_menu()

    order_log = {}

    # Scale order volume with risk level to increase targeted inventory turnover.
    at_risk_count = len(analysis.get("at_risk", []))
    min_orders = 20 + min(10, at_risk_count // 3)
    max_orders = 50 + min(20, at_risk_count // 2)
    num_orders = random.randint(min_orders, max_orders)

    weighted_menu = get_weighted_menu(menu, decisions)

    for _ in range(num_orders):
        dish = weighted_choice(weighted_menu)

        print(f"[ORDER] {dish}")

        if dish not in order_log:
            order_log[dish] = 0

        order_log[dish] += 1

        consume_dish(dish, 1)

    log_dish_orders(order_log)
    
    # Persistent output
    save_run(result)
    
    # Evaluation Layer
    current_state = get_inventory_state()
    records = evaluate_day(inventory_state, current_state, result.get("decisions", {}), result.get("analysis", {}))
    save_evaluation(records)
    
    return {
        "explanation": result.get("explanation", ""),
        "decisions": result.get("decisions"),
        "orders": order_log
    }