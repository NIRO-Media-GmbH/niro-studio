from niro_transcribe.transcribe import transcribe_file
from niro_transcribe.cache import TranscriptCache
from niro_transcribe.models import Transcript, Word


def _mk(engine):
    return Transcript(source_file="a.wav", engine=engine, text=engine,
                      words=[Word(engine, 0.0, 1.0)])


def test_transcribe_file_uses_and_fills_cache(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"audio")
    cache = TranscriptCache(tmp_path / "cache")
    calls = {"scribe": 0, "whisper": 0}

    def scribe_fn(path, api_key, **kw):
        calls["scribe"] += 1
        return _mk("scribe")

    def whisper_fn(path, model_size="large-v3", **kw):
        calls["whisper"] += 1
        return _mk("whisper")

    out1 = transcribe_file(wav, cache, "key", scribe_fn=scribe_fn, whisper_fn=whisper_fn)
    assert set(out1) == {"scribe", "whisper"}
    assert out1["scribe"].text == "scribe"
    assert calls == {"scribe": 1, "whisper": 1}

    # zweiter Lauf -> alles aus Cache, keine neuen Aufrufe
    out2 = transcribe_file(wav, cache, "key", scribe_fn=scribe_fn, whisper_fn=whisper_fn)
    assert calls == {"scribe": 1, "whisper": 1}
    assert out2["whisper"].text == "whisper"
