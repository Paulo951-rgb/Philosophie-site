"""Magasin de cartes publiques + rendu PNG serveur (Pillow).

Chaque carte partagée possède une URL unique ``/carte/<id>`` servie avec
des métadonnées Open Graph dynamiques ; l'image OG elle-même provient du
rendu serveur ``/carte/<id>.png``.

Le magasin est volontairement simple : un fichier JSON local. Une base
SQL serait le pas naturel si le produit passait freemium (§12).
"""

from __future__ import annotations

import json
import os
import secrets
import threading

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA_DIR = Path(os.environ.get("GRAND_DATA_DIR", "data"))
CARDS_FILE = DATA_DIR / "cards.json"

FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CARD_SIZES = {
    "story": (1080, 1920),
    "square": (1080, 1080),
    "landscape": (1200, 630),
}
MAX_CHARS = {"story": 1400, "square": 900, "landscape": 420}

# Palette(s) templating
PALETTE = {
    "ink": (20, 17, 12),
    "gold": (176, 141, 62),
    "gold_soft": (200, 166, 99),
    "ivory": (241, 232, 214),
    "muted": (146, 131, 104),
}

_lock = threading.Lock()

# Le fichier JSON ne doit pas grossir sans borne : on écarte les plus
# anciennes entrées au-delà d'un plafond (FIFO).
MAX_CARDS = 5000


def _load() -> dict:
    if CARDS_FILE.exists():
        try:
            return json.loads(CARDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(store: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CARDS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CARDS_FILE)


def _evict_oldest(store: dict) -> None:
    while len(store) > MAX_CARDS:
        # dict ordonné => la première clé est la plus ancienne créée
        del store[next(iter(store))]



def create_card(payload: dict) -> str:
    with _lock:
        store = _load()
        for _ in range(8):
            cid = secrets.token_hex(5)
            if cid not in store:
                store[cid] = payload
                _evict_oldest(store)
                _save(store)
                return cid
    raise RuntimeError("impossible d'allouer un identifiant de carte")


def get_card(card_id: str) -> dict | None:
    with _lock:
        return _load().get(card_id)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _spaced(draw: ImageDraw.ImageDraw, x: float, y: float, text: str,
            font: ImageFont.FreeTypeFont, fill, tracking: int = 6) -> float:
    """Dessine un texte avec approches (letter-spacing) centrées."""
    total = sum(draw.textlength(ch, font=font) + tracking for ch in text) - tracking
    cx = x - total / 2
    for ch in text:
        w = draw.textlength(ch, font=font)
        draw.text((cx, y), ch, font=font, fill=fill)
        cx += w + tracking
    return total


def _wrap(draw: ImageDraw.ImageDraw, text: str,
          font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _ornament_row(draw: ImageDraw.ImageDraw, cx: float, y: float, width: float,
                  color) -> None:
    """Ligne fine avec un losange au centre — le sceau du produit."""
    half = width / 2
    draw.line([(cx - half, y), (cx - 16, y)], fill=color, width=1)
    draw.line([(cx + 16, y), (cx + half, y)], fill=color, width=1)
    d = 7
    draw.polygon([(cx, y - d), (cx + d, y), (cx, y + d), (cx - d, y)],
                 outline=color, width=1)


def render_card(card: dict, size_key: str = "landscape") -> Image.Image:
    """Rend le visuel de la carte : encre, or, capitale, filigrane."""
    if size_key not in CARD_SIZES:
        size_key = "landscape"
    W, H = CARD_SIZES[size_key]
    img = Image.new("RGB", (W, H), PALETTE["ink"])
    draw = ImageDraw.Draw(img)

    # Vignette douce (façon lampe sur papier)
    small = Image.radial_gradient("L").resize((W, H)).filter(ImageFilter.GaussianBlur(26))
    glow = Image.new("RGB", (W, H), (36, 29, 19))
    img.paste(glow, mask=small.point(lambda v: int(v * 0.30)))
    draw = ImageDraw.Draw(img)

    margin = 45 if W > 700 else 34
    # double cadre doré
    draw.rectangle([margin, margin, W - margin, H - margin], outline=PALETTE["gold"], width=3)
    draw.rectangle([margin + 12, margin + 12, W - margin - 12, H - margin - 12],
                   outline=PALETTE["gold"], width=1)

    inner_w = W - 2 * margin - 60
    y = margin + 40

    # en-tête : nom du produit, lettres espacées
    head_size = max(20, int(26 * W / 1200))
    _spaced(draw, W / 2, y, "LE GRAND PHILOSOPHE",
            _font(FONT_SERIF_BOLD, head_size), PALETTE["gold"])
    y += head_size + 26
    _ornament_row(draw, W / 2, y, inner_w * 0.6, PALETTE["gold"])
    y += 40

    # Corps : troncation élégante si la réflexion dépasse le format
    text = card.get("generated_text", "")
    limit = MAX_CHARS[size_key]
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = cut.rstrip(".;") + "…"

    # Capitale ornée en début de réflexion
    body_size = int(34 * W / 1200) if size_key != "landscape" else 30
    cap_size = int(body_size * 2.6)
    body_font = _font(FONT_SERIF, body_size)
    cap_font = _font(FONT_SERIF_BOLD, cap_size)

    first = text[0]
    rest = text[1:]
    cap_w = draw.textlength(first, font=cap_font) + 14
    lines = _wrap(draw, rest, body_font, inner_w - cap_w)
    draw.text((margin + 30, y + cap_size // 6), first, font=cap_font,
              fill=PALETTE["gold_soft"])
    line_h = int(body_size * 1.55)
    tx = margin + 30 + cap_w
    avail = H - y - margin - (150 if card.get("attribution") else 90)
    max_lines = max(1, int(avail / line_h))
    for line in lines[:max_lines]:
        draw.text((tx, y), line, font=body_font, fill=PALETTE["ivory"])
        y += line_h

    # Attribution fictive (mode citation)
    if card.get("attribution"):
        y = H - margin - 150
        attr_font = _font(FONT_SERIF, int(body_size * 0.85))
        attr = card["attribution"]
        for line in _wrap(draw, attr, attr_font, inner_w)[:2]:
            w_ = draw.textlength(line, font=attr_font)
            draw.text((W - margin - 30 - w_, y), line,
                      font=attr_font, fill=PALETTE["muted"])
            y += int(body_size)
        # Badge : sécurité anti-confusion (§9.2)
        badge = "citation humoristique · attribution fictive"
        b_font = _font(FONT_SANS, int(body_size * 0.55))
        bw = draw.textlength(badge, font=b_font) + 28
        bx = W / 2 - bw / 2
        by = H - margin - 96
        draw.rounded_rectangle([bx, by, bx + bw, by + 30], radius=15,
                               outline=PALETTE["gold"], width=1)
        draw.text((bx + 14, by + 6), badge, font=b_font, fill=PALETTE["gold"])

    # pied de carte : sceau + URL du produit
    fy = H - margin - 42
    if not card.get("attribution"):
        _ornament_row(draw, W / 2, fy, inner_w * 0.5, PALETTE["gold"])
    foot_font = _font(FONT_SANS, max(13, int(15 * W / 1200)))
    _spaced(draw, W / 2, fy + 12, "LEGRANDPHILOSOPHE", foot_font, PALETTE["muted"], 4)

    return img
