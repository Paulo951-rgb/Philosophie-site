# Le Grand Philosophe

Transforme une phrase banale (« j'ai faim », « le bus est en retard ») en
réflexion philosophique exagérément sérieuse — subtile ou totalement
caricaturale.

> **Objectif** : transformez n'importe quoi en traité de métaphysique.
> Aucune clé d'API externe, aucun compte, entièrement gratuit : le moteur
> est un vrai modèle de langage qui tourne sur votre machine.

## Fonctionnalités

- **Générateur paramétrable** : profondeur (légère → métaphysique), exagération
  (sérieux → prend beaucoup trop au sérieux), styles (13 fiches, combinaison 1-2),
  longueur (50 à ~1500 mots), registre (simple → complètement pompeux).
- **Modes spéciaux** : Réflexion libre, Dissertation (I./II./III./Conclusion),
  Citation avec attribution **forcément fictive**.
- **Boutons magiques** (9 actions de transformation sur le texte généré) dont
  « Retour à la réalité », qui referme toujours le texte sur la chute banale.
- **Cartes de partage** : export canvas (story 1080×1920, carré 1080×1080,
  paysage 1200×630), téléchargement PNG, Web Share, lien public `/carte/<id>`
  avec Open Graph dynamique (image OG rendue côté serveur en Pillow).
- **Historique local** (localStorage, 300 entrées) avec recherche full-text,
  filtre par style, favoris et vue galerie.
- Thèmes sombre / clair / auto. Interface entièrement responsive.

Le moteur principal est un **vrai modèle de langage local** : llama.cpp
(`llama-server`) servant Qwen2.5-3B-Instruct (GGUF Q4, ~2 Go) sur le port
8090. Aucune clé d'API, aucun service externe, aucune donnée ne quitte la
machine. `app/generation/llm.py` construit les prompts à partir des 5
paramètres + fiches de style + mode, post-traite la sortie (nettoyage
markdown, filtre anti-attribution à de vrais philosophes) et retombe
automatiquement sur le moteur procédural (`engine.py`) si le modèle est
indisponible.

## Lancement

### Clonage

```bash
git clone https://github.com/Paulo951-rgb/Philosophie-site.git
cd Philosophie-site
pip install -r requirements.txt
./start.sh    # démarre le modèle local (port 8090) + l'app (port 12000)
```

### Dépendances système

Le moteur LLM utilise un binaire llama.cpp compilé pour la machine cible :
`télécharger/compilez llama.cpp` puis posez le binaire où vous voulez.
Le modèle GGUF attendu par défaut est **Qwen2.5-3B-Instruct** (Q4_K_M) ;
tout autre GGUF compatible fonctionne (prendre un modèle léger si priorité
vitesse).

### Variables de configuration

| Variable | Défaut | Description |
|---|---|---|
| `LLAMA_BIN` | `/workspace/llama/llama-b10632/llama-server` | Chemin du binaire llama.cpp |
| `MODEL` | `/workspace/models/qwen2.5-3b-instruct-q4_k_m.gguf` | Chemin du modèle GGUF |
| `LLAMA_PORT` | `8090` | Port du serveur de génération |
| `APP_PORT` | `12000` | Port de l'application FastAPI |

Sans modèle, l'application fonctionne en mode procédural dégradé (le site
est utilisable, sans le style d'un vrai modèle).

Ouvrir http://localhost:12000

## Tests

```bash
pip install pytest httpx
python -m pytest -q
```

## Structure

```
app/
├── main.py              # FastAPI : SPA + API + pages publiques OG
├── schemas.py           # validation des requêtes
├── cards.py             # magasin de cartes + rendu PNG serveur
├── generation/
│   ├── engine.py        # dispatch LLM/procédural + composition des réflexions
│   ├── llm.py           # appels au serveur local, prompts, post-traitement
│   ├── analysis.py      # analyseur sémantique du texte d'entrée
│   ├── styles.py        # 13 fiches de style
│   ├── lexicon.py       # concepts, connecteurs, attributions fictives
│   ├── transforms.py    # les 9 boutons magiques
│   └── safety.py        # filtre anti-attribution à de vrais philosophes
└── static/
    ├── index.html       # SPA (toutes les vues)
    ├── css/app.css      # design system (sombre par défaut, or, papier)
    └── js/              # app.js (générateur), history.js, cards.js
```

## Avertissement produit

Aucun texte généré n'est attribué à un vrai philosophe ni à une personne
réelle ; le filtre `safety.py` supprime tout nom réel même s'il apparaît dans
l'entrée utilisateur. Les cartes du mode Citation portent un badge
« citation humoristique · attribution fictive ».
