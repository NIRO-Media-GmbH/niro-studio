"""MEK — Nachtranskription der a7MK4-Interview-Clips (Kontext-Kamera).

Die Charge wurde am 22.07. nur FX3-seitig transkribiert; die David-Regel
„beide Kameras transkribieren" (2026-08-07) kam danach. Dieser Runner holt
die a7MK4-Seite nach: FX3 bleibt Ton-/Timecode-Referenz (kamera_rolle=ton,
David-Bestätigung 22.07.), a7MK4 = kontext (Interviewer/Raum, Wer-ist-wer).
Timecodes der beiden Kameras sind NICHT übertragbar (unterschiedliche Starts).

Erweitert transcripts_index.json (Backfill kamera_rolle=ton auf Bestand,
Append der a7-Einträge, idempotent bei Wiederholung). Originale nur lesen.
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
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Marien-Elisabeth-Kliniken Kassel gGmbH/02_Projekte/"
    "01_Projekt-2xAds1xImagefilm_24.06.26/03_Medien/01_Footage"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/"
    "Recruiting/2026-07 Erster Dreh"
)
SCAN_DIRS = [
    "Standort 1/Sortiert/Interviews",
    "Standort 2/Sortiert/Interviews",
]


def collect() -> list[dict]:
    out = []
    for rel in SCAN_DIRS:
        base = FOOTAGE / rel
        for p in sorted(base.rglob("a7MK4_*.MP4")):
            parts = p.relative_to(FOOTAGE).parts
            standort, kategorie = parts[0], parts[2]
            person = parts[3] if len(parts) > 4 else kategorie
            out.append({"path": p, "standort": standort,
                        "kategorie": kategorie, "person": person})
    return out


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    index = json.loads(index_path.read_text(encoding="utf-8"))
    for rec in index:
        rec.setdefault("kamera_rolle", "ton")
    done = {rec["name"] for rec in index}

    todo = [it for it in collect() if it["path"].name not in done]
    print(f"{len(todo)} a7MK4-Clips zu transkribieren "
          f"(Index hat {len(index)} Bestandseinträge)", flush=True)

    for i, item in enumerate(todo, 1):
        p = item["path"]
        clip = Clip(path=p,
                    camera=f'{item["standort"]}/{item["kategorie"]}/{item["person"]}',
                    sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "standort": item["standort"], "kategorie": item["kategorie"],
            "person": item["person"], "kamera_rolle": "kontext",
            "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers,
                        "text": t.text})
            print(f"{i}/{len(todo)} OK   [{clip.camera}] {p.name} "
                  f"({rec['n_words']} Wörter, {len(speakers)} Sprecher)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(todo)} FEHLER [{clip.camera}] {p.name}: {rec['error']}",
                  flush=True)
        finally:
            wav = work / f"{p.stem}.wav"
            if wav.exists():
                wav.unlink()
        index.append(rec)
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    n_ok = sum(1 for r in index if r.get("ok"))
    print(f"FERTIG: {n_ok}/{len(index)} ok → {index_path}", flush=True)


if __name__ == "__main__":
    main()
