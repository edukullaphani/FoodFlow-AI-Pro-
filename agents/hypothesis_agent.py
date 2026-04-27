from utils.llm_client import generate


def load_prompt():
    with open("prompts/hypothesis_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def run(signals):
    template = load_prompt()
    prompt = template.format(signals=signals)
    return generate(prompt)