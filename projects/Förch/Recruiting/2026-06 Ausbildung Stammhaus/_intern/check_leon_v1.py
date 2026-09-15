"""Leon V1-Abnahme (Frame.io-Lieferung 06.08.2026): Transkripte + Prüf-Frames.

Nutzt denselben Transkript-Cache wie der Schnittplan-Lauf; Frames landen in
_intern/work/leon-v1-frames/<az>/ zur Sicht-Prüfung (Captions, Inserts, Endcards).
"""
from __future__ import annotations

import json
import subprocess
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

DELIVERY = Path("/Users/jansantos/Downloads/Förch Leon V1/Förch Videos")
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Förch/Recruiting/"
    "2026-06 Ausbildung Stammhaus"
)

VIDEOS = [
    ("az-a", "Werbeanzeige — „Hand oder Kopf – bei Förch geht beides“.mp4"),
    ("az-c", "Was du nach drei Jahren wirklich kannst.mp4"),
    ("az-g", "Bereichs-Video Logistik Ausbildung (Fachlagerist).mp4"),
    ("az-h", "Bereichs-Video Logistik Duales Studium (Warenwirtschaft-und Logistik).mp4"),
    ("az-i", "Bereichs-Video IT Ausbildung (Fachinformatik).mp4"),
    ("az-j", "IT Duales Studium (Wirtschaftsinformatik).mp4"),
    ("az-k", "Bereichs-Video Kaufmännisch Ausbildung (Kaufleute Großund-Außenhandel).mp4"),
    ("az-l", "Bereichs-Video Kaufmännisch Duales Studium (BWL-Internationaler Handel).mp4"),
]


def duration_of(p: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(p)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def grab(p: Path, t: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(p),
         "-frames:v", "1", "-vf", "scale=880:-2", "-q:v", "3", str(dest)],
        check=True)


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(exist_ok=True)
    frames_root = work / "leon-v1-frames"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    index = []
    for az, fname in VIDEOS:
        p = DELIVERY / fname
        d = duration_of(p)
        times = [0.5, 4.0, 0.25 * d, 0.5 * d, 0.75 * d, d - 2.2, d - 0.7]
        for t in times:
            grab(p, max(t, 0.0), frames_root / az / f"t{t:05.1f}.jpg")
        rec = {"az": az, "name": fname, "duration_s": round(d, 2),
               "fingerprint": clip_fingerprint(p)}
        try:
            clip = Clip(path=p, camera=f"LeonV1/{az}", sidecar=find_sidecar(p))
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            words = []
            for w in t.words:
                start = getattr(w, "start", None)
                txt = getattr(w, "text", None) or getattr(w, "word", "")
                if txt.strip():
                    words.append([round(start, 2) if start is not None else None,
                                  txt])
            rec.update({"ok": True, "n_words": len(words), "text": t.text,
                        "words": words})
            print(f"OK   {az} ({d:.1f}s, {len(words)} Wörter)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"FEHLER {az}: {rec['error']}", flush=True)
        finally:
            wav = work / f"{p.stem}.wav"
            if wav.exists():
                wav.unlink()
        index.append(rec)
        (intern / "leon_v1_transcripts.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for r in index if r.get("ok"))
    print(f"FERTIG: {n_ok}/{len(index)} ok; Frames: {frames_root}", flush=True)


if __name__ == "__main__":
    main()
