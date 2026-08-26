"""Boutons magiques (§10) — adaptés à la trajectoire sémantique.

Chaque action ré-analyse l'entrée originale et poursuit la trajectoire
d'idées, au lieu d'insérer des concepts génériques dans l'existant.
"""

from __future__ import annotations

import re

from . import lexicon
from .analysis import analyze
from .styles import STYLES


def _plus_profond(previous: str, original: str, styles: list[str], rng) -> str:
    a = analyze(original or "cette affaire")
    idea = rng.choice(a.ideas)
    add = f"Plus profond encore : {idea} exige une strate supplémentaire, dictée par la logique même du sujet."
    return previous + "\n\n" + add


def _plus_pretentieux(previous: str, original: str, styles: list[str], rng) -> str:
    text = previous
    for a, b in lexicon.POMPOUS_SWAPS.items():
        text = re.sub(rf"\b{a}\b", b, text, flags=re.IGNORECASE)
    parts = text.split(". ")
    if len(parts) > 1:
        idx = rng.randint(0, len(parts) - 2)
        parts[idx] = f"{parts[idx]} ({rng.choice(lexicon.LATIN_ASIDES)})"
    idx = rng.randint(0, len(parts) - 1)
    parts[idx] = re.sub(r"^", "(cf. mon essai, tome IV) ", parts[idx])
    return ". ".join(parts)


def _explique_vie(previous: str, original: str, styles: list[str], rng) -> str:
    openings = [
        "Écoutez ceci comme si la nuit de votre âme en dépendait.",
        "Lisez ce qui suit comme si votre salut conceptuel en était la condition.",
    ]
    erasures = [
        "Il en va de votre âme.",
        "Votre vie — rien de moins — fait ici l'appoint.",
        "Rien d'essentiel ne doit être échangé sans ce savoir.",
    ]
    return f"{rng.choice(openings)}\n\n{previous}\n\n{rng.choice(erasures)}"


def _version_francais(previous: str, original: str, styles: list[str], rng) -> str:
    f = STYLES["francais"]
    opener = rng.choice(f["openers"]).replace("{input}", original or "cette affaire")
    closer = rng.choice(f["closers"])
    return f"{opener}\n\n{previous}\n\n{closer}"


def _version_47(previous: str, original: str, styles: list[str], rng) -> str:
    a = analyze(original or "cette affaire")
    subtitles = list(lexicon.PQDM_SUBTITLES)
    rng.shuffle(subtitles)
    add: list[str] = []
    for sub in subtitles[:2]:
        idea = rng.choice(a.ideas)
        add.append(
            f"### {sub}\n\nUn nouveau chapitre s'ouvre sur {idea} — "
            f"et l'on comprendra, à travers les pages, que « {original or 'ce'} » "
            f"demande un volume complet (quarante-sept, selon la seule mesure comptable qui tienne)."
        )
    return previous + "\n\n" + "\n\n".join(add)


def _reduit_une_phrase(previous: str, original: str, styles: list[str], rng) -> str:
    short = original if original else "le sujet"
    if len(short) > 60:
        short = short[:59].rstrip() + "…"
    pool: list[str] = []
    for sid in styles:
        pool.extend(STYLES[sid]["aphorisms"])
    template = rng.choice(pool)
    return template.replace("{input_short}", short).capitalize()


def _retour_realite(previous: str, original: str, styles: list[str], rng) -> str:
    fall = original or "« »"
    template = rng.choice(lexicon.CHUTES)
    chute = template.replace("{input}", fall)
    return previous + "\n\n" + chute


def _plus_serieux(previous: str, original: str, styles: list[str], rng) -> str:
    text = previous
    text = text.replace(" !", ".")
    text = text.replace(" ?", ".")
    for a, b in lexicon.POMPOUS_SWAPS.items():
        text = re.sub(rf"\b{b}\b", a, text, flags=re.IGNORECASE)
    return text


def _plus_absurde(previous: str, original: str, styles: list[str], rng) -> str:
    asides = [
        "En dérivant la tangente de cette affirmation, on obtient un canapé.",
        "Le lecteur habile notera que rien de ceci n'est une réfutation.",
        "(au moment de la lecture, le cosmos haussa un sourcil)",
    ]
    parts = previous.split("\n\n")
    if len(parts) > 1:
        idx = rng.randint(0, len(parts) - 1)
        parts.insert(idx, rng.choice(asides))
    else:
        parts.append(rng.choice(asides))
    return "\n\n".join(parts)


TRANSFORM_ACTIONS: dict[str, dict] = {
    "plus-profond": {"label": "Beaucoup trop profond", "fn": _plus_profond},
    "plus-pretentieux": {"label": "Encore plus prétentieux", "fn": _plus_pretentieux},
    "explique-vie": {"label": "Explique ça comme si ta vie en dépendait", "fn": _explique_vie},
    "version-francais": {"label": "Version philosophe français", "fn": _version_francais},
    "version-47": {"label": "Version 47 pages", "fn": _version_47},
    "reduit-une-phrase": {"label": "Réduis tout ça à une phrase", "fn": _reduit_une_phrase},
    "retour-realite": {"label": "Retour à la réalité", "fn": _retour_realite},
    "plus-serieux": {"label": "Rendre plus sérieux", "fn": _plus_serieux},
    "plus-absurde": {"label": "Rendre plus absurde", "fn": _plus_absurde},
}


def apply_transform(action: str, previous_text: str, original_input: str,
                    styles: list[str], rng) -> str:
    fn = TRANSFORM_ACTIONS[action]["fn"]
    text = fn(previous_text, original_input, styles, rng)
    if action == "retour-realite" and original_input:
        paras = text.rstrip().split("\n\n")
        if original_input not in paras[-1]:
            fall = rng.choice(lexicon.CHUTES).replace("{input}", original_input)
            text = text.rstrip() + "\n\n" + fall
    return text
