from pathlib import Path

from ollama import Client


def welcome_message() -> str:
    return "Bonjour, que puis-je faire ?"


def say_hello() -> str:
    return "Bonjour !"


def tell_name() -> str:
    return "Je suis un agent autonome minimal."


def ask_llm(
  prompt: str, json_format: bool = False, model: str = "llama3.2"
) -> str:
    client = Client(host="http://localhost:11434")
    response = client.generate(
    model=model,
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


def analyze_project_structure(directory: str) -> str:
  return analyze_project_detail(directory, "structure")


def analyze_project_detail(directory: str, topic: str) -> str:
  root = Path(directory)
  allowed_suffixes = {".py", ".cpp", ".cc", ".c", ".h", ".hpp", ".pro", ".ui", ".qrc", ".cmake"}
  ignored_directories = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist", "release", "debug"}
  ignored_file_names = {"moc_predefs.h"}
  files = []

  for path in sorted(root.rglob("*")):
    if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
      continue
    if any(part in ignored_directories for part in path.relative_to(root).parts):
      continue
    filename = path.name.lower()
    if filename in ignored_file_names:
      continue
    files.append(path)

  source_files = [
    path for path in files
    if not path.name.lower().startswith(("moc_", "qrc_"))
  ]
  source_files.sort(key=lambda path: (path.stem.lower() != "main", str(path).lower()))

  observations = []
  for path in source_files[:25]:
    try:
      content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
      continue
    observations.append(f"--- {path.relative_to(root)} ---\n{content[:6000]}")

  if not observations:
    return "Aucun fichier source lisible n'a été trouvé dans ce répertoire."

  entrypoint_observations = [
    observation for observation in observations
    if "int main(" in observation or "int main (" in observation
  ]
  entrypoint_context = "\n".join(entrypoint_observations)
  if not entrypoint_context:
    entrypoint_context = "Aucune fonction main() observée dans les fichiers lus."
  visual_instructions = ""
  if topic == "visualisation Mermaid du flux d'exécution":
    visual_instructions = """
Pour cette demande visuelle, réponds uniquement avec les quatre sections demandées, sans titre,
commentaire ou diagramme avant la section 1. La section 2 doit contenir un seul diagramme Mermaid
dans un bloc `mermaid`, et ce diagramme ne doit apparaître nulle part ailleurs dans la réponse.
Construis d'abord le flux global observé, dans cet ordre lorsqu'il est présent :
fonction `main()` -> création de l'application Qt -> création de la fenêtre ou du widget ->
configuration de l'interface ou du rendu -> appel à `show()` -> appel à `app.exec()` ou boucle
d'événements. Ajoute ensuite les détails techniques utiles comme les layouts, widgets, shaders
ou ressources, en les reliant au composant concerné.
- Utilise des identifiants de nœuds Mermaid uniques et stables.
- Ne répète jamais un même nœud pour donner plusieurs numéros d'étape.
- N'ajoute aucun numéro dans les libellés, notamment pas de forme comme `1:11`.
- Ne représente que les étapes et relations visibles dans les observations ; omets une étape
  absente plutôt que de l'inventer.
- Après le diagramme, ajoute une courte phrase indiquant les étapes qui restent incertaines.
"""
  flow_instructions = ""
  if topic == "flux d'exécution et point d'entrée":
    flow_instructions = """
Pour cette demande, la section 2 doit décrire le flux dans son ordre d'exécution, et pas seulement
nommer le point d'entrée. Lorsque les appels sont observés, détaille explicitement la chaîne :
fonction `main()` -> création de l'application -> création de la fenêtre ou du widget ->
configuration éventuelle -> `show()` -> `app.exec()` ou boucle d'événements. Pour chaque étape,
cite le fichier et l'appel correspondant. Si une étape n'est pas observée, indique-le sans la
présenter comme un fait.
- Distingue clairement le flux confirmé par les appels de `main()` des callbacks ou étapes de
  cycle de vie Qt, OpenGL ou Vulkan comme `initializeGL()`, `createRenderer()` et les méthodes de
  rendu. Ces étapes sont secondaires et leur moment exact doit être décrit comme dépendant du
  framework lorsqu'il n'est pas directement ordonné dans le code observé.
- Ne place pas un callback graphique comme une étape certaine entre deux appels de `main()` sans
  preuve explicite de cet ordre.
"""

  prompt = f"""
Tu analyses uniquement le projet situé dans le répertoire {root}.
Voici les fichiers effectivement lus :
{chr(10).join(observations)}

Pour l'analyse du flux d'exécution, voici le relevé prioritaire des points d'entrée globaux :
{entrypoint_context}

La demande de précision porte sur : {topic}.
{visual_instructions}
{flow_instructions}
Réponds en français avec exactement quatre sections :
1. Faits observés
2. Réponse précise
3. Preuves utilisées
4. Limites de l'analyse

Règles :
- Ne cite que les fichiers et éléments présents dans les observations.
- Ne mélange aucune connaissance d'un autre projet.
- Un fait doit être directement visible dans le code.
- Une interprétation doit être présentée comme probable.
- Pour le flux d'exécution, cherche d'abord une fonction `main` dans les fichiers observés.
  Un constructeur, `initializeGL()` ou `createRenderer()` est un point technique secondaire,
  pas le point d'entrée global de l'application. Si aucune fonction `main` n'est observée,
  indique explicitement que le point d'entrée global n'a pas été trouvé.
- Lorsque le code montre qu'un constructeur configure l'interface avant l'appel à `show()`,
  présente cet ordre comme un fait observé. Indique seulement que le détail interne de création
  des widgets et des layouts n'est pas entièrement décrit si les observations sont incomplètes.
- Ne prétends pas avoir exécuté ou compilé le projet.
"""
  return ask_llm(prompt, model="qwen3:4b")