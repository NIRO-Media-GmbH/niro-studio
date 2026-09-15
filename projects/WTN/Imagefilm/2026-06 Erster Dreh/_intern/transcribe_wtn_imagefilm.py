"""WTN Imagefilm (B2B) — selektive Transkription der Ton-Kamera-Clips.

Explizite Clip-Liste: Ton-Kamera wurde pro Ordner per Audio-Level-Check
bestimmt (2026-08-03, s. script_structured.json hinweise). Azubi-/Ausbilder-
Interviews bewusst ausgelassen (Recruiting-Content, nicht B2B).
Originale werden nur gelesen.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

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
    "/Volumes/NIRO-SSD-02/WTN/01_Projekt-Dreh_09.06.26/03_Medien/01_Footage"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/WTN/Imagefilm/2026-06 Erster Dreh"
)

# (relativer Pfad, kategorie, person)
CLIPS = [
    ("Video Spezifisch/Imagefilm/Sprechpart01/C8092.MP4",
     "Sprechpart", "Sprechpart01 (Sprecher tbd)"),
    ("Video Spezifisch/Imagefilm/Sprechpart02/a7MK4_20260609_9684.MP4",
     "Sprechpart", "Sprechpart02 (Sprecher tbd)"),
    ("Interviews/Interview_Technischer Vertrieb_Markus/a7MK4_20260609_9683.MP4",
     "Interview", "Technischer Vertrieb Markus"),
    ("Interviews/Interview_Technischer Vertrieb_Roland/a7MK4_20260609_9685.MP4",
     "Interview", "Technischer Vertrieb Roland"),
    ("Interviews/Interview_Produktionsleiter/C0686.MP4",
     "Interview", "Produktionsleiter Dirk Wetzel"),
    ("Interviews/Interview_Teamleiter/a7MK4_20260609_9681.MP4",
     "Interview", "Teamleiter Eduard Weber"),
]

def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    print(f"{len(CLIPS)} Clips in der Liste", flush=True)
    index = []
    for i, (rel, kategorie, person) in enumerate(CLIPS, 1):
        p = FOOTAGE / rel
        clip = Clip(path=p, camera=f"{kategorie}/{person}", sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "kategorie": kategorie, "person": person,
            "ordner": p.parent.name,
            "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers, "text": t.text})
            print(f"{i}/{len(CLIPS)} OK   [{clip.camera}] {p.name} "
                  f"({rec['n_words']} Wörter, {len(speakers)} Sprecher)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(CLIPS)} FEHLER [{clip.camera}] {p.name}: {rec['error']}", flush=True)
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
