"""gyroflow.py — Preset aus der Telemetrie, Deckel-Prüfung, Sidecar-Pfad, Clip-Export, Charge-Lauf (Spec 2026-09-22)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import gyroflow as G
from niro_autocut.charge import AutoCutError

CFG = {
    "gyroflow": {
        "cli": "/Applications/Gyroflow.app/Contents/MacOS/gyroflow",
        "zeitueberschreitung_s": 300,
        "glaettung": {"stativ": 0.2, "gimbal": 0.4, "hand": 0.7},
        "max_zoom": {"stativ": 105, "gimbal": 110, "hand": 120},
    },
    "telemetrie": {"digitalzoom_faktor": 1.25, "digitalzoom_max": 1.5},
}


def test_deckel_haelt_die_ungleichung_ein():
    G.pruefe_deckel(CFG)   # 120 ≤ 1.5 / 1.25 × 100 = 120 — Gleichheit ist erlaubt


def test_deckel_zu_hoch_bricht_ab():
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["max_zoom"]["hand"] = 130
    with pytest.raises(AutoCutError, match="max_zoom"):
        G.pruefe_deckel(cfg)


def test_preset_nimmt_glaettung_und_deckel_der_haltung():
    p = G.preset_fuer({"haltung": "hand"}, CFG)
    assert p["version"] == 2
    st = p["stabilization"]
    assert st["max_zoom"] == 120
    assert {"name": "smoothness", "value": 0.7} in st["smoothing_params"]


def test_preset_ohne_haltung_nimmt_die_vorsichtigste_stufe():
    p = G.preset_fuer({"haltung": None}, CFG)
    assert p["stabilization"]["max_zoom"] == 105
    assert {"name": "smoothness", "value": 0.2} in p["stabilization"]["smoothing_params"]


def test_preset_hash_haengt_am_inhalt_nicht_an_der_reihenfolge():
    a = G.preset_fuer({"haltung": "gimbal"}, CFG)
    b = json.loads(json.dumps(a))
    assert G.preset_hash(a) == G.preset_hash(b)
    assert len(G.preset_hash(a)) == 12
    assert G.preset_hash(a) != G.preset_hash(G.preset_fuer({"haltung": "hand"}, CFG))
