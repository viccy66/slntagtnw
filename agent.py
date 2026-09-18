import json

from tools import analyze_intent, welcome_message, ask_llm


class Agent:
    def __init__(self):
        self.name = "Llama"

    def analyze_file(self, file_ref: str) -> str:
        if not file_ref or not str(file_ref).strip():
            return "Quel fichier veux-tu que j'analyse ?"

        return (
            f"J'analyse le fichier {str(file_ref).strip()}. "
            "Donne-moi le chemin exact ou le contenu pour que je puisse l'étudier."
        )

    def run(self, question: str) -> str:
        if not question or not question.strip():
            return "Aucune demande saisie. Aucune action effectuée."

        normalized = question.strip().lower()

        if normalized in {"bonjour", "salut", "hello", "hi"}:
            return "Bonjour !"

        if "comment t'appelles-tu" in normalized or "quel est ton nom" in normalized:
            return f"Je m'appelle {self.name}."

        raw_result = analyze_intent(question)
        result = json.loads(raw_result)

        intention = result.get("intention", "unknown")
        value = result.get("valeur")

        if intention == "change_name":
            if not value or not str(value).strip():
                return "Quel nom veux-tu me donner ?"

            self.name = str(value).strip()
            return f"D'accord, je m'appelle maintenant {self.name}."

        if intention == "ask_name":
            return f"Je m'appelle {self.name}."

        if intention == "analyze_file":
            return self.analyze_file(value)

        return ask_llm(question)

    def welcome(self) -> str:
        return welcome_message()
