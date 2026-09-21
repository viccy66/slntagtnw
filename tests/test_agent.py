import agent as agent_module
from agent import Agent


def test_agent_answers_bonjour():
    agent = Agent()
    assert agent.run("bonjour") == "Bonjour !"


def test_agent_answers_name_question(tmp_path):
    agent = Agent(tmp_path / "history.jsonl")
    assert agent.run("Quel est ton nom ?") == "Je n'ai pas encore de nom."


def test_agent_ignores_empty_question_without_changing_name(tmp_path):
    agent = Agent(tmp_path / "history.jsonl")
    assert agent.run("   ") == "Aucune demande saisie. Aucune action effectuée."
    assert agent.name is None


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


def test_agent_reloads_name_from_history(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_intent",
        lambda question: '{"intention": "change_name", "valeur": "Sayent"}',
    )
    history_path = tmp_path / "agent_history.jsonl"

    first_agent = Agent(history_path)
    assert first_agent.run("Donne-moi un nouveau nom") == (
        "D'accord, je m'appelle maintenant Sayent."
    )

    second_agent = Agent(history_path)
    assert second_agent.run("Quel est ton nom ?") == "Je m'appelle Sayent."


def test_agent_lists_existing_directory(tmp_path):
    (tmp_path / "rapport.txt").write_text("contenu", encoding="utf-8")
    (tmp_path / "notes").mkdir()

    agent = Agent(tmp_path / "history.jsonl")
    result = agent.run(str(tmp_path))

    assert result == f"Contenu de {tmp_path} :\nnotes\nrapport.txt"


def test_agent_requests_directory_path_when_model_invents_invalid_path(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "analyze_intent",
        lambda question: (
            '{"intention": "list_directory", '
            '"valeur": "/home/user/repositories"}'
        ),
    )

    agent = Agent()

    assert agent.run("Affiche le contenu d'un répertoire") == (
        "Quel est le chemin exact du répertoire ?"
    )


def test_agent_uses_last_directory_for_content_analysis(monkeypatch, tmp_path):
    (tmp_path / "rapport.txt").write_text("contenu", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "describe_directory_content",
        lambda directory, entries: f"Analyse de {directory} avec {entries}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Peux-tu analyser ce contenu ?") == (
        f"Analyse de {tmp_path} avec ['rapport.txt']"
    )


def test_agent_uses_last_directory_for_directory_content_analysis(monkeypatch, tmp_path):
    (tmp_path / "agent.py").write_text("class Agent: pass", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "describe_directory_content",
        lambda directory, entries: f"Analyse de {directory} avec {entries}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Analyse le contenu de ce répertoire") == (
        f"Analyse de {tmp_path} avec ['agent.py']"
    )


def test_agent_distinguishes_list_from_analyze_directory_intentions(monkeypatch, tmp_path):
    (tmp_path / "agent.py").write_text("class Agent: pass", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "analyze_intent",
        lambda question: (
            '{"intention": "analyze_directory", "valeur": "' + str(tmp_path) + '"}'
        ),
    )
    monkeypatch.setattr(
        agent_module,
        "describe_directory_content",
        lambda directory, entries: f"Analyse de {directory} avec {entries}",
    )

    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run("Que peux-tu me dire sur ce répertoire ?") == (
        f"Analyse de {tmp_path} avec ['agent.py']"
    )
