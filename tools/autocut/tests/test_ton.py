"""Tests für ton.py — ffmpeg-Parser, Gain-Formel, Cache, ton.json."""
from __future__ import annotations

import json
import math

import pytest

from niro_autocut.timeline_model import Item
from niro_autocut import ton as T

CFG = {"ziel_dbtp": -3.0, "max_gain_db": 30.0, "clip_warn_dbtp": -0.5, "silence_dbtp": -60.0}
FFMPEG_TAIL = """[Parsed_ebur128_0 @ 0x1] Summary:

  Integrated loudness:
    I:         -24.3 LUFS
    Threshold: -34.5 LUFS

  Loudness range:
    LRA:         6.1 LU
    Threshold: -44.6 LUFS
    LRA low:   -28.0 LUFS
    LRA high:  -21.9 LUFS

  True peak:
    Peak:      -15.2 dBFS
"""


def test_parse_true_peak_reads_summary_and_returns_none_without_it():
    assert T.parse_true_peak(FFMPEG_TAIL) == -15.2
    assert T.parse_true_peak("kein ebur128 hier") is None
    assert T.parse_true_peak(FFMPEG_TAIL.replace("-15.2 dBFS", "-inf dBFS")) == -math.inf


def test_gain_formula_limits_and_warnings():
    assert T.gain_db_for(-15.2, CFG) == (12.2, "")
    g, w = T.gain_db_for(-40.0, CFG)
    assert g == 30.0 and "30" in w
    g, w = T.gain_db_for(-0.2, CFG)
    assert g == -2.8 and "Clipping" in w
    g, w = T.gain_db_for(-70.0, CFG)
    assert g == 0.0 and "Stille" in w
    assert round(T.db_to_lin(6.0206), 3) == 2.0 and round(T.lin_to_db(2.0), 2) == 6.02


def test_measure_a1_items_uses_cache_and_only_a1(tmp_path):
    items = [Item("V1", "/nas/FX3_1.MP4", 250, 300, 0, 50), Item("A1", "/nas/FX3_1.MP4", 250, 300, 0, 50),
             Item("A1", "/nas/FX3_2.MP4", 0, 25, 60, 85)]
    calls = []

    def fake_measure(path, in_s, dur_s):
        calls.append((path, in_s, dur_s))
        return -15.2
    cache = {"/nas/FX3_1.MP4|250|300": {"tpk_dbfs": -9.0}}
    out = T.measure_a1_items(items, 25.0, CFG, cache, measure=fake_measure)
    assert [e["name"] for e in out] == ["FX3_1.MP4", "FX3_2.MP4"]
    assert out[0]["tpk_dbfs"] == -9.0 and out[0]["gain_db"] == 6.0 and round(out[0]["gain_lin"], 3) == 1.995
    assert calls == [("/nas/FX3_2.MP4", 0.0, 1.0)] and out[1]["gain_db"] == 12.2
    assert cache["/nas/FX3_2.MP4|0|25"]["tpk_dbfs"] == -15.2


def test_build_ton_writes_json(charge_dir):
    from niro_autocut.charge import Charge
    ch = Charge.open(charge_dir)
    tp = {"fps": 25, "items": [Item("A1", "/nas/FX3_1.MP4", 250, 300, 0, 50).to_dict()]}
    out = T.build_ton(ch, tp, CFG, measure=lambda p, i, d: -20.0)
    assert out["ziel_dbtp"] == -3.0 and out["items"][0]["gain_db"] == 17.0
    assert json.loads((ch.autocut / "ton.json").read_text())["items"][0]["gain_lin"] == out["items"][0]["gain_lin"]
    assert (ch.work / "ton_cache.json").exists()


def test_build_ton_persists_cache_when_measure_raises_mid_batch(charge_dir):
    """Finding 1: Cache-Verlust bei Abbruch mitten in der Messschleife — erste Messung darf nicht verloren gehen."""
    from niro_autocut.charge import AutoCutError, Charge
    ch = Charge.open(charge_dir)
    tp = {"fps": 25, "items": [
        Item("A1", "/nas/FX3_1.MP4", 250, 300, 0, 50).to_dict(),
        Item("A1", "/nas/FX3_2.MP4", 0, 25, 60, 85).to_dict(),
    ]}
    calls: list[str] = []

    def flaky_measure(path, in_s, dur_s):
        calls.append(path)
        if len(calls) == 1:
            return -15.0
        raise AutoCutError("NAS nicht erreichbar")

    with pytest.raises(AutoCutError):
        T.build_ton(ch, tp, CFG, measure=flaky_measure)

    cache = json.loads((ch.work / "ton_cache.json").read_text())
    assert cache["/nas/FX3_1.MP4|250|300"]["tpk_dbfs"] == -15.0
    assert "/nas/FX3_2.MP4|0|25" not in cache


def test_build_ton_normalizes_non_finite_true_peak_for_json(charge_dir):
    """Finding 2: -inf True Peak darf nicht als -Infinity ins JSON gelangen."""
    from niro_autocut.charge import Charge
    ch = Charge.open(charge_dir)
    tp = {"fps": 25, "items": [Item("A1", "/nas/FX3_1.MP4", 0, 25, 0, 25).to_dict()]}
    out = T.build_ton(ch, tp, CFG, measure=lambda p, i, d: -math.inf)
    entry = out["items"][0]
    assert entry["tpk_dbfs"] == -120.0
    assert entry["gain_db"] == 0.0
    assert "Stille" in entry["warnung"]
    json.dumps(out, allow_nan=False)  # darf nicht scheitern (kein -Infinity/NaN mehr im Baum)
    cache = json.loads((ch.work / "ton_cache.json").read_text())
    assert cache["/nas/FX3_1.MP4|0|25"]["tpk_dbfs"] == -120.0


def test_measure_a1_items_measures_mapped_path_but_keys_original():
    from niro_autocut.ton import measure_a1_items
    seen = []

    def fake_measure(path, in_s, dur_s):
        seen.append(path)
        return -12.0

    items = [Item("A1", "/Volumes/NAS/proj/FX3_0001.MP4", 25, 125, 0, 100, True, "1")]
    cache: dict = {}
    cfg = {"ziel_dbtp": -3.0, "max_gain_db": 30.0, "clip_warn_dbtp": -0.5, "silence_dbtp": -60.0}
    out = measure_a1_items(items, 25.0, cfg, cache, fake_measure, map_path=lambda p: p.replace("/Volumes/NAS/", "/Volumes/SSD/"))
    assert seen == ["/Volumes/SSD/proj/FX3_0001.MP4"]
    assert out[0]["clip"] == "/Volumes/NAS/proj/FX3_0001.MP4" and list(cache) == ["/Volumes/NAS/proj/FX3_0001.MP4|25|125"]
