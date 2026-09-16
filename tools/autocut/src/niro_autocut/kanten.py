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


# --- Befund-Regeln: Bild -----------------------------------------------------------

def laeufe(maske) -> list[tuple[int, int]]:
    """Zusammenhängende True-Bereiche als (erstes Frame, letztes Frame + 1)."""
    m = np.asarray(maske, dtype=bool).astype(np.int8)
    if m.size == 0:
        return []
    d = np.diff(np.concatenate(([0], m, [0])))
    return [(int(a), int(b)) for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1))]


def _schwarz(mittel, streuung, cfg: dict) -> np.ndarray:
    return (np.asarray(mittel) < cfg["schwarz_mittel_max"]) & (np.asarray(streuung) < cfg["schwarz_streuung_max"])


def schwarz_befunde(mittel, streuung, cfg: dict) -> list[dict]:
    """Schwarzbild: dunkle Frames ohne Struktur als zusammenhängende Läufe (Spec 3)."""
    mittel = np.asarray(mittel, dtype=float)
    return [{"art": "Schwarzbild", "frame": a, "frames": b - a, "wert": round(float(mittel[a:b].mean()), 1)}
            for a, b in laeufe(_schwarz(mittel, streuung, cfg))]


def schnipsel_befunde(diff, mittel, streuung, cfg: dict) -> list[dict]:
    """Schnipsel: zwei harte Bildwechsel höchstens ``schnipsel_max_frames`` auseinander. Direkt aufeinanderfolgende
    Schnipsel verschmelzen; komplett schwarze Schnipsel zählen nur als Schwarzbild."""
    d = np.asarray(diff, dtype=float)
    harte = np.flatnonzero(d >= cfg["wechsel_diff_min"])
    schwarz = _schwarz(mittel, streuung, cfg)
    out: list[dict] = []
    for f1, f2 in zip(harte[:-1], harte[1:]):
        f1, f2 = int(f1), int(f2)
        if f2 - f1 > cfg["schnipsel_max_frames"] or bool(schwarz[f1:f2].all()):
            continue
        wert = round(float(min(d[f1], d[f2])), 1)
        if out and out[-1]["frame"] + out[-1]["frames"] == f1:
            out[-1]["frames"] = f2 - out[-1]["frame"]
            out[-1]["wert"] = min(out[-1]["wert"], wert)
        else:
            out.append({"art": "Schnipsel", "frame": f1, "frames": f2 - f1, "wert": wert})
    return out


# --- Befund-Regeln: Ton ------------------------------------------------------------

def knack_messung(audio, sr: int, sample: int, cfg: dict) -> dict:
    """Spitze der zweiten Differenz ±``knack_kante_ms`` um das Schnitt-Sample gegen das 99. Perzentil der Umgebung
    (±``knack_fenster_ms`` ohne die Kante), je Kanal; zurück kommt der auffälligste Kanal (0-basiert)."""
    x = np.asarray(audio)
    if x.ndim == 1:
        x = x[:, None]
    kante = max(1, int(round(cfg["knack_kante_ms"] * sr / 1000)))
    fenster = int(round(cfg["knack_fenster_ms"] * sr / 1000))
    a, b = max(0, sample - fenster), min(len(x), sample + fenster)
    leer = {"spitze": 0.0, "umgebung": 0.0, "verhaeltnis": 0.0, "versatz_ms": 0.0, "kanal": 0}
    if b - a < 3:
        return leer
    seg = x[a:b].astype(np.float64)
    d2 = np.abs(seg[2:] - 2.0 * seg[1:-1] + seg[:-2])
    idx = np.arange(len(d2)) + a + 1
    nah = np.abs(idx - sample) <= kante
    if not nah.any() or nah.all():
        return leer
    spitze = d2[nah].max(axis=0)
    umgebung = np.percentile(d2[~nah], 99, axis=0)
    verh = spitze / np.maximum(umgebung, 1e-6)
    treffer = (spitze >= cfg["knack_min"]) & (verh >= cfg["knack_faktor"])
    k = int(np.argmax(np.where(treffer, verh, -1.0))) if treffer.any() else int(np.argmax(verh))
    pos = int(idx[nah][int(np.argmax(d2[nah][:, k]))])
    return {"spitze": float(spitze[k]), "umgebung": float(umgebung[k]), "verhaeltnis": float(verh[k]),
            "versatz_ms": round((pos - sample) * 1000 / sr, 1), "kanal": k}


def knack_befunde(audio, sr: int, fps: float, ton_schnitte: list[int], cfg: dict) -> tuple[list[dict], list[float]]:
    """Knackser je Ton-Schnitt (Spec 3). Rückgabe: Befunde und alle Verhältnisse (für die Kalibrierung)."""
    befunde, verhaeltnisse = [], []
    for f in ton_schnitte:
        m = knack_messung(audio, sr, int(round(f * sr / fps)), cfg)
        verhaeltnisse.append(round(m["verhaeltnis"], 2))
        if m["spitze"] >= cfg["knack_min"] and m["verhaeltnis"] >= cfg["knack_faktor"]:
            befunde.append({"art": "Knackser", "frame": int(f), "frames": 1, "wert": round(m["verhaeltnis"], 1),
                            "spitze": round(m["spitze"], 4), "versatz_ms": m["versatz_ms"], "kanal": m["kanal"] + 1})
    return befunde, verhaeltnisse


def rms_dbfs_je_frame(audio, sr: int, fps: float, n_frames: int) -> np.ndarray:
    """RMS in dBFS je Frame-Fenster (``sr/fps`` Samples) über alle Kanäle; digitale Stille = −200."""
    x = np.asarray(audio)
    if x.ndim == 1:
        x = x[:, None]
    out = np.full(int(n_frames), -200.0)
    spf = sr / fps
    for i in range(int(n_frames)):
        seg = x[int(round(i * spf)):int(round((i + 1) * spf))]
        if seg.size:
            r = float(np.sqrt(np.mean(np.square(seg, dtype=np.float64))))
            if r > 0:
                out[i] = max(-200.0, 20.0 * np.log10(r))
    return out


def tonloch_befunde(rms_db, maske, cfg: dict) -> list[dict]:
    """Tonloch: digitale Stille (RMS < ``tonloch_dbfs``) ab ``tonloch_min_frames``, wo ein aktiver Tonclip liegt."""
    rms_db = np.asarray(rms_db, dtype=float)
    m = np.asarray(maske, dtype=bool)
    n = min(rms_db.size, m.size)
    still = (rms_db[:n] < cfg["tonloch_dbfs"]) & m[:n]
    return [{"art": "Tonloch", "frame": a, "frames": b - a, "wert": round(float(rms_db[a:b].max()), 1)}
            for a, b in laeufe(still) if b - a >= cfg["tonloch_min_frames"]]
