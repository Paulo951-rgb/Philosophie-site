# Mémoire du dépôt — Le Grand Philosophe

## Stack & lancement

- Backend : FastAPI + Uvicorn (Python 3.13), frontend : SPA vanilla JS/CSS
  servie par `/static` (pas de build step).
- Démarrage : `./start.sh` (modèle local + app) ou
  `python -m uvicorn app.main:app --host 0.0.0.0 --port 12000` seul
  (repli procédural si le modèle est éteint).
- **LLM local** : llama.cpp binaire dans `/workspace/llama/` (hors dépôt),
  modèle GGUF Qwen2.5-3B Q4_K_M dans `/workspace/models/` (hors dépôt, ~2 Go),
  servi sur `127.0.0.1:8090`. ~8 tok/s sur 4 cœurs → « moyen » ≈ 25 s.
- Tests : `python -m pytest -q` (63 tests, hermétiques : `tests/conftest.py`
  simule le modèle éteint pour forcer le chemin procédural).

## Conventions du moteur de génération

- Génération par **LLM local** (`app/generation/llm.py`) : construit
  système+utilisateur à partir des 5 paramètres + fiches de style + mode ;
  `generate()`/`transform()` d'`engine.py` essaient le LLM puis retombent
  sur le moteur procédural si `llm.generate_llm`/`transform_llm` → None.
- Le moteur procédural (analysis.py + engine.py) reste le filet de sécurité :
  les 5 paramètres doivent chacun produire un effet perceptible — jamais
  cosmétique.
- Les gabarits français vivent dans `generation/styles.py` (13 fiches) et
  `generation/lexicon.py`. Toute nouvelle phrase doit être du français
  grammaticalement propre : éviter les prépositions devant « le/la/l'… » des
  concepts (utiliser les gabarits en `chez {concept}` / « à ce qu'on nomme… »).
- `safety.py` : jamais de vrai philosophe (Kant, Camus…) dans les sorties —
  le scrubber s'applique à la génération ET aux transformations.
- « Retour à la réalité » doit toujours se terminer par la chute banale
  (dernier paragraphe contenant le texte original).
- Le mode Citation produit une attribution fictive + badge
  « citation humoristique · attribution fictive » sur les exports.

## Pièges rencontrés

- FastAPI : déclarer `/carte/{id}.png` AVANT `/carte/{id}` sinon le .png est
  capturé comme id HTML.
- `[hidden]` perd contre `display: grid` en CSS — la règle
  `[hidden]{display:none!important}` existe dans app.css.
- L'historique est 100% localStorage (clé `gp.history`, 300 entrées max) ;
  les cartes publiques sont persistées côté serveur dans `data/cards.json`.
- Le rendu PNG serveur (Pillow) utilise les polices DejaVu Serif de
  /usr/share/fonts/truetype/dejavu ; le canvas client utilise les Google Fonts
  (Fraunces/EB Garamond/Inter).

## État du cahier des charges

- MVP V1 : complet (générateur, animation, boutons magiques, cartes,
  historique, thèmes, responsive).
- V1.5 intégrée : modes Dissertation + Citation ; recherche + favoris.
  L'authentification n'est PAS implémentée (historique local choisi).
- V2 non implémentée (Duel, Portrait, audio, débat, etc.) — pistes listées
  sur la page À propos.
