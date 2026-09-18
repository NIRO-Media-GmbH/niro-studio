from __future__ import annotations

import shutil

import pytest

from niro_review import medien
from niro_review.ablage import ReviewFehler


def probe(codec="h264", pix="yuv420p", audio="aac", container="mov,mp4,m4a,3gp,3g2,mj2", nb_frames="574", dauer="23.040000"):
    streams = [{"codec_type": "video", "codec_name": codec, "pix_fmt": pix, "width": 2160, "height": 3840,
                "r_frame_rate": "25/1", "avg_frame_rate": "25/1", "nb_frames": nb_frames}]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": audio})
    return {"streams": streams, "format": {"format_name": container, "duration": dauer, "size": "35497873"}}


def test_info_aus_probe():
    info = medien.info_aus_probe(probe(), 35497873)
    assert (info.fps, info.frames, info.breite, info.hoehe, info.groesse) == (25.0, 574, 2160, 3840, 35497873)
    assert info.dauer_s == pytest.approx(23.04) and info.video_codec == "h264" and info.audio_codec == "aac" and not info.alpha


def test_info_frames_aus_dauer_und_fps_bruch():
    p = probe(nb_frames=None, dauer="10.0")
    p["streams"][0]["avg_frame_rate"] = "24000/1001"
    p["streams"][0]["r_frame_rate"] = "24000/1001"
    del p["streams"][0]["nb_frames"]
    info = medien.info_aus_probe(p)
    assert info.fps == pytest.approx(23.976, abs=0.001) and info.frames == 240


def test_info_ohne_video():
    with pytest.raises(ReviewFehler):
        medien.info_aus_probe({"streams": [{"codec_type": "audio"}], "format": {}})


@pytest.mark.parametrize("kw,erwartet", [
    ({}, "kopie"),
    ({"audio": None}, "kopie"),
    ({"codec": "hevc"}, "umkodieren"),
    ({"pix": "yuv422p"}, "umkodieren"),
    ({"audio": "pcm_s16le"}, "umkodieren"),
    ({"container": "matroska,webm"}, "umkodieren"),
    ({"codec": "prores", "pix": "yuva444p10le"}, "alpha"),
    ({"codec": "png", "pix": "rgba"}, "alpha"),
])
def test_entscheidung(kw, erwartet):
    assert medien.entscheidung(medien.info_aus_probe(probe(**kw))) == erwartet


def test_ffmpeg_befehl():
    cmd = medien.ffmpeg_befehl("/q.mov", "/z.mp4", "h264_videotoolbox", True, 1920 * 1080)
    assert cmd[:2] == ["ffmpeg", "-y"] and "-c:v" in cmd and cmd[cmd.index("-c:v") + 1] == "h264_videotoolbox"
    assert "yuv420p" in cmd and "+faststart" in cmd and cmd[-1] == "/z.mp4" and "0:a:0?" in cmd
    assert cmd[cmd.index("-b:v") + 1] == "8M"
    cmd4k = medien.ffmpeg_befehl("/q.mov", "/z.mp4", "libx264", False, 2160 * 3840)
    assert "-crf" in cmd4k and "0:a:0?" not in cmd4k


@pytest.mark.parametrize("frame,fps,tc", [
    (0, 25.0, "00:00:00:00"), (50, 25.0, "00:00:02:00"), (729, 25.0, "00:00:29:04"), (90061, 25.0, "01:00:02:11"),
    (24, 23.976, "00:00:01:00"), (100, 50.0, "00:00:02:00"), (None, 25.0, "—"),
])
def test_timecode(frame, fps, tc):
    assert medien.timecode(frame, fps) == tc


def test_frame_aus_timecode():
    assert medien.frame_aus_timecode("00:00:29:04", 25.0) == 729
    assert medien.frame_aus_timecode("01:00:02:11", 25) == 90061
    with pytest.raises(ReviewFehler):
        medien.frame_aus_timecode("29:04", 25.0)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg fehlt")
def test_probe_kopie_und_umkodieren(testvideo_h264, testvideo_mpeg4, tmp_path):
    medien.werkzeuge_pruefen()
    info = medien.info_aus_probe(medien.ffprobe(testvideo_h264), testvideo_h264.stat().st_size)
    assert medien.entscheidung(info) == "kopie" and info.frames == 50 and info.fps == 25.0
    info2 = medien.info_aus_probe(medien.ffprobe(testvideo_mpeg4))
    assert medien.entscheidung(info2) == "umkodieren"
    ziel = tmp_path / "video.mp4"
    encoder = medien.umkodieren(testvideo_mpeg4, ziel, info2)
    assert encoder in ("h264_videotoolbox", "libx264") and ziel.stat().st_size > 0
    neu = medien.info_aus_probe(medien.ffprobe(ziel))
    assert neu.video_codec == "h264" and neu.pix_fmt == "yuv420p" and neu.audio_codec == "aac" and abs(neu.frames - 50) <= 1
    bild = tmp_path / "thumb.jpg"
    medien.vorschaubild(ziel, bild, neu.dauer_s)
    assert bild.stat().st_size > 1000
