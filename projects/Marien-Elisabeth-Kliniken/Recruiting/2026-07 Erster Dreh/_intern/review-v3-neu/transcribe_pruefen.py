"""MEK Recruiting — Video 3: beide Fassungen aus „Prüfen" per Scribe transkribieren (Review 14.09.).

alt = …_720p.mp4 (Kontrolle gegen Export 07.08.), neu = …_NEU.mov (Umsetzung Schnittplan V2).
Gleiche Pipeline wie transcribe_schnitt_v3.py (Scribe, Cache in _intern/cache), Quellen nur lesen.
"""
from __future__ import annotations

import json, os, sys, unicodedata
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

PROJECT = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
PRUEFEN = next(p for p in PROJECT.iterdir() if unicodedata.normalize("NFC", p.name) == "Prüfen")
OUT = PROJECT / "_intern" / "review-v3-neu"


def main() -> None:
    cache = TranscriptCache(PROJECT / "_intern" / "cache")
    work = PROJECT / "_intern" / "work"
    api_key = os.environ["ELEVENLABS_API_KEY"]
    for tag, suffix in (("alt", "_720p.mp4"), ("neu", "_NEU.mov")):
        src = next(p for p in PRUEFEN.iterdir() if p.name.endswith(suffix))
        clip = Clip(path=src, camera=f"V3-Pruefen-{tag}", sidecar=find_sidecar(src))
        t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
        (OUT / f"scribe_{tag}.json").write_text(json.dumps(t.to_dict(), ensure_ascii=False, indent=2))
        print(f"\n===== {tag}: {src.name}  fp={clip_fingerprint(src)[:12]}  {t.duration():.1f}s  {len(t.words)} Tokens")
        seg, start, spk = [], None, None
        for w in t.words:
            if w.text.strip() == "":
                continue
            if start is None:
                start, spk = w.start, w.speaker
            seg.append(w.text.strip())
            if w.text.strip()[-1:] in ".?!":
                print(f"[{start:5.2f}–{w.end:5.2f}] {spk}: {' '.join(seg)}")
                seg, start = [], None
        if seg:
            print(f"[{start:5.2f}–end] {spk}: {' '.join(seg)}")


if __name__ == "__main__":
    main()
