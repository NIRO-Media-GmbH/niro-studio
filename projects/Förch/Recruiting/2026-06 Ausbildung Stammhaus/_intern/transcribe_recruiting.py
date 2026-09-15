"""Förch Recruiting (Ausbildung, Dreh 30.06.2026) — selektive Transkription.

Ton-Kamera Interviews = a7MK4 (per Pegelmessung verifiziert; C-Cam nur Scratch).
Video spezifisch = FX3-Einzelcam (Hooks/Szenen/1W1B). Keine B-Roll, keine
Proxies, keine Actioncam. Originale auf dem NAS werden NUR GELESEN.
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
    "Förch GmbH & Co. KG/02_Projekte/03_30.05.26/03_Medien/01_Footage/Sortiert"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Förch/Recruiting/"
    "2026-06 Ausbildung Stammhaus"
)

# Interviews: NUR die a7MK4-Ton-Kamera (C-Cam hat kein Mikro-Signal)
INTERVIEWS = [
    ("Alisa_Duales Studium Logistik", "a7MK4_20260630_9958.MP4", "Alisa"),
    ("Emili_Ausbildung Kaufmännisch", "a7MK4_20260630_9962.MP4", "Emili"),
    ("Fabian_Duales Studium Kaufmännisch", "a7MK4_20260630_9961.MP4", "Fabian"),
    ("Luis_Duales Studium IT", "a7MK4_20260630_9964.MP4", "Luis"),
    ("Mia_Ausbildung IT", "a7MK4_20260630_9963.MP4", "Mia"),
    ("Mia_Ausbildung IT", "a7MK4_20260630_9965.MP4", "Mia"),
    ("Tobias_Ausbildung Logistik", "a7MK4_20260630_9959.MP4", "Tobias"),
]


def collect() -> list[dict]:
    out = []
    for folder, fname, person in INTERVIEWS:
        p = FOOTAGE / "Interviews" / folder / fname
        out.append({"path": p, "kategorie": f"Interviews/{folder}",
                    "person": person})
    vs = FOOTAGE / "Video spezifisch"
    for p in sorted(vs.rglob("*.MP4")):
        if "Proxy" in p.parts:
            continue
        rel = p.parent.relative_to(vs)
        out.append({"path": p, "kategorie": f"Video spezifisch/{rel}",
                    "person": "unbekannt"})
    return out


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    todo = collect()
    print(f"{len(todo)} Clips zu transkribieren", flush=True)
    index = []
    for i, item in enumerate(todo, 1):
        p = item["path"]
        clip = Clip(path=p, camera=item["kategorie"], sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "standort": "Stammhaus Neuenstadt", "kategorie": item["kategorie"],
            "person": item["person"], "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers,
                        "text": t.text})
            print(f"{i}/{len(todo)} OK   {rec['kategorie']}/{p.name} "
                  f"({rec['n_words']} Wörter)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(todo)} FEHLER {p.name}: {rec['error']}", flush=True)
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
