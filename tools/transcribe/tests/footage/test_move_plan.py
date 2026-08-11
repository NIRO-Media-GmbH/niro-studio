from niro_transcribe.footage.move_plan import Move, MovePlan


def test_validate_ok_when_every_clip_mapped_once():
    discovered = ["/f/a.mp4", "/f/b.mp4"]
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/a.mp4"),
                           Move("/f/b.mp4", "/s/_nicht_zugeordnet/b.mp4")])
    assert plan.validate(discovered) == []


def test_validate_flags_missing_duplicate_and_unknown():
    discovered = ["/f/a.mp4", "/f/b.mp4"]
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/x/a.mp4"),
                           Move("/f/a.mp4", "/s/y/a.mp4"),   # duplicate src + dup name ok? dst unique
                           Move("/f/c.mp4", "/s/x/a.mp4")])  # unknown src + duplicate dst
    problems = plan.validate(discovered)
    assert any("b.mp4" in p and "fehlt" in p for p in problems)      # b nicht abgedeckt
    assert any("/f/a.mp4" in p and "mehrfach" in p for p in problems)  # a doppelt
    assert any("/f/c.mp4" in p and "unbekannt" in p for p in problems)  # c nicht discovered
    assert any("/s/x/a.mp4" in p and "Ziel" in p for p in problems)   # dst kollidiert


def test_save_and_load_roundtrip(tmp_path):
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/a.mp4")])
    p = tmp_path / "manifest.json"
    plan.save(p)
    loaded = MovePlan.load(p)
    assert loaded.moves == plan.moves


def test_validate_flags_renamed_filename():
    discovered = ["/f/a.mp4"]
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/b.mp4")])
    problems = plan.validate(discovered)
    assert any("Dateiname geändert" in p for p in problems)


def test_validate_accepts_path_objects_as_discovered():
    from pathlib import Path
    from niro_transcribe.footage.move_plan import Move, MovePlan
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/a.mp4")])
    # discovered passed as Path objects (as the docs' `c.path` yields)
    assert plan.validate([Path("/f/a.mp4")]) == []
