import json
from pathlib import Path

from tools import (
    analyze_intent,
    analyze_project_detail,
    analyze_project_structure,
    describe_directory_content,
    welcome_message,
    ask_llm,
)


class Agent:
    def __init__(self, history_path: str | Path = ".agent_history.jsonl"):
        self.history_path = Path(history_path)
        self.name = self._load_name()
        self.last_directory: Path | None = None
        self.last_directory_entries: list[str] = []
        self.pending_intent: str | None = None

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
            self.pending_intent = None
            return "Bonjour !"

        if direct_path.is_dir():
            if self.pending_intent == "analyze_directory":
                self.pending_intent = None
                self.list_directory(str(direct_path))
                return self.analyze_directory_content()

            if self.pending_intent == "analyze_structure":
                self.pending_intent = None
                self.list_directory(str(direct_path))
                return analyze_project_structure(str(direct_path))

            self.pending_intent = None
            return self.list_directory(str(direct_path))

        references_last_directory = (
            "ce contenu" in normalized
            or "contenu de ce répertoire" in normalized
            or "ce répertoire" in normalized
        )
        asks_for_new_directory = any(
            marker in normalized
            for marker in (
                "d'un répertoire",
                "d’un répertoire",
                "un répertoire",
                "d'un dossier",
                "d’un dossier",
                "un dossier",
                "autre répertoire",
                "autre repertoire",
                "autre dossier",
            )
        ) and not references_last_directory
        if asks_for_new_directory and "analys" in normalized:
            self.pending_intent = (
                "analyze_structure" if "structure" in normalized else "analyze_directory"
            )
            return "Quel répertoire veux-tu que j'analyse ?"
        detail_topic = self._detail_topic(normalized)
        if self.last_directory is not None and detail_topic:
            return analyze_project_detail(str(self.last_directory), detail_topic)
        if (
            self.last_directory is not None
            and "structure" in normalized
            and ("analys" in normalized or "décris" in normalized or "décrit" in normalized)
        ):
            return analyze_project_structure(str(self.last_directory))
        asks_for_another_directory = any(
            marker in normalized
            for marker in (
                "autre répertoire",
                "autre repertoire",
                "autre dossier",
            )
        )
        if (
            self.last_directory is not None
            and "analys" in normalized
            and references_last_directory
            and not asks_for_another_directory
        ):
            return self.analyze_directory_content()

        if "comment t'appelles-tu" in normalized or "quel est ton nom" in normalized:
            if self.name is None:
                return "Je n'ai pas encore de nom."
            return f"Je m'appelle {self.name}."

        if (
            "structure" in normalized
            and any(marker in normalized for marker in ("répertoire", "repertoire", "dossier"))
        ):
            self.pending_intent = "analyze_structure"
            return "Quel répertoire veux-tu que j'analyse ?"

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
            self.pending_intent = None
            if value and str(value).strip():
                return self.list_directory(value)
            self.pending_intent = "list_directory"
            return "Quel répertoire veux-tu que j'affiche ?"

        if intention == "analyze_directory":
            if value and str(value).strip():
                self.pending_intent = None
                self.list_directory(value)
                return self.analyze_directory_content()

            if self.last_directory is None:
                self.pending_intent = "analyze_directory"
                return "Quel répertoire veux-tu que j'analyse ?"

            if any(
                marker in normalized
                for marker in (
                    "autre répertoire",
                    "autre repertoire",
                    "un autre répertoire",
                    "un autre repertoire",
                    "d'un autre répertoire",
                    "d'un autre repertoire",
                    "autre dossier",
                    "un autre dossier",
                    "d'un autre dossier",
                )
            ):
                self.pending_intent = "analyze_directory"
                return "Quel répertoire veux-tu que j'analyse ?"

            self.pending_intent = None
            return self.analyze_directory_content()

        self.pending_intent = None
        return ask_llm(question)

    def analyze_directory_content(self) -> str:
        if self.last_directory is None:
            return "Quel répertoire veux-tu que j'analyse ?"

        return describe_directory_content(
            str(self.last_directory), self.last_directory_entries
        )

    @staticmethod
    def _detail_topic(question: str) -> str | None:
        if not any(
            marker in question
            for marker in (
                "précis", "precis", "detail", "détail", "explique",
                "décris", "decris", "quels", "quelles", "peux-tu",
            )
        ):
            return None

        topics = (
            (("preuves", "preuve"), "preuves observables"),
            (("hypothèses", "hypotheses"), "hypothèses et déductions"),
            (("classes", "classe"), "classes et héritages"),
            (("widgets", "widget"), "widgets et interface Qt"),
            (("dépendances", "dependances"), "dépendances et inclusions"),
            (("flux",), "flux d'exécution"),
            (("limites",), "limites de l'analyse"),
            (("confiance",), "niveau de confiance et incertitudes"),
        )
        for markers, topic in topics:
            if any(marker in question for marker in markers):
                return topic
        return None

    def welcome(self) -> str:
        return welcome_message()
