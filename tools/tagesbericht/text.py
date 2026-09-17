"""Gemeinsame Textkürzung für Tagesstand und Bericht."""
from __future__ import annotations


def kuerzen(text: str, laenge: int) -> str:
    """Whitespace auf einzelne Leerzeichen normalisieren, bei Überlänge mit „…“ abschneiden."""
    text = " ".join(text.split())
    if len(text) <= laenge:
        return text
    return text[: laenge - 1].rstrip() + "…"


def erste_zeile(texte: list[str]) -> str:
    """Erste nicht leere Zeile aus einer Liste von Texten."""
    for text in texte:
        for zeile in text.splitlines():
            if zeile.strip():
                return zeile.strip()
    return ""
