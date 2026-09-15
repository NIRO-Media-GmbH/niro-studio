"""Setzer — Video 4 „Fleischsalat Zutaten": fertigen Schnitt transkribieren.

Grundlage: `Video 4 zum Transkribieren/04 - Fleischsalat Zutaten.mp4`
(Audio-Export des Schnitts, AAC 48 kHz, kein Videostream, 131,8 s).
Die mitgelieferte Premiere-UT-SRT ist unbrauchbar (Verhörer, japanische
Halluzinationen ab ~35 s) und wird durch eine Scribe-Wort-SRT ersetzt.

Gleiche Pipeline wie transcribe_setzer.py: ElevenLabs Scribe, Cache in
_intern/cache, Quelldatei wird nur gelesen.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

for line in (TOOL / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip, find_sidecar
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip

PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Setzer/Social-Reels/2026-08 Dreh 18.08"
)
MP4 = PROJECT / "Video 4 zum Transkribieren" / "04 - Fleischsalat Zutaten.mp4"


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(parents=True, exist_ok=True)
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clip = Clip(path=MP4, camera="04-Schnitt", sidecar=find_sidecar(MP4))
    t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)

    out = intern / "video4_scribe_words.json"
    out.write_text(json.dumps(t.to_dict(), ensure_ascii=False, indent=2))

    print(f"Fingerprint: {clip_fingerprint(MP4)}")
    print(f"Dauer: {t.duration():.1f}s, {len(t.words)} Wörter")
    print(f"Sprecher: {sorted({w.speaker for w in t.words if w.speaker})}")
    print("--- TEXT ---")
    print(t.text)


if __name__ == "__main__":
    main()
