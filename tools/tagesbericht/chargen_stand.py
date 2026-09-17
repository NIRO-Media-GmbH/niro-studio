"""Quelle Chargen (Spec 2.2): Protokoll-Einträge des Tages je Charge (Sammelzeile ab fünf gleichen Überschriften)
und neue Dateien unter Ergebnisse/."""
from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from text import kuerzen
from umgebung import tagesgrenzen

SAMMEL_AB = 5
UEBERSCHRIFT_MAX = 120
BEISPIELE_MAX = 5


@dataclass
class Lieferung:
    charge: str
    anzahl: int
    beispiele: list[str]


@dataclass
class ChargenStand:
    je_charge_alle: dict[str, list[str]] = field(default_factory=dict)
    je_charge: dict[str, list[str]] = field(default_factory=dict)
    sammel: list[tuple[str, int]] = field(default_factory=list)
    lieferungen: list[Lieferung] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def chargen_ordner(repo: Path, fehler: list[str] | None = None) -> list[Path]:
    """Ordner in Tiefe 2 und 3 unter projects/ mit Protokoll.md oder Ergebnisse/. Unlesbare Ordner werden
    übersprungen und in `fehler` vermerkt."""
    projects = repo / "projects"
    try:
        if not projects.is_dir():
            return []
    except OSError as e:
        if fehler is not None:
            fehler.append(f"projects/: {e}")
        return []
    gefunden = set()
    for muster in ("*/*", "*/*/*"):
        try:
            kandidaten = list(projects.glob(muster))
        except OSError as e:
            if fehler is not None:
                fehler.append(f"projects/{muster}: {e}")
            continue
        for p in kandidaten:
            try:
                if p.is_dir() and ((p / "Protokoll.md").is_file() or (p / "Ergebnisse").is_dir()):
                    gefunden.add(p)
            except OSError as e:
                if fehler is not None:
                    fehler.append(f"{p.relative_to(repo).as_posix()}: {e}")
    return sorted(gefunden)


def eintraege_des_tages(protokoll: Path, tag: date) -> list[str]:
    """Überschriften `## …`, die das Datum als JJJJ-MM-TT oder TT.MM.JJJJ enthalten, ohne `## `, gekürzt."""
    iso, deutsch = tag.isoformat(), tag.strftime("%d.%m.%Y")
    ergebnis = []
    with open(protokoll, encoding="utf-8", errors="replace") as fh:
        for zeile in fh:
            if zeile.startswith("## ") and (iso in zeile or deutsch in zeile):
                ergebnis.append(kuerzen(zeile[3:], UEBERSCHRIFT_MAX))
    return ergebnis


def chargen_stand(repo: Path, tag: date) -> ChargenStand:
    stand = ChargenStand()
    anfang, ende = tagesgrenzen(tag)
    von, bis = anfang.timestamp(), ende.timestamp()
    for ordner in chargen_ordner(repo, stand.fehler):
        charge = ordner.relative_to(repo).as_posix()
        protokoll = ordner / "Protokoll.md"
        ergebnisse = ordner / "Ergebnisse"
        try:
            hat_protokoll = protokoll.is_file()
            hat_ergebnisse = ergebnisse.is_dir()
        except OSError as e:
            stand.fehler.append(f"{charge}: {e}")
            continue
        if hat_protokoll:
            try:
                eintraege = eintraege_des_tages(protokoll, tag)
            except OSError as e:
                stand.fehler.append(f"{charge}/Protokoll.md: {e}")
                eintraege = []
            if eintraege:
                stand.je_charge_alle[charge] = eintraege
        if hat_ergebnisse:
            treffer = []
            for wurzel, _ordner, dateien in os.walk(ergebnisse):
                for name in dateien:
                    if name == ".DS_Store":
                        continue
                    pfad = Path(wurzel) / name
                    try:
                        mtime = pfad.stat().st_mtime
                    except OSError:
                        continue
                    if von <= mtime < bis:
                        treffer.append(pfad.relative_to(ergebnisse).as_posix())
            if treffer:
                treffer.sort()
                stand.lieferungen.append(Lieferung(charge=charge, anzahl=len(treffer), beispiele=treffer[:BEISPIELE_MAX]))
    zaehler = Counter(u for eintraege in stand.je_charge_alle.values() for u in set(eintraege))
    stand.sammel = sorted(((u, n) for u, n in zaehler.items() if n >= SAMMEL_AB), key=lambda x: (-x[1], x[0]))
    zusammengefasst = {u for u, _ in stand.sammel}
    for charge, eintraege in stand.je_charge_alle.items():
        rest = [u for u in eintraege if u not in zusammengefasst]
        if rest:
            stand.je_charge[charge] = rest
    return stand
