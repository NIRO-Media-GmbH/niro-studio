"""Tests für cutlist.py — Modell, Rundreise, harte Prüfung, Gesamtlänge, Hash."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError
from niro_autocut.cutlist import Beat, Cut, Cutlist, Sperre, cutlist_hash, total_length_s, verify_cutlist

CFG = {"pause_s": 1.0, "handle_in_frames": 6, "handle_out_frames": 8, "align_min_score": 0.8,
       "duration_tolerance": [0.5, 2.0], "target_length_warn": 0.25}
WORDS = {"/nas/FX3_1.MP4": [{"text": t, "start": 1 + i * 0.4, "end": 1.3 + i * 0.4, "speaker": "s1"}
                            for i, t in enumerate("Weil das mein Job ist Das ist meins".split())]}
DUR = {"/nas/FX3_1.MP4": 300.0}


def _cl(**kw):
    beats = kw.pop("beats", [Beat(nr="1", szene="Hook", typ="oton", person="Sandra", clip="/nas/FX3_1.MP4",
                                  cuts=[Cut(in_s=1.0, out_s=4.1, text="Weil das mein Job ist. Das ist meins.")], plan_dauer_s=3)])
    return Cutlist(video="video-1.md", ziel_laenge_s=kw.pop("ziel", 4.0), fps=25, format="16:9", pause_s=1.0,
                   beats=beats, sperren=kw.pop("sperren", []))


# --- Modell / Datei -----------------------------------------------------

def test_roundtrip(tmp_path):
    cl = _cl(); p = tmp_path / "c.json"; cl.save(p)
    assert Cutlist.load(p).beats[0].cuts[0].text.startswith("Weil")


def test_roundtrip_is_lossless(tmp_path):
    cl = _cl(sperren=[Sperre(clip="/nas/FX3_1.MP4", von_s=10, bis_s=20, grund="Tabu")])
    cl.beats.append(Beat(nr="2", szene="VO", typ="vo", text="Viele denken", platzhalter_s=6, pause_after_s=0.0))
    cl.hinweise = ["Konkurrenz-Nennungen: nur Text, keine Sperre"]
    p = tmp_path / "c.json"; cl.save(p)
    assert Cutlist.load(p) == cl
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["hinweise"] == cl.hinweise and data["beats"][1]["pause_after_s"] == 0.0


def test_from_dict_rejects_unknown_key():
    d = _cl().to_dict()
    d["beats"][0]["cuts"][0]["hard_out"] = True          # Tippfehler statt hart_out
    with pytest.raises(AutoCutError, match="hard_out"):
        Cutlist.from_dict(d)
    d = _cl().to_dict()
    d["beats"][0]["timecode"] = "03:37"
    with pytest.raises(AutoCutError, match="timecode"):
        Cutlist.from_dict(d)


def test_from_dict_reports_missing_required_field():
    d = _cl().to_dict()
    del d["beats"][0]["szene"]
    with pytest.raises(AutoCutError, match="szene"):
        Cutlist.from_dict(d)
    with pytest.raises(AutoCutError, match="fps"):
        Cutlist.from_dict({"video": "v", "beats": []})


def test_load_reports_invalid_json(tmp_path):
    p = tmp_path / "c.json"; p.write_text("{kaputt", encoding="utf-8")
    with pytest.raises(AutoCutError, match="c.json"):
        Cutlist.load(p)
    with pytest.raises(AutoCutError, match="fehlt"):
        Cutlist.load(tmp_path / "gibt-es-nicht.json")


def test_cutlist_hash_changes_with_content(tmp_path):
    p = tmp_path / "c.json"; _cl().save(p); h1 = cutlist_hash(p)
    cl = _cl(); cl.beats[0].cuts[0].out_s = 4.0; cl.save(p)
    assert len(h1) == 64 and cutlist_hash(p) != h1


def test_beat_dauer():
    b = Beat(nr="1", szene="A", typ="oton", clip="/x", cuts=[Cut(1.0, 2.5, "a"), Cut(4.0, 5.0, "b")])
    assert abs(b.dauer_s() - 2.5) < 1e-9
    assert Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6).dauer_s() == 6.0
    assert Beat(nr="3", szene="B", typ="bild").dauer_s() == 0.0


# --- Prüfung -------------------------------------------------------------

def test_verify_ok():
    r = verify_cutlist(_cl(), None, WORDS, DUR, CFG)
    assert r.ok and r.errors == []


def test_verify_missing_clip_and_words():
    cl = _cl(); cl.beats[0].clip = "/nas/FEHLT.MP4"
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert not r.ok and any("Transkript" in e or "Clip" in e for e in r.errors)


def test_verify_sperre_overlap():
    cl = _cl(sperren=[Sperre(clip="/nas/FX3_1.MP4", von_s=3.0, bis_s=10.0, grund="Tabu")])
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert any("Sperre" in e for e in r.errors)


def test_verify_sperre_hit_by_handle_only():
    # Sperre beginnt 0,1 s nach dem Cut-Ende: der 8-Frame-Nachlauf (0,32 s) ragt hinein …
    cl = _cl(sperren=[Sperre(clip="/nas/FX3_1.MP4", von_s=4.2, bis_s=10.0, grund="Tabu")])
    assert any("Sperre" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)
    # … mit hartem Out (0 Frames) nicht mehr.
    cl.beats[0].cuts[0].hart_out = True
    assert verify_cutlist(cl, None, WORDS, DUR, CFG).ok


def test_verify_sperre_on_other_clip_is_fine():
    cl = _cl(sperren=[Sperre(clip="/nas/FX3_2.MP4", von_s=0.0, bis_s=100.0, grund="Tabu")])
    words = {**WORDS, "/nas/FX3_2.MP4": []}
    assert verify_cutlist(cl, None, words, {**DUR, "/nas/FX3_2.MP4": 100.0}, CFG).ok


def test_verify_sperre_unknown_clip_or_bad_interval_is_error():
    cl = _cl(sperren=[Sperre(clip="/nas/TIPPFEHLER.MP4", von_s=1.0, bis_s=2.0, grund="x")])
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert any("Sperre" in e and "TIPPFEHLER" in e for e in r.errors)
    cl = _cl(sperren=[Sperre(clip="/nas/FX3_1.MP4", von_s=20.0, bis_s=10.0, grund="x")])
    assert any("Sperre" in e and "20" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)


def test_verify_text_mismatch():
    cl = _cl(); cl.beats[0].cuts[0].text = "Völlig anderer Satz über Lastwagen und Reifen"
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert any("stimmt nicht" in e for e in r.errors)


def test_verify_extra_words_in_interval_warns():
    cl = _cl(); cl.beats[0].cuts[0].text = "Weil das mein Job ist."   # Intervall reicht bis „meins"
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert r.ok and any("nicht im Text" in w and "meins" in w for w in r.warnings)


def test_verify_cut_without_text_is_error():
    cl = _cl(); cl.beats[0].cuts[0].text = ""
    assert any("ohne Text" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)


def test_verify_invalid_intervals():
    cl = _cl(); cl.beats[0].cuts[0].out_s = 301.0
    assert any("Clip-Ende" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)
    cl = _cl(); cl.beats[0].cuts[0].out_s = 0.5
    assert any("ungültiges Intervall" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)
    cl = _cl(); cl.beats[0].cuts[0].in_s = 100.0; cl.beats[0].cuts[0].out_s = 102.0
    assert any("kein Transkript-Wort" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)


def test_verify_overlapping_cuts_warn():
    cl = _cl(beats=[Beat(nr="1", szene="A", typ="oton", clip="/nas/FX3_1.MP4",
                         cuts=[Cut(1.0, 2.5, "Weil das mein Job"), Cut(2.0, 4.1, "Job ist. Das ist meins.")])])
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert any("überschneiden" in w for w in r.warnings)


def test_verify_placeholder_required_and_type_checked():
    cl = _cl(beats=[Beat(nr="2", szene="VO", typ="vo", text="Viele denken")])
    assert any("platzhalter_s" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)
    cl = _cl(beats=[Beat(nr="9", szene="X", typ="musik", platzhalter_s=3)])
    assert any("Typ" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)
    cl = _cl(beats=[Beat(nr="1", szene="A", typ="oton", clip="/nas/FX3_1.MP4", cuts=[])])
    assert any("cuts fehlen" in e for e in verify_cutlist(cl, None, WORDS, DUR, CFG).errors)


def test_verify_empty_and_duplicate_beats():
    assert any("keine Beats" in e for e in verify_cutlist(_cl(beats=[]), None, WORDS, DUR, CFG).errors)
    cl = _cl(); cl.beats.append(Beat(nr="1", szene="VO", typ="vo", platzhalter_s=2))
    assert any("doppelt" in w for w in verify_cutlist(cl, None, WORDS, DUR, CFG).warnings)


def test_duration_and_target_warnings():
    cl = _cl(ziel=60.0); cl.beats[0].plan_dauer_s = 20
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert any("Plan-Schätzung" in w for w in r.warnings) and any("Ziellänge" in w for w in r.warnings)


def test_no_target_warning_within_tolerance():
    cl = _cl(ziel=3.5)
    r = verify_cutlist(cl, None, WORDS, DUR, CFG)
    assert r.ok and not any("Ziellänge" in w for w in r.warnings)


def test_verify_sync_coverage_warning():
    paar = {"ref": "/nas/FX3_1.MP4", "other": "/nas/a7.MP4", "offset_s": 2.0, "offset_frames": 50,
            "confidence": 10, "overlap_ref": [0.0, 300.0], "drift_frames": 0, "ok": True, "note": ""}
    r = verify_cutlist(_cl(), None, WORDS, DUR, CFG, sync={"fps": 25, "paare": [paar]})
    assert r.ok and not any("a7" in w for w in r.warnings)
    # Überlappung beginnt erst nach dem Cut-Anfang → V2 bleibt leer
    r = verify_cutlist(_cl(), None, WORDS, DUR, CFG, sync={"fps": 25, "paare": [{**paar, "overlap_ref": [2.0, 300.0]}]})
    assert any("a7" in w and "V2" in w for w in r.warnings)
    # Paar nicht ok → ebenfalls Warnung
    r = verify_cutlist(_cl(), None, WORDS, DUR, CFG, sync={"fps": 25, "paare": [{**paar, "ok": False}]})
    assert any("a7" in w for w in r.warnings)


def test_verify_with_charge_checks_original_and_proxy(charge_dir):
    from niro_autocut.charge import Charge
    ch = Charge.open(charge_dir)
    rec = ch.load_index()[0]
    words = {rec["path"]: ch.cache_transcript(rec["fingerprint"])["words"]}
    cl = _cl(ziel=None, beats=[Beat(nr="1", szene="A", typ="oton", clip=rec["path"],
                                    cuts=[Cut(1.0, 2.0, "Das ist meins.")])])
    r = verify_cutlist(cl, ch, words, {rec["path"]: 10.0}, ch.config)
    assert any("nicht gefunden" in e for e in r.errors)          # Original fehlt (NAS nicht da)
    orig = Path(rec["path"]); orig.parent.mkdir(parents=True); orig.write_bytes(b"x")
    r = verify_cutlist(cl, ch, words, {rec["path"]: 10.0}, ch.config)
    assert any("Proxy" in e for e in r.errors)                    # Proxy fehlt
    (orig.parent / "Proxy").mkdir(); (orig.parent / "Proxy" / (orig.stem + ".mov")).write_bytes(b"x")
    r = verify_cutlist(cl, ch, words, {rec["path"]: 10.0}, ch.config)
    assert r.ok, r.errors


# --- Gesamtlänge -----------------------------------------------------------

def test_total_length_includes_pauses_and_placeholders():
    cl = _cl(); cl.beats.append(Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6))
    assert abs(total_length_s(cl, CFG) - (3.1 + 1.0 + 6.0)) < 1e-6


def test_total_length_respects_pause_override():
    cl = _cl(); cl.beats[0].pause_after_s = 0.0
    cl.beats.append(Beat(nr="2", szene="VO", typ="vo", platzhalter_s=6))
    assert abs(total_length_s(cl, CFG) - (3.1 + 6.0)) < 1e-6
    assert abs(total_length_s(_cl(), CFG) - 3.1) < 1e-6           # keine Pause nach dem letzten Beat


# --- CLI autocut_verify.py ---------------------------------------------------

def test_verify_cli_writes_verify_json(charge_dir):
    import subprocess, sys
    from niro_autocut.charge import Charge, TOOL_ROOT
    script = TOOL_ROOT / "scripts" / "autocut_verify.py"
    ch = Charge.open(charge_dir)
    rec = ch.load_index()[0]
    orig = Path(rec["path"]); orig.parent.mkdir(parents=True, exist_ok=True); orig.write_bytes(b"x")
    (orig.parent / "Proxy").mkdir(exist_ok=True); (orig.parent / "Proxy" / (orig.stem + ".mov")).write_bytes(b"x")

    r = subprocess.run([sys.executable, str(script), str(charge_dir)], capture_output=True, text=True)
    assert r.returncode != 0 and "cutlist.json" in (r.stdout + r.stderr)      # Cutlist fehlt noch

    cpath = ch.autocut / "cutlist.json"
    cl = Cutlist(video="video-1-test.md", ziel_laenge_s=None, fps=25, format="16:9", pause_s=1.0,
                 beats=[Beat(nr="1", szene="A", typ="oton", person="Anna", clip=rec["path"],
                             cuts=[Cut(1.0, 2.0, "Das ist meins.")]),
                        Beat(nr="2", szene="VO", typ="vo", text="Viele denken", platzhalter_s=6)],
                 hinweise=["Konkurrenz-Nennungen: nur Text"])
    cl.save(cpath)
    r = subprocess.run([sys.executable, str(script), str(charge_dir)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HINWEIS: Konkurrenz" in r.stdout and "sync.json fehlt" in r.stdout and "OK" in r.stdout
    v = json.loads((ch.autocut / "verify.json").read_text(encoding="utf-8"))
    assert v["ok"] is True and v["cutlist_hash"] == cutlist_hash(cpath) and v["n_beats"] == 2
    assert abs(v["gesamtlaenge_s"] - (1.0 + 1.0 + 6.0)) < 1e-6

    cl.beats[0].cuts[0].text = "Völlig anderer Satz über Lastwagen"
    cl.save(cpath)
    r = subprocess.run([sys.executable, str(script), str(charge_dir)], capture_output=True, text=True)
    assert r.returncode == 1 and "FEHLER:" in r.stdout and "stimmt nicht" in r.stdout
    v = json.loads((ch.autocut / "verify.json").read_text(encoding="utf-8"))
    assert v["ok"] is False and v["cutlist_hash"] == cutlist_hash(cpath) and v["errors"]


# --- Entwurf aus dem Plan -----------------------------------------------------

FIX_PLAN = Path(__file__).parent / "fixtures" / "plan_mek_auszug.md"


def _words(text: str, t0: float, spk: str = "speaker_1", step: float = 0.4) -> list[dict]:
    return [{"text": w, "start": round(t0 + i * step, 2), "end": round(t0 + i * step + 0.3, 2), "speaker": spk}
            for i, w in enumerate(text.split())]


def _mek_like(tmp_path: Path) -> tuple[Path, list[dict], dict, dict, list[dict]]:
    """Charge mit dem MEK-Fixture-Plan und synthetischen Transkripten für die genannten Clips."""
    root = tmp_path / "2026-06 MEK"
    (root / "Ergebnisse" / "O-Ton-Pläne").mkdir(parents=True)
    (root / "_intern" / "cache").mkdir(parents=True)
    (root / "Ergebnisse" / "O-Ton-Pläne" / "video-1-imagefilm.md").write_text(FIX_PLAN.read_text(encoding="utf-8"), encoding="utf-8")
    clips = {  # Stem → (Person, Dauer, Wörter)
        "FX3_9557": ("Sandra_Notaufnahme", 227.5, _words("Weil das mein Job ist Das ist meins", 217.5)),
        "FX3_9994": ("Ramona_Leiterin Intensivstation", 807.1,
                     _words("es gibt einem schon was wenn man merkt die Patienten ähm denen geht's besser Man ist Teil davon dass es den Menschen besser geht", 463.4)),
        "FX3_9993": ("Jessi_Intensivstation", 453.5,
                     _words("ich äh sag immer das ist die Familie die ich nie haben wollte aber", 315.5)
                     + _words("ich gehe arbeiten um Geld zu verdienen nicht um Freunde zu finden", 318.0, "speaker_1", 0.2)
                     + _words("der Zusammenhalt ist einfach super", 321.1)),
        "FX3_9558": ("Marina_Notaufnahme", 459.1,
                     _words("da haben ganz viele von uns glaube ich Zweifel gerade wenn wir von Station kommen Aber man lernt es super schnell", 209.0)),
        "FX3_9554": ("Martina_Notaufnahme", 729.8, _words("hier gibt was es nicht gibt", 100.0)),   # Verhörer: Score < 0.8, aber ≥ 0.7
        "FX3_9650": ("Sodan_Intensivstation", 618.9, []),          # kein Transkript → OFFEN
        "FX3_9651": ("Christian_Chefarzt Intensivstation", 413.7, []),
        "a7MK4_20260624_9889": ("Sandra_Notaufnahme", 670.2, []),
    }
    index, utterances = [], []
    for stem, (person, dur, words) in clips.items():
        path = str(tmp_path / "nas" / person / f"{stem}.MP4")
        fp = f"fp_{stem}"
        rolle = "kontext" if stem.startswith("a7") else "ton"
        index.append({"name": f"{stem}.MP4", "path": path, "kategorie": "Interviews", "person": person,
                      "kamera_rolle": rolle, "fingerprint": fp, "ok": True, "duration_s": dur, "n_words": len(words)})
        if words:
            (root / "_intern" / "cache" / f"{fp}.scribe.json").write_text(
                json.dumps({"source_file": f"{stem}.MP4", "engine": "scribe", "text": "", "words": words}), encoding="utf-8")
        utts = []
        if stem == "FX3_9557":   # Fusions-Antwort um 02:38: Frage (speaker_0) + zweiteilige Antwort (speaker_1)
            utts = [{"speaker": "speaker_0", "von": "02:33", "bis": "02:36", "von_s": 153.0, "bis_s": 156.0, "text": "Frage?"},
                    {"speaker": "speaker_1", "von": "02:36", "bis": "02:45", "von_s": 156.5, "bis_s": 165.0, "text": "Antwort Teil 1"},
                    {"speaker": "speaker_1", "von": "02:45", "bis": "02:51", "von_s": 165.8, "bis_s": 171.0, "text": "Antwort Teil 2"},
                    {"speaker": "speaker_0", "von": "02:52", "bis": "02:54", "von_s": 172.0, "bis_s": 174.0, "text": "Nächste Frage"}]
        if stem == "FX3_9994":   # „chillig" um 05:23: Plan-Zeit fällt noch in die Frage, Antwort beginnt 323.9
            utts = [{"speaker": "speaker_0", "von": "05:09", "bis": "05:23", "von_s": 309.0, "bis_s": 323.4, "text": "Frage"},
                    {"speaker": "speaker_1", "von": "05:23", "bis": "05:58", "von_s": 323.9, "bis_s": 358.6, "text": "chillig …"}]
        utterances.append({"name": f"{stem}.MP4", "person": person, "utterances": utts})
    (root / "_intern" / "transcripts_index.json").write_text(json.dumps(index), encoding="utf-8")
    (root / "_intern" / "utterances.json").write_text(json.dumps(utterances), encoding="utf-8")
    words_by_clip = {r["path"]: clips[Path(r["name"]).stem][2] for r in index}
    durations = {r["path"]: r["duration_s"] for r in index}
    return root, index, words_by_clip, durations, utterances


def test_draft_from_plan_beats(tmp_path):
    from niro_autocut.cutlist import draft_from_plan
    from niro_autocut.plan import parse_plan
    root, index, words, durations, utts = _mek_like(tmp_path)
    plan = parse_plan(root / "Ergebnisse" / "O-Ton-Pläne" / "video-1-imagefilm.md")
    cl, offen = draft_from_plan(plan, index, words, durations, CFG, 25.0, "16:9", utts)
    assert cl.video == "video-1-imagefilm.md" and cl.ziel_laenge_s == 185 and cl.fps == 25 and cl.pause_s == 1.0
    by_nr = {b.nr: b for b in cl.beats}
    assert len(cl.beats) == 12 and [b.typ for b in cl.beats][:5] == ["oton", "vo", "vo", "bild", "bild"]
    b1 = by_nr["1"]
    assert b1.person == "Sandra" and b1.rolle == "Fachkrankenschwester Notfallpflege"
    assert b1.clip.endswith("FX3_9557.MP4") and len(b1.cuts) == 1 and b1.plan_dauer_s == 3
    assert abs(b1.cuts[0].in_s - 217.5) < 1e-6 and b1.cuts[0].text.startswith("Weil")
    assert b1.cuts[0].hart_out is True and b1.cuts[0].hart_in is False      # „Harter Schnitt danach"
    assert b1.bild_hinweis.startswith("Gehaltenes Gesicht") and b1.caption is None and b1.sound == "Nur Raumton"
    b2 = by_nr["2"]
    assert b2.typ == "vo" and b2.text.startswith("Viele denken:") and b2.platzhalter_s == 6 and not b2.text.startswith("VO")
    assert by_nr["4"].typ == "bild" and by_nr["4"].platzhalter_s == 7 and by_nr["4"].caption == "„ELISABETH.\""
    b8 = by_nr["8"]                       # „[…]" ohne Jumpcut-Hinweis → EIN durchgehender Cut (Cutter-Standard)
    assert len(b8.cuts) == 1 and abs(b8.cuts[0].in_s - 315.5) < 1e-6 and b8.cuts[0].out_s > 321.1
    assert " […] " in b8.cuts[0].text and (b8.cuts[0].hart_in, b8.cuts[0].hart_out) == (False, False)
    assert by_nr["12"].cuts[0].hart_in is True         # „In hart bei …"
    b6 = by_nr["6"]                       # kein Transkript → clip gesetzt, cuts leer, offener Punkt
    assert b6.clip.endswith("FX3_9650.MP4") and b6.cuts == [] and any("#6" in o for o in offen)
    assert by_nr["10"].rolle == "Chefarzt Intensiv, ärztl. Direktor"   # „(s. o.)" → Rolle aus #9 übernommen
    assert verify_cutlist(cl, None, words, durations, CFG).errors   # Entwurf ist unvollständig → nicht baubar


def test_draft_from_plan_sperren(tmp_path):
    from niro_autocut.cutlist import draft_from_plan
    from niro_autocut.plan import parse_plan
    root, index, words, durations, utts = _mek_like(tmp_path)
    plan = parse_plan(root / "Ergebnisse" / "O-Ton-Pläne" / "video-1-imagefilm.md")
    cl, offen = draft_from_plan(plan, index, words, durations, CFG, 25.0, "16:9", utts)
    got = sorted((Path(s.clip).stem, s.von_s, s.bis_s) for s in cl.sperren)
    assert ("FX3_9994", 16.0, 52.0) in got and ("FX3_9994", 156.0, 204.0) in got      # Volkmarsen, zwei Bereiche
    assert ("FX3_9650", 311.0, 618.9) in got                                          # „ab 05:11" → Clip-Ende
    assert ("FX3_9557", 156.5, 171.0) in got                                          # 02:38 → ganze Antwort
    assert ("FX3_9994", 323.9, 358.6) in got                                          # „chillig" 05:23 → beginnende Antwort, nicht die Frage
    martina = [s for s in cl.sperren if Path(s.clip).stem == "FX3_9554"]              # Zitat ohne Zeit → find_quote
    assert len(martina) == 1 and martina[0].von_s < 100.4 < martina[0].bis_s
    assert any("Konkurrenz" in h for h in cl.hinweise)                                # reine Textsperre
    assert not any("Sperre" in o for o in offen), offen
    # Sperren-Prüfung akzeptiert alle Einträge (Clips im Index, gültige Intervalle)
    r = verify_cutlist(cl, None, words, durations, CFG)
    assert not any("Sperre" in e for e in r.errors), r.errors


def test_draft_cli_writes_and_refuses_overwrite(tmp_path):
    import subprocess, sys
    from niro_autocut.charge import TOOL_ROOT
    root, *_ = _mek_like(tmp_path)
    script = TOOL_ROOT / "scripts" / "autocut_cutlist_draft.py"
    r = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Entwurf geschrieben" in r.stdout and "OFFEN:" in r.stdout and "fps=25 angenommen" in r.stdout
    cl = Cutlist.load(root / "_intern" / "autocut" / "cutlist.json")
    assert len(cl.beats) == 12 and cl.sperren
    r = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
    assert r.returncode != 0 and "--force" in (r.stdout + r.stderr)
    r = subprocess.run([sys.executable, str(script), str(root), "--force"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_answer_span_rules():
    from niro_autocut.cutlist import _answer_span
    utts = [{"speaker": "s0", "von_s": 144.0, "bis_s": 157.1}, {"speaker": "s1", "von_s": 158.0, "bis_s": 159.9},
            {"speaker": "s0", "von_s": 160.0, "bis_s": 168.7}, {"speaker": "s1", "von_s": 172.6, "bis_s": 174.4},
            {"speaker": "s1", "von_s": 175.0, "bis_s": 180.0}]
    assert _answer_span(utts, 158.0) == (158.0, 159.9)      # beginnt bei t, nächste ist anderer Sprecher
    assert _answer_span(utts, 157.0) == (158.0, 159.9)      # t liegt noch in der Frage → beginnende Antwort
    assert _answer_span(utts, 172.0) == (172.6, 180.0)      # Antwort über zwei Utterances desselben Sprechers
    assert _answer_span(utts, 150.0) == (144.0, 157.1)      # nichts beginnt nahe t → enthaltende Utterance
    assert _answer_span(utts, 300.0) is None and _answer_span([], 1.0) is None


def test_from_dict_pause_null_and_non_number():
    d = _cl().to_dict()
    d["pause_s"] = None                                   # null → Standardpause, kein TypeError
    assert Cutlist.from_dict(d).pause_s == 1.0
    d["pause_s"] = "eins"
    with pytest.raises(AutoCutError, match="pause_s"):
        Cutlist.from_dict(d)
