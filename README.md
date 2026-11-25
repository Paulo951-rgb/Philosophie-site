# Le Grand Philosophe

Transforme une phrase banale (« j'ai faim », « le bus est en retard ») en
réflexion philosophique exagérément sérieuse — subtile ou totalement
caricaturale.

> **Objectif** : transformer n'importe quoi en traité de métaphysique.
> Le site utilise par défaut un véritable modèle de langage distant via LLM Faucet :
> aucun modèle à télécharger et aucune clé API personnelle à fournir.

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

Le moteur principal est un **véritable modèle de langage cloud** via
[LLM Faucet](https://llmfaucet.dev), une passerelle compatible OpenAI qui route
vers des fournisseurs anonymes/keyless. Le backend appelle
`https://api.llmfaucet.dev/v1` avec le modèle `auto:smart` : aucun modèle
n'est téléchargé sur l'ordinateur et aucune clé API personnelle n'est requise.
`app/generation/llm.py` construit les prompts à partir des paramètres et des
styles, puis nettoie et sécurise la réponse. En mode cloud, une panne du
fournisseur renvoie une erreur explicite : le générateur procédural ne fabrique
jamais de résultat à la place de l'IA.

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
| AI_PROVIDER | cloud | `cloud` (défaut) ou `local` pour llama.cpp |
| AI_API_KEY | free | Valeur publique documentée par LLM Faucet ; aucune clé personnelle |
| AI_BASE_URL | https://api.llmfaucet.dev/v1 | URL de la passerelle compatible OpenAI |
| AI_MODEL | auto:smart | Routage automatique vers un modèle adapté |
| LLM_URL | http://127.0.0.1:8090 | URL llama.cpp si `AI_PROVIDER=local` |
| `LLAMA_BIN` | `/workspace/llama/llama-b10632/llama-server` | Chemin du binaire llama.cpp |
| `MODEL` | `/workspace/models/qwen2.5-3b-instruct-q4_k_m.gguf` | Chemin du modèle GGUF |
| `LLAMA_PORT` | `8090` | Port du serveur de génération |
| `APP_PORT` | `12000` | Port de l'application FastAPI |

Le mode cloud est activé par défaut : sur votre hébergeur, aucune variable n'est nécessaire pour commencer. Vous pouvez laisser les valeurs par défaut ou définir `AI_BASE_URL`, `AI_MODEL` et éventuellement `AI_API_KEY` dans les variables d'environnement du backend. N'exposez jamais ces variables au JavaScript. L'offre anonyme LLM Faucet annonce actuellement 20 requêtes par jour et par IP ; elle est expérimentale et sa capacité peut changer ou disparaître. Pour un site public, prévoyez donc un quota applicatif et un fournisseur plus robuste si l'audience augmente.

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


## IA cloud sans clé personnelle

Le fournisseur par défaut est LLM Faucet :

- Base URL : `https://api.llmfaucet.dev/v1`
- Modèle : `auto:smart`
- Valeur d'authentification publique : `free` (pas de clé personnelle)
- Endpoint utilisé : `POST /chat/completions`

Le backend relaie les requêtes : aucune URL ni donnée d'authentification n'est exposée dans le navigateur. LLM Faucet annonce un quota anonyme de 20 requêtes par jour et par IP et précise que le service est expérimental. Les visiteurs d'un même déploiement partagent donc potentiellement le quota de l'adresse IP du serveur. Ce fournisseur convient à un prototype/démonstrateur, pas à un service public dont la disponibilité doit être garantie.

Pour utiliser un serveur llama.cpp local à la place : définir `AI_PROVIDER=local`. Si le fournisseur cloud est indisponible ou atteint son quota, l'API renvoie HTTP 503 ; elle ne bascule jamais vers les textes préfabriqués.
