"""Förch Messevideos — selektive Transkription der gesprochenen Takes.

Nur die 6 FX3-Clips aus 'Gesprochene Takes' (SSD NIRO-SSD-02). Keine B-Roll,
kein Timelapse. Originale werden nur gelesen.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

# .env laden (nur ELEVENLABS_API_KEY nötig)
import os
for line in (TOOL / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip, find_sidecar
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip

FOOTAGE = Path(
    "/Volumes/NIRO-SSD-02/05_Förch Messestand Schwarz Gruppe/03_Medien/01_Footage"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Förch/Messevideos/2026-07 Messestand Schwarz Gruppe"
)
SCAN_DIRS = ["Gesprochene Takes"]


def collect() -> list[dict]:
    out = []
    for rel in SCAN_DIRS:
        base = FOOTAGE / rel
        for p in sorted(base.glob("FX3_*.MP4")):
            out.append({"path": p, "standort": "Messestand", "kategorie": rel,
                        "person": "unbekannt"})
    return out


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    todo = collect()
    print(f"{len(todo)} FX3-Clips gefunden", flush=True)
    index = []
    for i, item in enumerate(todo, 1):
        p = item["path"]
        clip = Clip(path=p, camera=f'{item["kategorie"]}',
                    sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "standort": item["standort"], "kategorie": item["kategorie"],
            "person": item["person"], "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers, "text": t.text})
            print(f"{i}/{len(todo)} OK   {p.name} "
                  f"({rec['n_words']} Wörter, {len(speakers)} Sprecher)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(todo)} FEHLER {p.name}: {rec['error']}", flush=True)
        finally:
            wav = work / f"{p.stem}.wav"
            if wav.exists():
                wav.unlink()
        index.append(rec)
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for r in index if r.get("ok"))
    print(f"FERTIG: {n_ok}/{len(index)} ok → {index_path}", flush=True)


if __name__ == "__main__":
    main()
