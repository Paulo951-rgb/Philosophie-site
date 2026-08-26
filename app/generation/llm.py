"""Génération via un vrai modèle de langage local (llama.cpp + Qwen2.5-3B).

Le modèle tourne sur la machine (llama-server, port 8090), sans clé ni
service externe. Ce module construit les prompts à partir des paramètres
utilisateur, appelle le serveur local et post-traite la sortie. En cas
d'indisponibilité du modèle, il renvoie None : l'appelant retombe alors
sur le moteur procédural.
"""

from __future__ import annotations

import re
import time

import httpx

from .safety import contains_real_philosopher, scrub

LLM_URL = "http://127.0.0.1:8090"
_HEALTH_TTL = 15.0  # secondes entre deux sondes de santé

_health_ok: float | None = None  # timestamp du dernier état connu
_health_state = False

_MAX_TOKENS = {
    "court": 140, "moyen": 320, "long": 700, "tres-long": 1150, "pqdm": 1500,
}
_TEMPERATURE = {
    "serieux": 0.55, "subtile": 0.8, "dramatique": 0.95,
    "caricatural": 1.05, "trop-serieux": 1.1,
}

_DEPTH_DESC = {
    "legere": "effleure une seule idée philosophique, sans t'attarder",
    "profond": "pose une thèse claire et développe-la",
    "tres-profond": "croise plusieurs concepts (désir, finitude, condition humaine)",
    "metaphysique": "perds-toi en digressions théoriques, au point de frôler la perte du fil initial",
}

_EXAG_DESC = {
    "serieux": "ton posé, presque crédible comme un vrai texte de philosophie",
    "subtile": "le sérieux domine, mais une ou deux touches trahissent l'absurdité du sujet",
    "dramatique": "emphase, ponctuation expressive, vocabulaire de la tragédie",
    "caricatural": "comique assumé dès la première phrase, exagération visible",
    "trop-serieux": "l'auteur semble sincèrement bouleversé par ce sujet trivial — décalage maximal",
}

_COMPLEXITY_DESC = {
    "simple": "vocabulaire courant, phrases lisibles",
    "soutenu": "vocabulaire choisi, phrases élégantes",
    "tres-soutenu": "vocabulaire riche, tournures littéraires",
    "intimidant": "vocabulaire académique, références abstraites, phrases longues",
    "pompeux": "jargon quasi incompréhensible, tournures alambiquées volontairement excessives",
}

_SAFETY = (
    "Règles absolues : n'invente jamais de citation de philosophe réel et "
    "n'attribue jamais le texte à un penseur réel (Kant, Nietzsche, Camus, "
    "Platon, Descartes...). Ne mentionne leur nom que pour t'en écarter. "
    "Reste satirique et bienveillant : on se moque du genre pompeux, jamais "
    "de la personne. Pas de markdown, pas de listes, pas de préface méta : "
    "écris directement la réflexion."
)


def _style_block(styles: list[str], style_defs: dict) -> str:
    lines = []
    for sid in styles:
        sheet = style_defs.get(sid, {})
        label = sheet.get("label", sid)
        desc = sheet.get("desc", "")
        vocab = ", ".join(sheet.get("vocab", [])[:5])
        lines.append(f"- {label} : {desc} Vocabulaire caractéristique : {vocab}.")
    block = "\n".join(lines)
    if len(styles) == 2:
        block += ("\nFusionne les deux styles en une voix unique et cohérente, "
                  "sans juxtaposition artificielle.")
    return block


def build_generation_prompt(
    input_text: str,
    depth: str,
    exaggeration: str,
    styles: list[str],
    length: str,
    complexity: str,
    mode: str,
    style_defs: dict,
    length_words: dict,
) -> tuple[str, str, int, float]:
    """Retourne (système, utilisateur, max_tokens, température)."""
    words = length_words.get(length, 150)
    system = (
        "Tu incarnes un philosophe caricatural de salon littéraire. Ta mission : "
        "transformer une phrase banale en une réflexion exagérément profonde, drôle "
        "par le contraste, et surtout COHÉRENTE avec le sujet précis de la phrase. "
        "Analyse d'abord mentalement ce que la phrase dit vraiment (son objet, "
        "l'intention de celui qui parle), puis écris une réflexion qui parle de "
        "cela — jamais d'un autre sujet.\n"
        f"Style(s) à incarner :\n{_style_block(styles, style_defs)}\n"
        f"Degré d'exagération : {_EXAG_DESC.get(exaggeration, _EXAG_DESC['subtile'])}.\n"
        f"Registre de langue : {_COMPLEXITY_DESC.get(complexity, _COMPLEXITY_DESC['soutenu'])}.\n"
        f"{_SAFETY}"
    )

    if mode == "citation":
        user = (
            f"À partir de cette phrase banale : « {input_text} »\n"
            "Écris UN aphorisme philosophique unique (une ou deux phrases), "
            "formulé comme une citation, en rapport direct avec le sujet de la phrase. "
            "Puis, sur une nouvelle ligne, ajoute une attribution ENTIÈREMENT FICTIVE "
            "et humoristique au format : — Prénom ou nom inventé, qualificatif comique, époque. "
            "Exemple de format (à ne pas copier) : — Hilaire de Jonquille, penseur du mardi gras, XVIIIe siècle. "
            "Le nom doit être inventé de toutes pièces."
        )
        return system, user, 120, _TEMPERATURE.get(exaggeration, 0.8)

    if mode == "dissertation":
        user = (
            f"À partir de cette phrase banale : « {input_text} »\n"
            f"Rédige une mini-dissertation philosophique d'environ {words} mots, "
            f"profondeur : {_DEPTH_DESC.get(depth, _DEPTH_DESC['profond'])}. "
            "Structure exigée, avec ces titres exacts sur leurs propres lignes :\n"
            "Introduction\n(accroche, reformulation de la situation banale en enjeu existentiel, "
            "problématique disproportionnée)\n"
            "I.\n(premier axe)\n"
            "II.\n(deuxième axe)\n"
            "III.\n(dépassement dialectique)\n"
            "Conclusion\n(ouverture finale exagérément grave). "
            "La dissertation doit porter réellement sur le sujet de la phrase."
        )
        return system, user, max(_MAX_TOKENS.get(length, 320), 700), _TEMPERATURE.get(exaggeration, 0.8)

    user = (
        f"Phrase banale : « {input_text} »\n"
        f"Écris la réflexion philosophique d'environ {words} mots. "
        f"Profondeur : {_DEPTH_DESC.get(depth, _DEPTH_DESC['profond'])}. "
        "Commence par rappeler la phrase entre guillemets français « », pose une "
        "problématique grandiloquente liée au sujet réel de la phrase, développe "
        "en enchaînant les idées (chaque phrase découle de la précédente), puis "
        "termine par une chute qui ramène brutalement à la banalité de la phrase "
        "initiale. Reste centré sur le sujet de la phrase du début à la fin."
    )
    return system, user, _MAX_TOKENS.get(length, 320), _TEMPERATURE.get(exaggeration, 0.8)


_TRANSFORM_INSTRUCTIONS = {
    "plus-profond": (
        "Ajoute une couche de réflexion supplémentaire : complexifie chaque idée, "
        "creuse les présupposés, ajoute une digression métaphysique. Garde le sujet."
    ),
    "plus-pretentieux": (
        "Réécris ce texte avec un vocabulaire plus pompeux, des tournures plus "
        "alambiquées, des parenthèses doctes et un orgueil tranquille. Garde le sujet."
    ),
    "explique-vie": (
        "Réécris ce texte comme si expliquer cette réflexion était une question de "
        "vie ou de mort : urgence dramatique, enjeu existentiel maximal, gravité "
        "absolue. Garde le sujet."
    ),
    "version-francais": (
        "Réécris ce texte dans le style caricatural du philosophe français de "
        "plateau : café serré, formules brillantes, bons mots, nonchalance géniale. "
        "Garde le sujet."
    ),
    "version-47": (
        "Développe massivement ce texte : digressions nombreuses, exemples "
        "inutilement précis, sous-arguments qui s'emboîtent. Triple au moins la "
        "longueur. Garde le sujet."
    ),
    "reduit-une-phrase": (
        "Condense toute cette réflexion en UN seul aphorisme prétentieux et "
        "percutant, qui garde l'essence du sujet."
    ),
    "retour-realite": (
        "Garde ce texte tel quel, mais ajoute à la fin une chute d'une ou deux "
        "phrases qui dégonfle brutalement tout l'édifice et ramène au fait banal "
        "d'origine, de façon comique et déflatrice."
    ),
    "plus-serieux": (
        "Réécris ce texte en retirant les traces d'absurdité : ton plus posé, "
        "presque crédible comme vraie philosophie. Garde le sujet."
    ),
    "plus-absurde": (
        "Réécris ce texte en poussant l'absurdité : images incongrues, comparaisons "
        "inattendues, exagération comique assumée. Garde le sujet."
    ),
}


def build_transform_prompt(
    action: str,
    previous_text: str,
    original_input: str,
) -> tuple[str, str, int]:
    """Prompt de transformation : le texte précédent est retravaillé, pas régénéré."""
    instruction = _TRANSFORM_INSTRUCTIONS[action]
    system = (
        "Tu réécris des textes philosophiques satiriques. " + _SAFETY
    )
    context = f"Phrase banale d'origine : « {original_input} »\n" if original_input else ""
    user = (
        f"{context}Texte à retravailler :\n[TEXTE]\n{previous_text}\n[/TEXTE]\n\n"
        f"Consigne : {instruction}\n"
        "Réponds uniquement avec le nouveau texte : ne reproduis pas les balises "
        "[TEXTE], pas de commentaire, pas d'explication."
    )
    if action == "reduit-une-phrase":
        max_tokens = 120
    elif action == "version-47":
        max_tokens = 1500
    elif action == "retour-realite":
        max_tokens = min(1600, len(previous_text.split()) * 2 + 120)
    else:
        max_tokens = min(1200, len(previous_text.split()) * 2 + 150)
    return system, user, max_tokens


# ------------------------------------------------------------------ appel HTTP


def llm_available() -> bool:
    """Sonde le serveur local (résultat mis en cache quelques secondes)."""
    global _health_ok, _health_state
    now = time.monotonic()
    if _health_ok is not None and now - _health_ok < _HEALTH_TTL:
        return _health_state
    try:
        r = httpx.get(f"{LLM_URL}/health", timeout=2.0)
        _health_state = r.status_code == 200
    except httpx.HTTPError:
        _health_state = False
    _health_ok = now
    return _health_state


def _chat(system: str, user: str, max_tokens: int, temperature: float,
          timeout: float) -> str | None:
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    try:
        r = httpx.post(f"{LLM_URL}/v1/chat/completions", json=payload,
                       timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError):
        return None


# ------------------------------------------------------------------ post-traitement


_MD_NOISE = re.compile(r"[*_`#]|^\s*[-•]\s?", re.MULTILINE)


def _postprocess(text: str) -> str:
    text = text.strip()
    # délimiteurs de bloc parfois répétés par le modèle
    text = text.replace("«««", "").replace("»»»", "")
    text = text.replace("[TEXTE]", "").replace("[/TEXTE]", "")
    text = _MD_NOISE.sub("", text)
    # retire une éventuelle ligne méta du modèle ("Voici la réflexion...")
    lines = [ln for ln in text.split("\n")]
    if lines and re.match(r"(?i)^(voici|bien sûr|certainement|d'accord)", lines[0].strip()):
        lines = lines[1:]
    text = "\n".join(lines).strip()
    # guillemets droits → guillemets français autour de la phrase citée
    text = re.sub(r'"([^"\n]{3,80})"', r"« \1 »", text)
    # espaces issues de la tokenisation («  mot → « mot, mot  » → mot »)
    text = re.sub(r"«\s+", "« ", text)
    text = re.sub(r"\s+»", " »", text)
    return text


def _safe_text(text: str, rng=None) -> str:
    """Filtre anti-attribution : si un vrai nom de philosophe apparaît, on
    le gomme via safety.scrub."""
    if contains_real_philosopher(text):
        text = scrub(text, rng)
    return text


# ------------------------------------------------------------------ API publique


def generate_llm(
    input_text: str,
    depth: str,
    exaggeration: str,
    styles: list[str],
    length: str,
    complexity: str,
    mode: str,
    style_defs: dict,
    length_words: dict,
) -> dict | None:
    """Génère via le modèle local. None si indisponible (→ repli procédural)."""
    if not llm_available():
        return None
    system, user, max_tokens, temperature = build_generation_prompt(
        input_text, depth, exaggeration, styles, length, complexity, mode,
        style_defs, length_words,
    )
    timeout = 60.0 + max_tokens / 8  # ~8 tok/s sur CPU, marge incluse
    raw = _chat(system, user, max_tokens, temperature, timeout)
    if not raw or len(raw.strip()) < 20:
        return None
    text = _safe_text(_postprocess(raw))

    if mode == "citation":
        quote, attribution = _split_attribution(text)
        if not quote:
            return None
        if attribution and contains_real_philosopher(attribution):
            attribution = None
        if not attribution:
            attribution = "— Anonyme, penseur du dimanche soir"
        return {"text": quote, "attribution": attribution}

    return {"text": text}


def transform_llm(action: str, previous_text: str, original_input: str) -> dict | None:
    if not llm_available() or action not in _TRANSFORM_INSTRUCTIONS:
        return None
    system, user, max_tokens = build_transform_prompt(action, previous_text, original_input)
    timeout = 60.0 + max_tokens / 8
    raw = _chat(system, user, max_tokens, 0.85, timeout)
    if not raw or len(raw.strip()) < 10:
        return None
    text = _safe_text(_postprocess(raw))
    # retour-realite : la chute doit mentionner le fait banal initial
    if action == "retour-realite" and original_input:
        short = original_input if len(original_input) <= 120 else original_input[:117] + "…"
        if short[:25].lower() not in text.lower():
            text = text.rstrip() + f"\n\nBref : « {short} ». Le reste n'était que littérature."
    return {"text": text}


def _split_attribution(text: str) -> tuple[str, str | None]:
    """Sépare l'aphorisme de la ligne d'attribution « — Nom, ... ».
    Seule la DERNIÈRE ligne est candidate : un tiret en plein corps du
    texte (usage légitime en français) ne doit pas être découpé."""
    lines = text.strip().split("\n")
    last = lines[-1].strip()
    match = re.match(r"^[—–-]\s+(.+)$", last)
    if match and len(lines) > 1 and len(last) >= 6:
        quote = "\n".join(lines[:-1]).strip()
        if quote:
            return quote, "— " + match.group(1).strip()
    return text.strip(), None
