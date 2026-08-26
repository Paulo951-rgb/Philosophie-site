"""Schémas pydantic des endpoints publics."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .generation import STYLES
from .generation.engine import COMPLEXITY, DEPTH, EXAGGERATION, LENGTH_WORDS, MODES


class GenerateRequest(BaseModel):
    input_text: str = Field(min_length=1)
    depth: str = "profond"
    exaggeration: str = "subtile"
    styles: list[str] = ["francais"]
    length: str = "moyen"
    complexity: str = "soutenu"
    mode: str = "standard"

    def validated(self) -> "GenerateRequest":
        self.depth = self.depth if self.depth in DEPTH else "profond"
        self.exaggeration = self.exaggeration if self.exaggeration in EXAGGERATION else "subtile"
        self.styles = [s for s in self.styles if s in STYLES][:2] or ["francais"]
        self.length = self.length if self.length in LENGTH_WORDS else "moyen"
        self.complexity = self.complexity if self.complexity in COMPLEXITY else "soutenu"
        self.mode = self.mode if self.mode in MODES else "standard"
        # Sécurité : borne du texte d'entrée (le frontend avertit à 2000)
        self.input_text = self.input_text[:2000]
        return self


class TransformRequest(BaseModel):
    action: str
    previous_text: str = Field(min_length=1, max_length=12000)
    original_input: str = Field(default="", max_length=2000)
    styles: list[str] = ["francais"]


class CardCreateRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=2000)
    generated_text: str = Field(min_length=1, max_length=12000)
    attribution: str | None = None
    mode: str = "standard"
    styles: list[str] = ["francais"]
    favorites_folded: bool = False  # marqueur badge citation


class MetaResponse(BaseModel):
    styles: dict
    depths: list[str]
    exaggerations: list[str]
    lengths: dict[str, int]
    complexities: list[str]
    modes: list[str]
    defaults: dict
    loading_phrases: list[str]
    transform_actions: dict[str, str]
