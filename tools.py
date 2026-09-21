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

Règles strictes :
- Réponds uniquement avec du JSON brut, sans blocs de code, sans explication, sans commentaire.
- N'invente jamais de chemin, de fichier ou de nom : si aucun n'est explicitement donné par
  l'utilisateur, mets null dans "valeur".
- "fichier" et "répertoire" sont deux choses différentes. Un répertoire contient plusieurs éléments
  et se liste ou s'explore ; un fichier est un élément unique que l'on ouvre ou que l'on lit.
  N'utilise jamais "analyze_file" pour une demande qui parle d'un répertoire ou d'un dossier.
- Si l'utilisateur demande d'analyser, d'ouvrir ou de lire un fichier précis, utilise l'intention
  "analyze_file" et place son chemin ou son nom dans "valeur".
- Si l'utilisateur demande seulement d'afficher, de lister ou de montrer le contenu d'un répertoire,
  utilise l'intention "list_directory" et place son chemin dans "valeur".
- Si l'utilisateur demande d'analyser, de décrire ou d'identifier la nature d'un répertoire (pas
  seulement d'en afficher la liste), utilise l'intention "analyze_directory" et place son chemin dans
  "valeur".
- Si l'utilisateur donne un nouveau nom à l'agent, utilise l'intention "change_name" et place le nom dans "valeur".
- Si l'utilisateur parle de changer le nom sans donner de nom précis, utilise "change_name" et mets obligatoirement 
  null dans "valeur".
- Si l'utilisateur demande le nom de l'agent, utilise l'intention "ask_name".
- Si la demande est non reconnue ou vide, utilise "unknown" et mets null dans "valeur".
- Ne renvoie jamais de texte libre.

Exemples :
Demande : "affiche le contenu d'un répertoire"
Réponse : {{"intention": "list_directory", "valeur": null}}

Demande : "analyse le contenu d'un répertoire"
Réponse : {{"intention": "analyze_directory", "valeur": null}}

Demande : "analyse le fichier rapport.txt"
Réponse : {{"intention": "analyze_file", "valeur": "rapport.txt"}}

Demande de l'utilisateur : {question}
"""
    return ask_llm(prompt, json_format=True)


def describe_directory_content(directory: str, entries: list[str]) -> str:
    listing = "\n".join(entries) if entries else "(répertoire vide)"
    prompt = f"""
Voici le contenu observé du répertoire {directory} :
{listing}

Décris ce que ce contenu permet d'identifier : nature probable du projet, rôle des éléments présents.
Distingue clairement les observations certaines (ce qui est réellement présent) des hypothèses
(ce que tu en déduis). Ne décris que les éléments listés ci-dessus, n'en invente aucun autre.
Réponds en texte libre, en français, sans JSON.
"""
    return ask_llm(prompt)