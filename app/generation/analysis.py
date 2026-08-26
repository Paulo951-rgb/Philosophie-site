"""Analyse sémantique de l'entrée utilisateur.

Le moteur ne fonctionne plus par gabarits et remplacement de mots : il
décompose la phrase (intention + objet), l'ancre dans une famille
sémantique, et en déduit une constellation de concepts pertinents.
Pipeline : analyse → problématique → trajectoire d'idées (voir engine).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------- familles

# Chaque famille associe des lemmes de vocabulaire de surface à des
# concepts philosophiques pertinents (construits comme des ideas, pas des
# phrases clonées).
FAMILIES: dict[str, dict] = {
    "nourriture": {
        "lemmas": [
            "couscous", "pizza", "pizzas", "burger", "chocolat", "pain",
            "fromage", "frites", "gâteau", "glace", "café", "thé", "vin",
            "bière", "mangue", "sushi", "pâtes", "raclette", "sandwich",
            "croissant", "soupe", "salade", "tacos", "kebab", "nourriture",
            "plat", "repas", "goûter", "manger", "cuisine", "recette",
        ],
        "ideas": [
            "le goût comme expérience du monde",
            "le plaisir qui ne se justifie pas",
            "la mémoire emportée par un parfum",
            "le partage qui fait de la table un agora",
            "la convivialité comme façon d'être ensemble",
            "le désir qui précède le repas",
            "l'enfance revenue à travers une recette",
            "la culture logée jusqu'au mélange",
        ],
        "color": "alimentaire",
        "subprofiles": {
            "festif": {
                "terms": ["pizza", "pizzas", "burger", "frites", "kebab", "tacos", "sushi"],
                "ideas": [
                    "la joie partagée du vendredi soir",
                    "le rassemblement autour d'une boîte en carton",
                    "la fête sans prétention",
                    "la convivialité qui n'a pas besoin de raison",
                ],
            },
            "traditionnel": {
                "terms": ["couscous", "raclette", "tajine", "paëlla", "cassoulet", "pot-au-feu"],
                "ideas": [
                    "la mémoire des gestes transmis",
                    "la transmission d'une recette comme héritage",
                    "le rituel du dimanche",
                    "la tradition qui se mange",
                ],
            },
            "quotidien": {
                "terms": ["pain", "café", "thé", "croissant", "soupe"],
                "ideas": [
                    "le rituel du matin",
                    "le besoin comme compagnon fidèle",
                    "la routine qui structure les jours",
                    "le confort des habitudes",
                ],
            },
            "fête": {
                "terms": ["chocolat", "gâteau", "glace", "champagne", "vin"],
                "ideas": [
                    "la célébration comme art de vivre",
                    "le plaisir qui ne demande pas pardon",
                    "la gourmandise comme philosophie",
                    "le régal comme petite victoire",
                ],
            },
        },
    },
    "famine": {
        "lemmas": ["faim", "soif", "creve", "affamé", "appétit", "manger"],
        "ideas": [
            "le manque comme premier des savoirs",
            "le corps qui rappelle son droit au sujet",
            "la temporalité de l'attente du repas",
            "l'imagination du combler",
        ],
        "color": "corporelle",
    },
    "sommeil": {
        "lemmas": ["dors", "dort", "dormir", "sommeil", "dodo", "sieste", "répit",
                       "couche", "sommeiller", "se reposer", "somnoler"],
        "ideas": [
            "le sommeil comme souveraineté du repos",
            "la confiance du vivant qui s'abandonne",
            "le temps soustrait aux affaires du monde",
            "le doux droit de ne rien produire",
        ],
        "color": "du repos",
        "subprofiles": {
            "felin": {
                "terms": ["chat", "chaton", "minet", "matou"],
                "ideas": [
                    "l'indifférence du chat comme leçon de dignité",
                    "la nonchalance comme philosophie pratique",
                    "le sommeil comme art de vivre",
                    "l'indépendance qui n'a pas besoin de vous",
                    "l'élégance du geste gratuit",
                    "le ronron comme métaphysique du bonheur",
                    "la sieste comme résistance au monde",
                ],
            },
            "canin": {
                "terms": ["chien", "chiot", "toutou", "clebs"],
                "ideas": [
                    "la fidélité inconditionnelle comme mystère",
                    "la joie simple d'être ensemble",
                    "la loyauté sans calcul",
                    "la présence qui ne demande rien",
                    "le bonheur de la promenade",
                    "la confiance qui ne connaît pas la trahison",
                ],
            },
            "animal": {
                "terms": ["oiseau", "animal", "bête", "hamster", "poisson"],
                "ideas": [
                    "l'innocence de l'animal qui dort",
                    "la confiance absolue du vivant",
                    "le sommeil comme souveraineté du repos",
                ],
            },
        },
    },
    "fatigue": {
        "lemmas": ["fatigué", "fatiguée", "fatigue", "épuisé", "éreinté",
                   "crevé", "las", "lasse", "lessive"],
        "ideas": [
            "l'épuisement comme monsoie du monde",
            "ce que le corps demande (se reposer)",
            "la dignité du repos",
            "l'usure comme message à lire",
        ],
        "color": "de l'énergie",
    },
    "transport": {
        "lemmas": ["bus", "voiture", "train", "métro", "tram", "avion",
                   "vélo", "scooter", "embouteillage", "retard", "route"],
        "ideas": [
            "l'attente comme philosophie vécue",
            "le retard du monde comme rappel de notre impuissance",
            "la liberté de mouvement",
            "la motorisation comme promesse moderne",
        ],
        "color": "du trajet",
        "subprofiles": {
            "automobile": {
                "terms": ["voiture", "auto", "bagnole", "caisse"],
                "ideas": [
                    "l'acquisition comme promesse de liberté",
                    "le statut social sur quatre roues",
                    "la route comme horizon personnel",
                    "la vitesse comme illusion de maîtrise",
                ],
            },
            "collectif": {
                "terms": ["bus", "train", "métro", "tram", "avion"],
                "ideas": [
                    "l'attente collective comme lot commun",
                    "le retard comme leçon d'humilité",
                    "le voyage partagé comme micro-société",
                    "la ponctualité comme contrat social",
                ],
            },
        },
    },
    "relations": {
        "lemmas": ["chat", "chien", "oiseau", "amicale", "ami", "amie",
                   "voisin", "maman", "papa", "frère", "sœur", "enfant",
                   "phrase", "souvenir", "lettre", "message", "naissance"],
        "ideas": [
            "l'altérité qui répond sans demander",
            "la fidélité silencieuse de la relation",
            "le cohabitation comme première politique",
            "la confiance sans contrat",
        ],
        "color": "relationnelle",
        "subprofiles": {
            "felin": {
                "terms": ["chat", "chaton", "minet", "matou"],
                "ideas": [
                    "l'indifférence du chat comme leçon de dignité",
                    "la nonchalance comme philosophie pratique",
                    "le sommeil comme art de vivre",
                    "l'indépendance qui n'a pas besoin de vous",
                    "l'élégance du geste gratuit",
                    "le ronron comme métaphysique du bonheur",
                ],
            },
            "canin": {
                "terms": ["chien", "chiot", "toutou", "clebs"],
                "ideas": [
                    "la fidélité inconditionnelle comme mystère",
                    "la joie simple d'être ensemble",
                    "la loyauté sans calcul",
                    "la présence qui ne demande rien",
                    "le bonheur de la promenade",
                    "la confiance qui ne connaît pas la trahison",
                ],
            },
        },
    },
    "tech": {
        "lemmas": ["ordinateur", "téléphone", "smartphone", "bug",
                   "internet", "wifi", "écran", "clavier", "machine",
                   "application", "logiciel", "lenteur", "vitesse"],
        "ideas": [
            "la lenteur comme maximum des ambitions modernes",
            "l'outil qui nous défie de retrouver la mesure",
            "la promesse de l'efficacité",
            "le disturb de la technique dans la vie",
        ],
        "color": "technique",
    },
    "artere": {
        "lemmas": ["riche", "argent", "fortune", "pauvre", "salarié",
                   "prime", "millionnaire", "bourse", "salaire"],
        "ideas": [
            "la valeur et sa mesure",
            "l'ambition comme désir de forme",
            "la reconnaissance autant que la richesse",
            "le lien entre moyens et liberté",
        ],
        "color": "économique",
    },
    "mort": {
        "lemmas": ["mort", "mourir", "peur", "angoisse", "disparaître",
                   "fin", "disparition"],
        "ideas": [
            "la finitude qui donne poids aux instants",
            "la conscience de la limite",
            "ce qui demeure",
            "le temps comme bien précaire",
        ],
        "color": "existentielle",
    },
    "meteo": {
        "lemmas": ["pleut", "pluie", "pleuve", "soleil", "neige", "vent",
                   "orage", "nuage", "gris", "météo", "froid", "chaud"],
        "ideas": [
            "l'indifférence du ciel comme vérité",
            "le consentement au monde",
            "le décor sans ingérence",
            "le fer de l'humeur face au ciel",
        ],
        "color": "céleste",
    },
    "espace": {
        "lemmas": ["espace", "cosmos", "planète", "étoile", "galaxie",
                   "univers", "astronaute", "fusée", "voyage", "ailleurs"],
        "ideas": [
            "le dehors comme dernier horizon du désir",
            "l'échelle inoue des distances",
            "la curiosité comme premier mouvement",
            "le rêve d'ensemble",
        ],
        "color": "cosmique",
    },
    "devoirs": {
        "lemmas": ["devoirs", "devoir", "travail", "tâche", "école",
                   "examen", "corvée", "leçons", "étude", "boulot"],
        "ideas": [
            "la liberté de refuser l'obligation",
            "l'institution comme forme",
            "la discipline et ce qu'elle enseigne",
            "le devoir comme rapport à soi",
        ],
        "color": "du devoir",
    },
    "amour": {
        "lemmas": ["aimer", "aime", "amour", "adore", "adouée"],
        "ideas": [
            "l'amour comme acte de sens sans tribunal",
            "l'appréciation sans obligation de sérieux",
        ],
        "color": "affective",
    },
    "valorisation": {
        "lemmas": ["déteste", "haine", "lassitude", "dégoût", "mépris"],
        "ideas": [
            "la répulsion comme jugement sans peine",
            "la négation qui affirme",
        ],
        "color": "du refus",
    },
    "generique": {
        "lemmas": [],
        "ideas": [
            "le sens de la chose commune",
            "la profondeur cachée du quotidien",
            "ce que dit la phrase de notre rapport au monde",
            "l'aura de la banalité",
        ],
        "color": "générique",
    },
}

# ---------------------------------------------------------------- intentions

INTENT_PATTERNS: list[tuple[str, str]] = [
    (r"j'aime|j'adore|j'apprécie|aime|adorer", "aimer"),
    (r"je déteste|déteste|je n'aime pas|je hais|odiez|horreur de", "répulsion"),
    (r"j'ai faim|j'ai soif|j'ai la dalle|faim", "faim"),
    (r"j'ai peur|je crains|anxieux|angoisse|j'angoisse|peur", "peur"),
    (r"je veux|j'aimerais|je souhaite|je voudrais|je désire|veux", "désir"),
    (r"je dois|il faut|je suis obligé|je devrais|doit", "obligation"),
    (r"j'ai acheté|buyed|acheté|acquis|commande|commandé", "acquisition"),
    (r"je suis|j'ai|je me sens|état", "constatation"),
    (r"il pleut|il neige|il fait|météo", "constatation"),
]

INTENT_TO_IDEA = {
    "aimer": "l'attachement qui ne se justifie pas",
    "répulsion": "le jugement porté sans tribunal",
    "faim": "le manque comme premier savoir du corps",
    "peur": "la conscience de la finitude",
    "désir": "l'ambition comme mouvement vers la forme",
    "obligation": "la liberté face à la coerced",
    "acquisition": "le lien entre moyens et liberté",
    "constatation": "le consentement au monde",
}


@dataclass
class InputAnalysis:
    raw: str
    tokens: list[str] = field(default_factory=list)
    intent: str = "constatation"
    verb: str = ""
    object_surface: str = ""
    object_det: str = ""
    family: str = "generique"
    ideas: list[str] = field(default_factory=list)

    def object_with_article(self) -> str:
        return f"{self.object_det} {self.object_surface}".strip() if self.object_det else self.object_surface


# Article défini : certains mots sont invariables (couscous, devoirs...).
# Sinon heuristique simple.
_INVARIABLE_MASCULINE = {"couscous", "retard", "chat", "chien", "sommeil",
                         "devoir", "ordinateur", "bus", "métro", "train",
                         "travail", "tâche", "riche", "voiture", "faim",
                         "pleut", "neige"}

# mots féminins malgré la terminaison
_FEMININE_EXCEPTIONS = {"voiture", "pluie", "faim", "fatiguée", "riche",
                        "métro", "route"}

# mots féminins pluriels (déjà avec « s »)
_FEMININE_PLURAL = {"pizzas", "frites", "pâtes", "chaussures", "chaussure"}


def assign_determiner(surface: str) -> str:
    low = surface.lower()
    if re.match(r"^(le|la|l'|les|un|une|des|du|de la|de l'|d')\S", low):
        return ""  # déjà déterminé
    first = low.split()[0] if low else ""
    if not first:
        return ""
    if first in _FEMININE_PLURAL:
        return "les"
    if first in _FEMININE_EXCEPTIONS:
        return "la"
    if first in _INVARIABLE_MASCULINE:
        return "le"
    if first.endswith(("s", "x")) and len(first) > 2:
        return "les"
    if first[0] in "aeiouyéèê":
        return "l'"
    if first.endswith(("e", "ue", "ie", "ine")) and len(first) > 3:
        return "la"
    return "le"


_STOPWORDS = {
    "a", "au", "aux", "avec", "ces", "cet", "cette", "comme", "dans", "des",
    "du", "elle", "en", "encore", "est", "et", "être", "faire", "faut", "il",
    "ils", "je", "la", "le", "les", "leur", "ma", "mais", "me", "mes", "moi",
    "ne", "nos", "notre", "nous", "on", "ou", "où", "par", "pas", "peux",
    "plus", "pour", "que", "qui", "quoi", "sa", "se", "ses", "si", "son",
    "sont", "sur", "ta", "te", "tes", "toi", "ton", "tout", "très", "tu",
    "un", "une", "vais", "votre", "vous", "y", "ça", "ce", "de", "dont",
    "ai", "as", "ont", "avons", "avez", "sommes", "êtes", "était", "étais",
    "étant", "sera", "serait", "va", "vas", "allons", "font", "fait", "fais",
    "faisons", "dit", "à", "chez", "entre", "vers", "sans", "sous", "car",
    "quand", "alors", "après", "avant", "pendant", "toute", "tous",
    "aimerais", "voudrais", "souhaite", "désire", "devenir", "nouvelle",
    "nouveau", "nouvel", "nouvelles", "lent", "lente", "lents", "lentes",
    "pleut", "est", "suis", "sommes", "êtes", "sont", "étais", "était",
    "étaient", "serai", "sera", "seront", "serait", "seraient", "devenu",
    "devenue", "acheté", "achetée", "achetés", "achetées", "dois", "doit",
    "doivent", "peux", "peut", "peuvent", "veux", "veut", "veulent",
    "voyager", "dans", "aujourd'hui", "hier", "demain", "maintenant",
}


def analyze(text: str) -> InputAnalysis:
    analysis = InputAnalysis(raw=text.strip())
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text.lower())
    analysis.tokens = tokens

    # 1. intention
    scored: list[tuple[int, str]] = []
    for pattern, intent in INTENT_PATTERNS:
        if re.search(pattern, re.sub(r"\s+", " ", text.lower())):
            scored.append((len(pattern), intent))
    if scored:
        scored.sort(key=lambda x: -x[0])
        analysis.intent = scored[0][1]

    # 2. termes significatifs (les mots-clés utiles)
    sig: list[str] = []
    for t in tokens:
        stripped = t.split("'")[-1] if t.startswith(("l'", "d'", "j'", "c'", "n'", "s'", "m'", "t'", "qu'")) else t.strip("'")
        if len(stripped) >= 2 and stripped not in _STOPWORDS and stripped not in sig:
            sig.append(stripped)

    # 3. famille sémantique : le plus grand nombre de lemmas gagne ;
    # les sous-profils affinent ensuite la constellation d'idées
    best_family, best_score = "generique", 0
    for name, data in FAMILIES.items():
        if name == "generique":
            continue
        match_count = sum(1 for term in sig if any(term.startswith(lemma) or lemma.startswith(term) for lemma in data["lemmas"]))
        if match_count > best_score:
            best_family, best_score = name, match_count
    analysis.family = best_family

    # 4. objet principal : préférer le terme qui correspond à un sous-profil,
    # sinon le premier terme qui définit la famille, sinon le premier terme
    if sig:
        family_data = FAMILIES[best_family]
        obj = sig[0]
        # cherche d'abord un terme qui active un sous-profil
        if "subprofiles" in family_data:
            for term in sig:
                for profile in family_data["subprofiles"].values():
                    if any(term.startswith(t) or t.startswith(term) for t in profile["terms"]):
                        obj = term
                        break
                if obj != sig[0]:
                    break
        # sinon le premier terme qui définit la famille
        if obj == sig[0]:
            lemma_terms = []
            for term in sig:
                if any(term.startswith(lemma) or lemma.startswith(term) for lemma in family_data["lemmas"]):
                    lemma_terms.append(term)
            if lemma_terms:
                obj = lemma_terms[0]
        analysis.object_surface = obj
        analysis.object_det = assign_determiner(obj)

    # 5. constellation d'idées : sous-profil d'objet (prioritaire) + intention + famille
    ideas: list[str] = []
    family_data = FAMILIES[best_family]
    sub_ideas: list[str] = []
    if "subprofiles" in family_data and analysis.object_surface:
        for profile in family_data["subprofiles"].values():
            if any(analysis.object_surface.startswith(t) or t.startswith(analysis.object_surface) for t in profile["terms"]):
                sub_ideas.extend(profile["ideas"])
                break
    ideas.extend(sub_ideas)
    if analysis.intent in INTENT_TO_IDEA:
        ideas.append(INTENT_TO_IDEA[analysis.intent])
    ideas.extend(family_data["ideas"])
    if not ideas:
        ideas = list(FAMILIES["generique"]["ideas"])
    # pour « J'ai peur du couscous » : la famille nourriture ne doit pas
    # diluer l'angoisse — on ne garde que l'intention + quelques idées
    # existentielles (pas les idées alimentaires)
    if analysis.intent == "peur":
        ideas = [INTENT_TO_IDEA["peur"]] + FAMILIES["mort"]["ideas"]
    analysis.ideas = ideas
    return analysis


# ---------------------------------------------------------------- problématique

def _find_subprofile(a: InputAnalysis) -> str | None:
    """Retourne le nom du sous-profil actif, ou None."""
    if not a.object_surface:
        return None
    family_data = FAMILIES.get(a.family, {})
    if "subprofiles" not in family_data:
        return None
    for pname, profile in family_data["subprofiles"].items():
        for term in profile["terms"]:
            if a.object_surface.startswith(term) or term.startswith(a.object_surface):
                return pname
    return None


def formulate_problematic(a: InputAnalysis) -> str:
    """Construit la question qui engage le texte — liée au sens, pas au vocabulaire."""
    obj = a.object_with_article() or "ceci"
    if a.intent == "aimer" and a.family == "nourriture":
        # la problématique varie selon le sous-profil de l'objet
        sub = _find_subprofile(a)
        if sub == "festif":
            return f"Pourquoi {obj} est-il devenu le symbole d'une joie partagée sans prétention ?"
        if sub == "traditionnel":
            return f"Pourquoi {obj} porte-t-il en lui la mémoire des gestes transmis ?"
        if sub == "quotidien":
            return f"Pourquoi {obj} structure-t-il nos jours comme un rituel du matin ?"
        if sub == "fête":
            return f"Pourquoi {obj} incarne-t-il la célébration comme art de vivre ?"
        return f"Pourquoi une chose aussi simple que {obj} peut-elle devenir une source de plaisir, de mémoire et d'attachement ?"
    if a.intent == "répulsion":
        return f"Que vaut un « non » porté volontairement contre {obj} — et que nous dit-il de notre liberté ?"
    if a.intent == "faim":
        return "Pourquoi le manque sait-il si bien nous rappeler que nous sommes un corps avant d'être un sujet ?"
    if a.intent == "peur":
        return f"De quoi {obj} est-il le nom, et comment la conscience de la limite influe ce qui demeure ?"
    if a.intent == "désir":
        if a.family == "artere":
            return "Qu'est-ce que vouloir devenir riche, et que promet cette chose sur notre rapport aux valeurs ?"
        return f"Qu'est-ce que vouloir {obj}, et que promet cette chose sur notre rapport aux valeurs ?"
    if a.intent == "obligation" and a.family in ("devoirs", "work", "tâche"):
        return "Comment du devoir le plus simple se lit-il notre rapport à la liberté et aux institutions ?"
    if a.intent == "acquisition":
        return f"Que promet {obj} au sujet de la liberté, de la valeur et de la reconnaissance ?"
    if a.family == "sommeil" or (a.family == "relations" and "dort" in a.raw.lower()):
        return "Que signifie que quelqu'un — même un animal — s'abandonne au sommeil dans un monde qui ne dort jamais ?"
    if a.family == "fatigue":
        return "Qu'est-ce que le corps demande quand il dit « je suis fatigué », et quel savoir porte-t-il ?"
    if a.family == "meteo":
        return "Comment le ciel se contente-t-il de faire, sans demander notre avis — et pourquoi cela nous console-t-il ou nous offense ?"
    if a.family == "artere":
        return "Que vaut la valeur, et la reconnaissance vaut-elle le rêve ?"
    if a.family == "transport":
        return "L'attente au bord du trafic est-elle une philosophie vécue ou une simple difficulté ?"
    if a.family == "tech":
        return "L'outil lent défie-t-il nos ambitions modernes, ou nous invite-t-il à retrouver la mesure ?"
    if a.family == "relations":
        return "Qu'est-ce que cohabiter avec une altérité qui répond sans demander de compte ?"
    if a.family == "espace":
        return "Pourquoi le « ailleurs » demeure-t-il le dernier horizon du désir ?"
    return f"Que dit la phrase « {a.raw} » de notre rapport au monde ?"
