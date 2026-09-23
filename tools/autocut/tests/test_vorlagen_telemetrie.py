"""Vorlagen 6d und 3a: kompilieren, nutzen die Telemetrie-Helfer (stabil_vorschlag, Brennweitenregel), Spalten stabil/zoom,
Stabilize und Zoom nur für ausgewählte Shots; Planfunktionen mit Telemetrie-Datensätzen ohne Resolve. Gesichts-Check (6e)
und Grafik-Review (6b) zeigen V3 mit dem digitalen Zoom."""
from __future__ import annotations

import importlib.util
import py_compile
from pathlib import Path

import pytest

from niro_autocut import telemetrie as T
from niro_autocut.charge import load_config

VORLAGE = Path(__file__).resolve().parents[1] / "vorlagen" / "feinschnitt" / "feinschnitt_bauen.py"
VORLAGE_3A = VORLAGE.with_name("broll_einsetzen.py")
GESICHTSCHECK = VORLAGE.parent / "gesichtscheck" / "gesichtscheck.py"
GRAFIK_REVIEW = VORLAGE.with_name("grafik_review.py")
README = VORLAGE.parents[1] / "README.md"


def test_vorlage_kompiliert_und_nutzt_telemetrie():
    py_compile.compile(str(VORLAGE), doraise=True)
    text = VORLAGE.read_text(encoding="utf-8")
    assert "from niro_autocut import telemetrie as TM" in text
    assert "TM.stabil_vorschlag(" in text and "TM.finden(" in text and "TM.laden(" in text
    assert "TM.genutzter_quellbereich_s(" in text             # Quellbereich korrekt skaliert (Fix-Runde 1)
    assert "stabil_hand" in text and '"stabil_grund"' in text
    assert 'if not m["stabil"]' in text                      # Stabilize() nur für ausgewählte Shots


def test_readme_nennt_die_spalte():
    assert "stabil" in README.read_text(encoding="utf-8") and "telemetrie.json" in README.read_text(encoding="utf-8")


# --- Final Review (21.09.2026): Spalte 7 True bei _stabilized-Datei stoppt den Bau (I4) -----------------------------------

def test_vorlage_prueft_spalte_7_true_bei_stabilized():
    """I4: User-Regel — Avata nur als …_stabilized, nie der Resolve-Stabilizer; die Vorlage meldet das als Plan-Fehler."""
    text = VORLAGE.read_text(encoding="utf-8")
    assert "Spalte 7 True bei _stabilized-Datei — Avata nie in Resolve stabilisieren" in text
    assert '"_stabilized" in' in text


def _vorlage_laden(monkeypatch):
    """Vorlage als Modul laden; ihr Import setzt RA.TRACK_INDEX["A3"] — auf einer Kopie, damit nichts in andere Tests
    wandert."""
    from niro_autocut import resolve_api as RA
    monkeypatch.setattr(RA, "TRACK_INDEX", dict(RA.TRACK_INDEX))
    spec = importlib.util.spec_from_file_location("feinschnitt_bauen_vorlage", VORLAGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("datei,spalte7,fehler_erwartet", [
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (True,), True),
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (), False),        # Vorschlag: nie stabilisieren
    ("/ssd/Avata/DJI_0005_D_stabilized.mov", (False,), False),
    ("/ssd/FX3/FX3_0001.MP4", (True,), False),                   # Handkamera-Datei darf erzwungen werden
])
def test_plan_stoppt_bei_spalte_7_true_und_stabilized(monkeypatch, datei, spalte7, fehler_erwartet):
    fb = _vorlage_laden(monkeypatch)
    monkeypatch.setattr(fb, "anpassen_pruefen", lambda fuer_bau=False: None)
    monkeypatch.setattr(fb, "ENDE", 100)
    monkeypatch.setattr(fb, "alpha_min", lambda: [255] * 100)
    monkeypatch.setattr(fb, "v4_stuecke", lambda fehler: [])
    monkeypatch.setattr(fb, "BROLL", [(1, 0, 40, 0, "1", False, *spalte7)])
    shots = {1: {"nr": 1, "clip": Path(datei).stem, "datei": datei, "clip_fps": 25.0, "left_offset_f": 0, "dauer_f": 100}}
    p, fehler = fb.plan({"items": []}, shots)
    treffer = [f for f in fehler if "Spalte 7 True bei _stabilized-Datei" in f]
    assert bool(treffer) is fehler_erwartet
    if fehler_erwartet:
        assert treffer == ["S01: Spalte 7 True bei _stabilized-Datei — Avata nie in Resolve stabilisieren"]


# --- Brennweitenregel und Zoomfahrten (Spec 2026-09-21) ------------------------------------------------------------------

def _zoom(von: float, bis: float, von_mm: float, bis_mm: float, tempo: float) -> dict:
    return {"von_s": von, "bis_s": bis, "von_mm": von_mm, "bis_mm": bis_mm, "tempo_max": tempo, "tempo_mittel": tempo,
            "ruck": 0.1, "ruckartig": False, "urteil": "schnell"}


# Clip A: 35 → 50 mm bei 0,4–0,9 s, 50 mm bis 2 s, dann Zoom auf 100 mm. Clip B: 24 → 52 mm bei 2,0–2,5 s, 52 mm bis
# 3,7 s, dann Zoom auf 70 mm (4,2 s). Beide 50p, gimbal, gemessen mit den ausgelieferten Schwellen (config_hash).
HASH = T.config_hash(load_config(Path("/nirgendwo"))["telemetrie"])
TELE_A = {"path": "/ssd/FX3/FX3_A.MP4", "quelle": "rtmd", "haltung": "gimbal", "wackeln": 0.02, "fehler": None,
          "config_hash": HASH, "fenster": [[0.0, 0.02, 0.1, "statisch"]],
          "kb_verlauf": [[0.0, 35.0], [0.4, 35.0], [0.9, 50.0], [2.0, 50.0], [3.0, 100.0], [10.0, 100.0]],
          "zooms": [_zoom(0.4, 0.9, 35.0, 50.0, 72.4), _zoom(2.0, 3.0, 50.0, 100.0, 69.3)]}
TELE_B = {**TELE_A, "path": "/ssd/FX3/FX3_B.MP4",
          "kb_verlauf": [[0.0, 24.0], [2.0, 24.0], [2.5, 52.0], [3.7, 52.0], [4.2, 70.0], [10.0, 70.0]],
          "zooms": [_zoom(2.0, 2.5, 24.0, 52.0, 150.0), _zoom(3.7, 4.2, 52.0, 70.0, 59.4)]}
SHOTS = {1: {"nr": 1, "clip": "FX3_A", "datei": "/ssd/FX3/FX3_A.MP4", "clip_fps": 50.0, "left_offset_f": 0,
             "dauer_f": 100},
         2: {"nr": 2, "clip": "FX3_B", "datei": "/ssd/FX3/FX3_B.MP4", "clip_fps": 50.0, "left_offset_f": 50,
             "dauer_f": 100}}


def _fb_plan(monkeypatch, broll: list[tuple], tele: list[dict]):
    fb = _vorlage_laden(monkeypatch)
    monkeypatch.setattr(fb, "anpassen_pruefen", lambda fuer_bau=False: None)
    monkeypatch.setattr(fb, "ENDE", 80)
    monkeypatch.setattr(fb, "alpha_min", lambda: [255] * 80)
    monkeypatch.setattr(fb, "v4_stuecke", lambda fehler: [])
    monkeypatch.setattr(fb, "TELE", tele)
    monkeypatch.setattr(fb, "TCFG", {**fb.TCFG, "brennweite_gleich_max": 0.2, "digitalzoom_faktor": 1.25,
                                     "digitalzoom_max": 1.5})
    monkeypatch.setattr(fb, "BROLL", broll)
    p, fehler = fb.plan({"items": []}, SHOTS)
    return fb, p, fehler


def test_6d_plan_brennweitenregel_mit_50_prozent(monkeypatch, capsys):
    """S01 (100 %) Record 0–40: Quelle 0–80 Frames = 0–1,6 s → am Out 50 mm. S02 (50 %) Record 40–80 direkt danach:
    Quell-In (50 + 20) · 2 = 140 Frames = 2,8 s, 40 Timeline-Frames bei 50 % = 0,8 s Quelle → 2,8–3,6 s → am In
    52 mm. 50/52 mm = gleich → Zoom 1,25× auf S02 (längere Brennweite). Schneller Zoom 0,4–0,9 s liegt in S01;
    der von B bei 3,7–4,2 s liegt nur bei 100 % im genutzten Bereich, bei 50 % nicht."""
    fb, p, fehler = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True)], [TELE_A, TELE_B])
    assert fehler == []
    m1, m2 = p["v3_meta"]
    assert (m1["kb_ende"], m2["kb_anfang"]) == (50.0, 52.0) and (m1["zoom"], m2["zoom"]) == (1.0, 1.25)
    assert m1["zoom_hinweise"] == ["S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)"] and m2["zoom_hinweise"] == []
    assert m2["zoom_hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02" and m1["zoom_hinweis"] is None
    fb.bericht(p)
    out = capsys.readouterr().out
    assert "Hinweis: S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)" in out
    assert "Hinweis: S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02" in out
    assert "KB 52 → 52 mm  Zoom 1,25×" in out and "keine Telemetrie" not in out
    assert "neu laufen lassen" not in out                        # aktuelle Datensätze: kein Hinweis auf alte Telemetrie


def test_6d_plan_spalte_zoom_und_ohne_telemetrie(monkeypatch, capsys):
    _, p, fehler = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True, None, 1.0)],
                            [TELE_A, TELE_B])
    assert fehler == [] and [m["zoom"] for m in p["v3_meta"]] == [1.3, 1.0]     # S02 fest → A: 1,25 × 52 / 50
    _, p2, fehler2 = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True, None, 1.6)],
                              [TELE_A, TELE_B])
    assert "S02: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)" in fehler2
    fb, p3, fehler3 = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True)], [])
    assert fehler3 == [] and [m["zoom"] for m in p3["v3_meta"]] == [1.0, 1.0]
    fb.bericht(p3)
    assert "Hinweis: keine Telemetrie — Brennweitenregel nicht geprüft" in capsys.readouterr().out


def test_6d_meldet_alte_und_abweichende_telemetrie(monkeypatch, capsys):
    """I2 (Final Review 21.09.2026): Datensätze von vor der Umstellung (rtmd ohne kb_verlauf) bzw. mit anderen
    Schwellen schalten die Brennweitenregel sonst stumm ab — der Probelauf meldet sie je genutztem Clip."""
    alt_a = {k: v for k, v in TELE_A.items() if k not in ("kb_verlauf", "zooms")}
    anders_b = {**TELE_B, "config_hash": "ffffffffffff"}
    fb, p, fehler = _fb_plan(monkeypatch, [(1, 0, 40, 0, "1", False), (2, 20, 40, 40, "1", True)], [alt_a, anders_b])
    assert fehler == [] and p["v3_meta"][0]["kb_anfang"] is None
    fb.bericht(p)
    out = capsys.readouterr().out
    assert "Hinweis: 1 Clip ohne Brennweitenverlauf (alte Telemetrie) — autocut_telemetrie.py neu laufen lassen" in out
    assert "Hinweis: 1 Clip mit anderen Telemetrie-Schwellen gemessen — autocut_telemetrie.py neu laufen lassen" in out
    assert "keine Telemetrie" not in out


def test_6d_vorlage_setzt_zoom_beim_bau():
    text = VORLAGE.read_text(encoding="utf-8")
    assert "TM.brennweitenfolge(folge, TCFG)" in text and "TM.kb_am(" in text and "TM.zoom_hinweise(" in text
    assert "tempo_faktor=0.5 if langsam else 1.0" in text      # Zeitlupe: sichtbares Tempo zählt
    assert 'RA._safe(x.SetProperty, False, k, float(m["zoom"]))' in text and 'for k in ("ZoomX", "ZoomY")' in text
    assert 'RA._safe(x.GetProperty, None, "ZoomX")' in text and 'out["zoom_abweichungen"]' in text
    assert "8. Spalte optional" in text
    # M3: Readback über den Record-In (TM.zoom_abweichungen), nicht über die Position der Items
    assert 'out["zoom_abweichungen"] = TM.zoom_abweichungen(p["v3_meta"], zoom_ist)' in text
    assert "zip(sorted(p[\"v3_meta\"], key=lambda v: v[\"rec_in_f\"]), v3_zoom)" not in text


def _3a_pruefen(monkeypatch, plan: list[tuple], tele: list[dict]):
    spec = importlib.util.spec_from_file_location("broll_einsetzen_vorlage", VORLAGE_3A)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "TELE", tele)
    monkeypatch.setattr(mod, "TCFG", {**mod.TCFG, "brennweite_gleich_max": 0.2, "digitalzoom_faktor": 1.25,
                                      "digitalzoom_max": 1.5})
    monkeypatch.setattr(mod, "PLAN", plan)
    tl = {"items": [{"rec_out_f": 200}], "beats": [{"nr": "1"}]}
    zeilen, fehler = mod.pruefen(SHOTS, tl)
    return mod, tl, zeilen, fehler


def test_3a_pruefen_brennweitenregel_bei_100_prozent(monkeypatch, capsys):
    """Wie 6d, aber Tempo 100 %: S02 nutzt die Quelle 2,8–4,4 s (140 + 80 Frames bei 50p) — dort liegt der schnelle
    Zoom 3,7–4,2 s von B (Hinweis). Am Schnitt 50/52 mm → Zoom 1,25× auf S02."""
    mod, tl, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")],
                                          [TELE_A, TELE_B])
    assert fehler == [] and [z["zoom"] for z in zeilen] == [1.0, 1.25]
    assert zeilen[0]["zoom_hinweise"] == ["S01: schneller Zoom 0,4–0,9 s (35 → 50 mm, 72 %/s)"]
    assert zeilen[1]["zoom_hinweise"] == ["S02: schneller Zoom 3,7–4,2 s (52 → 70 mm, 59 %/s)"]
    assert zeilen[1]["zoom_hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02"
    # M4: KB-Brennweite am Quell-In/-Out je Shot im Plan (→ broll_einsatz.json) — S02 3,9–4,4 s: 59,2 … 70 → 68,2
    assert [(z["kb_anfang"], z["kb_ende"]) for z in zeilen] == [(35.0, 50.0), (52.0, 68.2)]
    mod.bericht(zeilen, tl)
    out = capsys.readouterr().out
    assert "Zoom 1,25×" in out and "Hinweis: S02: schneller Zoom 3,7–4,2 s (52 → 70 mm, 59 %/s)" in out
    assert "A  KB 35 → 50 mm" in out and "B  KB 52 → 68,2 mm  Zoom 1,25×" in out


def test_3a_hinweis_nennt_den_sprung(monkeypatch):
    """I1: ein Zoom, der nur wegen des Sprungs schnell ist (91 %/s unter 100, Sprung 18,2 %), nennt im 3a-Hinweis den
    Sprung — die Vorlage gibt die Telemetrie-Config an zoom_hinweise weiter."""
    sprung = {**_zoom(3.7, 4.2, 52.0, 70.0, 91.2), "sprung_proz": 18.2}
    tele_b = {**TELE_B, "zooms": [TELE_B["zooms"][0], sprung]}
    _, _, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")],
                                       [TELE_A, tele_b])
    assert fehler == []
    assert zeilen[1]["zoom_hinweise"] == ["S02: schneller Zoom 3,7–4,2 s (52 → 70 mm, 91 %/s, Sprung 18 %)"]


def test_3a_pruefen_spalte_zoom_und_ohne_telemetrie(monkeypatch, capsys):
    _, _, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B", 1.0)],
                                       [TELE_A, TELE_B])
    assert fehler == [] and [z["zoom"] for z in zeilen] == [1.3, 1.0]
    _, _, _, fehler2 = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A", 1.6), (2, 20, 40, 40, "1", "B")],
                                   [TELE_A, TELE_B])
    assert fehler2 == ["S01: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"]
    mod, tl, zeilen3, fehler3 = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")], [])
    assert fehler3 == [] and [z["zoom"] for z in zeilen3] == [1.0, 1.0]
    assert [(z["kb_anfang"], z["kb_ende"]) for z in zeilen3] == [(None, None), (None, None)]
    mod.bericht(zeilen3, tl)
    out = capsys.readouterr().out
    assert "Hinweis: keine Telemetrie — Brennweitenregel nicht geprüft" in out and out.count("KB –") == 2


def test_3a_meldet_alte_telemetrie(monkeypatch, capsys):
    """I2: wie 6d — beide Clips vor der Umstellung gemessen → Hinweis, jeder Shot „KB –"."""
    alte = [{k: v for k, v in r.items() if k not in ("kb_verlauf", "zooms", "config_hash")} for r in (TELE_A, TELE_B)]
    mod, tl, zeilen, fehler = _3a_pruefen(monkeypatch, [(1, 0, 40, 0, "1", "A"), (2, 20, 40, 40, "1", "B")], alte)
    assert fehler == [] and [z["zoom"] for z in zeilen] == [1.0, 1.0]
    mod.bericht(zeilen, tl)
    out = capsys.readouterr().out
    assert "Hinweis: 2 Clips ohne Brennweitenverlauf (alte Telemetrie) — autocut_telemetrie.py neu laufen lassen" in out
    assert "anderen Telemetrie-Schwellen" not in out


def test_3a_vorlage_setzt_zoom_beim_bau():
    py_compile.compile(str(VORLAGE_3A), doraise=True)
    text = VORLAGE_3A.read_text(encoding="utf-8")
    assert "TM.brennweitenfolge(folge, TCFG)" in text and "TM.genutzter_quellbereich_s(" in text
    assert 'SetProperty, False, k, float(z["zoom"]))' in text and 'for k in ("ZoomX", "ZoomY")' in text
    assert 'RA._safe(it.GetProperty, None, "ZoomX")' in text and '"zoom_abweichungen": zoom_abweichungen' in text
    assert "zoom_abweichungen = TM.zoom_abweichungen(zeilen, zoom_ist)" in text      # M3: wie 6d, Liste {shot, soll, ist}


# --- Final Review (21.09.2026) I3: Gesichts-Check und Grafik-Review mit dem digitalen Zoom ------------------------------

def _modul(monkeypatch, pfad: Path, name: str):
    """Vorlage als Modul laden (der Gesichts-Check lädt fb, das RA.TRACK_INDEX["A3"] setzt — auf einer Kopie)."""
    from niro_autocut import resolve_api as RA
    monkeypatch.setattr(RA, "TRACK_INDEX", dict(RA.TRACK_INDEX))
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("pfad,breite,hoehe", [(GESICHTSCHECK, 960, 540), (GRAFIK_REVIEW, 1920, 1080)])
def test_pruefbild_filter_mit_digitalem_zoom(monkeypatch, pfad, breite, hoehe):
    """I3: ZoomX/ZoomY auf die Bildmitte wie beim Bau = Ausschnitt iw/z × ih/z (crop mittig) vor dem Skalieren."""
    mod = _modul(monkeypatch, pfad, f"{pfad.stem}_vorlage")
    assert mod.bild_filter(1.25) == f"crop=iw/1.25:ih/1.25,scale={breite}:{hoehe}"
    assert mod.bild_filter(1.266) == f"crop=iw/1.266:ih/1.266,scale={breite}:{hoehe}"
    assert mod.bild_filter(1.0) == mod.bild_filter(None) == f"scale={breite}:{hoehe}"


def test_gesichtscheck_holt_v3_mit_zoom(monkeypatch):
    """I3: das oberste Bild trägt den Zoom aus fb.plan (v3_meta); er gehört in die Cache-Signatur und in den Filter."""
    from niro_autocut.timeline_model import Item
    gc = _modul(monkeypatch, GESICHTSCHECK, "gesichtscheck_vorlage")
    p = {"v3_meta": [{"rec_in_f": 0, "langsam": False, "zoom": 1.25}, {"rec_in_f": 50, "langsam": True, "zoom": 1.0}],
         "V3": [Item("V3", "/ssd/A.MP4", 100, 200, 0, 50, True, "1", "broll", True),
                Item("V3", "/ssd/B.MP4", 0, 100, 50, 100, True, "1", "broll", True)],
         "V2": [], "V1": []}
    a, b = gc.oberstes_bild(p, 10), gc.oberstes_bild(p, 60)
    assert a == ("V3", "/ssd/A.MP4", 2.4, False, 0, 1.25)          # (100 + 2 · 10) / 50 s, Zoom 1,25
    assert b == ("V3", "/ssd/B.MP4", 0.2, False, 50, 1.0)          # 50 %: (0 + 1 · 10) / 50 s
    assert gc.signatur(a) == "/ssd/A.MP4@2.400×1.25" and gc.signatur(b) == "/ssd/B.MP4@0.200"
    assert gc.signatur(None) is None
    text = GESICHTSCHECK.read_text(encoding="utf-8")
    assert '"-vf", bild_filter(zoom)' in text and "signatur(lagen[f])" in text


def test_grafik_review_legt_die_grafik_ueber_den_gezoomten_ausschnitt():
    """I3: V3 aus broll_einsatz.json mit Spalte zoom des Plans (ältere Dateien ohne zoom: 1,0)."""
    spec = importlib.util.spec_from_file_location("grafik_review_vorlage", GRAFIK_REVIEW)
    gr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gr)
    broll = {"plan": [{"rec_in_f": 0, "rec_out_f": 50, "datei": "/ssd/A.MP4", "left_offset_f": 25, "zoom": 1.25},
                      {"rec_in_f": 50, "rec_out_f": 100, "datei": "/ssd/B.MP4", "left_offset_f": 0}]}
    tl = {"items": [{"track": "V1", "clip": "/ssd/FX3.MP4", "src_in_f": 0, "rec_in_f": 0, "rec_out_f": 100}]}
    assert gr.schichten(10, tl, broll) == [("V3", "/ssd/A.MP4", 1.4, 1.25), ("V1", "/ssd/FX3.MP4", 0.4, 1.0)]
    assert gr.schichten(60, tl, broll)[0] == ("V3", "/ssd/B.MP4", 0.4, 1.0)
    assert '"-vf", bild_filter(zoom)' in GRAFIK_REVIEW.read_text(encoding="utf-8")


# --- 6d Gyroflow-Verdrahtung (Spec 2026-09-22, Gesamtprüfung 23.09.2026) ------------------------------------
# Der Bau braucht Resolve und ist nicht ausführbar zu testen. Geprüft wird darum der Quelltext genau der
# Stabilisierungs-Schleife — eng genug, dass ein Rückfall in die alten Muster auffällt.

def _gyro_schleife() -> str:
    """Quelltext der Stabilisierungs-Schleife (Gyroflow-Zweig und Stabilize()-Rückfall) aus der 6d-Vorlage."""
    text = VORLAGE.read_text(encoding="utf-8")
    i = text.index('for n_, m in enumerate(p["v3_meta"], 1):')
    return text[i:text.index('out["stabilisiert"] = stab', i)]


def test_gyroflow_block_nimmt_die_haltung_aus_dem_gyroflow_datensatz():
    """Ein zweiter Join über TM.finden (exakter String, sonst Dateiname) griff bei zwei Karten mit FX3_0001.MP4
    ins Leere und machte aus einer Handkamera still ein Stativ — Smoothness 0,2 statt 0,7, und das überstimmt
    laut Befund 1 Punkt 5 auch das Sidecar. haltung steht im selben Datensatz wie der Sidecar-Pfad."""
    block = _gyro_schleife()
    assert 'eintrag.get("haltung")' in block
    assert "TM.finden(" not in block


def test_gyroflow_block_prueft_ob_der_sidecar_noch_existiert():
    """Sidecars laufen nicht über studio_abgleich.sh. Fehlt die Datei nach einem NAS-Umzug, nimmt SetInput den
    toten Pfad klaglos an — ohne Prüfung wäre der Shot weder per Gyroflow noch per Stabilize() stabilisiert."""
    block = _gyro_schleife()
    assert "Path(sidecar).is_file()" in block
    assert "Sidecar fehlt" in block


def test_gyroflow_block_zaehlt_erst_nach_dem_readback():
    """Hausregel wie bei zoom_abweichungen/speed_gesetzt: setzen, zurücklesen, dann zählen. Vorher zählte
    gyroflow_gesetzt die Versuche, nicht die Erfolge."""
    block = _gyro_schleife()
    assert "GetInput" in block
    assert block.index("GetInput") < block.index("gyroflow_gesetzt += 1")
    assert "gyrodata nicht gesetzt" in block
    # Ein leerer Readback ist der Fehlschlag; ein anders geschriebener Pfad wird gemeldet, gilt aber als gesetzt —
    # sonst legte ein PathMap-Unterschied auf jedem Shot zusätzlich Stabilize() über den Gyroflow-Comp.
    assert "gesetzt_ok = isinstance(ist, str) and bool(ist)" in block
    assert "gyrodata anders zurückgelesen" in block


def test_gyroflow_block_meldet_shots_ganz_ohne_eintrag():
    """Häufigster echter Fall: veraltete gyroflow.json (BROLL geändert, --bauen ohne neuen Sidecar-Lauf).
    Ohne Diagnose nähmen genau die neuen Shots still den alten Weg."""
    assert '"grund": "kein Sidecar"' in _gyro_schleife()


def test_gyroflow_block_greift_nicht_mit_harter_klammer_auf_die_config():
    """Der Block darf nicht raisen (er läuft nach append_items, mitten im Bau)."""
    block = _gyro_schleife()
    assert 'CFG["gyroflow"]' not in block
    assert '(CFG.get("gyroflow") or {}).get("glaettung")' in block


def test_gyroflow_joins_laufen_ueber_norm_pfad():
    """Alle Pfad-Joins rund um Gyroflow über GF.norm_pfad (aufgelöst + NFC) — Path.resolve() allein lässt
    NFD ≠ NFC stehen, und macOS liefert Umlaute teils in NFD."""
    text = VORLAGE.read_text(encoding="utf-8")
    assert text.count("GF.norm_pfad(") >= 2
    assert "expanduser().resolve()" not in text


def test_probelauf_verodert_tempo50_ueber_alle_verwendungen():
    """Dieselbe Quelldatei einmal mit 100 % und einmal mit 50 % im Schnitt: „erste gewinnt" wies sie im Bericht
    falsch aus. Reine Anzeige — VideoSpeed leitet der Bau je Shot aus m[\"langsam\"] ab."""
    text = VORLAGE.read_text(encoding="utf-8")
    i = text.index("gyro_clips, nach_datei")
    block = text[i:text.index("gyroflow_clips.json", i)]
    assert 'eintrag["tempo50"] = eintrag["tempo50"] or bool(zeile[5])' in block
    assert "gesehen" not in block                       # kein Set, das die zweite Verwendung verwirft
