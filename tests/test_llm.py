"""Tests du module llm : construction des prompts, post-traitement,
repli procédural quand le modèle local est éteint."""

from app.generation import generate
from app.generation.engine import LENGTH_WORDS
from app.generation.llm import (
    _postprocess,
    _split_attribution,
    _TRANSFORM_INSTRUCTIONS,
    build_generation_prompt,
    build_transform_prompt,
    generate_llm,
)
from app.generation.styles import STYLES


def _prompt(**kw):
    params = dict(
        input_text="J'aime le couscous",
        depth="profond", exaggeration="subtile", styles=["francais"],
        length="moyen", complexity="soutenu", mode="standard",
        style_defs=STYLES, length_words=LENGTH_WORDS,
    )
    params.update(kw)
    return build_generation_prompt(**params)


class TestBuildPrompt:
    def test_le_prompt_contient_la_phrase(self):
        _, user, _, _ = _prompt()
        assert "J'aime le couscous" in user

    def test_le_prompt_contient_les_regles_de_securite(self):
        system, _, _, _ = _prompt()
        assert "philosophe réel" in system
        assert "Kant" in system  # exemples explicites d'interdits

    def test_le_prompt_contient_le_style(self):
        system, _, _, _ = _prompt(styles=["existentialiste"])
        assert "Existentialiste" in system

    def test_fusion_deux_styles_demandee(self):
        system, _, _, _ = _prompt(styles=["existentialiste", "poetique"])
        assert "Fusionne" in system

    def test_la_longueur_influe_sur_les_mots_et_tokens(self):
        _, user_court, tok_court, _ = _prompt(length="court")
        _, user_long, tok_long, _ = _prompt(length="tres-long")
        assert "50" in user_court and "700" in user_long
        assert tok_court < tok_long

    def test_la_complexite_change_le_registre(self):
        sys_simple, _, _, _ = _prompt(complexity="simple")
        sys_pompeux, _, _, _ = _prompt(complexity="pompeux")
        assert "courant" in sys_simple
        assert "incompréhensible" in sys_pompeux

    def test_mode_dissertation_impose_la_structure(self):
        _, user, max_tokens, _ = _prompt(mode="dissertation", length="long")
        for titre in ("Introduction", "I.", "II.", "III.", "Conclusion"):
            assert titre in user
        assert max_tokens >= 700

    def test_mode_citation_impose_attribution_fictive(self):
        _, user, _, _ = _prompt(mode="citation")
        assert "FICTIVE" in user
        assert "inventé" in user

    def test_chaque_action_de_transformation_a_une_consigne(self):
        attendues = {"plus-profond", "plus-pretentieux", "explique-vie",
                     "version-francais", "version-47", "reduit-une-phrase",
                     "retour-realite", "plus-serieux", "plus-absurde"}
        assert set(_TRANSFORM_INSTRUCTIONS) == attendues

    def test_prompt_transform_injecte_le_texte_precedent(self):
        _, user, _ = build_transform_prompt(
            "plus-pretentieux", "Texte déjà généré.", "J'ai faim")
        assert "Texte déjà généré." in user
        assert "J'ai faim" in user


class TestPostprocess:
    def test_retire_le_markdown(self):
        assert "**" not in _postprocess("**Gras** et _italique_")

    def test_retire_la_preface_meta(self):
        out = _postprocess("Voici la réflexion demandée :\nLe vrai texte.")
        assert out.startswith("Le vrai texte.")

    def test_guillemets_droits_convertis(self):
        out = _postprocess('Il dit "j\'ai faim" au monde.')
        assert "« j'ai faim »" in out

    def test_split_attribution(self):
        quote, attr = _split_attribution(
            "Le pain est une métaphysique du matin.\n— Hilaire de Jonquille, penseur du mardi")
        assert quote == "Le pain est une métaphysique du matin."
        assert attr.startswith("— Hilaire de Jonquille")

    def test_split_attribution_ne_decoupe_pas_un_tiret_dans_le_corps(self):
        """Régression : un « — » en plein corps du texte ne doit pas être
        confondu avec la ligne d'attribution."""
        corps = "Première pensée — elliptique — dans le brouillard.\nSeconde pensée."
        quote, attr = _split_attribution(corps)
        assert attr is None
        assert quote == corps

    def test_split_sans_attribution(self):
        quote, attr = _split_attribution("Juste une phrase.")
        assert attr is None and quote == "Juste une phrase."


class TestFallback:
    def test_repli_procedural_quand_modele_eteint(self):
        """Sans serveur de modèle (fixture conftest), generate() retombe
        sur le moteur procédural."""
        out = generate("J'aime le couscous", seed=3)
        assert out["engine"] == "procedural"
        assert "couscous" in out["text"].lower()

    def test_generate_llm_renvoie_none_sans_serveur(self):
        assert generate_llm("J'ai faim", "profond", "subtile", ["francais"],
                            "moyen", "soutenu", "standard", STYLES,
                            LENGTH_WORDS) is None
