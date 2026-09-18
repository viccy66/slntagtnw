from ollama import Client


def welcome_message() -> str:
    return "Bonjour, que puis-je faire ?"


def say_hello() -> str:
    return "Bonjour !"


def tell_name() -> str:
    return "Je suis un agent autonome minimal."


def ask_llm(prompt: str, json_format: bool = False) -> str:
    client = Client(host="http://localhost:11434")
    response = client.generate(
        model="llama3.2",
        prompt=prompt,
        **({"format": "json"} if json_format else {}),
    )
    return response["response"]


def analyze_intent(question: str) -> str:
    prompt = f"""
Analyse la demande de l'utilisateur.
Retourne uniquement un objet JSON avec exactement ces deux champs :
- "intention" : l'intention détectée
- "valeur" : la valeur importante à mémoriser, ou null si aucune valeur n'est présente

Pour une demande où l'utilisateur donne un nouveau nom à l'agent,
utilise l'intention "change_name" et place le nom dans "valeur".
Si l'utilisateur parle de changer le nom sans donner de nom précis,
utilise "change_name" et mets obligatoirement null dans "valeur".
N'invente jamais de nom et ne transforme pas une explication en nom.
Pour une question sur le nom de l'agent, utilise l'intention "ask_name".
Pour toute demande non reconnue, utilise "unknown".

Demande de l'utilisateur : {question}
"""
    return ask_llm(prompt, json_format=True)