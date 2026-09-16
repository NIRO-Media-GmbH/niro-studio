"""schnittbild: PNG aus einem mit ffmpeg erzeugten Testclip (Filmstreifen, Pegel, Wörter, Schnitte, Marken)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from niro_autocut import schnittbild as SB
from niro_autocut.charge import AutoCutError

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


@pytest.fixture
def clip(tmp_path: Path) -> Path:
    p = tmp_path / "c.mov"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=2",
                    "-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le", str(p)], check=True)
    return p


def test_pegel_db_level_of_sine(clip):
    db = SB.pegel_db(clip, 0.0, 1.0)
    assert 90 <= db.size <= 101
    assert -30 < float(np.median(db)) < -15          # lavfi-Sinus: Amplitude 1/8 → RMS ≈ −21 dBFS


def test_zeichne_png_mit_woertern_schnitten_und_marken(clip, tmp_path):
    woerter = [{"text": "Hallo", "start": 0.2, "end": 0.6}, {"text": "Ja,", "start": 0.9, "end": 0.9},
               {"text": "draußen", "start": 1.5, "end": 1.9}, {"text": "ohne", "start": None, "end": None}]
    ziel = SB.zeichne(clip, 0.1, 1.9, tmp_path / "out" / "b.png", woerter=woerter, bild_schnitte=[1.0, 5.0],
                      ton_schnitte=[1.04], marken=[(1.0, "1 Knackser")], frames=6, beschriftung="Test",
                      tc_start="01:00:00:00", fps=25.0)
    assert ziel == tmp_path / "out" / "b.png"
    with Image.open(ziel) as im:
        assert im.size == (SB.BREITE, SB.HOEHE)
        rgb = im.convert("RGB")
        mitte = rgb.getpixel((SB.RAND + 150, SB.STREIFEN_Y + SB.STREIFEN_H // 2))
        assert mitte not in (SB.HG, SB.ZELLE)                     # Filmstreifen zeigt Bildinhalt
        pegel = [rgb.getpixel((x, y)) for x in range(SB.RAND + 10, SB.BREITE - SB.RAND - 10, 40)
                 for y in range(SB.PEGEL_Y + 5, SB.PEGEL_Y + SB.PEGEL_H - 5, 20)]
        assert any(p not in (SB.HG, SB.ZELLE) for p in pegel)       # Pegelband gezeichnet


def test_zeichne_fehler(clip, tmp_path):
    with pytest.raises(AutoCutError, match="nicht nach dem Anfang"):
        SB.zeichne(clip, 1.0, 1.0, tmp_path / "x.png")
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        SB.zeichne(tmp_path / "fehlt.mov", 0.0, 1.0, tmp_path / "x.png")
