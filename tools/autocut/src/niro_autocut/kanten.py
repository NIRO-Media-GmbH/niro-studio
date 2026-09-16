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
    """Knackser-Maß am Schnitt-Sample: Rest einer AR-Vorhersage der Ordnung ``knack_ar_ordnung``.

    Die Koeffizienten werden in ±``knack_fenster_ms`` ohne die Kante gefittet; gemessen wird die Spitze des Rests in
    ±``knack_kante_ms`` gegen seine robuste Streuung (MAD) außerhalb der Kante. Sprache und Musik sind gut vorhersagbar,
    ein Sprung im Signal nicht (Kalibrierung Taxodia 16.09.: 99.-Perzentil-Vergleich der zweiten Differenz erkannte
    einen −26-dBFS-Sprung nur an 16 von 51 O-Ton-Kanten, das AR-Maß einen −40-dBFS-Sprung an 51 von 51).
    Je Kanal; zurück kommt der auffälligste Kanal (0-basiert).
    """
    x = np.asarray(audio)
    if x.ndim == 1:
        x = x[:, None]
    p = int(cfg["knack_ar_ordnung"])
    kante = max(1, int(round(cfg["knack_kante_ms"] * sr / 1000)))
    fenster = int(round(cfg["knack_fenster_ms"] * sr / 1000))
    a, b = max(p, sample - fenster), min(len(x), sample + fenster)
    leer = {"spitze": 0.0, "umgebung": 0.0, "verhaeltnis": 0.0, "versatz_ms": 0.0, "kanal": 0}
    if b - a < 4 * p:
        return leer
    idx = np.arange(a, b)
    nah = np.abs(idx - sample) <= kante
    fit = np.abs(idx - sample) > kante + p
    if not nah.any() or int(fit.sum()) < 2 * p:
        return leer
    kandidaten = []
    for k in range(x.shape[1]):
        v = x[a - p:b, k].astype(np.float64)
        X = np.stack([v[p - j:len(v) - j] for j in range(1, p + 1)], axis=1)
        t = v[p:]
        koeff = np.linalg.lstsq(X[fit], t[fit], rcond=None)[0]
        rest = np.abs(t - X @ koeff)
        i = int(np.argmax(rest[nah]))
        spitze = float(rest[nah][i])
        sigma = float(np.median(rest[fit])) / 0.6745
        kandidaten.append({"spitze": spitze, "umgebung": sigma, "verhaeltnis": spitze / max(sigma, 1e-7),
                           "versatz_ms": round((int(idx[nah][i]) - sample) * 1000 / sr, 1), "kanal": k})
    treffer = [c for c in kandidaten if c["spitze"] >= cfg["knack_min"] and c["verhaeltnis"] >= cfg["knack_faktor"]]
    return max(treffer or kandidaten, key=lambda c: c["verhaeltnis"])


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


def _db_mittel(werte) -> float:
    """Mittlere Leistung mehrerer dBFS-Werte, wieder in dBFS (leer → −200)."""
    w = np.asarray(werte, dtype=float)
    if w.size == 0:
        return -200.0
    return float(10.0 * np.log10(max(float(np.mean(np.power(10.0, w / 10.0))), 1e-20)))


def _kanten_pegel(pegel, datei, t: float, ws: float, we: float) -> tuple[float, float] | None:
    """(Pegel an der Kante = leiserer der beiden 20-ms-Streifen, Wortspitze) in dBFS aus 10-ms-RMS; None ohne Quelle."""
    von = max(0.0, min(t, ws) - 0.1)
    db = pegel(datei, von, max(t, we) + 0.1)
    if db is None or len(db) == 0:
        return None
    db = np.asarray(db, dtype=float)
    i = int(round((t - von) / 0.01))
    vor, nach = db[max(0, i - 2):max(0, i)], db[max(0, i):i + 2]
    kante = min(_db_mittel(vor), _db_mittel(nach)) if vor.size and nach.size else -200.0
    a, b = int(np.floor((ws - von) / 0.01)), int(np.ceil((we - von) / 0.01))
    wort = db[max(0, a):max(a + 1, min(len(db), b))]
    return kante, (float(wort.max()) if wort.size else -200.0)


def wort_befunde(snap: dict, transkripte, cfg: dict, pegel=None) -> tuple[list[dict], dict]:
    """Wort angeschnitten (Spec 3, Nachtrag 16.09.): eine O-Ton-Kante liegt an einem Wort (Scribe, ±``wort_toleranz_ms``)
    und der Quellton ist auf beiden Seiten der Kante (je 20 ms) höchstens ``wort_tal_db`` unter der Wortspitze und über
    ``wort_pegel_min_dbfs`` — der Schnitt geht durch hörbaren Klang, nicht durch ein Tal.

    ``pegel(datei, von_s, bis_s)`` liefert 10-ms-RMS in dBFS der Quelldatei oder None (Quelle nicht erreichbar).
    Kalibrierung Taxodia 16.09.: Scribe-Wortenden hängen vor Komma und bei „ähm" bis 300 ms nach; die reine Zeitregel
    meldete vier Schnitte in Pegeltälern (−55 dBFS, 20–25 dB unter dem Wort).
    """
    fps = float(snap["fps"])
    tol = cfg["wort_toleranz_ms"] / 1000.0
    befunde: list[dict] = []
    mit, ohne, ohne_quelle = 0, [], []
    items = [(key, r, transkripte.woerter(r["datei"])) for key, r in _ton_items(snap)]
    oton_spuren = {key for key, _r, w in items if w is not None}      # Musik-/SFX-Spuren ohne Transkript nicht auflisten
    for key, r, woerter in items:
        name = r["name"] or str(r["datei"])
        if woerter is None:
            if key in oton_spuren:
                ohne.append(name)
            continue
        kandidaten = []
        for seite, t, frame in (("in", r["quell_in"] / fps, r["start"]),
                                ("out", (r["quell_in"] + r["dauer"]) / fps, r["start"] + r["dauer"] - 1)):
            nah = [w for w in woerter if float(w["end"]) > float(w["start"])
                   and float(w["start"]) - tol < t < float(w["end"]) + tol]
            if nah:
                w = min(nah, key=lambda w: abs((float(w["start"]) + float(w["end"])) / 2 - t))
                kandidaten.append((seite, t, frame, w))
        messungen = []
        for seite, t, frame, w in kandidaten:
            m = None if pegel is None else _kanten_pegel(pegel, r["datei"], t, float(w["start"]), float(w["end"]))
            if m is None:
                break
            messungen.append((seite, t, frame, w, m))
        if len(messungen) < len(kandidaten):
            ohne_quelle.append(name)
            continue
        mit += 1
        for seite, t, frame, w, (kante, spitze) in messungen:
            if kante >= cfg["wort_pegel_min_dbfs"] and kante >= spitze - cfg["wort_tal_db"]:
                befunde.append({"art": "Wort angeschnitten", "frame": int(frame), "frames": 1,
                                "wert": round(kante - spitze, 1), "kante_dbfs": round(kante, 1), "wort": w.get("text"),
                                "seite": seite, "spur": key, "clip": r["name"], "datei": r["datei"],
                                "quell_s": round(t, 3)})
    return befunde, {"mit_transkript": mit, "ohne_transkript": len(ohne), "ohne_liste": sorted(set(ohne)),
                     "ohne_quelle": len(ohne_quelle), "ohne_quelle_liste": sorted(set(ohne_quelle))}


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


def grafik_hinweise(snap: dict, befunde: list[dict], cfg: dict) -> tuple[list[dict], list[dict]]:
    """Schnipsel höchstens ``grafik_abstand_frames`` neben der Kante eines aktiven Grafik-Items sind gewollte
    Grafik-Übergänge (Flash, Wipe, Iris) und werden zum Hinweis. Grafik-Items: Dateipfad enthält eines der
    ``grafik_pfade`` (Motion-Renders) oder das Item liegt auf einer der ``grafik_spuren``. Kalibrierung Taxodia 16.09.:
    16 von 16 Schnipseln lagen an Kanten der Grafikebene; der User verschob sie später von V4 auf V5.
    Rückgabe: verbleibende Befunde, Hinweise."""
    pfade = [_nfc(x) for x in (cfg.get("grafik_pfade") or [])]
    spuren = set(cfg.get("grafik_spuren") or [])
    kanten = sorted({f for key, rows in snap["spuren"].items() if key.startswith("V") for r in rows if r["aktiv"]
                     and (key in spuren or (r.get("datei") and any(x in _nfc(r["datei"]) for x in pfade)))
                     for f in (r["start"], r["start"] + r["dauer"])})
    if not kanten:
        return befunde, []
    abstand = int(cfg.get("grafik_abstand_frames", 2))
    bleiben, hinweise = [], []
    for x in befunde:
        if x["art"] == "Schnipsel" and any(min(abs(g - x["frame"]), abs(g - (x["frame"] + x["frames"]))) <= abstand
                                           for g in kanten):
            hinweise.append({"art": "Grafik-Übergang", "frame": x["frame"], "frames": x["frames"], "wert": x["wert"]})
        else:
            bleiben.append(x)
    return bleiben, hinweise


def pruefe(snap: dict, bild: dict | None, audio, sr: int, transkripte, cfg: dict, pegel=None) -> dict:
    """Alle Befund-Regeln auf Schnappschuss und Messwerte anwenden (ohne Bilder).

    ``bild``: Arrays ``mittel``, ``streuung``, ``diff`` je Frame oder None; ``audio``: Samples × Kanäle oder None;
    ``pegel``: Quellton-Pegel für die Wortkanten (siehe ``wort_befunde``), ohne → Wortkanten nicht geprüft.
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
    wb, zaehler = wort_befunde(snap, transkripte, cfg, pegel)
    befunde += wb
    warnungen = []
    if zaehler["mit_transkript"] == 0 and zaehler["ohne_quelle"] == 0 and any(True for _ in _ton_items(snap)):
        warnungen.append("Kein Tonclip mit Transkript gefunden — Wortkanten nicht geprüft (transcripts_index.json der "
                         "Charge, Dateinamen der O-Ton-Clips prüfen).")
    befunde, hinweise = grafik_hinweise(snap, befunde, cfg)
    befunde.sort(key=lambda x: (x["frame"], ARTEN.index(x["art"])))
    for nr, x in enumerate(befunde, 1):
        x["nr"] = nr
        x["timecode"] = timecode(x["frame"], fps, snap["start_timecode"])
        x["kontext"] = kontext(snap, x["frame"], b_schnitte, t_schnitte)
        if x["art"] == "Schnipsel":
            x["an_schnitt"] = any(abs(s - x["frame"]) <= 1 or abs(s - (x["frame"] + x["frames"])) <= 1
                                  for s in b_schnitte)
    for h in hinweise:
        h["timecode"] = timecode(h["frame"], fps, snap["start_timecode"])
    return {"timeline": snap["timeline"], "fps": fps, "laenge": n,
            "umfang": {"bild_schnitte": len(b_schnitte), "ton_schnitte": len(t_schnitte), **zaehler},
            "zaehlung": {a: sum(1 for x in befunde if x["art"] == a) for a in ARTEN},
            "befunde": befunde, "hinweise": hinweise, "verteilung": verteilung, "warnungen": warnungen}
