import json
from pathlib import Path

from tools import analyze_intent, describe_directory_content, welcome_message, ask_llm


class Agent:
    def __init__(self, history_path: str | Path = ".agent_history.jsonl"):
        self.history_path = Path(history_path)
        self.name = self._load_name()
        self.last_directory: Path | None = None
        self.last_directory_entries: list[str] = []

    def _load_name(self) -> str | None:
        try:
            entries = self.history_path.read_text(encoding="utf-8").splitlines()
        except (FileNotFoundError, OSError):
            return None

        name = None
        for entry in entries:
            try:
                event = json.loads(entry)
            except json.JSONDecodeError:
                continue

            if not isinstance(event, dict) or event.get("intention") != "change_name":
                continue

            value = event.get("valeur")
            if value and str(value).strip():
                name = str(value).strip()

        return name

    def _record_name_change(self) -> None:
        with self.history_path.open("a", encoding="utf-8") as history:
            history.write(
                json.dumps(
                    {"intention": "change_name", "valeur": self.name},
                    ensure_ascii=False,
                )
                + "\n"
            )

    def analyze_file(self, file_ref: str) -> str:
        if not file_ref or not str(file_ref).strip():
            return "Quel fichier veux-tu que j'analyse ?"

        return (
            f"J'analyse le fichier {str(file_ref).strip()}. "
            "Donne-moi le chemin exact ou le contenu pour que je puisse l'étudier."
        )

    def list_directory(self, directory_ref: str) -> str:
        if not directory_ref or not str(directory_ref).strip():
            return "Quel répertoire veux-tu que j'affiche ?"

        directory = Path(str(directory_ref).strip())
        if not directory.is_dir():
            return "Quel est le chemin exact du répertoire ?"

        entries = sorted(entry.name for entry in directory.iterdir())
        self.last_directory = directory
        self.last_directory_entries = entries
        if not entries:
            return f"Le répertoire {directory} est vide."

        return f"Contenu de {directory} :\n" + "\n".join(entries)

    def run(self, question: str) -> str:
        if not question or not question.strip():
            return "Aucune demande saisie. Aucune action effectuée."

        normalized = question.strip().lower()
        direct_path = Path(question.strip())

        if normalized in {"bonjour", "salut", "hello", "hi"}:
            return "Bonjour !"

        if direct_path.is_dir():
            return self.list_directory(str(direct_path))

        references_last_directory = (
            "ce contenu" in normalized
            or "contenu de ce répertoire" in normalized
            or "ce répertoire" in normalized
        )
        if self.last_directory is not None and "analys" in normalized and references_last_directory:
            return self.analyze_directory_content()

        if "comment t'appelles-tu" in normalized or "quel est ton nom" in normalized:
            if self.name is None:
                return "Je n'ai pas encore de nom."
            return f"Je m'appelle {self.name}."

        raw_result = analyze_intent(question)

        try:
            result = json.loads(raw_result)
        except json.JSONDecodeError:
            return "Je n'ai pas compris la demande. Peux-tu reformuler ?"

        if not isinstance(result, dict):
            return "Je n'ai pas compris la demande. Peux-tu reformuler ?"

        if set(result.keys()) != {"intention", "valeur"}:
            return "Je n'ai pas compris la demande. Peux-tu reformuler ?"

        intention = result.get("intention")
        value = result.get("valeur")

        if intention not in {
            "change_name",
            "ask_name",
            "analyze_file",
            "list_directory",
            "analyze_directory",
            "unknown",
        }:
            return "Je n'ai pas compris la demande. Peux-tu reformuler ?"

        if intention == "change_name":
            if not value or not str(value).strip():
                return "Quel nom veux-tu me donner ?"

            self.name = str(value).strip()
            self._record_name_change()
            return f"D'accord, je m'appelle maintenant {self.name}."

        if intention == "ask_name":
            return f"Je m'appelle {self.name}."

        if intention == "analyze_file":
            return self.analyze_file(value)

        if intention == "list_directory":
            return self.list_directory(value)

        if intention == "analyze_directory":
            if value and str(value).strip():
                self.list_directory(value)
            return self.analyze_directory_content()

        return ask_llm(question)

    def analyze_directory_content(self) -> str:
        if self.last_directory is None:
            return "Quel répertoire veux-tu que j'analyse ?"

        return describe_directory_content(
            str(self.last_directory), self.last_directory_entries
        )

    def welcome(self) -> str:
        return welcome_message()
