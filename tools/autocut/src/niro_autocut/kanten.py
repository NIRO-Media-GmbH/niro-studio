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


# --- Wortkanten --------------------------------------------------------------------

def _nfc(p) -> str:
    return unicodedata.normalize("NFC", str(p))


class Transkripte:
    """Scribe-Wörter je Clip aus dem Transkript-Index der Charge: Treffer über den Pfad (auch über ``path_map``),
    sonst über einen eindeutigen Dateinamen."""

    def __init__(self, charge):
        self.charge = charge
        try:
            index = charge.load_index()
        except AutoCutError:
            index = []
        self.nach_pfad: dict[str, dict] = {}
        namen: dict[str, list[dict]] = {}
        for e in index:
            if not e.get("fingerprint") or not e.get("path"):
                continue
            for p in (e["path"], charge.map_path(e["path"])):
                self.nach_pfad[_nfc(p)] = e
            namen.setdefault(_nfc(Path(e["path"]).name), []).append(e)
        self.nach_name = {k: v[0] for k, v in namen.items() if len(v) == 1}
        self._woerter: dict[str, list[dict]] = {}

    def eintrag(self, datei) -> dict | None:
        if not datei:
            return None
        return self.nach_pfad.get(_nfc(datei)) or self.nach_name.get(_nfc(Path(str(datei)).name))

    def woerter(self, datei) -> list[dict] | None:
        """Wörter (``text``, ``start``, ``end`` in Quellsekunden) oder None, wenn der Clip kein Transkript hat."""
        e = self.eintrag(datei)
        if e is None:
            return None
        fp = e["fingerprint"]
        if fp not in self._woerter:
            daten = self.charge.cache_transcript(fp) or {}
            self._woerter[fp] = [w for w in daten.get("words") or []
                                 if w.get("start") is not None and w.get("end") is not None]
        return self._woerter[fp]


def _ton_items(snap: dict):
    """Aktive A-Items mit Quell-In und Tempo 100 % (oder unbekannt), Spuren in Namensreihenfolge."""
    for key in sorted(k for k in snap["spuren"] if k.startswith("A")):
        for r in snap["spuren"][key]:
            if r["aktiv"] and r["quell_in"] is not None and (r["tempo"] is None or abs(r["tempo"] - 100.0) < 0.01):
                yield key, r


def wort_befunde(snap: dict, transkripte, cfg: dict) -> tuple[list[dict], dict]:
    """Wort angeschnitten: O-Ton-Kante liegt in einem Wort, von dem mindestens ``wort_min_ms`` wegfallen (Spec 3)."""
    fps = float(snap["fps"])
    grenze = cfg["wort_min_ms"] / 1000.0
    befunde: list[dict] = []
    mit, ohne = 0, []
    for key, r in _ton_items(snap):
        woerter = transkripte.woerter(r["datei"])
        if woerter is None:
            ohne.append(r["name"] or str(r["datei"]))
            continue
        mit += 1
        for seite, t, frame in (("in", r["quell_in"] / fps, r["start"]),
                                ("out", (r["quell_in"] + r["dauer"]) / fps, r["start"] + r["dauer"] - 1)):
            for w in woerter:
                ws, we = float(w["start"]), float(w["end"])
                if not ws < t < we:
                    continue
                weg = (we - t) if seite == "out" else (t - ws)
                if weg >= grenze:
                    befunde.append({"art": "Wort angeschnitten", "frame": int(frame), "frames": 1,
                                    "wert": int(round(weg * 1000)), "wort": w.get("text"), "seite": seite,
                                    "spur": key, "clip": r["name"]})
    return befunde, {"mit_transkript": mit, "ohne_transkript": len(ohne), "ohne_liste": sorted(set(ohne))}


def export_woerter(snap: dict, transkripte, von_s: float, bis_s: float) -> list[dict]:
    """Wörter der aktiven Tonclips in Export-Sekunden, nur innerhalb ihres Items und des Bereichs [von_s, bis_s]."""
    fps = float(snap["fps"])
    out = []
    for _key, r in _ton_items(snap):
        woerter = transkripte.woerter(r["datei"])
        if not woerter:
            continue
        a, b = r["start"] / fps, (r["start"] + r["dauer"]) / fps
        versatz = a - r["quell_in"] / fps
        for w in woerter:
            s, e = float(w["start"]) + versatz, float(w["end"]) + versatz
            if e > max(a, von_s) and s < min(b, bis_s):
                out.append({"text": w.get("text"), "start": round(s, 3), "end": round(e, 3)})
    return sorted(out, key=lambda w: w["start"])


# --- Gesamtprüfung -----------------------------------------------------------------

def kennzahlen(werte) -> dict:
    """Anzahl, Median, 95. Perzentil und Maximum (für die Kalibrierung im Bericht)."""
    w = np.asarray(list(werte), dtype=float)
    if w.size == 0:
        return {"n": 0}
    return {"n": int(w.size), "median": round(float(np.median(w)), 2),
            "p95": round(float(np.percentile(w, 95)), 2), "max": round(float(w.max()), 2)}


def diff_verteilung(diff, bild_schnitte: list[int]) -> dict:
    """``diff`` an Bild-Schnitten gegen die übrigen Frames (ohne ±1 Frame um Schnitte, ohne Frame 0)."""
    d = np.asarray(diff, dtype=float)
    an = np.zeros(d.size, dtype=bool)
    for f in bild_schnitte:
        if 0 <= f < d.size:
            an[f] = True
    nahe = an.copy()
    nahe[1:] |= an[:-1]
    nahe[:-1] |= an[1:]
    if d.size:
        nahe[0] = True
    return {"an_schnitten": kennzahlen(d[an]), "uebrige": kennzahlen(d[~nahe])}


def pruefe(snap: dict, bild: dict | None, audio, sr: int, transkripte, cfg: dict) -> dict:
    """Alle Befund-Regeln auf Schnappschuss und Messwerte anwenden (ohne Bilder).

    ``bild``: Arrays ``mittel``, ``streuung``, ``diff`` je Frame oder None; ``audio``: Samples × Kanäle oder None.
    """
    fps, n = float(snap["fps"]), int(snap["laenge"])
    b_schnitte, t_schnitte = schnitte(snap, "bild"), schnitte(snap, "ton")
    befunde: list[dict] = []
    verteilung: dict = {}
    if bild is not None:
        befunde += schwarz_befunde(bild["mittel"], bild["streuung"], cfg)
        befunde += schnipsel_befunde(bild["diff"], bild["mittel"], bild["streuung"], cfg)
        verteilung["diff"] = diff_verteilung(bild["diff"], b_schnitte)
    if audio is not None:
        kb, verh = knack_befunde(audio, sr, fps, t_schnitte, cfg)
        befunde += kb
        befunde += tonloch_befunde(rms_dbfs_je_frame(audio, sr, fps, n), ton_maske(snap), cfg)
        verteilung["knack_verhaeltnis"] = kennzahlen(verh)
    wb, zaehler = wort_befunde(snap, transkripte, cfg)
    befunde += wb
    befunde.sort(key=lambda x: (x["frame"], ARTEN.index(x["art"])))
    for nr, x in enumerate(befunde, 1):
        x["nr"] = nr
        x["timecode"] = timecode(x["frame"], fps, snap["start_timecode"])
        x["kontext"] = kontext(snap, x["frame"], b_schnitte, t_schnitte)
        if x["art"] == "Schnipsel":
            x["an_schnitt"] = any(abs(s - x["frame"]) <= 1 or abs(s - (x["frame"] + x["frames"])) <= 1
                                  for s in b_schnitte)
    return {"timeline": snap["timeline"], "fps": fps, "laenge": n,
            "umfang": {"bild_schnitte": len(b_schnitte), "ton_schnitte": len(t_schnitte), **zaehler},
            "zaehlung": {a: sum(1 for x in befunde if x["art"] == a) for a in ARTEN},
            "befunde": befunde, "verteilung": verteilung, "warnungen": []}
