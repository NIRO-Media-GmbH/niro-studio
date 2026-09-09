from __future__ import annotations

from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError, Charge, append_protokoll, load_config


def test_open_creates_autocut_dirs(charge_dir):
    ch = Charge.open(charge_dir)
    assert ch.autocut == charge_dir / "_intern" / "autocut"
    assert ch.autocut.is_dir() and ch.work.is_dir() and ch.ergebnisse.is_dir()


def test_open_fails_without_plaene(tmp_path):
    with pytest.raises(AutoCutError, match="O-Ton-Pläne"):
        Charge.open(tmp_path / "leer")


def test_config_merges_charge_override(charge_dir):
    (charge_dir / "_intern" / "autocut").mkdir(parents=True, exist_ok=True)
    (charge_dir / "_intern" / "autocut" / "config.yaml").write_text(
        "pause_s: 2.0\nsync:\n  min_confidence: 9\n", encoding="utf-8")
    cfg = load_config(charge_dir)
    assert cfg["pause_s"] == 2.0
    assert cfg["sync"]["min_confidence"] == 9
    assert cfg["sync"]["sr"] == 16000  # Default bleibt


def test_resolve_plan_single(charge_dir):
    ch = Charge.open(charge_dir)
    assert ch.resolve_plan(None).name == "video-1-test.md"


def test_resolve_plan_ambiguous_lists_options(charge_dir):
    (charge_dir / "Ergebnisse" / "O-Ton-Pläne" / "video-2-x.md").write_text("#", encoding="utf-8")
    ch = Charge.open(charge_dir)
    with pytest.raises(AutoCutError, match="video-2-x.md"):
        ch.resolve_plan(None)
    assert ch.resolve_plan("video-2-x.md").name == "video-2-x.md"


def test_cache_transcript_and_index(charge_dir):
    ch = Charge.open(charge_dir)
    assert ch.load_index()[0]["name"] == "FX3_0001.MP4"
    assert ch.cache_transcript("abc123")["words"][0]["text"] == "Das"
    assert ch.cache_transcript("fehlt") is None


def test_assert_writable_blocks_nas_and_foreign(charge_dir, tmp_path):
    ch = Charge.open(charge_dir)
    ch.assert_writable(ch.autocut / "x.json")
    ch.assert_writable(ch.ergebnisse / "r.md")
    with pytest.raises(AutoCutError):
        ch.assert_writable(Path("/Volumes/NIRO NAS/x"))
    with pytest.raises(AutoCutError):
        ch.assert_writable(charge_dir / "Material" / "x")


def test_append_protokoll_creates_and_appends(charge_dir):
    ch = Charge.open(charge_dir)
    append_protokoll(ch, "Rohschnitt gebaut", ["Timeline X", "3 Warnungen"])
    text = ch.protokoll.read_text(encoding="utf-8")
    assert "AutoCut" in text and "Timeline X" in text
    append_protokoll(ch, "Zweiter Lauf", ["ok"])
    assert text in ch.protokoll.read_text(encoding="utf-8")


from niro_autocut.charge import map_path


def test_map_path_longest_prefix_and_folder_boundary():
    pm = {"/Volumes/NAS/a": "/Volumes/SSD/a", "/Volumes/NAS/a/tief": "/Volumes/X/tief", "/Volumes/NAS": "/Volumes/Y"}
    assert map_path("/Volumes/NAS/a/tief/clip.mp4", pm) == "/Volumes/X/tief/clip.mp4"
    assert map_path("/Volumes/NAS/a/clip.mp4", pm) == "/Volumes/SSD/a/clip.mp4"
    assert map_path("/Volumes/NAS/ab/clip.mp4", pm) == "/Volumes/Y/ab/clip.mp4"        # „a" passt nicht auf „ab"
    assert map_path("/Volumes/NAS/a", pm) == "/Volumes/SSD/a"                          # exakt der Präfix selbst
    assert map_path("/anders/clip.mp4", pm) == "/anders/clip.mp4"
    assert map_path("/anders/clip.mp4", None) == "/anders/clip.mp4"
    assert map_path("/Volumes/NAS/a/", {"/Volumes/NAS/a/": "/Volumes/SSD/a/"}) == "/Volumes/SSD/a/"   # Schrägstrich am Ende egal


def test_map_path_is_unicode_normalization_agnostic():
    nfd = "/Volumes/NAS/Kliniken GmbH/März/clip.mp4"       # „ä" als a + Kombinationszeichen
    nfc = "/Volumes/NAS/Kliniken GmbH/März"
    assert map_path(nfd, {nfc: "/Volumes/SSD/März"}) == "/Volumes/SSD/März/clip.mp4"


def test_charge_map_path_uses_config(charge_dir):
    (charge_dir / "_intern" / "autocut").mkdir(parents=True, exist_ok=True)
    (charge_dir / "_intern" / "autocut" / "config.yaml").write_text('path_map:\n  "/Volumes/NAS/p": "/Volumes/SSD/p"\n', encoding="utf-8")
    ch = Charge.open(charge_dir)
    assert ch.map_path("/Volumes/NAS/p/x.mp4") == "/Volumes/SSD/p/x.mp4"
    assert ch.map_path("/woanders/x.mp4") == "/woanders/x.mp4"


def test_charge_map_path_rejects_invalid_path_map(charge_dir):
    """Minor 4: ein kaputtes path_map (YAML-Tippfehler, falscher Werttyp) muss eine deutsche AutoCutError
    auslösen statt eines rohen Python-Tracebacks (AttributeError: 'str' object has no attribute 'items')."""
    ch = Charge.open(charge_dir)
    ch.config["path_map"] = "kaputt"
    with pytest.raises(AutoCutError, match="path_map"):
        ch.map_path("/x/y.mp4")

    ch.config["path_map"] = {"/a": 123}
    with pytest.raises(AutoCutError, match="path_map"):
        ch.map_path("/a/y.mp4")

    ch.config["path_map"] = {"/a": None}                                 # YAML `"/a":` ohne Wert → sonst „None/y.mp4“
    with pytest.raises(AutoCutError, match="path_map"):
        ch.map_path("/a/y.mp4")

    ch.config["path_map"] = {"/a": "/b"}
    assert ch.map_path("/a/y.mp4") == "/b/y.mp4"                    # gültiges path_map bleibt unangetastet
