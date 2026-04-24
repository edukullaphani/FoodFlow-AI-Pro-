from utils.llm_client import generate

def run(signals, hypothesis):
    prompt = (
        f"Current signals for {signals['item']}:\n"
        f"  - Consumption Rate: {signals['consumption_rate']:.2f} units/day\n"
        f"  - Days to Expiry: {signals['days_to_expiry']} days\n"
        f"  - Trend: {signals['trend']}\n\n"
        f"Hypothesis about demand: {hypothesis}\n\n"
        f"Simulate 1-2 possible future scenarios:\n"
        f"1. What happens if current {signals['trend']} trend continues?\n"
        f"2. What is the risk of expiry or stockout?\n\n"
        f"Keep output short and focused on risks."
    )
    return generate(prompt)