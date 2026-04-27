from utils.llm_client import generate


def load_prompt():
    with open("prompts/strategy_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(decision, signals):
    template = load_prompt()
    prompt = template.format(
        decision=decision,
        signals=signals
    )
    return generate(prompt)