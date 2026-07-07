from __future__ import annotations

import json
from pathlib import Path

from ..config import Config
from ..cache import TranscriptCache
from ..transcribe.elevenlabs import transcribe_scribe
from .audio import extract_audio
from .discover import discover_clips
from .transcribe_clips import clip_fingerprint, transcribe_clip


def transcribe_all(footage_root, project_dir, *, api_key=None, diarize=True,
                   extractor=extract_audio, transcriber=transcribe_scribe,
                   log=print) -> list[dict]:
    project_dir = Path(project_dir)
    cache = TranscriptCache(project_dir / "cache")
    work = project_dir / "work"
    index_path = project_dir / "transcripts_index.json"
    if api_key is None:
        api_key = Config.load().elevenlabs_api_key

    clips = discover_clips(footage_root)
    index: list[dict] = []
    for i, clip in enumerate(clips, 1):
        rec = {
            "path": str(clip.path), "camera": clip.camera, "name": clip.path.name,
            "sidecar": clip.sidecar.name if clip.sidecar else None,
            "fingerprint": clip_fingerprint(clip.path),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work,
                                diarize=diarize, extractor=extractor, transcriber=transcriber)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({"ok": True, "duration_s": round(t.duration(), 1),
                        "n_words": len(t.words), "speakers": speakers, "text": t.text})
            wav = work / f"{clip.path.stem}.wav"
            if wav.exists():
                wav.unlink()
            log(f"{i}/{len(clips)} OK [{clip.camera}] {clip.path.name}")
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            log(f"{i}/{len(clips)} FEHLER [{clip.camera}] {clip.path.name}: {rec['error']}")
        index.append(rec)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index
