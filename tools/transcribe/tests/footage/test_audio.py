import shutil
import subprocess
from pathlib import Path

import pytest

from niro_transcribe.footage.audio import extract_audio

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _make_tiny_mp4(path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5",
         "-f", "lavfi", "-i", "testsrc=duration=0.5:size=128x128:rate=10",
         "-shortest", str(path)],
        check=True, capture_output=True,
    )


def test_extract_audio_produces_wav(tmp_path):
    mp4 = tmp_path / "clip.mp4"
    _make_tiny_mp4(mp4)
    out = extract_audio(mp4, tmp_path / "work")
    assert out.exists()
    assert out.suffix == ".wav"
    assert out.stat().st_size > 0
