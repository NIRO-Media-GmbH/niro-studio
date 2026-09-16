"""Tests für finalize.py — Ablauf gegen das Fake-Resolve, Patch-Listen, Prüfungen, Abbruch ohne Löschung."""
from __future__ import annotations

import json

import pytest

from fake_resolve import FakeResolve
from niro_autocut import finalize as F
from niro_autocut.charge import AutoCutError, Charge
from niro_autocut.resolve_api import ResolveSession, build_from_plan
from niro_autocut.timeline_model import BeatPos, Item, MarkerSpec, TimelinePlan

CFG = {"resolve": {"bin_root": "AutoCut", "timeline_prefix": "AutoCut", "start_timecode": "01:00:00:00", "roh_suffix": " (roh)",
                   "track_names": {"V1": "FX3", "V2": "a7IV", "V3": "B-Roll", "A1": "FX3 Ton"}},
       "ton": {"ziel_dbtp": -3.0, "max_gain_db": 30.0, "clip_warn_dbtp": -0.5, "silence_dbtp": -60.0}}
FX = "/nas/Interviews/Anna/FX3_1.MP4"
BR = "/nas/B-Roll/Flur/FX3_9.MP4"
MEDIA = {"format": {"fps": 25, "width": 3840, "height": 2160},
         "clips": {FX: {"proxy_path": "/nas/Interviews/Anna/Proxy/FX3_1.mov", "original": {"nb_frames": 7500}}}}


def _plan():
    items = [Item("V1", FX, 244, 316, 0, 72, True, "1"), Item("A1", FX, 244, 316, 0, 72, True, "1"),
             Item("V1", FX, 500, 550, 97, 147, True, "3"), Item("A1", FX, 500, 550, 97, 147, True, "3")]
    return TimelinePlan(25.0, 3840, 2160, items, [MarkerSpec(0, "#1 Hook", "", "Blue"), MarkerSpec(97, "#3", "", "Blue")],
                        [BeatPos("1", "oton", 0, 72, FX, "Anna"), BeatPos("3", "oton", 97, 147, FX, "Anna")], 147)


def _prepare(charge_dir, with_broll=True, with_user_timeline=False):
    ch = Charge.open(charge_dir)
    fr = FakeResolve()
    if with_user_timeline:
        fr.p.mp.CreateEmptyTimeline("Bestehende User-Timeline")   # offen, BEVOR die Session startet
    s = ResolveSession(fr)
    tp = _plan()
    res = build_from_plan(s, tp, MEDIA, "AutoCut video-1 2026-09-04 1530 (roh)", CFG)
    ch.write_json("timeline.json", {**tp.to_dict(), "timeline": res["timeline"], "start_frame": res["start_frame"], "video": "video-1.md"})
    ch.write_json("build.json", {**res, "status": "ok", "video": "video-1.md"})
    if with_broll:
        roh = fr.p.timelines[-1]
        folder = s.ensure_bin(["AutoCut", "video-1", "B-Roll"])
        mi = s.import_media([BR], folder)
        mi[BR].SetClipProperty("FPS", "50")                                       # Fake: 50p-Clip
        v3 = Item("V3", BR, 0, 100, 72, 122, True, "1", "broll", True, tempo=2)     # 100 Quellframes 50p → roh 50 Frames
        s.append_items(roh, [v3], mi, res["start_frame"])
        ch.write_json("broll_build.json", {"status": "ok", "timeline": res["timeline"], "items": [v3.to_dict()],
                                            "markers": [MarkerSpec(72, "Szene 1 · Flur · 1 Shots", "", "Cyan").to_dict()]})
    ch.write_json("probe_xml.json", {"ok": True, "level_import_ok": True, "speed_import_ok": True})
    return ch, fr, s


def test_expected_items_and_patch_lists(charge_dir):
    ch, fr, s = _prepare(charge_dir)
    tp = ch.read_json("timeline.json")
    bb = ch.read_json("broll_build.json")
    exp = F.expected_items(tp, bb)
    assert {(e["track"], e["rec_in_f"], e["dur_f"], e["tempo"]) for e in exp} == {("V1", 0, 72, 1), ("A1", 0, 72, 1), ("V1", 97, 50, 1),
                                                                                 ("A1", 97, 50, 1), ("V3", 72, 100, 2)}
    ton = {"items": [{"clip": FX, "name": "FX3_1.MP4", "rec_in_f": 0, "gain_lin": 2.0}, {"clip": FX, "name": "FX3_1.MP4", "rec_in_f": 97, "gain_lin": 1.5}]}
    assert F.level_patches(ton) == [{"track": 1, "start": 0, "name": "FX3_1.MP4", "level": 2.0},
                                    {"track": 1, "start": 97, "name": "FX3_1.MP4", "level": 1.5}]
    assert F.speed_patches(bb) == [{"track": 3, "start": 72, "name": "FX3_9.MP4", "tempo": 2, "end": 172}]
    assert F.final_name("AutoCut video-1 2026-09-04 1530 (roh)", " (roh)") == "AutoCut video-1 2026-09-04 1530"
    with pytest.raises(AutoCutError):
        F.final_name("AutoCut video-1 2026-09-04 1530", " (roh)")


def test_verify_final_reports_missing_and_wrong_duration():
    exp = [{"track": "V1", "rec_in_f": 0, "dur_f": 72, "name": "FX3_1.MP4", "tempo": 1},
           {"track": "V3", "rec_in_f": 72, "dur_f": 100, "name": "FX3_9.MP4", "tempo": 2}]
    rb = {"tracks": {"V1": {"items": [{"name": "FX3_1.MP4", "start": 90000, "duration": 72}]},
                     "V3": {"items": [{"name": "FX3_9.MP4", "start": 90072, "duration": 50}]}}}
    probs = F.verify_final(rb, exp, 90000)
    assert len(probs) == 1 and "V3" in probs[0] and "50" in probs[0]
    assert F.verify_final({"tracks": {"V1": {"items": []}}}, exp[:1], 90000)[0].startswith("V1")


def test_finalize_end_to_end_with_fake(charge_dir):
    ch, fr, s = _prepare(charge_dir)
    out = F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    assert out["status"] == "ok" and out["timeline"] == "AutoCut video-1 2026-09-04 1530" and out["roh_geloescht"] is True
    names = [t.name for t in fr.p.timelines]
    assert "AutoCut video-1 2026-09-04 1530" in names and "AutoCut video-1 2026-09-04 1530 (roh)" not in names
    final = next(t for t in fr.p.timelines if t.name == out["timeline"])
    a1 = final.GetItemListInTrack("audio", 1)
    assert [round(i.level, 3) for i in a1] == [3.981, 3.981]                  # +12 dB
    v3 = final.GetItemListInTrack("video", 3)[0]
    assert v3.dur == 100 and v3.speed == 50.0 and v3.GetClipColor() == "Teal"
    assert final.names[("video", 3)] == "B-Roll" and len(final.marker_data) == 3
    assert fr.p.current is s.user_timeline or s.user_timeline is None
    fj = json.loads((ch.autocut / "finalize.json").read_text())
    assert fj["levels_set"] == 2 and fj["speeds_set"] == 1 and (ch.autocut / "ton.json").exists()


def test_finalize_refuses_without_probe_and_keeps_roh_on_mismatch(charge_dir):
    ch, fr, s = _prepare(charge_dir, with_broll=False)
    (ch.autocut / "probe_xml.json").unlink()
    with pytest.raises(AutoCutError):
        F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    ch.write_json("probe_xml.json", {"ok": True, "level_import_ok": True, "speed_import_ok": False})
    tp = ch.read_json("timeline.json")
    tp["items"][0]["rec_out_f"] = 60          # Erwartung passt nicht mehr zur roh-Timeline → Prüfung schlägt fehl
    ch.write_json("timeline.json", tp)
    with pytest.raises(AutoCutError):
        F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    names = [t.name for t in fr.p.timelines]
    assert "AutoCut video-1 2026-09-04 1530 (roh)" in names and "AutoCut video-1 2026-09-04 1530 FEHLER" in names
    assert json.loads((ch.autocut / "finalize.json").read_text())["status"] == "fehler"


def test_finalize_missing_roh_restores_user_timeline_and_writes_fehler(charge_dir):
    """roh-Timeline von Hand aus dem Projekt entfernt, BEVOR finalize() läuft (z. B. jemand hat sie in Resolve
    gelöscht): AutoCutError, finalize.json trotzdem mit status "fehler" (keine End-Timeline entstand je — das
    Verzweigen auf "… FEHLER" darf hier also nicht versucht werden), und die VORHER offene User-Timeline wird
    wieder aktiviert, obwohl der Fehler ganz am Anfang der Resolve-Arbeit auftritt."""
    ch, fr, s = _prepare(charge_dir, with_broll=False, with_user_timeline=True)
    assert s.user_timeline is not None
    roh = fr.p.timelines[-1]
    fr.p.mp.DeleteTimelines([roh])
    with pytest.raises(AutoCutError):
        F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    fj = json.loads((ch.autocut / "finalize.json").read_text())
    assert fj["status"] == "fehler" and fj["roh_geloescht"] is False
    assert fr.p.current is s.user_timeline


def test_finalize_wraps_raw_exception_and_restores_user_timeline(charge_dir):
    """Eine rohe, nicht-AutoCutError-Exception aus der Resolve-Session (z. B. Absturz beim Export) wird als
    AutoCutError verpackt (Klassenname im Text), finalize.json trotzdem geschrieben, User-Timeline trotzdem
    wiederhergestellt — auch wenn der Fehler vor dem Import der End-Timeline auftritt."""
    ch, fr, s = _prepare(charge_dir, with_broll=False, with_user_timeline=True)

    def boom(*a, **k):
        raise RuntimeError("boom")

    s.export_timeline = boom
    with pytest.raises(AutoCutError) as ei:
        F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    assert "RuntimeError" in str(ei.value)
    fj = json.loads((ch.autocut / "finalize.json").read_text())
    assert fj["status"] == "fehler"
    assert fr.p.current is s.user_timeline


def test_finalize_schreibt_bau_readback(charge_dir):
    ch, fr, s = _prepare(charge_dir)
    out = F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    rb = ch.autocut / "readback" / f"{out['timeline']}.json"
    assert out["bau_readback"] == str(rb) and rb.is_file()


def test_finalize_behaelt_hochgeladene_roh_timeline(charge_dir):
    ch, fr, s = _prepare(charge_dir)
    roh = ch.read_json("build.json")["timeline"]
    replay = charge_dir / "_intern" / "replay"
    replay.mkdir(parents=True)
    (replay / "uploads.json").write_text(json.dumps([{"titel": roh, "timeline": roh}]), encoding="utf-8")
    out = F.finalize(ch, s, CFG, measure=lambda p, i, d: -15.0)
    assert out["status"] == "ok" and out["roh_geloescht"] is False
    assert roh in [t.name for t in fr.p.timelines]
    assert any("Replay" in w for w in out["warnings"])
