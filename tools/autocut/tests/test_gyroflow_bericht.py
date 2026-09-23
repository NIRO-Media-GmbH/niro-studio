"""gyroflow_bericht.py — Bericht über Sidecars, Überspringungen und gedeckelte Clips (Spec 2026-09-22)."""
from __future__ import annotations

import unicodedata

from niro_autocut.gyroflow_bericht import bericht_md


def test_bericht_nennt_sidecars_ueberspringungen_und_deckel():
    erg = {
        "clips": [
            {"clip": "FX3_0001", "path": "/m/FX3_0001.MP4", "kamera": "FX3", "haltung": "hand", "zoom_ist": 1.20,
             "zoom_gedeckelt": True, "sidecar": "/m/FX3_0001.gyroflow", "fehler": None},
            {"clip": "FX3_0002", "path": "/m/FX3_0002.MP4", "kamera": "FX3", "haltung": "gimbal", "zoom_ist": 1.06,
             "zoom_gedeckelt": False, "sidecar": "/m/FX3_0002.gyroflow", "fehler": None},
        ],
        "uebersprungen": [{"datei": "/m/ZV_0001.MP4", "grund": "keine Gyrospur"}],
        "stand": "2026-09-22T21:00:00",
    }
    md = bericht_md(erg, [{"datei": "/m/FX3_0001.MP4", "tempo50": True}])

    assert "2 Sidecars" in md
    assert "FX3_0001" in md and "FX3_0002" in md
    assert "keine Gyrospur" in md and "ZV_0001" in md
    assert "50 %" in md            # Zeitlupen-Shots werden eigens genannt


def test_bericht_weist_den_zoom_als_obergrenze_aus_nicht_als_messwert():
    """zoom_ist_lesen liefert in der Praxis immer den Deckel zurück (adaptive_zoom_fovs_dekodiert schreibt niemand,
    Spec Befund 1 Punkt 6). „1,20×" läse sich wie eine Messung, ist aber nur der Deckelwert — Spec Abschnitt 1
    Punkt 4 verlangt ausdrücklich die Obergrenze."""
    erg = {"clips": [{"clip": "FX3_0001", "path": "/m/FX3_0001.MP4", "kamera": "FX3", "haltung": "hand",
                      "zoom_ist": 1.20, "zoom_gedeckelt": True, "sidecar": "/m/FX3_0001.gyroflow", "fehler": None}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}

    md = bericht_md(erg, [])

    zeile = next(z for z in md.splitlines() if z.startswith("| FX3_0001"))
    assert "≤ 1,20×" in zeile and "nicht gemessen" in zeile
    # Kein Abschnitt, der den Deckelwert als Befund ausgibt: er träfe auf jeden exportierten Clip zu.
    assert "## Deckel griff" not in md
    assert "der Rand ist ausgereizt" not in md
    # Stattdessen der Hinweis, dass der digitale Zoom der Brennweitenregel obendrauf kommt (Review-Fund 1).
    assert "digitalzoom_max" in md and "1,8" in md


def test_bericht_behauptet_keine_stabilisierung_sondern_sidecars():
    """Ein Sidecar ist noch keine Stabilisierung — die passiert erst im 6d-Bau. Die Kopfzeile sagte „N von M Clips
    stabilisiert" und versprach damit mehr, als der Lauf tut."""
    erg = {"clips": [{"clip": "FX3_0001", "path": "/m/FX3_0001.MP4", "kamera": "FX3", "haltung": "hand",
                      "zoom_ist": 1.20, "zoom_gedeckelt": True, "sidecar": "/m/FX3_0001.gyroflow", "fehler": None}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}

    md = bericht_md(erg, [])

    assert "stabilisiert," not in md
    assert "1 von 1 Clips mit Sidecar" in md


def test_bericht_nennt_fehler_je_clip():
    erg = {"clips": [{"clip": "FX3_0003", "path": "/m/FX3_0003.MP4", "kamera": "FX3", "haltung": "hand",
                      "zoom_ist": None, "zoom_gedeckelt": None, "sidecar": None, "fehler": "kein Gyro gefunden"}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}
    md = bericht_md(erg, [])
    assert "kein Gyro gefunden" in md
    assert "0 Sidecars" in md      # ein Clip nur mit Fehler zählt nicht als Sidecar (Review-Fund, Minor)


def test_tempo50_wird_ueber_den_pfad_nicht_ueber_den_clip_stamm_gematcht():
    """Kartennummern setzen pro Karte/Dreh neu auf — zwei Quelldateien an verschiedenen Orten können denselben
    Clip-Stamm tragen. Nur die Datei, die in der Shot-Liste wirklich als tempo50 steht, darf 50 % bekommen
    (Review-Fund: das Matching lief vorher über den nicht eindeutigen Clip-Stamm statt über den Pfad)."""
    erg = {
        "clips": [
            {"clip": "FX3_0001", "path": "/m/Tag1/FX3_0001.MP4", "kamera": "FX3", "haltung": "hand",
             "zoom_ist": 1.20, "zoom_gedeckelt": True, "sidecar": "/m/Tag1/FX3_0001.gyroflow", "fehler": None},
            {"clip": "FX3_0001", "path": "/m/Tag2/FX3_0001.MP4", "kamera": "FX3", "haltung": "hand",
             "zoom_ist": 1.10, "zoom_gedeckelt": False, "sidecar": "/m/Tag2/FX3_0001.gyroflow", "fehler": None},
        ],
        "uebersprungen": [], "stand": "2026-09-22T21:00:00",
    }
    md = bericht_md(erg, [{"datei": "/m/Tag1/FX3_0001.MP4", "tempo50": True}])

    zeilen = [z for z in md.splitlines() if z.startswith("| FX3_0001")]
    assert len(zeilen) == 2
    assert sum("50 %" in z for z in zeilen) == 1
    assert sum("100 %" in z for z in zeilen) == 1


def test_tempo50_matcht_auch_ueber_abweichende_unicode_form():
    """Shot-Liste und gyroflow.json können denselben Pfad in verschiedener Unicode-Form tragen (macOS liefert
    Dateinamen teils in NFD). Ohne NFC-Normalisierung stünde die Zeile fälschlich auf 100 % (Review-Fund)."""
    nfc = "/medien/Drehort Grünwald/FX3_0001.MP4"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfc != nfd
    erg = {"clips": [{"clip": "FX3_0001", "path": nfc, "kamera": "FX3", "haltung": "hand", "zoom_ist": 1.20,
                      "zoom_gedeckelt": True, "sidecar": nfc[:-4] + ".gyroflow", "fehler": None}],
           "uebersprungen": [], "stand": "2026-09-22T21:00:00"}

    md = bericht_md(erg, [{"datei": nfd, "tempo50": True}])

    zeile = next(z for z in md.splitlines() if z.startswith("| FX3_0001"))
    assert "50 %" in zeile
