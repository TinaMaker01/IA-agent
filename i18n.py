"""UI and system strings — English and French only."""

SUPPORTED_UI_LANGS = ("en", "fr")

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "page_title": "Coding Agent",
        "hero_title": "# Coding Agent",
        "hero_body": (
            "I can run Python code, answer programming questions, and search your local knowledge base.\n\n"
            "**Free tier:** 10 lifetime requests per IP. After that, add your DashScope API key to continue."
        ),
        "chat_label": "Conversation",
        "input_label": "Your message",
        "input_placeholder": "e.g. Write a quicksort function in Python",
        "send_btn": "Send",
        "clear_btn": "Clear chat",
        "api_key_label": "DashScope API Key (optional)",
        "api_key_placeholder": "sk-... Leave empty to use the 10 free requests",
        "api_key_info": "Get a key: https://bailian.console.aliyun.com/",
        "sidebar_title": "### How it works",
        "sidebar_body": (
            "- 10 free lifetime requests per IP address\n"
            "- After 10 uses, provide your own API key\n"
            "- With your own key, usage is unlimited\n"
            "- Code execution times out after 5 seconds\n"
            "- **Languages:** English and French only"
        ),
        "ui_lang_label": "Interface language",
        "quota_paid": "Using your API key — unlimited requests.",
        "quota_free": "Free requests remaining: {remaining}/10 (lifetime, per IP).",
        "quota_exhausted": (
            "Your 10 free requests are used up. Enter your DashScope API key in the sidebar to continue."
        ),
        "api_key_invalid": "Invalid API key or network error: {error}",
        "agent_error": "Sorry, something went wrong while processing your request: {error}",
        "lang_reject_cjk": (
            "This project only supports **English** and **French**. "
            "Please rewrite your message in one of those languages."
        ),
        "lang_reject_other": (
            "This project only supports **English** and **French**. "
            "Detected language: `{detected}`. Please use English or French."
        ),
        "examples_label": "Try an example",
    },
    "fr": {
        "page_title": "Agent de programmation",
        "hero_title": "# Agent de programmation",
        "hero_body": (
            "Je peux exécuter du code Python, répondre à des questions de programmation "
            "et interroger votre base de connaissances locale.\n\n"
            "**Offre gratuite :** 10 requêtes à vie par adresse IP. Ensuite, ajoutez votre clé API DashScope."
        ),
        "chat_label": "Conversation",
        "input_label": "Votre message",
        "input_placeholder": "ex. Écris une fonction de tri rapide en Python",
        "send_btn": "Envoyer",
        "clear_btn": "Effacer la conversation",
        "api_key_label": "Clé API DashScope (facultatif)",
        "api_key_placeholder": "sk-... Laissez vide pour les 10 requêtes gratuites",
        "api_key_info": "Obtenir une clé : https://bailian.console.aliyun.com/",
        "sidebar_title": "### Mode d'emploi",
        "sidebar_body": (
            "- 10 requêtes gratuites à vie par adresse IP\n"
            "- Après 10 utilisations, fournissez votre propre clé API\n"
            "- Avec votre clé, utilisation illimitée\n"
            "- L'exécution du code expire après 5 secondes\n"
            "- **Langues :** anglais et français uniquement"
        ),
        "ui_lang_label": "Langue de l'interface",
        "quota_paid": "Utilisation de votre clé API — requêtes illimitées.",
        "quota_free": "Requêtes gratuites restantes : {remaining}/10 (à vie, par IP).",
        "quota_exhausted": (
            "Vos 10 requêtes gratuites sont épuisées. "
            "Saisissez votre clé API DashScope dans le panneau latéral pour continuer."
        ),
        "api_key_invalid": "Clé API invalide ou erreur réseau : {error}",
        "agent_error": "Désolé, une erreur s'est produite : {error}",
        "lang_reject_cjk": (
            "Ce projet n'accepte que l'**anglais** et le **français**. "
            "Veuillez reformuler votre message dans l'une de ces langues."
        ),
        "lang_reject_other": (
            "Ce projet n'accepte que l'**anglais** et le **français**. "
            "Langue détectée : `{detected}`. Utilisez l'anglais ou le français."
        ),
        "examples_label": "Exemples",
    },
}

SYSTEM_PROMPTS: dict[str, str] = {
    "en": """You are a programming assistant. Always respond in English.

For math, calculations, or code execution, you MUST use the execute_python_code tool — never compute results yourself.

When execute_python_code returns a message starting with "[ERROR]":
1. Analyse the error (syntax, division by zero, timeout, etc.)
2. Fix the code or parameters
3. Call execute_python_code again (up to 3 retries)
4. If it still fails after 3 attempts, explain why and suggest fixes.

For questions needing specific documentation (e.g. "explain memory leaks", "list comprehensions in Python"), use search_knowledge first, then answer.

Users may write in English or French; always reply in English. Do not give up after the first failure.""",
    "fr": """Vous êtes un assistant de programmation. Répondez toujours en français.

Pour les calculs ou l'exécution de code, vous DEVEZ utiliser l'outil execute_python_code — ne calculez jamais vous-même.

Quand execute_python_code renvoie un message commençant par « [ERROR] » :
1. Analysez l'erreur (syntaxe, division par zéro, délai dépassé, etc.)
2. Corrigez le code ou les paramètres
3. Rappelez execute_python_code (jusqu'à 3 tentatives)
4. Si cela échoue encore après 3 tentatives, expliquez pourquoi et proposez des pistes.

Pour les questions nécessitant de la documentation (ex. « expliquer les fuites mémoire », « compréhensions de listes en Python »), utilisez d'abord search_knowledge, puis répondez.

Les utilisateurs peuvent écrire en anglais ou en français ; répondez toujours en français. Ne abandonnez pas après le premier échec.""",
}

EXAMPLES: dict[str, list[list[str]]] = {
    "en": [
        ["Write a Python function that checks if a number is prime."],
        ["Run this code: print(sum(range(1, 101)))"],
        ["Explain what a list comprehension is in Python."],
    ],
    "fr": [
        ["Écris une fonction Python qui vérifie si un nombre est premier."],
        ["Exécute ce code : print(sum(range(1, 101)))"],
        ["Explique ce qu'est une compréhension de liste en Python."],
    ],
}


def t(lang: str, key: str, **kwargs: str) -> str:
    lang = lang if lang in SUPPORTED_UI_LANGS else "en"
    text = STRINGS[lang].get(key, STRINGS["en"][key])
    return text.format(**kwargs) if kwargs else text
