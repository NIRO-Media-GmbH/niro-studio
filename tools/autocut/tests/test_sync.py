"""Tests für sync.py — Onset-Hüllkurve, Kreuzkorrelation, Vorzeichen, Prüffenster, Paar-Auswahl.

Konvention (Plan „Global Constraints“): other_time = ref_time + offset_s, d. h. ein positiver
Versatz heißt „die a7 lief schon, als die FX3 startete“.
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from scipy.io import wavfile

from niro_autocut import sync as S
from niro_autocut.charge import AutoCutError, Charge

SR = 16000
CFG = {"sr": SR, "hop_s": 0.005, "win_s": 0.02, "min_confidence": 4.0, "max_drift_frames": 1.0, "exclusion_s": 1.0}


def _speech_like(seconds: float, seed: int) -> np.ndarray:
    """Silben-artige Rausch-Bursts mit zufälligen Pausen — sprachähnliche Hüllkurve ohne Periodizität."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    env = np.zeros(n)
    t = 0
    while t < n:
        dur = int(rng.integers(int(0.05 * SR), int(0.3 * SR)))
        gap = int(rng.integers(int(0.02 * SR), int(0.4 * SR)))
        env[t:t + dur] = rng.uniform(0.2, 1.0)
        t += dur + gap
    return env * rng.normal(0, 0.3, n)


def _write(path, x: np.ndarray) -> None:
    wavfile.write(path, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


# --- Hüllkurve -----------------------------------------------------------

def test_onset_envelope_shape_and_rate():
    x = _speech_like(10, 3)
    env, fs = S.onset_envelope(x, SR, 0.005, 0.02)
    assert fs == pytest.approx(200.0)
    assert env.dtype == np.float32
    # ~10 s bei 5 ms Hop → knapp 2000 Werte; zentriert
    assert 1900 <= len(env) <= 2000
    assert abs(float(env.mean())) < 1e-3
    assert float(env.max()) > 0.0


def test_onset_envelope_rejects_too_short():
    with pytest.raises(AutoCutError, match="zu kurz"):
        S.onset_envelope(np.zeros(100), SR, 0.005, 0.02)


# --- Vorzeichen und Genauigkeit -------------------------------------------

def test_offset_sign_and_precision():
    ref = _speech_like(60, 1)
    lead = 1.95                          # a7 startet 1.95 s FRÜHER → a7_zeit = fx3_zeit + 1.95
    other = np.concatenate([np.random.default_rng(2).normal(0, 0.05, int(lead * SR)),
                            ref * 0.4 + np.random.default_rng(3).normal(0, 0.1, len(ref))])
    e1, fs = S.onset_envelope(ref, SR, CFG["hop_s"], CFG["win_s"])
    e2, _ = S.onset_envelope(other, SR, CFG["hop_s"], CFG["win_s"])
    off, conf = S.estimate_offset(e1, e2, fs, CFG["exclusion_s"])
    assert abs(off - lead) < 0.02 and conf > 4


def test_negative_offset_partial_overlap():
    ref = _speech_like(90, 5)
    other = ref[int(30 * SR):] * 0.5     # a7 beginnt 30 s NACH der FX3 → offset −30
    e1, fs = S.onset_envelope(ref, SR, 0.005, 0.02)
    e2, _ = S.onset_envelope(other, SR, 0.005, 0.02)
    off, conf = S.estimate_offset(e1, e2, fs, 1.0)
    assert abs(off + 30.0) < 0.02


def test_window_offset_corrects_for_window_start():
    """Ein Prüffenster, das bei ref-Sekunde a beginnt, muss denselben Versatz liefern wie das Gesamtsignal
    (der Prototyp hatte hier einen Vorzeichenfehler — Fensterstart wird ABGEZOGEN)."""
    ref = _speech_like(60, 21)
    lead = 2.0
    other = np.concatenate([np.zeros(int(lead * SR)), ref * 0.5])
    e1, fs = S.onset_envelope(ref, SR, 0.005, 0.02)
    e2, _ = S.onset_envelope(other, SR, 0.005, 0.02)
    off_full, _ = S.estimate_offset(e1, e2, fs, 1.0)
    off_w1, c1 = S.window_offset(e1, e2, fs, 0.0, 30.0, 1.0)
    off_w2, c2 = S.window_offset(e1, e2, fs, 30.0, 60.0, 1.0)
    assert abs(off_full - lead) < 0.02
    assert abs(off_w1 - lead) < 0.02 and abs(off_w2 - lead) < 0.02
    assert c1 > 4 and c2 > 4


def test_window_offset_negative_offset_late_window():
    ref = _speech_like(90, 22)
    other = ref[int(30 * SR):] * 0.5     # offset −30; Überlappung in ref-Zeit 30–90
    e1, fs = S.onset_envelope(ref, SR, 0.005, 0.02)
    e2, _ = S.onset_envelope(other, SR, 0.005, 0.02)
    off_w, _ = S.window_offset(e1, e2, fs, 60.0, 90.0, 1.0)
    assert abs(off_w + 30.0) < 0.02


# --- WAV lesen -------------------------------------------------------------

def test_read_wav_mono_int16_and_stereo(tmp_path):
    x = _speech_like(2, 8)
    _write(tmp_path / "m.wav", x)
    y, sr = S.read_wav_mono(tmp_path / "m.wav")
    assert sr == SR and y.dtype == np.float32 and float(np.abs(y).max()) <= 1.0
    xc = np.clip(x, -1, 1)                       # wie _write: kein int16-Überlauf
    stereo = np.stack([xc, xc * 0.5], axis=1)
    wavfile.write(tmp_path / "s.wav", SR, (stereo * 32767).astype(np.int16))
    z, _ = S.read_wav_mono(tmp_path / "s.wav")
    assert z.ndim == 1 and len(z) == len(x) and z.dtype == np.float32
    # Stereo muss ebenfalls auf [-1, 1] normiert sein (Kanalmittel, nicht Rohwerte ±32767)
    assert float(np.abs(z).max()) <= 1.0
    assert np.allclose(z, 0.75 * xc, atol=2e-3)


# --- Paar-Sync -------------------------------------------------------------

def test_sync_pair_writes_frames_overlap_and_drift(tmp_path):
    ref = _speech_like(60, 7)
    other = np.concatenate([np.zeros(int(2.0 * SR)), ref * 0.5])
    _write(tmp_path / "ref.wav", ref)
    _write(tmp_path / "oth.wav", other)
    p = S.sync_pair(tmp_path / "ref.wav", tmp_path / "oth.wav", 25.0, CFG)
    assert p.ok and p.offset_frames == 50 and abs(p.drift_frames) <= 1.0
    assert p.overlap_ref[0] == 0.0 and abs(p.overlap_ref[1] - 60.0) < 0.2
    assert p.note == ""
    d = p.to_dict()
    assert set(d) == {"ref", "other", "offset_s", "offset_frames", "confidence", "overlap_ref", "drift_frames", "ok", "note"}
    assert d["ref"].endswith("ref.wav")


def test_sync_pair_negative_offset_overlap_window(tmp_path):
    ref = _speech_like(90, 9)
    other = ref[int(30 * SR):] * 0.5
    _write(tmp_path / "ref.wav", ref)
    _write(tmp_path / "oth.wav", other)
    p = S.sync_pair(tmp_path / "ref.wav", tmp_path / "oth.wav", 25.0, CFG)
    assert p.ok and p.offset_frames == -750
    assert abs(p.overlap_ref[0] - 30.0) < 0.2 and abs(p.overlap_ref[1] - 90.0) < 0.2


def test_unrelated_signals_not_ok(tmp_path):
    a = _speech_like(40, 11)
    b = _speech_like(40, 12)
    _write(tmp_path / "a.wav", a)
    _write(tmp_path / "b.wav", b)
    p = S.sync_pair(tmp_path / "a.wav", tmp_path / "b.wav", 25.0, CFG)
    assert not p.ok and p.note != ""


def test_sync_pair_large_positive_offset_full_ref_coverage(tmp_path):
    ref = _speech_like(30, 13)
    other = np.concatenate([np.zeros(int(40 * SR)), ref * 0.5])   # a7 hat 40 s Vorlauf, ref nur 30 s lang
    _write(tmp_path / "ref.wav", ref)
    _write(tmp_path / "oth.wav", other)
    p = S.sync_pair(tmp_path / "ref.wav", tmp_path / "oth.wav", 25.0, CFG)
    assert p.offset_frames == 1000 and p.ok
    assert p.overlap_ref[0] == 0.0 and abs(p.overlap_ref[1] - 30.0) < 0.2


def test_sync_pair_rejects_different_samplerates(tmp_path):
    x = _speech_like(10, 15)
    wavfile.write(tmp_path / "a.wav", SR, (x * 32767).astype(np.int16))
    wavfile.write(tmp_path / "b.wav", 8000, (x[::2] * 32767).astype(np.int16))
    with pytest.raises(AutoCutError, match="Abtastrate"):
        S.sync_pair(tmp_path / "a.wav", tmp_path / "b.wav", 25.0, CFG)


# --- Charge ----------------------------------------------------------------

def test_sync_charge_writes_sync_json(charge_dir, tmp_path, monkeypatch):
    ch = Charge.open(charge_dir)
    ref = _speech_like(40, 31)
    other = np.concatenate([np.zeros(int(1.0 * SR)), ref * 0.5])
    wavs = {"/nas/Interviews/Anna/FX3_0001.MP4": tmp_path / "fx3.wav",
            "/nas/Interviews/Anna/a7MK4_0001.MP4": tmp_path / "a7.wav"}
    _write(wavs["/nas/Interviews/Anna/FX3_0001.MP4"], ref)
    _write(wavs["/nas/Interviews/Anna/a7MK4_0001.MP4"], other)
    # Audio-Extraktion durch die fertigen Test-WAVs ersetzen (kein ffmpeg, kein NAS)
    monkeypatch.setattr(S, "extract_audio_16k", lambda src, out_dir, sr=16000: wavs[str(src)])
    media = {"format": {"fps": 25.0, "width": 3840, "height": 2160, "orientation": "16:9"},
             "clips": {}, "ordner": {"Anna": {"ton": ["/nas/Interviews/Anna/FX3_0001.MP4"],
                                              "kontext": ["/nas/Interviews/Anna/a7MK4_0001.MP4"]}}}
    out = S.sync_charge(ch, media)
    assert out["fps"] == 25.0 and len(out["paare"]) == 1
    p = out["paare"][0]
    assert p["ref"] == "/nas/Interviews/Anna/FX3_0001.MP4" and p["other"] == "/nas/Interviews/Anna/a7MK4_0001.MP4"
    assert p["ok"] and p["offset_frames"] == 25
    on_disk = json.loads((ch.autocut / "sync.json").read_text(encoding="utf-8"))
    assert on_disk == out


def test_sync_charge_keeps_other_folders_when_filtered(charge_dir, tmp_path, monkeypatch):
    ch = Charge.open(charge_dir)
    ref = _speech_like(30, 41)
    wavs = {"/nas/Interviews/Bea/FX3_0002.MP4": tmp_path / "fx3.wav",
            "/nas/Interviews/Bea/a7MK4_0002.MP4": tmp_path / "a7.wav"}
    _write(wavs["/nas/Interviews/Bea/FX3_0002.MP4"], ref)
    _write(wavs["/nas/Interviews/Bea/a7MK4_0002.MP4"], np.concatenate([np.zeros(int(0.6 * SR)), ref * 0.5]))
    monkeypatch.setattr(S, "extract_audio_16k", lambda src, out_dir, sr=16000: wavs[str(src)])
    alt = {"ref": "/nas/Interviews/Anna/FX3_0001.MP4", "other": "/nas/Interviews/Anna/a7MK4_0001.MP4",
           "offset_s": 1.0, "offset_frames": 25, "confidence": 9.0, "overlap_ref": [0.0, 40.0],
           "drift_frames": 0.0, "ok": True, "note": ""}
    ch.write_json("sync.json", {"fps": 25.0, "paare": [alt]})
    media = {"format": {"fps": 25.0}, "clips": {},
             "ordner": {"Anna": {"ton": ["/nas/Interviews/Anna/FX3_0001.MP4"], "kontext": ["/nas/Interviews/Anna/a7MK4_0001.MP4"]},
                        "Bea": {"ton": ["/nas/Interviews/Bea/FX3_0002.MP4"], "kontext": ["/nas/Interviews/Bea/a7MK4_0002.MP4"]}}}
    out = S.sync_charge(ch, media, nur_ordner=["Bea"])
    refs = {p["ref"] for p in out["paare"]}
    assert refs == {"/nas/Interviews/Anna/FX3_0001.MP4", "/nas/Interviews/Bea/FX3_0002.MP4"}
    bea = next(p for p in out["paare"] if p["ref"].endswith("FX3_0002.MP4"))
    assert bea["ok"] and bea["offset_frames"] == 15


def test_sync_charge_pair_error_becomes_not_ok(charge_dir, tmp_path, monkeypatch):
    ch = Charge.open(charge_dir)
    wavs = {"/nas/Interviews/Cem/FX3_0003.MP4": tmp_path / "fx3.wav",
            "/nas/Interviews/Cem/a7MK4_0003.MP4": tmp_path / "a7.wav"}
    _write(wavs["/nas/Interviews/Cem/FX3_0003.MP4"], _speech_like(20, 51))
    _write(wavs["/nas/Interviews/Cem/a7MK4_0003.MP4"], np.zeros(50))      # viel zu kurz
    monkeypatch.setattr(S, "extract_audio_16k", lambda src, out_dir, sr=16000: wavs[str(src)])
    media = {"format": {"fps": 25.0}, "clips": {},
             "ordner": {"Cem": {"ton": ["/nas/Interviews/Cem/FX3_0003.MP4"], "kontext": ["/nas/Interviews/Cem/a7MK4_0003.MP4"]}}}
    out = S.sync_charge(ch, media)
    assert len(out["paare"]) == 1 and not out["paare"][0]["ok"] and "zu kurz" in out["paare"][0]["note"]


# --- Paar-Auswahl für einen Schnitt ---------------------------------------

def test_a7_for_cut_coverage():
    sync = {"fps": 25, "paare": [{"ref": "/fx3", "other": "/a7", "offset_s": 1.95, "offset_frames": 49, "confidence": 12,
                                  "overlap_ref": [0.0, 300.0], "drift_frames": 0.1, "ok": True, "note": ""}]}
    assert S.a7_for_cut(sync, "/fx3", 10, 20)["other"] == "/a7"
    assert S.a7_for_cut(sync, "/fx3", 290, 310) is None
    assert S.a7_for_cut(sync, "/anderer", 10, 20) is None


def test_a7_for_cut_prefers_confidence_and_skips_not_ok():
    base = {"ref": "/fx3", "offset_s": 1.0, "offset_frames": 25, "drift_frames": 0.0, "note": ""}
    sync = {"fps": 25, "paare": [
        dict(base, other="/a7-schwach", confidence=5.0, overlap_ref=[0.0, 100.0], ok=True),
        dict(base, other="/a7-stark", confidence=15.0, overlap_ref=[0.0, 100.0], ok=True),
        dict(base, other="/a7-kaputt", confidence=99.0, overlap_ref=[0.0, 100.0], ok=False)]}
    assert S.a7_for_cut(sync, "/fx3", 10, 20)["other"] == "/a7-stark"
    assert S.a7_for_cut({"paare": []}, "/fx3", 0, 1) is None
