import json

from tools import analyze_intent, welcome_message, ask_llm


class Agent:
    def __init__(self):
        self.name = "Llama"

    def run(self, question: str) -> str:
        raw_result = analyze_intent(question)
        result = json.loads(raw_result)

        intention = result.get("intention", "unknown")
        value = result.get("valeur")

        if intention == "change_name":
            if not value:
                return "Quel nom veux-tu me donner ?"

            self.name = value
            return f"D'accord, je m'appelle maintenant {self.name}."

        if intention == "ask_name":
            return f"Je m'appelle {self.name}."

        return ask_llm(question)

    def welcome(self) -> str:
        return welcome_message()
