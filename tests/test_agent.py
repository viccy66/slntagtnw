import agent as agent_module
from agent import Agent


def test_agent_answers_bonjour():
    agent = Agent()
    assert agent.run("bonjour") == "Bonjour !"


def test_agent_answers_name_question():
    agent = Agent()
    assert agent.run("Quel est ton nom ?") == "Je m'appelle Llama."


def test_agent_ignores_empty_question_without_changing_name():
    agent = Agent()
    assert agent.run("   ") == "Aucune demande saisie. Aucune action effectuée."
    assert agent.name == "Llama"


def test_agent_handles_analyze_file_intent(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "analyze_intent",
        lambda question: '{"intention": "analyze_file", "valeur": "rapport.txt"}',
    )

    agent = Agent()
    assert agent.run("Analyse le fichier rapport.txt") == (
        "J'analyse le fichier rapport.txt. Donne-moi le chemin exact ou le contenu "
        "pour que je puisse l'étudier."
    )
