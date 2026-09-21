"""telemetrie.py — Kennzahlen (synthetische Verläufe), später Clip-Messung, Cache, Charge-Lauf, 2b/6d-Helfer (Task 4)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from niro_autocut import telemetrie as T

CFG = {"fenster_s": 2.0, "schritt_s": 1.0, "tiefpass_s": 0.5, "ruhig_max_px": 0.15, "stativ_max_grad_s": 0.3,
       "stativ_max_px": 0.02, "schwenk_min_grad_s": 3.0, "schwenk_min_px": 1.0, "hf_grenze_hz": 3.0,
       "hand_hf_anteil_min": 0.35, "brennweite_klassen_kb": [30, 60], "pitch_klassen_grad": [-60, -8, 8],
       "achsen": {"schwenk": 1, "tilt": 0}, "vorzeichen": {"schwenk": -1, "tilt": 1, "pitch": 1},
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2}


def _sinus(hz: float, amp: float, n: int = 100, fps: float = 25.0) -> np.ndarray:
    t = np.arange(n) / fps
    return np.stack([amp * np.sin(2 * math.pi * hz * t), np.zeros(n)], axis=1)


def test_f_px_und_gyro_je_frame():
    assert T.f_px(36.0) == 480.0 and round(T.f_px(283.8), 1) == 3784.0
    g = np.tile(np.array([[1.0, 2.0, 3.0]]), (160, 1))
    g[80:] *= 2
    m = T.gyro_je_frame(g, 80, 25.0)
    assert m.shape == (2, 3) and np.allclose(m[0], [1, 2, 3]) and np.allclose(m[1], [2, 4, 6])
    assert T.gyro_je_frame(g, 40, 50.0).shape == (2, 3)          # 50p: 40 Proben je Frame, 2 Frames je Zielframe
    assert T.gyro_je_frame(np.zeros((0, 3)), 80, 25.0).shape == (0, 3)


def test_verschiebung_aus_rate_achsen_und_vorzeichen():
    rate = np.zeros((4, 3))
    rate[:, 1] = 10.0                                    # Schwenk um y mit 10 °/s
    dxy = T.verschiebung_aus_rate(rate, 36.0, CFG)     # f_px 480 → 10 °/s ≙ 3,351 px je Frame
    assert dxy.shape == (4, 2) and np.allclose(dxy[:, 0], -3.351, atol=0.01) and np.allclose(dxy[:, 1], 0)
    rate2 = np.zeros((4, 3))
    rate2[:, 0] = 5.0                                    # Tilt um x
    dxy2 = T.verschiebung_aus_rate(rate2, 36.0, CFG)
    assert np.allclose(dxy2[:, 0], 0) and np.allclose(dxy2[:, 1], 1.676, atol=0.01)


def test_wackeln_bewegung_wie_ruhe_py():
    dxy = np.array([[0, 0], [1, 0], [0, 0], [1, 0]], float)
    wk, bw = T.wackeln_bewegung(dxy)
    assert wk == 0.5 and bw == 0.25            # Mittel über beide Spalten: |Δdx| = 1,1,1 / |Δdy| = 0 → 0,5; |dx| Mittel 0,5, |dy| 0 → 0,25
    assert T.wackeln_bewegung(np.zeros((1, 2))) == (0.0, 0.0)


def test_hf_anteil_trennt_schnell_von_langsam():
    assert T.hf_anteil(_sinus(6.0, 1.0)) > 0.9
    assert T.hf_anteil(_sinus(0.5, 3.0)) < 0.1
    assert T.hf_anteil(np.zeros((100, 2))) == 0.0 and T.hf_anteil(np.zeros((4, 2))) == 0.0


def test_schwellen_px_mit_und_ohne_brennweite():
    min_px, stativ_px = T.schwellen_px(36.0, CFG)
    assert round(min_px, 3) == 1.005 and round(stativ_px, 4) == 0.1005     # 3 °/s bzw. 0,3 °/s bei f_px 480
    assert T.schwellen_px(None, CFG) == (1.0, 0.02)


@pytest.mark.parametrize("dxy,erwartet", [
    (np.zeros((50, 2)), "statisch"),
    (np.tile([[2.0, 0.0]], (50, 1)), "schwenk_links"),
    (np.tile([[-2.0, 0.0]], (50, 1)), "schwenk_rechts"),
    (np.tile([[0.0, 2.0]], (50, 1)), "tilt_auf"),
    (np.tile([[0.0, -2.0]], (50, 1)), "tilt_ab"),
    (np.vstack([np.tile([[2.0, 0.0]], (25, 1)), np.tile([[-2.0, 0.0]], (25, 1))]), "gemischt"),
    (np.tile([[2.0, 2.0]], (50, 1)), "gemischt"),
])
def test_bewegungsart_klassen(dxy, erwartet):
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == erwartet


def test_bewegungsart_fahrt_ohne_dominante_richtung():
    rng = np.random.default_rng(0)
    dxy = rng.normal(0, 0.3, (50, 2))                  # Bewegung da, Mittel ≈ 0 → Fahrt
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == "fahrt"


def test_haltung():
    assert T.haltung(np.zeros((100, 2)), 0.02, CFG) == "stativ"
    assert T.haltung(_sinus(6.0, 1.0), 0.02, CFG) == "hand"
    assert T.haltung(_sinus(0.3, 3.0), 0.02, CFG) == "gimbal"


def test_fenster_und_mehrheit():
    fen = T.fenster(np.tile([[2.0, 0.0]], (100, 1)), CFG, 1.0, 0.02)
    assert [f["t_s"] for f in fen] == [0.0, 1.0, 2.0, 3.0] and all(f["bewegungsart"] == "schwenk_links" for f in fen)
    assert [f["t_s"] for f in T.fenster(np.zeros((74, 2)), CFG, 1.0, 0.02)] == [0.0, 1.0]     # 3-s-Clip optisch: 74 Verschiebungen
    assert fen[0]["wackeln"] == 0.0 and fen[0]["bewegung"] == 1.0
    kurz = T.fenster(np.zeros((20, 2)), CFG, 1.0, 0.02)
    assert len(kurz) == 1 and kurz[0]["t_s"] == 0.0
    assert T.fenster(np.zeros((1, 2)), CFG, 1.0, 0.02) == []
    assert T.mehrheit(["fahrt", "fahrt", "statisch"]) == "fahrt" and T.mehrheit(["fahrt", "statisch"]) == "gemischt"
    assert T.mehrheit([]) == "gemischt"


def test_lage_pitch_roll_und_gate():
    ruhig = np.tile([[0.0, 1.15, 0.0]], (200, 1))                       # FX3-Betrag 1,15 g, waagerecht
    l = T.lage(ruhig)
    assert l["pitch_grad"] == 0.0 and l["roll_grad"] == 0.0 and l["grund"] is None
    unten = np.tile([[0.0, math.cos(math.radians(30)), -math.sin(math.radians(30))]], (200, 1))
    assert T.lage(unten)["pitch_grad"] == -30.0                          # Kamera schaut 30° nach unten
    assert T.lage(unten, vorzeichen_pitch=-1.0)["pitch_grad"] == 30.0
    schief = np.tile([[math.sin(math.radians(2)), math.cos(math.radians(2)), 0.0]], (200, 1))
    assert T.lage(schief)["roll_grad"] == 2.0
    wild = np.tile([[0.0, 1.0, 0.0]], (200, 1)) * np.linspace(0.5, 1.5, 200)[:, None]
    assert T.lage(wild)["pitch_grad"] is None and "schwankt" in T.lage(wild)["grund"]
    assert T.lage(np.zeros((0, 3)))["grund"] == "keine Beschleunigungsdaten"


def test_klassen():
    assert [T.brennweitenklasse(k, [30, 60]) for k in (24, 30, 50, 60, 71.6, 283.8)] == ["weit", "normal", "normal", "normal", "tele", "tele"]
    assert [T.perspektive_hoehe(p, [-60, -8, 8]) for p in (-90, -60, -12, -8, 0, 7.9, 8, 20)] == \
        ["Vogelperspektive", "Vogelperspektive", "Aufsicht", "Aufsicht", "Augenhöhe", "Augenhöhe", "Untersicht", "Untersicht"]
    assert T.perspektive_hoehe(None, [-60, -8, 8]) is None


def test_kennzahlen_gesamt():
    k = T.kennzahlen(np.tile([[2.0, 0.0]], (100, 1)), CFG, 36.0)
    assert k["wackeln"] == 0.0 and k["bewegung"] == 1.0 and k["haltung"] == "gimbal" and k["bewegungsart"] == "schwenk_links"
    assert k["fenster"][0] == [0.0, 0.0, 1.0, "schwenk_links", None] and k["ruhige_fenster"] == [0.0, 1.0, 2.0, 3.0]
    assert k["hf_anteil"] == 0.0 and k["schaerfe_p10"] is None
    mit = T.kennzahlen(np.zeros((100, 2)), CFG, None, schaerfe=np.linspace(1.0, 10.0, 101))   # optisch: n+1 Frames
    assert mit["schaerfe_p10"] == 0.21 and mit["fenster"][0][4] < mit["fenster"][-1][4] <= 1.1
    assert mit["fenster"][0][4] == round(float(np.percentile(np.linspace(1.0, 10.0, 101)[:50], 10)) / 9.1, 2)
    unruhig = T.kennzahlen(_sinus(6.0, 1.0), CFG, None)
    assert unruhig["haltung"] == "hand" and unruhig["ruhige_fenster"] == [] and unruhig["hf_anteil"] > 0.9
