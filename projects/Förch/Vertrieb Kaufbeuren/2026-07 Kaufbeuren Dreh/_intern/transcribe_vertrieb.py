"""Förch Vertrieb Kaufbeuren (Dreh 09.07.2026) — selektive Transkription.

BEIDE Kameras pro Interview (David-Regel 2026-08-07):
- FX3  = Ton-Kamera (Mikro 100 %) → Zitate + Timecodes für den Cutter.
- a7MK4 = Raum/Interviewer besser hörbar → Kontext, Wer-ist-wer.
FX3 läuft je ~0,5–5 s länger (früher gestartet) — Timecodes NICHT übertragbar,
jede Kamera hat eigene Positionen. Originale auf dem NAS werden NUR GELESEN.
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
    "Förch GmbH & Co. KG/02_Projekte/04_2026.07.09 Kaufbeuren Vertrieb/"
    "Footage Sortiert"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Förch/Vertrieb Kaufbeuren/"
    "2026-07 Kaufbeuren Dreh"
)

# (Person, Datei, Kamera-Rolle)
INTERVIEWS = [
    ("Adriano", "FX3_0078.MP4", "ton"),
    ("Adriano", "a7MK4_20260709_9973.MP4", "kontext"),
    ("Franzi", "FX3_0079.MP4", "ton"),
    ("Franzi", "a7MK4_20260709_9974.MP4", "kontext"),
    ("Friedrich", "FX3_0080.MP4", "ton"),
    ("Friedrich", "a7MK4_20260709_9975.MP4", "kontext"),
    ("Thomas", "FX3_0081.MP4", "ton"),
    ("Thomas", "a7MK4_20260709_9976.MP4", "kontext"),
]


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    index = []
    for i, (person, fname, rolle) in enumerate(INTERVIEWS, 1):
        p = FOOTAGE / "Interviews" / person / fname
        clip = Clip(path=p, camera=f"Interviews/{person}", sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "standort": "Niederlassung Kaufbeuren",
            "kategorie": f"Interviews/{person}", "person": person,
            "kamera_rolle": rolle, "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers,
                        "text": t.text})
            print(f"{i}/{len(INTERVIEWS)} OK   {person}/{p.name} [{rolle}] "
                  f"({rec['n_words']} Wörter)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(INTERVIEWS)} FEHLER {p.name}: {rec['error']}",
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
