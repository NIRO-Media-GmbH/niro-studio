"""Tests für resolve_api.py gegen das Fake-Resolve (tests/fake_resolve.py): Dedupe, Settings, Aufrufreihenfolge,
recordFrame absolut / Marker relativ, endFrame-Semantik aus der Probe, Readback, Proxy, Bau aus dem Plan, Lesen, Export."""
from __future__ import annotations

import datetime as _dt
import math

import pytest

from fake_resolve import FakeProject, FakeResolve, FakeTimeline
from niro_autocut import resolve_api as R
from niro_autocut.charge import AutoCutError
from niro_autocut.resolve_api import ResolveSession, build_from_plan
from niro_autocut.timeline_model import BeatPos, Item, MarkerSpec, TimelinePlan

CFG = {"resolve": {"bin_root": "AutoCut", "timeline_prefix": "AutoCut", "start_timecode": "01:00:00:00",
                   "track_names": {"V1": "FX3", "V2": "a7IV", "V3": "B-Roll", "A1": "FX3 Ton"}}}
FX, A7 = "/nas/Interviews/Anna/FX3_1.MP4", "/nas/Interviews/Anna/a7_1.MP4"
MEDIA = {"format": {"fps": 25, "width": 3840, "height": 2160}, "clips": {
    FX: {"proxy_path": "/nas/Interviews/Anna/Proxy/FX3_1.mov", "original": {"nb_frames": 7500}},
    A7: {"proxy_path": None, "original": {"nb_frames": 8000}}}}


def _plan() -> TimelinePlan:
    items = [Item("V1", FX, 244, 316, 0, 72, True, "1"), Item("A1", FX, 244, 316, 0, 72, True, "1"),
             Item("V2", A7, 294, 366, 0, 72, True, "1"),
             Item("V1", FX, 500, 550, 247, 297, True, "3"), Item("A1", FX, 500, 550, 247, 297, True, "3")]
    markers = [MarkerSpec(0, "#1 Hook", "O-Ton: Weil", "Blue"), MarkerSpec(97, "#2 VO", "Text: …", "Yellow"),
               MarkerSpec(247, "#3 B", "", "Blue")]
    beats = [BeatPos("1", "oton", 0, 72, FX, "Anna"), BeatPos("2", "vo", 97, 222), BeatPos("3", "oton", 247, 297, FX, "Anna")]
    return TimelinePlan(25.0, 3840, 2160, items, markers, beats, 297)


@pytest.fixture(autouse=True)
def _default_fake_semantics():
    FakeTimeline.inclusive = True
    FakeTimeline.reject_beyond_end = False
    yield
    FakeTimeline.inclusive = True
    FakeTimeline.reject_beyond_end = False


# --- Plan-Tests (Task 8 Step 1) ---------------------------------------------

def test_find_media_item_dedupes_by_path():
    s = ResolveSession(FakeResolve())
    f = s.ensure_bin(["AutoCut", "Test"])
    items = s.import_media(["/nas/a.MP4"], f)
    assert s.find_media_item("/nas/a.MP4") is items["/nas/a.MP4"]
    again = s.import_media(["/nas/a.MP4"], f)
    assert again["/nas/a.MP4"] is items["/nas/a.MP4"]  # nicht doppelt importiert
    assert [c for c in s.media_pool.calls if c[0] == "ImportMedia"] == [("ImportMedia", ["/nas/a.MP4"])]


def test_create_timeline_sets_custom_settings():
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("AutoCut X", 25.0, 2160, 3840, "01:00:00:00")
    assert t.settings["useCustomSettings"] == "1" and t.settings["timelineResolutionWidth"] == "2160"
    s.ensure_tracks(t, 3, 2, {"V1": "FX3", "A2": "a7IV Ton stumm"})
    assert t.tracks == {"video": 3, "audio": 2} and t.names[("audio", 2)] == "a7IV Ton stumm"


def test_append_items_uses_absolute_record_frames_and_disables_a2():
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("AutoCut X", 25.0, 3840, 2160, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media(["/nas/fx.MP4", "/nas/a7.MP4"], f)
    items = [Item("V1", "/nas/fx.MP4", 244, 316, 0, 72), Item("A1", "/nas/fx.MP4", 244, 316, 0, 72),
             Item("A2", "/nas/a7.MP4", 294, 366, 0, 72, enabled=False), Item("V3", "/nas/a7.MP4", 0, 50, 100, 150, video_only=True)]
    tl = s.append_items(t, items, mi, 90000)
    infos = t.items
    assert infos[0]["recordFrame"] == 90000 and infos[0]["trackIndex"] == 1 and infos[0]["mediaType"] == 1
    assert infos[1]["mediaType"] == 2 and infos[2]["trackIndex"] == 2
    assert infos[3]["mediaType"] == 1 and infos[3]["trackIndex"] == 3 and infos[3]["recordFrame"] == 90100
    assert tl[2].enabled is False


def test_quellframes_treffen_die_timeline_dauer_exakt():
    """Resolve rechnet die Dauer als abgerundet(Quellframes · 25 / Clip-fps). Die Quellframes müssen für jede Länge
    genau die Soll-Dauer liefern — auch wenn Resolve NTSC-Raten intern exakt (k·1000/1001) statt dezimal rechnet."""
    exakt = {119.88: 120000 / 1001, 59.94: 60000 / 1001, 29.97: 30000 / 1001}
    for fps in (119.88, 59.94, 29.97, 30.0, 50.0, 100.0):
        for n in range(1, 1500):
            q = R.quellframes(n, fps, 25.0)
            for rate in {fps, exakt.get(fps, fps)}:
                assert math.floor(q * 25 / rate + 1e-9) == n, (fps, n, q, rate)
    assert R.quellframes(24, 119.88, 25.0) == 116 and R.quellframes(24, 50.0, 25.0) == 48


def test_append_items_fremde_bildrate_trifft_slot_dauer():
    """Klebl 25.09.: Actioncam 119,88 fps in 25p, 24-Frame-Slot. Die Vorlage rechnet round(24 · 4,7952) = 115
    Quellframes, Resolve macht daraus 23 Frames, und der Readback bricht ab. append_items rundet selbst passend."""
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("T", 25.0, 2160, 3840, "01:00:00:00")
    cam, broll = "/nas/Actioncam/DJI_0012_D.MP4", "/nas/B-Roll/FX3_9.MP4"
    s.media_pool.fps_by_path.update({cam: "119.88", broll: "50"})
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([cam, broll], f)
    items = [Item("V3", cam, 43157, 43157 + round(n * 119.88 / 25), rec, rec + n, True, "4", "broll", True)
             for rec, n in ((0, 24), (24, 25), (49, 26))]
    items.append(Item("V3", broll, 100, 148, 75, 99, True, "4", "broll", True))       # 50p: 48 Quellframes = 24
    tl = s.append_items(t, items, mi, 90000)
    assert [int(x.GetDuration()) for x in tl] == [24, 25, 26, 24]
    assert t.items[0]["endFrame"] == 43157 + 116 - 1                                    # 116 statt 115 Quellframes
    assert t.items[3]["endFrame"] == 147                                                # ganzzahliges Verhältnis bleibt


def test_markers_are_relative_to_timeline_start():
    # Recherche 03.09.: Timeline.AddMarker(frameId) ist RELATIV zum Timeline-Start (README „timeline offset",
    # Forum t=175315) — im Gegensatz zu recordFrame (absolut). Kein Startframe addieren.
    s = ResolveSession(FakeResolve()); t = s.create_timeline("T", 25, 1, 1, "01:00:00:00")
    s.add_markers(t, [MarkerSpec(10, "#1 A", "n", "Blue")], 90000)
    assert t.markers[0] == (10, "Blue", "#1 A")


# --- Recherche-Korrekturen ------------------------------------------------------

def test_append_is_one_call_after_selected_clip_and_current_timeline():
    s = ResolveSession(FakeResolve())
    other = s.create_timeline("Andere", 25.0, 3840, 2160, "01:00:00:00")
    t = s.create_timeline("Ziel", 25.0, 3840, 2160, "01:00:00:00")
    s.project.SetCurrentTimeline(other)                       # Append darf nur in die Ziel-Timeline schreiben
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX, A7], f)
    items = [Item("V1", FX, 244, 316, 0, 72), Item("A1", FX, 244, 316, 0, 72),
             Item("V2", A7, 294, 366, 0, 72), Item("A2", A7, 294, 366, 0, 72, enabled=False)]
    tl = s.append_items(t, items, mi, 90000)
    calls = [c for c in s.media_pool.calls if c[0] in ("AppendToTimeline", "SetSelectedClip")]
    assert calls == [("SetSelectedClip", "FX3_1.MP4"), ("AppendToTimeline", 4)]
    assert s.project.GetCurrentTimeline() is t and other.items == [] and len(t.items) == 4
    # endFrame inklusiv (Default): Dauer 72 → endFrame = src_out_f − 1
    assert t.items[0]["startFrame"] == 244 and t.items[0]["endFrame"] == 315
    assert all(int(x.GetDuration()) == 72 and int(x.GetStart()) == 90000 for x in tl)
    assert t.linked and [x.GetName() for x in t.linked[0]] == ["FX3_1.MP4", "FX3_1.MP4"]   # V1+A1 best effort verknüpft


def test_readback_mismatch_raises_with_soll_und_ist():
    FakeTimeline.inclusive = False                            # Resolve verhält sich anders als angenommen
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("T", 25.0, 3840, 2160, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX], f)
    with pytest.raises(AutoCutError, match=r"Soll.*72.*Ist.*71"):
        s.append_items(t, [Item("V1", FX, 244, 316, 0, 72)], mi, 90000)


def test_end_frame_semantics_come_from_probe():
    FakeTimeline.inclusive = False
    s = ResolveSession(FakeResolve(), probe={"end_frame_inclusive": False})
    assert s.end_frame_inclusive is False
    t = s.create_timeline("T", 25.0, 3840, 2160, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX], f)
    tl = s.append_items(t, [Item("V1", FX, 244, 316, 0, 72)], mi, 90000)
    assert t.items[0]["endFrame"] == 316 and tl[0].GetDuration() == 72
    assert ResolveSession(FakeResolve()).end_frame_inclusive is R.END_FRAME_INCLUSIVE is True
    assert ResolveSession(FakeResolve(), probe={}).end_frame_inclusive is True


def test_append_reports_missing_media_item_and_failed_append():
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("T", 25.0, 3840, 2160, "01:00:00:00")
    with pytest.raises(AutoCutError, match="Media-Pool"):
        s.append_items(t, [Item("V1", FX, 0, 10, 0, 10)], {}, 90000)
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX], f)
    s.project.current = None
    s.project.SetCurrentTimeline = lambda tl: False           # Append landet nirgends → Resolve gibt None
    with pytest.raises(AutoCutError, match="AppendToTimeline"):
        s.append_items(t, [Item("V1", FX, 0, 10, 0, 10)], mi, 90000)
    assert s.append_items(t, [], mi, 90000) == []


def test_create_timeline_restores_color_keys_start_tc_and_checks_fps():
    s = ResolveSession(FakeResolve())
    t = s.create_timeline("AutoCut Y", 25.0, 3840, 2160, "02:00:00:00")
    for key in R.COLOR_KEYS:
        assert t.settings[key] == FakeTimeline("x", s.project).settings[key], key
    assert t.settings["timelineOutputResolutionHeight"] == "2160"
    assert t.GetStartTimecode() == "02:00:00:00" and s.timeline_start_frame(t) == 180000
    assert s.project.GetCurrentTimeline() is t and s.current_timeline is t
    assert "timelineFrameRate" not in [k for k, v in t.settings.items() if v != "25"]   # nie gesetzt
    with pytest.raises(AutoCutError, match="existiert bereits"):
        s.create_timeline("AutoCut Y", 25.0, 3840, 2160, "01:00:00:00")
    n = s.project.GetTimelineCount()
    with pytest.raises(AutoCutError, match="Bildrate"):
        s.create_timeline("AutoCut Z", 50.0, 3840, 2160, "01:00:00:00")
    assert s.project.GetTimelineCount() == n                  # nichts angelegt


def test_create_timeline_resolution_readback_is_checked(monkeypatch):
    s = ResolveSession(FakeResolve())
    orig = FakeTimeline.SetSetting

    def stubborn(self, k, v):
        if k == "timelineResolutionWidth":
            self.settings[k] = "1920"; return True             # BMD-Bug: meldet Erfolg, ändert nichts
        return orig(self, k, v)
    monkeypatch.setattr(FakeTimeline, "SetSetting", stubborn)
    with pytest.raises(AutoCutError, match="Auflösung"):      # Hochkant weicht vom Fake-Projekt (3840x2160) ab → eigene Einstellungen
        s.create_timeline("AutoCut Q", 25.0, 2160, 3840, "01:00:00:00")


def test_ensure_tracks_rejects_unknown_key_and_is_idempotent():
    s = ResolveSession(FakeResolve()); t = s.create_timeline("T", 25.0, 1, 1, "01:00:00:00")
    s.ensure_tracks(t, 3, 2, CFG["resolve"]["track_names"]); s.ensure_tracks(t, 3, 2, {})
    assert t.tracks == {"video": 3, "audio": 2} and t.GetTrackName("video", 3) == "B-Roll"
    with pytest.raises(AutoCutError, match="Spur"):
        s.ensure_tracks(t, 3, 2, {"V9": "x"})


def test_link_proxy_skips_when_already_linked():
    s = ResolveSession(FakeResolve()); f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX, A7], f)
    mi[A7].props["Proxy"] = "1920x1080"
    assert s.link_proxy(mi[A7], "/nas/p.mov") is True and mi[A7].link_calls == 0
    assert s.link_proxy(mi[FX], "/nas/p.mov") is True and mi[FX].link_calls == 1 and mi[FX].proxy == "/nas/p.mov"
    assert s.link_proxy(mi[FX], None) is False


def test_disable_items_warns_instead_of_failing():
    s = ResolveSession(FakeResolve()); t = s.create_timeline("T", 25.0, 1, 1, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([A7], f)
    tl = s.append_items(t, [Item("A2", A7, 0, 10, 0, 10)], mi, 90000)
    tl[0].refuse_disable = True
    s.disable_items(tl)
    assert tl[0].enabled is True and any("stumm" in w for w in s.warnings)


def test_add_markers_beyond_content_end_are_moved_with_warning():
    FakeTimeline.reject_beyond_end = True
    s = ResolveSession(FakeResolve()); t = s.create_timeline("T", 25.0, 1, 1, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"]); mi = s.import_media([FX], f)
    s.append_items(t, [Item("V1", FX, 0, 72, 0, 72)], mi, 90000)
    s.add_markers(t, [MarkerSpec(0, "#1", "", "Blue"), MarkerSpec(97, "#2 Endcard", "", "Purple"),
                      MarkerSpec(120, "#3 Ende", "", "Green")], 90000)
    assert [m[0] for m in t.markers] == [0, 71, 70]
    assert sum("verschoben" in w for w in s.warnings) == 2 and "#2 Endcard" in "".join(s.warnings)


def test_build_from_plan_end_to_end():
    s = ResolveSession(FakeResolve(FakeProject("MEK")))
    name = R.timeline_name("AutoCut", "video-1-imagefilm", _dt.datetime(2026, 9, 4, 9, 5))
    assert name == "AutoCut video-1-imagefilm 2026-09-04 0905"
    res = build_from_plan(s, _plan(), MEDIA, name, CFG)
    t = s.project.timelines[-1]
    assert t.name == name and res["timeline"] == name and res["items"] == 5 and res["markers"] == 3
    assert res["warnings"] == [] and res["start_frame"] == 90000 and res["saved"] is True
    assert res["project"] == "MEK" and res["end_frame_inclusive"] is True and res["bin"] == "AutoCut/video-1-imagefilm"
    assert t.tracks == {"video": 3, "audio": 1} and t.GetTrackName("audio", 1) == "FX3 Ton"
    # Bin AutoCut/<Video-Kurzname>, Medien darin, Proxy nur für FX3 (a7 hat keinen)
    root = s.media_pool.GetRootFolder()
    assert [f.name for f in root.subs] == ["AutoCut"] and [f.name for f in root.subs[0].subs] == ["video-1-imagefilm"]
    bin_items = {c.GetName(): c for c in root.subs[0].subs[0].clips}
    assert bin_items["FX3_1.MP4"].proxy == MEDIA["clips"][FX]["proxy_path"] and bin_items["a7_1.MP4"].proxy is None
    # Reihenfolge je Cut V1/A1/V2, dann nächster Cut; recordFrame absolut; Marker relativ; kein A2
    assert [(i["trackIndex"], i["mediaType"], i["recordFrame"]) for i in t.items] == [
        (1, 1, 90000), (1, 2, 90000), (2, 1, 90000), (1, 1, 90247), (1, 2, 90247)]
    assert [x.enabled for x in t.tl_items] == [True, True, True, True, True]
    assert [m[0] for m in t.markers] == [0, 97, 247] and t.marker_data[97]["color"] == "Yellow"
    assert s.media_pool.refreshed == 1 and s.project.saved == 1
    assert [c for c in s.media_pool.calls if c[0] == "AppendToTimeline"] == [("AppendToTimeline", 5)]


def test_build_from_plan_second_run_reuses_bin_and_media():
    s = ResolveSession(FakeResolve())
    build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 0905", CFG)
    build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 0911", CFG)
    imports = [c for c in s.media_pool.calls if c[0] == "ImportMedia"]
    assert len(imports) == 1 and sorted(imports[0][1]) == [FX, A7]
    assert [c for c in s.media_pool.calls if c[0] == "AddSubFolder"] == [("AddSubFolder", "AutoCut"), ("AddSubFolder", "video-1")]
    assert [t.name for t in s.project.timelines] == ["AutoCut video-1 2026-09-04 0905", "AutoCut video-1 2026-09-04 0911"]


def test_build_from_plan_proxy_warning():
    s = ResolveSession(FakeResolve())
    orig = R.ResolveSession.link_proxy
    s.link_proxy = lambda item, p: False if p else orig(s, item, p)
    res = build_from_plan(s, _plan(), MEDIA, "AutoCut v 2026-09-04 0905", CFG)
    assert res["warnings"] == ["Proxy nicht verknüpft: FX3_1.MP4"]


def test_bin_name_for_strips_prefix_and_timestamp():
    assert R.bin_name_for("AutoCut video-1-imagefilm 2026-09-04 0905", "AutoCut") == "video-1-imagefilm"
    assert R.bin_name_for("Probe/Lauf", "AutoCut") == "Probe-Lauf"
    assert R.bin_name_for("AutoCut " + "x" * 80 + " 2026-09-04 0905", "AutoCut") == "x" * 60


def test_read_timeline_lists_tracks_items_and_markers():
    s = ResolveSession(FakeResolve())
    build_from_plan(s, _plan(), MEDIA, "AutoCut v 2026-09-04 0905", CFG)
    t = s.find_timeline("AutoCut v 2026-09-04 0905")
    assert t is not None and s.find_timeline("gibt es nicht") is None
    d = s.read_timeline(t)
    assert d["name"] == "AutoCut v 2026-09-04 0905" and d["start_frame"] == 90000 and d["fps"] == "25"
    assert d["width"] == 3840 and d["height"] == 2160
    assert list(d["tracks"]) == ["V1", "V2", "V3", "A1"] and d["tracks"]["V1"]["name"] == "FX3"
    v1 = d["tracks"]["V1"]["items"]
    assert v1[0] == {"name": "FX3_1.MP4", "file": FX, "start": 90000, "end": 90072, "duration": 72,
                     "src_in": 244, "src_out": 315, "enabled": True, "left_offset": 244, "speed": 100.0}
    assert d["tracks"]["V2"]["items"][0]["enabled"] is True and d["tracks"]["V3"]["items"] == []
    assert d["markers"]["97"]["name"] == "#2 VO" and d["n_items"] == 5


def test_export_timeline_kinds(tmp_path):
    s = ResolveSession(FakeResolve()); t = s.create_timeline("T", 25.0, 1, 1, "01:00:00:00")
    p = s.export_timeline(t, tmp_path / "t.xml")
    assert p.read_text().startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5">')
    assert t.exports[-1] == (str(p), FakeResolve.EXPORT_FCP_7_XML, None)
    s.export_timeline(t, tmp_path / "t.otio", "otio"); assert t.exports[-1][1] == FakeResolve.EXPORT_OTIO
    s.export_timeline(t, tmp_path / "t.edl", "edl"); assert t.exports[-1][1:] == (FakeResolve.EXPORT_EDL, FakeResolve.EXPORT_NONE)
    with pytest.raises(AutoCutError, match="Export-Art"):
        s.export_timeline(t, tmp_path / "t.aaf", "aaf")
    t.Export = lambda *a: False
    with pytest.raises(AutoCutError, match="fehlgeschlagen"):
        s.export_timeline(t, tmp_path / "t2.xml")


def test_session_requires_open_project_and_connect_messages(monkeypatch):
    r = FakeResolve(); r.p = None
    with pytest.raises(AutoCutError, match="kein Projekt"):
        ResolveSession(r)

    class Mod:
        @staticmethod
        def scriptapp(name):
            return None
    monkeypatch.setattr(R, "_import_module", lambda: Mod)
    with pytest.raises(AutoCutError, match="Externes Scripting"):
        R.connect()

    def broken():
        raise ImportError("kein fusionscript")
    monkeypatch.setattr(R, "_import_module", broken)
    with pytest.raises(AutoCutError, match="nicht ladbar"):
        R.connect()
    fake = FakeResolve()
    monkeypatch.setattr(R, "_import_module", lambda: type("M", (), {"scriptapp": staticmethod(lambda n: fake)}))
    assert R.connect() is fake


def test_bin_name_strips_roh_suffix_and_session_restores_user_timeline():
    assert R.bin_name_for("AutoCut video-1 2026-09-04 1530 (roh)", "AutoCut") == "video-1"
    assert R.bin_name_for("AutoCut video-1 2026-09-04 1530", "AutoCut") == "video-1"
    fr = FakeResolve()
    user_tl = fr.p.mp.CreateEmptyTimeline("Users Schnitt")
    s = ResolveSession(fr)
    assert s.user_timeline is user_tl
    res = build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 1530 (roh)", CFG)
    t = fr.p.timelines[-1]
    assert t.tracks == {"video": 3, "audio": 1}
    assert fr.p.current is t
    assert s.restore_user_timeline() is True and fr.p.current is user_tl
    assert res["items"] == 5  # Cut 1: V1/A1/V2, Cut 3: V1/A1 — kein A2


def test_export_patch_import_roundtrip_with_fake(tmp_path):
    fr = FakeResolve()
    s = ResolveSession(fr)
    build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 1530 (roh)", CFG)
    roh = fr.p.timelines[-1]
    xml = s.export_timeline(roh, tmp_path / "roh.xml")
    from niro_autocut import xml_patch as X
    tree = X.load_xml(xml)
    assert [c["start"] for c in X.read_levels(tree)] == [0, 247]
    X.apply_patches(tree, [{"track": 1, "start": 247, "name": "FX3_1.MP4", "level": 2.0}], [])
    X.save_xml(tree, tmp_path / "final.xml")
    folder = s.ensure_bin(["AutoCut", "video-1"])
    final = s.import_timeline_xml(tmp_path / "final.xml", "AutoCut video-1 2026-09-04 1530", [folder])
    assert final.GetName() == "AutoCut video-1 2026-09-04 1530" and final in fr.p.timelines
    rb = s.read_timeline(final)
    assert [r["start"] for r in rb["tracks"]["A1"]["items"]] == [90000, 90247]
    assert final.GetItemListInTrack("audio", 1)[1].level == 2.0
    with pytest.raises(AutoCutError):
        s.import_timeline_xml(tmp_path / "final.xml", "AutoCut video-1 2026-09-04 1530", [folder])   # Name existiert


def test_delete_own_timeline_guard_and_color_items():
    fr = FakeResolve()
    s = ResolveSession(fr)
    build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 1530 (roh)", CFG)
    roh = fr.p.timelines[-1]
    with pytest.raises(AutoCutError):
        s.delete_own_timeline(roh, " (roh)", "AutoCut video-1 2026-09-04 1530")     # Name passt nicht
    other = fr.p.mp.CreateEmptyTimeline("Fremd (roh)")
    with pytest.raises(AutoCutError):
        s.delete_own_timeline(other, " (roh)", "AutoCut video-1 2026-09-04 1530 (roh)")
    n = s.color_items(roh, 1, {90000}, "Teal")
    assert n == 1 and roh.GetItemListInTrack("video", 1)[0].GetClipColor() == "Teal"
    assert s.delete_own_timeline(roh, " (roh)", "AutoCut video-1 2026-09-04 1530 (roh)") is True
    assert roh not in fr.p.timelines


def test_duplicate_media_and_fps_and_probe_cleanup():
    fr = FakeResolve()
    s = ResolveSession(fr)
    f = s.ensure_bin(["AutoCut", "PROBE-XML"])
    a = s.import_media(["/nas/b.MP4"], f)["/nas/b.MP4"]
    d = s.add_duplicate_media("/nas/b.MP4", f)
    assert d is not None and d is not a and s.set_clip_fps(d, 25) is True and d.GetClipProperty("FPS") == "25"
    rep = s.delete_probe_objects([], [d], [f])
    assert rep == {"timelines": True, "clips": True, "folders": True}
    assert d not in f.clips                                       # Duplikat-Clip wirklich aus dem Bin entfernt
    root = s.media_pool.GetRootFolder()
    autocut = next(sub for sub in root.subs if sub.name == "AutoCut")
    assert f not in autocut.subs                                  # Probe-Bin wirklich kein Unterordner von AutoCut mehr


def test_import_timeline_xml_preserves_empty_trailing_video_track(tmp_path):
    # roh-Timelines legen laut Spec immer 3 Videospuren an (build_from_plan → ensure_tracks(t, 3, 1, …)); V3
    # (B-Roll) bleibt im Standardplan unbenutzt. Track-Zählung nur über belegte Clipitems würde diese leere,
    # nachgestellte Spur beim Re-Import verlieren (V3 hat kein einziges Clipitem zum Zählen).
    fr = FakeResolve()
    s = ResolveSession(fr)
    build_from_plan(s, _plan(), MEDIA, "AutoCut video-1 2026-09-04 1530 (roh)", CFG)
    roh = fr.p.timelines[-1]
    assert roh.tracks == {"video": 3, "audio": 1}       # V3 existiert, aber ohne Items
    xml = s.export_timeline(roh, tmp_path / "roh.xml")
    folder = s.ensure_bin(["AutoCut", "video-1"])
    final = s.import_timeline_xml(xml, "AutoCut video-1 2026-09-04 1530", [folder])
    assert final.tracks == {"video": 3, "audio": 1}


def test_import_timeline_xml_unknown_clip_becomes_phantom_item(tmp_path):
    # Pinnt das HEUTIGE Fake-Verhalten: Ein Clipitem-Name aus dem XML, der in keinem der übergebenen Bins
    # auftaucht, ergibt ein Phantom-Item unter '/import/<name>'. Ob das echte Resolve genauso reagiert (oder
    # z. B. „Offline Media" erzeugt), misst eine spätere Aufgabe per Live-Probe — hier nur das Fake dokumentiert.
    fr = FakeResolve()
    s = ResolveSession(fr)
    t = s.create_timeline("T", 25.0, 3840, 2160, "01:00:00:00")
    f = s.ensure_bin(["AutoCut"])
    mi = s.import_media([FX], f)
    s.append_items(t, [Item("V1", FX, 0, 72, 0, 72)], mi, 90000)
    xml = s.export_timeline(t, tmp_path / "t.xml")
    leer = s.ensure_bin(["AutoCut", "Leer"])            # Bin ohne den exportierten Clip → Name nicht auffindbar
    final = s.import_timeline_xml(xml, "Import-Phantom", [leer])
    mpi = final.GetItemListInTrack("video", 1)[0].GetMediaPoolItem()
    assert mpi.GetClipProperty("File Path") == "/import/FX3_1.MP4"


def test_import_media_finds_mapped_item_without_import_and_keeps_original_key():
    p = FakeProject()
    mp = p.GetMediaPool()
    root = mp.GetRootFolder()
    ssd = mp.ImportMedia(["/Volumes/SSD/proj/Interviews/FX3_0001.MP4"])[0]
    mp.calls.clear()
    s = ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    out = s.import_media(["/Volumes/NAS/proj/Interviews/FX3_0001.MP4"], root)
    assert out == {"/Volumes/NAS/proj/Interviews/FX3_0001.MP4": ssd}
    assert not any(c[0] == "ImportMedia" for c in mp.calls)
    assert s.find_media_item("/Volumes/NAS/proj/Interviews/FX3_0001.MP4") is ssd


def test_import_media_imports_mapped_path_when_missing():
    p = FakeProject()
    mp = p.GetMediaPool()
    s = ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    out = s.import_media(["/Volumes/NAS/proj/B/FX3_0002.MP4"], mp.GetRootFolder())
    assert ("ImportMedia", ["/Volumes/SSD/proj/B/FX3_0002.MP4"]) in mp.calls
    assert list(out) == ["/Volumes/NAS/proj/B/FX3_0002.MP4"]
    assert out["/Volumes/NAS/proj/B/FX3_0002.MP4"].GetClipProperty("File Path") == "/Volumes/SSD/proj/B/FX3_0002.MP4"


def test_link_proxy_maps_proxy_path():
    p = FakeProject()
    item = p.GetMediaPool().ImportMedia(["/Volumes/SSD/proj/FX3_0003.MP4"])[0]
    s = ResolveSession(FakeResolve(p), path_map={"/Volumes/NAS/proj": "/Volumes/SSD/proj"})
    assert s.link_proxy(item, "/Volumes/NAS/proj/Proxy/FX3_0003.mov") is True
    assert item.proxy == "/Volumes/SSD/proj/Proxy/FX3_0003.mov"


def test_session_without_path_map_is_unchanged():
    p = FakeProject()
    mp = p.GetMediaPool()
    s = ResolveSession(FakeResolve(p))
    s.import_media(["/Volumes/NAS/proj/FX3_0004.MP4"], mp.GetRootFolder())
    assert ("ImportMedia", ["/Volumes/NAS/proj/FX3_0004.MP4"]) in mp.calls
