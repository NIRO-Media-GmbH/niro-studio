from pathlib import Path

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip
from niro_transcribe.models import Transcript, Word


def test_fingerprint_stable_and_content_independent(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"abc")
    fp1 = clip_fingerprint(f)
    fp2 = clip_fingerprint(f)
    assert fp1 == fp2 and len(fp1) == 64


def test_transcribe_clip_uses_cache_on_second_call(tmp_path):
    mp4 = tmp_path / "clip.mp4"
    mp4.write_bytes(b"video-bytes")
    clip = Clip(path=mp4, camera="Kamera-A", sidecar=None)
    cache = TranscriptCache(tmp_path / "cache")
    calls = {"extract": 0, "transcribe": 0}

    def fake_extract(video, out_dir):
        calls["extract"] += 1
        p = Path(out_dir) / "clip.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"wav")
        return p

    def fake_transcribe(audio, api_key, *, diarize=True):
        calls["transcribe"] += 1
        return Transcript(source_file=Path(audio).name, engine="scribe", text="hallo welt",
                          words=[Word("hallo", 0.0, 0.4, "speaker_0")])

    t1 = transcribe_clip(clip, cache=cache, api_key="k", work_dir=tmp_path / "work",
                         extractor=fake_extract, transcriber=fake_transcribe)
    t2 = transcribe_clip(clip, cache=cache, api_key="k", work_dir=tmp_path / "work",
                         extractor=fake_extract, transcriber=fake_transcribe)

    assert t1.text == "hallo welt" and t2.text == "hallo welt"
    assert t1.source_file == "clip.mp4"  # nicht "clip.wav"
    assert calls["transcribe"] == 1  # zweiter Aufruf aus Cache
    assert calls["extract"] == 1
