"""6d-Vorlage: kompiliert, nutzt stabil_vorschlag, dokumentiert die 7. BROLL-Spalte, Stabilize nur für ausgewählte Shots."""
from __future__ import annotations

import py_compile
from pathlib import Path

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
