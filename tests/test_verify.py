from niro_transcribe.models import Statement, Transcript, Word
from niro_transcribe.verify import verify_statement


def _tr():
    return Transcript("a.wav", "scribe", "eins zwei drei", [
        Word("eins", 0.0, 1.0), Word("zwei", 1.0, 2.0), Word("drei", 2.0, 3.0),
    ])


def _stmt(von, bis):
    return Statement("s1", "a.wav", "Max", "Lager", von, bis, "zwei", "x")


def test_valid_statement_has_no_problems():
    assert verify_statement(_stmt(0.9, 2.1), _tr()) == []


def test_reversed_times_flagged():
    probs = verify_statement(_stmt(2.0, 1.0), _tr())
    assert any("von" in p and "bis" in p for p in probs)


def test_out_of_bounds_flagged():
    probs = verify_statement(_stmt(0.0, 10.0), _tr())
    assert any("Dauer" in p for p in probs)


def test_no_overlapping_words_flagged():
    probs = verify_statement(_stmt(0.0, 0.05), _tr())
    assert any("kein" in p.lower() for p in probs)
