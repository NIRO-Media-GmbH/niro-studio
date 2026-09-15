#!/usr/bin/env python
"""Transkribiert die Audio-Spur des finalen 9:16-Schnitts (Basis fürs 16:9-Master).

Aufruf: tools/transcribe/venv/bin/python transcribe_final.py {scribe|whisper}
Output: transcript.<engine>.json (Transcript.to_dict-Format, Wort-Timestamps)
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[5]
sys.path.insert(0, str(STUDIO / "tools/transcribe/src"))


def load_env(path: Path) -> None:
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_env(STUDIO / "tools/transcribe/.env")
    engine = sys.argv[1]
    if engine == "scribe":
        from niro_transcribe.transcribe.elevenlabs import transcribe_scribe

        transcript = transcribe_scribe(
            HERE / "final-audio-48k.wav",
            os.environ["ELEVENLABS_API_KEY"],
            diarize=True,
        )
    elif engine == "whisper":
        from niro_transcribe.transcribe.whisper import transcribe_whisper

        transcript = transcribe_whisper(
            HERE / "final-audio-16k.wav",
            os.environ.get("NIRO_WHISPER_MODEL", "large-v3"),
        )
    else:
        sys.exit(f"Unbekannte Engine: {engine!r} (scribe|whisper)")

    out = HERE / f"transcript.{engine}.json"
    out.write_text(json.dumps(transcript.to_dict(), ensure_ascii=False, indent=1))
    print(f"{engine}: {len(transcript.words)} Wörter, {transcript.duration():.1f}s -> {out}")


if __name__ == "__main__":
    main()
