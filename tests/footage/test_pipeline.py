import json
from pathlib import Path

from niro_transcribe.footage.pipeline import transcribe_all
from niro_transcribe.models import Transcript, Word


def _fake_extract(video, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{Path(video).stem}.wav"
    p.write_bytes(b"wav")
    return p


def _fake_transcribe(audio, api_key, *, diarize=True):
    if "BAD" in Path(audio).name:
        raise RuntimeError("boom")
    return Transcript(source_file=Path(audio).name, engine="scribe", text="hallo welt",
                      words=[Word("hallo", 0.0, 0.5, "speaker_0"), Word("welt", 0.5, 1.0, "speaker_1")])


def test_transcribe_all_resilient_and_writes_index(tmp_path):
    foot = tmp_path / "footage"
    (foot / "Kamera-A").mkdir(parents=True)
    (foot / "Kamera-A" / "GOOD.mp4").write_bytes(b"v")
    (foot / "Kamera-A" / "BAD.mp4").write_bytes(b"v")
    proj = tmp_path / "proj"

    recs = transcribe_all(foot, proj, api_key="k", extractor=_fake_extract,
                          transcriber=_fake_transcribe, log=lambda *_: None)

    by = {r["name"]: r for r in recs}
    assert by["GOOD.mp4"]["ok"] is True
    assert by["GOOD.mp4"]["speakers"] == ["speaker_0", "speaker_1"]
    assert by["GOOD.mp4"]["duration_s"] == 1.0
    assert by["BAD.mp4"]["ok"] is False and "boom" in by["BAD.mp4"]["error"]
    # Index-Datei geschrieben und vollständig
    idx = json.loads((proj / "transcripts_index.json").read_text(encoding="utf-8"))
    assert len(idx) == 2
    # WAV des erfolgreichen Clips wurde aufgeräumt
    assert not (proj / "work" / "GOOD.wav").exists()
