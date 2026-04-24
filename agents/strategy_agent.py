from utils.llm_client import generate

def run(decision, signals):
    prompt = (
        f"Decision: {decision}\n\n"
        f"Current signals for {signals['item']}:\n"
        f"  - Consumption Rate: {signals['consumption_rate']:.2f} units/day\n"
        f"  - Days to Expiry: {signals['days_to_expiry']} days\n"
        f"  - Trend: {signals['trend']}\n\n"
        f"Suggest 1-3 practical business actions such as:\n"
        f"- promotions for near-expiry items\n"
        f"- adjust order quantities\n"
        f"- menu or pricing adjustments\n\n"
        f"Be concise and business-focused."
    )
    return generate(prompt)