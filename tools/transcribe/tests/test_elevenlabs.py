from niro_transcribe.transcribe.elevenlabs import transcribe_scribe


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_transcribe_scribe_parses_words(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFFfake")
    calls = {}

    def fake_poster(url, headers=None, data=None, files=None, timeout=None):
        calls["url"] = url
        calls["headers"] = headers
        calls["data"] = data
        return FakeResponse({
            "text": "hallo welt",
            "words": [
                {"text": "hallo", "start": 0.0, "end": 0.5, "type": "word", "speaker_id": "speaker_0"},
                {"text": " ", "start": 0.5, "end": 0.5, "type": "spacing"},
                {"text": "welt", "start": 0.5, "end": 1.0, "type": "word", "speaker_id": "speaker_1"},
            ],
        })

    t = transcribe_scribe(wav, "key123", poster=fake_poster)
    assert calls["headers"]["xi-api-key"] == "key123"
    assert calls["data"]["model_id"] == "scribe_v1"
    assert calls["data"]["language_code"] == "deu"
    assert calls["data"]["diarize"] == "true"
    assert t.engine == "scribe"
    assert t.text == "hallo welt"
    assert [w.text for w in t.words] == ["hallo", "welt"]
    assert t.words[1].start == 0.5
    # Diarisation: Sprecher pro Wort übernommen
    assert t.words[0].speaker == "speaker_0"
    assert t.words[1].speaker == "speaker_1"


def test_transcribe_scribe_diarize_can_be_disabled(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFFfake")
    calls = {}

    def fake_poster(url, headers=None, data=None, files=None, timeout=None):
        calls["data"] = data
        return FakeResponse({"text": "", "words": []})

    transcribe_scribe(wav, "key123", diarize=False, poster=fake_poster)
    assert calls["data"]["diarize"] == "false"
