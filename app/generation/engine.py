"""Moteur de génération sémantique (remplace le système par gabarits).

Pipeline : analyse de l'entrée (analysis.py) → problématique → trajectoire
d'idées reliées → retour contrasté à la phrase initiale. Chaque phrase du
corps découle de l'idée précédente et reste liée au sujet.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from . import lexicon, llm
from .analysis import InputAnalysis, analyze, formulate_problematic
from .styles import DEFAULT_STYLE, STYLES
from .safety import scrub
from .transforms import TRANSFORM_ACTIONS, apply_transform

# ------------------------------------------------------------------ gabarits

DEPTH = {
    "legere": {"paras": 1, "steps": 2},
    "profond": {"paras": 2, "steps": 3},
    "tres-profond": {"paras": 3, "steps": 4},
    "metaphysique": {"paras": 4, "steps": 5},
}

LENGTH_WORDS = {
    "court": 50, "moyen": 150, "long": 350, "tres-long": 700, "pqdm": 1500,
}

COMPLEXITY = ["simple", "soutenu", "tres-soutenu", "intimidant", "pompeux"]
EXAGGERATION = ["serieux", "subtile", "dramatique", "caricatural", "trop-serieux"]
MODES = ["standard", "dissertation", "citation"]

# Chaque idée de la trajectoire est développée par une phrase pleine où le
# {idea} porte le sens ; le {obj} rappelle l'objet. Jamais d'injection brute.
IDEA_SENTENCES = [
    "C'est que {idea} trouve ici un lieu de démonstration discret : la phrase banale suffit à le faire éclore.",
    "Et l'on comprend que {idea} n'est pas une abstraction : elle se lit dans ce qui arrive à « {obj} ».",
    "Le propos s'épaissit : {idea} donne à la situation son poids réel.",
    "Ce n'est pas un détail : {idea} décide de la tonalité entière de l'affaire.",
    "On n'échappe pas à ceci : {idea} révèle ce que le quotidien sait sans le dire.",
    "La chose est moins simple qu'elle n'y paraît : {idea} s'y engage sans bruit.",
    "Ici encore, {idea} se donne à voir dans le geste le plus commun.",
    "Il y a, dans cette affaire, {idea} qui demande à être reconnu.",
]

# Ponts entre étapes (évitent la simple juxtaposition)
BRIDGES = [
    "Mais ce n'est pas tout.",
    "Ce n'est qu'un début.",
    "Il faut aller plus loin.",
    "Et ce n'est pas fini.",
    "Une chose en entraîne une autre.",
    "Ceci posé, autre chose s'annonce.",
]

# Ornements selon le degré d'exagération (appliqués au texte assemblé)
EXAG_ASIDES = {
    "subtile": ["(et ce n'est pas une mince affaire)", "— le sourire en coin —"],
    "dramatique": ["Ô sublime enjeu !", "— tremblement du sens —", "Hélas !"],
    "caricatural": ["(applaudissements de l'âme)", "ne riez pas, c'est grave", "— ici, le lecteur se lève —"],
    "trop-serieux": ["et l'affaire est on ne peut plus grave", "ceci, pensons-le bien, n'admet pas le rire"],
}

TROP_SERIEUX_FALLBACK = "Et, sincèrement, elle ne pardonnerait pas à l'histoire de l'avoir oubliée."

DIGRESSIONS = [
    "Mais je m'égare — quoique l'égarement soit ici la voie royale.",
    "Ce n'est qu'en apparence une digression ; revenons, le sujet nous attend de pied ferme.",
]

CHUTES_FINALES = [
    "Et pourtant, après toutes ces considérations, il reste une vérité beaucoup plus simple : « {input} ».",
    "Résumons : tout ceci, pour dire que « {input} ». La métaphysique s'incline.",
    "Au terme de l'exercice, la phrase demeure — étrangement solide : « {input} ».",
    "Bref. Écartons le théâtre : « {input} ». Le reste était l'épaisseur du propos.",
]


@dataclass
class PromptSpec:
    role: str
    exaggeration: str
    depth: str
    length: str
    complexity: str
    mode: str
    styles: list[str]
    safety_rules: list[str] = field(
        default_factory=lambda: [
            "Jamais de citation réelle attribuée à un vrai philosophe.",
            "Jamais d'attribution à une personne réelle ou fictive nommée.",
            "Registre satirique et bienveillant, sans offenser l'utilisateur.",
        ]
    )

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "exagération": self.exaggeration,
            "profondeur": self.depth,
            "longueur": self.length,
            "complexité": self.complexity,
            "mode": self.mode,
            "styles": self.styles,
            "sécurité": self.safety_rules,
        }


def _normalize_input(raw: str) -> str:
    text = re.sub(r"\s+", " ", (raw or "").strip())
    return text[:2000] if len(text) > 2000 else text


def _input_short(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _pick_style_item(rng: random.Random, styles: list[str], key: str) -> str:
    pool: list[str] = []
    for sid in styles:
        pool.extend(STYLES[sid][key])
    return rng.choice(pool)


def _scrub_clean(text: str, rng: random.Random) -> str:
    text = scrub(text, rng)
    text = re.sub(r"[«\"]\s+", "« ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([.,;:!?…])", r"\1", text)
    return text.strip()


# ---------------------------------------------------------------- trajectoire

def _build_trajectory(rng: random.Random, a: InputAnalysis, depth_id: str) -> list[str]:
    """Choisit une sous-suite ordonnée d'idées pertinentes (la trajectoire
    philosophique), reliée à l'objet par le sens — pas par un mot-clé."""
    depth = DEPTH[depth_id]
    steps = depth["steps"]
    ideas = list(a.ideas)
    rng.shuffle(ideas)
    chosen = ideas[:steps]
    obj = a.object_with_article() or "ceci"
    out: list[str] = []
    for i, idea in enumerate(chosen):
        sentence = rng.choice(IDEA_SENTENCES)
        sentence = sentence.replace("{idea}", idea).replace("{obj}", obj)
        if i > 0 and rng.random() < 0.45:
            sentence = rng.choice(BRIDGES) + " " + sentence
        out.append(sentence)
    return out


def _exaggerate(rng: random.Random, sentences: list[str], level: str) -> list[str]:
    if level == "serieux":
        return sentences
    out = list(sentences)
    asides = EXAG_ASIDES.get(level, [])
    eligible = [i for i, s in enumerate(out) if len(s.split()) >= 4]
    if asides and eligible:
        idx = rng.choice(eligible)
        aside = rng.choice(asides)
        if level == "caricatural":
            out[idx] = f"{aside} {out[idx]}"
        else:
            out[idx] = f"{out[idx]} {aside}."
    if level in ("dramatique", "caricatural") and eligible:
        idx = rng.choice(eligible)
        out[idx] = out[idx].rstrip(".") + " !"
        if level == "dramatique":
            out.append("Qui donc viendra mesurer l'ampleur du propos ?")
    if level == "trop-serieux":
        out.append(TROP_SERIEUX_FALLBACK)
    return out


def _apply_register(rng: random.Random, text: str, level: str) -> str:
    if level == "simple":
        swaps = {"dès lors": "alors", "au demeurant": "aussi", "en vérité": "vraiment"}
        for a, b in swaps.items():
            text = text.replace(a, b)
        return text
    if level in ("soutenu", "tres-soutenu"):
        parts = text.split(". ")
        if len(parts) > 1:
            eligible = [
                i for i in range(len(parts))
                if len(parts[i].split()) >= 3
                and not parts[i].lstrip().startswith(("(", "—", "«"))
                and parts[i].count("«") == parts[i].count("»")
            ]
            if eligible:
                idx = rng.choice(eligible)
                c = rng.choice(lexicon.CONNECTORS_SOUTENU)
                seg = parts[idx]
                parts[idx] = c.capitalize() + ", " + seg[0].lower() + seg[1:]
        return ". ".join(parts)
    if level in ("intimidant", "pompeux"):
        for a, b in lexicon.POMPOUS_SWAPS.items():
            text = re.sub(rf"\b{a}\b", b, text, flags=re.IGNORECASE)
        asides = lexicon.LATIN_ASIDES + (lexicon.GREEK_TERMS if level == "pompeux" else [])
        parts = text.split(". ")
        if len(parts) > 1:
            idx = rng.randint(0, len(parts) - 2)
            if "cf." not in parts[idx]:
                parts[idx] = f"{parts[idx]} ({rng.choice(asides)})"
        if level == "pompeux":
            idx = rng.randint(0, len(parts) - 1)
            if "cf." not in parts[idx]:
                parts[idx] = f"{parts[idx]} (cf. mon essai, tome IV)"
        return ". ".join(parts)
    return text


# ------------------------------------------------------------------ modes

def _build_standard(rng: random.Random, a: InputAnalysis, style_ids: list[str],
                    depth_id: str, exag: str, complexity: str) -> str:
    opener = _pick_style_item(rng, style_ids, "openers").replace("{input}", a.raw)
    problematique = formulate_problematic(a)
    trajectory = _build_trajectory(rng, a, depth_id)
    trajectory = _exaggerate(rng, trajectory, exag)
    paras = DEPTH[depth_id]["paras"]
    grouped: list[list[str]] = [[] for _ in range(paras)]
    for i, step in enumerate(trajectory):
        grouped[i % paras].append(step)
    body = [" ".join(g) for g in grouped if g]
    closer = _pick_style_item(rng, style_ids, "closers")
    final = rng.choice(CHUTES_FINALES).replace("{input}", a.raw)
    text = "\n\n".join([opener, problematique, *body, closer, final])
    text = _apply_register(rng, text, complexity)
    return _scrub_clean(text, rng)


def _build_dissertation(rng: random.Random, a: InputAnalysis, style_ids: list[str],
                        depth_id: str, exag: str, complexity: str) -> str:
    accroche = (
        f"Il est des énoncés que l'histoire de la pensée aurait dû prévoir : « {a.raw} » en est un. "
        f"De la pure banalité naît ici un enjeu que nul syllabus n'aurait osé rêver."
    )
    problematique = formulate_problematic(a)
    trajectory = _build_trajectory(rng, a, "tres-profond" if depth_id == "metaphysique" else "profond")
    trajectory = _exaggerate(rng, trajectory, exag)
    axes: list[str] = []
    n_axes = 3
    per = max(1, len(trajectory) // n_axes)
    ideas_used = a.ideas[:3] if len(a.ideas) >= 3 else a.ideas + ["le sens"]
    for i, roman in enumerate(("I.", "II.", "III.")):
        title = ideas_used[i].capitalize() if i < len(ideas_used) else "Le dépassement"
        chunk = trajectory[i * per:(i + 1) * per] or trajectory[-1:]
        axes.append(f"{roman} {title}\n" + " ".join(chunk))
    conclusion = (
        f"Conclusion\nS'il fallait retenir une ligne à l'encre forte, ce serait celle-ci : "
        f"{rng.choice(IDEA_SENTENCES).replace('{idea}', a.ideas[0]).replace('{obj}', a.object_with_article() or 'ceci')} "
        f"Et l'ouverture s'impose, grave et sereine : que sera demain, si « {_input_short(a.raw)} » se répète ?"
    )
    text = "\n\n".join([accroche, problematique, *axes, conclusion])
    text = _apply_register(rng, text, complexity)
    return _scrub_clean(text, rng)


def _build_citation(rng: random.Random, a: InputAnalysis, style_ids: list[str]) -> dict:
    short = _input_short(a.raw)
    template = _pick_style_item(rng, style_ids, "aphorisms")
    aphorism = template.replace("{input_short}", short)
    name = rng.choice(lexicon.FIRST_NAMES)
    epithet = rng.choice(lexicon.EPITHETS)
    century = rng.choice(lexicon.CENTURIES)
    attribution = f"— {name}, {epithet}, {century}"
    text = _scrub_clean(aphorism, rng)
    return {"text": text, "attribution": _scrub_clean(attribution, rng)}


def _build_pqdm(rng: random.Random, a: InputAnalysis, style_ids: list[str],
                exag: str, complexity: str) -> str:
    subtitles = list(lexicon.PQDM_SUBTITLES)
    rng.shuffle(subtitles)
    sections: list[str] = []
    for subtitle in subtitles[: rng.randint(4, 6)]:
        trajectory = _build_trajectory(rng, a, "tres-profond")
        trajectory = _exaggerate(rng, trajectory, exag if exag != "serieux" else "subtile")
        body = " ".join(trajectory)
        sections.append(f"### {subtitle}\n\n{body}")
    preface = f"« {a.raw} » : autant dire qu'il faudra bien plus qu'une note."
    final = rng.choice(CHUTES_FINALES).replace("{input}", a.raw)
    text = preface + "\n\n" + "\n\n".join(sections) + "\n\n" + final
    text = _apply_register(rng, text, complexity)
    return _scrub_clean(text, rng)


# ------------------------------------------------------------------ dispatcher

def generate(
    input_text: str,
    depth: str = "profond",
    exaggeration: str = "subtile",
    styles: list[str] | None = None,
    length: str = "moyen",
    complexity: str = "soutenu",
    mode: str = "standard",
    seed: int | None = None,
) -> dict:
    styles = [s for s in (styles or [DEFAULT_STYLE]) if s in STYLES][:2] or [DEFAULT_STYLE]
    if depth not in DEPTH:
        depth = "profond"
    if exaggeration not in EXAGGERATION:
        exaggeration = "subtile"
    if length not in LENGTH_WORDS:
        length = "moyen"
    if complexity not in COMPLEXITY:
        complexity = "soutenu"
    if mode not in MODES:
        mode = "standard"

    clean_input = _normalize_input(input_text)

    # 1. modèle de langage local (vrai LLM, cohérence sémantique réelle)
    spec = PromptSpec(
        role=f"Tu incarnes un philosophe caricatural de style {' + '.join(styles)}.",
        exaggeration=exaggeration,
        depth=depth,
        length=f"≈ {LENGTH_WORDS[length]} mots",
        complexity=complexity,
        mode=mode,
        styles=styles,
    )
    llm_result = llm.generate_llm(
        clean_input, depth, exaggeration, styles, length, complexity, mode,
        STYLES, LENGTH_WORDS,
    )
    if llm_result is not None:
        payload = {"text": llm_result["text"], "engine": "llm"}
        if llm_result.get("attribution"):
            payload["attribution"] = llm_result["attribution"]
        payload["prompt_details"] = spec.as_dict()
        payload["word_count"] = len(payload["text"].split())
        return payload

    # 2. repli procédural si le modèle est indisponible
    payload = _generate_procedural(clean_input, depth, exaggeration, styles,
                                   length, complexity, mode, seed)
    payload["prompt_details"] = spec.as_dict()
    payload["engine"] = "procedural"
    return payload


def _generate_procedural(
    clean_input: str,
    depth: str,
    exaggeration: str,
    styles: list[str],
    length: str,
    complexity: str,
    mode: str,
    seed: int | None,
) -> dict:
    rng = random.Random(seed)
    analysis = analyze(clean_input)

    best: dict | None = None
    for attempt in range(3):
        if mode == "citation":
            result = _build_citation(rng, analysis, styles)
            best = {"text": result["text"], "attribution": result["attribution"]}
            break
        if mode == "dissertation":
            text = _build_dissertation(rng, analysis, styles, depth, exaggeration, complexity)
        elif length == "pqdm":
            text = _build_pqdm(rng, analysis, styles, exaggeration, complexity)
        else:
            text = _build_standard(rng, analysis, styles, depth, exaggeration, complexity)
        target = LENGTH_WORDS[length]
        words = len(text.split())
        if mode == "standard" and length != "pqdm" and words < target * 0.6:
            extra = _build_trajectory(rng, analysis, depth)
            insert = " ".join(extra[:2])
            text = text + "\n\n" + _scrub_clean(_apply_register(rng, insert, complexity), rng)
            words = len(text.split())
        if best is None or abs(words - target) < abs(best["words"] - target):
            best = {"text": text, "words": words}
        if best and abs(best["words"] - target) <= target * 0.35:
            break

    assert best is not None
    payload = {"text": best["text"]}
    if "attribution" in best:
        payload["attribution"] = best["attribution"]
    payload["word_count"] = len(payload["text"].split())
    return payload


def transform(
    action: str,
    previous_text: str,
    original_input: str,
    styles: list[str] | None = None,
    seed: int | None = None,
) -> dict:
    if action not in TRANSFORM_ACTIONS:
        raise ValueError(f"action inconnue : {action}")

    # 1. modèle local : transforme le texte précédent, ne régénère pas
    llm_result = llm.transform_llm(action, previous_text, original_input)
    if llm_result is not None:
        return {
            "text": llm_result["text"],
            "action": action,
            "engine": "llm",
            "word_count": len(llm_result["text"].split()),
        }

    # 2. repli procédural
    rng = random.Random(seed)
    styles = [s for s in (styles or [DEFAULT_STYLE]) if s in STYLES][:2] or [DEFAULT_STYLE]
    new_text = apply_transform(action, previous_text, original_input, styles, rng)
    return {
        "text": _scrub_clean(new_text, rng),
        "action": action,
        "engine": "procedural",
        "word_count": len(new_text.split()),
    }
