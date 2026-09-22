"""gyroflow_bericht.py — Bericht über Sidecars, Überspringungen und gedeckelte Clips (Spec 2026-09-22)."""
from __future__ import annotations

from niro_autocut.gyroflow_bericht import bericht_md


def test_bericht_nennt_sidecars_ueberspringungen_und_deckel():
    erg = {
        "clips": [
            {"clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "zoom_ist": 1.20,
             "zoom_gedeckelt": True, "sidecar": "/m/FX3_0001.gyroflow", "fehler": None},
            {"clip": "FX3_0002", "kamera": "FX3", "haltung": "gimbal", "zoom_ist": 1.06,
             "zoom_gedeckelt": False, "sidecar": "/m/FX3_0002.gyroflow", "fehler": None},
        ],
        "uebersprungen": [{"datei": "/m/ZV_0001.MP4", "grund": "keine Gyrospur"}],
        "stand": "2026-09-22T21:00:00",
    }
    md = bericht_md(erg, [{"datei": "/m/FX3_0001.MP4", "tempo50": True}])

    assert "2 Sidecars" in md
    assert "FX3_0001" in md and "FX3_0002" in md
    assert "keine Gyrospur" in md and "ZV_0001" in md
    assert "gedeckelt" in md.lower()
    assert "50 %" in md            # Zeitlupen-Shots werden eigens genannt


def test_bericht_nennt_fehler_je_clip():
    erg = {"clips": [{"clip": "FX3_0003", "kamera": "FX3", "haltung": "hand", "zoom_ist": None,
                      "zoom_gedeckelt": None, "sidecar": None, "fehler": "kein Gyro gefunden"}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}
    md = bericht_md(erg, [])
    assert "kein Gyro gefunden" in md
