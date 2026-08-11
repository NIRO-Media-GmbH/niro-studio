from __future__ import annotations

import hashlib
from pathlib import Path

from ..cache import TranscriptCache
from ..models import Transcript
from ..transcribe.elevenlabs import transcribe_scribe
from .audio import extract_audio


def clip_fingerprint(path: str | Path) -> str:
    p = Path(path)
    st = p.stat()
    return hashlib.sha256(f"{p.name}:{st.st_size}:{st.st_mtime_ns}".encode("utf-8")).hexdigest()


def transcribe_clip(clip, *, cache: TranscriptCache, api_key: str, work_dir,
                    diarize: bool = True, extractor=extract_audio,
                    transcriber=transcribe_scribe) -> Transcript:
    fp = clip_fingerprint(clip.path)
    cached = cache.load(fp, "scribe")
    if cached is not None:
        return Transcript.from_dict(cached)
    audio = extractor(clip.path, work_dir)
    transcript = transcriber(audio, api_key, diarize=diarize)
    transcript.source_file = clip.path.name
    cache.save(fp, "scribe", transcript.to_dict())
    return transcript
