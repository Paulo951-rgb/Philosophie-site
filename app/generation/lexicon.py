"""Lexique destinataire du moteur : concepts, registres, attributions.

Tout le contenu généré est assemblé à partir de gabarits internes.
Le filtre de sécurité (safety.py) veille en outre à ce qu'aucun nom de
philosophe réel ne soit jamais émis par le moteur.
"""

# --------------------------------------------------------------- concepts

CONCEPTS = [
    "la finitude", "le désir", "la condition humaine", "le temps",
    "l'altérité", "le néant", "la liberté", "l'être", "le devenir",
    "la contingence", "l'essence", "l'existence", "la substance",
    "l'accident", "le destin", "la nécessité", "le possible",
    "la conscience", "l'apparence", "le vide", "le trop-plein",
    "le manque", "l'habitude", "la banalité du quotidien", "le geste quotidien",
    "la répétition", "l'attente", "la présence", "l'absence",
]

OPPOSITIONS = [
    ("la servitude du besoin", "la souveraineté du choix"),
    ("la pesanteur du monde", "la légèreté de l'esprit"),
    ("l'immuable", "le fugace"),
    ("la faim de l'être", "l'être de la faim"),
    ("la contrainte", "l'affranchissement"),
    ("le déjà-là", "le pas-encore"),
    ("l'ordre des choses", "le désordre des désirs"),
    ("la banalité", "l'absolu"),
]

# ------------------------------------------------------------ connectors

CONNECTORS_SIMPLE = ["et", "mais", "alors", "car"]
CONNECTORS_SOUTENU = ["or", "certes", "en vérité", "au demeurant",
                      "d'aucuns diront", "qu'il soit bien entendu"]
LATIN_ASIDES = ["in abstracto", "sub specie aeternitatis", "a priori",
                "ipso facto", "mutatis mutandis", "qua", "sic erat in principio",
                "de facto et de jure", "ex nihilo", "in potentia"]
GREEK_TERMS = ["l'apologie du banal", "l'onto-théologie du repas",
               "le kath' héautón de l'objet", "la phusis du banal",
               "l'epochè face au quotidien", "l'aporia fondatrice",
               "le logos du banal", "le pathos de l'ordinaire"]

# --------------------------------------- substitutions pour registre élevé

POMPOUS_SWAPS = {
    "très": "infiniment",
    "donc": "partant",
    "alors": "dès lors",
    "mais": "or",
    "grand": "considérable",
    "vrai": "véridique",
    "chose": "res extensa",
    "idée": "topos",
    "question": "problème (cf. infra)",
    "simple": "pur",
    "pense": "conceptualise",
    "vie": "existence précaire",
    "monde": "cosmos contingens",
}

# swap inversé pour « Rendre plus sérieux » : on rabat le décorum
SERIOUS_SWAPS = {v: k for k, v in POMPOUS_SWAPS.items()}

# ------------------------------------------------- anim. & aperçu profil

EXAGGERATION_DESC = {
    "serieux": "d'une probité presque crédible",
    "subtile": "sérieux en apparence, fêlé en filigrane",
    "dramatique": "tragique dans l'âme",
    "caricatural": "comique assumé d'emblée",
    "trop-serieux": "sincèrement bouleversé par rien",
}

# ----------------------------------------- chutes pour « Retour à la réalité »

CHUTES = [
    "Enfin, disons-le simplement : « {input} ». Tout ceci pour cela.",
    "Bref. Écartons le théâtre : « {input} ». La métaphysique attendra le dîner.",
    "Ou, pour parler le langage du commun des mortels : « {input} ».",
    "Résumons l'opuscule entier en une note de bas de page : « {input} ».",
    "Et le sage, en tirant sa langue de la joue, conclut : « {input} ».",
]

# --------------------------------------------------- attributions fictives

FIRST_NAMES = ["Julien", "Tilde", "Casimir", "Vernelle", "Odon", "Ysaure",
               "Gonthier", "Pancrace", "Lélianne", "Rubis", "Taurin",
               "Éponine-Glacine", "Witolf", "Salmigondis", "Esmée"]
EPITHETS = ["philosophe de comptoir", "penseur du dimanche soir",
            "essayiste des corridors", "chroniqueur du vide majeur",
            "moraliste et interprète", "sage des buffets froids",
            "docteur ès bagatelles", "herméneute du banal",
            "métaphysicien amateur", "sophiste repenti",
            "académicien des sirops"]
CENTURIES = ["XXIe siècle", "XXIIe siècle (par anticipation)", "ère du soupir",
             "temps modernes", "posthume d'avance", "sans date précise",
             "notre ère, à son corps défendant"]

# sous-titres ironiques pour la longueur « Pourquoi ai-je demandé ça ? »
PQDM_SUBTITLES = [
    "Avant-propos inutile mais nécessaire",
    "Chapitre premier — où l'auteur prend son temps",
    "Intermède méthodique",
    "Chapitre second — du rien comme problème",
    "Digression que le lecteur sautera à ses risques",
    "Chapitre dernier — récapitulation fatidique",
    "Postface de l'auteur à lui-même",
    "Appendice des compléments indispensables",
]

# mots amoureux pour la page à l'ambiance feutrée
AMBIENT_LOADING = [
    "Consultation des ombres de la caverne…",
    "Interrogation du sens de l'existence…",
    "Pesée des mots avec gravité…",
    "Lecture des Anciens sous la lampe…",
    "Affûtage du concept sur la meule…",
    "Déploiement du syllogisme…",
    "Écoute du silence interconceptuel…",
    "Feuilletage du grand in-octavo…",
    "Frottement du doute sur le parchemin…",
    "Appel de la dialectique au chevet du banal…",
]

# mots-concepts élevés (utilisés pour gonfler « très profond »/« métaphysique »)
DEEP_MOVES = [
    "et ce n'est pas le moindre des paradoxes",
    "ce qui, à bien y songer, renvoie le sujet à sa propre opacité",
    "étant entendu que toute question en cache une autre",
    "s'il est permis de parler ainsi",
    "entre parenthèses de l'être",
    "dans le clair-obscur de la pensée",
    "sur le seuil de l'indicible",
    "à l'intersection du sens et du soupir",
]
