"""probe_media: ffmpeg-Argumentlisten für das synthetische Testmaterial der API-Probe, Überspringen vorhandener
Dateien, Fehlerbild; optional ein echter ffmpeg-Lauf (AUTOCUT_FFMPEG_LIVE=1)."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from niro_autocut import probe_media as PM
from niro_autocut.charge import AutoCutError


def _argv_by_key(work: Path) -> dict[str, list[str]]:
    return dict(PM.ffmpeg_commands(work, "/usr/bin/ffmpeg"))


def test_commands_cover_all_files_in_dependency_order(tmp_path):
    cmds = PM.ffmpeg_commands(tmp_path, "/usr/bin/ffmpeg")
    assert [k for k, _ in cmds] == ["ton_wav", "ton", "versetzt", "zaehler", "overlay"]
    for key, argv in cmds:
        assert argv[0] == "/usr/bin/ffmpeg" and argv[-1] == str(tmp_path / PM.FILES[key])
        assert "-y" in argv


def test_audio_is_deterministic_bursts_with_known_peak(tmp_path):
    argv = _argv_by_key(tmp_path)["ton_wav"]
    src = argv[argv.index("-i") + 1]
    assert src.startswith("aevalsrc=") and "random(0)" in src and "d=12" in src and "c=stereo" in src
    assert f"{PM.PEAK_AMPLITUDE}*" in src and f"gt(t,{PM.VERSATZ_S})" in src


def test_ton_and_versetzt_differ_only_by_seek(tmp_path):
    a = _argv_by_key(tmp_path)
    ton, ver = a["ton"], a["versetzt"]
    assert ton[ton.index("-ss") + 1] == str(PM.VERSATZ_S) and "-ss" not in ver
    assert ton[ton.index("-t") + 1] == "10" and ver[ver.index("-t") + 1] == "12"
    assert str(tmp_path / "ton.wav") in ton and str(tmp_path / "ton.wav") in ver
    assert "prores_ks" in ton and "pcm_s16le" in ton


def test_zaehler_is_50p_without_audio_and_overlay_has_alpha(tmp_path):
    a = _argv_by_key(tmp_path)
    assert "testsrc=size=1920x1080:rate=50" in a["zaehler"] and "-an" in a["zaehler"]
    ov = a["overlay"]
    assert "4444" in ov and "yuva444p10le" in ov and "black@0.0" in ov[ov.index("-i") + 1]


def test_ensure_runs_only_missing_and_returns_paths(tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, **kw):
        calls.append(argv)
        Path(argv[-1]).write_bytes(b"x")
        return subprocess.CompletedProcess(argv, 0, "", "")

    (tmp_path / "ton.wav").write_bytes(b"vorhanden")
    paths = PM.ensure_probe_media(tmp_path, run=fake_run, ffmpeg="/usr/bin/ffmpeg")
    assert [c[-1] for c in calls] == [str(paths[k]) for k in ("ton", "versetzt", "zaehler", "overlay")]
    assert paths["ton_wav"].read_bytes() == b"vorhanden"
    assert PM.ensure_probe_media(tmp_path, run=fake_run, ffmpeg="/usr/bin/ffmpeg") == paths
    assert len(calls) == 4                                   # zweiter Lauf: nichts mehr zu tun


def test_ensure_uses_subprocess_run_by_default(tmp_path, monkeypatch):
    def fake_run(argv, **kw):
        Path(argv[-1]).write_bytes(b"x")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(PM.subprocess, "run", fake_run)
    monkeypatch.setattr(PM, "_which", lambda name: "/usr/bin/ffmpeg")
    assert PM.ensure_probe_media(tmp_path)["overlay"].is_file()


def test_ensure_raises_german_error_on_ffmpeg_failure(tmp_path):
    def bad_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, "", "Unrecognized option")

    with pytest.raises(AutoCutError, match="ton.wav konnte nicht erzeugt werden"):
        PM.ensure_probe_media(tmp_path, run=bad_run, ffmpeg="/usr/bin/ffmpeg")


def test_ensure_regenerates_empty_file(tmp_path):
    calls: list[list[str]] = []

    def fake_run(argv, **kw):
        calls.append(argv)
        Path(argv[-1]).write_bytes(b"neu")
        return subprocess.CompletedProcess(argv, 0, "", "")

    (tmp_path / "ton.wav").write_bytes(b"")                     # leer = gilt als fehlend
    paths = PM.ensure_probe_media(tmp_path, run=fake_run, ffmpeg="/usr/bin/ffmpeg")
    assert calls[0][-1] == str(paths["ton_wav"]) and len(calls) == 5
    assert paths["ton_wav"].read_bytes() == b"neu"


def test_ensure_raises_when_ffmpeg_succeeds_without_output(tmp_path):
    def silent_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, "", "")      # rc 0, aber keine Datei

    with pytest.raises(AutoCutError, match="konnte nicht erzeugt werden"):
        PM.ensure_probe_media(tmp_path, run=silent_run, ffmpeg="/usr/bin/ffmpeg")


@pytest.mark.skipif(not os.environ.get("AUTOCUT_FFMPEG_LIVE") or not shutil.which("ffmpeg"),
                    reason="AUTOCUT_FFMPEG_LIVE=1 und ffmpeg nötig — echter Lauf, dauert und schreibt ~100 MB")
def test_real_ffmpeg_media_have_expected_properties(tmp_path):
    from niro_autocut.ton import measure_true_peak
    paths = PM.ensure_probe_media(tmp_path)

    def probe(p: Path) -> dict[str, str]:
        # Wertzuordnung per Feldname statt CSV-Position: ffprobe 8.0.1 gibt -show_entries-Felder in fester
        # interner Reihenfolge aus, unabhängig von der hier angefragten Reihenfolge (verifiziert per Handlauf).
        r = subprocess.run([shutil.which("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=r_frame_rate,pix_fmt", "-of", "default=noprint_wrappers=1", str(p)],
                            capture_output=True, text=True)
        return dict(line.split("=", 1) for line in r.stdout.strip().splitlines())

    assert probe(paths["ton"])["r_frame_rate"] == "25/1" and probe(paths["zaehler"])["r_frame_rate"] == "50/1"
    # ProRes 4444/4444 XQ ist laut Spezifikation ein 12-Bit-Codec — ffmpegs prores_ks/proresdec berichten
    # yuva444p12le für JEDEN 4444-Profil-Stream, auch ohne Alphakanal und unabhängig vom Encoder-Eingabe-Pixelformat
    # (per Handlauf verifiziert: -pix_fmt yuva444p10le, -alpha_bits 8 und Profil 4444xq ändern daran nichts).
    # yuva444p10le ist für dieses Profil bei keiner ffmpeg-Version erreichbar; erwartet daher yuva444p12le.
    assert probe(paths["overlay"])["pix_fmt"] == "yuva444p12le"
    tpk = measure_true_peak(paths["ton"], 0.0, 10.0)
    assert -13.0 <= tpk <= -11.0
