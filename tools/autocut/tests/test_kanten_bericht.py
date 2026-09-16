"""kanten_bericht: Markdown mit und ohne Befunde."""
from __future__ import annotations

from niro_autocut.kanten import ARTEN
from niro_autocut.kanten_bericht import bericht


def _erg(befunde: list[dict]) -> dict:
    return {"timeline": "T", "fps": 25.0, "laenge": 50,
            "export": {"datei": "/e/T.mov", "fps": 25.0, "frames": 50, "breite": 160, "hoehe": 90, "ton": True,
                       "dauer_s": 2.0},
            "schnappschuss": {"quelle": "plan", "gelesen_am": "2026-09-16T12:00:00", "projekt": "P"},
            "umfang": {"bild_schnitte": 3, "ton_schnitte": 2, "mit_transkript": 1, "ohne_transkript": 1,
                       "ohne_liste": ["x.MP4"]},
            "zaehlung": {a: sum(1 for b in befunde if b["art"] == a) for a in ARTEN},
            "befunde": befunde,
            "verteilung": {"diff": {"an_schnitten": {"n": 3, "median": 40.0, "p95": 50.0, "max": 55.0},
                                    "uebrige": {"n": 0}},
                           "knack_verhaeltnis": {"n": 2, "median": 1.2, "p95": 1.9, "max": 2.0}},
            "parameter": {"knack_faktor": 6.0}, "warnungen": ["Bild zu Befund 2: x"]}


def test_bericht_ohne_befunde():
    text = bericht(_erg([]))
    assert text.startswith("# Kantenprüfung — T\n") and "**Keine Befunde.**" in text and "| Nr |" not in text
    assert "Median 40.0" in text and "x.MP4" in text and "Warnung: Bild zu Befund 2: x" in text
    assert "knack_faktor 6.0" in text and text.endswith("\n")


def test_bericht_tabelle_mit_kontext():
    b = {"nr": 1, "art": "Knackser", "frame": 12, "frames": 1, "wert": 9.5, "spitze": 0.3, "versatz_ms": 0.0,
         "kanal": 1, "timecode": "01:00:00:12", "bild": "/p/k.png",
         "kontext": {"bild_schnitt": {"frame": 12, "abstand": 0}, "ton_schnitt": None,
                     "items": [{"spur": "A1", "name": "a|b.MP4"}]}}
    text = bericht(_erg([b]))
    assert "**1 Befund** — Knackser: 1" in text
    zeile = next(z for z in text.splitlines() if z.startswith("| 1 |"))
    assert "01:00:00:12" in zeile and "9.5 ×" in zeile and "a/b.MP4" in zeile and "`/p/k.png`" in zeile
    assert "Bild-Schnitt +0 F" in zeile and "Spitze 0.3" in zeile
