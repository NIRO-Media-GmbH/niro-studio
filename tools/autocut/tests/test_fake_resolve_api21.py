"""Fake-Resolve, API 21.1: Properties, Speed-Semantiken (umschaltbar), Fades, Transition, Normalize,
AutoAlign, QuickExport, Konstanten. Belegt, was das Probe-Skript später vom Fake erwartet."""
from __future__ import annotations

import pytest

from fake_resolve import FakeProject, FakeResolve, FakeTimeline


@pytest.fixture(autouse=True)
def _defaults():
    FakeTimeline.inclusive = True
    FakeTimeline.speed_extends = True
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0
    yield
    FakeTimeline.inclusive = True
    FakeTimeline.speed_extends = True
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0


def _v3_timeline(project: FakeProject, starts=(0, 100, 150, 200)):
    """Timeline mit vier 50p-Clips (je 100 Quellframes = 50 Timeline-Frames) auf V3: A, Lücke, B, C, D."""
    mp = project.GetMediaPool()
    mp.fps_by_path["/z.mov"] = 50
    z = mp.ImportMedia(["/z.mov"])[0]
    t = mp.CreateEmptyTimeline("T")
    t.AddTrack("video")
    t.AddTrack("video")
    mp.SetSelectedClip(z)
    infos = [{"mediaPoolItem": z, "startFrame": 0, "endFrame": 99, "recordFrame": 90000 + s, "trackIndex": 3,
              "mediaType": 1} for s in starts]
    return t, mp.AppendToTimeline(infos)


def _audio_item(project: FakeProject):
    mp = project.GetMediaPool()
    clip = mp.ImportMedia(["/ton.mov"])[0]
    t = mp.CreateEmptyTimeline("A")
    mp.SetSelectedClip(clip)
    v, a = mp.AppendToTimeline([
        {"mediaPoolItem": clip, "startFrame": 25, "endFrame": 124, "recordFrame": 90000, "trackIndex": 1, "mediaType": 1},
        {"mediaPoolItem": clip, "startFrame": 25, "endFrame": 124, "recordFrame": 90000, "trackIndex": 1, "mediaType": 2}])
    return t, v, a


def test_setspeed_extends_into_gap_and_keeps_source():
    t, (a, b, c, d) = _v3_timeline(FakeProject())
    assert a.GetDuration() == 50 and a.timeline is t
    assert a.SetSpeed({"Percentage": 50.0, "RippleTimeline": False}) is True
    assert a.GetDuration() == 100
    assert a.GetSpeed() == {"Percentage": 50.0}
    assert (a.GetSourceStartFrame(), a.GetSourceEndFrame()) == (0, 99)
    assert b.GetStart() == 90100          # Nachbar unverändert


def test_setspeed_blocked_by_neighbour_keeps_duration():
    t, (a, b, c, d) = _v3_timeline(FakeProject())
    assert b.SetSpeed({"Percentage": 50.0, "RippleTimeline": False}) is True
    assert b.GetDuration() == 50 and c.GetStart() == 90150


def test_setspeed_ripple_shifts_following_items():
    t, (a, b, c, d) = _v3_timeline(FakeProject())
    assert c.SetSpeed({"Percentage": 50.0, "RippleTimeline": True}) is True
    assert c.GetDuration() == 100 and d.GetStart() == 90250


def test_setspeed_keeps_duration_mode_shrinks_source():
    FakeTimeline.speed_extends = False
    t, (a, b, c, d) = _v3_timeline(FakeProject())
    assert a.SetSpeed({"Percentage": 50.0}) is True
    assert a.GetDuration() == 50
    assert a.GetSourceEndFrame() == 50    # 0..99 (100 Frames) × 0,5 → endFrame 50


def test_setspeed_rejects_zero_percent():
    t, (a, *_) = _v3_timeline(FakeProject())
    assert a.SetSpeed({"Percentage": 0.0}) is False


def test_properties_volume_and_validation():
    t, v, a = _audio_item(FakeProject())
    assert a.GetType() == "audio" and v.GetType() == "video"
    assert a.GetProperties()["AudioVolume"] == 0.0 and a.GetProperties()["AudioVolumeEnabled"] is True
    assert a.SetProperties({"AudioVolume": 9.0}) is True
    assert a.GetProperties()["AudioVolume"] == 9.0
    assert a.SetProperties({"AudioVolume": 40.0}) is False       # außerhalb −100…30
    assert a.SetProperties({"GibtEsNicht": 1}) is False
    assert a.GetProperties()["AudioVolume"] == 9.0               # unverändert nach Ablehnung


def test_fades_and_active_timeline_flag():
    p = FakeProject()
    t, v, a = _audio_item(p)
    assert a.SetFades({"FadeIn": 3, "FadeOut": 5}) is True
    assert a.GetFades() == {"FadeIn": 3, "FadeOut": 5}
    other = p.GetMediaPool().CreateEmptyTimeline("B")      # macht B aktuell
    FakeTimeline.fades_need_active = True
    assert a.SetFades({"FadeIn": 2, "FadeOut": 2}) is False
    assert a.GetFades() == {"FadeIn": 3, "FadeOut": 5}
    p.SetCurrentTimeline(t)
    assert a.SetFades({"FadeIn": 2, "FadeOut": 2}) is True


def test_add_transition_returns_transition_item():
    t, v, a = _audio_item(FakeProject())
    tr = v.AddTransition({"type": "Cross Dissolve", "category": "simple", "position": "start",
                          "alignment": "center", "duration": 12})
    assert tr is not None and tr.GetType() == "transition" and tr.GetDuration() == 12
    assert t.transitions == [tr]
    assert v.AddTransition({"type": "X", "category": "unbekannt", "position": "start"}) is None


def test_normalize_true_peak_sets_volume_from_tpk():
    t, v, a = _audio_item(FakeProject())
    assert "True Peak" in t.GetNormalizeAudioModes()
    assert t.NormalizeAudioLevel([a], {"normalizationMode": "True Peak", "targetLevel": -3.0, "setLevelMode": 1}) is True
    assert a.GetProperties()["AudioVolume"] == 9.0             # −3 − (−12)
    assert t.NormalizeAudioLevel([a], {"normalizationMode": "Gibt es nicht"}) is False
    assert len(t.normalize_calls) == 1


def test_autoalign_moves_v2_and_linked_audio():
    p = FakeProject()
    mp = p.GetMediaPool()
    x, y = mp.ImportMedia(["/x.mov", "/y.mov"])
    t = mp.CreateEmptyTimeline("S")
    t.AddTrack("video")
    t.AddTrack("audio", "stereo")
    mp.SetSelectedClip(x)
    v1, a1, v2, a2 = mp.AppendToTimeline([
        {"mediaPoolItem": x, "startFrame": 0, "endFrame": 249, "recordFrame": 90100, "trackIndex": 1, "mediaType": 1},
        {"mediaPoolItem": x, "startFrame": 0, "endFrame": 249, "recordFrame": 90100, "trackIndex": 1, "mediaType": 2},
        {"mediaPoolItem": y, "startFrame": 0, "endFrame": 299, "recordFrame": 90100, "trackIndex": 2, "mediaType": 1},
        {"mediaPoolItem": y, "startFrame": 0, "endFrame": 299, "recordFrame": 90100, "trackIndex": 2, "mediaType": 2}])
    assert t.AutoAlignClips([v1, v2], {"SyncUsing": 1, "UseTrack": -1}) is True
    assert (v1.GetStart(), v2.GetStart(), a2.GetStart()) == (90100, 90050, 90050)
    FakeTimeline.align_moves = "V1"
    assert t.AutoAlignClips([v1, v2], {"SyncUsing": 1}) is True
    assert (v1.GetStart(), a1.GetStart()) == (90150, 90150)
    assert t.AutoAlignClips([v1], {}) is False


def test_quickexport_writes_file_and_reports(tmp_path):
    p = FakeProject()
    mp = p.GetMediaPool()
    mp.CreateEmptyTimeline("R")
    assert "H.265 Master" in p.GetQuickExportRenderPresets()
    st = p.RenderWithQuickExport("H.265 Master", {"TargetDir": str(tmp_path / "out"), "CustomName": "probe_api"})
    assert st["JobStatus"] == "Render Complete" and (tmp_path / "out" / "probe_api.mov").stat().st_size > 0
    assert p.IsRenderingInProgress() is False
    assert p.RenderWithQuickExport("Kein Preset", {"TargetDir": str(tmp_path)})["JobStatus"] == "Render Failed"


def test_alpha_mode_and_constants_and_version():
    p = FakeProject()
    mp = p.GetMediaPool()
    mp.alpha_by_path["/o.mov"] = "Straight"
    o, n = mp.ImportMedia(["/o.mov", "/n.mov"])
    assert o.GetClipProperty("Alpha mode") == "Straight" and n.GetClipProperty("Alpha mode") == "None"
    r = FakeResolve(p)
    assert r.GetVersionString() == "21.1.0.14"
    assert r.NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT == 1 and r.AUTO_ALIGN_CLIPS_USING_WAVEFORM == 1
    assert r.AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_AUTOMATIC == -1
