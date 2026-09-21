"""Optischer Messweg der Telemetrie: Graustufen-Frames 480×270 bei 25 fps und
globale Verschiebung zwischen Nachbarframes per Phasenkorrelation (numpy statt
cv2, damit es im AutoCut-venv läuft). Rückfall für Clips ohne rtmd (Mavic) und
Referenz der Kalibrierung. Übernimmt das Verfahren aus ``ruhe.py`` der
Hochzeitszauber-Charge.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from scipy import ndimage

from .charge import AutoCutError
from .media import _which

BREITE, HOEHE = 480, 270
_FENSTER: dict[tuple[int, int], np.ndarray] = {}


def graustufen(path: str | Path, fps: float = 25.0, von_s: float | None = None,
               dauer_s: float | None = None, breite: int = BREITE,
               hoehe: int = HOEHE) -> np.ndarray:
    """Frames als (n, hoehe, breite) uint8; ``von_s``/``dauer_s`` schneiden per
    ffmpeg ``-ss``/``-t`` (Suche im Index).
    """
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-v", "error"]
    if von_s is not None:
        cmd += ["-ss", f"{von_s:.3f}"]
    if dauer_s is not None:
        cmd += ["-t", f"{dauer_s:.3f}"]
    cmd += ["-i", str(p), "-an", "-vf",
            f"fps={fps:g},scale={breite}:{hoehe}", "-f", "rawvideo",
            "-pix_fmt", "gray", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise AutoCutError(
            f"Frames nicht dekodierbar für {p.name}: "
            f"{r.stderr[-300:].decode(errors='replace')}")
    n = len(r.stdout) // (breite * hoehe)
    return np.frombuffer(r.stdout, np.uint8)[: n * breite * hoehe].reshape(
        n, hoehe, breite)


def _fenster(h: int, w: int) -> np.ndarray:
    """Hanning-Fenster zweidimensional als Cache."""
    if (h, w) not in _FENSTER:
        _FENSTER[(h, w)] = np.outer(np.hanning(h), np.hanning(w)).astype(
            np.float32)
    return _FENSTER[(h, w)]


def _subpixel(cm1: float, c0: float, cp1: float) -> float:
    """Subpixel-Versatz per quadratischer Interpolation."""
    d = cm1 - 2.0 * c0 + cp1
    return 0.0 if d == 0 else 0.5 * (cm1 - cp1) / d


def phasenkorrelation(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Verschiebung des Bildinhalts von ``a`` nach ``b`` in Pixeln: dx > 0
    nach rechts, dy > 0 nach unten (Subpixel).
    """
    if np.array_equal(a, b):
        return (0.0, 0.0)
    h, w = a.shape
    win = _fenster(h, w)
    fa = np.fft.fft2((a.astype(np.float32) - float(a.mean())) * win)
    fb = np.fft.fft2((b.astype(np.float32) - float(b.mean())) * win)
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    c = np.real(np.fft.ifft2(r))
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    py = (iy + _subpixel(c[(iy - 1) % h, ix], c[iy, ix],
                         c[(iy + 1) % h, ix]))
    px = (ix + _subpixel(c[iy, (ix - 1) % w], c[iy, ix],
                         c[iy, (ix + 1) % w]))
    if px > w / 2:
        px -= w
    if py > h / 2:
        py -= h
    return float(-px), float(-py)


def verschiebungen(frames: np.ndarray) -> np.ndarray:
    """(n−1, 2): Verschiebung des Inhalts von Frame i nach i+1 in px."""
    if len(frames) < 2:
        return np.zeros((0, 2), np.float64)
    return np.array(
        [phasenkorrelation(frames[i], frames[i + 1])
         for i in range(len(frames) - 1)],
        np.float64)


def schaerfe(frames: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Schärfe je Frame: mittlere quadrierte Laplace-Antwort nach Glättung
    (σ), geteilt durch die Bildvarianz (kontrastunabhängig, S-Log ist flach);
    0 bei flachem Bild. Verfahren aus ``broll_qualitaet.py`` (Wurst & Liebe,
    17.09.2026).
    """
    out = np.zeros(len(frames), np.float64)
    for i, f in enumerate(frames):
        g = ndimage.gaussian_filter(f.astype(np.float32), sigma)
        var = float(g.var())
        if var <= 1e-6:
            continue
        out[i] = float((ndimage.laplace(g) ** 2).mean()) / var
    return out
