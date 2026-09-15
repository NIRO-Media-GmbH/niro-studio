"""Craiss Generation Logistik — Recruiting-Videos, Dreh 10.08.2026.

Selektive Transkription der Interview-Clips (NUR Interviews/, keine B-Roll).

BEIDE Kameras pro Interview (David-Regel 2026-08-07):
- FX3   = Ton-Kamera (David bestätigt 12.08.2026) -> Zitate + Timecodes für den Cutter.
- a7MK4 = Kontext-Kamera (Raum/Interviewer besser hörbar) -> Wer-ist-wer, nie Tonquelle.
Timecodes NICHT zwischen den Kameras übertragbar — beide Kameras laufen
zeitversetzt (eigene Start-/Stopp-Punkte, siehe XML-CreationDate).

Originale auf dem NAS werden NUR GELESEN.
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

FOOTAGE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Craiss Generation Logistik GmbH & Co. KG/02_Projekte/01_Projekt-4 Ads/"
    "03_Medien/01_Footage/Sortiert/Interviews"
)
PROJECT = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh")


def kamera_rolle(name: str) -> str:
    return "ton" if name.startswith("FX3") else "kontext"


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(parents=True, exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clips = sorted(
        (p for p in FOOTAGE.rglob("*.MP4") if p.is_file()),
        key=lambda p: (str(p.parent.relative_to(FOOTAGE)), p.name),
    )

    # Bereits transkribierte Ergebnisse behalten (Wiederaufnahme nach Abbruch)
    index = []
    done = set()
    if index_path.exists():
        index = json.loads(index_path.read_text())
        done = {r["path"] for r in index if r.get("ok")}

    for i, p in enumerate(clips, 1):
        if str(p) in done:
            print(f"{i}/{len(clips)} SKIP {p.name} (bereits im Index)", flush=True)
            continue
        vorordner = str(p.parent.relative_to(FOOTAGE))
        vorordner = "" if vorordner == "." else vorordner
        clip = Clip(path=p, camera=vorordner, sidecar=find_sidecar(p))
        rec = {
            "name": p.name,
            "path": str(p),
            "vorordner": vorordner,          # bestehende Grob-Sortierung (GF/HR/"")
            "kategorie": "Interviews",
            "person": None,                   # wird nach Analyse gefüllt
            "kamera": "FX3" if p.name.startswith("FX3") else "a7MK4",
            "kamera_rolle": kamera_rolle(p.name),
            "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({
                "ok": True,
                "duration_s": round(t.duration(), 1),
                "n_words": len(t.words),
                "speakers": speakers,
                "text": t.text,
            })
            print(f"{i}/{len(clips)} OK   {vorordner or '-'}/{p.name} "
                  f"[{rec['kamera_rolle']}] ({rec['n_words']} Wörter, "
                  f"{len(speakers)} Sprecher)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(clips)} FEHLER {p.name}: {rec['error']}", flush=True)

        index = [r for r in index if r["path"] != str(p)] + [rec]
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    ok = sum(1 for r in index if r.get("ok"))
    print(f"\nFERTIG: {ok}/{len(clips)} Clips transkribiert -> {index_path}")


if __name__ == "__main__":
    main()
