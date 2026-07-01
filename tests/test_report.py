from niro_transcribe.models import (
    Statement, SelectedStatement, VideoPlan, InterviewMeta,
)
from niro_transcribe.report import render_video_plan, render_overview


def _sel(pos, person, von, bis, text, grund):
    st = Statement(f"s{pos}", "Interview_Lager_Max.wav", person, "Lager", von, bis, text, "x")
    return SelectedStatement(statement=st, begruendung=grund, position=pos)


def _plan():
    return VideoPlan(
        titel="Video 3 — Nachhaltigkeit",
        framework="Problem-Agitate-Solve",
        framework_begruendung="passt zum Fokus",
        geschaetzte_laenge_sek=85,
        statements=[
            _sel(2, "Anna", 10.0, 15.0, "Zweite Aussage", "Beweis"),
            _sel(1, "Max", 134.0, 143.0, "Erste Aussage", "Hook"),
        ],
        roter_faden="Vom Problem zur Lösung.",
    )


def test_render_video_plan_contains_key_fields():
    md = render_video_plan(_plan())
    assert "Video 3 — Nachhaltigkeit" in md
    assert "Problem-Agitate-Solve" in md
    assert "01:25" in md  # 85s geschätzte Länge
    assert "02:14–02:23" in md  # Max' Statement
    # Reihenfolge: Position 1 (Max) vor Position 2 (Anna)
    assert md.index("Erste Aussage") < md.index("Zweite Aussage")
    assert "Roter Faden" in md


def test_render_overview_lists_interpretations_and_unused():
    metas = [InterviewMeta("Interview_Lager_Max.wav", "Interview", "Lager", "Max")]
    unused = [Statement("u1", "Interview_Lager_Max.wav", "Max", "Lager", 5.0, 8.0, "ungenutzt stark", "x")]
    md = render_overview([_plan()], metas, unused)
    assert "Interview_Lager_Max.wav" in md
    assert "Max" in md and "Lager" in md
    assert "ungenutzt stark" in md
