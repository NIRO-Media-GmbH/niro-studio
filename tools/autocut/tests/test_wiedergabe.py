"""wiedergabe.py: Vollbild-Wiedergabe aus der Fensterliste von fenster.swift erkennen."""
from __future__ import annotations

from niro_autocut import wiedergabe as W

HAUPT = "101\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920x1080\tTaxodia 09.26\n"
VIEWER = "102\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920x1080\t\n"


def test_status_unklar_ohne_ausgabe_oder_namen():
    assert W.status(None) == "unklar" and W.status("") == "unklar"
    assert W.status("7\tFinder\tlayer=0\tonscreen=true\t1920x1080\tDesktop\n") == "unklar"
    assert W.status(VIEWER) == "unklar"          # alle Resolve-Namen leer → kein Bildschirmaufnahme-Recht


def test_status_ruhig_und_spielt_ab():
    assert W.status(HAUPT) == "ruhig"
    assert W.status(HAUPT + "103\tDaVinci Resolve\tlayer=3\tonscreen=true\t320x200\t\n") == "ruhig"
    assert W.status(HAUPT + "104\tDaVinci Resolve\tlayer=0\tonscreen=false\t1920x1080\t\n") == "ruhig"
    assert W.status(HAUPT + VIEWER) == "spielt_ab"
    assert W.status(HAUPT + "105\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920.0x1080.0\t\n") == "spielt_ab"


def test_fenster_ausgabe_ohne_swift(monkeypatch):
    monkeypatch.setattr(W.shutil, "which", lambda name: None)
    assert W.fenster_ausgabe() is None


def test_fenster_swift_liegt_im_tool():
    assert W.FENSTER_SWIFT.is_file()
    assert "CGWindowListCopyWindowInfo" in W.FENSTER_SWIFT.read_text(encoding="utf-8")
