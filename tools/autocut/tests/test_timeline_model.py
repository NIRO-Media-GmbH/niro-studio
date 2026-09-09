"""Tests für timeline_model.py — Beats → frame-genaue Items mit Pausen, Platzhaltern, Handles, Markern."""
from __future__ import annotations

import pytest

from niro_autocut.charge import AutoCutError
from niro_autocut.cutlist import Beat, Cut, Cutlist
from niro_autocut.media import seconds_to_frames
from niro_autocut.timeline_model import (BeatPos, Item, MarkerSpec, TimelinePlan, build_timeline_plan,
                                         clamp_handles)

CFG = {"pause_s": 1.0, "handle_in_frames": 6, "handle_out_frames": 8, "resolve": {"track_names": {}}}
FX, A7 = "/nas/FX3_1.MP4", "/nas/a7_1.MP4"
MEDIA = {"format": {"fps": 25, "width": 3840, "height": 2160}, "clips": {
    FX: {"original": {"duration_s": 300.0, "nb_frames": 7500}}, A7: {"original": {"duration_s": 320.0, "nb_frames": 8000}}}}
SYNC = {"fps": 25, "paare": [{"ref": FX, "other": A7, "offset_s": 2.0, "offset_frames": 50, "confidence": 10,
                              "overlap_ref": [0.0, 300.0], "drift_frames": 0, "ok": True, "note": ""}]}
# Sprecher s1 sagt 10,0–12,3 s „Weil das mein Job ist“; s0 (Interviewer) spricht direkt davor und danach.
_S1 = [{"text": t, "start": 10 + i * 0.5, "end": 10.3 + i * 0.5, "speaker": "s1"}
       for i, t in enumerate("Weil das mein Job ist".split())]
WORDS = {FX: [{"text": "Frage", "start": 8.0, "end": 9.9, "speaker": "s0"}] + _S1
            + [{"text": "Aha", "start": 12.6, "end": 13.0, "speaker": "s0"}]}
# Gleiche Aussage, aber die Fremdwörter liegen außerhalb der Handles (6 Frames = 0,24 s / 8 Frames = 0,32 s).
WORDS_FREI = {FX: [{"text": "Frage", "start": 8.0, "end": 9.5, "speaker": "s0"}] + _S1
                 + [{"text": "Aha", "start": 12.7, "end": 13.0, "speaker": "s0"}]}


def _cl(beats):
    return Cutlist(video="v", ziel_laenge_s=None, fps=25, format="16:9", pause_s=1.0, beats=beats)


def test_items_positions_pause_and_v2_offset():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "Weil das mein Job ist")]),
              Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6),
              Beat(nr="3", szene="B", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "Weil das mein Job ist", hart_in=True, hart_out=True)])])
    tp = build_timeline_plan(cl, MEDIA, SYNC, WORDS_FREI, CFG)
    v1 = [i for i in tp.items if i.track == "V1"]; v2 = [i for i in tp.items if i.track == "V2"]
    assert v1[0].src_in_f == 250 - 6 and v1[0].src_out_f == round(12.3 * 25) + 8 and v1[0].rec_in_f == 0
    assert v2[0].src_in_f == v1[0].src_in_f + 50 and v2[0].rec_in_f == 0
    assert not [i for i in tp.items if i.track == "A2"]
    assert [i for i in tp.items if i.track == "V2"]
    # Beat 2 = Lücke 6 s nach 1 s Pause; Beat 3 harte Kanten
    assert tp.beats[1].rec_in_f == v1[0].rec_out_f + 25 and tp.beats[1].rec_out_f == tp.beats[1].rec_in_f + 150
    assert v1[1].rec_in_f == tp.beats[1].rec_out_f + 25 and v1[1].src_in_f == 250 and v1[1].src_out_f == round(12.3 * 25)
    assert tp.total_frames == v1[1].rec_out_f
    assert [m.name for m in tp.markers][:2] == ["#1 A", "#2 VO"]


def test_handles_clamped_to_other_speaker():
    a, b = clamp_handles(WORDS[FX], 10.0, 12.3, 0.24, 0.32, "s1")
    assert a == 9.9 and b == 12.6


def test_no_v2_without_coverage():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    tp = build_timeline_plan(cl, MEDIA, {"fps": 25, "paare": []}, WORDS, CFG)
    assert not [i for i in tp.items if i.track == "V2"]
    assert any(m.color == "Red" for m in tp.markers)


# --- Ergänzungen über den Plan hinaus ---------------------------------------

def test_build_clamps_handles_when_other_speaker_adjacent():
    """Im Bau greifen die begrenzten Handles: Vorlauf endet am Fremdwort-Ende, Nachlauf am Fremdwort-Anfang."""
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "Weil das mein Job ist")])])
    tp = build_timeline_plan(cl, MEDIA, SYNC, WORDS, CFG)
    v1 = [i for i in tp.items if i.track == "V1"][0]
    assert v1.src_in_f == seconds_to_frames(9.9, 25) and v1.src_out_f == seconds_to_frames(12.6, 25)
    assert 9.9 * 25 <= v1.src_in_f and v1.src_out_f <= 12.6 * 25 + 0.5
    v2 = [i for i in tp.items if i.track == "V2"][0]
    assert (v2.src_in_f, v2.src_out_f) == (v1.src_in_f + 50, v1.src_out_f + 50)
    assert v1.rec_out_f - v1.rec_in_f == v1.src_out_f - v1.src_in_f == tp.total_frames


def test_clamp_handles_straddling_word_and_unknown_speaker():
    words = WORDS[FX]
    # Fremdwort ragt über den In-Punkt hinaus → gar kein Vorlauf; eigener Sprecher wird nie beschnitten.
    a, b = clamp_handles(words, 9.8, 12.3, 0.24, 0.32, "s1")
    assert a == 9.8 and b == 12.6
    # Ohne bekannten Sprecher zählt jedes angrenzende Wort als fremd (konservativ).
    a, b = clamp_handles(words, 10.5, 11.8, 0.24, 0.32, None)
    assert a == 10.3 and b == 12.0
    # Ohne Nachbarn bleiben die vollen Handles; nie unter 0.
    a, b = clamp_handles(_S1, 10.0, 12.3, 0.24, 0.32, "s1")
    assert (a, b) == (9.76, 12.62)
    assert clamp_handles([], 0.1, 1.0, 0.24, 0.32, None)[0] == 0.0
    # Scribe-Sonderelemente und Klammer-Annotationen sind keine Wörter.
    extra = [{"text": "(übersprechen 00:00:09)", "start": 9.5, "end": 9.95, "speaker": "s0"},
             {"text": " ", "type": "spacing", "start": 9.95, "end": 10.0, "speaker": "s0"}]
    assert clamp_handles(_S1 + extra, 10.0, 12.3, 0.24, 0.32, "s1")[0] == 9.76


def test_multiple_cuts_in_one_beat_are_gapless_and_custom_pause():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, pause_after_s=2.0,
                   cuts=[Cut(10.0, 10.8, "Weil das", hart_out=True), Cut(11.5, 12.3, "Job ist", hart_in=True)]),
              Beat(nr="2", szene="Bild", typ="bild", platzhalter_s=4, pause_after_s=9.0),
              Beat(nr="3", szene="Grafik", typ="grafik", platzhalter_s=2)])
    tp = build_timeline_plan(cl, MEDIA, SYNC, WORDS_FREI, CFG)
    v1 = [i for i in tp.items if i.track == "V1"]
    assert len(v1) == 2 and v1[1].rec_in_f == v1[0].rec_out_f          # Teilschnitte ohne Lücke
    assert v1[0].src_out_f == seconds_to_frames(10.8, 25) and v1[1].src_in_f == seconds_to_frames(11.5, 25)
    assert tp.beats[0].rec_out_f == v1[1].rec_out_f
    assert tp.beats[1].rec_in_f == tp.beats[0].rec_out_f + 50           # pause_after_s 2,0 statt 1,0
    assert tp.beats[2].rec_in_f == tp.beats[1].rec_out_f + 225          # pause_after_s 9,0
    assert tp.total_frames == tp.beats[2].rec_out_f == tp.beats[2].rec_in_f + 50   # keine Pause nach dem letzten Beat
    assert [(m.name, m.color) for m in tp.markers] == [("#1 A", "Blue"), ("#2 Bild", "Green"), ("#3 Grafik", "Purple")]
    assert all(it.beat_nr == "1" and it.kind == "oton" and not it.video_only for it in tp.items)


def test_marker_notes_and_positions():
    cl = _cl([Beat(nr="1", szene="Hook", typ="oton", person="Sandra", rolle="Pflegerin", clip=FX,
                   cuts=[Cut(10.0, 10.8, "Weil das"), Cut(11.5, 12.3, "Job ist")],
                   bild_hinweis="Gesicht roh", kommentar="KEINE Bauchbinde", caption="Sandra M."),
              Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6, text="Viele denken", sound="Musik leise")])
    tp = build_timeline_plan(cl, MEDIA, SYNC, WORDS_FREI, CFG)
    m1, m2 = tp.markers[0], tp.markers[1]
    assert m1.frame == tp.beats[0].rec_in_f == 0 and m2.frame == tp.beats[1].rec_in_f
    assert "Weil das […] Job ist" in m1.note and "Sandra" in m1.note and "Pflegerin" in m1.note
    assert "Gesicht roh" in m1.note and "KEINE Bauchbinde" in m1.note and "Sandra M." in m1.note
    assert "Viele denken" in m2.note and "Musik leise" in m2.note and m2.color == "Yellow"
    assert tp.beats[0] == BeatPos("1", "oton", 0, tp.beats[0].rec_out_f, FX, "Sandra")
    assert tp.beats[1].clip is None and tp.beats[1].person is None


def test_v2_missing_marker_does_not_collide_with_beat_marker():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    tp = build_timeline_plan(cl, MEDIA, {"fps": 25, "paare": []}, WORDS, CFG)
    frames = [m.frame for m in tp.markers]
    assert len(frames) == len(set(frames)), "Resolve erlaubt nur einen Marker pro Frame"
    warn = [m for m in tp.markers if m.color == "Red"][0]
    assert "V2 fehlt" in warn.name and warn.frame == 1 and warn.duration == tp.items[0].rec_out_f
    assert not [i for i in tp.items if i.track in ("V2", "A2")]


def test_v2_only_when_pair_covers_handled_range():
    # Überlappung endet bei 12,5 s: die Handles reichen bis 12,62 s → keine volle Abdeckung → kein V2.
    sync = {"fps": 25, "paare": [dict(SYNC["paare"][0], overlap_ref=[0.0, 12.5])]}
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    tp = build_timeline_plan(cl, MEDIA, sync, WORDS_FREI, CFG)
    assert not [i for i in tp.items if i.track == "V2"] and any(m.color == "Red" for m in tp.markers)
    # Harte Kanten: Bereich endet bei 12,3 s → abgedeckt → V2 da.
    cl.beats[0].cuts[0].hart_out = True
    tp = build_timeline_plan(cl, MEDIA, sync, WORDS_FREI, CFG)
    assert [i for i in tp.items if i.track == "V2"] and not any(m.color == "Red" for m in tp.markers)


def test_v2_skipped_when_offset_leaves_a7_clip():
    # Paar behauptet Abdeckung, aber der Versatz schiebt den a7-Bereich hinter das a7-Ende (8000 Frames).
    sync = {"fps": 25, "paare": [dict(SYNC["paare"][0], offset_s=310.0, offset_frames=7750)]}
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    tp = build_timeline_plan(cl, MEDIA, sync, WORDS_FREI, CFG)
    assert not [i for i in tp.items if i.track == "V2"] and any(m.color == "Red" for m in tp.markers)


def test_src_out_clamped_to_clip_end():
    media = {"format": MEDIA["format"], "clips": {FX: {"original": {"duration_s": 12.5, "nb_frames": 312}}}}
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    tp = build_timeline_plan(cl, media, {"fps": 25, "paare": []}, WORDS_FREI, CFG)
    assert tp.items[0].src_out_f == 312 and tp.total_frames == 312 - tp.items[0].src_in_f


def test_fps_and_format_come_from_media():
    media = {"format": {"fps": 50, "width": 2160, "height": 3840}, "clips": MEDIA["clips"]}
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")]),
              Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6)])
    tp = build_timeline_plan(cl, media, {"fps": 50, "paare": []}, WORDS_FREI, CFG)
    assert (tp.fps, tp.width, tp.height) == (50.0, 2160, 3840)
    assert tp.items[0].src_in_f == 500 - 6 and tp.beats[1].rec_in_f == tp.beats[0].rec_out_f + 50
    assert tp.beats[1].rec_out_f - tp.beats[1].rec_in_f == 300


def test_errors_are_german_and_actionable():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip="/nas/FEHLT.MP4", cuts=[Cut(10.0, 12.3, "x")])])
    with pytest.raises(AutoCutError, match="media.json"):
        build_timeline_plan(cl, MEDIA, SYNC, WORDS, CFG)
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[])])
    with pytest.raises(AutoCutError, match="Beat #1"):
        build_timeline_plan(cl, MEDIA, SYNC, WORDS, CFG)
    cl = _cl([Beat(nr="2", szene="VO", typ="vo")])
    with pytest.raises(AutoCutError, match="platzhalter_s"):
        build_timeline_plan(cl, MEDIA, SYNC, WORDS, CFG)
    cl = _cl([Beat(nr="3", szene="X", typ="musik", platzhalter_s=3)])
    with pytest.raises(AutoCutError, match="Typ"):
        build_timeline_plan(cl, MEDIA, SYNC, WORDS, CFG)


def test_empty_cutlist_gives_empty_plan():
    tp = build_timeline_plan(_cl([]), MEDIA, SYNC, WORDS, CFG)
    assert tp.items == [] and tp.markers == [] and tp.beats == [] and tp.total_frames == 0


def test_to_dict_from_dict_roundtrip():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")]),
              Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6)])
    tp = build_timeline_plan(cl, MEDIA, SYNC, WORDS_FREI, CFG)
    d = tp.to_dict()
    assert set(d) == {"fps", "width", "height", "items", "markers", "beats", "total_frames"}
    assert d["beats"][0] == {"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 72, "clip": FX, "person": None}
    assert d["items"][2] == {"track": "V2", "clip": A7, "src_in_f": 294, "src_out_f": 366, "rec_in_f": 0, "rec_out_f": 72,
                             "enabled": True, "beat_nr": "1", "kind": "oton", "video_only": False, "tempo": 1}
    assert TimelinePlan.from_dict(d) == tp
    assert Item.from_dict(d["items"][0]) == tp.items[0] and MarkerSpec.from_dict(d["markers"][0]) == tp.markers[0]
    # Positionale Signaturen wie in den Tests der Tasks 8/9/11
    assert TimelinePlan(25, 3840, 2160, [Item("V1", FX, 244, 316, 0, 72)], [MarkerSpec(0, "#1 Hook", "", "Blue")],
                        [BeatPos("1", "oton", 0, 72, FX, "Sandra")], 72).total_frames == 72
    assert Item("V3", A7, 0, 50, 100, 150, video_only=True).video_only and Item("A2", A7, 0, 1, 0, 1, enabled=False).enabled is False


def test_v2_coverage_uses_clip_end_when_handle_exceeds_clip():
    """Cut endet kurz vor dem Clip-Ende (12,5 s = 312 Frames); der Nachlauf (0,32 s) ragt darüber hinaus.
    Das Paar deckt den Clip bis zum Ende ab → V2 wird gesetzt, obwohl out+Handle > overlap_ref[1]."""
    media = {"format": MEDIA["format"], "clips": {FX: {"original": {"duration_s": 12.5, "nb_frames": 312}},
                                                 A7: MEDIA["clips"][A7]}}
    sync = {"fps": 25, "paare": [dict(SYNC["paare"][0], overlap_ref=[0.0, 12.5])]}
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.4, "x")])])
    tp = build_timeline_plan(cl, media, sync, {FX: _S1}, CFG)
    v1 = [i for i in tp.items if i.track == "V1"][0]
    v2 = [i for i in tp.items if i.track == "V2"]
    assert v1.src_out_f == 312 and v2 and (v2[0].src_in_f, v2[0].src_out_f) == (v1.src_in_f + 50, 312 + 50)
    assert not any(m.color == "Red" for m in tp.markers)


def test_missing_config_or_format_is_reported_in_german():
    cl = _cl([Beat(nr="1", szene="A", typ="oton", clip=FX, cuts=[Cut(10.0, 12.3, "x")])])
    with pytest.raises(AutoCutError, match="handle_in_frames"):
        build_timeline_plan(cl, MEDIA, SYNC, WORDS, {"pause_s": 1.0})
    with pytest.raises(AutoCutError, match="media.json"):
        build_timeline_plan(cl, {"clips": MEDIA["clips"]}, SYNC, WORDS, CFG)


def test_v2_has_no_a2_items_and_item_has_tempo():
    from niro_autocut.timeline_model import Item
    it = Item("V3", "/nas/b.MP4", 0, 100, 0, 100)
    assert it.tempo == 1 and Item.from_dict({**it.to_dict(), "tempo": 2}).tempo == 2
