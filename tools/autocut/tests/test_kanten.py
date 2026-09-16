"""Kantenprüfung (Spec 2026-09-16): Schnappschuss, Schnitte, Maske, Timecode, Befund-Regeln, Wortkanten — ohne ffmpeg."""
from __future__ import annotations

import unicodedata
from pathlib import Path

import numpy as np
import pytest
import yaml

from niro_autocut import kanten as K
from niro_autocut.charge import DEFAULTS_FILE, AutoCutError, Charge

TL = {"name": "T", "start_frame": 90000, "end_frame": 90100, "start_timecode": "01:00:00:00", "fps": "25",
      "tracks": {
          "V1": {"name": "FX3", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": 100.0},
              {"name": "b.MP4", "file": "/x/b.MP4", "start": 90040, "end": 90100, "duration": 60, "src_in": 0,
               "src_out": 60, "enabled": False, "left_offset": 0, "speed": 50.0}]},
          "A1": {"name": "Ton", "items": [
              {"name": "a.MP4", "file": "/x/a.MP4", "start": 90000, "end": 90040, "duration": 40, "src_in": 99,
               "src_out": 139, "enabled": True, "left_offset": 100, "speed": None},
              {"name": "c.MP4", "file": "/x/c.MP4", "start": 90050, "end": 90090, "duration": 40, "src_in": 5,
               "src_out": 45, "enabled": True, "left_offset": None, "speed": None}]}},
      "markers": {}, "n_items": 4}


@pytest.fixture
def cfg() -> dict:
    return yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["kanten"]


def _snap() -> dict:
    return K.snapshot_from_readback(TL, "P", gelesen_am="2026-09-16T12:00:00")


def test_snapshot_relative_frames_left_offset_and_flags():
    s = _snap()
    assert (s["timeline"], s["projekt"], s["fps"], s["laenge"], s["start_timecode"]) == ("T", "P", 25.0, 100, "01:00:00:00")
    assert s["spuren"]["V1"][0] == {"name": "a.MP4", "datei": "/x/a.MP4", "start": 0, "dauer": 40, "quell_in": 100,
                                    "aktiv": True, "tempo": 100.0}
    assert s["spuren"]["V1"][1]["aktiv"] is False and s["spuren"]["V1"][1]["tempo"] == 50.0
    assert s["spuren"]["A1"][1]["quell_in"] is None and s["spuren"]["A1"][1]["start"] == 50
    assert s["quelle"] == "resolve" and s["gelesen_am"] == "2026-09-16T12:00:00"


def test_snapshot_rejects_missing_end_or_fps():
    with pytest.raises(AutoCutError, match="kein Ende"):
        K.snapshot_from_readback({**TL, "end_frame": None}, "P")
    with pytest.raises(AutoCutError, match="Bildrate"):
        K.snapshot_from_readback({**TL, "fps": None}, "P")


def test_schnitte_skip_inactive_items_and_timeline_edges():
    s = _snap()
    assert K.schnitte(s, "bild") == [40]
    assert K.schnitte(s, "ton") == [40, 50, 90]


def test_ton_maske_excludes_item_edges():
    m = K.ton_maske(_snap())
    assert m.shape == (100,)
    assert not m[0] and m[1] and m[38] and not m[39] and not m[45]
    assert not m[50] and m[51] and m[88] and not m[89]


def test_timecode_and_back():
    assert K.timecode(0, 25) == "01:00:00:00"
    assert K.timecode(25 * 61 + 7, 25) == "01:01:01:07"
    assert K.tc_to_frame("01:01:01:07", 25) == 1532
    assert K.timecode(3, 50, "00:59:59:48") == "01:00:00:01"
    with pytest.raises(AutoCutError, match="Timecode"):
        K.tc_to_frame("1:2", 25)


def test_kontext_nearest_cuts_and_items():
    s = _snap()
    k = K.kontext(s, 42, K.schnitte(s, "bild"), K.schnitte(s, "ton"))
    assert k["bild_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["ton_schnitt"] == {"frame": 40, "abstand": -2}
    assert k["items"] == []
    assert K.kontext(s, 10, [], [])["items"] == [{"spur": "A1", "name": "a.MP4"}, {"spur": "V1", "name": "a.MP4"}]
    assert K.kontext(s, 10, [], [])["bild_schnitt"] is None


def test_laeufe():
    assert K.laeufe([False, True, True, False, True]) == [(1, 3), (4, 5)]
    assert K.laeufe([]) == []


def test_schwarzbild_runs(cfg):
    mittel, streuung = np.full(10, 80.0), np.full(10, 30.0)
    mittel[4:7], streuung[4:7] = cfg["schwarz_mittel_max"] - 8, 0.5
    got = K.schwarz_befunde(mittel, streuung, cfg)
    assert [(b["art"], b["frame"], b["frames"]) for b in got] == [("Schwarzbild", 4, 3)]
    assert got[0]["wert"] == round(cfg["schwarz_mittel_max"] - 8, 1)


def test_schnipsel_one_frame_merge_and_black(cfg):
    n, hoch = 60, cfg["wechsel_diff_min"] + 20
    d, mittel, streuung = np.zeros(n), np.full(n, 80.0), np.full(n, 30.0)
    d[10] = d[11] = hoch                                           # 1 Frame Schnipsel
    d[20] = d[20 + cfg["schnipsel_max_frames"] + 3] = hoch         # weit genug auseinander → normale Schnitte
    d[35] = d[36] = hoch
    mittel[35], streuung[35] = cfg["schwarz_mittel_max"] - 8, 0.5  # schwarzer Einzelframe → nur Schwarzbild
    d[45] = d[46] = d[47] = hoch                                   # Flackern → ein Befund über 2 Frames
    got = K.schnipsel_befunde(d, mittel, streuung, cfg)
    assert [(b["frame"], b["frames"]) for b in got] == [(10, 1), (45, 2)]
    assert got[0]["wert"] == round(hoch, 1)


def _ton(sekunden: float = 2.0, seed: int = 1) -> np.ndarray:
    sr = 48000
    rng = np.random.default_rng(seed)
    t = np.arange(int(sr * sekunden)) / sr
    x = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 1330 * t) + rng.normal(0, 0.001, t.size)
    return np.stack([x, x], axis=1).astype(np.float32)


def test_knackser_only_at_cut_sample(cfg):
    sr, fps, spf = 48000, 25.0, 1920
    sauber = _ton()
    assert K.knack_befunde(sauber, sr, fps, [12], cfg)[0] == []
    sprung = sauber.copy()
    sprung[12 * spf:, 0] += 0.3                                   # Sprung genau am Schnitt-Sample, nur links
    befunde, verh = K.knack_befunde(sprung, sr, fps, [12], cfg)
    assert [(b["art"], b["frame"], b["kanal"]) for b in befunde] == [("Knackser", 12, 1)]
    assert abs(befunde[0]["versatz_ms"]) <= cfg["knack_kante_ms"] and verh[0] >= cfg["knack_faktor"]
    daneben = sauber.copy()
    daneben[12 * spf + int(0.2 * sr):, 0] += 0.3                  # 200 ms neben dem Schnitt
    assert K.knack_befunde(daneben, sr, fps, [12], cfg)[0] == []


def test_knack_messung_handles_file_edges(cfg):
    x = _ton(0.05)
    assert K.knack_messung(x, 48000, 0, cfg)["verhaeltnis"] >= 0.0
    assert K.knack_messung(x[:2], 48000, 1, cfg)["spitze"] == 0.0


def test_tonloch_in_mask_only(cfg):
    sr, fps, spf, n = 48000, 25.0, 1920, 40
    lang, kurz = int(cfg["tonloch_min_frames"]) + 1, int(cfg["tonloch_min_frames"]) - 1
    x = np.random.default_rng(2).normal(0, 0.01, (n * spf, 2)).astype(np.float32)
    x[10 * spf:(10 + lang) * spf] = 0.0
    if kurz > 0:
        x[30 * spf:(30 + kurz) * spf] = 0.0
    rms = K.rms_dbfs_je_frame(x, sr, fps, n)
    assert rms[10] == -200.0 and rms[5] > -50
    maske = np.zeros(n, dtype=bool)
    maske[5:36] = True
    got = K.tonloch_befunde(rms, maske, cfg)
    assert [(b["frame"], b["frames"]) for b in got] == [(10, lang)]
    assert got[0]["wert"] == -200.0
    assert K.tonloch_befunde(rms, np.zeros(n, dtype=bool), cfg) == []


@pytest.fixture
def charge(charge_dir: Path) -> Charge:
    return Charge.open(charge_dir)


def _fx3(charge: Charge) -> str:
    return charge.load_index()[0]["path"]


class _Stub:
    """Ersatz für Transkripte: liefert für jeden Clip dieselbe Wortliste (oder None)."""

    def __init__(self, woerter):
        self._w = woerter

    def woerter(self, datei):
        return self._w


def test_transkripte_match_path_nfd_and_unique_name(charge):
    import json
    index = charge.load_index()
    index[0]["path"] = str(Path(index[0]["path"]).parent.parent / "Jörn" / "FX3_0001.MP4")
    (charge.intern / "transcripts_index.json").write_text(json.dumps(index), encoding="utf-8")
    t = K.Transkripte(charge)
    pfad = index[0]["path"]
    assert [w["text"] for w in t.woerter(pfad)] == ["Das", "ist", "meins."]
    assert t.woerter(unicodedata.normalize("NFD", pfad)) is not None
    assert t.woerter("/Volumes/SSD/woanders/FX3_0001.MP4") is not None      # eindeutiger Dateiname
    assert t.woerter("/x/unbekannt.MP4") is None and t.woerter(None) is None


def _ton_snap(datei: str, items: list[tuple[int, int, int]]) -> dict:
    """Schnappschuss mit A1-Items (start, dauer, quell_in) eines Clips."""
    return {"fps": 25.0, "laenge": 200, "start_timecode": "01:00:00:00", "timeline": "T",
            "spuren": {"A1": [{"name": Path(datei).name, "datei": datei, "start": s, "dauer": d, "quell_in": q,
                               "aktiv": True, "tempo": None} for s, d, q in items]}}


def _pegel_stub(laut: list[tuple[float, float]], grund: float = -70.0, spitze: float = -25.0):
    """Pegel-Funktion wie im Skript: 10-ms-RMS in dBFS für [von_s, bis_s); laut = Bereiche mit Sprache (Quellsekunden)."""
    def pegel(datei, von_s, bis_s):
        n = int(round((bis_s - von_s) / 0.01))
        t = von_s + (np.arange(n) + 0.5) * 0.01
        db = np.full(n, grund)
        for a, b in laut:
            db[(t >= a) & (t < b)] = spitze
        return db
    return pegel


def _ton_item(name, start, dauer, quell_in, tempo=None, datei=None):
    return {"name": name, "datei": datei or name, "start": start, "dauer": dauer, "quell_in": quell_in, "aktiv": True,
            "tempo": tempo}


def test_wort_befunde_level_rule(cfg):
    """Kalibrierung Taxodia 16.09.: Scribe-Wortenden hängen vor Komma/„ähm" nach — gemeldet wird nur, wenn der Pegel
    auf beiden Seiten der Kante nahe der Wortspitze liegt (nicht im Tal)."""
    assert cfg["wort_tal_db"] >= 6 and cfg["wort_pegel_min_dbfs"] <= -40
    woerter = [{"text": "Hallo", "start": 1.0, "end": 1.6}, {"text": "Welt.", "start": 2.0, "end": 2.8},
               {"text": "kurz", "start": 3.0, "end": 3.0}]
    laut = [(1.0, 1.5), (2.0, 2.7)]                  # hörbare Sprache endet vor dem Scribe-Wortende
    snap = {"fps": 25.0, "laenge": 500, "start_timecode": "01:00:00:00", "timeline": "T", "spuren": {"A1": [
        _ton_item("a", 0, 20, 30),                   # In 1,20 s mitten in „Hallo" (laut) → Befund
        _ton_item("b", 100, 14, 25),                 # Out 1,56 s: Scribe-Wort, aber Pegeltal → kein Befund
        _ton_item("c", 200, 10, 50, 50.0),           # Tempo 50 % → nicht geprüft
        _ton_item("d", 300, 15, 60),                 # In 2,40 s mitten in „Welt." → Befund; Out 3,00 s: Wort mit Länge 0
    ]}}
    befunde, z = K.wort_befunde(snap, _Stub(woerter), cfg, pegel=_pegel_stub(laut))
    assert [(b["clip"], b["seite"], b["wort"], b["frame"]) for b in befunde] == [("a", "in", "Hallo", 0),
                                                                                ("d", "in", "Welt.", 300)]
    assert befunde[0]["wert"] == 0.0 and befunde[0]["kante_dbfs"] == -25.0
    assert (z["mit_transkript"], z["ohne_transkript"], z["ohne_quelle"]) == (3, 0, 0)


def test_wort_befunde_quiet_word_and_missing_source(cfg):
    woerter = [{"text": "leise", "start": 1.0, "end": 1.6}]
    snap = {"fps": 25.0, "laenge": 100, "start_timecode": "01:00:00:00", "timeline": "T",
            "spuren": {"A1": [_ton_item("a", 0, 20, 30)]}}
    fluestern = _pegel_stub([(1.0, 1.6)], grund=-80.0, spitze=cfg["wort_pegel_min_dbfs"] - 5)
    assert K.wort_befunde(snap, _Stub(woerter), cfg, pegel=fluestern)[0] == []
    befunde, z = K.wort_befunde(snap, _Stub(woerter), cfg, pegel=lambda datei, von, bis: None)
    assert befunde == [] and (z["mit_transkript"], z["ohne_quelle"], z["ohne_quelle_liste"]) == (0, 1, ["a"])
    befunde, z = K.wort_befunde(snap, _Stub(woerter), cfg)
    assert befunde == [] and z["ohne_quelle"] == 1


def test_wort_befunde_real_transcript(charge, cfg):
    snap = {"fps": 25.0, "laenge": 200, "start_timecode": "01:00:00:00", "timeline": "T", "spuren": {"A1": [
        _ton_item("FX3_0001.MP4", 0, 20, 35, datei=_fx3(charge)),            # In 1,40 s in „ist" (1,3–1,5), Out 2,20 s frei
        _ton_item("x.MP4", 40, 5, 0, datei="/x/x.MP4")],                     # ohne Transkript, O-Ton-Spur
        "A2": [_ton_item("Musik.wav", 0, 100, 0, datei="/m/Musik.wav")]}}   # Musikspur: nicht aufgelistet
    befunde, z = K.wort_befunde(snap, K.Transkripte(charge), cfg, pegel=_pegel_stub([(1.0, 2.0)]))
    assert [(b["seite"], b["wort"]) for b in befunde] == [("in", "ist")]
    assert (z["mit_transkript"], z["ohne_transkript"], z["ohne_liste"]) == (1, 1, ["x.MP4"])


def test_export_woerter_shift_and_window(charge):
    snap = _ton_snap(_fx3(charge), [(100, 25, 25)])                 # Export 4,0–5,0 s zeigt Quelle 1,0–2,0 s
    t = K.Transkripte(charge)
    assert K.export_woerter(snap, t, 4.25, 4.55) == [{"text": "ist", "start": 4.3, "end": 4.5}]
    assert [w["text"] for w in K.export_woerter(snap, t, 0.0, 10.0)] == ["Das", "ist", "meins."]


def test_kennzahlen_and_diff_verteilung():
    assert K.kennzahlen([]) == {"n": 0}
    assert K.kennzahlen([1, 2, 3, 4]) == {"n": 4, "median": 2.5, "p95": 3.85, "max": 4.0}
    d = np.array([0.0, 1.0, 2.0, 50.0, 2.0, 1.0, 3.0])
    v = K.diff_verteilung(d, [3])
    assert v["an_schnitten"]["n"] == 1 and v["an_schnitten"]["max"] == 50.0
    assert v["uebrige"] == {"n": 3, "median": 1.0, "p95": 2.8, "max": 3.0}


def test_pruefe_combines_rules_numbers_and_context(cfg):
    n, fps, sr, spf = 50, 25.0, 48000, 1920
    snap = {"quelle": "plan", "gelesen_am": "x", "projekt": "P", "timeline": "T", "fps": fps, "start_frame": 0,
            "start_timecode": "01:00:00:00", "laenge": n, "spuren": {
                "V1": [{"name": "v", "datei": "v", "start": 0, "dauer": 20, "quell_in": 0, "aktiv": True, "tempo": 100.0},
                       {"name": "w", "datei": "w", "start": 20, "dauer": 30, "quell_in": 0, "aktiv": True, "tempo": 100.0}],
                "A1": [{"name": "a", "datei": "/x/a", "start": 0, "dauer": 50, "quell_in": 0, "aktiv": True, "tempo": None}]}}
    mittel, streuung = np.full(n, 90.0, dtype=np.float32), np.full(n, 30.0, dtype=np.float32)
    diff = np.zeros(n, dtype=np.float32)
    diff[20] = cfg["wechsel_diff_min"] + 20
    mittel[35], streuung[35] = cfg["schwarz_mittel_max"] - 8, 0.5
    audio = np.random.default_rng(3).normal(0, 0.01, (n * spf, 2)).astype(np.float32)
    lang = int(cfg["tonloch_min_frames"]) + 1
    audio[40 * spf:(40 + lang) * spf] = 0.0
    erg = K.pruefe(snap, {"mittel": mittel, "streuung": streuung, "diff": diff}, audio, sr, _Stub(None), cfg)
    assert erg["zaehlung"] == {"Schwarzbild": 1, "Schnipsel": 0, "Knackser": 0, "Tonloch": 1, "Wort angeschnitten": 0}
    assert [(b["nr"], b["art"], b["frame"], b["timecode"]) for b in erg["befunde"]] == [
        (1, "Schwarzbild", 35, "01:00:01:10"), (2, "Tonloch", 40, "01:00:01:15")]
    assert erg["befunde"][0]["kontext"]["bild_schnitt"] == {"frame": 20, "abstand": -15}
    assert erg["umfang"] == {"bild_schnitte": 1, "ton_schnitte": 0, "mit_transkript": 0, "ohne_transkript": 0,
                             "ohne_liste": [], "ohne_quelle": 0, "ohne_quelle_liste": []}
    assert erg["verteilung"]["diff"]["an_schnitten"]["n"] == 1 and erg["hinweise"] == []
    assert erg["warnungen"] == ["Kein Tonclip mit Transkript gefunden — Wortkanten nicht geprüft (transcripts_index.json "
                                "der Charge, Dateinamen der O-Ton-Clips prüfen)."]


def test_knackser_small_step_in_dense_signal(cfg):
    """Kalibrierung Taxodia 16.09.: kleiner Sprung (−30 dBFS) unter dichtem Klang (10 Töne bis 6 kHz) wird erkannt,
    ohne Sprung nicht — der frühere Vergleich der zweiten Differenz mit dem 99. Perzentil kam hier nur auf ≈ 3."""
    sr, fps, spf = 48000, 25.0, 1920
    rng = np.random.default_rng(5)
    t = np.arange(2 * sr) / sr
    x = sum(0.05 * np.sin(2 * np.pi * f * t + ph) for f, ph in zip(rng.uniform(200, 6000, 10), rng.uniform(0, 6.3, 10)))
    x = np.stack([x, x], axis=1) + rng.normal(0, 0.0005, (t.size, 2))
    assert K.knack_befunde(x.astype(np.float32), sr, fps, [12], cfg)[0] == []
    x[12 * spf:] += 0.03
    befunde, _ = K.knack_befunde(x.astype(np.float32), sr, fps, [12], cfg)
    assert [b["frame"] for b in befunde] == [12]


def test_pruefe_schnipsel_an_grafikkante_wird_hinweis(cfg):
    n = 60
    snap = {"quelle": "plan", "gelesen_am": "x", "projekt": "P", "timeline": "T", "fps": 25.0, "start_frame": 0,
            "start_timecode": "01:00:00:00", "laenge": n, "spuren": {
                "V1": [{"name": "v", "datei": "v", "start": 0, "dauer": n, "quell_in": 0, "aktiv": True, "tempo": 100.0}],
                "V4": [{"name": "Adjustment Clip", "datei": None, "start": 0, "dauer": n, "quell_in": 90000,
                        "aktiv": True, "tempo": 100.0}],
                "V5": [{"name": "g", "datei": "/p/Charge/Ergebnisse/Renders/g.mov", "start": 20, "dauer": 10,
                        "quell_in": 0, "aktiv": True, "tempo": 100.0}]}}
    mittel, streuung, diff = np.full(n, 90.0), np.full(n, 30.0), np.zeros(n)
    hoch = cfg["wechsel_diff_min"] + 20
    diff[20] = diff[21] = hoch                     # Flash am Grafik-Start → Hinweis
    diff[45] = diff[46] = hoch                     # fern jeder Grafik-Kante → Befund
    erg = K.pruefe(snap, {"mittel": mittel, "streuung": streuung, "diff": diff}, None, 48000, _Stub(None), cfg)
    assert [(b["art"], b["frame"]) for b in erg["befunde"]] == [("Schnipsel", 45)]
    assert erg["hinweise"] == [{"art": "Grafik-Übergang", "frame": 20, "frames": 1, "wert": round(hoch, 1),
                                "timecode": "01:00:00:20"}]
    ohne = K.pruefe(snap, {"mittel": mittel, "streuung": streuung, "diff": diff}, None, 48000, _Stub(None),
                    {**cfg, "grafik_spuren": [], "grafik_pfade": []})
    assert ohne["zaehlung"]["Schnipsel"] == 2 and ohne["hinweise"] == []
    spur = K.pruefe(snap, {"mittel": mittel, "streuung": streuung, "diff": diff}, None, 48000, _Stub(None),
                    {**cfg, "grafik_spuren": ["V5"], "grafik_pfade": []})
    assert [b["frame"] for b in spur["befunde"]] == [45] and len(spur["hinweise"]) == 1
