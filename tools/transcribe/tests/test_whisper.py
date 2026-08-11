from types import SimpleNamespace
from niro_transcribe.transcribe.whisper import transcribe_whisper


def test_transcribe_whisper_flattens_words(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFFfake")

    def fake_transcriber(path, model_size):
        seg1 = SimpleNamespace(words=[
            SimpleNamespace(word="hallo", start=0.0, end=0.5),
            SimpleNamespace(word=" welt", start=0.5, end=1.0),
        ])
        return [seg1], "hallo welt"

    t = transcribe_whisper(wav, transcriber=fake_transcriber)
    assert t.engine == "whisper"
    assert t.text == "hallo welt"
    assert [w.text for w in t.words] == ["hallo", "welt"]  # getrimmt
    assert t.words[1].end == 1.0
