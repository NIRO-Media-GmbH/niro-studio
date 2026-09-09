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
