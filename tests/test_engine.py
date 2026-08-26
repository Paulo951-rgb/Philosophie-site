"""Tests du moteur de génération et des transformations."""

import pytest

from app.generation import generate, transform
from app.generation.engine import LENGTH_WORDS
from app.generation.styles import STYLES
from app.generation.transforms import TRANSFORM_ACTIONS
from app.generation.safety import contains_real_philosopher, scrub


INPUT = "Je dois acheter du pain."


class TestStyles:
    def test_thirteen_styles(self):
        assert len(STYLES) == 13

    def test_style_fiche_complete(self):
        for sid, fiche in STYLES.items():
            for key in ("label", "desc", "vocab", "openers", "signatures", "closers", "aphorisms"):
                assert fiche[key], f"style {sid} sans {key}"


class TestGenerate:
    def test_coherence_semantique(self):
        """La réflexion parle du sujet : problématique explicite + retour
        contrasté à la phrase initiale."""
        generated = generate(
            "J'aime le couscous", styles=["francais"], mode="standard", seed=11
        )
        text = generated["text"]
        assert "couscous" in text.lower()
        # la problématique ou le corps doit évoquer le sens (pas juste le mot)
        assert any(word in text.lower() for word in ("plaisir", "mémoire", "goût", "partage"))

    def test_separation_semantique(self):
        """Deux phrases avec même structure mais intention/objet différents
        produisent des réflexions différentes."""
        aimer = generate("J'aime le couscous", seed=7)
        peur = generate("J'ai peur du couscous", seed=7)
        assert aimer["text"] != peur["text"]
        # les mots-clés sémantiques diffèrent
        assert "plaisir" in aimer["text"].lower() or "mémoire" in aimer["text"].lower()
        assert "finitude" in peur["text"].lower() or "limite" in peur["text"].lower()

    def test_standard_produit_du_texte(self):
        r = generate(INPUT, seed=1)
        assert r["text"]
        assert r["word_count"] > 10

    def test_deterministe_avec_seed(self):
        a = generate(INPUT, seed=42)
        b = generate(INPUT, seed=42)
        assert a["text"] == b["text"]

    def test_styles_multi_max_deux(self):
        r = generate(INPUT, styles=["francais", "poetique", "absurde"], seed=3)
        assert len(r["prompt_details"]["styles"]) <= 2

    @pytest.mark.parametrize("length", list(LENGTH_WORDS))
    def test_parametre_longueur_produit_profils_differents(self, length):
        r = generate(INPUT, length=length, seed=7)
        assert r["text"]

    def test_fusion_deux_styles(self):
        solo = generate(INPUT, styles=["existentialiste"], seed=7)
        duo = generate(INPUT, styles=["existentialiste", "poetique"], seed=7)
        assert solo["text"] != duo["text"]

    def test_citation_attribution_fictive(self):
        r = generate(INPUT, mode="citation", seed=11)
        assert r["attribution"].startswith("—")
        assert not contains_real_philosopher(r["attribution"])
        assert not contains_real_philosopher(r["text"])

    def test_dissertation_structure(self):
        r = generate(INPUT, mode="dissertation", seed=2)
        for marker in ("I. ", "II. ", "III. ", "Conclusion"):
            assert marker in r["text"]

    def test_pqdm_sous_titres(self):
        r = generate(INPUT, length="pqdm", seed=5)
        assert "### " in r["text"]

    @pytest.mark.parametrize("mode", ["standard", "dissertation", "citation"])
    def test_safety_noms_reels_scrubs(self, mode):
        r = generate("comme disait Descartes et Nietzsche ensemble", mode=mode, seed=1)
        all_text = r["text"] + " " + (r.get("attribution") or "")
        assert not contains_real_philosopher(all_text)

    def test_input_trop_longue_coupee(self):
        r = generate("x " * 2000, seed=1)
        assert r["text"]


class TestTransforms:
    def test_retour_realite_termine_sur_la_chute(self):
        base = generate(INPUT, seed=1)
        t = transform("retour-realite", base["text"], INPUT, ["francais"], seed=4)
        last_para = t["text"].rstrip().split("\n\n")[-1]
        assert INPUT in last_para

    @pytest.mark.parametrize("action", list(TRANSFORM_ACTIONS))
    def test_chaque_action_disponible(self, action):
        base = generate(INPUT, seed=1)
        t = transform(action, base["text"], INPUT, ["francais"], seed=8)
        assert t["text"]
        assert t["word_count"] > 0

    def test_action_inconnue_rejete(self):
        with pytest.raises(ValueError):
            transform("action-nulle", "texte", INPUT)

    def test_safety_appliquer_aux_transforms(self):
        base = "Texte contenant Descartes par malheur."
        t = transform("plus-profond", base, INPUT, seed=1)
        assert not contains_real_philosopher(t["text"])


class TestSafetyModule:
    def test_scrub_remplace_les_penseurs_reels(self):
        out = scrub("Une pensée, comme disait Kant.")
        assert not contains_real_philosopher(out)

    def test_scrub_ne_touche_pas_au_reste(self):
        text = "Rien d'interdit ici."
        assert scrub(text, None) == text
