"""Medien-Metadaten (ffprobe), Proxy-Suche, Format/Rotation, Fingerprint, Audio-Extraktion.

Alle Funktionen lesen die Originale nur. Geschrieben wird ausschließlich in
``extract_audio_16k`` — und dort nie unter /Volumes/ (NAS).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from niro_transcribe.footage.transcribe_clips import clip_fingerprint  # nur Import, keine Änderung

from .charge import AutoCutError

PROXY_DIR = "Proxy"
PROXY_EXTS = (".mov", ".mp4", ".MOV", ".MP4")
NAS_ROOT_PARTS = ("/", "Volumes")


@dataclass
class MediaInfo:
    """Kennzahlen einer Videodatei, wie ffprobe sie liefert (Rotation als 0/90/180/270)."""
    path: str
    duration_s: float
    fps: float
    width: int
    height: int
    rotation: int
    nb_frames: int
    timecode: str | None
    has_audio: bool
    sample_rate: int
    channels: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MediaInfo":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__})


# --- Hilfen -------------------------------------------------------------

def _which(name: str) -> str:
    p = shutil.which(name)
    if not p:
        raise AutoCutError(f"{name} nicht gefunden (brew install ffmpeg).")
    return p


def _fps(s: str) -> float:
    """„25/1" → 25.0, „30000/1001" → 29.97, „0/0" → 0.0."""
    if "/" in s:
        n, d = s.split("/", 1)
        return round(int(n) / int(d), 3) if int(d) else 0.0
    return float(s or 0)


def _assert_not_nas(path: Path, zweck: str) -> None:
    """Schreibziele unter /Volumes/ (NAS, externe SSDs) sind tabu."""
    p = path.expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if p.parts[:2] == NAS_ROOT_PARTS:
        raise AutoCutError(f"{zweck} verweigert: {p}\nAutoCut schreibt nie auf das NAS oder externe "
                           f"Volumes — Arbeitsdateien gehören nach <Charge>/_intern/autocut/work.")


# --- ffprobe ------------------------------------------------------------

def _parse_probe(path: str, data: dict) -> MediaInfo:
    """ffprobe-JSON (-show_format -show_streams) in MediaInfo übersetzen."""
    streams = data.get("streams", []) or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    if v is None:
        raise AutoCutError(f"Kein Videostream in {path}")
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fps = _fps(v.get("avg_frame_rate") or "0/1") or _fps(v.get("r_frame_rate") or "0/1")
    duration = float((data.get("format") or {}).get("duration") or v.get("duration") or 0.0)
    rotation = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rotation = abs(int(round(float(sd["rotation"])))) % 360
    if not rotation and (v.get("tags") or {}).get("rotate"):
        rotation = abs(int(v["tags"]["rotate"])) % 360
    nb = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else round(duration * fps)
    tc = None
    for s in streams:
        t = (s.get("tags") or {}).get("timecode")
        if t:
            tc = t
            break
    if tc is None:
        tc = ((data.get("format") or {}).get("tags") or {}).get("timecode")
    return MediaInfo(path=str(path), duration_s=duration, fps=fps, width=int(v.get("width", 0)),
                     height=int(v.get("height", 0)), rotation=rotation, nb_frames=nb, timecode=tc,
                     has_audio=a is not None, sample_rate=int((a or {}).get("sample_rate", 0) or 0),
                     channels=int((a or {}).get("channels", 0) or 0))


def ffprobe(path: str | Path) -> MediaInfo:
    """Metadaten einer Videodatei lesen (nur Header, auch bei großen NAS-Dateien schnell)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise AutoCutError(f"ffprobe fehlgeschlagen für {p.name}: {r.stderr[-300:]}")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise AutoCutError(f"ffprobe lieferte kein JSON für {p.name}: {e}") from e
    return _parse_probe(str(p), data)


# --- Proxy, Fingerprint -------------------------------------------------

def proxy_for(path: str | Path) -> Path | None:
    """Proxy-Datei neben dem Original: <dir>/Proxy/<stem>.mov (oder .mp4), sonst None."""
    p = Path(path)
    for ext in PROXY_EXTS:
        cand = p.parent / PROXY_DIR / (p.stem + ext)
        if cand.is_file():
            return cand
    return None


def fingerprint(path: str | Path) -> str:
    """Derselbe Fingerprint wie im Transkript-Cache von niro_transcribe (Name, Größe, mtime)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    return clip_fingerprint(p)


# --- Format -------------------------------------------------------------

def is_portrait(info: MediaInfo) -> bool:
    """Hochkant, wenn die Datei liegend gespeichert und um 90/270° gedreht ist — oder stehend gespeichert."""
    if info.rotation in (90, 270):
        return info.width >= info.height
    return info.height > info.width


def timeline_format(info: MediaInfo) -> dict:
    """Timeline-Format aus der Datei: fps, Breite/Höhe nach Rotation, Orientierung 16:9 oder 9:16."""
    w, h = info.width, info.height
    if info.rotation in (90, 270):
        w, h = h, w
    return {"fps": info.fps, "width": w, "height": h, "orientation": "9:16" if h > w else "16:9"}


def check_proxy_match(orig: MediaInfo, proxy: MediaInfo, tol_frames: int = 1) -> list[str]:
    """Bildrate muss gleich sein, Frame-Zahl darf höchstens tol_frames abweichen (Spec 3.1)."""
    probs: list[str] = []
    if abs(orig.fps - proxy.fps) > 0.01:
        probs.append(f"Bildrate weicht ab: Original {orig.fps} / Proxy {proxy.fps}")
    if abs(orig.nb_frames - proxy.nb_frames) > tol_frames:
        probs.append(f"Frames weichen ab: Original {orig.nb_frames} / Proxy {proxy.nb_frames}")
    return probs


# --- Frames -------------------------------------------------------------

def seconds_to_frames(s: float, fps: float) -> int:
    return int(round(s * fps))


def frames_to_seconds(f: int, fps: float) -> float:
    return round(f / fps, 3)


# --- Audio --------------------------------------------------------------

def extract_audio_16k(src: str | Path, out_dir: str | Path, sr: int = 16000) -> Path:
    """Mono-WAV aus dem ORIGINAL (lesend), gecacht per Fingerprint im out_dir.

    out_dir ist vom Aufrufer auf <Charge>/_intern/autocut/work zu legen; unter /Volumes/ wird verweigert.
    """
    src = Path(src)
    out_dir = Path(out_dir)
    _assert_not_nas(out_dir, "Audio-Extraktion")
    if not src.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {src}\nIst das NAS gemountet?")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{src.stem}.{fingerprint(src)[:12]}.wav"
    if target.exists() and target.stat().st_size > 1000:
        return target
    # Erst in eine .part-Datei schreiben und nur bei Erfolg umbenennen: ein abgebrochener ffmpeg-Lauf
    # (Ctrl-C, NAS-Abriss) darf keine halbe WAV hinterlassen, die beim nächsten Aufruf als Cache-Treffer gilt.
    part = target.with_name(target.name + ".part")
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vn",
           "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", "-f", "wav", str(part)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not part.exists():
            raise AutoCutError(f"Audio-Extraktion fehlgeschlagen für {src.name}: {r.stderr[-300:]}")
        os.replace(part, target)
    finally:
        part.unlink(missing_ok=True)
    return target
