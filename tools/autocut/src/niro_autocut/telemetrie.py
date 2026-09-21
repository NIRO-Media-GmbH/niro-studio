"""Kamera-Telemetrie je Clip (Spec 2026-09-19): Kennzahlen aus der Sony-rtmd-Datenspur (Gyro, Beschleunigung, Brennweite)
oder aus der optischen Verschiebungsreihe, Clip-Messung mit Cache, Charge-Lauf, Abschnittswerte für Stufe 2b und der
Stabilisierungs-Vorschlag für 6d.

Beide Messwege liefern dieselbe Größe: Verschiebung des Bildinhalts je 25-fps-Frame in px @480 (``dx`` > 0 nach rechts,
``dy`` > 0 nach unten). Der Gyro wird über die KB-Brennweite umgerechnet: ``f_px = 480 · kb_mm / 36``,
``dx = ω_schwenk · π/180 · f_px / 25``. ``wackeln`` = Mittel von |Δdx|,|Δdy| zwischen Nachbarframes (Zittern),
``bewegung`` = Mittel von |dx|,|dy| (langsame Kamerabewegung) — wie ``jitter``/``bewegung`` in ``ruhe.py``.
Bewegungsart: ``schwenk_links`` = Kamera dreht nach links = Bildinhalt wandert nach rechts.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import ffprobe, fingerprint
from .rtmd import auswerten, datenspur_lesen, kamera_erkennen, samples, sidecar_modell
from .telemetrie_optisch import graustufen, verschiebungen
from .telemetrie_optisch import schaerfe as schaerfe_frames

ZIEL_FPS = 25.0
BEWEGUNGSARTEN = ["statisch", "schwenk_links", "schwenk_rechts", "tilt_auf", "tilt_ab", "fahrt", "gemischt"]
HALTUNGEN = ["stativ", "gimbal", "hand"]
CACHE_DIR = "telemetrie"
VIDEO_EXTS = {".mp4", ".mov", ".mxf"}


# --- Kennzahlen ---------------------------------------------------------------------------------------------------------

def f_px(kb_mm: float, breite: int = 480) -> float:
    """Brennweite in Pixeln bei Bildbreite ``breite`` (Kleinbild 36 mm breit)."""
    return breite * float(kb_mm) / 36.0


def gyro_je_frame(werte: np.ndarray, proben_je_sample: int, fps: float, ziel_fps: float = ZIEL_FPS,
                  imu_hz: float | None = None) -> np.ndarray:
    """IMU-Proben (n, k) → Mittel je Zielframe (m, k); Proben je Zielframe = imu_hz / ziel_fps (IMU-Rate aus Tag 0xE435),
    ohne Rate proben_je_sample · fps / ziel_fps (driftet bei 59,94p/119,88p: dort schwankt die Probenzahl je Sample)."""
    if len(werte) == 0 or (not imu_hz and proben_je_sample <= 0):
        return np.zeros((0, werte.shape[1] if werte.ndim == 2 else 3), np.float64)
    je = max(1, int(round(imu_hz / ziel_fps if imu_hz else proben_je_sample * fps / ziel_fps)))
    m = len(werte) // je
    return werte[: m * je].reshape(m, je, -1).mean(axis=1)


def verschiebung_aus_rate(rate: np.ndarray, kb_mm: float, cfg: dict,
                          ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """(m, 3) °/s je Frame → (m, 2) px: dx aus der Schwenk-Achse, dy aus der Tilt-Achse (Achsen/Vorzeichen aus cfg)."""
    k = math.pi / 180.0 * f_px(kb_mm, int(cfg["optisch_breite"])) / ziel_fps
    a, v = cfg["achsen"], cfg["vorzeichen"]
    dx = float(v["schwenk"]) * rate[:, int(a["schwenk"])] * k
    dy = float(v["tilt"]) * rate[:, int(a["tilt"])] * k
    return np.stack([dx, dy], axis=1)


def wackeln_bewegung(dxy: np.ndarray) -> tuple[float, float]:
    """(wackeln, bewegung) in px je Frame wie ``ruhe.py``: Mittel von |Δ| zwischen Nachbarframes bzw. Mittel von |Wert|."""
    if len(dxy) == 0:
        return 0.0, 0.0
    bewegung = float(np.abs(dxy).mean())
    if len(dxy) < 2:
        return 0.0, bewegung
    return float(np.abs(np.diff(dxy, axis=0)).mean()), bewegung


def hf_anteil(dxy: np.ndarray, fps: float = ZIEL_FPS, grenze_hz: float = 3.0) -> float:
    """Leistungsanteil der Verschiebungsreihe ab ``grenze_hz`` (Mittel über dx und dy), 0–1; 0 bei zu kurzer/leerer Reihe."""
    n = len(dxy)
    if n < 8:
        return 0.0
    freq = np.fft.rfftfreq(n, d=1.0 / fps)
    anteile = []
    for c in range(dxy.shape[1]):
        x = dxy[:, c] - dxy[:, c].mean()
        p = np.abs(np.fft.rfft(x)) ** 2
        gesamt = float(p[1:].sum())
        if gesamt > 0:
            anteile.append(float(p[freq >= grenze_hz].sum()) / gesamt)
    return float(np.mean(anteile)) if anteile else 0.0


def schwellen_px(kb_mm: float | None, cfg: dict) -> tuple[float, float]:
    """(min_px für Schwenk/Tilt, stativ_px): aus °/s über f_px, wenn Brennweite bekannt, sonst px-Werte."""
    if kb_mm:
        k = math.pi / 180.0 * f_px(kb_mm, int(cfg["optisch_breite"])) / ZIEL_FPS
        return float(cfg["schwenk_min_grad_s"]) * k, float(cfg["stativ_max_grad_s"]) * k
    return float(cfg["schwenk_min_px"]), float(cfg["stativ_max_px"])


def _tiefpass(x: np.ndarray, breite: int) -> np.ndarray:
    """Gleitendes Mittel über ``breite`` Frames je Spalte, Ränder auf die vorhandenen Werte normiert."""
    if breite <= 1 or len(x) == 0:
        return x.astype(np.float64)
    k = np.ones(breite) / breite
    norm = np.convolve(np.ones(len(x)), k, mode="same")
    return np.stack([np.convolve(x[:, c], k, mode="same") / norm for c in range(x.shape[1])], axis=1)


def _ist_stativ(dxy: np.ndarray, stativ_px: float) -> bool:
    """Stativ (keine Bewegung): Zittern und Bewegung beide unter Schwelle."""
    wk, bw = wackeln_bewegung(dxy)
    return wk < stativ_px and bw < stativ_px


def bewegungsart(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> str:
    """Bewegungsart eines Fensters: statisch, Schwenk/Tilt, gemischt oder fahrt."""
    if len(dxy) == 0:
        return "statisch"
    if _ist_stativ(dxy, stativ_px):
        return "statisch"
    glatt = _tiefpass(dxy, int(round(float(cfg["tiefpass_s"]) * ZIEL_FPS)))
    h = len(glatt) // 2
    if h >= 2:
        for c in (0, 1):
            a, b = float(glatt[:h, c].mean()), float(glatt[h:, c].mean())
            if abs(a) >= min_px and abs(b) >= min_px and a * b < 0:
                return "gemischt"
    mx, my = float(glatt[:, 0].mean()), float(glatt[:, 1].mean())
    ax, ay = abs(mx), abs(my)
    if ax >= min_px and ax >= 1.5 * ay:
        return "schwenk_links" if mx > 0 else "schwenk_rechts"
    if ay >= min_px and ay >= 1.5 * ax:
        return "tilt_auf" if my > 0 else "tilt_ab"
    if ax >= min_px and ay >= min_px:
        return "gemischt"
    return "fahrt"


def haltung(dxy: np.ndarray, stativ_px: float, cfg: dict) -> str:
    """stativ (keine Bewegung), hand (viel Energie über Grenzfrequenz) oder gimbal (nur darunter)."""
    if _ist_stativ(dxy, stativ_px):
        return "stativ"
    anteil = hf_anteil(dxy, ZIEL_FPS, float(cfg["hf_grenze_hz"]))
    return "hand" if anteil >= float(cfg["hand_hf_anteil_min"]) else "gimbal"


def fenster(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> list[dict]:
    """Fenster von ``fenster_s`` mit Schritt ``schritt_s``; letztes halb so lang; ab 2 Frames."""
    n = len(dxy)
    w = max(2, int(round(float(cfg["fenster_s"]) * ZIEL_FPS)))
    s = max(1, int(round(float(cfg["schritt_s"]) * ZIEL_FPS)))
    # erstes Fenster immer (ab 2 Frames), weitere nur, wenn noch mindestens ein halbes Fenster übrig ist
    starts = [st for st in range(0, n, s) if st == 0 or n - st >= w // 2] if n >= 2 else []
    out = []
    for st in starts:
        teil = dxy[st:st + w]
        wk, bw = wackeln_bewegung(teil)
        out.append({"t_s": round(st / ZIEL_FPS, 1), "wackeln": round(wk, 3), "bewegung": round(bw, 3),
                    "bewegungsart": bewegungsart(teil, cfg, min_px, stativ_px)})
    return out


def mehrheit(werte: list[str], anteil: float = 0.6) -> str:
    """Häufigster Wert, wenn er mindestens ``anteil`` der Fenster stellt, sonst „gemischt"."""
    if not werte:
        return "gemischt"
    wert, n = Counter(werte).most_common(1)[0]
    return wert if n / len(werte) >= anteil else "gemischt"


def lage(acc: np.ndarray, toleranz: float = 0.10, vorzeichen_pitch: float = 1.0) -> dict:
    """Pitch (< 0: Kamera schaut nach unten) und Roll aus dem Median-Schwerkraftvektor der ruhigen Proben
    (|a| innerhalb ±toleranz um den Clip-Median — FX3 misst konstant 1,15 g, daher relativ, nie absolut)."""
    if len(acc) == 0:
        return {"pitch_grad": None, "roll_grad": None, "grund": "keine Beschleunigungsdaten"}
    betrag = np.linalg.norm(acc, axis=1)
    med = float(np.median(betrag))
    if med <= 0:
        return {"pitch_grad": None, "roll_grad": None, "grund": "Beschleunigung null"}
    ruhig = np.abs(betrag - med) <= toleranz * med
    if float(ruhig.mean()) < 0.5:
        anteil = 100 * (1 - float(ruhig.mean()))
        return {"pitch_grad": None, "roll_grad": None,
                "grund": f"Beschleunigung schwankt ({anteil:.0f} % außerhalb "
                         f"±{toleranz * 100:.0f} %)"}
    a = np.median(acc[ruhig], axis=0)          # x links, y oben, z vorwärts
    pitch = vorzeichen_pitch * math.degrees(math.atan2(a[2], math.hypot(a[0], a[1])))
    roll = math.degrees(math.atan2(a[0], a[1]))
    return {"pitch_grad": round(pitch + 0.0, 1), "roll_grad": round(roll + 0.0, 1), "grund": None}


def brennweitenklasse(kb_mm: float, grenzen: list | tuple) -> str:
    """weit unter grenzen[0], tele über grenzen[1], dazwischen normal (Grenzen zählen zu normal)."""
    if kb_mm < grenzen[0]:
        return "weit"
    if kb_mm > grenzen[1]:
        return "tele"
    return "normal"


def perspektive_hoehe(pitch_grad: float | None, grenzen: list | tuple) -> str | None:
    """Vogelperspektive ≤ grenzen[0], Aufsicht ≤ grenzen[1], Untersicht ≥ grenzen[2], sonst Augenhöhe; None ohne Pitch."""
    if pitch_grad is None:
        return None
    if pitch_grad <= grenzen[0]:
        return "Vogelperspektive"
    if pitch_grad <= grenzen[1]:
        return "Aufsicht"
    if pitch_grad >= grenzen[2]:
        return "Untersicht"
    return "Augenhöhe"


def kennzahlen(dxy: np.ndarray, cfg: dict, kb_mm: float | None,
               schaerfe: np.ndarray | None = None) -> dict:
    """wackeln, bewegung, haltung, bewegungsart (Mehrheit der Fenster), fenster, ruhige_fenster aus einer Verschiebungsreihe;
    ``fenster_s`` = Fensterlänge, mit der ``fenster`` gebaut wurde (Auswertung später mit derselben Länge);
    ``schaerfe`` je Frame (optional) wird relativ zum 90. Perzentil des Clips als p10 je Fenster und je Clip ausgegeben."""
    min_px, stativ_px = schwellen_px(kb_mm, cfg)
    wk, bw = wackeln_bewegung(dxy)
    fen = fenster(dxy, cfg, min_px, stativ_px)
    rel = None
    if schaerfe is not None and len(schaerfe):
        p90 = float(np.percentile(schaerfe, 90))
        rel = np.asarray(schaerfe, np.float64) / p90 if p90 > 0 else None
    w = max(2, int(round(float(cfg["fenster_s"]) * ZIEL_FPS)))

    def _schaerfe(f: dict):
        if rel is None:
            return None
        st = int(round(f["t_s"] * ZIEL_FPS))
        teil = rel[st:st + w]
        return round(float(np.percentile(teil, 10)), 2) if len(teil) else None

    return {"wackeln": round(wk, 3), "bewegung": round(bw, 3), "haltung": haltung(dxy, stativ_px, cfg),
            "hf_anteil": round(hf_anteil(dxy, ZIEL_FPS, float(cfg["hf_grenze_hz"])), 3),
            "bewegungsart": mehrheit([f["bewegungsart"] for f in fen]), "fenster_s": float(cfg["fenster_s"]),
            "fenster": [[f["t_s"], f["wackeln"], f["bewegung"], f["bewegungsart"], _schaerfe(f)] for f in fen],
            "ruhige_fenster": [f["t_s"] for f in fen if f["wackeln"] <= float(cfg["ruhig_max_px"])],
            "schaerfe_p10": round(float(np.percentile(rel, 10)), 2) if rel is not None else None}


# --- Clip-Messung ---------------------------------------------------------------------------------------------------------

def config_hash(cfg: dict) -> str:
    """Kurzer Hash (12 Hex-Zeichen, sha1) der ``telemetrie:``-Config ohne ``parallel`` — Haltung, Bewegungsart, Klassen,
    wackeln × px_faktor, ruhige Fenster und Fensterlänge hängen an ihr; ein Cache-Datensatz mit anderem Hash ist veraltet."""
    text = json.dumps({k: v for k, v in cfg.items() if k != "parallel"}, sort_keys=True, default=str)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _leer(path: Path, kamera: str, modell: str | None) -> dict:
    return {"path": str(path), "clip": path.stem, "kamera": kamera, "modell": modell, "dauer_s": None, "fps": None,
            "quelle": "keine", "imu_hz": None, "samples": 0, "brennweite_mm": None, "kb_mm": None, "kb_min": None,
            "kb_max": None, "zoomfahrt": False, "fokus_m": None, "brennweitenklasse": None, "pitch_grad": None,
            "roll_grad": None, "lage_grund": None, "perspektive_hoehe": None, "haltung": None, "hf_anteil": None,
            "bewegungsart": None, "wackeln": None, "bewegung": None, "fenster_s": None, "fenster": [],
            "ruhige_fenster": [], "schaerfe_p10": None, "config_hash": None, "fehler": None}


def _frames(p: Path, cfg: dict) -> np.ndarray:
    breite = int(cfg["optisch_breite"])
    return graustufen(p, ZIEL_FPS, breite=breite, hoehe=int(round(breite * 9 / 16)))


def clip_messen(path: str | Path, cfg: dict, ohne_optisch: bool = False, schaerfe: bool = False) -> dict:
    """Ein Clip: rtmd-Weg (Gyro über KB-Brennweite in px), sonst optischer Weg, sonst ``quelle: keine``; Fehler im Datensatz.
    ``schaerfe=True`` dekodiert auch bei rtmd-Clips die Frames für die Schärfe (optischer Weg hat sie ohnehin)."""
    p = Path(path)
    modell = sidecar_modell(p)
    kamera = kamera_erkennen(p, modell)
    out = _leer(p, kamera, modell)
    out["config_hash"] = config_hash(cfg)
    try:
        info = ffprobe(p)
        out["dauer_s"], out["fps"] = round(float(info.duration_s), 2), float(info.fps)
        daten = None
        buf = datenspur_lesen(p)
        if buf:
            daten = auswerten(samples(buf))
        kb = None
        if daten is not None:
            out["samples"] = daten.samples
            if daten.kb_mm:
                kb = float(np.median(daten.kb_mm))
                out["kb_mm"], out["kb_min"], out["kb_max"] = (round(kb, 1), round(min(daten.kb_mm), 1),
                                                              round(max(daten.kb_mm), 1))
                out["zoomfahrt"] = bool(out["kb_max"] / max(out["kb_min"], 0.1) > 1.3)
                out["brennweitenklasse"] = brennweitenklasse(kb, cfg["brennweite_klassen_kb"])
            if daten.brennweite_mm:
                out["brennweite_mm"] = round(float(np.median(daten.brennweite_mm)), 1)
            if daten.fokus_m:
                out["fokus_m"] = round(float(np.median(daten.fokus_m)), 2)
            if len(daten.acc):
                l = lage(daten.acc, vorzeichen_pitch=float(cfg["vorzeichen"].get("pitch", 1)))
                out["pitch_grad"], out["roll_grad"], out["lage_grund"] = l["pitch_grad"], l["roll_grad"], l["grund"]
                out["perspektive_hoehe"] = perspektive_hoehe(l["pitch_grad"], cfg["pitch_klassen_grad"])
        gyro_ok = (daten is not None and len(daten.gyro) > 0 and daten.proben_je_sample > 0 and kb is not None
                   and kamera not in (cfg.get("optisch_fuer") or []))
        if gyro_ok:
            out["imu_hz"] = float(daten.imu_hz or daten.proben_je_sample * info.fps)
            rate = gyro_je_frame(daten.gyro, daten.proben_je_sample, info.fps, imu_hz=daten.imu_hz)
            faktor = float((cfg.get("px_faktor") or {}).get(kamera, 1.0))
            dxy = verschiebung_aus_rate(rate, kb, cfg) * faktor
            s = schaerfe_frames(_frames(p, cfg)) if schaerfe else None
            out.update(quelle="rtmd", **kennzahlen(dxy, cfg, kb, s))
        elif not ohne_optisch:
            frames = _frames(p, cfg)
            out.update(quelle="optisch", **kennzahlen(verschiebungen(frames), cfg, kb, schaerfe_frames(frames)))
    except AutoCutError as e:
        out["fehler"] = str(e)
    return out


def clip_mit_cache(ch, path: str | Path, cfg: dict, force: bool = False, ohne_optisch: bool = False,
                   schaerfe: bool = False) -> tuple[dict, bool]:
    """Datensatz aus ``_intern/autocut/telemetrie/<fingerprint>.json`` oder neu messen (atomar geschrieben).
    Eine kaputte/unlesbare Cache-Datei sowie ein gecachter Datensatz mit ``fehler`` oder mit fehlendem/anderem
    ``config_hash`` (Config unter ``telemetrie:`` geändert) gelten als Cache-Fehlschlag (neu messen, Datei überschreiben)
    statt den Lauf abzubrechen oder veraltete Werte zurückzugeben. Ein Cache-Treffer trägt Pfad und Clip-Namen des
    Aufrufs (der Fingerprint hängt nicht am Pfad — Material kann NAS → SSD gewandert sein)."""
    fp = fingerprint(path)
    cache = Path(ch.autocut) / CACHE_DIR / f"{fp}.json"
    if cache.exists() and not force:
        try:
            rec = json.loads(cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            rec = None
        if isinstance(rec, dict):
            veraltet = (rec.get("fehler") or (rec.get("quelle") == "keine" and not ohne_optisch)
                       or (schaerfe and rec.get("schaerfe_p10") is None) or rec.get("config_hash") != config_hash(cfg))
            if not veraltet:
                rec["path"], rec["clip"] = str(path), Path(path).stem
                return rec, True
    rec = clip_messen(path, cfg, ohne_optisch, schaerfe)
    rec["fingerprint"] = fp
    rec["gemessen_am"] = _dt.datetime.now().isoformat(timespec="seconds")
    ch.assert_writable(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    # je Schreiber ein eindeutiger .part-Name (pid + Thread-Id): zwei Schreiber mit gleichem Fingerprint
    # (Dublette in der Clip-Liste oder zwei Pfade mit gleichem Name/Größe/mtime) kollidieren sonst im selben .part.
    part = cache.with_name(f"{cache.name}.{os.getpid()}-{threading.get_ident()}.part")
    part.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(part, cache)
    return rec, False


# --- Clip-Quellen und Charge-Lauf ------------------------------------------------------------------------------------------

def _videos(root: Path) -> list[dict]:
    """Videodateien unter ``root`` (rekursiv, ohne Proxy-Ordner und versteckte Dateien); ``ordner`` relativ zur Wurzel."""
    out = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in VIDEO_EXTS or f.name.startswith("."):
            continue
        if any(part == "Proxy" or part.startswith(".") for part in f.relative_to(root).parts[:-1]):
            continue
        out.append({"path": str(f), "ordner": "/".join(f.relative_to(root).parts[:-1])})
    return out


def clips_finden(ch, ordner: list[str] | None = None) -> list[dict]:
    """Clip-Liste: --ordner → broll_index.json → inventar.json → B-Roll-Wurzeln des Transkript-Index → media.json."""
    if ordner:
        clips = []
        for o in ordner:
            root = Path(o).expanduser()
            if not root.is_dir():
                raise AutoCutError(f"Ordner nicht gefunden: {root}\nIst das NAS gemountet?")
            clips += _videos(root)
        return clips
    ac = Path(ch.autocut)
    index = ch.read_json("broll_index.json")
    if index and index.get("clips"):
        return [{"path": str(c["path"]), "ordner": c.get("ordner") or ""} for c in index["clips"]]
    inventar = ch.read_json("inventar.json")
    if inventar:
        return [{"path": str(c["path"]), "ordner": c.get("ordner") or ""} for c in inventar]
    if (Path(ch.intern) / "transcripts_index.json").exists():
        from .broll_index import discover_broll
        clips = discover_broll(ch.load_index())
        if clips:
            return [{"path": c["path"], "ordner": c.get("ordner") or ""} for c in clips]
    media = ch.read_json("media.json")
    if media and media.get("clips"):
        return [{"path": p, "ordner": Path(p).parent.name} for p in media["clips"]]
    raise AutoCutError(f"Keine Clips gefunden: weder --ordner noch broll_index.json, inventar.json, Transkript-Index oder "
                       f"media.json unter {ac}.")


def clips_eindeutig(clips: list[dict]) -> list[dict]:
    """Clip-Liste ohne doppelte Pfade (erster Eintrag gewinnt, samt ``ordner``); Reihenfolge bleibt."""
    gesehen: set[str] = set()
    eindeutig: list[dict] = []
    for c in clips:
        if c["path"] not in gesehen:
            gesehen.add(c["path"])
            eindeutig.append(c)
    return eindeutig


def _zusammenfuehren(clips: list[dict], ergebnisse: dict[str, dict], alt: list[dict]) -> list[dict]:
    """``telemetrie.json`` nach einem (Teil-)Lauf: zuerst die Clip-Liste des Laufs in ihrer Reihenfolge (Ergebnis dieses
    Laufs, sonst der bisherige Eintrag), danach die übrigen bisherigen Einträge in alter Reihenfolge — ohne Dubletten nach
    Pfad und ohne bisherige Einträge, deren Fingerprint schon vorkommt (Clip umgezogen, z. B. NAS → SSD)."""
    alt_je_pfad: dict[str, dict] = {}
    for r in alt:
        alt_je_pfad.setdefault(str(r.get("path")), r)
    out: list[dict] = []
    for c in clips:
        if c["path"] in ergebnisse:
            out.append(ergebnisse[c["path"]])
        elif c["path"] in alt_je_pfad:
            out.append(alt_je_pfad[c["path"]])
    pfade = {str(r.get("path")) for r in out}
    fingerprints = {r["fingerprint"] for r in out if r.get("fingerprint")}
    for r in alt:
        p, fp = str(r.get("path")), r.get("fingerprint")
        if p in pfade or (fp and fp in fingerprints):
            continue
        out.append(r)
        pfade.add(p)
        if fp:
            fingerprints.add(fp)
    return out


def telemetrie_charge(ch, clips: list[dict], cfg: dict, limit: int | None = None, force: bool = False,
                      ohne_optisch: bool = False, parallel: int | None = None, melden=print, schaerfe: bool = False) -> dict:
    """Clips messen (Cache je Clip, parallel) und ``telemetrie.json`` (Liste) schreiben; Fehler je Clip sammeln, bricht
    dabei nie ab (KeyboardInterrupt ausgenommen). Doppelte Pfade werden vor ``limit`` entfernt (erster Eintrag gewinnt,
    samt ``ordner``). Ein Teil-Lauf (``limit``, andere ``--ordner``) ergänzt ``telemetrie.json``, statt sie zu kürzen
    (siehe ``_zusammenfuehren``); ``clips`` der Rückgabe = nur dieser Lauf, ``gesamt`` = Einträge in ``telemetrie.json``."""
    eindeutig = clips_eindeutig(clips)
    todo = eindeutig[:limit] if limit else eindeutig
    fehlend = [c["path"] for c in todo if not Path(c["path"]).is_file()]
    if todo and len(fehlend) == len(todo):
        raise AutoCutError(f"Keine der {len(todo)} Dateien erreichbar (z. B. {fehlend[0]}) — ist das NAS gemountet?")
    ergebnisse: dict[str, dict] = {}
    fehler: list[str] = []
    treffer = gemessen = 0
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel or cfg.get("parallel", 2))))
    try:
        futs = {ex.submit(clip_mit_cache, ch, c["path"], cfg, force, ohne_optisch, schaerfe): c for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            c = futs[fut]
            name = Path(c["path"]).name
            try:
                rec, aus_cache = fut.result()
            except Exception as e:
                # Jede Ausnahme eines einzelnen Clips (AutoCutError wie z. B. fingerprint → „Datei nicht gefunden",
                # aber auch JSON-/OSError/struct-/ValueError aus einer ungewöhnlichen Datenspur …) bricht den Lauf
                # nicht ab: Eintrag mit fehler in die Ergebnisliste, nicht in den Cache geschrieben.
                meldung = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
                fehler.append(f"{name}: {meldung}")
                melden(f"[{i}/{len(todo)}] FEHLER {name}: {meldung}", flush=True)
                # kamera nur aus dem Dateinamen (kamera_erkennen ohne modell) — sidecar_modell liest eine Datei
                # und darf hier nicht erneut aufgerufen werden: ein OSError darin (Rechte-Fehler auf dem
                # Sidecar-XML) würde sonst ungefangen aus diesem except-Zweig entkommen und den Lauf abbrechen.
                p = Path(c["path"])
                rec = _leer(p, kamera_erkennen(p), None)
                rec["fehler"], rec["ordner"] = meldung, c.get("ordner") or ""
                ergebnisse[c["path"]] = rec
                continue
            rec["ordner"] = c.get("ordner") or ""
            if rec.get("fehler"):
                fehler.append(f"{name}: {rec['fehler']}")
            treffer += int(aus_cache)
            gemessen += int(not aus_cache)
            ergebnisse[c["path"]] = rec
            melden(f"[{i}/{len(todo)}] {'Cache' if aus_cache else rec['quelle']:<7} {name}: {rec.get('haltung') or '-'} / "
                   f"{rec.get('bewegungsart') or '-'} / wackeln "
                   f"{rec['wackeln'] if rec.get('wackeln') is not None else '-'}", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    liste = [ergebnisse[c["path"]] for c in todo if c["path"] in ergebnisse]
    gesamt = _zusammenfuehren(eindeutig, ergebnisse, laden(ch.autocut))
    ch.write_json("telemetrie.json", gesamt)
    return {"clips": liste, "fehler": fehler, "cache_treffer": treffer, "gemessen": gemessen, "gesamt": len(gesamt)}


def laden(autocut_dir: str | Path) -> list[dict]:
    """``telemetrie.json`` als Liste von Datensätzen; leer, wenn es sie nicht gibt oder sie kaputt/unlesbar ist —
    Telemetrie ist überall optional, ohne Daten gelten die bisherigen Standards (6d-Vorlage lädt sie beim Import)."""
    p = Path(autocut_dir) / "telemetrie.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return []
    if isinstance(data, dict):
        data = data.get("clips")
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def finden(tele: list[dict], path: str | Path) -> dict | None:
    """Datensatz zum Pfad: exakt, sonst über den Dateinamen (nur wenn eindeutig — Material kann NAS → SSD gewandert sein)."""
    s = str(path)
    for r in tele:
        if r.get("path") == s:
            return r
    name = Path(s).name
    treffer = [r for r in tele if Path(str(r.get("path", ""))).name == name]
    return treffer[0] if len(treffer) == 1 else None


# --- Helfer für Stufe 2b und 6d ------------------------------------------------------------------------------

def _fenster_im_bereich(rec: dict, von_s: float, bis_s: float, fenster_s: float) -> list[list]:
    """Fenster, deren Mitte im Bereich liegt; gibt es keine (Bereich kürzer als ein Fenster), alle überlappenden.
    Fensterlänge = ``fenster_s`` des Datensatzes (mit ihr wurden die Fenster gebaut), sonst der übergebene Wert."""
    fenster_s = float(rec.get("fenster_s") or fenster_s)
    alle = rec.get("fenster") or []
    mitte = [f for f in alle if von_s <= f[0] + fenster_s / 2 <= bis_s]
    return mitte or [f for f in alle if f[0] < bis_s and f[0] + fenster_s > von_s]


def abschnitt_werte(rec: dict | None, von_s: float, bis_s: float, fenster_s: float = 2.0) -> dict:
    """``bewegungsart`` (Mehrheit der Fenster im Bereich) und ``haltung`` des Clips für einen Abschnitt; None ohne Daten."""
    if not rec or not rec.get("fenster"):
        return {"bewegungsart": None, "haltung": (rec or {}).get("haltung")}
    fen = _fenster_im_bereich(rec, von_s, bis_s, fenster_s)
    return {"bewegungsart": mehrheit([f[3] for f in fen]) if fen else None, "haltung": rec.get("haltung")}


def genutzter_quellbereich_s(src_in_f: int, n_f: int, clip_fps: float, langsam: bool,
                             ziel_fps: float = ZIEL_FPS) -> tuple[float, float]:
    """Start und Ende (s) des Quellbereichs, den n_f Timeline-Frames (bei ziel_fps) ab Quellframe src_in_f bei
    100 % bzw. 50 % Tempo (langsam) nutzen; Ende = src_in_f + n_f · clip_fps / ziel_fps · (0,5 bei langsam,
    sonst 1,0) Quellframes, beide Werte durch clip_fps geteilt (6d: Quellbereich für stabil_vorschlag)."""
    ende_f = src_in_f + n_f * clip_fps / ziel_fps * (0.5 if langsam else 1.0)
    return src_in_f / clip_fps, ende_f / clip_fps


def stabil_vorschlag(von_s: float, bis_s: float, rec: dict | None, cfg: dict,
                     path: str | Path | None = None) -> tuple[bool, str]:
    """6d: stabilisieren? Datei ``_stabilized`` (Avata-Export, Regel 18.09.) → nie; hand mit wackeln > ruhig_max_px → ja;
    stativ/gimbal → nein; ohne Telemetrie → ja (bisheriger Standard). ``wackeln`` = Mittel der Fenster im
    genutzten Quellbereich."""
    name = Path(str(path or (rec or {}).get("path") or "")).name.lower()
    if "_stabilized" in name:
        return False, "bereits stabilisiert (Dateiname _stabilized)"
    if not rec or rec.get("quelle") in (None, "keine") or rec.get("fehler"):
        return True, "keine Telemetrie → Standard stabilisieren"
    fen = _fenster_im_bereich(rec, von_s, bis_s, float(cfg["fenster_s"]))
    wk = float(np.mean([f[1] for f in fen])) if fen else float(rec.get("wackeln") or 0.0)
    grenze = float(cfg["ruhig_max_px"])
    h = rec.get("haltung")
    if h == "stativ":
        return False, f"Stativ (wackeln {wk:.2f} px)".replace(".", ",")
    if h == "gimbal":
        return False, f"Gimbal (wackeln {wk:.2f} px)".replace(".", ",")
    if wk > grenze:
        return True, f"Hand, wackeln {wk:.2f} px > {grenze:.2f}".replace(".", ",")
    return False, f"Hand, aber ruhig (wackeln {wk:.2f} px ≤ {grenze:.2f})".replace(".", ",")
