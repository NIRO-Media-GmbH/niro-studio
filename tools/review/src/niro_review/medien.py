"""Medien: ffprobe → Medieninfo, Entscheidung Kopie/Umkodierung/Alpha, ffmpeg-Aufrufe, Vorschaubild, Timecode.
Spec „Befehle" (Review-Kopie) und „Datenmodell" (Frames sind die Wahrheit)."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Optional

from .ablage import ReviewFehler

_ALPHA_PIX = {"rgba", "bgra", "argb", "abgr", "ya8", "ya16le", "ya16be", "rgba64le", "rgba64be", "bgra64le", "bgra64be"}


@dataclass
class Medieninfo:
    dauer_s: float
    fps: float
    frames: int
    breite: int
    hoehe: int
    groesse: int
    container: str
    video_codec: str
    pix_fmt: str
    audio_codec: Optional[str]
    alpha: bool


def werkzeuge_pruefen() -> None:
    for w in ("ffmpeg", "ffprobe"):
        if not shutil.which(w):
            raise ReviewFehler(f"{w} fehlt — SETUP.md Schritt 3 (brew install ffmpeg).", 2)


def ffprobe(pfad: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(pfad)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise ReviewFehler(f"ffprobe scheitert an „{Path(pfad).name}“: {r.stderr.strip()[-300:]}", 1)
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        raise ReviewFehler(f"ffprobe liefert kein JSON für „{Path(pfad).name}“.", 1)


def _fps(stream: dict) -> float:
    for feld in ("avg_frame_rate", "r_frame_rate"):
        wert = stream.get(feld)
        if wert and wert not in ("0/0", "0", "0/1"):
            try:
                f = Fraction(wert)
                if f > 0:
                    return float(f)
            except (ValueError, ZeroDivisionError):
                pass
    return 25.0


def info_aus_probe(probe: dict, groesse: int = 0) -> Medieninfo:
    streams = probe.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        raise ReviewFehler("Datei enthält keinen Videostream.", 1)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = probe.get("format") or {}
    fps = _fps(video)
    dauer = float(fmt.get("duration") or video.get("duration") or 0.0)
    frames = int(video.get("nb_frames") or 0) or int(round(dauer * fps))
    if not dauer and frames:
        dauer = frames / fps
    pix = str(video.get("pix_fmt") or "")
    alpha = pix.startswith("yuva") or pix.startswith("gbrap") or pix in _ALPHA_PIX
    return Medieninfo(dauer_s=dauer, fps=fps, frames=frames, breite=int(video.get("width") or 0),
                      hoehe=int(video.get("height") or 0), groesse=int(groesse or fmt.get("size") or 0),
                      container=str(fmt.get("format_name") or ""), video_codec=str(video.get("codec_name") or ""),
                      pix_fmt=pix, audio_codec=str(audio.get("codec_name")) if audio else None, alpha=alpha)


MAX_KANTE = 1920  # Review-Kopie: lange Kante höchstens 1920 px — 4K ruckelt im Browser (Messung 18.09.: 131/142 Frames verworfen)


def entscheidung(info: Medieninfo, max_kante: Optional[int] = MAX_KANTE) -> str:
    """kopie = Browser spielt die Datei direkt (MP4/MOV, H.264 yuv420p, AAC oder ohne Ton, lange Kante ≤ max_kante);
    sonst umkodieren. max_kante None = Auflösung nie antasten."""
    if info.alpha:
        return "alpha"
    mp4 = any(t in ("mov", "mp4") for t in info.container.split(","))
    klein = max_kante is None or max(info.breite, info.hoehe) <= max_kante
    if mp4 and klein and info.video_codec == "h264" and info.pix_fmt == "yuv420p" and info.audio_codec in (None, "aac"):
        return "kopie"
    return "umkodieren"


def skalierung(max_kante: Optional[int]) -> str:
    """scale-Filter: lange Kante auf max_kante begrenzen (nie vergrößern), beide Seiten gerade."""
    if max_kante is None:
        return "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    m = int(max_kante)
    return (f"scale=w='if(gte(iw,ih),trunc(min(iw,{m})/2)*2,-2)':h='if(gte(iw,ih),-2,trunc(min(ih,{m})/2)*2)'")


def ffmpeg_befehl(quelle, ziel, encoder: str = "h264_videotoolbox", hat_ton: bool = True, pixel: int = 0,
                  max_kante: Optional[int] = MAX_KANTE) -> list:
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(quelle), "-map", "0:v:0"]
    if hat_ton:
        cmd += ["-map", "0:a:0?"]
    cmd += ["-c:v", encoder, "-vf", skalierung(max_kante), "-g", "25"]  # kurze GOP: flottes Scrubben und Frame-Steppen
    if encoder == "h264_videotoolbox":
        gross = max_kante is None and pixel > 1920 * 1080
        cmd += ["-b:v", "16M" if gross else "8M", "-allow_sw", "1"]
    else:
        cmd += ["-preset", "medium", "-crf", "18"]
    cmd += ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-map_metadata", "-1",
            "-f", "mp4", str(ziel)]
    return cmd


def umkodieren(quelle: Path, ziel: Path, info: Medieninfo, max_kante: Optional[int] = MAX_KANTE) -> str:
    """Review-Kopie als MP4 (H.264 yuv420p, AAC, lange Kante ≤ max_kante); erst VideoToolbox, dann libx264.
    Gibt den Encoder zurück."""
    fehler = ""
    for encoder in ("h264_videotoolbox", "libx264"):
        cmd = ffmpeg_befehl(quelle, ziel, encoder, info.audio_codec is not None, info.breite * info.hoehe, max_kante)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and Path(ziel).is_file() and Path(ziel).stat().st_size > 0:
            return encoder
        fehler = r.stderr.strip()[-300:]
    raise ReviewFehler(f"ffmpeg scheitert an „{Path(quelle).name}“: {fehler}", 2)


def vorschaubild(quelle: Path, ziel: Path, dauer_s: float) -> None:
    """JPEG bei 25 % der Dauer, 640 px breit; Rückfall auf das erste Bild."""
    for ss in (max(0.0, float(dauer_s or 0) * 0.25), 0.0):
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.3f}", "-i", str(quelle), "-frames:v", "1",
               "-vf", "scale=640:-2", "-q:v", "3", str(ziel)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and Path(ziel).is_file() and Path(ziel).stat().st_size > 0:
            return
    raise ReviewFehler(f"Vorschaubild scheitert an „{Path(quelle).name}“: {r.stderr.strip()[-200:]}", 2)


def timecode(frame: Optional[int], fps: float) -> str:
    if frame is None:
        return "—"
    basis = max(1, int(round(float(fps))))
    s, ff = divmod(int(frame), basis)
    m, ss = divmod(s, 60)
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def frame_aus_timecode(tc: str, fps: float) -> int:
    teile = str(tc).strip().split(":")
    if len(teile) != 4 or not all(t.isdigit() for t in teile):
        raise ReviewFehler(f"Timecode „{tc}“: erwartet HH:MM:SS:FF.", 1)
    h, m, s, ff = (int(t) for t in teile)
    basis = max(1, int(round(float(fps))))
    return ((h * 60 + m) * 60 + s) * basis + ff
