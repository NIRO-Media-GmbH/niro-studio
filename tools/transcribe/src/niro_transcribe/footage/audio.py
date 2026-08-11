from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def extract_audio(video_path: str | Path, out_dir: str | Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg nicht gefunden (im PATH installieren, z. B. brew install ffmpeg)")
    video = Path(video_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{video.stem}.wav"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn",
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not target.exists():
        raise RuntimeError(f"ffmpeg-Audioextraktion fehlgeschlagen für {video.name}: {proc.stderr[-500:]}")
    return target
