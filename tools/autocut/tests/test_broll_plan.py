"""Tests für broll_plan.py — Modell, harte Prüfung (Spec 5), V3-Items, kompakter Index, Profil, Bericht."""
from __future__ import annotations

import json

import pytest

from niro_autocut.broll_plan import (BrollBeat, BrollItem, BrollPlan, _usable_spans, build_v3_items, check_files,
                                     compact_index, load_profile, render_broll_plan_md, resolve_clip_ref, verify_broll_plan)
from niro_autocut.charge import AutoCutError
from niro_autocut.cutlist import Beat, Cut, Cutlist, Sperre

CFG = {"first_appearance_visible_s": 2.5, "min_len_s": 2.0, "max_len_s": 5.0, "montage_len_s": [1.5, 3.0],
       "fast_cuts_len_s": [1.0, 2.0], "max_coverage": 0.8, "tail_free_s": 1.5, "tail_free_min_beat_s": 8.0,
       "forbidden_maengel": ["Blick in Kamera"]}
TP = {"fps": 25, "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 250, "person": "Sandra"},
                           {"nr": "2", "typ": "vo", "rec_in_f": 275, "rec_out_f": 425, "person": None}]}
FX1, FX2 = "/nas/B-Roll/Flur/FX3_1.MP4", "/nas/B-Roll/Flur/FX3_2.MP4"
IDX = {"clips": [{"path": FX1, "ordner": "Flur", "dauer_s": 12.0, "beschreibung_kurz": "Pflegerin geht Flur entlang",
                  "abschnitte": [{"von_s": 0, "bis_s": 12, "beschreibung": "", "qualitaet": 4, "verwendbar": True}],
                  "maengel": [], "tags": ["Flur"], "qualitaet_gesamt": 4, "einstellung": "Halbtotale", "kamerabewegung": "Gimbal"},
                 {"path": FX2, "ordner": "Flur", "dauer_s": 8.0, "beschreibung_kurz": "Blick in Kamera",
                  "abschnitte": [{"von_s": 0, "bis_s": 8, "beschreibung": "", "qualitaet": 2, "verwendbar": False}],
                  "maengel": ["Blick in Kamera"], "tags": [], "qualitaet_gesamt": 2, "einstellung": "Nah", "kamerabewegung": "statisch"}]}
CL = Cutlist("v", None, 25, "16:9", 1.0, [Beat("1", "Hook", "oton", person="Sandra", clip="/nas/FX3_1.MP4", cuts=[Cut(10, 20, "x")]),
                                          Beat("2", "VO", "vo", platzhalter_s=6)])


# --------------------------------------------------------------------------- #
# Tests aus dem Plan
# --------------------------------------------------------------------------- #

def test_valid_plan_builds_items_and_markers():
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 1.0, 4.0, 3.0, "passt")]),
                         BrollBeat("2", [BrollItem(FX1, 5.0, 8.0, 0.0, "", abweichung=True, abweichung_grund="besser")])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert not r.ok  # Clip zweimal verwendet
    bp.beats[1].items = []
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert r.ok, r.errors
    items, markers = build_v3_items(bp, TP, 25)
    assert items[0].track == "V3" and items[0].video_only and items[0].rec_in_f == 75 and items[0].rec_out_f == 150 and items[0].src_in_f == 25
    assert items[0].src_out_f == 100 and items[0].kind == "broll" and items[0].beat_nr == "1" and items[0].enabled
    assert markers == []


def test_rules_first_appearance_length_forbidden_and_bounds():
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 1.0, 0.0)])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert any("Sprecher" in e for e in r.errors) and any("zu kurz" in e for e in r.errors)
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX2, 0.0, 3.0, 3.0)])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert any("verwendbar" in e or "Mangel" in e for e in r.errors)
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 4.0, 8.0)])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert any("Beat-Ende" in e for e in r.errors)


def test_placeholder_must_be_filled_and_no_overlap():
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 3.0, 0.0), BrollItem(FX1, 4.0, 7.0, 2.0)])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert any("überschneid" in e for e in r.errors)


def test_compact_index_fields():
    c = compact_index(IDX)[0]
    assert set(c) >= {"datei", "ordner", "kurz", "abschnitte", "tags", "maengel", "qualitaet", "einstellung", "bewegung", "dauer_s"}


# --------------------------------------------------------------------------- #
# Modell: Laden/Speichern, Feldprüfung
# --------------------------------------------------------------------------- #

def test_roundtrip_and_list_form(tmp_path):
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 1.0, 4.0, 3.0, "passt", True, "besser")])])
    p = tmp_path / "broll_plan.json"
    bp.save(p)
    back = BrollPlan.load(p)
    assert back == bp and back.beats[0].items[0].abweichung_grund == "besser"
    # Spec-Form: nackte Liste von Beats ist ebenfalls gültig (video bleibt leer)
    p.write_text(json.dumps([{"beat_nr": "2", "items": [{"clip": FX1, "in_s": 0, "out_s": 2, "start_offset_s": 0}]}]),
                 encoding="utf-8")
    lst = BrollPlan.load(p)
    assert lst.video == "" and lst.beats[0].beat_nr == "2" and lst.beats[0].items[0].out_s == 2.0


def test_unknown_field_and_missing_file_raise(tmp_path):
    p = tmp_path / "broll_plan.json"
    p.write_text(json.dumps({"video": "v", "beats": [{"beat_nr": "1", "items": [
        {"clip": FX1, "in_s": 0, "out_s": 2, "start_offset": 0}]}]}), encoding="utf-8")
    with pytest.raises(AutoCutError, match="unbekannte Felder"):
        BrollPlan.load(p)
    with pytest.raises(AutoCutError, match="fehlt"):
        BrollPlan.load(tmp_path / "nicht-da.json")


# --------------------------------------------------------------------------- #
# Einzelne Regeln
# --------------------------------------------------------------------------- #

def _idx(*clips: dict) -> dict:
    return {"clips": [dict(IDX["clips"][0], **c) for c in clips]}


def test_tail_free_and_coverage():
    tp = {"fps": 25, "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 250, "person": "Sandra"}]}
    # Beat 10 s ≥ 8 s: die letzten 1,5 s müssen frei bleiben → Item 6–10 s verletzt das
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 4.0, 6.0)])])
    r = verify_broll_plan(bp, tp, IDX, CL, CFG, 25)
    assert any("letzten" in e and "frei" in e for e in r.errors)
    # 3 s + 5 s = 8 s von 10 s = 80 % → gerade noch erlaubt; 3 + 5 + ... 8,5 s → zu viel
    idx = _idx({"path": FX1}, {"path": "/nas/B-Roll/Tisch/FX3_3.MP4", "ordner": "Tisch"})
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 3.0, 2.5), BrollItem("/nas/B-Roll/Tisch/FX3_3.MP4", 0.0, 3.0, 5.5)])])
    r = verify_broll_plan(bp, tp, idx, CL, CFG, 25)
    assert not any("abgedeckt" in e for e in r.errors), r.errors
    # 5 s + 4 s lückenlos = 9 s von 10 s = 90 % → zu viel (Abdeckung zählt die Vereinigung, nicht die Summe)
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 5.0, 0.0), BrollItem("/nas/B-Roll/Tisch/FX3_3.MP4", 0.0, 4.0, 5.0)])])
    r = verify_broll_plan(bp, tp, idx, CL, CFG, 25)
    assert any("abgedeckt" in e and "90 %" in e for e in r.errors)


def test_fast_cuts_and_montage_lengths():
    cl = Cutlist("v", None, 25, "16:9", 1.0, [Beat("4", "Welt 1", "bild", platzhalter_s=7, kommentar="Nur S1! Schnelle Cuts. ~7 s"),
                                              Beat("5", "Welt 2", "vo", platzhalter_s=6)])
    tp = {"fps": 25, "beats": [{"nr": "4", "typ": "bild", "rec_in_f": 0, "rec_out_f": 175, "person": None},
                               {"nr": "5", "typ": "vo", "rec_in_f": 200, "rec_out_f": 350, "person": None}]}
    idx = _idx({"path": FX1, "standort": "Standort 1"}, {"path": "/nas/B-Roll/Tisch/FX3_3.MP4", "ordner": "Tisch", "standort": "Standort 1"})
    bp = BrollPlan("v", [BrollBeat("4", [BrollItem(FX1, 0.0, 1.5, 0.0), BrollItem("/nas/B-Roll/Tisch/FX3_3.MP4", 0.0, 2.5, 1.5)])])
    r = verify_broll_plan(bp, tp, idx, cl, CFG, 25)
    assert any("zu lang" in e and "Schnelle Cuts" in e for e in r.errors) and not any("zu kurz" in e for e in r.errors)
    bp = BrollPlan("v", [BrollBeat("5", [BrollItem(FX1, 0.0, 3.5, 0.0)])])
    r = verify_broll_plan(bp, tp, idx, cl, CFG, 25)
    assert any("zu lang" in e and "Montage" in e for e in r.errors)


def test_standort_rule_from_plan_comment():
    cl = Cutlist("v", None, 25, "16:9", 1.0, [Beat("4", "Welt 1", "bild", platzhalter_s=7, kommentar="Nur S1! Schnelle Cuts.")])
    tp = {"fps": 25, "beats": [{"nr": "4", "typ": "bild", "rec_in_f": 0, "rec_out_f": 175, "person": None}]}
    idx = _idx({"path": FX1, "standort": "Standort 2"})
    bp = BrollPlan("v", [BrollBeat("4", [BrollItem(FX1, 0.0, 1.5, 0.0)])])
    r = verify_broll_plan(bp, tp, idx, cl, CFG, 25)
    assert any("Nur S1" in e and "Standort 2" in e for e in r.errors)
    idx = _idx({"path": FX1, "standort": "Standort 1"})
    r = verify_broll_plan(bp, tp, idx, cl, CFG, 25)
    assert not any("Nur S1" in e for e in r.errors)


def test_sperre_abweichung_and_placeholder_warnings():
    cl = Cutlist("v", None, 25, "16:9", 1.0, [Beat("2", "VO", "vo", platzhalter_s=6)],
                 sperren=[Sperre(FX1, 2.0, 6.0, "Kunden-Tabu")])
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 4.0, 7.0, 0.0, abweichung=True)])])
    r = verify_broll_plan(bp, TP, IDX, cl, CFG, 25)
    assert any("Sperre" in e for e in r.errors) and any("abweichung_grund" in e for e in r.errors)
    # Platzhalter: 3 s von 6 s gefüllt → Warnung, kein Fehler; ohne Items → Warnung
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 3.0, 0.0, "Auftakt")])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert r.ok and any("Lücke" in w for w in r.warnings)
    bp = BrollPlan("v", [BrollBeat("2", [])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert r.ok and any("keine B-Roll" in w for w in r.warnings)
    # vollständig gefüllt (2 Clips aus verschiedenen Ordnern) → keine Lücken-Warnung, keine Ordner-Warnung
    idx = _idx({"path": FX1}, {"path": "/nas/B-Roll/Tisch/FX3_3.MP4", "ordner": "Tisch"})
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 3.0, 0.0, "a"), BrollItem("/nas/B-Roll/Tisch/FX3_3.MP4", 1.0, 4.0, 3.0, "b")])])
    r = verify_broll_plan(bp, TP, idx, CL, CFG, 25)
    assert r.ok and not r.warnings, r.warnings


def test_same_folder_consecutive_is_warning_duplicate_clip_is_error():
    idx = _idx({"path": FX1}, {"path": "/nas/B-Roll/Flur/FX3_3.MP4"})
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 3.0, 0.0, "a"), BrollItem("/nas/B-Roll/Flur/FX3_3.MP4", 1.0, 4.0, 3.0, "b")])])
    r = verify_broll_plan(bp, TP, idx, CL, CFG, 25)
    assert r.ok and any("Ordner" in w and "Flur" in w for w in r.warnings)
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 0.0, 3.0, 3.0, "a")]), BrollBeat("2", [BrollItem(FX1, 5.0, 8.0, 0.0, "b")])])
    r = verify_broll_plan(bp, TP, idx, CL, CFG, 25)
    assert any("zweimal" in e or "doppelt" in e for e in r.errors)


def test_unknown_beat_clip_and_bad_times():
    bp = BrollPlan("v", [BrollBeat("9", [BrollItem(FX1, 0.0, 3.0, 0.0)]),
                         BrollBeat("2", [BrollItem("/nas/B-Roll/Flur/FX3_99.MP4", 0.0, 3.0, 0.0)]),
                         BrollBeat("1", [BrollItem(FX1, 10.0, 14.0, 3.0)])])
    r = verify_broll_plan(bp, TP, IDX, CL, CFG, 25)
    assert any("Beat #9" in e for e in r.errors)
    assert any("FX3_99.MP4" in e and "Index" in e for e in r.errors)
    assert any("außerhalb des Clips" in e for e in r.errors)


def test_clip_ref_resolution_by_short_name():
    idx = {"clips": [{"path": "/nas/Standort 1/Sortiert/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "ordner": "Flur", "standort": "Standort 1"},
                     {"path": "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_1.MP4", "datei": "FX3_1.MP4", "ordner": "Tisch", "standort": "Standort 2"},
                     {"path": "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4", "datei": "FX3_2.MP4", "ordner": "Tisch", "standort": "Standort 2"}]}
    assert resolve_clip_ref("/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4", idx) == ("/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4", "")
    assert resolve_clip_ref("FX3_2.MP4", idx)[0] == "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4"
    assert resolve_clip_ref("Standort 1/Flur/FX3_1.MP4", idx)[0] == "/nas/Standort 1/Sortiert/B-Roll/Flur/FX3_1.MP4"
    assert resolve_clip_ref("Tisch/FX3_1.MP4", idx)[0] == "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_1.MP4"
    path, err = resolve_clip_ref("FX3_1.MP4", idx)
    assert path is None and "mehrdeutig" in err
    path, err = resolve_clip_ref("FX3_7.MP4", idx)
    assert path is None and "nicht im Index" in err
    # verify normalisiert Kurzreferenzen auf den vollen Pfad
    tp = {"fps": 25, "beats": [{"nr": "2", "typ": "vo", "rec_in_f": 0, "rec_out_f": 150, "person": None}]}
    idx["clips"][2].update({"dauer_s": 8.0, "abschnitte": [{"von_s": 0, "bis_s": 8, "beschreibung": "", "qualitaet": 4, "verwendbar": True}], "maengel": []})
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem("FX3_2.MP4", 0.0, 2.0, 0.0, "x")])])
    r = verify_broll_plan(bp, tp, idx, Cutlist("v", None, 25, "16:9", 1.0, [Beat("2", "VO", "vo", platzhalter_s=6)]), CFG, 25)
    assert r.ok, r.errors
    assert bp.beats[0].items[0].clip == "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4"


def test_usable_span_may_cross_adjacent_usable_sections():
    idx = _idx({"path": FX1, "abschnitte": [{"von_s": 0, "bis_s": 5, "beschreibung": "", "qualitaet": 4, "verwendbar": True},
                                            {"von_s": 5, "bis_s": 9, "beschreibung": "", "qualitaet": 4, "verwendbar": True},
                                            {"von_s": 9, "bis_s": 12, "beschreibung": "", "qualitaet": 1, "verwendbar": False}]})
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 3.0, 6.0, 0.0, "x")])])
    assert verify_broll_plan(bp, TP, idx, CL, CFG, 25).ok
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 7.0, 10.0, 0.0, "x")])])
    r = verify_broll_plan(bp, TP, idx, CL, CFG, 25)
    assert any("verwendbar" in e for e in r.errors)


# --------------------------------------------------------------------------- #
# V3-Items, Marker
# --------------------------------------------------------------------------- #

def test_build_v3_markers_yellow_and_free_frame():
    tp = dict(TP, markers=[{"frame": 275, "name": "#2 VO", "note": "", "color": "Yellow", "duration": 1}])
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 3.0, 0.0, "x", abweichung=True, abweichung_grund="besser als Plan"),
                                         BrollItem(FX2, 1.0, 4.0, 3.0, "y")])])
    items, markers = build_v3_items(bp, tp, 25)
    assert [i.rec_in_f for i in items] == [275, 350] and [i.rec_out_f for i in items] == [350, 425]
    assert all(i.track == "V3" and i.video_only and i.kind == "broll" for i in items)
    assert len(markers) == 1 and markers[0].color == "Yellow" and "abweichend" in markers[0].name
    assert markers[0].frame == 276 and "besser als Plan" in markers[0].note   # 275 ist vom Beat-Marker belegt


def test_build_v3_clamps_rounding_to_beat_end():
    tp = {"fps": 25, "beats": [{"nr": "2", "typ": "vo", "rec_in_f": 100, "rec_out_f": 150, "person": None}]}
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(FX1, 0.0, 1.03, 0.99)])])   # 0,99 + 1,03 = 2,02 s > 2,0 s
    items, _ = build_v3_items(bp, tp, 25)
    assert items[0].rec_out_f == 150 and items[0].src_out_f - items[0].src_in_f == items[0].rec_out_f - items[0].rec_in_f
    with pytest.raises(AutoCutError, match="Beat #7"):
        build_v3_items(BrollPlan("v", [BrollBeat("7", [BrollItem(FX1, 0.0, 1.0, 0.0)])]), tp, 25)


# --------------------------------------------------------------------------- #
# Dateien, kompakter Index, Profil, Bericht
# --------------------------------------------------------------------------- #

def test_check_files(tmp_path):
    clip = tmp_path / "B-Roll" / "Flur" / "FX3_1.MP4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem(str(clip), 0.0, 3.0, 0.0), BrollItem(str(tmp_path / "weg.MP4"), 0.0, 3.0, 3.0)])])
    probs = check_files(bp, {"clips": []})
    assert any("Proxy" in p for p in probs) and any("weg.MP4" in p and "nicht gefunden" in p for p in probs)
    (clip.parent / "Proxy").mkdir()
    (clip.parent / "Proxy" / "FX3_1.mov").write_bytes(b"y")
    assert check_files(BrollPlan("v", [BrollBeat("2", [BrollItem(str(clip), 0.0, 3.0, 0.0)])]), {"clips": []}) == []


def test_compact_index_content_and_order():
    idx = {"clips": [{"path": "/nas/Standort 2/Sortiert/B-Roll/Tisch/FX3_2.MP4", "ordner": "Tisch", "standort": "Standort 2", "dauer_s": 8.0,
                      "beschreibung_kurz": "Kolleginnen am Tisch", "einstellung": "Halbnah", "kamerabewegung": "statisch", "tempo": "ruhig",
                      "abschnitte": [{"von_s": 0, "bis_s": 5, "beschreibung": "Gespräch", "qualitaet": 4, "verwendbar": True},
                                     {"von_s": 5, "bis_s": 8, "beschreibung": "unscharf", "qualitaet": 1, "verwendbar": False}],
                      "maengel": ["Unschärfe"], "tags": ["Team"], "eignung": ["Team"], "qualitaet_gesamt": 3},
                     dict(IDX["clips"][0], standort="Standort 1")]}
    c = compact_index(idx)
    assert [x["standort"] for x in c] == ["Standort 1", "Standort 2"]
    t = c[1]
    assert t["ref"] == "Standort 2/Tisch/FX3_2.MP4" and t["datei"] == "FX3_2.MP4" and t["kurz"] == "Kolleginnen am Tisch"
    assert t["abschnitte"] == [{"von_s": 0, "bis_s": 5, "kurz": "Gespräch", "q": 4}] and t["bewegung"] == "statisch"
    assert t["qualitaet"] == 3 and t["maengel"] == ["Unschärfe"] and t["eignung"] == ["Team"] and t["verwendbar"] is True
    assert c[0]["ref"] == "Standort 1/Flur/FX3_1.MP4"


def test_load_profile_default():
    text, cfg = load_profile("default")
    assert "m/w/d" in text and "zwei Takes" in text.lower() or "2 Takes" in text
    assert "scene_min_shots" in cfg and "max_coverage" not in cfg
    with pytest.raises(AutoCutError, match="Profil"):
        load_profile("gibt-es-nicht")


def test_render_report():
    bp = BrollPlan("v", [BrollBeat("1", [BrollItem(FX1, 1.0, 4.0, 3.0, "passt zur Aussage")]),
                         BrollBeat("2", [BrollItem(FX2, 0.0, 3.0, 0.0, "", abweichung=True, abweichung_grund="Plan-Motiv fehlt")])])
    txt = render_broll_plan_md(bp, IDX, TP, CL, warnings=["W1"], build={"timeline": "AutoCut v 2026", "items": 2})
    assert "| 1 |" in txt and "FX3_1.MP4" in txt and "passt zur Aussage" in txt and "Plan-Motiv fehlt" in txt
    assert "W1" in txt and "AutoCut v 2026" in txt and "00:03" in txt and "Hook" in txt


def test_build_v3_items_uses_clip_fps_for_source_frames():
    """B-Roll mit 50/100 fps: Quellframes mit Clip-Bildrate, Record-Frames mit Timeline-Bildrate (Live-Befund 04.09.)."""
    tp = {"fps": 25, "beats": [{"nr": "2", "typ": "vo", "rec_in_f": 100, "rec_out_f": 250, "person": None}], "markers": []}
    bp = BrollPlan("v", [BrollBeat("2", [BrollItem("/nas/B-Roll/Flur/FX3_0010.MP4", 1.0, 3.0, 0.0),
                                         BrollItem("/nas/B-Roll/Flur/FX3_0011.MP4", 0.5, 2.5, 2.0),
                                         BrollItem("/nas/B-Roll/Flur/FX3_0012.MP4", 0.0, 2.0, 4.0)])])
    items, _ = build_v3_items(bp, tp, 25, {"/nas/B-Roll/Flur/FX3_0010.MP4": 50.0, "FX3_0011.MP4": 100.0})
    by = {i.clip.split("/")[-1]: i for i in items}
    assert (by["FX3_0010.MP4"].src_in_f, by["FX3_0010.MP4"].src_out_f) == (50, 150)   # 50 fps: 1,0–3,0 s
    assert (by["FX3_0010.MP4"].rec_in_f, by["FX3_0010.MP4"].rec_out_f) == (100, 150)  # 2 s = 50 Timeline-Frames
    assert (by["FX3_0011.MP4"].src_in_f, by["FX3_0011.MP4"].src_out_f) == (50, 250)   # 100 fps über Dateinamen
    assert (by["FX3_0012.MP4"].src_in_f, by["FX3_0012.MP4"].src_out_f) == (0, 50)     # ohne Eintrag: Timeline-fps


def test_build_v3_items_snaps_rounding_overlap_to_previous_item():
    """Offsets 1,75/3,5/5,25 s runden auf 44/88/131 Frames — der dritte Clip würde den zweiten um 1 Frame überlappen."""
    tp = {"fps": 25, "beats": [{"nr": "4", "typ": "bild", "rec_in_f": 433, "rec_out_f": 608, "person": None}], "markers": []}
    bp = BrollPlan("v", [BrollBeat("4", [BrollItem("/nas/B-Roll/A/FX3_1.MP4", 0.5, 2.25, 0.0),
                                         BrollItem("/nas/B-Roll/B/FX3_2.MP4", 4.5, 6.25, 1.75),
                                         BrollItem("/nas/B-Roll/C/FX3_3.MP4", 8.5, 10.25, 3.5),
                                         BrollItem("/nas/B-Roll/D/FX3_4.MP4", 1.0, 2.75, 5.25)])])
    items, _ = build_v3_items(bp, tp, 25)
    recs = [(i.rec_in_f, i.rec_out_f) for i in items]
    assert all(b[0] >= a[1] for a, b in zip(recs, recs[1:]))     # keine Überlappung
    assert recs[-1][1] <= 608                                       # innerhalb des Beats
    assert recs == [(433, 477), (477, 521), (521, 565), (565, 608)]


def test_usable_spans_nimmt_stabile_bereiche_nur_auf_wunsch_auf():
    """Plan v1 ruft ohne den Parameter auf und darf sich nicht ändern (Spec 2026-09-23). Die verworfenen
    Abschnitte tragen den Schlüssel maengel (auch leer) — dieselbe Vorbedingung wie compact_index_v2 für die
    Rettung (Review-Fund I3); ohne den Schlüssel siehe die Gegenprobe unten."""
    c = {"abschnitte": [{"von_s": 0, "bis_s": 2, "verwendbar": False, "maengel": [], "stabil": [[0.0, 2.0, 0.05, 0.3]]},
                        {"von_s": 2, "bis_s": 5, "verwendbar": False, "maengel": [], "stabil": [[2.0, 4.8, 0.07, 0.3]]},
                        {"von_s": 5, "bis_s": 9, "verwendbar": True}]}
    assert _usable_spans(c) == [(5.0, 9.0)]
    # angrenzende gerettete Bereiche werden zusammengelegt — ein Shot darf über die Abschnittsgrenze laufen
    assert _usable_spans(c, stabil=True) == [(0.0, 4.8), (5.0, 9.0)]


def test_usable_spans_ignoriert_stabil_ohne_maengel_schluessel():
    """Review-Fund I3: ein alter Cache ohne den Schlüssel maengel am Abschnitt wird nie gerettet — der
    Verwerfungsgrund ist unbekannt, dieselbe Vorbedingung wie compact_index_v2 (Spec 2026-09-23)."""
    c = {"abschnitte": [{"von_s": 0, "bis_s": 2, "verwendbar": False, "stabil": [[0.0, 2.0, 0.05, 0.3]]},
                        {"von_s": 2, "bis_s": 5, "verwendbar": False, "stabil": [[2.0, 4.8, 0.07, 0.3]]},
                        {"von_s": 5, "bis_s": 9, "verwendbar": True}]}
    assert _usable_spans(c, stabil=True) == [(5.0, 9.0)]
