"""telemetrie_bericht.py — Markdown-Bericht: Kopf, Verteilung je Kamera, unruhigste Clips, Fehler,
Vergleich mit dem Index."""
from __future__ import annotations

from niro_autocut import telemetrie_bericht as B

TELE = [
    {"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "ordner": "FX3", "quelle": "rtmd",
     "haltung": "gimbal", "bewegungsart": "fahrt", "brennweitenklasse": "normal", "perspektive_hoehe": "Augenhöhe",
     "wackeln": 0.04, "bewegung": 0.5, "ruhige_fenster": [0.0, 1.0],
     "fenster": [[0.0, 0.04, 0.5, "fahrt"], [1.0, 0.04, 0.5, "fahrt"]], "fehler": None, "roll_grad": 0.4},
    {"path": "/nas/A7/a7_1.MP4", "clip": "a7_1", "kamera": "a7IV", "ordner": "A7iv", "quelle": "rtmd",
     "haltung": "hand", "bewegungsart": "schwenk_links", "brennweitenklasse": "tele", "perspektive_hoehe": "Aufsicht",
     "wackeln": 0.41, "bewegung": 2.0, "ruhige_fenster": [], "fenster": [[0.0, 0.41, 2.0, "schwenk_links"]],
     "fehler": None, "roll_grad": 2.6},
    {"path": "/nas/Mavic/DJI_1.MOV", "clip": "DJI_1", "kamera": "DJI", "ordner": "Mavic", "quelle": "optisch",
     "haltung": "gimbal", "bewegungsart": "fahrt", "brennweitenklasse": None, "perspektive_hoehe": None,
     "wackeln": 0.02, "bewegung": 0.3, "ruhige_fenster": [0.0], "fenster": [[0.0, 0.02, 0.3, "fahrt"]],
     "fehler": None, "roll_grad": None},
    {"path": "/nas/FX3/FX3_2.MP4", "clip": "FX3_2", "kamera": "FX3", "ordner": "FX3", "quelle": "keine",
     "haltung": None, "bewegungsart": None, "brennweitenklasse": None, "perspektive_hoehe": None, "wackeln": None,
     "bewegung": None, "ruhige_fenster": [], "fenster": [], "fehler": "Datei nicht gefunden: /nas/FX3/FX3_2.MP4",
     "roll_grad": None},
]
INDEX = {"clips": [
    {"path": "/nas/FX3/FX3_1.MP4", "kamerabewegung": "Gimbal",
     "abschnitte": [{"von_s": 0, "bis_s": 4, "brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/A7/a7_1.MP4", "kamerabewegung": "Handkamera",
     "abschnitte": [{"von_s": 0, "bis_s": 2, "brennweite": "normal", "perspektive_hoehe": "Aufsicht"},
                    {"von_s": 2, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Augenhöhe"}]},
    {"path": "/nas/Mavic/DJI_1.MOV", "kamerabewegung": "Drohne",
     "abschnitte": [{"von_s": 0, "bis_s": 3, "brennweite": "weit"}]},
]}


def test_bericht_kopf_verteilung_und_unruhigste():
    md = B.bericht_md(TELE, "Kunde A / Projekt B / 2026-09 Dreh")
    assert md.startswith("# Kamera-Telemetrie — Kunde A / Projekt B / 2026-09 Dreh")
    assert "4 Clips" in md and "rtmd 2" in md and "optisch 1" in md and "keine 1" in md and "Fehler 1" in md
    assert "| FX3 |" in md and "| a7IV |" in md and "| DJI |" in md
    assert "## Unruhigste Clips" in md and md.index("a7_1") < md.index("FX3_1")          # nach wackeln absteigend
    assert "0,41" in md and "schief 2,6°" in md
    assert "## Clips ohne Daten oder mit Fehler" in md and "FX3_2" in md and "Datei nicht gefunden" in md
    assert "## Vergleich" not in md


def test_vergleich_index_zaehlt_uebereinstimmung():
    v = B.vergleich_index(TELE, INDEX)
    # FX3 normal=normal, a7 A1 tele≠normal, A2 tele=tele
    assert v["brennweite"]["n"] == 3 and v["brennweite"]["gleich"] == 2
    assert v["perspektive_hoehe"]["n"] == 3 and v["perspektive_hoehe"]["gleich"] == 2
    assert (v["haltung"]["n"] == 3 and v["haltung"]["kreuz"][("gimbal", "Gimbal")] == 1
            and v["haltung"]["kreuz"][("hand", "Handkamera")] == 1)
    md = B.bericht_md(TELE, "T", INDEX)
    assert "## Vergleich mit dem B-Roll-Index" in md and "Brennweite: 2 von 3" in md and "| gimbal | Gimbal | 1 |" in md


def test_bericht_ohne_clips():
    md = B.bericht_md([], "Leer")
    assert "0 Clips" in md and "## Unruhigste Clips" in md


def test_bericht_unschaerfste_fenster_nur_mit_schaerfe():
    assert "## Unschärfste Fenster" not in B.bericht_md(TELE, "T")
    mit = [{**TELE[0], "schaerfe_p10": 0.4, "fenster": [[0.0, 0.04, 0.5, "fahrt", 0.35], [1.0, 0.04, 0.5, "fahrt", 0.9]]}]
    md = B.bericht_md(mit, "T")
    assert "## Unschärfste Fenster" in md and md.index("| FX3_1 | FX3 | 0 | 0,35 |") < md.index("| FX3_1 | FX3 | 1 | 0,90 |")


def test_vergleich_index_nutzt_claudes_originalwerte():
    """I2: nach Stufe 2b stehen in brennweite/perspektive_hoehe die Telemetrie-Werte — verglichen wird gegen Claudes
    Originalwerte in ``claude``; fehlen sie (Altbestand) und stammt das Feld laut felder_quelle aus der Telemetrie,
    wird der Abschnitt für dieses Feld übersprungen (kein Selbstvergleich)."""
    index = {"clips": [
        {"path": "/nas/A7/a7_1.MP4", "kamerabewegung": "Handkamera",
         "felder_quelle": {"brennweite": "rtmd", "perspektive_hoehe": "rtmd"},
         "abschnitte": [{"von_s": 0, "bis_s": 2, "brennweite": "tele", "perspektive_hoehe": "Aufsicht",
                         "claude": {"brennweite": "normal", "perspektive_hoehe": "Augenhöhe"}},
                        {"von_s": 2, "bis_s": 4, "brennweite": "tele", "perspektive_hoehe": "Aufsicht"}]}]}
    v = B.vergleich_index(TELE, index)
    assert v["brennweite"]["n"] == 1 and v["brennweite"]["gleich"] == 0
    assert v["brennweite"]["kreuz"][("tele", "normal")] == 1
    assert v["perspektive_hoehe"]["n"] == 1 and v["perspektive_hoehe"]["kreuz"][("Aufsicht", "Augenhöhe")] == 1
