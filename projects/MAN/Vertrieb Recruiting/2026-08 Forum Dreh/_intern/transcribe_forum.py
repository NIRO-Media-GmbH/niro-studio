"""MAN Vertrieb Recruiting — Forum-Dreh 04.08.2026 — selektive Transkription.

BEIDE Kameras pro Interview (David-Regel 2026-08-07):
- FX3   = Ton-Kamera (Freigabe David 2026-08-15) → Zitate + Timecodes.
- a7MK4 = Raum/Interviewer besser hörbar → Kontext, Wer-ist-wer.
Kameras laufen versetzt — Timecodes NICHT übertragbar, jede Kamera eigene
Positionen. Originale auf der SSD werden NUR GELESEN.
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

FOOTAGE = Path("/Volumes/NIRO-SSD-03/MAN Forum")
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/MAN/Vertrieb Recruiting/"
    "2026-08 Forum Dreh"
)

# (Person/Ordner, Datei, Kamera-Rolle)
INTERVIEWS = [
    ("Viktoria - Verkäuferin", "FX3_0543.MP4", "ton"),
    ("Viktoria - Verkäuferin", "FX3_0544.MP4", "ton"),
    ("Viktoria - Verkäuferin", "a7MK4_20260804_0011.MP4", "kontext"),
    ("Viktoria - Verkäuferin", "a7MK4_20260804_0012.MP4", "kontext"),
    ("Esta - Verkaufsleitung", "FX3_0545.MP4", "ton"),
    ("Esta - Verkaufsleitung", "a7MK4_20260804_0013.MP4", "kontext"),
    ("Roman - Verkäufer", "FX3_0546.MP4", "ton"),
    ("Roman - Verkäufer", "a7MK4_20260804_0014.MP4", "kontext"),
    ("Trainee Programm", "FX3_0547.MP4", "ton"),
    ("Trainee Programm", "a7MK4_20260804_0015.MP4", "kontext"),
    # Kurzer Nachschuss nur auf a7MK4 (50 s, kein FX3-Gegenstück):
    ("Trainee Programm", "a7MK4_20260804_0622.MP4", "kontext"),
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
            "standort": "MAN Truck/Bus Forum",
            "kategorie": f"Interviews/{person}",
            "person": person.split(" - ")[0],
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
