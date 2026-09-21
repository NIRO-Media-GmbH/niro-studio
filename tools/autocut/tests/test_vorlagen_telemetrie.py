"""6d-Vorlage: kompiliert, nutzt stabil_vorschlag, dokumentiert die 7. BROLL-Spalte, Stabilize nur für ausgewählte Shots."""
from __future__ import annotations

import importlib.util
import py_compile
from pathlib import Path

import pytest

VORLAGE = Path(__file__).resolve().parents[1] / "vorlagen" / "feinschnitt" / "feinschnitt_bauen.py"
README = VORLAGE.parents[1] / "README.md"


def test_vorlage_kompiliert_und_nutzt_telemetrie():
    py_compile.compile(str(VORLAGE), doraise=True)
    text = VORLAGE.read_text(encoding="utf-8")
    assert "from niro_autocut import telemetrie as TM" in text
    assert "TM.stabil_vorschlag(" in text and "TM.finden(" in text and "TM.laden(" in text
    assert "TM.genutzter_quellbereich_s(" in text             # Quellbereich korrekt skaliert (Fix-Runde 1)
    assert "stabil_hand" in text and '"stabil_grund"' in text
    assert 'if not m["stabil"]' in text                      # Stabilize() nur für ausgewählte Shots


def test_readme_nennt_die_spalte():
    assert "stabil" in README.read_text(encoding="utf-8") and "telemetrie.json" in README.read_text(encoding="utf-8")


# --- Final Review (21.09.2026): Spalte 7 True bei _stabilized-Datei stoppt den Bau (I4) -----------------------------------

def test_vorlage_prueft_spalte_7_true_bei_stabilized():
    """I4: User-Regel — Avata nur als …_stabilized, nie der Resolve-Stabilizer; die Vorlage meldet das als Plan-Fehler."""
    text = VORLAGE.read_text(encoding="utf-8")
    assert "Spalte 7 True bei _stabilized-Datei — Avata nie in Resolve stabilisieren" in text
    assert '"_stabilized" in' in text


def _vorlage_laden(monkeypatch):
    """Vorlage als Modul laden; ihr Import setzt RA.TRACK_INDEX["A3"] — auf einer Kopie, damit nichts in andere Tests
    wandert."""
    from niro_autocut import resolve_api as RA
    monkeypatch.setattr(RA, "TRACK_INDEX", dict(RA.TRACK_INDEX))
    spec = importlib.util.spec_from_file_location("feinschnitt_bauen_vorlage", VORLAGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("datei,spalte7,fehler_erwartet", [
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (True,), True),
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (), False),        # Vorschlag: nie stabilisieren
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (False,), False),
    ("/ssd/FX3/FX3_0001.MP4", (True,), False),                   # Handkamera-Datei darf erzwungen werden
])
def test_plan_stoppt_bei_spalte_7_true_und_stabilized(monkeypatch, datei, spalte7, fehler_erwartet):
    fb = _vorlage_laden(monkeypatch)
    monkeypatch.setattr(fb, "anpassen_pruefen", lambda fuer_bau=False: None)
    monkeypatch.setattr(fb, "ENDE", 100)
    monkeypatch.setattr(fb, "alpha_min", lambda: [255] * 100)
    monkeypatch.setattr(fb, "v4_stuecke", lambda fehler: [])
    monkeypatch.setattr(fb, "BROLL", [(1, 0, 40, 0, "1", False, *spalte7)])
    shots = {1: {"nr": 1, "clip": Path(datei).stem, "datei": datei, "clip_fps": 25.0, "left_offset_f": 0, "dauer_f": 100}}
    p, fehler = fb.plan({"items": []}, shots)
    treffer = [f for f in fehler if "Spalte 7 True bei _stabilized-Datei" in f]
    assert bool(treffer) is fehler_erwartet
    if fehler_erwartet:
        assert treffer == ["S01: Spalte 7 True bei _stabilized-Datei — Avata nie in Resolve stabilisieren"]
