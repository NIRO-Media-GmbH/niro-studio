"""MEK Recruiting — Video 3 „Intensiv ist nicht gleich Intensiv": fertigen Schnitt transkribieren.

Grundlage: `~/Downloads/vids 2/3 - Intensiv ist nicht gleich Intensiv.mp4`
(Cutter-Schnitt vom 07.08., 64,0 s, 2160×3840, 25 fps). Kunden-Feedback 11.09.
bezieht sich auf Schnitt-Timecodes (Cardiac Arrest Center 0:19–0:31 raus,
Einstieg durch Pflege statt Chefarzt) — dafür Wort-Timecodes des Schnitts.

Gleiche Pipeline wie transcribe_mek.py: ElevenLabs Scribe, Cache in
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
    "/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh"
)
MP4 = Path.home() / "Downloads" / "vids 2" / "3 - Intensiv ist nicht gleich Intensiv.mp4"


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(parents=True, exist_ok=True)
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clip = Clip(path=MP4, camera="V3-Schnitt", sidecar=find_sidecar(MP4))
    t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)

    out = intern / "schnitt_v3_scribe_words.json"
    out.write_text(json.dumps(t.to_dict(), ensure_ascii=False, indent=2))

    print(f"Fingerprint: {clip_fingerprint(MP4)}")
    print(f"Dauer: {t.duration():.1f}s, {len(t.words)} Wörter")
    print(f"Sprecher: {sorted({w.speaker for w in t.words if w.speaker})}")
    print("--- SÄTZE (Schnitt-Timecodes) ---")
    seg, start, spk = [], None, None
    for w in t.words:
        if w.text.strip() == "":
            continue
        if start is None:
            start, spk = w.start, w.speaker
        seg.append(w.text.strip())
        if w.text.strip()[-1:] in ".?!":
            print(f"[{start:5.1f}–{w.end:5.1f}] {spk}: {' '.join(seg)}")
            seg, start = [], None
    if seg:
        print(f"[{start:5.1f}–end] {spk}: {' '.join(seg)}")


if __name__ == "__main__":
    main()
