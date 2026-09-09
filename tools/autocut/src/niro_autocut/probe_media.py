"""Synthetisches Testmaterial für resolve_probe_api.py (Spec „Grundlage Resolve 21.1", Abschnitt 2.2) — lokal per
ffmpeg, kein NAS, kein Kundenmaterial. Reine Argumentlisten (testbar) plus ensure_probe_media (führt nur aus,
was fehlt).

Dateien in <Charge>/_intern/autocut/work/probe_api/:
  ton.wav              12 s, 48 kHz Stereo: Rausch-Bursts (Sample-Peak −12 dBFS), erste 2 s still, deterministisch
  ton_25p.mov          10 s, 1920×1080, 25 fps testsrc, Audio = ton.wav ab Sekunde 2 (Bursts ab 0 s)
  ton_25p_versetzt.mov 12 s, gleiches Bild, Audio = ton.wav komplett (dieselben Bursts 2,0 s = 50 Frames später)
  zaehler_50p.mov       4 s, 1920×1080, 50 fps testsrc, ohne Ton
  overlay_alpha.mov     2 s, 25 fps, rotes Feld 400×200 (60 % Deckung) auf transparentem Canvas, ProRes 4444
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .charge import AutoCutError
from .media import _which

FILES = {"ton_wav": "ton.wav", "ton": "ton_25p.mov", "versetzt": "ton_25p_versetzt.mov",
         "zaehler": "zaehler_50p.mov", "overlay": "overlay_alpha.mov"}
FPS = 25
VERSATZ_S = 2.0            # Bursts in „versetzt" liegen 2,0 s (50 Frames) später als in „ton"
PEAK_AMPLITUDE = 0.25      # Sample-Peak −12,04 dBFS
# Nicht periodische Bursts (Perioden 1,7 s und 2,3 s), erste VERSATZ_S Sekunden still; random(0) nutzt den internen
# Zustand 0 und liefert bei jedem Lauf dieselbe Folge. Das Gating gt(…,0) hält die Amplitude bei ≤ PEAK_AMPLITUDE.
_AUDIO_EXPR = f"{PEAK_AMPLITUDE}*random(0)*gt(t,{VERSATZ_S})*gt(lt(mod(t,1.7),0.35)+lt(mod(t,2.3),0.2),0)"
# Das harte An/Aus-Gating erzeugt Sprünge zwischen Samples; beim True-Peak (Oversampling-Rekonstruktion) schwingt
# das über das Sample-Maximum hinaus (gemessen 2–3 dB über PEAK_AMPLITUDE). lowpass=8000 glättet diese Kanten und
# hält den True Peak nah an den −12 dBFS Sample-Peak heran, ohne den Rausch-Charakter der Bursts zu verändern.
_AUDIO_FILTER = "lowpass=f=8000"
_PRORES_PROXY = ["-c:v", "prores_ks", "-profile:v", "0", "-pix_fmt", "yuv422p10le"]   # Proxy-Profil: klein, Resolve-sicher


def media_paths(work_dir: str | Path) -> dict[str, Path]:
    return {k: Path(work_dir) / v for k, v in FILES.items()}


def ffmpeg_commands(work_dir: str | Path, ffmpeg: str = "ffmpeg") -> list[tuple[str, list[str]]]:
    """(Schlüssel, argv) in Abhängigkeitsreihenfolge — ton.wav zuerst, beide Ton-Clips leiten sich daraus ab."""
    p = media_paths(work_dir)
    base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    video = f"testsrc=size=1920x1080:rate={FPS}"
    return [
        ("ton_wav", base + ["-f", "lavfi", "-i", f"aevalsrc=exprs='{_AUDIO_EXPR}':s=48000:c=stereo:d=12,{_AUDIO_FILTER}",
                            "-c:a", "pcm_s16le", str(p["ton_wav"])]),
        ("ton", base + ["-f", "lavfi", "-i", video, "-ss", str(VERSATZ_S), "-i", str(p["ton_wav"]), "-t", "10",
                        "-map", "0:v", "-map", "1:a", *_PRORES_PROXY, "-c:a", "pcm_s16le", str(p["ton"])]),
        ("versetzt", base + ["-f", "lavfi", "-i", video, "-i", str(p["ton_wav"]), "-t", "12",
                             "-map", "0:v", "-map", "1:a", *_PRORES_PROXY, "-c:a", "pcm_s16le", str(p["versetzt"])]),
        ("zaehler", base + ["-f", "lavfi", "-i", "testsrc=size=1920x1080:rate=50", "-t", "4", *_PRORES_PROXY, "-an",
                            str(p["zaehler"])]),
        ("overlay", base + ["-f", "lavfi", "-i", f"color=c=red@0.6:s=400x200:r={FPS},format=rgba,"
                                                   f"pad=1920:1080:200:200:color=black@0.0,format=yuva444p10le",
                            "-t", "2", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                            str(p["overlay"])]),
    ]


def ensure_probe_media(work_dir: str | Path, run=None, ffmpeg: str | None = None) -> dict[str, Path]:
    """Alle fünf Dateien bereitstellen; vorhandene (nicht leere) werden nicht neu erzeugt."""
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    run = run or subprocess.run
    ffmpeg = ffmpeg or _which("ffmpeg")
    paths = media_paths(work_dir)
    for key, argv in ffmpeg_commands(work_dir, ffmpeg):
        out = paths[key]
        if out.is_file() and out.stat().st_size > 0:
            continue
        r = run(argv, capture_output=True, text=True, errors="replace")
        if r.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
            raise AutoCutError(f"Testmaterial {out.name} konnte nicht erzeugt werden (ffmpeg rc={r.returncode}): "
                               f"{(r.stderr or '')[-300:]}")
    return paths
