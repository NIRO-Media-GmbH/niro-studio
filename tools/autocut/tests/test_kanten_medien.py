"""kanten_medien: ffprobe-Kennzahlen, Bild-Metriken mit Cache, Ton — an einem mit ffmpeg erzeugten Testclip."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from niro_autocut import kanten_medien as KM
from niro_autocut.charge import AutoCutError

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _clip(pfad: Path, schwarz_frame: int) -> Path:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=25:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
                    "-vf", f"drawbox=enable='eq(n,{schwarz_frame})':color=black:t=fill",
                    "-c:v", "mpeg4", "-q:v", "2", "-g", "1", "-c:a", "pcm_s16le", "-ac", "2", str(pfad)], check=True)
    return pfad


def test_export_info_metriken_cache_und_ton(tmp_path):
    clip = _clip(tmp_path / "t.mov", 20)
    info = KM.export_info(clip)
    assert (info["frames"], info["fps"], info["breite"], info["ton"]) == (50, 25.0, 160, True)
    m = KM.bild_metriken(clip, tmp_path / "cache", n_erwartet=50)
    assert m["mittel"].shape == (50,) and m["diff"][0] == 0.0
    assert m["mittel"][20] < 20 and m["streuung"][20] < 2 and m["mittel"][19] > 40
    assert m["diff"][20] > 20 and m["diff"][21] > 20
    assert len(list((tmp_path / "cache").glob("*.npz"))) == 1
    assert np.array_equal(KM.bild_metriken(clip, tmp_path / "cache")["diff"], m["diff"])     # Cache-Treffer
    x = KM.ton_lesen(clip)
    assert x.shape[1] == 2 and abs(x.shape[0] - 96000) <= 1024 and 0.05 < float(np.abs(x).max()) <= 1.0


def test_bild_und_ton_melden_unlesbaren_export(tmp_path):
    kaputt = tmp_path / "kaputt.mov"
    kaputt.write_bytes(b"kein video")
    with pytest.raises(AutoCutError, match="nicht lesbar"):
        KM.bild_metriken(kaputt, tmp_path / "cache")
    with pytest.raises(AutoCutError, match="nicht lesbar"):
        KM.ton_lesen(kaputt)
