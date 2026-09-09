from __future__ import annotations

from niro_autocut import align

W: list[dict] = []


def _w(text, t, spk="speaker_1"):
    W.append({"text": text, "start": t, "end": t + 0.3, "speaker": spk})


def _sentence(t0: float, text: str, spk: str = "speaker_1") -> None:
    """Scribe-Stil: Satzzeichen hängen am Wort, Füllwörter sind eigene Wörter; 0,4-s-Raster, 0,3 s Wortdauer."""
    for i, tok in enumerate(text.split()):
        _w(tok, t0 + i * 0.4, spk)


# Interview-Ausschnitt ab 10 s — Wortindizes: „Also" = 0, „Das" = 12, „getragen." = 20
_sentence(10, "Also unser Haus bezahlt, äh, die ganze Weiterbildung, ne, die Fachweiterbildung. "
              "Ähm. Das sind ja hundert Prozent von dem Haus getragen. Ne?")
# Interviewer-Frage, dann derselbe Take zweimal (Wiederholung im Dreh) ab 200 s und ab 260 s
_sentence(199.0, "Und warum?", "speaker_0")
_sentence(200, "Weil das mein Job ist. Das ist meins. Okay.")
_sentence(259.0, "Und warum?", "speaker_0")
_sentence(260, "Weil das mein Job ist. Das ist meins. Okay.")


def test_normalize():
    assert align.normalize("„Weil") == "weil" and align.normalize("Straße,") == "strasse"
    assert align.normalize("'n") == "n" and align.normalize("…") == ""


def test_split_fragments():
    assert align.split_fragments("„Also unser Haus bezahlt, äh, die ganze Weiterbildung. […] hundert Prozent von dem Haus getragen.\"") == \
        ["Also unser Haus bezahlt, äh, die ganze Weiterbildung.", "hundert Prozent von dem Haus getragen."]


def test_find_quote_with_elision():
    m = align.find_quote(W, "„Also unser Haus bezahlt, äh, die ganze Weiterbildung. […] hundert Prozent von dem Haus getragen.\"")
    assert m is not None and m.score >= 0.9
    assert abs(m.start_s - 10.0) < 1e-6 and abs(m.end_s - (10 + 20 * 0.4 + 0.3)) < 1e-6


def test_find_quote_prefers_near_hint():
    m = align.find_quote(W, "Weil das mein Job ist. Das ist meins.", near_s=255)
    assert abs(m.start_s - 260) < 1e-6
    m2 = align.find_quote(W, "Weil das mein Job ist. Das ist meins.", near_s=190)
    assert abs(m2.start_s - 200) < 1e-6


def test_tolerates_spelling_variants():
    m = align.find_quote(W, "Das sind 100 % von dem Haus getragen", min_score=0.7)
    assert m is not None and abs(m.start_s - (10 + 12 * 0.4)) < 1e-6


def test_no_match_returns_none():
    assert align.find_quote(W, "Völlig anderer Text über Autos und Trucks") is None
