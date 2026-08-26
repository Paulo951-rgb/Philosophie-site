"""Le Grand Philosophe — serveur applicatif (FastAPI).

Sert la SPA (routes : /, /histoire, /favoris, /a-propos, /parametres),
l'API de génération/transformation, ainsi que les pages publiques de
cartes (/carte/<id>) avec métadonnées Open Graph dynamiques.
"""

from __future__ import annotations

import html
import io
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import cards
from .generation import lexicon, generate, transform
from .generation.engine import COMPLEXITY, DEPTH, EXAGGERATION, LENGTH_WORDS, MODES
from .generation.styles import STYLES
from .generation.transforms import TRANSFORM_ACTIONS
from .schemas import (
    CardCreateRequest,
    GenerateRequest,
    MetaResponse,
    TransformRequest,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "app" / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app = FastAPI(title="Le Grand Philosophe", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ------------------------------------------------------------ page shell


_shell_cache: str | None = None


def _shell() -> str:
    """Lit index.html une seule fois (les requêtes shell sont fréquentes)."""
    global _shell_cache
    if _shell_cache is None:
        _shell_cache = INDEX_FILE.read_text(encoding="utf-8")
    return _shell_cache


@app.get("/", response_class=HTMLResponse)
@app.get("/histoire", response_class=HTMLResponse)
@app.get("/favoris", response_class=HTMLResponse)
@app.get("/a-propos", response_class=HTMLResponse)
@app.get("/parametres", response_class=HTMLResponse)
def page_shell():
    return HTMLResponse(_shell())


# Toute exception non gérée (moteur pyprocedural, cartes, etc.) doit rendre
# un JSON propre plutôt que la page 500 brute de Starlette.
@app.exception_handler(Exception)
def unexpected(req, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "erreur interne — le moteur s'en arrête ici"},
    )


# ----------------------------------------------------------------- API


@app.get("/api/meta", response_model=MetaResponse)
def api_meta():
    return {
        "styles": STYLES,
        "depths": list(DEPTH),
        "exaggerations": list(EXAGGERATION),
        "lengths": LENGTH_WORDS,
        "complexities": COMPLEXITY,
        "modes": MODES,
        "defaults": {
            "depth": "profond",
            "exaggeration": "subtile",
            "styles": ["francais"],
            "length": "moyen",
            "complexity": "soutenu",
            "mode": "standard",
        },
        "loading_phrases": lexicon.AMBIENT_LOADING,
        "transform_actions": {k: v["label"] for k, v in TRANSFORM_ACTIONS.items()},
    }


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    req = req.validated()
    result = generate(
        input_text=req.input_text,
        depth=req.depth,
        exaggeration=req.exaggeration,
        styles=req.styles,
        length=req.length,
        complexity=req.complexity,
        mode=req.mode,
    )
    return {
        "text": result["text"],
        "attribution": result.get("attribution"),
        "mode": req.mode,
        "params": {
            "depth": req.depth,
            "exaggeration": req.exaggeration,
            "styles": req.styles,
            "length": req.length,
            "complexity": req.complexity,
        },
        "word_count": result["word_count"],
    }


@app.post("/api/transform")
def api_transform(req: TransformRequest):
    try:
        result = transform(
            action=req.action,
            previous_text=req.previous_text,
            original_input=req.original_input,
            styles=req.styles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


# ---------------------------------------------------------------- cartes


_CARD_PAGE = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Carte partagée — Le Grand Philosophe</title>
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:type" content="article">
<meta property="og:image" content="/carte/{card_id}.png?format=landscape">
<meta name="twitter:card" content="summary_large_image">
<style>
body{{margin:0;background:#171310;color:#f0e6d0;display:flex;justify-content:center;
     min-height:100vh;font-family:Georgia,'Times New Roman',serif}}
main{{max-width:720px;padding:56px 20px;text-align:center}}
img.card{{max-width:92%;border:1px solid #b08d3e;box-shadow:0 20px 60px rgba(0,0,0,.5)}}
a.cta{{display:inline-block;margin:28px 0 12px;padding:14px 30px;border:1px solid #b08d3e;
color:#b08d3e;text-decoration:none;letter-spacing:.12em;font-size:13px;text-transform:uppercase}}
a.cta:hover{{background:#b08d3e;color:#171310}}
p.note{{color:#8d7c60;font-size:13px}}
</style></head><body><main>
<img class="card" src="/carte/{card_id}.png?format=story" alt="La Grande Réflexion">
<p class="note">Une réflexion philosophique générée par une machine feutrée.</p>
<a class="cta" href="/">Créer votre propre réflexion</a>
</main></body></html>"""


# Identifiants de carte attendus : token_hex(5) -> chiffrement hex strict.
_CARD_ID = re.compile(r"^[0-9a-f]{10}$")


def _validated_card(card_id: str) -> dict:
    """404 autant sur un id mal formé que sur un id inconnu."""
    if not _CARD_ID.match(card_id):
        raise HTTPException(status_code=404, detail="carte introuvable")
    card = cards.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="carte introuvable")
    return card


@app.get("/carte/{card_id}.png")
def carte_png(card_id: str, format: str = "landscape"):
    card = _validated_card(card_id)
    img = cards.render_card(card, format)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/carte/{card_id}", response_class=HTMLResponse)
def carte_page(card_id: str):
    card = _validated_card(card_id)
    generated = card.get("generated_text") or ""
    desc = re.sub(r"\s+", " ", generated).strip()
    og_desc = html.escape(desc[:180] + ("…" if len(desc) > 180 else ""))
    if card.get("attribution"):
        og_desc += " " + html.escape(card["attribution"])
    return HTMLResponse(
        _CARD_PAGE.format(
            card_id=card_id,
            og_title="La Grande Réflexion",
            og_desc=og_desc,
        )
    )


@app.post("/api/cards")
def api_create_card(req: CardCreateRequest):
    cid = cards.create_card(req.model_dump())
    return {"id": cid, "path": f"/carte/{cid}"}


@app.get("/api/cards/{card_id}")
def api_get_card(card_id: str):
    card = cards.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="carte introuvable")
    return card
