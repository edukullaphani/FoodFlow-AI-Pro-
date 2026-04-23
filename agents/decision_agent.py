from utils.llm_client import generate

def run(signals):
    prompt = f"Based on these signals: {signals}, make a decision."
    return generate(prompt)