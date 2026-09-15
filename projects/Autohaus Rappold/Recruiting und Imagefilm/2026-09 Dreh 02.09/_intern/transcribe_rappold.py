"""Autohaus Rappold — Recruiting-Videos + Imagefilm, Dreh 02.09.2026.

Selektive Transkription: NUR Interviews/* und „Schlüsselbox Carlo/"
(keine B-Roll, keine Drohne).

BEIDE Kameras pro Interview (David-Regel 2026-08-07). Welche Kamera die
Ton-Kamera ist, wird beim User erfragt und danach im Index als
kamera_rolle (ton|kontext) nachgetragen — hier noch „offen".
Timecodes NICHT zwischen den Kameras übertragbar (eigene Start-/Stopp-
Punkte; FX3-Uhr läuft laut creation_time ~8 min vor der a7MK4).

Drei Worker parallel, jeder schreibt nur seinen Cache-Eintrag (pro
Fingerprint eine Datei); der Index wird unter Lock geschrieben.
Wiederaufnahme: Cache-Treffer kommen in Sekunden zurück.

Originale auf dem NAS werden NUR GELESEN.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    "Autohaus Rappold GmbH/02_Projekte/01_Dreh_2026.09 Image & Ads, Schlüsselbox/"
    "03_Medien/01_Footage"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Autohaus Rappold/"
    "Recruiting und Imagefilm/2026-09 Dreh 02.09"
)
ORDNER = ["Interviews", "Schlüsselbox Carlo"]


def meta(p: Path) -> dict:
    rel = p.relative_to(FOOTAGE)
    if rel.parts[0] == "Interviews":
        ordner = rel.parts[1]                      # „Michael - Serviceberater"
        person, _, ordner_rolle = ordner.partition(" - ")
        kategorie = f"Interviews/{ordner}"
    else:
        ordner = rel.parts[0]                      # „Schlüsselbox Carlo"
        person, ordner_rolle = "Carlo", None
        kategorie = ordner
    return {
        "kategorie": kategorie,
        "person": person.strip(),
        "ordner_rolle": ordner_rolle,
        "kamera": "FX3" if p.name.startswith("FX3") else "a7MK4",
        "kamera_rolle": "offen",
    }


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(parents=True, exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clips = [p for o in ORDNER for p in (FOOTAGE / o).rglob("*.MP4") if p.is_file()]
    clips.sort(key=lambda p: -p.stat().st_size)    # lange Clips zuerst

    index: dict[str, dict] = {}
    if index_path.exists():
        index = {r["path"]: r for r in json.loads(index_path.read_text())}
    lock = threading.Lock()

    def job(p: Path) -> dict:
        clip = Clip(path=p, camera=meta(p)["kategorie"], sidecar=find_sidecar(p))
        rec = {"name": p.name, "path": str(p), "standort": "Autohaus Rappold",
               **meta(p), "fingerprint": clip_fingerprint(p)}
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers,
                        "text": t.text})
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
        finally:
            wav = work / f"{p.stem}.wav"
            if wav.exists():
                wav.unlink()
        return rec

    todo = [p for p in clips if not index.get(str(p), {}).get("ok")]
    print(f"{len(clips)} Clips, {len(clips) - len(todo)} bereits im Index, "
          f"{len(todo)} zu transkribieren", flush=True)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(job, p): p for p in todo}
        for n, fut in enumerate(as_completed(futures), 1):
            rec = fut.result()
            with lock:
                index[rec["path"]] = rec
                ordered = sorted(index.values(), key=lambda r: (r["kategorie"], r["name"]))
                index_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
            if rec["ok"]:
                print(f"{n}/{len(todo)} OK     {rec['kategorie']}/{rec['name']} "
                      f"({rec['n_words']} Wörter, {len(rec['speakers'])} Sprecher)",
                      flush=True)
            else:
                print(f"{n}/{len(todo)} FEHLER {rec['name']}: {rec['error']}", flush=True)

    ok = sum(1 for r in index.values() if r.get("ok"))
    print(f"\nFERTIG: {ok}/{len(clips)} Clips transkribiert -> {index_path}", flush=True)


if __name__ == "__main__":
    main()
