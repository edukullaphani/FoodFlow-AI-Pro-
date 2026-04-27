from utils.llm_client import generate


def load_prompt():
    with open("prompts/hypothesis_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals):
    template = load_prompt()
    prompt = template.format(
        item=signals['item'],
        consumption_rate=signals['consumption_rate'],
        days_to_expiry=signals['days_to_expiry'],
        trend=signals['trend']
    )
    return generate(prompt)