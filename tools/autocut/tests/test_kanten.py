"""Kantenprüfung (Spec 2026-09-16): Schnappschuss, Schnitte, Maske, Timecode, Befund-Regeln, Wortkanten — ohne ffmpeg."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pytest
import yaml

from niro_autocut import kanten as K
from niro_autocut.charge import DEFAULTS_FILE, AutoCutError, Charge

TL = {"name": "T", "start_frame": 90000, "end_frame": 90100, "start_timecode": "01:00:00:00", "fps": "25",
      "tracks": {
          "V1": {"name": "FX3", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": 100.0},
              {"name": "b.MP4", "file": "/x/b.MP4", "start": 90040, "end": 90100, "duration": 60, "src_in": 0,
               "src_out": 60, "enabled": False, "left_offset": 0, "speed": 50.0}]},
          "A1": {"name": "Ton", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": None},
              {"name": "c.MP4", "file": "/x/c.MP4", "start": 90050, "end": 90090, "duration": 40, "src_in": 5,
               "src_out": 45, "enabled": True, "left_offset": None, "speed": None}]}},
      "markers": {}, "n_items": 4}


@pytest.fixture
def cfg() -> dict:
    return yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["kanten"]


def _snap() -> dict:
    return K.snapshot_from_readback(TL, "P", gelesen_am="2026-09-16T12:00:00")


def test_snapshot_relative_frames_left_offset_and_flags():
    s = _snap()
    assert (s["timeline"], s["projekt"], s["fps"], s["laenge"], s["start_timecode"]) == ("T", "P", 25.0, 100, "01:00:00:00")
    assert s["spuren"]["V1"][0] == {"name": "a.MP4", "datei": "/x/a.MP4", "start": 0, "dauer": 40, "quell_in": 100,
                                    "aktiv": True, "tempo": 100.0}
    assert s["spuren"]["V1"][1]["aktiv"] is False and s["spuren"]["V1"][1]["tempo"] == 50.0
    assert s["spuren"]["A1"][1]["quell_in"] is None and s["spuren"]["A1"][1]["start"] == 50
    assert s["quelle"] == "resolve" and s["gelesen_am"] == "2026-09-16T12:00:00"


def test_snapshot_rejects_missing_end_or_fps():
    with pytest.raises(AutoCutError, match="kein Ende"):
        K.snapshot_from_readback({**TL, "end_frame": None}, "P")
    with pytest.raises(AutoCutError, match="Bildrate"):
        K.snapshot_from_readback({**TL, "fps": None}, "P")


def test_schnitte_skip_inactive_items_and_timeline_edges():
    s = _snap()
    assert K.schnitte(s, "bild") == [40]
    assert K.schnitte(s, "ton") == [40, 50, 90]


def test_ton_maske_excludes_item_edges():
    m = K.ton_maske(_snap())
    assert m.shape == (100,)
    assert not m[0] and m[1] and m[38] and not m[39] and not m[45]
    assert not m[50] and m[51] and m[88] and not m[89]


def test_timecode_and_back():
    assert K.timecode(0, 25) == "01:00:00:00"
    assert K.timecode(25 * 61 + 7, 25) == "01:01:01:07"
    assert K.tc_to_frame("01:01:01:07", 25) == 1532
    assert K.timecode(3, 50, "00:59:59:48") == "01:00:00:01"
    with pytest.raises(AutoCutError, match="Timecode"):
        K.tc_to_frame("1:2", 25)


def test_kontext_nearest_cuts_and_items():
    s = _snap()
    k = K.kontext(s, 42, K.schnitte(s, "bild"), K.schnitte(s, "ton"))
    assert k["bild_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["ton_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["items"] == []
    assert K.kontext(s, 10, [], [])["items"] == [{"spur": "A1", "name": "a.MP4"}, {"spur": "V1", "name": "a.MP4"}]
    assert K.kontext(s, 10, [], [])["bild_schnitt"] is None
