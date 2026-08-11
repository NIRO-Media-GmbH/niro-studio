from __future__ import annotations

from pathlib import Path
from ..models import Transcript, Word


def _default_transcriber(path, model_size):
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="auto", compute_type="auto")
    segments, _info = model.transcribe(str(path), language="de", word_timestamps=True)
    segments = list(segments)
    text = "".join(seg.text for seg in segments).strip()
    return segments, text


def transcribe_whisper(path, model_size: str = "large-v3", *, transcriber=None) -> Transcript:
    path = Path(path)
    transcriber = transcriber or _default_transcriber
    segments, text = transcriber(path, model_size)
    words: list[Word] = []
    for seg in segments:
        for w in (seg.words or []):
            words.append(Word(text=w.word.strip(), start=float(w.start), end=float(w.end)))
    return Transcript(source_file=path.name, engine="whisper", text=text, words=words)
