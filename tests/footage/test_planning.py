from pathlib import Path

from niro_transcribe.footage.discover import Clip
from niro_transcribe.footage.planning import build_move_plan, person_slug


SCRIPT = {"videos": [
    {"nr": 1, "titel": "Der Weg", "rows": [
        {"id": "1_HookA", "typ": "scripted", "text": "In welcher Kanzlei wirst du Chef?"},
        {"id": "1_Szene1", "typ": "interview", "text": "Frage: Wie kamst du hierher?"},
    ]},
]}


def _clip(path, camera):
    return Clip(path=Path(path), camera=camera, sidecar=None)


def test_person_slug_alias_and_none():
    assert person_slug(None) == "_ohne_Namen"
    assert person_slug("Suzan Baözen", {"Suzan Baözen": "Suzan Baüsen"}) == "Suzan Baüsen"


def test_build_move_plan_routing_and_balance(tmp_path):
    clips = [
        _clip("/f/Kamera-C/C01.mp4", "Kamera-C"),          # scripted
        _clip("/f/Kamera-A/A01.mp4", "Kamera-A"),          # interview Suzan (A)
        _clip("/f/Kamera-B/B01.mp4", "Kamera-B"),          # interview Suzan (B, andere Schreibweise)
        _clip("/f/Kamera-C/C02.mp4", "Kamera-C"),          # broll
        _clip("/f/Kamera-C/C03.mp4", "Kamera-C"),          # unsure
    ]
    cls = {
        "C01.mp4": {"category": "scripted", "video_nr": 1, "row_id": "1_HookA", "confidence": "hoch"},
        "A01.mp4": {"category": "interview", "person": "Suzan Baüsen"},
        "B01.mp4": {"category": "interview", "person": "Suzan Baözen"},
        "C02.mp4": {"category": "broll"},
        "C03.mp4": {"category": "unsure", "note": "unklar"},
    }
    sort = tmp_path / "sortiert"
    res = build_move_plan(clips, cls, SCRIPT, sort, aliases={"Suzan Baözen": "Suzan Baüsen"})

    dst = {Path(m.src).name: m.dst for m in res.plan.moves}
    assert dst["C01.mp4"] == str(sort / "Video 1 - Der Weg" / "01_HookA_In-welcher-Kanzlei-wirst-du-Chef" / "C01.mp4")
    assert dst["A01.mp4"] == str(sort / "Interviews" / "Suzan Baüsen" / "Kamera-A" / "A01.mp4")
    assert dst["B01.mp4"] == str(sort / "Interviews" / "Suzan Baüsen" / "Kamera-B" / "B01.mp4")
    assert dst["C02.mp4"] == str(sort / "B-Roll" / "C02.mp4")
    assert dst["C03.mp4"] == str(sort / "_nicht_zugeordnet" / "C03.mp4")
    assert res.balance["validate_ok"] is True
    assert res.balance == {"clips": 5, "scripted": 1, "interview": 2, "broll": 1, "nicht": 1, "validate_ok": True}
    assert "Zuordnungsplan" in res.markdown
