"""Fixtures de test : la suite s'exécute en mode "modèle local indisponible"
(état réel du runtime quand llama-server est éteint) pour rester hermétique
et rapide — le chemin LLM est couvert par les tests de construction de prompt
et de post-traitement de tests/test_llm.py."""

import time

import pytest

from app.generation import llm


@pytest.fixture(autouse=True)
def _llm_indisponible():
    """Pré-remplit le cache de santé : sonde négative, comme si le serveur
    de modèle était arrêté."""
    llm._health_ok = time.monotonic()
    llm._health_state = False
    yield
    llm._health_ok = None
    llm._health_state = False
