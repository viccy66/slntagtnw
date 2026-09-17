from agent import Agent


if __name__ == "__main__":
    agent = Agent()
    print(agent.welcome())

    while True:
        question = input("Vous : ")
        if question.strip().lower() in {"quit", "exit", "q"}:
            print("Au revoir !")
            break
        print(f"Agent : {agent.run(question)}")
