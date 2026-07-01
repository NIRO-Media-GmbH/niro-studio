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
                {"text": "hallo", "start": 0.0, "end": 0.5, "type": "word"},
                {"text": " ", "start": 0.5, "end": 0.5, "type": "spacing"},
                {"text": "welt", "start": 0.5, "end": 1.0, "type": "word"},
            ],
        })

    t = transcribe_scribe(wav, "key123", poster=fake_poster)
    assert calls["headers"]["xi-api-key"] == "key123"
    assert calls["data"]["model_id"] == "scribe_v1"
    assert t.engine == "scribe"
    assert t.text == "hallo welt"
    assert [w.text for w in t.words] == ["hallo", "welt"]
    assert t.words[1].start == 0.5
