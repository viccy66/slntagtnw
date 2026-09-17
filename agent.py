import json

from tools import analyze_intent, welcome_message, ask_llm


class Agent:
    def run(self, question: str) -> str:
        raw_result = analyze_intent(question)
        result = json.loads(raw_result)

        intention = result.get("intention", "unknown")
        value = result.get("valeur")

        return f"Intention détectée : {intention}\nValeur à mémoriser : {value}"
#        return ask_llm(question)

    def welcome(self) -> str:
        return welcome_message()
