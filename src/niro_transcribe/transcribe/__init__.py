from __future__ import annotations

from ..cache import TranscriptCache, file_hash
from ..models import Transcript
from .elevenlabs import transcribe_scribe
from .whisper import transcribe_whisper

__all__ = ["transcribe_file", "transcribe_scribe", "transcribe_whisper"]


def transcribe_file(
    path,
    cache: TranscriptCache,
    api_key: str,
    whisper_model: str = "large-v3",
    *,
    scribe_fn=transcribe_scribe,
    whisper_fn=transcribe_whisper,
) -> dict[str, Transcript]:
    h = file_hash(path)
    result: dict[str, Transcript] = {}

    cached = cache.load(h, "scribe")
    if cached is None:
        t = scribe_fn(path, api_key)
        cache.save(h, "scribe", t.to_dict())
    else:
        t = Transcript.from_dict(cached)
    result["scribe"] = t

    cached = cache.load(h, "whisper")
    if cached is None:
        t = whisper_fn(path, model_size=whisper_model)
        cache.save(h, "whisper", t.to_dict())
    else:
        t = Transcript.from_dict(cached)
    result["whisper"] = t

    return result
