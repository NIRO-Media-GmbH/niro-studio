"""telemetrie_optisch.py — Phasenkorrelation (Vorzeichen, Ganz- und Subpixel) und Frame-Dekodierung mit ffmpeg testsrc."""
from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest

from niro_autocut import telemetrie_optisch as O


def _bild(rng, h=270, w=480, rand=40):
    """Geglättetes Rauschbild mit Rand, aus dem verschobene Ausschnitte geschnitten werden."""
    base = rng.random((h + rand, w + rand)).astype(np.float32)
    k = np.ones((5, 5), np.float32) / 25
    from numpy.lib.stride_tricks import sliding_window_view
    sm = sliding_window_view(base, (5, 5)).reshape(-1, 25) @ k.ravel()
    return sm.reshape(h + rand - 4, w + rand - 4)


def test_phasenkorrelation_vorzeichen_und_subpixel():
    rng = np.random.default_rng(1)
    sm = _bild(rng)
    a = sm[10:280, 10:490]
    for sx, sy in ((5, 0), (-3, 2), (0, 7)):
        b = sm[10 - sy:280 - sy, 10 - sx:490 - sx]      # Inhalt von a um (sx, sy) verschoben: rechts/unten positiv
        dx, dy = O.phasenkorrelation(a, b)
        assert abs(dx - sx) < 0.1 and abs(dy - sy) < 0.1, (sx, sy, dx, dy)
    b = 0.5 * (sm[10:280, 8:488] + sm[10:280, 7:487])   # 2,5 px nach rechts
    dx, dy = O.phasenkorrelation(a, b)
    assert abs(dx - 2.5) < 0.15 and abs(dy) < 0.1


def test_phasenkorrelation_identisch_null():
    rng = np.random.default_rng(2)
    a = _bild(rng)[10:280, 10:490]
    assert O.phasenkorrelation(a, a) == (0.0, 0.0)


def test_verschiebungen_reihe():
    rng = np.random.default_rng(3)
    sm = _bild(rng)
    frames = np.stack([sm[10:280, 10 + k:490 + k] for k in (0, 2, 4, 4)])   # Inhalt wandert je Schritt 2 px nach links
    v = O.verschiebungen(frames)
    assert v.shape == (3, 2)
    assert np.allclose(v[:, 0], [-2, -2, 0], atol=0.1) and np.allclose(v[:, 1], 0, atol=0.1)
    assert O.verschiebungen(frames[:1]).shape == (0, 2)


def test_schaerfe_scharf_vor_unscharf():
    from scipy import ndimage
    rng = np.random.default_rng(4)
    scharf = (rng.random((270, 480)) * 255).astype(np.uint8)
    unscharf = ndimage.gaussian_filter(scharf, 3).astype(np.uint8)
    s = O.schaerfe(np.stack([scharf, unscharf, np.full((270, 480), 128, np.uint8)]))
    assert s.shape == (3,) and s[0] > 3 * s[1] > 0 and s[2] == 0.0


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_graustufen_dekodiert_testsrc(tmp_path):
    clip = tmp_path / "test.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=2",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    fr = O.graustufen(clip)
    assert fr.shape == (50, 270, 480) and fr.dtype == np.uint8
    teil = O.graustufen(clip, von_s=1.0, dauer_s=0.4)
    assert 8 <= teil.shape[0] <= 11
    assert O.verschiebungen(fr[:5]).shape == (4, 2)
