"""Quelle Sitzungen (Spec 2.3): Claude-Code-Verläufe (JSONL) eines Tages — Titel, Zeitraum, Aufträge, Schlussbericht,
Tool-Fehler, editierte Dateien, Werkzeuge, Chargen-Bezug. Subagenten-Verläufe und Sidechains bleiben draußen."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from text import erste_zeile, kuerzen
from umgebung import tagesgrenzen

AUFTRAG_MAX = 200
AUFTRAEGE_MAX = 12
SCHLUSS_MAX = 1500
FEHLER_MAX = 5
FEHLER_ZEILE_MAX = 160
DATEIEN_MAX = 20
WERKZEUGE_MAX = 5
TITEL_MAX = 80
CHARGE_MUSTER = re.compile(r"^\d{4}-\d{2}\b")
EDIT_WERKZEUGE = ("Edit", "Write", "NotebookEdit")
KEIN_AUFTRAG = ("<system-reminder>", "<task-notification>", "<command-name>", "<local-command", "[Request interrupted")
EXIT_MUSTER = re.compile(r"^Exit code \d+$")


@dataclass
class Sitzung:
    kennung: str
    titel: str = ""
    ordner: str = ""
    branch: str = ""
    von: str = ""
    bis: str = ""
    auftraege: list[str] = field(default_factory=list)
    weitere_auftraege: int = 0
    schluss: str = ""
    schluss_offen: bool = False
    fehler_anzahl: int = 0
    fehler: list[str] = field(default_factory=list)
    dateien: list[str] = field(default_factory=list)
    weitere_dateien: int = 0
    werkzeuge: list[tuple[str, int]] = field(default_factory=list)
    chargen: list[str] = field(default_factory=list)
    beginn: datetime | None = None


@dataclass
class SitzungenStand:
    sitzungen: list[Sitzung] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def relativ(pfad: str, repo: Path) -> str:
    """Pfad relativ zum Repo (realpath-Vergleich, macOS /var → /private/var); außerhalb unverändert."""
    wurzel = os.path.realpath(str(repo))
    p = os.path.realpath(pfad) if pfad.startswith("/") else pfad
    if p == wurzel:
        return "."
    if p.startswith(wurzel + "/"):
        return p[len(wurzel) + 1:]
    return pfad


def charge_aus_pfad(rel: str) -> str | None:
    """projects/<Kunde>/[<Projekt>/]<JJJJ-MM Charge>/… → Chargen-Pfad, sonst None."""
    teile = rel.split("/")
    if len(teile) < 3 or teile[0] != "projects":
        return None
    for i in range(2, min(len(teile), 4)):
        if CHARGE_MUSTER.match(teile[i]):
            return "/".join(teile[: i + 1])
    return None


def _text_bloecke(inhalt) -> list[str]:
    if isinstance(inhalt, str):
        return [inhalt]
    if isinstance(inhalt, list):
        return [b.get("text", "") for b in inhalt if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
    return []


def _fehlerzeile(texte: list[str]) -> str:
    """Erste aussagekräftige Zeile eines Tool-Fehlers: „Exit code N“ allein sagt nichts, dann die nächste Zeile."""
    zeilen = [z.strip() for t in texte for z in t.splitlines() if z.strip()]
    for zeile in zeilen:
        if not EXIT_MUSTER.match(zeile):
            return zeile
    return erste_zeile(texte)


def _zeitpunkt(ts) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def sitzung_lesen(datei: Path, tag: date, repo: Path) -> Sitzung | None:
    """Ein Verlauf; None, wenn er am Tag keine user-/assistant-Datensätze hat."""
    anfang, ende = tagesgrenzen(tag)
    s = Sitzung(kennung=datei.stem[:8])
    titel_custom = titel_summary = ""
    alle_auftraege: list[str] = []
    werkzeuge: Counter = Counter()
    dateien: list[str] = []
    beginn = letzte = None
    letzter_typ = ""
    with open(datei, encoding="utf-8", errors="replace") as fh:
        for zeile in fh:
            try:
                d = json.loads(zeile)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            typ = d.get("type")
            if typ == "custom-title":
                titel_custom = d.get("customTitle") or titel_custom
                continue
            if typ == "summary":
                titel_summary = d.get("summary") or titel_summary
                continue
            if typ not in ("user", "assistant") or d.get("isSidechain"):
                continue
            zeit = _zeitpunkt(d.get("timestamp"))
            if zeit is None or not (anfang <= zeit < ende):
                continue
            beginn = beginn or zeit
            letzte = zeit
            letzter_typ = typ
            s.branch = d.get("gitBranch") or s.branch
            if isinstance(d.get("cwd"), str) and d["cwd"]:
                s.ordner = relativ(d["cwd"], repo)
            nachricht = d.get("message") if isinstance(d.get("message"), dict) else {}
            inhalt = nachricht.get("content")
            if typ == "user":
                if isinstance(inhalt, list):
                    for b in inhalt:
                        if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                            s.fehler_anzahl += 1
                            if len(s.fehler) < FEHLER_MAX:
                                s.fehler.append(kuerzen(_fehlerzeile(_text_bloecke(b.get("content"))), FEHLER_ZEILE_MAX))
                if d.get("isMeta"):
                    continue
                for text in _text_bloecke(inhalt):
                    text = text.strip()
                    if not text or text.startswith(KEIN_AUFTRAG):
                        continue
                    alle_auftraege.append(text)
            else:
                for b in inhalt if isinstance(inhalt, list) else []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and isinstance(b.get("text"), str) and b["text"].strip():
                        s.schluss = kuerzen(b["text"], SCHLUSS_MAX)
                    elif b.get("type") == "tool_use":
                        name = b.get("name") or "?"
                        werkzeuge[name] += 1
                        eingabe = b.get("input") if isinstance(b.get("input"), dict) else {}
                        pfad = eingabe.get("file_path") if name in EDIT_WERKZEUGE else None
                        if isinstance(pfad, str) and pfad:
                            rel = relativ(pfad, repo)
                            if rel not in dateien:
                                dateien.append(rel)
    if beginn is None or letzte is None:
        return None
    s.beginn = beginn
    s.von, s.bis = beginn.strftime("%H:%M"), letzte.strftime("%H:%M")
    s.auftraege = [kuerzen(a, AUFTRAG_MAX) for a in alle_auftraege[:AUFTRAEGE_MAX]]
    s.weitere_auftraege = max(0, len(alle_auftraege) - AUFTRAEGE_MAX)
    s.schluss_offen = letzter_typ == "user" or not s.schluss
    s.dateien = dateien[:DATEIEN_MAX]
    s.weitere_dateien = max(0, len(dateien) - DATEIEN_MAX)
    s.werkzeuge = werkzeuge.most_common(WERKZEUGE_MAX)
    s.chargen = sorted({c for c in (charge_aus_pfad(p) for p in dateien) if c})
    s.titel = titel_custom or titel_summary or (kuerzen(alle_auftraege[0], TITEL_MAX) if alle_auftraege else "(ohne Titel)")
    return s


def sitzungen_stand(ordner: list[Path], tag: date, repo: Path) -> SitzungenStand:
    """Alle *.jsonl direkt in den Sitzungsordnern (keine Unterordner); Dateien, die seit Tagesbeginn unverändert
    sind, werden nicht geöffnet."""
    stand = SitzungenStand()
    anfang, _ = tagesgrenzen(tag)
    for o in ordner:
        try:
            dateien = sorted(p for p in o.iterdir() if p.is_file() and p.suffix == ".jsonl")
        except OSError as e:
            stand.fehler.append(f"Sitzungsordner {o}: {e}")
            continue
        for datei in dateien:
            try:
                if datei.stat().st_mtime < anfang.timestamp():
                    continue
                s = sitzung_lesen(datei, tag, repo)
            except OSError as e:
                stand.fehler.append(f"{datei.name}: {e}")
                continue
            if s is not None:
                stand.sitzungen.append(s)
    stand.sitzungen.sort(key=lambda s: s.beginn)
    return stand
