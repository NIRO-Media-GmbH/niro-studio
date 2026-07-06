from pathlib import Path
from niro_transcribe.footage.discover import discover_clips, Clip


def test_discover_finds_clips_with_camera_and_sidecar(tmp_path):
    cam_a = tmp_path / "Kamera-A FX3 1"
    cam_a.mkdir()
    (cam_a / "FX3_0001.MP4").write_bytes(b"x")
    (cam_a / "FX3_0001.XML").write_bytes(b"<meta/>")
    (cam_a / "FX3_0002.MP4").write_bytes(b"x")  # kein Sidecar
    cam_b = tmp_path / "Kamera-B A7iv"
    cam_b.mkdir()
    (cam_b / "a7_0001.mov").write_bytes(b"x")
    (cam_b / "notes.txt").write_bytes(b"ignore me")

    clips = discover_clips(tmp_path)

    assert [c.path.name for c in clips] == ["FX3_0001.MP4", "FX3_0002.MP4", "a7_0001.mov"]
    assert clips[0].camera == "Kamera-A FX3 1"
    assert clips[0].sidecar is not None and clips[0].sidecar.name == "FX3_0001.XML"
    assert clips[1].sidecar is None
    assert clips[2].camera == "Kamera-B A7iv"
