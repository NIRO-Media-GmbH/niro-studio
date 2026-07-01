from niro_transcribe.timefmt import fmt_time


def test_fmt_under_hour():
    assert fmt_time(134.0) == "02:14"


def test_fmt_rounds_down_to_second():
    assert fmt_time(134.9) == "02:14"


def test_fmt_over_hour():
    assert fmt_time(3725.0) == "1:02:05"
