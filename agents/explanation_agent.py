from utils.llm_client import generate

def run(decision, signals):
    prompt = (
        f"Given the decision: {decision}\n"
        f"And these signals:\n"
        f"  - Item: {signals['item']}\n"
        f"  - Consumption Rate: {signals['consumption_rate']:.2f} units/day\n"
        f"  - Days to Expiry: {signals['days_to_expiry']} days\n"
        f"  - Trend: {signals['trend']}\n\n"
        f"Provide a concise business-friendly explanation that includes:\n"
        f"1. Why this decision was made\n"
        f"2. What risk exists (expiry, waste, etc.)\n"
        f"3. One actionable suggestion\n"
        f"Keep it to 2-3 sentences."
    )
    return generate(prompt)