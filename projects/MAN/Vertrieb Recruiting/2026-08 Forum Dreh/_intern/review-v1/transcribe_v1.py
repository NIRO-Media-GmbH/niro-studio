"""Wort-Transkripte (Scribe) der vier V1-Schnitte für das Review 2026-09-07."""
from __future__ import annotations
import json, os, sys
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
from niro_transcribe.footage.transcribe_clips import transcribe_clip
PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / "Material" / "Videos V1"
OUT = PROJECT / "_intern" / "review-v1" / "transcripts"
cache = TranscriptCache(PROJECT / "_intern" / "cache")
work = PROJECT / "_intern" / "work"; work.mkdir(exist_ok=True)
key = os.environ["ELEVENLABS_API_KEY"]
for p in sorted(SRC.glob("*.mp4")):
    slug = p.name.split(" - ")[0].lower().replace(" ", "")
    clip = Clip(path=p, camera="Videos V1", sidecar=find_sidecar(p))
    t = transcribe_clip(clip, cache=cache, api_key=key, work_dir=work)
    (OUT / f"{slug}.words.json").write_text(json.dumps(
        {"file": p.name, "text": t.text, "words": [w.to_dict() for w in t.words]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    lines = []
    for w in t.words:
        lines.append(f"[{w.start:6.2f}-{w.end:6.2f}] {w.speaker or '-':>10} {w.text}")
    (OUT / f"{slug}.words.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"OK {p.name}: {len(t.words)} Wörter, {t.duration():.1f}s", flush=True)
