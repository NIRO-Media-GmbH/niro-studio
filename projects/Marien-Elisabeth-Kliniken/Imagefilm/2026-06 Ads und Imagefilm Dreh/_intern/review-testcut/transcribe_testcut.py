"""MEK Imagefilm — Testcut „MEK Test1.mov" per Scribe transkribieren (Review 14.09.). Quelle nur lesen, Cache in _intern/cache."""
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
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip
CH = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh")
SRC = CH / "Material" / "Testcut" / "MEK Test1.mov"
def main():
    cache = TranscriptCache(CH / "_intern" / "cache")
    work = CH / "_intern" / "work"; work.mkdir(parents=True, exist_ok=True)
    clip = Clip(path=SRC, camera="Testcut", sidecar=find_sidecar(SRC))
    t = transcribe_clip(clip, cache=cache, api_key=os.environ["ELEVENLABS_API_KEY"], work_dir=work)
    (CH / "_intern/review-testcut/scribe_testcut.json").write_text(json.dumps(t.to_dict(), ensure_ascii=False, indent=2))
    print(f"fp={clip_fingerprint(SRC)[:12]} {t.duration():.1f}s {len(t.words)} Tokens, Sprecher {sorted({w.speaker for w in t.words if w.speaker})}")
    seg, start, spk = [], None, None
    for w in t.words:
        if not w.text.strip(): continue
        if start is None: start, spk = w.start, w.speaker
        seg.append(w.text.strip())
        if w.text.strip()[-1:] in ".?!":
            print(f"[{start:6.2f}–{w.end:6.2f}] {spk}: {' '.join(seg)}"); seg, start = [], None
    if seg: print(f"[{start:6.2f}–end] {spk}: {' '.join(seg)}")
if __name__ == "__main__":
    main()
