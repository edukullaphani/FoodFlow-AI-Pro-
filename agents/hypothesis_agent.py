from utils.llm_client import generate

def run(signals):
    prompt = (
        f"Given these signals for {signals['item']}:\n"
        f"  - Consumption Rate: {signals['consumption_rate']:.2f} units/day\n"
        f"  - Days to Expiry: {signals['days_to_expiry']} days\n"
        f"  - Trend: {signals['trend']}\n\n"
        f"Analyze why the demand pattern is {signals['trend']}.\n"
        f"Provide 2-3 possible real-world causes (e.g., weekday/weekend patterns, customer behavior, seasonality).\n"
        f"Keep response concise (2-3 sentences)."
    )
    return generate(prompt)