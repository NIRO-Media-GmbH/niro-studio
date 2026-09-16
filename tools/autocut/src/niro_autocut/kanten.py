"""Kantenprüfung: Schnitte einer AutoCut-Timeline am fertigen Export messen (Spec 2026-09-16).

Reine Logik ohne ffmpeg und ohne Resolve-Verbindung: Schnappschuss aus dem Timeline-Readback, Schnitt-Listen,
Ton-Maske, Timecodes, Befund-Regeln (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) und Kontext.
Medien lesen: ``kanten_medien.py`` · Bericht: ``kanten_bericht.py`` · Bild: ``schnittbild.py``.
"""
from __future__ import annotations

import datetime as _dt
import unicodedata
from pathlib import Path

import numpy as np

from .charge import AutoCutError

ARTEN = ("Schwarzbild", "Schnipsel", "Knackser", "Tonloch", "Wort angeschnitten")
DATEINAME_ART = {"Schwarzbild": "schwarzbild", "Schnipsel": "schnipsel", "Knackser": "knackser",
                 "Tonloch": "tonloch", "Wort angeschnitten": "wort"}


def _fps_wert(v) -> float:
    """„25", „23.976", 25.0 → float; „29.97 DF" → 29.97; nicht lesbar → 0.0."""
    try:
        return float(str(v).strip().split()[0])
    except (ValueError, IndexError):
        return 0.0


# --- Schnappschuss ---------------------------------------------------------------

def snapshot_from_readback(tl: dict, projekt: str, quelle: str = "resolve", gelesen_am: str | None = None) -> dict:
    """``ResolveSession.read_timeline``-Dict → Schnappschuss mit Frames relativ zum Timeline-Start (Spec 1)."""
    start = int(tl.get("start_frame") or 0)
    if tl.get("end_frame") is None:
        raise AutoCutError(f"Timeline '{tl.get('name')}' liefert kein Ende (GetEndFrame) — Readback unvollständig.")
    fps = _fps_wert(tl.get("fps"))
    if fps <= 0:
        raise AutoCutError(f"Timeline '{tl.get('name')}' ohne lesbare Bildrate (timelineFrameRate={tl.get('fps')!r}).")
    spuren: dict[str, list[dict]] = {}
    for key, track in (tl.get("tracks") or {}).items():
        rows = []
        for it in track.get("items") or []:
            if it.get("start") is None or it.get("duration") is None:
                continue
            q = it.get("left_offset")
            rows.append({"name": it.get("name"), "datei": it.get("file"), "start": int(it["start"]) - start,
                         "dauer": int(it["duration"]), "quell_in": None if q is None else int(q),
                         "aktiv": it.get("enabled") is not False,
                         "tempo": None if it.get("speed") is None else float(it["speed"])})
        spuren[key] = sorted(rows, key=lambda r: r["start"])
    return {"quelle": quelle, "gelesen_am": gelesen_am or _dt.datetime.now().isoformat(timespec="seconds"),
            "projekt": projekt, "timeline": tl.get("name"), "fps": fps, "start_frame": start,
            "start_timecode": tl.get("start_timecode") or "01:00:00:00", "laenge": int(tl["end_frame"]) - start,
            "spuren": spuren}


def schnitte(snap: dict, art: str) -> list[int]:
    """Start- und End-Frames aktiver Items auf V-Spuren (``art="bild"``) bzw. A-Spuren (``"ton"``), ohne 0 und Ende."""
    prefix = {"bild": "V", "ton": "A"}[art]
    n = int(snap["laenge"])
    out: set[int] = set()
    for key, rows in snap["spuren"].items():
        if not key.startswith(prefix):
            continue
        for r in rows:
            if r["aktiv"]:
                out.update(f for f in (r["start"], r["start"] + r["dauer"]) if 0 < f < n)
    return sorted(out)


def ton_maske(snap: dict) -> np.ndarray:
    """Bool je Frame: liegt dort ein aktives A-Item? Erstes und letztes Frame jedes Items zählen nicht (Blenden)."""
    n = int(snap["laenge"])
    m = np.zeros(n, dtype=bool)
    for key, rows in snap["spuren"].items():
        if not key.startswith("A"):
            continue
        for r in rows:
            a, b = max(0, r["start"] + 1), min(n, r["start"] + r["dauer"] - 1)
            if r["aktiv"] and b > a:
                m[a:b] = True
    return m


# --- Timecode ----------------------------------------------------------------------

def _tc_frames(tc: str, base: int) -> int:
    try:
        h, m, s, f = (int(x) for x in str(tc).replace(";", ":").split(":"))
    except ValueError as e:
        raise AutoCutError(f"Timecode nicht lesbar: {tc!r} (erwartet HH:MM:SS:FF)") from e
    return ((h * 60 + m) * 60 + s) * base + f


def timecode(frame: int, fps: float, start_tc: str = "01:00:00:00") -> str:
    """Frame ab Timeline-Start → „HH:MM:SS:FF" nach dem Start-Timecode (ohne Drop-Frame)."""
    base = max(1, int(round(fps)))
    total = _tc_frames(start_tc, base) + int(frame)
    ff, total = total % base, total // base
    ss, total = total % 60, total // 60
    return f"{total // 60:02d}:{total % 60:02d}:{ss:02d}:{ff:02d}"


def tc_to_frame(tc: str, fps: float, start_tc: str = "01:00:00:00") -> int:
    """„HH:MM:SS:FF" → Frame ab Timeline-Start."""
    base = max(1, int(round(fps)))
    return _tc_frames(tc, base) - _tc_frames(start_tc, base)


# --- Kontext -----------------------------------------------------------------------

def items_bei(snap: dict, frame: int) -> list[dict]:
    """Aktive Items, die das Frame abdecken (Spur, Clipname), Spuren in Namensreihenfolge."""
    return [{"spur": key, "name": r["name"]} for key in sorted(snap["spuren"]) for r in snap["spuren"][key]
            if r["aktiv"] and r["start"] <= frame < r["start"] + r["dauer"]]


def kontext(snap: dict, frame: int, bild: list[int], ton: list[int]) -> dict:
    """Nächster Bild- und Ton-Schnitt (Frame, Abstand zum Befund) und die Items am Frame."""
    def naechster(liste):
        if not liste:
            return None
        f = min(liste, key=lambda x: (abs(x - frame), x))
        return {"frame": int(f), "abstand": int(f - frame)}
    return {"bild_schnitt": naechster(bild), "ton_schnitt": naechster(ton), "items": items_bei(snap, frame)}
