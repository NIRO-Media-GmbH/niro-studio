"""Export für die Kantenprüfung lesen (Spec 2026-09-16, Abschnitt 2): Kennzahlen per ffprobe, Graustufen-Metriken
je Frame (Mittel, Streuung, Differenz zum Vorframe; Cache je Fingerprint) und den Ton als float32-PCM."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import _assert_not_nas, _which, ffprobe, fingerprint

BREITE, HOEHE = 96, 54
SR = 48000


def export_info(path) -> dict:
    """Bildrate, Frame-Zahl, Größe, Ton und Dauer des Exports (ffprobe)."""
    info = ffprobe(path)
    return {"datei": str(path), "fps": float(info.fps), "frames": int(info.nb_frames), "breite": int(info.width),
            "hoehe": int(info.height), "ton": bool(info.has_audio), "dauer_s": round(float(info.duration_s), 3)}


def _metriken_lauf(path: Path, hwaccel: bool) -> tuple[dict | None, str]:
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error"]
    if hwaccel:
        cmd += ["-hwaccel", "videotoolbox"]
    cmd += ["-i", str(path), "-map", "0:v:0", "-vf", f"scale={BREITE}:{HOEHE}:flags=area,format=gray",
            "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    groesse = BREITE * HOEHE
    mittel, streuung, diff = [], [], []
    vorher = None
    with tempfile.TemporaryFile() as fehler:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=fehler)
        try:
            while True:
                buf = proc.stdout.read(groesse)
                if len(buf) < groesse:
                    break
                f = np.frombuffer(buf, dtype=np.uint8).astype(np.float32)
                mittel.append(float(f.mean()))
                streuung.append(float(f.std()))
                diff.append(0.0 if vorher is None else float(np.abs(f - vorher).mean()))
                vorher = f
        finally:
            proc.stdout.close()
            rc = proc.wait()
        fehler.seek(0)
        meldung = fehler.read().decode("utf-8", "replace").strip()[-500:]
    if rc != 0 or not mittel:
        return None, meldung or f"ffmpeg Exit {rc}"
    return {"mittel": np.asarray(mittel, dtype=np.float32), "streuung": np.asarray(streuung, dtype=np.float32),
            "diff": np.asarray(diff, dtype=np.float32)}, meldung


def bild_metriken(path, cache_dir, n_erwartet: int | None = None) -> dict:
    """Mittel, Streuung und Differenz zum Vorframe je Frame (Graustufen 96×54).

    Erst mit VideoToolbox, bei Fehler oder abweichender Frame-Zahl (``n_erwartet``) in Software; Ergebnis im Cache
    ``<cache_dir>/<fingerprint>.npz`` (Fingerprint: Name, Größe, mtime).
    """
    path, cache_dir = Path(path), Path(cache_dir)
    _assert_not_nas(cache_dir, "Kanten-Cache")
    ziel = cache_dir / f"{fingerprint(path)}.npz"
    if ziel.exists():
        with np.load(ziel) as z:
            return {k: z[k] for k in ("mittel", "streuung", "diff")}
    m, meldung = _metriken_lauf(path, hwaccel=True)
    if m is None or (n_erwartet is not None and m["mittel"].size != n_erwartet):
        m, meldung = _metriken_lauf(path, hwaccel=False)
    if m is None:
        raise AutoCutError(f"Bild des Exports nicht lesbar ({path.name}): {meldung}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    teil = cache_dir / f"{ziel.stem}.part.npz"
    np.savez(teil, **m)
    teil.replace(ziel)
    return m


def ton_lesen(path, sr: int = SR) -> np.ndarray:
    """Ton des Exports als float32-Array (Samples × 2 Kanäle, auf Stereo gemischt)."""
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-i", str(path), "-map", "0:a:0", "-vn",
           "-ac", "2", "-ar", str(sr), "-f", "f32le", "-acodec", "pcm_f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise AutoCutError(f"Ton des Exports nicht lesbar ({Path(path).name}): "
                           f"{r.stderr.decode('utf-8', 'replace').strip()[-500:]}")
    x = np.frombuffer(r.stdout, dtype=np.float32)
    return x[: x.size - x.size % 2].reshape(-1, 2)
