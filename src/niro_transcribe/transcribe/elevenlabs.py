from __future__ import annotations

from pathlib import Path
import requests
from ..models import Transcript, Word

SCRIBE_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def transcribe_scribe(path, api_key: str, *, poster=requests.post) -> Transcript:
    path = Path(path)
    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, "audio/wav")}
        resp = poster(
            SCRIBE_URL,
            headers={"xi-api-key": api_key},
            data={"model_id": "scribe_v1", "language_code": "deu"},
            files=files,
            timeout=600,
        )
    resp.raise_for_status()
    payload = resp.json()
    words = [
        Word(text=w["text"], start=float(w["start"]), end=float(w["end"]))
        for w in payload.get("words", [])
        if w.get("type") == "word"
    ]
    return Transcript(
        source_file=path.name,
        engine="scribe",
        text=payload.get("text", ""),
        words=words,
    )
