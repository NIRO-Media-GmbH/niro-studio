"""Tests für broll_layout.py — Plan v2, Fenster/Strecken/Raster (Teil 1), Prüfung/Platzierung (Teil 2, Task 10)."""
from __future__ import annotations

import json

import pytest

from niro_autocut import broll_layout as L
from niro_autocut import telemetrie as TM
from niro_autocut.charge import AutoCutError
from niro_autocut.cutlist import Beat, Cut, Cutlist

# telemetrie: wie defaults.yaml (Fix-Runde 1 zu Task 3) — cfg_broll allein trägt diesen Geschwister-Schlüssel in
# Produktion nie; ohne ihn im Test-CFG griff cfg.get("telemetrie") in broll_layout.py unbemerkt immer ins Leere.
CFG_TELEMETRIE = {"fenster_s": 2.0, "schritt_s": 1.0, "tiefpass_s": 0.5, "ruhig_max_px": 0.15, "stativ_max_grad_s": 0.3,
                  "stativ_max_px": 0.02, "schwenk_min_grad_s": 3.0, "schwenk_min_px": 1.0, "hf_grenze_hz": 3.0,
                  "hand_hf_anteil_min": 0.15, "pitch_klassen_grad": [-60, -8, 8], "achsen": {"schwenk": 1, "tilt": 0},
                  "vorzeichen": {"schwenk": 1, "tilt": -1, "pitch": 1}, "px_faktor": {"FX3": 0.60, "a7IV": 0.69},
                  "optisch_fuer": [], "optisch_breite": 480, "parallel": 2, "zoom_min_proz": 3.0, "zoom_rausch_proz_s": 1.0,
                  "zoom_schnell_proz_s": 100.0, "zoom_ruck_max": 1.0, "zoom_stocken_anteil": 0.0, "zoom_sprung_proz": 12.0,
                  "zoom_verlauf_hz": 5, "brennweite_gleich_max": 0.20, "digitalzoom_faktor": 1.25, "digitalzoom_max": 1.5,
                  "bewegung_rand_s": 0.5, "bewegung_spitze_faktor": 3.0}
CFG = {"face_share": [0.15, 0.20], "face_share_hard": [0.12, 0.23], "window_first_s": 2.5, "window_s": 2.0, "window_min_s": 1.5,
       "window_max_s": 4.0, "full_face_beat_max_s": 3.0, "full_face_keywords": ["Gehaltenes Gesicht", "Bookend"],
       "shot_len_s": [2.0, 5.0], "shot_len_slow_max_s": 6.0, "montage_len_s": [1.5, 3.0], "fast_cuts_len_s": [1.0, 2.0],
       "scene_min_shots": 3, "scene_short_stretch_s": 6.0, "setup_hash_min_distance": 10, "max_exceptions_warn": 3,
       "forbidden_maengel": ["Blick in Kamera", "Crew im Bild", "Logo/Marke"], "telemetrie": CFG_TELEMETRIE}
FX = "/nas/Interviews/Anna/FX3_1.MP4"
# Beats: 1 Hook 2,3 s | Pause 1 s | 2 VO 6 s | Pause | 3 O-Ton Anna 8 s | Pause | 4 O-Ton Bea 10 s (Bookend-Wort nicht) | Pause | 5 Grafik 4 s
TP = {"fps": 25, "total_frames": 875, "beats": [
    {"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 58, "person": "Anna", "clip": FX},
    {"nr": "2", "typ": "vo", "rec_in_f": 83, "rec_out_f": 233, "person": None},
    {"nr": "3", "typ": "oton", "rec_in_f": 258, "rec_out_f": 458, "person": "Anna", "clip": FX},
    {"nr": "4", "typ": "oton", "rec_in_f": 483, "rec_out_f": 733, "person": "Bea", "clip": FX},
    {"nr": "5", "typ": "grafik", "rec_in_f": 758, "rec_out_f": 858, "person": None}]}
CL = Cutlist("v.md", None, 25, "16:9", 1.0, [
    Beat("1", "Kaltstart", "oton", person="Anna", clip=FX, cuts=[Cut(1, 3)], bild_hinweis="Gehaltenes Gesicht"),
    Beat("2", "VO", "vo", platzhalter_s=6, bild_hinweis="Gesichter-Montage"),
    Beat("3", "Mensch", "oton", person="Anna", clip=FX, cuts=[Cut(10, 18)]),
    Beat("4", "Team", "oton", person="Bea", clip=FX, cuts=[Cut(20, 30)], kommentar="Schnelle Cuts"),
    Beat("5", "Endcard", "grafik", platzhalter_s=4)])


def test_plan_v2_roundtrip_and_v1_rejected(tmp_path):
    d = {"version": 2, "video": "v.md", "fenster": [{"beat_nr": "3", "dauer_s": 3.0, "grund": "x"}],
         "strecken": [{"nr": 1, "szenen": [{"ordner": "Standort 1/Flur", "shots": [{"clip": "Flur/FX3_9.MP4", "in_s": 1.0, "out_s": 4.0}]}]}]}
    p = L.LayoutPlan.from_dict(d)
    assert p.fenster[0].dauer_s == 3.0 and p.strecken[0].szenen[0].shots[0].tempo == 1 and p.strecken[0].szenen[0].shots[0].dauer_tl_s() == 3.0
    f = tmp_path / "plan.json"
    p.save(f)
    assert L.LayoutPlan.load(f).to_dict()["strecken"][0]["szenen"][0]["ordner"] == "Standort 1/Flur"
    with pytest.raises(AutoCutError, match="raster"):
        L.LayoutPlan.from_dict({"video": "v", "beats": []})
    with pytest.raises(AutoCutError):
        L.LayoutPlan.from_dict({**d, "strecken": [{"nr": 1, "szenen": [{"ordner": "x", "shots": [{"clip": "c", "in_s": 1, "out_s": 2, "tempo": 3}]}]}]})


def test_default_windows_full_face_and_first_appearance():
    w = {x.beat_nr: x for x in L.default_windows(TP, CL, CFG)}
    assert w["1"].voll is True                        # Beat 1 + Schlüsselwort + < 3 s
    assert w["3"].dauer_s == 2.0 and w["4"].dauer_s == 2.5 and "2" not in w and "5" not in w   # Anna war im Hook schon zu sehen
    cl2 = Cutlist("v", None, 25, "16:9", 1.0, CL.beats + [Beat("6", "Nochmal", "oton", person="Anna", clip=FX, cuts=[Cut(40, 45)])])
    tp2 = {**TP, "beats": TP["beats"] + [{"nr": "6", "typ": "oton", "rec_in_f": 883, "rec_out_f": 1008, "person": "Anna"}], "total_frames": 1008}
    w2 = {x.beat_nr: x for x in L.default_windows(tp2, cl2, CFG)}
    assert w2["6"].dauer_s == 2.0


def test_window_frames_stretches_and_face_share():
    plan = L.LayoutPlan("v.md", [L.Fenster("3", 0.0, 3.0), L.Fenster("3", 5.0, 1.5, grund="Peak")], [])
    wins = L.effective_windows(plan, TP, CL, CFG)
    wf, errs = L.window_frames(wins, TP, 25, CFG)
    assert errs == []
    # Beat 4 Fenster: window_first_s=2,5 s @ 25 fps = genau 62,5 Frames — seconds_to_frames() rundet mit Pythons
    # round() (Bankers Rounding) auf 62, nicht 63; 483+62=545. Von der Brief-Vorlage (546/546/63) abweichend korrigiert.
    assert [(x["beat_nr"], x["a_f"], x["b_f"]) for x in wf] == [("1", 0, 58), ("3", 258, 333), ("3", 383, 421), ("4", 483, 545)]
    st = L.stretches(wf, TP["total_frames"])
    assert [(s["nr"], s["von_f"], s["bis_f"]) for s in st] == [(1, 58, 258), (2, 333, 383), (3, 421, 483), (4, 545, 875)]
    assert round(L.face_share(wf, TP["total_frames"]), 3) == round((58 + 75 + 38 + 62) / 875, 3)
    bad = L.LayoutPlan("v.md", [L.Fenster("3", 7.0, 3.0)], [])          # ragt über das Beat-Ende
    _, errs = L.window_frames(L.effective_windows(bad, TP, CL, CFG), TP, 25, CFG)
    assert errs and "Beat" in errs[0]
    _, errs = L.window_frames(L.effective_windows(L.LayoutPlan("v.md", [L.Fenster("2", 0.0, 2.0)], []), TP, CL, CFG), TP, 25, CFG)
    assert errs and "O-Ton" in errs[0]


def test_raster_lists_stretches_with_beats_and_hints():
    r = L.raster(TP, CL, CFG)
    assert r["fps"] == 25 and len(r["strecken"]) == 3 and r["gesicht_anteil"] > 0
    s1 = r["strecken"][0]
    assert s1["von_s"] == 2.32 and [b["nr"] for b in s1["beats"]] == ["2"] and "Gesichter-Montage" in s1["hinweise"][0]
    md = L.render_raster_md(r, CL, TP)
    assert "Strecke 1" in md and "Gesichter-Montage" in md and "Gesicht" in md


def test_shot_tempo_zero_is_rejected():
    with pytest.raises(AutoCutError):
        L.Shot.from_dict({"clip": "c", "in_s": 1, "out_s": 2, "tempo": 0})


def test_strecke_nr_non_integer_is_rejected():
    with pytest.raises(AutoCutError):
        L.Strecke.from_dict({"nr": "eins", "szenen": []})


def test_window_frames_dauer_ausserhalb_bereich():
    plan = L.LayoutPlan("v.md", [L.Fenster("3", 0.0, 5.0)], [])          # window_max_s ist 4,0
    wins = L.effective_windows(plan, TP, CL, CFG)
    _, errs = L.window_frames(wins, TP, 25, CFG)
    assert errs and "außerhalb" in errs[0]


def test_window_frames_overlap_on_same_beat_is_rejected():
    plan = L.LayoutPlan("v.md", [L.Fenster("3", 0.0, 3.0), L.Fenster("3", 1.0, 3.0)], [])
    wins = L.effective_windows(plan, TP, CL, CFG)
    _, errs = L.window_frames(wins, TP, 25, CFG)
    assert errs and "überschneiden" in errs[0]


def test_beat_at_pause_and_before_first_beat():
    assert L.beat_at(TP, 70)["nr"] == "1"     # Pause zwischen Beat 1 (bis 58) und Beat 2 (ab 83) → voriger Beat
    assert L.beat_at(TP, -1) is None          # vor dem ersten Beat


def test_layoutplan_load_missing_and_malformed(tmp_path):
    with pytest.raises(AutoCutError):
        L.LayoutPlan.load(tmp_path / "missing.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(AutoCutError):
        L.LayoutPlan.load(bad)


# --------------------------------------------------------------------------- #
# Teil 2: Platzierung, Prüfung, V3-Items (Task 10)
# --------------------------------------------------------------------------- #

def _idx(n=6, fps=25.0, ordner="Flur"):
    def clip(i, einst, ansicht, brenn, fps_=fps, hash_="0" * 16):
        return {"path": f"/nas/Standort 1/Sortiert/B-Roll/{ordner}/FX3_{i}.MP4", "datei": f"FX3_{i}.MP4", "ordner": ordner, "standort": "Standort 1",
                "dauer_s": 12.0, "fps": fps_, "beschreibung_kurz": f"Clip {i}", "maengel": [], "qualitaet_gesamt": 4, "personen": {"blick_in_kamera": False},
                "abschnitte": [{"von_s": 0, "bis_s": 12, "beschreibung": "", "qualitaet": 4, "verwendbar": True, "einstellung": einst,
                                "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": ansicht, "brennweite": brenn,
                                "bewegungsrichtung": "keine", "hauptmotiv": "x", "setup_hash": hash_}]}
    return {"clips": [clip(1, "Totale", "ohne Person", "weit"), clip(2, "Halbnah", "seitlich", "normal"), clip(3, "Detail", "ohne Person", "tele"),
                      clip(4, "Totale", "ohne Person", "weit"), clip(5, "Halbtotale", "frontal", "normal", 50.0), clip(6, "Nah", "frontal", "tele")]}


def _plan(shots_per_strecke):
    strecken = []
    for nr, shots in shots_per_strecke.items():
        strecken.append(L.Strecke(nr, [L.Szene("Standort 1/Flur", [L.Shot(*s) for s in shots])]))
    return L.LayoutPlan("v.md", [], strecken)


def test_place_shots_fills_stretch_and_trims_last_shot():
    idx = _idx()
    # Strecke 1 = 58..258 (200 Frames = 8 s) mit Standardfenstern
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs == []
    assert [(p["rec_in_f"], p["rec_out_f"]) for p in placed if p["strecke"] == 1] == [(58, 133), (133, 208), (208, 258)]
    assert placed[2]["out_s"] == 2.0                           # letzter Shot auf 2 s gekürzt
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.5)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert placed[2]["rec_out_f"] == 258 and placed[2]["out_s"] == 2.0    # letzter Shot auf die Reststrecke verkürzt/verlängert
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 5.0), ("Flur/FX3_2.MP4", 1.0, 5.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert not errs and placed[1]["rec_out_f"] == 258                        # 5 + 3 s → letzter Shot 3 s
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 5.0), ("Flur/FX3_2.MP4", 1.0, 5.0), ("Flur/FX3_3.MP4", 0.0, 5.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs and "Strecke 1" in errs[0]                                    # Überlauf: zweiter Shot ragt schon über das Streckenende


def test_place_shots_tempo_conform_and_invalid_fps():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 2.0, 2), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs == []
    p = placed[0]
    assert (p["rec_in_f"], p["rec_out_f"], p["src_in_f"], p["src_out_f"], p["roh_out_f"]) == (58, 158, 0, 100, 108)
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 2.0, 2), ("Flur/FX3_2.MP4", 0.0, 3.0), ("Flur/FX3_3.MP4", 0.0, 3.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs and "tempo" in errs[0]                                        # 25p-Clip kann kein 2×


def test_verify_layout_rules():
    idx = _idx()
    ok = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)],
                2: [("Flur/FX3_4.MP4", 0.0, 2.0), ("Flur/FX3_6.MP4", 0.0, 2.0), ("Flur/FX3_5.MP4", 0.0, 2.0)],
                3: [("Flur/FX3_4.MP4", 5.0, 7.0), ("Flur/FX3_6.MP4", 5.0, 7.0), ("Flur/FX3_5.MP4", 5.0, 7.0)]})
    r = L.verify_layout(ok, TP, idx, CL, CFG, 25)
    assert any("zweimal" in e for e in r.errors)                             # Clip 4/5/6 doppelt (Strecke 2 und 3)
    ok.strecken[2].szenen[0].shots = [L.Shot("Flur/FX3_2.MP4", 6.0, 8.0), L.Shot("Flur/FX3_3.MP4", 6.0, 8.0), L.Shot("Flur/FX3_1.MP4", 6.0, 8.0)]
    r = L.verify_layout(ok, TP, idx, CL, CFG, 25)
    assert any("zweimal" in e for e in r.errors)
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_4.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)], 2: [], 3: []})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    assert any("Einstellung" in e and "Perspektive" in e for e in r.errors)  # 1 → 4 gleich (Totale/ohne Person/weit)
    assert any("Strecke 2" in e and "leer" in e for e in r.errors)           # Schwarz
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 4.0), ("Flur/FX3_2.MP4", 1.0, 5.0)], 2: [], 3: []})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    # Auf "Szene"+"3" allein kann man hier nicht prüfen: jeder Clipname ("FX3_…") enthält bereits eine "3", und die
    # leeren Strecken 2/3 melden unabhängig von Streckes 1 Ausnahme dauerhaft ihre eigene <3-Shots-Regel. Die Prüfung
    # zielt daher auf den genauen Regeltext, auf Strecke 1 eingegrenzt (empirisch verifiziert, siehe Report Task 10).
    assert any("Strecke 1 Szene" in e and "mindestens" in e for e in r.errors)  # < 3 Shots ohne Ausnahme
    plan.strecken[0].szenen[0].ausnahme = "Plan: Gesichter-Montage"
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    assert not any("Strecke 1 Szene" in e and "mindestens" in e for e in r.errors)


def test_verify_layout_face_share_and_missing_sections():
    idx = _idx()
    for c in idx["clips"]:
        c["abschnitte"][0].pop("brennweite")
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    assert any("Nachlauf" in e for e in r.errors)
    plan = L.LayoutPlan("v.md", [L.Fenster("3", 0.0, 4.0), L.Fenster("3", 4.5, 3.5), L.Fenster("4", 0.0, 4.0), L.Fenster("4", 5.0, 4.0)], [])
    r = L.verify_layout(plan, TP, _idx(), CL, CFG, 25)
    assert any("Gesichtsanteil" in e for e in r.errors)


def test_build_v3_items_v2_and_markers():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 2.0, 2), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    items, markers = L.build_v3_items_v2(placed, 25)
    assert [(i.track, i.rec_in_f, i.rec_out_f, i.src_in_f, i.src_out_f, i.tempo, i.video_only) for i in items][:1] == [("V3", 58, 108, 0, 100, 2, True)]
    assert markers[0].color == "Cyan" and markers[0].name.startswith("Szene 1") and markers[0].frame == 58
    cx = L.compact_index_v2(idx)
    assert cx[0]["abschnitte"][0]["einstellung"] == "Totale" and "perspektive" in cx[0]["abschnitte"][0]


# --------------------------------------------------------------------------- #
# Fix round 1 (Review Task 10): Toleranz nur letzter Shot, Tempo-Rest, Kleinteile
# --------------------------------------------------------------------------- #

def test_verify_layout_length_tolerance_only_applies_to_last_shot():
    """Die 0,5-s-Übertoleranz gilt nur für den letzten Shot einer Strecke — sonst würde jeder
    Shot beliebig lang sein dürfen, sobald er (zufällig) selbst der letzte in seiner Szene ist."""
    idx = _idx()
    # Eigene kleine Timeline (ein einziger VO/Montage-Beat über die ganze Strecke), damit die
    # Montage-Grenzen (1,5-3,0 s) unabhängig von der TP/CL-Fixture direkt greifen.
    tp = {"fps": 25, "total_frames": 300, "beats": [{"nr": "1", "typ": "vo", "rec_in_f": 0, "rec_out_f": 300, "person": None}]}
    cl = Cutlist("v.md", None, 25, "16:9", 1.0, [Beat("1", "VO", "vo", platzhalter_s=12)])
    # Shot 1 (nicht letzter) ist mit 3,4 s deklariert und wird nicht angetastet -> muss als "zu lang" gelten.
    plan = L.LayoutPlan("v.md", [], [L.Strecke(1, [L.Szene("Standort 1/Flur", [
        L.Shot("Flur/FX3_1.MP4", 0.0, 3.4), L.Shot("Flur/FX3_2.MP4", 0.0, 2.0)], ausnahme="Test: Länge")])])
    r = L.verify_layout(plan, tp, idx, cl, CFG, 25)
    assert any("zu lang" in e and "FX3_1" in e and "letzter" not in e for e in r.errors)
    # Ein einzelner (damit zwangsläufig letzter) Shot, dessen Reststrecke ebenfalls exakt 3,4 s ergibt,
    # darf das dank der 0,5-s-Toleranz (Grenze bis 3,5 s) — kein Längenfehler.
    tp2 = {"fps": 25, "total_frames": 85, "beats": [{"nr": "1", "typ": "vo", "rec_in_f": 0, "rec_out_f": 85, "person": None}]}
    cl2 = Cutlist("v.md", None, 25, "16:9", 1.0, [Beat("1", "VO", "vo", platzhalter_s=3.4)])
    plan2 = L.LayoutPlan("v.md", [], [L.Strecke(1, [L.Szene("Standort 1/Flur", [
        L.Shot("Flur/FX3_1.MP4", 0.0, 3.4)], ausnahme="Test: Länge")])])
    r2 = L.verify_layout(plan2, tp2, idx, cl2, CFG, 25)
    assert not any("zu lang" in e for e in r2.errors)


def test_place_shots_tempo_remainder_redistributed_and_errors_without_tempo1_shot():
    idx = _idx()
    # Strecke 1 = 58..258 (200 Frames, Standardfenster via cl=CL): 3 s (75 Frames, tempo 1) + 2 s tempo 2 als
    # letzter Shot lassen eine Reststrecke von 125 Frames — kein Vielfaches von tempo 2. Die überzähligen
    # 1 Frame müssen an den vorherigen tempo-1-Shot gehen, statt als schwarzes Bild verloren zu gehen.
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_5.MP4", 0.0, 2.0, 2)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs == []
    assert (placed[0]["rec_in_f"], placed[0]["rec_out_f"]) == (58, 134)      # 75 -> 76 Frames (1 Frame aus dem Rest)
    assert (placed[0]["src_out_f"], placed[0]["out_s"]) == (76, 3.04)
    assert (placed[1]["rec_in_f"], placed[1]["rec_out_f"]) == (134, 258)     # letzter Shot stößt lückenlos ans Streckenende
    # Ohne einen tempo-1-Shot in der Strecke kann der Rest nirgendwo hin. Strecke künstlich auf 201 Frames
    # gesetzt (direkt über strecken_frames, unabhängig von TP/CL), damit die Reststrecke (151) ungerade ist.
    plan2 = _plan({1: [("Flur/FX3_5.MP4", 0.0, 1.0, 2), ("Flur/FX3_5.MP4", 0.0, 2.0, 2)]})
    placed2, errs2 = L.place_shots(plan2, TP, idx, CFG, 25, strecken_frames=[{"nr": 1, "von_f": 0, "bis_f": 201}])
    assert len(placed2) == 1                                                 # nur der erste Shot konnte platziert werden
    assert errs2 and "151 Frames" in errs2[0] and "kein Vielfaches von tempo" in errs2[0] and "tempo-1-Shot" in errs2[0]


def test_hamming_distance():
    assert L._hamming("0" * 16, "f" * 16) == 64
    assert L._hamming("0" * 16, "0" * 14 + "ff") == 8


def test_verify_layout_no_similar_setup_warning_when_hashes_differ():
    idx = _idx()
    idx["clips"][0]["abschnitte"][0]["setup_hash"] = "0" * 16
    idx["clips"][1]["abschnitte"][0]["setup_hash"] = "f" * 16   # weit genug weg (Hamming 64 >= setup_hash_min_distance)
    idx["clips"][2]["abschnitte"][0]["setup_hash"] = "0" * 16
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    assert not any("fast gleich aus" in w for w in r.warnings)


def test_render_layout_md_report_contains_strecke_clip_and_face_share():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 5.0)]})
    placed, errs = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    assert errs == []
    r = L.raster(TP, CL, CFG)
    md = L.render_layout_md(plan, placed, r, idx, CL)
    assert "Strecke 1" in md and "FX3_1.MP4" in md and "Anteile" in md and "Gesicht" in md


# --------------------------------------------------------------------------- #
# Fix-Welle nach Gesamt-Review (2026-09-04): unfüllbare Kurz-Strecken nach
# Ganz-Gesicht-Beats, harte Gesichtsanteil-Prüfung in raster(), Filter-Reihenfolge (xml_patch)
# --------------------------------------------------------------------------- #

# Zwei O-Ton-Beats derselben Person: Beat 1 ist der erste Beat und damit automatisch voll (0-50, 2,0 s); Beat 2
# beginnt erst 25 Frames (1,0 s @ 25 fps) später bei Frame 75 — genau die Lücke aus dem Review-Fund.
_TP_KURZ = {"fps": 25, "total_frames": 400, "beats": [
    {"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 50, "person": "Anna"},
    {"nr": "2", "typ": "oton", "rec_in_f": 75, "rec_out_f": 275, "person": "Anna"}]}
_CL_KURZ = Cutlist("v.md", None, 25, "16:9", 1.0, [
    Beat("1", "Kaltstart", "oton", person="Anna", clip=FX, cuts=[Cut(1, 3)], bild_hinweis="Gehaltenes Gesicht"),
    Beat("2", "Mensch", "oton", person="Anna", clip=FX, cuts=[Cut(5, 13)])])


def test_adjust_short_stretches_shifts_default_window_after_voll_beat():
    """Beat 1 ist (voll), Beat 2 startet 25 Frames (1,0 s) später — ohne Korrektur bliebe dazwischen eine 1,0-s-
    Strecke, die kein Shot füllen kann (Mindestlänge 2,0 s). Das Standardfenster von Beat 2 muss automatisch so
    weit nach hinten rücken (offset_s), dass die Strecke davor mindestens 2,0 s hat."""
    wins = {w.beat_nr: w for w in L.effective_windows(None, _TP_KURZ, _CL_KURZ, CFG)}
    assert wins["1"].voll is True
    assert wins["2"].offset_s >= 1.0 - 1e-9
    assert "verschoben" in wins["2"].grund
    wf, errs = L.window_frames(list(wins.values()), _TP_KURZ, 25, CFG)
    assert errs == []
    w1 = next(w for w in wf if w["beat_nr"] == "1")
    w2 = next(w for w in wf if w["beat_nr"] == "2")
    assert (w2["a_f"] - w1["b_f"]) / 25 >= 2.0 - 1e-9         # Strecke dazwischen ist jetzt mindestens 2,0 s


def test_raster_reports_remaining_short_stretch_from_plan_window():
    """Setzt Claude im Plan selbst ein Fenster, das eine zu kurze Strecke hinterlässt, rührt adjust_short_stretches()
    es nicht an (Plan-Fenster sind Claudes Verantwortung) — raster() muss die verbleibende Kurz-Strecke als Fehler
    melden, mit Abhilfe-Text (welches Fenster verschieben bzw. welcher voll-Beat eine dauer_s bekommen könnte)."""
    plan = L.LayoutPlan("v.md", [L.Fenster("2", 0.0, 2.0, grund="Plan-Fenster")], [])
    r = L.raster(_TP_KURZ, _CL_KURZ, CFG, plan)
    kurz = [e for e in r["fehler"] if "kurz" in e]
    assert kurz, r["fehler"]
    assert "Strecke 1" in kurz[0] and "Beat #2" in kurz[0] and "Beat #1" in kurz[0]


def test_raster_reports_error_when_face_share_outside_hard_limit():
    """--raster darf nicht „ok" melden, wenn der Gesichtsanteil die harte Grenze (12–23 %) verletzt — bislang prüfte
    das nur verify_layout(), raster() (also --raster) gar nicht."""
    plan = L.LayoutPlan("v.md", [L.Fenster("3", 0.0, 4.0), L.Fenster("3", 4.5, 3.5), L.Fenster("4", 0.0, 4.0),
                                 L.Fenster("4", 5.0, 4.0)], [])
    r = L.raster(TP, CL, CFG, plan)
    assert any("Gesichtsanteil" in e and "außerhalb" in e for e in r["fehler"])


def test_raster_ok_stays_free_of_errors_on_the_default_mek_fixture():
    """Gegenprobe: die unveränderte TP/CL-Standardfixture (Gesichtsanteil ~19 %, Strecken 7–13 s) bleibt fehlerfrei —
    weder die neue Kurz-Strecken- noch die Gesichtsanteil-Prüfung schlägt hier grundlos an."""
    r = L.raster(TP, CL, CFG)
    assert r["fehler"] == []


def test_compact_index_v2_reicht_telemetriewerte_durch():
    idx = _idx()
    a = idx["clips"][0]["abschnitte"][0]
    a.update(brennweite_mm=71.6, zoom="langsam", bewegungsart="schwenk_links", haltung="gimbal",
             bewegung_spitzen=[[1.0, 3.0]])
    cx = L.compact_index_v2(idx)
    ab = cx[0]["abschnitte"][0]
    assert ab["brennweite_mm"] == 71.6 and ab["zoom"] == "langsam"
    assert ab["bewegungsart"] == "schwenk_links" and ab["haltung"] == "gimbal"
    assert ab["bewegung_spitzen"] == [[1.0, 3.0]]
    assert ab["brennweite"] == "weit"          # Claudes Klasse bleibt erhalten


def test_compact_index_v2_ohne_telemetrie_liefert_none():
    cx = L.compact_index_v2(_idx())
    ab = cx[0]["abschnitte"][0]
    assert ab["brennweite_mm"] is None and ab["zoom"] is None
    assert ab["bewegungsart"] is None and ab["haltung"] is None and ab["bewegung_spitzen"] == []


# --------------------------------------------------------------------------- #
# Task 3: Telemetrie in verify_layout() — Regel 3a (Brennweitenfolge)
# --------------------------------------------------------------------------- #

def _tele(datei, kb_mm, zooms=None, fenster=None):
    """Telemetrie-Datensatz wie in telemetrie.json; konstante Brennweite = ein kb_verlauf-Eintrag.

    ``config_hash`` trägt den Hash der Test-Config: produktiv setzt ihn clip_messen() bei jeder Messung, und
    seit Fund I4 überspringen Regel 3b und 3c Datensätze mit abweichendem Hash. Ein Datensatz ohne Hash ist
    damit ausdrücklich „mit anderen Schwellen gemessen" (siehe eigener Test)."""
    return {"path": f"/nas/Standort 1/Sortiert/B-Roll/Flur/{datei}", "clip": datei.split(".")[0],
            "quelle": "rtmd", "fps": 25.0, "dauer_s": 12.0, "fenster_s": 2.0, "config_hash": TM.config_hash(CFG_TELEMETRIE),
            "kb_verlauf": [[0.0, kb_mm]], "zooms": zooms or [], "fenster": fenster or []}


def test_verify_layout_brennweitenfolge_meldet_gleiche_kb_am_schnitt():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [_tele("FX3_1.MP4", 25.0), _tele("FX3_2.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("KB" in e and "FX3_1" in e and "FX3_2" in e for e in r.errors)   # 25,0 → 25,0 mm
    assert not any("KB" in e and "FX3_3" in e for e in r.errors)                # 25,0 → 70,0 mm ist weit genug


def test_verify_layout_brennweitenfolge_ohne_telemetrie_still():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, None)
    assert not any("KB" in e for e in r.errors)
    assert any("keine Telemetrie" in w for w in r.warnings)


def test_verify_layout_brennweitenfolge_frische_telemetrie_ohne_schwellen_warnung():
    """Fix-Runde 1: cfg["telemetrie"] muss der echte Geschwister-Block sein (siehe CFG_TELEMETRIE oben), sonst
    hasht telemetrie_hinweise() innerhalb von verify_layout gegen config_hash({}) statt gegen den echten Hash —
    die Warnung „… mit anderen Telemetrie-Schwellen gemessen" würde dann auch bei frischer, mit den aktuellen
    Schwellen gemessener Telemetrie immer feuern (und der empfohlene Neulauf sie nie beheben)."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    h = TM.config_hash(CFG["telemetrie"])
    tele = [{**_tele("FX3_1.MP4", 25.0), "config_hash": h}, {**_tele("FX3_2.MP4", 40.0), "config_hash": h},
            {**_tele("FX3_3.MP4", 70.0), "config_hash": h}]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("Telemetrie-Schwellen" in w for w in r.warnings)


def test_verify_layout_meldet_shots_ohne_telemetrie_datensatz():
    """Fix-Welle, Fund I2: Shots, für die finden() keinen Datensatz liefert, wurden bei 3b und 3c stumm
    übersprungen — der einzige Zähler zählte Schnittpaare und nannte ausdrücklich nur die Brennweitenregel.
    Hier hat nur FX3_1 einen Datensatz; für FX3_2 und FX3_3 muss der Bericht sagen, dass Zoom- und
    Bewegungsregel nicht geprüft wurden, getrennt von der Schnittpaar-Zählung."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, [_tele("FX3_1.MP4", 25.0)])
    ohne = [w for w in r.warnings if "ohne verwertbaren Telemetrie-Datensatz" in w]
    assert len(ohne) == 1 and ohne[0].startswith("2 von 3 Shots"), r.warnings
    assert "Zoom- und Bewegungsregel" in ohne[0]
    # getrennt davon die Schnittpaar-Zählung für die Brennweitenregel
    assert any("Schnitte ohne Brennweitenverlauf" in w and "Brennweitenregel" in w for w in r.warnings), r.warnings
    # Gegenprobe: mit Datensatz für alle drei Clips schweigt die Meldung
    tele = [_tele("FX3_1.MP4", 25.0), _tele("FX3_2.MP4", 40.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("ohne verwertbaren Telemetrie-Datensatz" in w for w in r.warnings), r.warnings


def test_verify_layout_datensatz_mit_fehler_zaehlt_als_ungeprueft():
    """Ein Datensatz mit ``fehler`` trägt weder ``zooms`` noch ``fenster`` — 3b und 3c würden still
    durchwinken. Er zählt deshalb wie ein fehlender Datensatz."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [{**_tele("FX3_1.MP4", 25.0), "fehler": "rtmd nicht lesbar"},
            _tele("FX3_2.MP4", 40.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any(w.startswith("1 von 3 Shots ohne verwertbaren Telemetrie-Datensatz") for w in r.warnings), r.warnings


def test_verify_layout_ohne_telemetrie_nur_eine_meldung():
    """Fix-Welle, Fund I2: ohne jede Telemetrie meldeten „N Schnitte ohne Brennweitenverlauf" und
    „keine Telemetrie" denselben Sachverhalt zweimal. Jetzt bleibt genau eine Meldung, die alle drei
    Regeln und die Zahl der Shots nennt."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, None)
    tele_w = [w for w in r.warnings if "Telemetrie" in w or "Brennweitenverlauf" in w]
    assert len(tele_w) == 1, tele_w
    assert tele_w[0].startswith("keine Telemetrie") and "alle 3 Shots" in tele_w[0]
    assert "Brennweiten-, Zoom- und Bewegungsregel" in tele_w[0]


# --------------------------------------------------------------------------- #
# Task 4: Regel 3b — kein schneller Zoom im genutzten Bereich
# --------------------------------------------------------------------------- #


def test_verify_layout_schneller_zoom_im_genutzten_bereich():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    langsam = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 30.0, "bis_mm": 35.0, "tempo_max": 28.0,
                "tempo_mittel": 20.0, "urteil": "langsam"}]
    tele = [_tele("FX3_1.MP4", 25.0, schnell), _tele("FX3_2.MP4", 70.0, langsam), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("schneller Zoom" in e and "FX3_1" in e for e in r.errors)
    assert not any("schneller Zoom" in e and "FX3_2" in e for e in r.errors)


def test_verify_layout_schneller_zoom_mit_abweichung_erlaubt():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    plan.strecken[0].szenen[0].shots[0].abweichung = True
    plan.strecken[0].szenen[0].shots[0].abweichung_grund = "Plan verlangt genau diese Fahrt"
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    tele = [_tele("FX3_1.MP4", 25.0, schnell), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("schneller Zoom" in e for e in r.errors)


def test_verify_layout_schneller_zoom_zeitlupe_halbiert_genutzten_bereich():
    """Fix-Runde 1 (Coordinator-Review zu Task 4): beide bisherigen Zoom-Tests nutzten nur tempo=1 —
    der Zeitlupen-Zweig `langsam=(p.get("tempo") or 1) > 1` beim Aufruf von TM.genutzter_quellbereich_s()
    in verify_layout() (broll_layout.py) war dadurch ungeprüft. Shot 0 ist wörtlich aus
    test_place_shots_tempo_conform_and_invalid_fps übernommen (Flur/FX3_5.MP4, 50 fps laut _idx(),
    tempo=2 -> rec_in_f=58, rec_out_f=158, src_in_f=0, src_out_f=100 sind dort bereits geprüft).

    Handrechnung TM.genutzter_quellbereich_s(src_in_f=0, n_f=rec_out_f-rec_in_f=100, clip_fps=50,
    langsam=True, ziel_fps=25):
        ende_f = 0 + 100 * 50/25 * 0,5 = 0 + 100 * 2 * 0,5 = 100
        von_s  = 0 / 50 = 0,0
        bis_s  = 100 / 50 = 2,0
    Genutzter Quellbereich also [0,0 - 2,0] s (deckt sich mit src_out_f/clip_fps = 100/50 = 2,0 s).
    Fiele `langsam=` weg (Regression auf den Faktor 1,0 wie bei tempo=1), ergäbe dieselbe Rechnung
    ende_f = 0 + 100 * 2 * 1,0 = 200 -> bis_s = 4,0 — die Zoomfahrt unten (2,5-3,5 s) läge dann fälschlich
    im Bereich und der Test unten (ohne Zeitlupe) würde nicht mehr zwischen beiden Fällen unterscheiden.
    """
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 2.0, 2), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 2.5, "bis_s": 3.5, "von_mm": 70.0, "bis_mm": 24.0, "tempo_max": 210.0,
                "tempo_mittel": 160.0, "urteil": "schnell"}]
    tele = [{**_tele("FX3_5.MP4", 35.0, schnell), "fps": 50.0}]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    # Zoomfahrt (2,5-3,5 s) liegt vollständig außerhalb des bei tempo=2 tatsächlich genutzten Bereichs (0,0-2,0 s).
    assert not any("schneller Zoom" in e and "FX3_5" in e for e in r.errors)


def test_verify_layout_schneller_zoom_ohne_zeitlupe_voller_bereich_gemeldet():
    """Gegenstück zum Zeitlupentest oben: derselbe Clip und dieselbe Zoomfahrt, aber tempo=1 mit doppelter
    Plandauer (4,0 statt 2,0 s) — das ergibt denselben Timeline-Frame-Count n_f=100 wie im Zeitlupentest,
    aber `langsam=False` lässt TM.genutzter_quellbereich_s() diesmal den vollen (nicht halbierten)
    Quellbereich berechnen, der die Zoomfahrt trifft. Erst im Zusammenspiel mit dem Test oben trennt das
    wirklich den `langsam`-Zweig, statt nur zufällig grün zu sein (siehe Auftrag Fix-Runde 1).

    Handrechnung place_shots() für Shot 0 (Flur/FX3_5.MP4, in_s=0,0, out_s=4,0, tempo=1, clip_fps=50,
    Strecke 1 beginnt bei Frame 58, wie im Zeitlupentest oben):
        n_tl     = seconds_to_frames(4,0 - 0,0, fps=25) * 1 = 100 * 1 = 100
        rec_in_f = 58, rec_out_f = 58 + 100 = 158                       (n_f = 100 - wie im Zeitlupentest)
        src_n    = round(n_tl * clip_fps/fps) = round(100 * 50/25) = 200
        src_in_f = 0, src_out_f = 0 + 200 = 200 -> out_s = 200/50 = 4,0 (unverändert, kein Kürzen)

    Handrechnung TM.genutzter_quellbereich_s(src_in_f=0, n_f=100, clip_fps=50, langsam=False, ziel_fps=25):
        ende_f = 0 + 100 * 50/25 * 1,0 = 200
        von_s  = 0 / 50 = 0,0
        bis_s  = 200 / 50 = 4,0
    Genutzter Quellbereich [0,0 - 4,0] s enthält die Zoomfahrt (2,5-3,5 s) diesmal vollständig.
    """
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 4.0), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 2.5, "bis_s": 3.5, "von_mm": 70.0, "bis_mm": 24.0, "tempo_max": 210.0,
                "tempo_mittel": 160.0, "urteil": "schnell"}]
    tele = [{**_tele("FX3_5.MP4", 35.0, schnell), "fps": 50.0}]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("schneller Zoom" in e and "FX3_5" in e for e in r.errors)


def test_verify_layout_meldet_fehlenden_telemetrie_configblock():
    """Fix-Welle, Fund M7: jeder fehlende broll.*-Schlüssel ist laut ein Config-Fehler, ein fehlender
    telemetrie:-Block fiel dagegen still auf Code-Defaults zurück — eine spätere Kalibrierung bliebe dann
    wirkungslos, ohne dass es jemand merkt. Fehlende Telemetrie-DATEN bleiben erlaubt (eigener Test),
    ein fehlender CONFIG-Block nicht."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    ohne = {k: v for k, v in CFG.items() if k != "telemetrie"}
    r = L.verify_layout(plan, TP, idx, CL, ohne, 25)
    assert any(e.startswith("Config: telemetrie fehlt") for e in r.errors), r.errors
    luecke = {**CFG, "telemetrie": {k: v for k, v in CFG_TELEMETRIE.items() if k != "bewegung_rand_s"}}
    r = L.verify_layout(plan, TP, idx, CL, luecke, 25)
    assert any("Config: telemetrie.bewegung_rand_s fehlt" in e for e in r.errors), r.errors
    # Gegenprobe: mit vollständigem Block meldet die Prüfung keinen Config-Fehler
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25)
    assert not any(e.startswith("Config:") for e in r.errors), r.errors


def test_verify_layout_zoom_tempo_4_nur_im_wirklich_genutzten_bereich():
    """Fix-Welle, Fund I3: der Quellbereich kommt aus ``src_in_f``/``src_out_f`` (place_shots), nicht aus
    ``TM.genutzter_quellbereich_s()``. Die kennt nur „langsam" (Faktor 0,5) und stimmt damit allein bei tempo 2;
    bei tempo 4 lieferte sie den doppelten Bereich und meldete Zoomfahrten, die in der Timeline nie zu sehen sind.

    Handrechnung place_shots() für Shot 0 (FX3_5.MP4 auf 100 fps gesetzt, tempo 4, in_s 0,0, out_s 1,0,
    Strecke 1 beginnt bei Frame 58):
        n_tl     = seconds_to_frames(1,0 - 0,0, fps=25) * 4 = 25 * 4 = 100   (4,0 s Timeline, O-Ton 2,0-6,0 s ok)
        src_n    = n_tl = 100   (tempo > 1: Quellframes = Timeline-Frames)
        src_in_f = 0, src_out_f = 100 -> genutzt 0/100 bis 100/100 = 0,0-1,0 s im Clip
    Der alte Weg TM.genutzter_quellbereich_s(0, n_f=100, clip_fps=100, langsam=True, ziel_fps=25):
        ende_f = 0 + 100 * 100/25 * 0,5 = 200 -> 0,0-2,0 s — doppelt so lang.
    Die Fahrt bei 1,3-1,8 s liegt genau dazwischen: im alten Bereich drin (harter Fehler), im echten draußen.
    """
    idx = _idx()
    for c in idx["clips"]:
        if c["datei"] == "FX3_5.MP4":
            c["fps"] = 100.0
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 1.0, 4), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    def _zoom(von_s, bis_s):
        return [{"von_s": von_s, "bis_s": bis_s, "von_mm": 70.0, "bis_mm": 24.0, "tempo_max": 210.0,
                 "tempo_mittel": 160.0, "urteil": "schnell"}]
    # 1,3-1,8 s: außerhalb der genutzten 0,0-1,0 s -> kein Fehler (mit dem alten Helfer war es einer)
    tele = [{**_tele("FX3_5.MP4", 35.0, _zoom(1.3, 1.8)), "fps": 100.0},
            _tele("FX3_1.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("schneller Zoom" in e and "FX3_5" in e for e in r.errors), r.errors
    # Gegenprobe im selben Test: dieselbe Fahrt bei 0,3-0,7 s liegt im genutzten Bereich und muss melden —
    # sonst wäre die Zusicherung oben auch mit einem leeren Bereich grün.
    tele = [{**_tele("FX3_5.MP4", 35.0, _zoom(0.3, 0.7)), "fps": 100.0},
            _tele("FX3_1.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("schneller Zoom" in e and "FX3_5" in e for e in r.errors), r.errors


def test_verify_layout_brennweitenfolge_tempo_4_liest_das_wirkliche_shot_ende():
    """Fund I3 für Regel 3a: `_kb_am_schnitt()` liest die KB am Ende des Shots. Bei tempo 4 endet Shot 0
    bei 1,0 s im Clip (Rechnung wie im Test darüber), nicht bei 2,0 s. Der Verlauf springt bei 1,5 s von
    30 auf 60 mm: am wirklichen Ende (kb_am über 0,5-1,0 s) sind es 30 mm — gleich wie die 30 mm des
    Folgeshots, also ein Fehler. Mit dem alten, doppelten Bereich läse die Regel bei 2,0 s (1,5-2,0 s)
    60 mm und schwiege (60/30 - 1 = 1,0 > brennweite_gleich_max)."""
    idx = _idx()
    for c in idx["clips"]:
        if c["datei"] == "FX3_5.MP4":
            c["fps"] = 100.0
    plan = _plan({1: [("Flur/FX3_5.MP4", 0.0, 1.0, 4), ("Flur/FX3_1.MP4", 0.0, 2.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [{**_tele("FX3_5.MP4", 30.0), "fps": 100.0, "kb_verlauf": [[0.0, 30.0], [1.4, 30.0], [1.5, 60.0], [6.0, 60.0]]},
            _tele("FX3_1.MP4", 30.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("KB" in e and "FX3_5" in e and "FX3_1" in e for e in r.errors), r.errors


def test_verify_layout_alte_schwellen_ueberspringt_zoom_und_bewegung_nicht_die_brennweite():
    """Fix-Welle, Fund I4 (Entscheidung des Users): Datensätze mit anderem ``config_hash`` tragen Zoom-Urteile
    und Fenster aus den Schwellen zur Messzeit — ``zoom_schnell_proz_s`` und Verwandte stehen NICHT in
    ``OHNE_MESSWIRKUNG``. Regel 3b und 3c würden damit Fehler melden, die die heutige Konfiguration gar nicht
    erzeugt: beide entfallen für solche Clips und werden gezählt. Regel 3a läuft weiter (``kb_verlauf`` ist roh,
    ``brennweite_gleich_max`` steht in ``OHNE_MESSWIRKUNG``).

    FX3_1 trägt beides: eine schnelle Zoomfahrt im genutzten Bereich (0,0-3,0 s) UND dieselbe KB wie FX3_2 am
    Schnitt. Mit veraltetem Hash muss genau der Zoomfehler verschwinden und der KB-Fehler bleiben."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    fen = [[0.0, 0.1, 0.4, "fahrt", None], [3.0, 0.1, 9.0, "schwenk_links", None], [8.0, 0.1, 0.5, "fahrt", None]]
    frisch = [_tele("FX3_1.MP4", 25.0, schnell, fen), _tele("FX3_2.MP4", 25.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, frisch)
    assert any("schneller Zoom" in e and "FX3_1" in e for e in r.errors), r.errors
    assert any("Bewegungsspitze" in w and "FX3_1" in w for w in r.warnings), r.warnings
    assert any("KB" in e and "FX3_1" in e and "FX3_2" in e for e in r.errors), r.errors

    alt = [{**frisch[0], "config_hash": "aaaaaaaaaaaa"}, frisch[1], frisch[2]]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, alt)
    assert not any("schneller Zoom" in e for e in r.errors), r.errors          # 3b übersprungen
    assert not any("Bewegungsspitze" in w for w in r.warnings), r.warnings     # 3c übersprungen
    assert any("KB" in e and "FX3_1" in e and "FX3_2" in e for e in r.errors), r.errors   # 3a läuft weiter
    hinweis = [w for w in r.warnings if "anderen Schwellen gemessen" in w]
    assert len(hinweis) == 1 and hinweis[0].startswith("1 von 3 Shots"), r.warnings
    assert "autocut_telemetrie.py neu laufen lassen" in hinweis[0]
    # eine Meldung je Sachverhalt: der allgemeine Hinweis aus telemetrie_hinweise() entfällt daneben
    assert not any(TM.HINWEIS_SCHWELLEN in w for w in r.warnings), r.warnings


def test_verify_layout_datensatz_ohne_config_hash_gilt_als_alt_gemessen():
    """Ein Datensatz ohne ``config_hash`` ist von unbekannter Herkunft — clip_messen() setzt ihn bei jeder
    Messung. Er wird wie ein veralteter behandelt (3b/3c übersprungen), damit die Prüfung nicht still auf
    Urteilen aus unbekannten Schwellen aufbaut."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    schnell = [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    tele = [{k: v for k, v in _tele("FX3_1.MP4", 25.0, schnell).items() if k != "config_hash"},
            _tele("FX3_2.MP4", 40.0), _tele("FX3_3.MP4", 70.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("schneller Zoom" in e for e in r.errors), r.errors
    assert any("anderen Schwellen gemessen" in w for w in r.warnings), r.warnings


def test_verify_layout_bewegungsspitze_an_der_schnittgrenze_warnt_nur():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    # Shot 1 endet bei 3,0 s; Spitze bei 3,0 s mit 9,0 gegen Grundniveau 0,45 = Faktor 20 (Fix-Runde 1: das
    # Fenster bei t=1,0 liegt nur 2,0 s entfernt und fällt NICHT aus dem 3,0-s-Ausschluss; Median von
    # [0,4 @ 0,0s; 0,5 @ 8,0s] = 0,45, nicht 0,5)
    fen = [[0.0, 0.1, 0.4, "fahrt", None], [1.0, 0.1, 0.6, "fahrt", None],
           [3.0, 0.1, 9.0, "schwenk_links", None], [8.0, 0.1, 0.5, "fahrt", None]]
    tele = [_tele("FX3_1.MP4", 25.0, None, fen), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("Bewegungsspitze" in w for w in r.warnings)
    assert not any("Bewegungsspitze" in e for e in r.errors)     # NIE ein Fehler: Schwellen unkalibriert


def test_verify_layout_bewegungsspitze_unter_ruhig_max_px_warnt_nicht():
    """Fix-Runde 1 (Review, Fund 2): rein multiplikativer Vergleich hätte auf Stativmaterial schon bei
    winzigen Ausreißern deutlich unterhalb ruhig_max_px gefeuert. Handrechnung:
    grund_px = bewegung_grundniveau(rec, 3.0, 3.0) = Median der Fenster mit Abstand >= 3,0 s von t=3,0 s
             = Median([0,019 @ 6,0s]) = 0,019       (nur ein Fenster fern genug -> Median = der Wert selbst)
    Ohne Untergrenze: Faktor = 0,08 / 0,019 ≈ 4,21 >= bewegung_spitze_faktor (3,0) -> hätte gewarnt.
    Mit Untergrenze:  basis = max(grund_px, ruhig_max_px) = max(0,019; 0,15) = 0,15
                      bewegung_spitze_faktor * basis = 3,0 * 0,15 = 0,45
                      bw (0,08) >= 0,45 ist False -> keine Warnung, weil das System dieses Bild an
                      anderer Stelle (ruhig_max_px) ohnehin als ruhig einstuft."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    fen = [[3.0, 0.1, 0.08, "schwenk_links", None], [6.0, 0.1, 0.019, "fahrt", None]]
    tele = [_tele("FX3_1.MP4", 25.0, None, fen), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert not any("Bewegungsspitze" in w for w in r.warnings)


def test_verify_layout_bewegungsspitze_grundniveau_null_warnt_trotzdem():
    """Fix-Runde 1 (Review, Fund 1): grund_px = 0,0 ist falsy — ``if grund_px and …`` hätte jede noch so
    extreme Spitze übergangen (der Faktor wäre rechnerisch unendlich). Handrechnung:
    grund_px = bewegung_grundniveau(rec, 3.0, 3.0) = Median([0,0 @ 6,0s]) = 0,0
    Mit explizitem ``is None``-Check (0,0 ist nicht None) und Untergrenze:
                      basis = max(grund_px, ruhig_max_px) = max(0,0; 0,15) = 0,15
                      bewegung_spitze_faktor * basis = 3,0 * 0,15 = 0,45
                      bw (5,0) >= 0,45 ist True -> die Warnung muss kommen."""
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    fen = [[3.0, 0.1, 5.0, "schwenk_links", None], [6.0, 0.1, 0.0, "fahrt", None]]
    tele = [_tele("FX3_1.MP4", 25.0, None, fen), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    r = L.verify_layout(plan, TP, idx, CL, CFG, 25, tele)
    assert any("Bewegungsspitze" in w for w in r.warnings)
    assert not any("Bewegungsspitze" in e for e in r.errors)     # NIE ein Fehler: Schwellen unkalibriert


# --------------------------------------------------------------------------- #
# Task 6: Bericht — KB-Spalte in render_layout_md
# --------------------------------------------------------------------------- #

def test_render_layout_md_zeigt_kb_brennweite():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    tele = [_tele("FX3_1.MP4", 25.4), _tele("FX3_2.MP4", 70.0), _tele("FX3_3.MP4", 35.0)]
    placed, _ = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    r = L.raster(TP, CL, CFG, plan)
    md = L.render_layout_md(plan, placed, r, idx, CL, tele=tele)
    assert "| KB |" in md and "25,4 mm" in md


def test_render_layout_md_ohne_telemetrie_zeigt_gedankenstrich():
    idx = _idx()
    plan = _plan({1: [("Flur/FX3_1.MP4", 0.0, 3.0), ("Flur/FX3_2.MP4", 1.0, 4.0), ("Flur/FX3_3.MP4", 0.0, 2.0)]})
    placed, _ = L.place_shots(plan, TP, idx, CFG, 25, cl=CL)
    r = L.raster(TP, CL, CFG, plan)
    md = L.render_layout_md(plan, placed, r, idx, CL)
    assert "| KB |" in md
    assert " – | " in md                        # kein Absturz und keine „None"-Anzeige ohne tele
