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
import json
import math
import os
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


def gyro_je_frame(werte: np.ndarray, proben_je_sample: int, fps: float, ziel_fps: float = ZIEL_FPS) -> np.ndarray:
    """IMU-Proben (n, k) → Mittel je Zielframe (m, k); Proben je Zielframe = proben_je_sample · fps / ziel_fps."""
    if len(werte) == 0 or proben_je_sample <= 0:
        return np.zeros((0, werte.shape[1] if werte.ndim == 2 else 3), np.float64)
    je = max(1, int(round(proben_je_sample * fps / ziel_fps)))
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
    """(min_px für Schwenk/Tilt, stativ_px): aus °/s über f_px, wenn die KB-Brennweite bekannt ist, sonst px-Standardwerte."""
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


def bewegungsart(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> str:
    """Bewegungsart eines Fensters: statisch, Schwenk/Tilt mit Richtung, gemischt (Richtungswechsel oder beide Achsen), fahrt."""
    if len(dxy) == 0:
        return "statisch"
    wk, bw = wackeln_bewegung(dxy)
    if wk < stativ_px and bw < stativ_px:
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
    """stativ (keine Bewegung), hand (viel Energie über hf_grenze_hz) oder gimbal (Bewegung fast nur darunter)."""
    wk, bw = wackeln_bewegung(dxy)
    if wk < stativ_px and bw < stativ_px:
        return "stativ"
    anteil = hf_anteil(dxy, ZIEL_FPS, float(cfg["hf_grenze_hz"]))
    return "hand" if anteil >= float(cfg["hand_hf_anteil_min"]) else "gimbal"


def fenster(dxy: np.ndarray, cfg: dict, min_px: float, stativ_px: float) -> list[dict]:
    """Fenster von ``fenster_s`` mit Schritt ``schritt_s``; das letzte darf halb so lang sein; kurze Clips: ein Fenster (ab 2 Frames)."""
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
        return {"pitch_grad": None, "roll_grad": None,
                "grund": f"Beschleunigung schwankt ({100 * (1 - float(ruhig.mean())):.0f} % der Proben außerhalb ±{toleranz * 100:.0f} %)"}
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
            "bewegungsart": mehrheit([f["bewegungsart"] for f in fen]),
            "fenster": [[f["t_s"], f["wackeln"], f["bewegung"], f["bewegungsart"], _schaerfe(f)] for f in fen],
            "ruhige_fenster": [f["t_s"] for f in fen if f["wackeln"] <= float(cfg["ruhig_max_px"])],
            "schaerfe_p10": round(float(np.percentile(rel, 10)), 2) if rel is not None else None}
