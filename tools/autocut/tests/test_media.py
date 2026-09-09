"""Tests für media.py — ffprobe-Parsing, Proxy-Suche, Format, Frame-Rechnung, Audio-Extraktion."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from niro_autocut import media
from niro_autocut.charge import AutoCutError
from niro_autocut.media import MediaInfo

PROBE_JSON = {
    "streams": [
        {"index": 0, "codec_type": "video", "codec_name": "h264", "width": 3840, "height": 2160,
         "r_frame_rate": "25/1", "avg_frame_rate": "25/1", "nb_frames": "10344",
         "side_data_list": [{"side_data_type": "Display Matrix", "rotation": -90}]},
        {"index": 1, "codec_type": "audio", "codec_name": "pcm_s16be", "sample_rate": "48000", "channels": 2},
        {"index": 2, "codec_type": "data", "tags": {"timecode": "04:03:46:17"}}],
    "format": {"duration": "413.760000"}}


def _copy() -> dict:
    return json.loads(json.dumps(PROBE_JSON))


# --- Parsen ------------------------------------------------------------

def test_parse_probe_rotation_and_tc():
    info = media._parse_probe("/x/FX3_9651.MP4", PROBE_JSON)
    assert info.fps == 25.0 and info.rotation == 90 and info.nb_frames == 10344
    assert info.timecode == "04:03:46:17" and info.has_audio and info.sample_rate == 48000
    assert info.channels == 2 and info.duration_s == 413.76
    assert info.path == "/x/FX3_9651.MP4"
    assert media.is_portrait(info)
    fmt = media.timeline_format(info)
    assert (fmt["width"], fmt["height"], fmt["orientation"]) == (2160, 3840, "9:16")
    assert fmt["fps"] == 25.0


def test_landscape_when_no_rotation():
    d = _copy()
    d["streams"][0].pop("side_data_list")
    info = media._parse_probe("/x/a.MP4", d)
    assert info.rotation == 0
    assert not media.is_portrait(info)
    fmt = media.timeline_format(info)
    assert (fmt["width"], fmt["height"], fmt["orientation"]) == (3840, 2160, "16:9")


def test_rotation_from_legacy_tag():
    d = _copy()
    d["streams"][0].pop("side_data_list")
    d["streams"][0]["tags"] = {"rotate": "270"}
    info = media._parse_probe("/x/a.MP4", d)
    assert info.rotation == 270 and media.is_portrait(info)


def test_nb_frames_fallback_from_duration():
    d = _copy()
    d["streams"][0].pop("nb_frames")
    info = media._parse_probe("/x/a.MP4", d)
    assert info.nb_frames == round(413.76 * 25)


def test_fps_fallback_to_r_frame_rate():
    d = _copy()
    d["streams"][0]["avg_frame_rate"] = "0/0"
    d["streams"][0]["r_frame_rate"] = "30000/1001"
    info = media._parse_probe("/x/a.MP4", d)
    assert info.fps == 29.97


def test_no_audio_stream():
    d = _copy()
    d["streams"] = [s for s in d["streams"] if s["codec_type"] != "audio"]
    info = media._parse_probe("/x/a.MP4", d)
    assert not info.has_audio and info.sample_rate == 0 and info.channels == 0


def test_no_video_stream_raises():
    d = _copy()
    d["streams"] = [s for s in d["streams"] if s["codec_type"] != "video"]
    with pytest.raises(AutoCutError, match="Kein Videostream"):
        media._parse_probe("/x/a.MP4", d)


def test_mediainfo_roundtrip():
    info = media._parse_probe("/x/FX3_9651.MP4", PROBE_JSON)
    assert MediaInfo.from_dict(json.loads(json.dumps(info.to_dict()))) == info


# --- Proxy -------------------------------------------------------------

def test_proxy_for(tmp_path):
    clip = tmp_path / "Interviews" / "Anna" / "FX3_0001.MP4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    assert media.proxy_for(clip) is None
    prox = clip.parent / "Proxy" / "FX3_0001.mov"
    prox.parent.mkdir()
    prox.write_bytes(b"y")
    assert media.proxy_for(clip) == prox
    assert media.proxy_for(str(clip)) == prox


def test_check_proxy_match():
    o = MediaInfo("/o", 413.76, 25.0, 3840, 2160, 90, 10344, None, True, 48000, 2)
    p = MediaInfo("/p", 413.82, 25.0, 1920, 1080, 0, 10345, None, True, 48000, 2)
    assert media.check_proxy_match(o, p) == []
    p2 = MediaInfo("/p", 400.0, 30.0, 1920, 1080, 0, 12000, None, True, 48000, 2)
    probs = media.check_proxy_match(o, p2)
    assert any("Bildrate" in x for x in probs) and any("Frames" in x for x in probs)


def test_check_proxy_match_tolerance_is_one_frame():
    o = MediaInfo("/o", 413.76, 25.0, 3840, 2160, 90, 10344, None, True, 48000, 2)
    p = MediaInfo("/p", 413.84, 25.0, 1920, 1080, 0, 10346, None, True, 48000, 2)
    assert media.check_proxy_match(o, p) != []
    assert media.check_proxy_match(o, p, tol_frames=2) == []


# --- Frames ------------------------------------------------------------

def test_frames_roundtrip():
    assert media.seconds_to_frames(1.95, 25) == 49
    assert media.frames_to_seconds(48, 25) == 1.92
    assert media.seconds_to_frames(0, 25) == 0
    assert media.frames_to_seconds(0, 25) == 0.0


# --- Dateizugriffe -----------------------------------------------------

def test_ffprobe_missing_file(tmp_path):
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        media.ffprobe(tmp_path / "fehlt.MP4")


def test_extract_audio_refuses_nas(tmp_path):
    src = tmp_path / "clip.MP4"
    src.write_bytes(b"x")
    with pytest.raises(AutoCutError, match="NAS"):
        media.extract_audio_16k(src, "/Volumes/Irgendein NAS/_work")


def test_extract_audio_failure_leaves_no_partial_wav(tmp_path, monkeypatch):
    """Bricht ffmpeg ab, darf keine halbe WAV liegen bleiben (sonst gälte sie beim nächsten Aufruf als Cache)."""
    src = tmp_path / "clip.MP4"
    src.write_bytes(b"x" * 10)
    out_dir = tmp_path / "work" / "audio"

    def fake_run(cmd, **kw):
        Path(cmd[-1]).write_bytes(b"\0" * 5000)  # ffmpeg hat schon geschrieben, stirbt dann
        return subprocess.CompletedProcess(cmd, 1, "", "Input/output error")

    monkeypatch.setattr(media.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(media.subprocess, "run", fake_run)
    with pytest.raises(AutoCutError, match="Audio-Extraktion fehlgeschlagen"):
        media.extract_audio_16k(src, out_dir)
    assert list(out_dir.iterdir()) == []


HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@pytest.fixture
def synth_clip(tmp_path: Path) -> Path:
    """1 s Testclip 64x36 @ 25 fps mit 440-Hz-Sinus, 48 kHz stereo, per ffmpeg erzeugt."""
    clip = tmp_path / "Interviews" / "Anna" / "FX3_0001.MOV"
    clip.parent.mkdir(parents=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "testsrc=size=64x36:rate=25",
           "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
           "-t", "1", "-c:v", "mpeg4", "-c:a", "pcm_s16le", "-ac", "2", str(clip)]
    subprocess.run(cmd, check=True)
    return clip


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe nicht installiert")
def test_ffprobe_real_file(synth_clip):
    info = media.ffprobe(synth_clip)
    assert info.path == str(synth_clip)
    assert info.fps == 25.0 and info.width == 64 and info.height == 36 and info.rotation == 0
    assert info.nb_frames == 25 and abs(info.duration_s - 1.0) < 0.05
    assert info.has_audio and info.sample_rate == 48000 and info.channels == 2
    assert media.timeline_format(info)["orientation"] == "16:9"
    assert len(media.fingerprint(synth_clip)) == 64


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe nicht installiert")
def test_extract_audio_16k_and_cache(synth_clip, tmp_path):
    out_dir = tmp_path / "_intern" / "autocut" / "work" / "audio"
    wav = media.extract_audio_16k(synth_clip, out_dir)
    assert wav.parent == out_dir and wav.suffix == ".wav"
    assert wav.name.startswith("FX3_0001.")
    # WAV hat keinen Videostream, daher direkt per ffprobe prüfen statt über media.ffprobe
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", str(wav)],
                       capture_output=True, text=True, check=True)
    a = json.loads(r.stdout)["streams"][0]
    assert a["codec_type"] == "audio" and a["sample_rate"] == "16000" and a["channels"] == 1
    assert a["codec_name"] == "pcm_s16le"
    mtime = wav.stat().st_mtime_ns
    assert media.extract_audio_16k(synth_clip, out_dir) == wav
    assert wav.stat().st_mtime_ns == mtime, "zweiter Aufruf muss den Cache nutzen"
