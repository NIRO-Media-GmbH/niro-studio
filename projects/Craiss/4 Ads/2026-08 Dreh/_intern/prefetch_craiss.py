"""Cache-Vorfüller — arbeitet dieselbe Clip-Liste RÜCKWÄRTS ab.

Läuft parallel zu transcribe_craiss.py. Schreibt NUR in den Scribe-Cache
(pro Fingerprint eine Datei), NIE in transcripts_index.json — dadurch kein
Schreib-Konflikt mit dem Hauptlauf. Der Hauptlauf holt die vorgefüllten
Clips danach als Cache-Treffer in Sekunden ab.

Eigenes work_dir, damit sich die WAV-Zwischendateien nicht in die Quere kommen.
"""
from __future__ import annotations

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

FOOTAGE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Craiss Generation Logistik GmbH & Co. KG/02_Projekte/01_Projekt-4 Ads/"
    "03_Medien/01_Footage/Sortiert/Interviews"
)
PROJECT = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh")


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work_prefetch"
    work.mkdir(parents=True, exist_ok=True)
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clips = sorted(
        (p for p in FOOTAGE.rglob("*.MP4") if p.is_file()),
        key=lambda p: (str(p.parent.relative_to(FOOTAGE)), p.name),
    )
    clips.reverse()

    for i, p in enumerate(clips, 1):
        fp = clip_fingerprint(p)
        if cache.load(fp, "scribe") is not None:
            print(f"{i}/{len(clips)} CACHE {p.name}", flush=True)
            continue
        vorordner = str(p.parent.relative_to(FOOTAGE))
        clip = Clip(path=p, camera="" if vorordner == "." else vorordner,
                    sidecar=find_sidecar(p))
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            print(f"{i}/{len(clips)} OK    {p.name} ({len(t.words)} Wörter)", flush=True)
        except Exception as e:
            print(f"{i}/{len(clips)} FEHLER {p.name}: {type(e).__name__}: {e}", flush=True)

    print("\nPREFETCH FERTIG")


if __name__ == "__main__":
    main()
