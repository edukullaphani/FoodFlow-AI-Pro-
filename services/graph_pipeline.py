import pandas as pd
from langgraph.graph import StateGraph, END
from typing import TypedDict

from core.data_processor import load_data, clean_data
from core.feature_engineering import compute_consumption_rate, compute_days_to_expiry
from core.metrics import detect_trend
from agents.decision_agent import run as run_decision
from agents.explanation_agent import run as run_explanation
from agents.hypothesis_agent import run as run_hypothesis
from agents.simulation_agent import run as run_simulation
from agents.strategy_agent import run as run_strategy


class AgentState(TypedDict):
    signals: dict
    hypothesis: dict
    simulation: dict
    decision: dict
    strategy: dict
    explanation: dict


def hypothesis_node(state: AgentState) -> AgentState:
    signals = state["signals"]
    hypothesis = run_hypothesis(signals)
    # return {"hypothesis": hypothesis}
    state["hypothesis"] = hypothesis
    return state


def simulation_node(state: AgentState) -> AgentState:
    signals = state["signals"]
    hypothesis = state["hypothesis"]
    simulation = run_simulation(signals, hypothesis)
    # return {"simulation": simulation}
    state["simulation"] = simulation
    return state

def decision_node(state: AgentState) -> AgentState:
    signals = state["signals"]
    hypothesis = state["hypothesis"]
    simulation = state["simulation"]
    # decision_input = {
    #     "signals": signals,
    #     "hypothesis": hypothesis,
    #     "simulation": simulation
    # }
    decision = run_decision(signals, hypothesis, simulation)
    # return {"decision": decision}
    state["decision"] = decision
    return state


def strategy_node(state: AgentState) -> AgentState:
    decision = state["decision"]
    signals = state["signals"]
    strategy = run_strategy(decision, signals)
    # return {"strategy": strategy}
    state["strategy"] = strategy
    return state


def explanation_node(state: AgentState) -> AgentState:
    decision = state["decision"]
    signals = state["signals"]
    explanation = run_explanation(decision, signals)
    # return {"explanation": explanation}
    state["explanation"] = explanation
    return state


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("hypothesis", hypothesis_node)
    workflow.add_node("simulation", simulation_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("explanation", explanation_node)
    workflow.set_entry_point("hypothesis")
    workflow.add_edge("hypothesis", "simulation")
    workflow.add_edge("simulation", "decision")
    workflow.add_edge("decision", "strategy")
    workflow.add_edge("strategy", "explanation")
    workflow.add_edge("explanation", END)
    return workflow.compile()


def run_graph_pipeline(csv_path):
    df = load_data(csv_path)
    df = clean_data(df)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    item = df['item'].iloc[0]
    consumption_rate = compute_consumption_rate(df)
    days_to_expiry = compute_days_to_expiry(df)
    trend = detect_trend(df)
    signals = {
        "item": item,
        "consumption_rate": consumption_rate,
        "days_to_expiry": days_to_expiry,
        "trend": trend
    }
    initial_state: AgentState = {
        "signals": signals,
        "hypothesis": {},
        "simulation": {},
        "decision": {},
        "strategy": {},
        "explanation": {}
    }
    graph = build_graph()
    result = graph.invoke(initial_state)
    return result["explanation"]


import pandas as pd