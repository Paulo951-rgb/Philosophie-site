"""Garde-fou de sécurité éditoriale.

Règle absolue du produit : ne jamais émettre le nom d'un philosophe réel
(citation inventée, attribution, "comme disait X"). Même en plaisanterie.
Le filtre ci-dessous est une dernière rampe : le moteur est procédural
et n'utilise pas de citations du monde, mais le texte d'entrée
utilisateur pourrait contenir un tel nom ; on le retire du flux et on
le remplace par un néologisme comique.
"""

import re

# Liste non exhaustive mais large, volontairement conservative.
REAL_PHILOSOPHERS = [
    "Platon", "Aristote", "Socrate", "Épicure", "Épictète", "Sénèque",
    "Marc Aurèle", "Plotin", "Augustin", "Thomas d'Aquin", "Descartes",
    "Spinoza", "Leibniz", "Locke", "Hume", "Kant", "Hegel", "Marx",
    "Nietzsche", "Kierkegaard", "Schopenhauer", "Bergson", "Husserl",
    "Heidegger", "Wittgenstein", "Russell", "Sartre", "Camus", "Beauvoir",
    "Merleau-Ponty", "Lévinas", "Ricœur", "Derrida", "Foucault", "Deleuze",
    "Rousseau", "Voltaire", "Diderot", "Montaigne", "Pascal", "Alain",
    "Machiavel", "Hobbes", "Bentham", "Mill", "Confucius", "Lao Tseu",
    "Heraclite", "Parménide", "Épicure", "Cicéron", "Ribot", "Ozanam",
]

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in sorted(REAL_PHILOSOPHERS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

_SUBSTITUTES = [
    "un penseur oublié des catalogues",
    "un philosophe de liquide vaisselle",
    "un académicien du buffet froid",
    "un oracle en congé",
    "une sommité de la quatrième logos",
]


def scrub(text: str, rng=None) -> str:
    """Remplace toute occurrence d'un nom de philosophe réel.

    Retourne le texte filtré ; jamais modifié si le filtre ne trouve rien.
    """
    def _rep(m: re.Match) -> str:
        if rng is not None:
            return rng.choice(_SUBSTITUTES)
        return _SUBSTITUTES[0]

    return _PATTERN.sub(_rep, text)


def contains_real_philosopher(text: str) -> bool:
    return bool(_PATTERN.search(text))
