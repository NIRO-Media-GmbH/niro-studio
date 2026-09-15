"""Phase 1 (nur lesen): alle Clips finden, Audio extrahieren, per Scribe
transkribieren (gecacht), Index schreiben. Verschiebt NICHTS."""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

from niro_transcribe.config import Config
from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import discover_clips
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip

FOOTAGE = Path("/Volumes/NIRO-SSD-02/Lohi Backup/01_Footage")
PROJ = Path("projects/LohiBW Recruiting")
CACHE = PROJ / "cache"
WORK = PROJ / "work"
INDEX = PROJ / "transcripts_index.json"
PROGRESS = PROJ / "phase1_progress.txt"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(PROGRESS, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main() -> int:
    cfg = Config.load()
    cache = TranscriptCache(CACHE)
    clips = discover_clips(FOOTAGE)
    log(f"START Phase 1 — {len(clips)} Clips gefunden")

    index = []
    failures = []
    for i, clip in enumerate(clips, 1):
        rec = {
            "path": str(clip.path),
            "camera": clip.camera,
            "name": clip.path.name,
            "sidecar": clip.sidecar.name if clip.sidecar else None,
            "fingerprint": clip_fingerprint(clip.path),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=cfg.elevenlabs_api_key, work_dir=WORK)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({
                "ok": True,
                "duration_s": round(t.duration(), 1),
                "n_words": len(t.words),
                "speakers": speakers,
                "text": t.text,
            })
            # wav aufräumen (Cache hält das JSON)
            wav = WORK / f"{clip.path.stem}.wav"
            if wav.exists():
                wav.unlink()
            log(f"{i}/{len(clips)} OK  [{clip.camera}] {clip.path.name}  "
                f"{rec['duration_s']}s  spk={speakers}  '{t.text[:60].replace(chr(10),' ')}'")
        except Exception as e:  # pro Clip resilient
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            failures.append(rec)
            log(f"{i}/{len(clips)} FEHLER [{clip.camera}] {clip.path.name}: {rec['error']}")
            traceback.print_exc()
        index.append(rec)
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in index if r.get("ok"))
    log(f"FERTIG — {ok}/{len(clips)} transkribiert, {len(failures)} Fehler")
    log(f"Index: {INDEX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
