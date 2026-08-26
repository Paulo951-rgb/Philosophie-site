"""Tests de l'API et du rendu des cartes."""

import os

os.environ.setdefault("GRAND_DATA_DIR", "data-test")

from fastapi.testclient import TestClient

from app import cards
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


class TestMeta:
    def test_meta_public(self):
        r = client.get("/api/meta")
        assert r.status_code == 200
        data = r.json()
        assert len(data["styles"]) == 13
        assert data["defaults"]["mode"] == "standard"


class TestGenerateAPI:
    def test_generate_ok(self):
        r = client.post("/api/generate", json={
            "input_text": "J'ai faim.",
            "depth": "profond",
            "exaggeration": "subtile",
            "styles": ["francais"],
            "length": "court",
            "complexity": "soutenu",
            "mode": "standard",
        })
        assert r.status_code == 200
        assert r.json()["text"]

    def test_generate_entrees_invalidees_fallbacks(self):
        r = client.post("/api/generate", json={
            "input_text": "Test.",
            "depth": "excessif",
            "styles": ["inconnu"],
            "mode": "bizarre",
        })
        assert r.status_code == 200
        assert r.json()["params"]["depth"] == "profond"
        assert r.json()["params"]["styles"] == ["francais"]

    def test_input_plus_de_2000_chars(self):
        r = client.post("/api/generate", json={"input_text": "a " * 5000})
        assert r.status_code == 200


class TestTransformAPI:
    def test_transform_ok(self):
        r = client.post("/api/transform", json={
            "action": "retour-realite",
            "previous_text": "Texte dense.",
            "original_input": "j'ai faim",
        })
        assert r.status_code == 200
        assert "j'ai faim" in r.json()["text"].split("\n\n")[-1]

    def test_transform_action_inconnue(self):
        r = client.post("/api/transform", json={
            "action": "brouillon", "previous_text": "x",
        })
        assert r.status_code == 400


class TestCards:
    def _create(self):
        r = client.post("/api/cards", json={
            "input_text": "Mon chat dort.",
            "generated_text": "Le repos du félin expose le néant du bruit du monde.",
            "attribution": None,
            "mode": "standard",
            "styles": ["poetique"],
        })
        assert r.status_code == 200
        return r.json()["id"]

    def test_create_and_get(self):
        cid = self._create()
        g = client.get(f"/api/cards/{cid}")
        assert g.status_code == 200
        assert g.json()["generated_text"].startswith("Le repos")

    def test_card_page_avec_og(self):
        cid = self._create()
        p = client.get(f"/carte/{cid}")
        assert p.status_code == 200
        assert 'property="og:image"' in p.text
        assert "og:description" in p.text

    def test_card_png_landscape_story_square(self):
        cid = self._create()
        for fmt in ("story", "square", "landscape"):
            r = client.get(f"/carte/{cid}.png?format={fmt}")
            assert r.status_code == 200
            assert r.headers["content-type"] == "image/png"
            assert r.content[:4] == b"\x89PNG"

    def test_card_unknown_404(self):
        assert client.get("/api/cards/nul-id").status_code == 404
        assert client.get("/carte/nul-id").status_code == 404

    def test_render_badge_citation(self):
        img = cards.render_card(
            {"generated_text": "Le néant n'abonde pas.",
             "attribution": "— Tilde, sage des buffets froids, XXIe siècle"},
            "story",
        )
        assert img.size == (1080, 1920)


class TestShellPages:
    def test_shell_routes(self):
        for path in ["/", "/histoire", "/favoris", "/a-propos", "/parametres"]:
            r = client.get(path)
            assert r.status_code == 200
            assert "Le Grand Philosophe" in r.text


class TestHardening:
    def test_card_id_malformed_404_et_pas_injection(self):
        """Un id non-hex ne doit jamais atteindre le template HTML."""
        assert client.get("/carte/bad'\"id").status_code == 404
        assert client.get("/carte/bad'\"id.png?format=landscape").status_code == 404

    def test_500_renvoie_un_json_propre(self):
        """Le handler global évite la page d'erreur brute de Starlette."""
        from app import cards
        original = cards.get_card
        cards.get_card = lambda cid: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            r = client.get("/carte/" + "ab" * 5)
            assert r.status_code == 500
            assert "detail" in r.json()
        finally:
            cards.get_card = original

    def test_plafond_fifo_des_cartes(self):
        """Le magasin local purge les plus anciennes entrées au-delà du plafond."""
        from app import cards
        limit = cards.MAX_CARDS
        cards.MAX_CARDS = 3
        try:
            ids = [
                cards.create_card({"generated_text": f"t{i}", "input_text": "x"})
                for i in range(5)
            ]
            store = cards._load()
            assert len(store) == 3
            assert ids[0] not in store and ids[-1] in store
        finally:
            cards.MAX_CARDS = limit
