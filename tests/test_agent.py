import agent as agent_module
import tools as tools_module
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


def test_agent_requests_path_when_user_asks_for_another_directory(monkeypatch, tmp_path):
    (tmp_path / "agent.py").write_text("class Agent: pass", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "describe_directory_content",
        lambda directory, entries: f"Analyse de {directory} avec {entries}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Analyse le contenu d'un autre répertoire") == (
        "Quel répertoire veux-tu que j'analyse ?"
    )


def test_agent_analyzes_directory_when_user_provides_path_after_prompt(monkeypatch, tmp_path):
    (tmp_path / "agent.py").write_text("class Agent: pass", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "analyze_intent",
        lambda question: '{"intention": "analyze_directory", "valeur": null}',
    )
    monkeypatch.setattr(
        agent_module,
        "describe_directory_content",
        lambda directory, entries: f"Analyse de {directory} avec {entries}",
    )

    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run("Analyse le contenu d'un autre répertoire") == (
        "Quel répertoire veux-tu que j'analyse ?"
    )
    assert agent.run(str(tmp_path)) == f"Analyse de {tmp_path} avec ['agent.py']"


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


def test_agent_uses_structure_analysis_for_current_directory(monkeypatch, tmp_path):
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "analyze_project_structure",
        lambda directory: f"Structure de {directory} lue par qwen3:4b",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Analyse la structure de ce répertoire") == (
        f"Structure de {tmp_path} lue par qwen3:4b"
    )


def test_agent_preserves_structure_request_while_waiting_for_path(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_structure",
        lambda directory: f"Structure de {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run("J'aimerais que tu analyses la structure d'un répertoire") == (
        "Quel répertoire veux-tu que j'analyse ?"
    )
    assert agent.run(str(tmp_path)) == f"Structure de {tmp_path}"


def test_agent_does_not_reuse_directory_for_new_structure_request(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_structure",
        lambda directory: f"Structure de {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")
    agent.run(str(tmp_path))

    assert agent.run("J'aimerais que tu analyses la structure d'un répertoire.") == (
        "Quel répertoire veux-tu que j'analyse ?"
    )


def test_agent_answers_precise_widget_question_from_current_directory(monkeypatch, tmp_path):
    (tmp_path / "calculatorform.ui").write_text(
        "<widget class='QSpinBox' name='inputSpinBox1'/>", encoding="utf-8"
    )
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Précision {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Peux-tu préciser quels widgets sont utilisés ?") == (
        f"Précision widgets et interface Qt pour {tmp_path}"
    )


def test_agent_answers_architecture_question_from_current_directory(monkeypatch, tmp_path):
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (tmp_path / "widget.h").write_text("class Widget {};", encoding="utf-8")
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Architecture {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    agent.run(str(tmp_path))

    assert agent.run("Peux-tu me décrire l'architecture du projet ?") == (
        f"Architecture architecture du projet pour {tmp_path}"
    )


def test_agent_requests_directory_for_unspecified_project_architecture(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Architecture {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run("Peux-tu me décrire l'architecture d'un projet ?") == (
        "Quel répertoire veux-tu que j'analyse ?"
    )
    assert agent.run(str(tmp_path)) == f"Architecture architecture du projet pour {tmp_path}"


def test_agent_analyzes_architecture_for_embedded_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Architecture {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run(
        f"Peux-tu me décrire l'architecture du projet {tmp_path} ?"
    ) == f"Architecture architecture du projet pour {tmp_path}"


def test_agent_answers_execution_flow_question_from_current_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Flux {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")
    agent.run(str(tmp_path))

    assert agent.run(
        "Peux-tu m'expliquer le flux d'exécution du projet ?"
    ) == f"Flux flux d'exécution et point d'entrée pour {tmp_path}"


def test_agent_requests_directory_for_unspecified_execution_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Flux {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run(
        "Peux-tu m'expliquer le flux d'exécution d'un projet ?"
    ) == "Quel répertoire veux-tu que j'analyse ?"
    assert agent.run(str(tmp_path)) == (
        f"Flux flux d'exécution et point d'entrée pour {tmp_path}"
    )


def test_agent_analyzes_execution_flow_for_embedded_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Flux {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")

    assert agent.run(
        f"Peux-tu m'expliquer le flux d'exécution du projet {tmp_path} ?"
    ) == f"Flux flux d'exécution et point d'entrée pour {tmp_path}"


def test_agent_requests_visual_execution_flow_from_current_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(
        agent_module,
        "analyze_project_detail",
        lambda directory, topic: f"Visuel {topic} pour {directory}",
    )
    agent = Agent(tmp_path / "history.jsonl")
    agent.run(str(tmp_path))

    assert agent.run(
        "Peux-tu représenter visuellement le flux d'exécution du projet ?"
    ) == f"Visuel visualisation Mermaid du flux d'exécution pour {tmp_path}"


def test_visual_execution_flow_prompt_requests_mermaid(monkeypatch, tmp_path):
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "diagramme OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    assert tools_module.analyze_project_detail(
        str(tmp_path), "visualisation Mermaid du flux d'exécution"
    ) == "diagramme OK"
    assert "bloc" in captured["prompt"]
    assert "mermaid" in captured["prompt"]


def test_visual_execution_flow_prompt_prioritizes_global_flow_and_unique_nodes(
    monkeypatch, tmp_path
):
    (tmp_path / "main.cpp").write_text(
        "int main() { QApplication app; CalculatorForm form; form.show(); return app.exec(); }",
        encoding="utf-8",
    )
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "diagramme OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(
        str(tmp_path), "visualisation Mermaid du flux d'exécution"
    )

    assert "flux global observé" in captured["prompt"]
    assert "identifiants de nœuds Mermaid uniques" in captured["prompt"]
    assert "app.exec()" in captured["prompt"]
    assert "1:11" in captured["prompt"]


def test_execution_flow_prompt_requires_ordered_runtime_steps(monkeypatch, tmp_path):
    (tmp_path / "main.cpp").write_text(
        "int main() { QApplication app; CalculatorForm form; form.show(); return app.exec(); }",
        encoding="utf-8",
    )
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "flux OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(
        str(tmp_path), "flux d'exécution et point d'entrée"
    )

    assert "pas seulement" in captured["prompt"]
    assert "création de l'application" in captured["prompt"]
    assert "`show()`" in captured["prompt"]
    assert "`app.exec()`" in captured["prompt"]


def test_execution_flow_prompt_distinguishes_framework_callbacks(
    monkeypatch, tmp_path
):
    (tmp_path / "main.cpp").write_text(
        "int main() { QApplication app; MainWidget widget; widget.show(); return app.exec(); }",
        encoding="utf-8",
    )
    (tmp_path / "mainwidget.cpp").write_text(
        "void MainWidget::initializeGL() {}", encoding="utf-8"
    )
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "flux OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(
        str(tmp_path), "flux d'exécution et point d'entrée"
    )

    assert "flux confirmé par les appels de `main()`" in captured["prompt"]
    assert "callbacks ou étapes de" in captured["prompt"]
    assert "moment exact" in captured["prompt"]


def test_execution_flow_prompt_distinguishes_setup_order_from_internal_details(
    monkeypatch, tmp_path
):
    (tmp_path / "main.cpp").write_text(
        "int main() { QApplication app; CalculatorForm form; form.show(); return app.exec(); }",
        encoding="utf-8",
    )
    (tmp_path / "calculatorform.cpp").write_text(
        "CalculatorForm::CalculatorForm() { setupUi(this); }", encoding="utf-8"
    )
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "flux OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(
        str(tmp_path), "flux d'exécution et point d'entrée"
    )

    assert "présente cet ordre comme un fait observé" in captured["prompt"]
    assert "détail interne de création" in captured["prompt"]


def test_visual_execution_flow_prompt_allows_one_diagram_only_in_section_two(
    monkeypatch, tmp_path
):
    (tmp_path / "main.cpp").write_text(
        "int main() { QApplication app; MainWidget widget; widget.show(); return app.exec(); }",
        encoding="utf-8",
    )
    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "diagramme OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(
        str(tmp_path), "visualisation Mermaid du flux d'exécution"
    )

    assert "sans titre" in captured["prompt"]
    assert "La section 2 doit contenir" in captured["prompt"]
    assert "ne doit apparaître nulle part ailleurs" in captured["prompt"]


def test_analyze_project_detail_excludes_generated_qt_resource_artifacts(monkeypatch, tmp_path):
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")
    (tmp_path / "composition.cpp").write_text(
        "class CompositionWidget : public QWidget {};", encoding="utf-8"
    )
    (tmp_path / "qrc_composition.cpp").write_text(
        "static const unsigned char qt_resource_data[] = { 0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a };",
        encoding="utf-8",
    )
    (tmp_path / "moc_composition.cpp").write_text(
        "class MocGenerated {};", encoding="utf-8"
    )

    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "analyse OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    result = tools_module.analyze_project_detail(str(tmp_path), "structure")

    assert result == "analyse OK"
    assert "qrc_composition.cpp" not in captured["prompt"]
    assert "moc_composition.cpp" not in captured["prompt"]
    assert "main.cpp" in captured["prompt"]
    assert "composition.cpp" in captured["prompt"]


def test_analyze_project_detail_keeps_relevant_generated_ui_header(monkeypatch, tmp_path):
    (tmp_path / "calculatorform.ui").write_text(
        "<widget class='QWidget' name='CalculatorForm' />", encoding="utf-8"
    )
    (tmp_path / "ui_calculatorform.h").write_text(
        "class Ui_CalculatorForm { public: QWidget *widget; };", encoding="utf-8"
    )
    (tmp_path / "main.cpp").write_text("int main() { return 0; }", encoding="utf-8")

    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "analyse OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    result = tools_module.analyze_project_detail(str(tmp_path), "structure")

    assert result == "analyse OK"
    assert "ui_calculatorform.h" in captured["prompt"]
    assert "calculatorform.ui" in captured["prompt"]


def test_analyze_project_detail_prioritizes_main_and_ignores_generated_files(
    monkeypatch, tmp_path
):
    (tmp_path / "main.cpp").write_text(
        "int main() { return 0; }", encoding="utf-8"
    )
    for index in range(30):
        (tmp_path / f"component_{index:02d}.cpp").write_text(
            f"class Component{index} {{}};", encoding="utf-8"
        )
    for index in range(10):
        (tmp_path / f"moc_component_{index:02d}.cpp").write_text(
            "class Generated {};", encoding="utf-8"
        )

    captured = {}

    def fake_ask_llm(prompt, json_format=False, model=None):
        captured["prompt"] = prompt
        return "analyse OK"

    monkeypatch.setattr(tools_module, "ask_llm", fake_ask_llm)

    tools_module.analyze_project_detail(str(tmp_path), "flux d'exécution")

    assert "--- main.cpp ---" in captured["prompt"]
    assert "relevé prioritaire des points d'entrée globaux" in captured["prompt"]
    assert "moc_component_00.cpp" not in captured["prompt"]
