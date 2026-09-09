from __future__ import annotations

import pytest

from niro_autocut.charge import AutoCutError, Charge
from niro_autocut.cutlist import Beat, Cut, Cutlist, Sperre
from niro_autocut.report import (fmt_mmss, fmt_tc, protokoll_zeilen_rohschnitt, render_broll_index,
                                 render_broll_plan, render_rohschnitt, write_report)
from niro_autocut.timeline_model import BeatPos, Item, MarkerSpec, TimelinePlan

FX, A7 = "/nas/Interviews/Sandra/FX3_1.MP4", "/nas/Interviews/Sandra/a7.MP4"
MEDIA = {"format": {"fps": 25, "width": 3840, "height": 2160, "orientation": "16:9"},
         "clips": {FX: {"ordner": "Sandra", "kamera": "FX3", "rolle": "ton", "original": {"nb_frames": 7500}},
                   A7: {"ordner": "Sandra", "kamera": "a7MK4", "rolle": "kontext", "original": {"nb_frames": 8000}}}}
SYNC = {"fps": 25, "paare": [
    {"ref": FX, "other": A7, "offset_s": 2.0, "offset_frames": 50, "confidence": 12.5, "overlap_ref": [0.0, 300.0],
     "drift_frames": 0.0, "ok": True, "note": ""},
    {"ref": "/nas/Interviews/Anna/FX3_2.MP4", "other": "/nas/Interviews/Anna/a7_2.MP4", "offset_s": 265.44,
     "offset_frames": 6636, "confidence": 1.04, "overlap_ref": [0.0, 71.5], "drift_frames": 0.0, "ok": False,
     "note": "Konfidenz 1.0 unter 4"}]}


def _cl():
    return Cutlist("v.md", 185, 25, "16:9", 1.0,
                   [Beat("1", "Hook", "oton", person="Sandra", rolle="Fachkrankenschwester", clip=FX,
                         cuts=[Cut(10, 12.3, "Weil")], plan_dauer_s=3),
                    Beat("2", "VO: Vorurteil", "vo", text="Viele denken …", platzhalter_s=6, bild_hinweis="Gesichter"),
                    Beat("3", "Schluss", "oton", person="Sandra", clip=FX, cuts=[Cut(20, 22, "Das ist meins")])],
                   sperren=[Sperre(FX, 100, 120, "Volkmarsen (Kunden-Tabu)")],
                   hinweise=["Textsperre ohne Zeit: Konkurrenz-Nennungen"])


def _tp():
    # Beat 1: 0–72 mit V2; Pause 25; Beat 2: 97–247 (Lücke); Pause 25; Beat 3: 272–322 ohne V2
    return TimelinePlan(25, 3840, 2160,
                        [Item("V1", FX, 244, 316, 0, 72, True, "1"), Item("A1", FX, 244, 316, 0, 72, True, "1"),
                         Item("V2", A7, 294, 366, 0, 72, True, "1"), Item("A2", A7, 294, 366, 0, 72, False, "1"),
                         Item("V1", FX, 494, 558, 272, 322, True, "3"), Item("A1", FX, 494, 558, 272, 322, True, "3")],
                        [MarkerSpec(0, "#1 Hook", "", "Blue"), MarkerSpec(97, "#2 VO: Vorurteil", "", "Yellow"),
                         MarkerSpec(272, "#3 Schluss", "", "Blue"),
                         MarkerSpec(273, "V2 fehlt #3 Schluss", "Keine a7-Abdeckung für diesen Schnitt.", "Red", 50)],
                        [BeatPos("1", "oton", 0, 72, FX, "Sandra"), BeatPos("2", "vo", 97, 247),
                         BeatPos("3", "oton", 272, 322, FX, "Sandra")], 322)


def test_fmt_tc():
    assert fmt_tc(0, 25) == "00:00:00" and fmt_tc(25 * 61 + 3, 25) == "01:01:03"
    assert fmt_tc(24, 23.976) == "00:01:00" and fmt_tc(-3, 25) == "-00:00:03"


def test_fmt_mmss():
    assert fmt_mmss(0) == "00:00" and fmt_mmss(185) == "03:05" and fmt_mmss(205.68) == "03:26"


def test_render_and_write(charge_dir):
    ch = Charge.open(charge_dir)
    cl = Cutlist("v.md", 185, 25, "16:9", 1.0, [Beat("1", "Hook", "oton", person="Sandra", clip="/nas/FX3_1.MP4", cuts=[Cut(10, 12.3, "Weil")])])
    tp = TimelinePlan(25, 3840, 2160, [Item("V1", "/nas/FX3_1.MP4", 244, 316, 0, 72), Item("V2", "/nas/a7.MP4", 294, 366, 0, 72)],
                      [MarkerSpec(0, "#1 Hook", "", "Blue")], [BeatPos("1", "oton", 0, 72, "/nas/FX3_1.MP4", "Sandra")], 72)
    txt = render_rohschnitt(cl, tp, {"paare": []}, {"timeline": "AutoCut v 2026", "warnings": []}, {"warnings": ["W1"]}, {"format": {"fps": 25, "width": 3840, "height": 2160}})
    assert "| 1 |" in txt and "Sandra" in txt and "FX3_1.MP4" in txt and "W1" in txt and "AutoCut v 2026" in txt
    p = write_report(ch, "v-rohschnitt.md", txt)
    assert p.parent == ch.ergebnisse and p.read_text(encoding="utf-8") == txt


def test_rohschnitt_beat_table_source_duration_v2():
    txt = render_rohschnitt(_cl(), _tp(), SYNC, {"timeline": "AutoCut v 2026-09-04 0010", "warnings": ["Proxy fehlt: a7.MP4"]},
                            {"ok": True, "errors": [], "warnings": ["Beat #1: Dauer 2,9 s statt ~3 s"]}, MEDIA)
    zeilen = {z.split("|")[1].strip(): z for z in txt.splitlines() if z.startswith("| ") and z.split("|")[1].strip() in ("1", "2", "3")}
    b1, b2, b3 = zeilen["1"], zeilen["2"], zeilen["3"]
    # Quelle dreiteilig: Person · Datei · mm:ss–mm:ss (Cutter-Standard), Rolle in Klammern
    assert "Sandra (Fachkrankenschwester) · FX3_1.MP4 · 00:10–00:12" in b1
    # V2 ja/nein aus den Items, Platzhalter ohne V2-Angabe
    assert "| ja |" in b1 and "| nein |" in b3 and "| – |" in b2
    # Dauer aus der Timeline (72 Frames = 2,9 s) mit Plan-Schätzung; Position als mm:ss:ff
    assert "2,9 s (Plan ~3 s)" in b1 and "00:00:00–00:02:22" in b1
    # Platzhalter zeigt Typ und Text/Bild-Hinweis
    assert "Platzhalter VO" in b2 and "Viele denken" in b2 and "6,0 s" in b2
    # Kopf: Timeline, Format, Gesamtlänge mm:ss (322 Frames = 12,88 s) mit Ziel und Abweichung
    assert "AutoCut v 2026-09-04 0010" in txt and "3840×2160" in txt and "00:13" in txt and "03:05" in txt
    assert "V2 (a7IV): 1 von 2 O-Ton-Beats" in txt
    # Warnungen aus Bau, Prüfung und roten Markern; Hinweise und Sperren aus der Cutlist
    assert "Proxy fehlt: a7.MP4" in txt and "Dauer 2,9 s statt ~3 s" in txt and "V2 fehlt #3 Schluss" in txt
    assert "Konkurrenz-Nennungen" in txt and "Volkmarsen (Kunden-Tabu)" in txt and "01:40–02:00" in txt


def test_rohschnitt_sync_table():
    txt = render_rohschnitt(_cl(), _tp(), SYNC, {"timeline": "T", "warnings": []}, {"warnings": []}, MEDIA)
    rows = [z for z in txt.splitlines() if z.startswith("| Sandra |") or z.startswith("| Anna |")]
    assert len(rows) == 2
    ok, bad = rows[0], rows[1]
    assert "FX3_1.MP4" in ok and "a7.MP4" in ok and "+50" in ok and "+2,000 s" in ok and "12,5" in ok and "| ok |" in ok
    assert "00:00–05:00" in ok and "| 1 |" in ok          # Überlappung und Beats, die das Paar nutzen
    assert "nicht ok — Konfidenz 1.0 unter 4" in bad and "+6636" in bad
    # ohne Paare: klarer Hinweis statt leerer Tabelle
    txt2 = render_rohschnitt(_cl(), _tp(), {"paare": []}, {"timeline": "T", "warnings": []}, {"warnings": []}, MEDIA)
    assert "Keine Sync-Paare" in txt2


def test_rohschnitt_no_warnings_and_missing_fields():
    cl = Cutlist("v.md", None, 25, "16:9", 1.0, [Beat("1", "Hook", "oton", clip=FX, cuts=[Cut(10, 12.3, "Weil")])])
    tp = TimelinePlan(25, 1080, 1920, [Item("V1", FX, 250, 308, 0, 58, True, "1")], [], [BeatPos("1", "oton", 0, 58, FX)], 58)
    txt = render_rohschnitt(cl, tp, {}, {}, {}, {})
    assert "Keine Warnungen" in txt and "Ziellänge: –" in txt and "| 1 |" in txt and "FX3_1.MP4" in txt


def test_write_report_refuses_paths_outside(charge_dir):
    ch = Charge.open(charge_dir)
    for bad in ("../Protokoll.md", "sub/dir.md", "/tmp/x.md", ""):
        with pytest.raises(AutoCutError):
            write_report(ch, bad, "x")
    assert not (charge_dir / "Protokoll.md").exists()


def test_protokoll_zeilen(charge_dir):
    ch = Charge.open(charge_dir)
    zeilen = protokoll_zeilen_rohschnitt(_cl(), _tp(), {"timeline": "AutoCut v 2026", "warnings": ["x"]},
                                         {"warnings": ["y"]}, ch.ergebnisse / "v-rohschnitt.md")
    txt = "\n".join(zeilen)
    assert "AutoCut v 2026" in txt and "3 Beats" in txt and "00:13" in txt and "03:05" in txt
    # Warnungen = Bau (x) + Prüfung (y) + roter Marker „V2 fehlt“ der Timeline
    assert "V2 (a7IV): 1 von 2" in txt and "3 Warnungen" in txt and "v-rohschnitt.md" in txt


IDX = {"erstellt_am": "2026-09-03T23:56:14", "modell": "claude-opus-5", "anzahl": 3, "fehler": ["FX3_9.MP4: Proxy leer"],
       "clips": [
           {"path": "/nas/S1/Sortiert/B-Roll/Flur/FX3_1.MP4", "datei": "FX3_1.MP4", "ordner": "Flur", "standort": "Standort 1",
            "dauer_s": 12.0, "beschreibung_kurz": "Pflegerin geht Flur entlang", "einstellung": "Halbtotale",
            "kamerabewegung": "Gimbal", "qualitaet_gesamt": 4, "tags": ["Flur", "Pflege"], "maengel": [], "eignung": ["Übergang"],
            "abschnitte": [{"von_s": 0, "bis_s": 8, "beschreibung": "", "qualitaet": 4, "verwendbar": True},
                           {"von_s": 8, "bis_s": 12, "beschreibung": "", "qualitaet": 2, "verwendbar": False}]},
           {"path": "/nas/S1/Sortiert/B-Roll/Flur/FX3_2.MP4", "datei": "FX3_2.MP4", "ordner": "Flur", "standort": "Standort 1",
            "dauer_s": 8.0, "beschreibung_kurz": "Blick in Kamera | Pfleger", "einstellung": "Nah", "kamerabewegung": "statisch",
            "qualitaet_gesamt": 2, "maengel": ["Blick in Kamera"],
            "abschnitte": [{"von_s": 0, "bis_s": 8, "beschreibung": "", "qualitaet": 2, "verwendbar": False}]},
           {"path": "/nas/S2/Sortiert/B-Roll/OP/FX3_3.MP4", "datei": "FX3_3.MP4", "ordner": "OP", "standort": "Standort 2",
            "beschreibung_kurz": "OP-Saal Detail"}]}


def test_render_broll_index():
    txt = render_broll_index(IDX)
    assert txt.startswith("# B-Roll-Index") and "claude-opus-5" in txt and "3" in txt
    assert "## Standort 1" in txt and "### Flur" in txt and "## Standort 2" in txt and "### OP" in txt
    rows = [z for z in txt.splitlines() if z.startswith("| FX3_")]
    assert len(rows) == 3
    r1 = rows[0]
    assert "12,0 s" in r1 and "Halbtotale" in r1 and "Gimbal" in r1 and "Pflegerin geht Flur entlang" in r1 and "| 4 |" in r1
    assert "1/2" in r1 and "0–8" in r1 and "Flur, Pflege" in r1
    assert "Blick in Kamera / Pfleger" in rows[1] and "Blick in Kamera" in rows[1]   # Pipe im Text entschärft
    assert "| – |" in rows[2]                                                         # fehlende Felder → „–"
    assert "## Fehler" in txt and "FX3_9.MP4: Proxy leer" in txt
    # Übersicht je Ordner: Clips, verwendbare, Ø Qualität
    assert "| Flur | Standort 1 | 2 | 1 | 3,0 |" in txt
    assert "Keine Clips" in render_broll_index({"clips": []}) and "Keine Clips" in render_broll_index({})


PLAN = {"video": "v.md", "beats": [
    {"beat_nr": "1", "items": [{"clip": "/nas/S1/Sortiert/B-Roll/Flur/FX3_1.MP4", "in_s": 1.0, "out_s": 4.0,
                                "start_offset_s": 3.0, "grund": "passt zur Bild-Spalte"}]},
    {"beat_nr": "2", "items": [{"clip": "/nas/S2/Sortiert/B-Roll/OP/FX3_3.MP4", "in_s": 2.0, "out_s": 4.5,
                                "start_offset_s": 0.0, "abweichung": True, "abweichung_grund": "S2 statt S1, weil kein Flur-Clip frei"},
                               {"clip": "/nas/Unbekannt/FX3_7.MP4", "in_s": 0, "out_s": 2}]},
    {"beat_nr": "3", "items": []}]}


def test_render_broll_plan():
    txt = render_broll_plan(PLAN, IDX)
    assert txt.startswith("# B-Roll-Zuordnung") and "v.md" in txt
    rows = [z for z in txt.splitlines() if z.startswith("| ")]
    r1 = next(z for z in rows if "FX3_1.MP4" in z)
    assert "| 1 |" in r1 and "Flur" in r1 and "00:01–00:04" in r1 and "3,0 s" in r1 and "+3,0 s" in r1
    assert "Pflegerin geht Flur entlang" in r1 and "passt zur Bild-Spalte" in r1
    r2 = next(z for z in rows if "FX3_3.MP4" in z)
    assert "| 2 |" in r2 and "OP" in r2 and "2,5 s" in r2 and "S2 statt S1" in r2 and "ja" in r2
    r3 = next(z for z in rows if "FX3_7.MP4" in z)
    assert "| – |" in r3 or "nicht im Index" in r3
    assert "3" in txt and "ohne B-Roll" in txt and "Abweichungen: 1" in txt
    assert "Keine Items" in render_broll_plan({}, {}) or "Keine B-Roll" in render_broll_plan({}, {})
    # Spec 5: broll_plan.json darf die reine Beat-Liste sein — gleiche Zeilen wie beim Dict
    assert "FX3_1.MP4" in render_broll_plan(PLAN["beats"], IDX) and "Abweichungen: 1" in render_broll_plan(PLAN["beats"], IDX)
