"""Auswertung der API-Probe 21.1: Erwartungswerte, Klassifikation der Befunde, Pflichtmessungen, Zusammenfassung."""
from __future__ import annotations

from niro_autocut import probe_api as PA


def test_expected_gain_from_true_peak():
    assert PA.expected_gain_db(-12.0) == 9.0
    assert PA.expected_gain_db(-12.04, ziel_dbtp=-3.0) == 9.04
    assert PA.expected_gain_db(-1.5) == -1.5


def test_eval_volume_tolerance_and_enabled():
    assert PA.eval_volume(True, 9.0, True)["ok"] is True
    assert PA.eval_volume(True, 9.04, True)["ok"] is True
    assert PA.eval_volume(True, 9.2, True)["ok"] is False
    assert PA.eval_volume(True, 9.0, False)["ok"] is False
    assert PA.eval_volume(False, 9.0, True)["ok"] is False
    assert PA.eval_volume(True, None, True)["ok"] is False


def test_eval_normalize_within_half_db():
    r = PA.eval_normalize(True, 9.3, -12.0, ["Sample Peak Program", "True Peak"])
    assert r["ok"] is True and r["soll"] == 9.0 and r["diff"] == 0.3 and r["tpk_ffmpeg"] == -12.0
    assert PA.eval_normalize(True, 9.6, -12.0, ["True Peak"])["ok"] is False
    assert PA.eval_normalize(False, 9.0, -12.0, ["True Peak"])["ok"] is False
    assert PA.eval_normalize(True, None, -12.0, ["True Peak"])["diff"] is None


def test_speed_classification():
    assert PA.classify_speed_gap(50, 100) == "verlängert"
    assert PA.classify_speed_gap(50, 99) == "verlängert"
    assert PA.classify_speed_gap(50, 50) == "behält_dauer"
    assert PA.classify_speed_gap(50, 70) == "teilweise"
    assert PA.classify_ripple(90200, 90250, 50) == "verschiebt"
    assert PA.classify_ripple(90200, 90200, 50) == "bleibt"
    assert PA.classify_ripple(90200, 90230, 50) == "anders (+30)"
    assert PA.source_kept((0, 99), (0, 100)) is True
    assert PA.source_kept((0, 99), (0, 50)) is False
    assert PA.speed_percent_ok({"Percentage": 50.0}) is True
    assert PA.speed_percent_ok({"Percentage": 100.0}) is False
    assert PA.speed_percent_ok(None) is False


def test_fades_and_align():
    assert PA.fades_match({"FadeIn": 3, "FadeOut": 5}, {"FadeIn": 3.0, "FadeOut": 5.0}) is True
    assert PA.fades_match({"FadeIn": 3, "FadeOut": 5}, {"FadeIn": 3, "FadeOut": 4}) is False
    assert PA.fades_match({"FadeIn": 3, "FadeOut": 5}, None) is False
    r = PA.classify_align(90100, 90100, 90100, 90050)
    assert r == {"moved": "V2", "delta_frames": -50, "ok": True}
    assert PA.classify_align(90100, 90150, 90100, 90100)["moved"] == "V1"
    assert PA.classify_align(90100, 90150, 90100, 90100)["ok"] is True      # relativ −50
    assert PA.classify_align(90100, 90100, 90100, 90100) == {"moved": "keiner", "delta_frames": 0, "ok": False}
    assert PA.classify_align(90100, 90120, 90100, 90090)["moved"] == "beide"


def test_overall_ok_requires_only_mandatory_keys():
    res = {"volume": {"ok": True}, "speed": {"ok": True}, "fades": {"ok": True}, "quickexport": {"ok": False}}
    assert PA.overall_ok(res) is True
    assert PA.overall_ok({**res, "speed": {"ok": False}}) is False
    assert PA.overall_ok({"volume": {"ok": True}}) is False


def test_summary_lines_mention_every_measure():
    res = {"volume": {"ok": True}, "normalize": {"uebersprungen": "Modus fehlt"},
           "speed": {"ok": True, "gap": "verlängert", "ripple": "verschiebt", "source_kept": True},
           "fades": {"ok": False}, "transition": {"ok": True},
           "autoalign": {"ok": True, "moved": "V2", "delta_frames": -50},
           "inactive": {"ok": False, "fades_on_inactive_ok": False},
           "quickexport": {"ok": True, "status": "Render Complete", "wanddauer_s": 4.2},
           "alpha_import": {"ok": True}}
    lines = PA.summary_lines(res)
    text = "\n".join(lines)
    for k in ("volume", "normalize", "speed", "fades", "transition", "autoalign", "inactive", "quickexport", "alpha_import"):
        assert f"  {k}:" in text
    assert "übersprungen — Modus fehlt" in text and "gap=verlängert" in text and "moved=V2" in text
    assert lines[-1].endswith("False")        # fades nicht ok → Pflicht verletzt
