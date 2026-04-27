from utils.llm_client import generate


def load_prompt():
    with open("prompts/explanation_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(decision, signals):
    # if decision and "action:" in decision:
    #     decision = decision.split("action:")[-1].strip()
    template = load_prompt()
    prompt = template.format(
        decision=decision,
        item=signals.get("item", "unknown"),
        consumption_rate=signals.get("consumption_rate", 0),
        days_to_expiry=signals.get("days_to_expiry", 0),
        trend=signals.get("trend", "unknown")
    )
    return generate(prompt, max_tokens=2000)