"""Quelle Gedächtnis (Spec 2.4): am Tag geänderte Notizen mit ihrer Beschreibungszeile."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from text import kuerzen
from umgebung import tagesgrenzen

BESCHREIBUNG_MAX = 160


@dataclass
class Notiz:
    name: str
    beschreibung: str


def frontmatter(datei: Path) -> tuple[str, str]:
    """name und description aus dem YAML-Kopf (nur einzeilige Werte, Anführungszeichen entfernt)."""
    name = beschreibung = ""
    with open(datei, encoding="utf-8", errors="replace") as fh:
        if fh.readline().strip() != "---":
            return "", ""
        for zeile in fh:
            if zeile.strip() == "---":
                break
            if zeile.startswith("name:"):
                name = zeile[len("name:"):].strip().strip('"')
            elif zeile.startswith("description:"):
                beschreibung = zeile[len("description:"):].strip().strip('"').replace('\\"', '"')
    return name, beschreibung


def gedaechtnis_stand(ordner: Path, tag: date) -> tuple[list[Notiz], list[str]]:
    anfang, ende = tagesgrenzen(tag)
    von, bis = anfang.timestamp(), ende.timestamp()
    try:
        dateien = sorted(p for p in ordner.iterdir() if p.suffix == ".md" and p.name != "MEMORY.md")
    except OSError as e:
        return [], [f"Gedächtnis {ordner}: {e}"]
    notizen, fehler = [], []
    for datei in dateien:
        try:
            if not (von <= datei.stat().st_mtime < bis):
                continue
            name, beschreibung = frontmatter(datei)
        except OSError as e:
            fehler.append(f"{datei.name}: {e}")
            continue
        notizen.append(Notiz(name=name or datei.stem, beschreibung=kuerzen(beschreibung, BESCHREIBUNG_MAX)))
    return notizen, fehler
