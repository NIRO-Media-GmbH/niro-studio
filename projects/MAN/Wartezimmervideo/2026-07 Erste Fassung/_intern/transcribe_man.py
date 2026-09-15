"""MAN Wartezimmervideo — selektive Transkription der freigegebenen Interviews.

Clip-Liste kommt aus _intern/interview-kandidaten.md: Zeilen mit [OK]
(plus [OK?], wenn --include-fragezeichen gesetzt ist — Dreh-01-Takes nach
Sample-Check). Originale auf dem NAS werden nur gelesen.

Aufruf:
  transcribe_man.py [--limit N] [--only SUBSTRING] [--include-fragezeichen]
"""
from __future__ import annotations

import argparse
import json
import re
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

NAS = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "MAN Truck and Bus/02_Projekte"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung"
)


def person_from_path(rel: Path) -> str:
    """Bester Personen-Hinweis aus dem Pfad (endgültige Klärung via Selbstvorstellung)."""
    m = re.search(r"\d+_Interview ([^/]+)", str(rel))
    if m:
        return m.group(1)  # z. B. "Julia NFZ", "Markus Chef"
    return rel.parent.name  # z. B. "Interviews", "01 Cam - A7iv - Jan"


def collect(include_fragezeichen: bool) -> list[dict]:
    md = (PROJECT / "_intern" / "interview-kandidaten.md").read_text()
    marks = ("| [OK] |", "| [OK?] |") if include_fragezeichen else ("| [OK] |",)
    out = []
    for line in md.splitlines():
        if not line.startswith(marks):
            continue
        m = re.search(r"`([^`]+)`", line)
        if not m:
            continue
        rel = Path(m.group(1))
        out.append({
            "path": NAS / rel,
            "dreh": rel.parts[0],
            "person": person_from_path(rel),
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--include-fragezeichen", action="store_true")
    args = ap.parse_args()

    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    todo = collect(args.include_fragezeichen)
    if args.only:
        todo = [t for t in todo if args.only in str(t["path"])]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} Clips zu transkribieren", flush=True)

    index = []
    if index_path.exists():
        index = json.loads(index_path.read_text())
        done = {r["path"] for r in index if r.get("ok")}
        todo = [t for t in todo if str(t["path"]) not in done]
        print(f"{len(done)} bereits im Index, {len(todo)} offen", flush=True)

    for i, item in enumerate(todo, 1):
        p = item["path"]
        clip = Clip(path=p, camera=f'{item["dreh"]}/{item["person"]}',
                    sidecar=find_sidecar(p))
        rec = {
            "name": p.name, "path": str(p),
            "standort": item["dreh"], "kategorie": "interview",
            "person": item["person"], "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers, "text": t.text})
            print(f"{i}/{len(todo)} OK   [{clip.camera}] {p.name} "
                  f"({rec['n_words']} Wörter, {len(speakers)} Sprecher)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(todo)} FEHLER [{clip.camera}] {p.name}: {rec['error']}", flush=True)
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
