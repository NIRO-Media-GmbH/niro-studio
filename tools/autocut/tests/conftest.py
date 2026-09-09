from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def charge_dir(tmp_path: Path) -> Path:
    """Minimale Charge mit Plan, Index, Utterances und Cache."""
    root = tmp_path / "2026-06 Testdreh"
    (root / "Ergebnisse" / "O-Ton-Pläne").mkdir(parents=True)
    (root / "_intern" / "cache").mkdir(parents=True)
    (root / "Ergebnisse" / "O-Ton-Pläne" / "video-1-test.md").write_text("# Test\n", encoding="utf-8")
    fp = "abc123"
    (root / "_intern" / "transcripts_index.json").write_text(json.dumps([{
        "name": "FX3_0001.MP4", "path": str(tmp_path / "nas" / "Interviews" / "Anna" / "FX3_0001.MP4"),
        "kategorie": "Interviews", "person": "Anna", "kamera": "FX3", "kamera_rolle": "ton",
        "fingerprint": fp, "ok": True, "duration_s": 10.0, "n_words": 3}]), encoding="utf-8")
    (root / "_intern" / "utterances.json").write_text(json.dumps([{
        "name": "FX3_0001.MP4", "person": "Anna", "utterances": [
            {"speaker": "speaker_0", "von": "00:01", "bis": "00:02", "von_s": 1.0, "bis_s": 2.0, "text": "Das ist meins."}]}]), encoding="utf-8")
    (root / "_intern" / "cache" / f"{fp}.scribe.json").write_text(json.dumps({
        "source_file": "FX3_0001.MP4", "engine": "scribe", "text": "Das ist meins.",
        "words": [{"text": "Das", "start": 1.0, "end": 1.2, "speaker": "speaker_0"},
                  {"text": "ist", "start": 1.3, "end": 1.5, "speaker": "speaker_0"},
                  {"text": "meins.", "start": 1.6, "end": 2.0, "speaker": "speaker_0"}]}), encoding="utf-8")
    return root
