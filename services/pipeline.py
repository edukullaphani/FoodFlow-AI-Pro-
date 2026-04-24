import pandas as pd
from core.data_processor import load_data, clean_data
from core.feature_engineering import compute_consumption_rate, compute_days_to_expiry
from core.metrics import detect_trend
from agents.decision_agent import run as run_decision
from agents.explanation_agent import run as run_explanation
from agents.hypothesis_agent import run as run_hypothesis
from agents.simulation_agent import run as run_simulation
from agents.strategy_agent import run as run_strategy

def run_pipeline(csv_path):
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
    hypothesis = run_hypothesis(signals)
    simulation = run_simulation(signals, hypothesis)
    decision_input = {
        "signals": signals,
        "hypothesis": hypothesis,
        "simulation": simulation
    }
    decision = run_decision(decision_input)
    strategy = run_strategy(decision, signals)
    explanation = run_explanation(decision, signals)
    return explanation