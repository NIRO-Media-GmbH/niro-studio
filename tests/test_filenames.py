from niro_transcribe.filenames import guess_meta


def test_three_parts_underscore():
    m = guess_meta("Interview_Werkzeugmechaniker_Milena.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "Werkzeugmechaniker", "Milena")
    assert m.quelldatei == "Interview_Werkzeugmechaniker_Milena.wav"


def test_multi_word_bereich():
    m = guess_meta("Interview_CNC_Fräsen_Anna.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "CNC Fräsen", "Anna")


def test_mixed_separators():
    m = guess_meta("Interview-Lager Max.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "Lager", "Max")


def test_two_parts():
    m = guess_meta("Interview_Sabine.wav")
    assert (m.typ, m.bereich, m.name) == ("Interview", "", "Sabine")


def test_single_token():
    m = guess_meta("Milena.wav")
    assert (m.typ, m.bereich, m.name) == ("", "", "Milena")
