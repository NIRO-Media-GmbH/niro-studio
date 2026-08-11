from niro_transcribe.models import Word, Transcript, Statement


def test_transcript_roundtrip():
    t = Transcript(
        source_file="a.wav",
        engine="scribe",
        text="hallo welt",
        words=[Word("hallo", 0.0, 0.5), Word("welt", 0.5, 1.0)],
    )
    d = t.to_dict()
    back = Transcript.from_dict(d)
    assert back == t
    assert back.language == "de"


def test_transcript_duration():
    t = Transcript("a.wav", "scribe", "x", [Word("x", 1.0, 3.5)])
    assert t.duration() == 3.5


def test_statement_von_bis_and_roundtrip():
    s = Statement(
        id="s1", quelldatei="a.wav", person="Milena", bereich="Werkzeugmechanik",
        von=134.0, bis=143.0, text="Früher haben wir …", thema="Wandel",
    )
    assert s.von_bis() == "02:14–02:23"
    assert Statement.from_dict(s.to_dict()) == s
