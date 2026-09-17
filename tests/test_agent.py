from agent import Agent


def test_agent_answers_bonjour():
    agent = Agent()
    assert agent.run("bonjour") == "Bonjour !"


def test_agent_answers_name_question():
    agent = Agent()
    assert agent.run("Comment t'appelles-tu ?") == "Je suis un agent autonome minimal."
