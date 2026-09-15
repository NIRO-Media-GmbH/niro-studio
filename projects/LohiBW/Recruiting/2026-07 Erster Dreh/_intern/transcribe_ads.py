#!/usr/bin/env python3
"""
Transkribiert die vier fertig geschnittenen LohiBW-Ads mit Wort-Zeitstempeln.

Grundlage für die Untertitel-Animation: gebraucht werden exakte Wort-Timings
gegen die Timeline des fertigen Schnitts (nicht gegen das Rohmaterial).

Aufruf aus der Studio-Wurzel:
    tools/transcribe/venv/bin/python "<dieser Pfad>"
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]          # NIRO Studio
CHARGE = Path(__file__).resolve().parents[1]        # …/2026-07 Erster Dreh
VIDEO_DIR = CHARGE / "Material" / "Video"
OUT = CHARGE / "_intern" / "ad_transcripts"
WORK = CHARGE / "_intern" / "work" / "ad_audio"

sys.path.insert(0, str(ROOT / "tools" / "transcribe" / "src"))
from niro_transcribe.transcribe.elevenlabs import transcribe_scribe  # noqa: E402


def load_key() -> str:
    env = ROOT / "tools" / "transcribe" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("ELEVENLABS_API_KEY fehlt in tools/transcribe/.env")


def extract_audio(mp4: Path) -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    wav = WORK / (mp4.stem + ".wav")
    if wav.exists():
        return wav
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(mp4),
         "-vn", "-ac", "1", "-ar", "16000", "-y", str(wav)],
        check=True,
    )
    return wav


def main() -> None:
    key = load_key()
    OUT.mkdir(parents=True, exist_ok=True)
    mp4s = sorted(VIDEO_DIR.glob("Video *.mp4"))
    if not mp4s:
        raise SystemExit(f"Keine Videos in {VIDEO_DIR}")

    for mp4 in mp4s:
        target = OUT / (mp4.stem + ".json")
        if target.exists():
            print(f"[skip] {mp4.name} (Transkript liegt schon vor)", flush=True)
            continue
        print(f"[audio] {mp4.name}", flush=True)
        wav = extract_audio(mp4)
        print(f"[scribe] {mp4.name} …", flush=True)
        tr = transcribe_scribe(wav, key, diarize=True)
        target.write_text(
            json.dumps(tr.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[ok] {mp4.name}: {len(tr.words)} Wörter, "
              f"{tr.duration():.1f}s -> {target.name}", flush=True)

    print("\nFERTIG", flush=True)


if __name__ == "__main__":
    main()
