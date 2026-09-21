"""telemetrie.py — Kennzahlen (synthetische Verläufe), Clip-Messung, Cache, Charge-Lauf, 2b/6d-Helfer (Task 4)."""
from __future__ import annotations

import json
import math
import os
import shutil
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest

from niro_autocut import rtmd as R
from niro_autocut import telemetrie as T
from niro_autocut.charge import Charge, load_config
from niro_autocut.media import MediaInfo

CFG = {"fenster_s": 2.0, "schritt_s": 1.0, "tiefpass_s": 0.5, "ruhig_max_px": 0.15, "stativ_max_grad_s": 0.3,
       "stativ_max_px": 0.02, "schwenk_min_grad_s": 3.0, "schwenk_min_px": 1.0, "hf_grenze_hz": 3.0,
       "hand_hf_anteil_min": 0.35, "pitch_klassen_grad": [-60, -8, 8],
       "achsen": {"schwenk": 1, "tilt": 0}, "vorzeichen": {"schwenk": -1, "tilt": 1, "pitch": 1},
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2,
       "zoom_min_proz": 3.0, "zoom_rausch_proz_s": 1.0, "zoom_schnell_proz_s": 20.0, "zoom_ruck_max": 0.6,
       "zoom_stocken_anteil": 0.2, "zoom_verlauf_hz": 5, "brennweite_gleich_max": 0.20, "digitalzoom_faktor": 1.25,
       "digitalzoom_max": 1.5}


def _sinus(hz: float, amp: float, n: int = 100, fps: float = 25.0) -> np.ndarray:
    t = np.arange(n) / fps
    return np.stack([amp * np.sin(2 * math.pi * hz * t), np.zeros(n)], axis=1)


def test_f_px_und_gyro_je_frame():
    assert T.f_px(36.0) == 480.0 and round(T.f_px(283.8), 1) == 3784.0
    g = np.tile(np.array([[1.0, 2.0, 3.0]]), (160, 1))
    g[80:] *= 2
    m = T.gyro_je_frame(g, 80, 25.0)
    assert m.shape == (2, 3) and np.allclose(m[0], [1, 2, 3]) and np.allclose(m[1], [2, 4, 6])
    assert T.gyro_je_frame(g, 40, 50.0).shape == (2, 3)          # 50p: 40 Proben je Frame, 2 Frames je Zielframe
    assert T.gyro_je_frame(np.zeros((0, 3)), 80, 25.0).shape == (0, 3)


def test_verschiebung_aus_rate_achsen_und_vorzeichen():
    rate = np.zeros((4, 3))
    rate[:, 1] = 10.0                                    # Schwenk um y mit 10 °/s
    dxy = T.verschiebung_aus_rate(rate, 36.0, CFG)     # f_px 480 → 10 °/s ≙ 3,351 px je Frame
    assert dxy.shape == (4, 2) and np.allclose(dxy[:, 0], -3.351, atol=0.01) and np.allclose(dxy[:, 1], 0)
    rate2 = np.zeros((4, 3))
    rate2[:, 0] = 5.0                                    # Tilt um x
    dxy2 = T.verschiebung_aus_rate(rate2, 36.0, CFG)
    assert np.allclose(dxy2[:, 0], 0) and np.allclose(dxy2[:, 1], 1.676, atol=0.01)


def test_wackeln_bewegung_wie_ruhe_py():
    dxy = np.array([[0, 0], [1, 0], [0, 0], [1, 0]], float)
    wk, bw = T.wackeln_bewegung(dxy)
    # Mittel über beide Spalten: |Δdx| = 1,1,1 / |Δdy| = 0 → 0,5; |dx| Mittel 0,5, |dy| 0 → 0,25
    assert wk == 0.5 and bw == 0.25
    assert T.wackeln_bewegung(np.zeros((1, 2))) == (0.0, 0.0)


def test_hf_anteil_trennt_schnell_von_langsam():
    assert T.hf_anteil(_sinus(6.0, 1.0)) > 0.9
    assert T.hf_anteil(_sinus(0.5, 3.0)) < 0.1
    assert T.hf_anteil(np.zeros((100, 2))) == 0.0 and T.hf_anteil(np.zeros((4, 2))) == 0.0


def test_schwellen_px_mit_und_ohne_brennweite():
    min_px, stativ_px = T.schwellen_px(36.0, CFG)
    assert round(min_px, 3) == 1.005 and round(stativ_px, 4) == 0.1005     # 3 °/s bzw. 0,3 °/s bei f_px 480
    assert T.schwellen_px(None, CFG) == (1.0, 0.02)


@pytest.mark.parametrize("dxy,erwartet", [
    (np.zeros((50, 2)), "statisch"),
    (np.tile([[2.0, 0.0]], (50, 1)), "schwenk_links"),
    (np.tile([[-2.0, 0.0]], (50, 1)), "schwenk_rechts"),
    (np.tile([[0.0, 2.0]], (50, 1)), "tilt_auf"),
    (np.tile([[0.0, -2.0]], (50, 1)), "tilt_ab"),
    (np.vstack([np.tile([[2.0, 0.0]], (25, 1)), np.tile([[-2.0, 0.0]], (25, 1))]), "gemischt"),
    (np.tile([[2.0, 2.0]], (50, 1)), "gemischt"),
])
def test_bewegungsart_klassen(dxy, erwartet):
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == erwartet


def test_bewegungsart_fahrt_ohne_dominante_richtung():
    rng = np.random.default_rng(0)
    dxy = rng.normal(0, 0.3, (50, 2))                  # Bewegung da, Mittel ≈ 0 → Fahrt
    assert T.bewegungsart(dxy, CFG, 1.0, 0.02) == "fahrt"


def test_haltung():
    assert T.haltung(np.zeros((100, 2)), 0.02, CFG) == "stativ"
    assert T.haltung(_sinus(6.0, 1.0), 0.02, CFG) == "hand"
    assert T.haltung(_sinus(0.3, 3.0), 0.02, CFG) == "gimbal"


def test_fenster_und_mehrheit():
    fen = T.fenster(np.tile([[2.0, 0.0]], (100, 1)), CFG, 1.0, 0.02)
    assert [f["t_s"] for f in fen] == [0.0, 1.0, 2.0, 3.0] and all(f["bewegungsart"] == "schwenk_links" for f in fen)
    # 3-s-Clip optisch: 74 Verschiebungen
    assert [f["t_s"] for f in T.fenster(np.zeros((74, 2)), CFG, 1.0, 0.02)] == [0.0, 1.0]
    assert fen[0]["wackeln"] == 0.0 and fen[0]["bewegung"] == 1.0
    kurz = T.fenster(np.zeros((20, 2)), CFG, 1.0, 0.02)
    assert len(kurz) == 1 and kurz[0]["t_s"] == 0.0
    assert T.fenster(np.zeros((1, 2)), CFG, 1.0, 0.02) == []
    assert T.mehrheit(["fahrt", "fahrt", "statisch"]) == "fahrt" and T.mehrheit(["fahrt", "statisch"]) == "gemischt"
    assert T.mehrheit([]) == "gemischt"


def test_lage_pitch_roll_und_gate():
    ruhig = np.tile([[0.0, 1.15, 0.0]], (200, 1))                       # FX3-Betrag 1,15 g, waagerecht
    l = T.lage(ruhig)
    assert l["pitch_grad"] == 0.0 and l["roll_grad"] == 0.0 and l["grund"] is None
    unten = np.tile([[0.0, math.cos(math.radians(30)), -math.sin(math.radians(30))]], (200, 1))
    assert T.lage(unten)["pitch_grad"] == -30.0                          # Kamera schaut 30° nach unten
    assert T.lage(unten, vorzeichen_pitch=-1.0)["pitch_grad"] == 30.0
    schief = np.tile([[math.sin(math.radians(2)), math.cos(math.radians(2)), 0.0]], (200, 1))
    assert T.lage(schief)["roll_grad"] == 2.0
    wild = np.tile([[0.0, 1.0, 0.0]], (200, 1)) * np.linspace(0.5, 1.5, 200)[:, None]
    assert T.lage(wild)["pitch_grad"] is None and "schwankt" in T.lage(wild)["grund"]
    assert T.lage(np.zeros((0, 3)))["grund"] == "keine Beschleunigungsdaten"


def test_klassen():
    assert not hasattr(T, "brennweitenklasse")                 # Brennweitenklassen entfallen (Spec 2026-09-21)
    perspektiven = [T.perspektive_hoehe(p, [-60, -8, 8]) for p in (-90, -60, -12, -8, 0, 7.9, 8, 20)]
    assert perspektiven == (["Vogelperspektive", "Vogelperspektive", "Aufsicht", "Aufsicht", "Augenhöhe",
                             "Augenhöhe", "Untersicht", "Untersicht"])
    assert T.perspektive_hoehe(None, [-60, -8, 8]) is None


def test_kennzahlen_gesamt():
    k = T.kennzahlen(np.tile([[2.0, 0.0]], (100, 1)), CFG, 36.0)
    assert k["wackeln"] == 0.0 and k["bewegung"] == 1.0 and k["haltung"] == "gimbal" and k["bewegungsart"] == "schwenk_links"
    assert k["fenster"][0] == [0.0, 0.0, 1.0, "schwenk_links", None] and k["ruhige_fenster"] == [0.0, 1.0, 2.0, 3.0]
    assert k["hf_anteil"] == 0.0 and k["schaerfe_p10"] is None
    mit = T.kennzahlen(np.zeros((100, 2)), CFG, None, schaerfe=np.linspace(1.0, 10.0, 101))   # optisch: n+1 Frames
    assert mit["schaerfe_p10"] == 0.21 and mit["fenster"][0][4] < mit["fenster"][-1][4] <= 1.1
    assert mit["fenster"][0][4] == round(float(np.percentile(np.linspace(1.0, 10.0, 101)[:50], 10)) / 9.1, 2)
    unruhig = T.kennzahlen(_sinus(6.0, 1.0), CFG, None)
    assert unruhig["haltung"] == "hand" and unruhig["ruhige_fenster"] == [] and unruhig["hf_anteil"] > 0.9


def _info(path: str, fps: float = 25.0, dauer: float = 4.0) -> MediaInfo:
    return MediaInfo(path=path, duration_s=dauer, fps=fps, width=3840, height=2160, rotation=0, nb_frames=int(dauer * fps),
                     timecode=None, has_audio=True, sample_rate=48000, channels=2)


def _kb(mm: float) -> bytes:
    """KB-Brennweite in mm als RDD-18-Wert (Exponent −4: 0,1 mm Auflösung bis 409,5 mm), z. B. 71,6 → c2cc."""
    return struct.pack(">H", 0xC000 | int(round(mm * 10)))


def _rtmd_puffer(frames: int = 100, proben: int = 80, gyro_y: float = 0.0, acc=(0.0, 1.15, 0.0),
                 kb: bytes | list[bytes] = bytes.fromhex("c2cc")) -> bytes:
    """Synthetische Datenspur: je Frame ein Sample mit konstantem Gyro (°/s um y) und Schwerkraftvektor; ``kb`` als
    Liste = KB-Brennweite je Frame (``_kb``)."""
    def imu(v):
        out = struct.pack(">II", proben, 6)
        for _ in range(proben):
            out += struct.pack(">hhh", *v)
        return out
    g = imu((0, int(round(gyro_y * 65.5)), 0))
    a = imu(tuple(int(round(x * 8192)) for x in acc))
    tags = {R.TAG_GYRO: g, R.TAG_GYRO_SKALA: struct.pack(">f", 65.5), R.TAG_ACC: a,
            R.TAG_ACC_SKALA: struct.pack(">f", 8192.0),
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: kb if isinstance(kb, bytes) else kb[0],
            R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"), R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    if isinstance(kb, bytes):
        return R.paket_bauen(tags) * frames
    return b"".join(R.paket_bauen({**tags, R.TAG_KB_MM: k}) for k in kb[:frames])


def test_defaults_haben_telemetrie_block():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    for k in ("fenster_s", "ruhig_max_px", "achsen", "vorzeichen", "px_faktor", "optisch_fuer", "optisch_breite",
              "parallel"):
        assert k in cfg


def test_clip_messen_rtmd_weg(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0001.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100, gyro_y=10.0))
    rng = np.random.default_rng(9)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (101, 1, 1)))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "rtmd" and rec["kamera"] == "FX3" and rec["imu_hz"] == 2000.0 and rec["samples"] == 100
    assert rec["schaerfe_p10"] is None and rec["fenster"][0][4] is None    # rtmd ohne --schaerfe: keine Dekodierung
    mit = T.clip_messen(clip, CFG, schaerfe=True)
    assert mit["quelle"] == "rtmd" and mit["schaerfe_p10"] == 1.0 and mit["fenster"][0][4] == 1.0
    assert rec["kb_mm"] == 71.6 and rec["brennweite_mm"] == 67.7 and rec["fokus_m"] == 15.82 and rec["zoomfahrt"] is False
    assert "brennweitenklasse" not in rec and rec["pitch_grad"] == 0.0 and rec["perspektive_hoehe"] == "Augenhöhe"
    # Rechnet mit der Test-CFG (Vorzeichen Schwenk −1, Stand vor der Kalibrierung): Gyro-y +10 °/s → dx negativ →
    # schwenk_rechts. Ausgeliefert ist +1 (defaults.yaml) → schwenk_links: test_ausgelieferte_konvention_aus_defaults_yaml
    assert rec["bewegungsart"] == "schwenk_rechts"
    assert rec["haltung"] == "gimbal" and rec["wackeln"] == 0.0 and rec["bewegung"] > 3
    # 10 °/s bei 71,6 mm KB ≈ 6,7 px dx, Mittel über dx/dy ≈ 3,3
    assert len(rec["fenster"]) == 4 and rec["ruhige_fenster"] == [0.0, 1.0, 2.0, 3.0] and rec["fehler"] is None


def test_clip_messen_faellt_ohne_datenspur_auf_optisch(monkeypatch, tmp_path):
    clip = tmp_path / "DJI_0504.MOV"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    rng = np.random.default_rng(10)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (30, 1, 1)))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "optisch" and rec["kamera"] == "DJI" and rec["kb_mm"] is None and rec["haltung"] == "stativ"
    assert rec["schaerfe_p10"] == 1.0 and rec["fenster"][0][4] == 1.0                     # optisch: Schärfe kostenlos dabei
    ohne = T.clip_messen(clip, CFG, ohne_optisch=True)
    assert ohne["quelle"] == "keine" and ohne["fenster"] == [] and ohne["schaerfe_p10"] is None


def test_clip_messen_optisch_fuer_kamera_behaelt_brennweite(monkeypatch, tmp_path):
    clip = tmp_path / "a7MK4_1.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p), fps=50.0))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=200, proben=40, gyro_y=10.0))
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.zeros((30, hoehe, breite), np.uint8))
    rec = T.clip_messen(clip, {**CFG, "optisch_fuer": ["a7IV"]})
    assert (rec["quelle"] == "optisch" and rec["kb_mm"] == 71.6 and rec["kb_verlauf"] == [[0.0, 71.6]]
           and rec["haltung"] == "stativ")


def test_clip_messen_fehler_wird_datensatz(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0002.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: (_ for _ in ()).throw(T.AutoCutError("ffprobe kaputt")))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "keine" and "ffprobe kaputt" in rec["fehler"] and rec["clip"] == "FX3_0002"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_telemetrie_charge_mit_inventar_und_cache(basis_charge, tmp_path):
    clip = tmp_path / "nas" / "DJI_0001.mp4"
    clip.parent.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    (ac / "inventar.json").write_text(
        json.dumps([{"ordner": "Mavic", "name": clip.name, "path": str(clip)}]), encoding="utf-8")
    ch = Charge.open_basis(basis_charge)
    cfg = load_config(basis_charge)["telemetrie"]
    clips = T.clips_finden(ch)
    assert clips == [{"path": str(clip), "ordner": "Mavic"}]
    out = T.telemetrie_charge(ch, clips, cfg, melden=lambda *a, **k: None)
    assert out["gemessen"] == 1 and out["cache_treffer"] == 0 and out["fehler"] == []
    tele = T.laden(ac)
    assert len(tele) == 1 and tele[0]["quelle"] == "optisch" and tele[0]["clip"] == "DJI_0001" and tele[0]["fingerprint"]
    assert len(list((ac / "telemetrie").glob("*.json"))) == 1
    assert 0 <= tele[0]["wackeln"] < 5 and len(tele[0]["fenster"]) == 2                # testsrc: 3 s → Fenster bei 0 und 1 s
    again = T.telemetrie_charge(ch, clips, cfg, melden=lambda *a, **k: None)
    assert again["cache_treffer"] == 1 and again["gemessen"] == 0
    neu = T.telemetrie_charge(ch, clips, cfg, force=True, melden=lambda *a, **k: None)
    assert neu["gemessen"] == 1


def test_clips_finden_reihenfolge_und_ordner(basis_charge, tmp_path):
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    with pytest.raises(T.AutoCutError):
        T.clips_finden(ch)
    d = tmp_path / "B-Roll" / "Flur"
    d.mkdir(parents=True)
    (d / "FX3_0003.MP4").write_bytes(b"x")
    (d / "Proxy").mkdir()
    (d / "Proxy" / "FX3_0003.mov").write_bytes(b"x")
    (d / ".versteckt.mp4").write_bytes(b"x")
    assert T.clips_finden(ch, [str(tmp_path / "B-Roll")]) == [{"path": str(d / "FX3_0003.MP4"), "ordner": "Flur"}]
    (ac / "broll_index.json").write_text(
        json.dumps({"clips": [{"path": "/nas/x/FX3_9.MP4", "ordner": "Allgemein"}]}), encoding="utf-8")
    (ac / "inventar.json").write_text(json.dumps([{"path": "/nas/y/FX3_1.MP4", "ordner": "FX3"}]), encoding="utf-8")
    assert T.clips_finden(ch)[0]["path"] == "/nas/x/FX3_9.MP4"          # broll_index vor inventar
    (ac / "broll_index.json").unlink()
    assert T.clips_finden(ch)[0]["path"] == "/nas/y/FX3_1.MP4"


def test_finden_und_abschnitt_werte():
    tele = [{"path": "/nas/a/FX3_1.MP4", "clip": "FX3_1", "haltung": "hand",
             "fenster": [[0.0, 0.3, 1.0, "schwenk_links"], [1.0, 0.3, 1.0, "schwenk_links"], [2.0, 0.05, 0.1, "statisch"]]},
            {"path": "/nas/b/FX3_2.MP4", "clip": "FX3_2"}, {"path": "/nas/c/FX3_2.MP4", "clip": "FX3_2"}]
    assert T.finden(tele, "/nas/a/FX3_1.MP4")["clip"] == "FX3_1"
    assert T.finden(tele, "/ssd/a/FX3_1.MP4")["clip"] == "FX3_1"          # gleicher Dateiname, eindeutig
    assert T.finden(tele, "/ssd/FX3_2.MP4") is None                       # mehrdeutig
    assert T.finden(tele, "/nas/FX3_3.MP4") is None
    assert T.abschnitt_werte(tele[0], 0.0, 2.0) == {"bewegungsart": "schwenk_links", "haltung": "hand"}
    assert T.abschnitt_werte(tele[0], 2.5, 4.0) == {"bewegungsart": "statisch", "haltung": "hand"}
    assert T.abschnitt_werte(tele[1], 0.0, 1.0) == {"bewegungsart": None, "haltung": None}


@pytest.mark.parametrize("rec,von,bis,erwartet,grund", [
    (None, 0, 2, True, "keine Telemetrie"),
    ({"quelle": "keine", "fehler": None}, 0, 2, True, "keine Telemetrie"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "stativ", "wackeln": 0.0,
      "fenster": [[0.0, 0.0, 0.0, "statisch"]]}, 0, 2, False, "Stativ"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "gimbal", "wackeln": 0.05,
      "fenster": [[0.0, 0.05, 1.0, "fahrt"]]}, 0, 2, False, "Gimbal"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "hand", "wackeln": 0.4,
      "fenster": [[0.0, 0.4, 1.0, "fahrt"], [1.0, 0.1, 1.0, "fahrt"]]}, 0.0, 1.0, True, "Hand, wackeln 0,40"),
    ({"quelle": "rtmd", "fehler": None, "haltung": "hand", "wackeln": 0.4,
      "fenster": [[0.0, 0.4, 1.0, "fahrt"], [1.0, 0.1, 1.0, "fahrt"]]}, 2.5, 3.0, False, "Hand, aber ruhig"),
    ({"quelle": "optisch", "fehler": None, "haltung": "hand", "wackeln": 0.9, "fenster": [],
      "path": "/nas/Avata/DJI_0005_D_stabilized.mov"}, 0, 2, False, "bereits stabilisiert"),
])
def test_stabil_vorschlag(rec, von, bis, erwartet, grund):
    stabil, text = T.stabil_vorschlag(von, bis, rec, CFG)
    assert stabil is erwartet and grund in text


def test_stabil_vorschlag_stabilized_ohne_telemetrie():
    stabil, text = T.stabil_vorschlag(0, 2, None, CFG, path="/ssd/Avata/DJI_0006_D_stabilized.mov")
    assert stabil is False and "bereits stabilisiert" in text
    assert T.stabil_vorschlag(0, 2, None, CFG, path="/ssd/FX3/FX3_0001.MP4")[0] is True


# --- Fix-Runde 1 (Task 9): genutzter_quellbereich_s skaliert den Quellbereich bei 50 % korrekt mit clip_fps ---------

@pytest.mark.parametrize("clip_fps,langsam,erwartet", [
    (25.0, False, (4.0, 6.0)),                  # 25p/100 %: Quelldauer = Timeline-Dauer (2,0 s)
    (50.0, False, (2.0, 4.0)),                  # 50p/100 %: Quelldauer bleibt 2,0 s (fps-unabhängig)
    (50.0, True, (2.0, 3.0)),                   # 50p/50 %: halbe Quelldauer (1,0 s)
    (60.0, True, (100 / 60, 160 / 60)),          # 60p/50 %: 1,0 s, aber mit faktor 2,4 skaliert
    (100.0, True, (1.0, 2.0)),                  # 100p/50 %: 1,0 s
])
def test_genutzter_quellbereich_s(clip_fps, langsam, erwartet):
    """Quellbereich (s), den n_f=50 Timeline-Frames ab src_in_f=100 bei 100 %/50 % Tempo nutzen — vorher wurde bei
    50 % nicht mit clip_fps skaliert (zu kurzer Bereich bei allem außer 50p, Review-Befund Task 9)."""
    von, bis = T.genutzter_quellbereich_s(100, 50, clip_fps, langsam)
    assert von == pytest.approx(erwartet[0]) and bis == pytest.approx(erwartet[1])


# --- Fix-Runde 1: Cache-Robustheit (F2), Dubletten (F3), Fehler brechen den Lauf nie ab (F4) --------------------------

def test_clip_mit_cache_kaputte_datei_wird_neu_gemessen(monkeypatch, basis_charge, tmp_path):
    """F2a: eine unlesbare/kaputte Cache-Datei ist ein Cache-Fehlschlag — neu messen statt abbrechen."""
    ac = basis_charge / "_intern" / "autocut"
    (ac / T.CACHE_DIR).mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    clip = tmp_path / "FX3_0020.MP4"
    clip.write_bytes(b"x")
    cache = ac / T.CACHE_DIR / f"{T.fingerprint(clip)}.json"
    cache.write_text("{kaputt", encoding="utf-8")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    rng = np.random.default_rng(11)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (30, 1, 1)))
    rec, aus_cache = T.clip_mit_cache(ch, clip, CFG)
    assert aus_cache is False and rec["quelle"] == "optisch" and rec["fehler"] is None
    neu = json.loads(cache.read_text(encoding="utf-8"))
    assert isinstance(neu, dict) and neu["quelle"] == "optisch"
    assert list(cache.parent.glob("*.part")) == []


def test_clip_mit_cache_datensatz_mit_fehler_wird_neu_gemessen(monkeypatch, basis_charge, tmp_path):
    """F2b: ein gecachter Datensatz mit fehler gilt als veraltet — neu messen statt den alten Fehler zurückgeben."""
    ac = basis_charge / "_intern" / "autocut"
    (ac / T.CACHE_DIR).mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    clip = tmp_path / "FX3_0021.MP4"
    clip.write_bytes(b"x")
    fp = T.fingerprint(clip)
    cache = ac / T.CACHE_DIR / f"{fp}.json"
    cache.write_text(json.dumps({"path": str(clip), "quelle": "optisch", "fehler": "NAS-Aussetzer",
                                 "fingerprint": fp, "schaerfe_p10": None}), encoding="utf-8")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    rng = np.random.default_rng(12)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (30, 1, 1)))
    rec, aus_cache = T.clip_mit_cache(ch, clip, CFG)
    assert aus_cache is False and rec["fehler"] is None and rec["quelle"] == "optisch"


def test_telemetrie_charge_dedupliziert_pfade_vor_limit(basis_charge, tmp_path, monkeypatch):
    """F3: doppelte Pfade werden vor limit entfernt (erster Eintrag gewinnt, samt ordner)."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    a = tmp_path / "FX3_A.MP4"
    a.write_bytes(b"x")
    b = tmp_path / "FX3_B.MP4"
    b.write_bytes(b"x")
    calls: list[str] = []

    def fake(ch_, path, cfg, force=False, ohne_optisch=False, schaerfe=False):
        calls.append(str(path))
        return T._leer(Path(path), "FX3", None), False

    monkeypatch.setattr(T, "clip_mit_cache", fake)
    clips = [{"path": str(a), "ordner": "Erster"}, {"path": str(a), "ordner": "Zweiter"}, {"path": str(b), "ordner": "B"}]
    out = T.telemetrie_charge(ch, clips, CFG, melden=lambda *a, **k: None)
    assert set(calls) == {str(a), str(b)} and len(calls) == 2
    assert out["gemessen"] == 2 and len(out["clips"]) == 2
    rec_a = next(c for c in out["clips"] if c["path"] == str(a))
    assert rec_a["ordner"] == "Erster"

    calls.clear()
    out2 = T.telemetrie_charge(ch, clips, CFG, limit=1, melden=lambda *a, **k: None)
    assert calls == [str(a)] and out2["gemessen"] == 1 and len(out2["clips"]) == 1
    assert out2["clips"][0]["path"] == str(a)


def test_telemetrie_charge_haelt_bei_unerwarteten_fehlern_durch(monkeypatch, basis_charge, tmp_path):
    """F4: ein Nicht-AutoCutError (z. B. ValueError) und ein fehlender Pfad brechen den Lauf nicht ab — beide
    bekommen einen Fehler-Eintrag in telemetrie.json, der gültige Clip daneben wird normal gemessen."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    gut = tmp_path / "FX3_0030.MP4"
    gut.write_bytes(b"x")
    kaputt = tmp_path / "FX3_0031.MP4"
    kaputt.write_bytes(b"x")
    fehlt = tmp_path / "FX3_0032.MP4"
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    rng = np.random.default_rng(13)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)

    def graustufen_fake(p, fps, breite, hoehe):
        if Path(p).name == kaputt.name:
            raise ValueError("Datenspur unlesbar")
        return np.tile(bild, (30, 1, 1))

    monkeypatch.setattr(T, "graustufen", graustufen_fake)
    clips = [{"path": str(gut), "ordner": "x"}, {"path": str(kaputt), "ordner": "x"}, {"path": str(fehlt), "ordner": "x"}]
    out = T.telemetrie_charge(ch, clips, CFG, melden=lambda *a, **k: None)
    assert len(out["clips"]) == 3 and len(out["fehler"]) == 2
    tele = T.laden(ac)
    assert len(tele) == 3
    rec_gut = next(r for r in tele if r["path"] == str(gut))
    assert rec_gut["fehler"] is None and rec_gut["quelle"] == "optisch"
    rec_kaputt = next(r for r in tele if r["path"] == str(kaputt))
    assert rec_kaputt["fehler"] and "ValueError" in rec_kaputt["fehler"] and rec_kaputt["kamera"] == "FX3"
    rec_fehlt = next(r for r in tele if r["path"] == str(fehlt))
    assert rec_fehlt["fehler"] and "nicht gefunden" in rec_fehlt["fehler"]
    assert any("ValueError" in f for f in out["fehler"]) and any("nicht gefunden" in f for f in out["fehler"])


def test_telemetrie_charge_uebersteht_sidecar_modell_fehler_im_fallback(monkeypatch, basis_charge, tmp_path):
    """Fix-Runde 2: der Fallback-Datensatz im except-Handler darf sidecar_modell nicht erneut aufrufen — ein
    OSError dort (Rechte-Fehler auf dem Sidecar-XML) darf den Lauf nicht abbrechen (genau der F4-Fehler)."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    gut = tmp_path / "FX3_0040.MP4"
    gut.write_bytes(b"x")
    kaputt = tmp_path / "FX3_0041.MP4"
    kaputt.write_bytes(b"x")
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    rng = np.random.default_rng(14)
    bild = (rng.random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (30, 1, 1)))

    def sidecar_fake(p):
        if Path(p).name == kaputt.name:
            raise PermissionError("Keine Rechte auf FX3_0041M01.XML")
        return None

    monkeypatch.setattr(T, "sidecar_modell", sidecar_fake)
    clips = [{"path": str(gut), "ordner": "x"}, {"path": str(kaputt), "ordner": "x"}]
    out = T.telemetrie_charge(ch, clips, CFG, melden=lambda *a, **k: None)
    assert len(out["clips"]) == 2 and len(out["fehler"]) == 1
    tele = T.laden(ac)
    rec_gut = next(r for r in tele if r["path"] == str(gut))
    assert rec_gut["fehler"] is None and rec_gut["quelle"] == "optisch"
    rec_kaputt = next(r for r in tele if r["path"] == str(kaputt))
    assert rec_kaputt["fehler"] and "PermissionError" in rec_kaputt["fehler"] and rec_kaputt["kamera"] == "FX3"
    assert any("PermissionError" in f for f in out["fehler"])


# --- Final Review (21.09.2026): Config-Hash im Cache (I1), Pfad bei Cache-Treffer (T4), IMU-Rate (M1), laden (M9) --------

def _optisch_fakes(monkeypatch, seed: int = 20) -> None:
    """ffprobe/Datenspur/Frames für einen optischen Clip ohne Datenspur (30 gleiche Zufallsbilder → stativ)."""
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: b"")
    bild = (np.random.default_rng(seed).random((270, 480)) * 255).astype(np.uint8)
    monkeypatch.setattr(T, "graustufen", lambda p, fps, breite, hoehe: np.tile(bild, (30, 1, 1)))


def test_config_hash_ohne_parallel():
    h = T.config_hash(CFG)
    assert len(h) == 12 and all(c in "0123456789abcdef" for c in h)
    assert T.config_hash({**CFG, "parallel": 8}) == h                          # parallel ändert keinen Messwert
    assert T.config_hash(dict(reversed(list(CFG.items())))) == h                # Reihenfolge der Schlüssel egal
    assert T.config_hash({**CFG, "ruhig_max_px": 0.2}) != h
    assert T.config_hash({**CFG, "px_faktor": {"FX3": 0.6, "a7IV": 1.0}}) != h
    leer = T._leer(Path("/nas/FX3_1.MP4"), "FX3", None)
    assert "config_hash" in leer and leer["config_hash"] is None and "fenster_s" in leer and leer["fenster_s"] is None


def test_clip_mit_cache_misst_nach_config_aenderung_neu(monkeypatch, basis_charge, tmp_path):
    """I1: haltung, bewegungsart, Klassen, wackeln × px_faktor, ruhige_fenster und Fensterlänge hängen an der Config zum
    Messzeitpunkt — ein gecachter Datensatz mit fehlendem oder anderem config_hash gilt als veraltet."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    clip = tmp_path / "DJI_0060.MOV"
    clip.write_bytes(b"x")
    _optisch_fakes(monkeypatch)
    rec, aus_cache = T.clip_mit_cache(ch, clip, CFG)
    assert aus_cache is False and rec["config_hash"] == T.config_hash(CFG) and rec["fenster_s"] == 2.0
    assert T.clip_mit_cache(ch, clip, {**CFG, "parallel": 4})[1] is True        # nur parallel geändert: Cache-Treffer
    cfg3 = {**CFG, "fenster_s": 3.0}
    neu, aus_cache = T.clip_mit_cache(ch, clip, cfg3)
    assert aus_cache is False and neu["fenster_s"] == 3.0 and neu["config_hash"] == T.config_hash(cfg3)
    assert T.clip_mit_cache(ch, clip, cfg3)[1] is True
    cache = ac / T.CACHE_DIR / f"{T.fingerprint(clip)}.json"
    alt = json.loads(cache.read_text(encoding="utf-8"))
    del alt["config_hash"]                                                         # Datensatz von vor dem Fix
    cache.write_text(json.dumps(alt), encoding="utf-8")
    assert T.clip_mit_cache(ch, clip, cfg3)[1] is False


def test_fensterlaenge_kommt_aus_dem_datensatz():
    """I1: Fenster, die mit fenster_s 6,0 gebaut wurden, werden auch mit 6,0 ausgewertet — nicht mit dem übergebenen
    Wert der aktuellen Config (2,0). Abschnitt 2–4 s: mit 2,0 zählen die Fenster ab 1/2/3 s, mit 6,0 die ab 0/1 s."""
    rec = {"quelle": "rtmd", "fehler": None, "haltung": "hand", "wackeln": 0.3, "fenster_s": 6.0,
           "fenster": [[0.0, 0.02, 0.1, "statisch"], [1.0, 0.02, 0.1, "statisch"], [2.0, 0.4, 1.0, "schwenk_links"],
                       [3.0, 0.4, 1.0, "schwenk_links"], [4.0, 0.4, 1.0, "schwenk_links"], [5.0, 0.4, 1.0, "schwenk_links"]]}
    assert T.abschnitt_werte(rec, 2.0, 4.0, 2.0)["bewegungsart"] == "statisch"
    stabil, grund = T.stabil_vorschlag(2.0, 4.0, rec, CFG)                        # CFG fenster_s 2,0
    assert stabil is False and "Hand, aber ruhig" in grund
    ohne = {k: v for k, v in rec.items() if k != "fenster_s"}                     # Altbestand: übergebener Wert gilt
    assert T.abschnitt_werte(ohne, 2.0, 4.0, 2.0)["bewegungsart"] == "schwenk_links"
    assert T.stabil_vorschlag(2.0, 4.0, ohne, CFG)[0] is True


def test_clip_mit_cache_treffer_traegt_den_aktuellen_pfad(monkeypatch, basis_charge, tmp_path):
    """T4: nach einem Umzug NAS → SSD (gleicher Fingerprint: Name, Größe, mtime) trägt der Cache-Treffer den neuen Pfad —
    sonst schriebe telemetrie.json alte Pfade, und der Dateinamen-Rückfall in finden versagt bei DJI_0001 u. ä."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    nas, ssd = tmp_path / "nas" / "Mavic" / "DJI_0001.MOV", tmp_path / "ssd" / "Mavic" / "DJI_0001.MOV"
    for p in (nas, ssd):
        p.parent.mkdir(parents=True)
        p.write_bytes(b"x")
    st = nas.stat()
    os.utime(ssd, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert T.fingerprint(nas) == T.fingerprint(ssd)
    _optisch_fakes(monkeypatch)
    assert T.clip_mit_cache(ch, nas, CFG)[0]["path"] == str(nas)
    rec, aus_cache = T.clip_mit_cache(ch, ssd, CFG)
    assert aus_cache is True and rec["path"] == str(ssd) and rec["clip"] == "DJI_0001"


def test_gyro_je_frame_mit_imu_rate_5994p():
    """M1: bei 59,94p liefert die Kamera 33–34 Proben je Sample; round(33 · 59,94 / 25) = 79 driftet. Mit der IMU-Rate
    aus Tag 0xE435 (2000 Hz) sind es genau 80 Proben je 25-fps-Frame."""
    g = np.vstack([np.tile([[1.0, 2.0, 3.0]], (80, 1)), np.tile([[2.0, 4.0, 6.0]], (80, 1))])
    m = T.gyro_je_frame(g, 33, 59.94, imu_hz=2000.0)
    assert m.shape == (2, 3) and np.allclose(m[0], [1, 2, 3]) and np.allclose(m[1], [2, 4, 6])
    assert not np.allclose(T.gyro_je_frame(g, 33, 59.94)[1], [2, 4, 6])           # ohne Rate: 79 je Frame
    assert T.gyro_je_frame(g, 80, 25.0).shape == (2, 3)                           # bisheriger Aufruf unverändert


def test_clip_messen_und_kalibrierung_geben_die_imu_rate_weiter(monkeypatch, tmp_path):
    """M1: beide Aufrufer übergeben imu_hz aus der Datenspur an gyro_je_frame."""
    from niro_autocut import telemetrie_kalibrierung as K
    clip = tmp_path / "FX3_0061.MP4"
    clip.write_bytes(b"x")
    gesehen: list = []

    def spion(werte, proben_je_sample, fps, ziel_fps=T.ZIEL_FPS, imu_hz=None):
        gesehen.append(imu_hz)
        return np.zeros((len(werte) // 80, 3))                                    # 25p-Puffer: 80 Proben je Frame

    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100, gyro_y=10.0))
    monkeypatch.setattr(T, "gyro_je_frame", spion)
    assert T.clip_messen(clip, CFG)["quelle"] == "rtmd"
    monkeypatch.setattr(K, "ffprobe", lambda p: _info(str(p)))
    monkeypatch.setattr(K, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100, gyro_y=10.0))
    monkeypatch.setattr(K, "graustufen", lambda p, fps, von, dauer, breite, hoehe: np.zeros((101, hoehe, breite), np.uint8))
    monkeypatch.setattr(K, "gyro_je_frame", spion)
    assert K.clip_kalibrieren(clip, CFG, 0.0) is not None
    assert gesehen == [2000.0, 2000.0]


def test_laden_kaputte_telemetrie_json_liefert_leer(tmp_path):
    """M9: Telemetrie ist überall optional — eine kaputte telemetrie.json darf weder die 6d-Vorlage beim Import noch
    Stufe 2b abbrechen; ohne Daten gelten die bisherigen Standards."""
    datei = tmp_path / "telemetrie.json"
    for inhalt in (b"{kaputt", b"\xff\xfe\x00", b"42", b'"text"'):
        datei.write_bytes(inhalt)
        assert T.laden(tmp_path) == []
    datei.write_text(json.dumps([{"path": "/nas/a.MP4"}, 3, None]), encoding="utf-8")
    assert T.laden(tmp_path) == [{"path": "/nas/a.MP4"}]                           # nur Datensätze (dicts)
    datei.unlink()
    datei.mkdir()                                                                  # OSError beim Lesen
    assert T.laden(tmp_path) == []


# --- Final Review (21.09.2026): Teil-Läufe kürzen telemetrie.json nicht (I3) --------------------------------------------

def _fake_messung(monkeypatch, calls: list[str] | None = None) -> None:
    """clip_mit_cache ersetzt: Datensatz „neu gemessen" mit Fingerprint aus dem Dateinamen."""
    def fake(ch_, path, cfg, force=False, ohne_optisch=False, schaerfe=False):
        if calls is not None:
            calls.append(str(path))
        rec = T._leer(Path(path), "FX3", None)
        rec.update(quelle="optisch", fingerprint="fp-" + Path(path).stem, neu=True)
        return rec, False

    monkeypatch.setattr(T, "clip_mit_cache", fake)


def test_telemetrie_charge_teillauf_ergaenzt_telemetrie_json(monkeypatch, basis_charge, tmp_path):
    """I3: --limit 2 nach einem Volllauf darf telemetrie.json nicht auf 2 Einträge kürzen. Reihenfolge: Clip-Liste des
    Laufs (dedupliziert), dann die übrigen alten Einträge in alter Reihenfolge; Rückgabe clips = nur dieser Lauf."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    p = {n: tmp_path / f"FX3_{n}.MP4" for n in "ABCD"}
    for f in p.values():
        f.write_bytes(b"x")
    alt = [{"path": "/nas/alt/FX3_X.MP4", "clip": "FX3_X", "quelle": "rtmd", "fingerprint": "fp-X"},
           {"path": str(p["C"]), "clip": "FX3_C", "quelle": "rtmd", "fingerprint": "fp-C"},
           {"path": str(p["A"]), "clip": "FX3_A", "quelle": "rtmd", "fingerprint": "fp-A-alt"}]
    (ac / "telemetrie.json").write_text(json.dumps(alt), encoding="utf-8")
    calls: list[str] = []
    _fake_messung(monkeypatch, calls)
    clips = [{"path": str(p[n]), "ordner": o} for n, o in (("A", "x"), ("A", "y"), ("B", "x"), ("C", "x"), ("D", "x"))]
    out = T.telemetrie_charge(ch, clips, CFG, limit=2, melden=lambda *a, **k: None)
    assert sorted(calls) == sorted([str(p["A"]), str(p["B"])])                   # dedupliziert vor limit, parallel
    assert [r["clip"] for r in out["clips"]] == ["FX3_A", "FX3_B"] and out["gemessen"] == 2
    tele = T.laden(ac)
    assert [r["clip"] for r in tele] == ["FX3_A", "FX3_B", "FX3_C", "FX3_X"]      # D: nie gemessen, kein alter Eintrag
    assert tele[0].get("neu") is True and tele[0]["ordner"] == "x"                 # A: Ergebnis dieses Laufs
    assert tele[2].get("neu") is None and tele[2]["quelle"] == "rtmd"             # C: alter Eintrag bleibt
    assert out["gesamt"] == 4


def test_telemetrie_charge_ersetzt_alten_pfad_mit_gleichem_fingerprint(monkeypatch, basis_charge, tmp_path):
    """I3/T4: nach einem Umzug NAS → SSD (gleicher Fingerprint) bleibt der alte NAS-Eintrag nicht zusätzlich stehen —
    sonst zählte der Bericht (aus der ganzen telemetrie.json) den Clip doppelt und finden wäre per Dateiname mehrdeutig."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    ssd = tmp_path / "ssd" / "DJI_0001.MOV"
    ssd.parent.mkdir(parents=True)
    ssd.write_bytes(b"x")
    alt = [{"path": "/nas/Mavic/DJI_0001.MOV", "clip": "DJI_0001", "quelle": "optisch", "fingerprint": "fp-DJI_0001"},
           {"path": "/nas/Mavic/DJI_0002.MOV", "clip": "DJI_0002", "quelle": "optisch", "fingerprint": "fp-DJI_0002"},
           {"path": "/nas/Mavic/kaputt.MOV", "clip": "kaputt", "quelle": "keine", "fehler": "Datei nicht gefunden"}]
    (ac / "telemetrie.json").write_text(json.dumps(alt), encoding="utf-8")
    _fake_messung(monkeypatch)
    out = T.telemetrie_charge(ch, [{"path": str(ssd), "ordner": "Mavic"}], CFG, melden=lambda *a, **k: None)
    tele = T.laden(ac)
    assert [r["path"] for r in tele] == [str(ssd), "/nas/Mavic/DJI_0002.MOV", "/nas/Mavic/kaputt.MOV"]
    assert out["gesamt"] == 3 and len(out["clips"]) == 1


# --- Final Review (21.09.2026): ausgelieferte Konvention gepinnt (M6) ------------------------------------------------------

@pytest.mark.parametrize("achse,erwartet", [(1, "schwenk_links"), (0, "tilt_ab")])
def test_ausgelieferte_konvention_aus_defaults_yaml(achse, erwartet):
    """M6: pinnt die Kalibrierung in defaults.yaml (21.09.2026, Hochzeitszauber): +ω_y → Bildinhalt wandert nach rechts
    (dx > 0) → schwenk_links; +ω_x → Bildinhalt wandert nach oben (dy < 0) → tilt_ab. Die übrigen Tests rechnen mit der
    Test-CFG (Vorzeichen Schwenk −1, Tilt +1, Stand vor der Kalibrierung)."""
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    min_px, stativ_px = T.schwellen_px(36.0, cfg)
    rate = np.zeros((50, 3))
    rate[:, achse] = 10.0                                                         # 10 °/s um die Gyro-Achse
    dxy = T.verschiebung_aus_rate(rate, 36.0, cfg) * float(cfg["px_faktor"]["FX3"])
    assert T.bewegungsart(dxy, cfg, min_px, stativ_px) == erwartet


# --- Zoomfahrten (Spec 2026-09-21, Abschnitt 1) ----------------------------------------------------------------------

def _zoomreihe(*stuecke: tuple[float, float, float], fps: float = 25.0) -> list[float]:
    """KB-Brennweite je Sample aus Stücken (Dauer s, mm von, mm bis), log-linear, auf 0,1 mm gerundet wie die Kamera."""
    werte: list[float] = []
    for dauer, von, bis in stuecke:
        n = int(round(dauer * fps))
        werte += np.exp(np.linspace(math.log(von), math.log(bis), n, endpoint=False)).tolist()
    werte.append(stuecke[-1][2])
    return [round(w, 1) for w in werte]


def _fahrten(kb: list[float], fps: float = 25.0) -> list[dict]:
    return T.zoomfahrten(T.kb_je_frame(kb, None, fps, len(kb)), CFG)


def test_defaults_haben_zoom_schluessel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    for k in ("zoom_min_proz", "zoom_rausch_proz_s", "zoom_schnell_proz_s", "zoom_ruck_max", "zoom_stocken_anteil",
              "zoom_verlauf_hz"):
        assert k in cfg


def test_kb_je_frame_median_raster_und_luecken():
    ausreisser = [50.0] * 10 + [80.0] + [50.0] * 10
    assert np.allclose(T.kb_je_frame(ausreisser, None, 25.0, 21), 50.0)         # Median über 0,2 s (5 Samples)
    reihe50 = _zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36), fps=50.0)  # 301 Samples bei 50p
    k50 = T.kb_je_frame(reihe50, None, 50.0, len(reihe50))
    assert len(k50) == 150 and k50[0] == 24.0 and k50[-1] == 36.0              # 25-fps-Raster
    idx = [i for i in range(len(reihe50)) if i % 3]                             # jedes dritte Sample ohne Brennweite
    luecken = T.kb_je_frame([reihe50[i] for i in idx], idx, 50.0, len(reihe50))
    assert len(luecken) == 150 and float(np.abs(luecken - k50).max()) < 0.5
    assert len(T.kb_je_frame([], [], 25.0, 100)) == 0
    assert np.allclose(T.kb_je_frame([50.0, 50.0], [0, 1, 2], 25.0, 2), 50.0)   # unpassender Index: lückenlos


def test_zoomfahrten_festbrennweite_und_rauschen():
    assert _fahrten([50.0] * 100) == []
    rng = np.random.default_rng(1)
    assert _fahrten((50.0 + 0.1 * rng.integers(0, 2, 200)).round(1).tolist()) == []     # Quantisierung 0,1 mm
    atmen = [round(50.0 * (1 + 0.01 * math.sin(math.pi * k / 25.0)), 1) for k in range(200)]
    assert _fahrten(atmen) == []                                                 # Fokus-Atmen ±1 % < zoom_min_proz


def test_zoomfahrt_langsam_gleichmaessig():
    z = _fahrten(_zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36)))
    assert len(z) == 1 and z[0]["urteil"] == "langsam" and z[0]["ruckartig"] is False
    # ln(36/24) / 4 s = 10,1 % pro s; 0,1-mm-Stufen und Glättung heben die Spitze etwas an
    assert 9.0 < z[0]["tempo_max"] < 13.0 and z[0]["tempo_mittel"] < z[0]["tempo_max"] and z[0]["ruck"] < 0.1
    assert abs(z[0]["von_s"] - 1.0) <= 0.15 and abs(z[0]["bis_s"] - 5.0) <= 0.15
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (24.0, 36.0)


def test_zoomfahrt_schnell():
    z = _fahrten(_zoomreihe((1.0, 24, 24), (0.8, 24, 70), (1.0, 70, 70)))
    # ln(70/24) / 0,8 s = 134 % pro s
    assert len(z) == 1 and z[0]["urteil"] == "schnell" and 120.0 < z[0]["tempo_max"] < 145.0
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (24.0, 70.0) and z[0]["ruckartig"] is False


def test_zoom_ruck_variationskoeffizient_und_stocken():
    # 20 Frames, Kern ohne je 2 Frames: Mittel der 5er-Schritte 6,4 / 4,6 / 10,0 → CV 2,245 / 7,0 = 0,32;
    # |v| fällt im Kern unter 20 % der Spitze (1 < 2) und steigt wieder → Stocken
    ruck, stockt = T.zoom_ruck(np.array([10.0] * 5 + [1.0] * 5 + [10.0] * 10), 0.2)
    assert ruck == pytest.approx(0.32, abs=0.005) and stockt is True
    assert T.zoom_ruck(np.full(20, 10.0), 0.2) == (0.0, False)
    assert T.zoom_ruck(np.linspace(0.0, 10.0, 20), 0.2)[1] is False            # Anlauf ist kein Stocken
    assert T.zoom_ruck(np.array([]), 0.2) == (0.0, False)


def test_zoomfahrt_mit_stocken_ist_ruckartig():
    # 15 % pro s (unter zoom_schnell_proz_s 20), dazwischen 0,2 s Halt: eine Fahrt, Stocken → ruckartig → schnell
    z = _fahrten(_zoomreihe((1.0, 24, 24), (1.0, 24, 27.9), (0.2, 27.9, 27.9), (1.0, 27.9, 32.4), (1.0, 32.4, 32.4)))
    assert len(z) == 1 and z[0]["tempo_max"] < 20.0
    assert z[0]["ruckartig"] is True and z[0]["urteil"] == "schnell"


def test_stop_and_go_unter_0_3_s_ist_eine_fahrt():
    def halt(s: float) -> list[float]:
        return _zoomreihe((1.0, 24, 24), (0.5, 24, 32.4), (s, 32.4, 32.4), (0.5, 32.4, 43.7), (1.0, 43.7, 43.7))
    eine = _fahrten(halt(0.2))
    assert len(eine) == 1 and (eine[0]["von_mm"], eine[0]["bis_mm"]) == (24.0, 43.7) and eine[0]["ruckartig"] is True
    zwei = _fahrten(halt(0.6))
    assert [(z["von_mm"], z["bis_mm"]) for z in zwei] == [(24.0, 32.4), (32.4, 43.7)]


def test_stufiger_sprung_ist_schnell():
    # Klarbild-Zoom der a7 IV schaltet stufig: 50 → 60 mm in zwei Frames (+20 %)
    z = _fahrten(_zoomreihe((1.0, 50, 50), (0.08, 50, 60), (1.0, 60, 60)))
    assert len(z) == 1 and z[0]["urteil"] == "schnell" and z[0]["tempo_max"] > 20.0
    assert (z[0]["von_mm"], z[0]["bis_mm"]) == (50.0, 60.0)


def test_kb_verlauf_kompakt_und_5_hz():
    assert T.kb_verlauf(np.full(100, 50.0), CFG) == [[0.0, 50.0]]
    assert T.kb_verlauf(np.array([50.0, 51.0, 50.4]), CFG) == [[0.0, 50.4]]    # 2 % < zoom_min_proz: Median
    k = T.kb_je_frame(_zoomreihe((1.0, 24, 24), (4.0, 24, 36), (1.0, 36, 36)), None, 25.0, 151)
    v = T.kb_verlauf(k, CFG)
    assert len(v) == 31 and v[:2] == [[0.0, 24.0], [0.2, 24.0]] and v[-1] == [6.0, 36.0]
    assert all(round(b[0] - a[0], 2) == 0.2 for a, b in zip(v, v[1:]))
    assert T.kb_verlauf(np.zeros(0), CFG) == []


def test_zoom_messen():
    assert T.zoom_messen([], [], 25.0, 100, CFG) == {"kb_verlauf": [], "zooms": []}
    assert T.zoom_messen([71.6] * 100, list(range(100)), 25.0, 100, CFG) == {"kb_verlauf": [[0.0, 71.6]], "zooms": []}
    kb = _zoomreihe((1.0, 24, 24), (0.8, 24, 70), (1.0, 70, 70))
    m = T.zoom_messen(kb, list(range(len(kb))), 25.0, len(kb), CFG)
    assert len(m["zooms"]) == 1 and m["zooms"][0]["urteil"] == "schnell" and m["kb_verlauf"][-1][1] == 70.0


def test_ruhige_fenster_ohne_schnelle_zooms():
    zooms = [{"von_s": 2.4, "bis_s": 3.4, "urteil": "schnell"}, {"von_s": 6.0, "bis_s": 9.0, "urteil": "langsam"}]
    # Fenster [t, t + 2): 1, 2 und 3 schneiden den schnellen Zoom, 6 nur den langsamen
    assert T.ruhige_ohne_schnelle_zooms([0.0, 1.0, 2.0, 3.0, 4.0, 6.0], zooms, 2.0) == [0.0, 4.0, 6.0]
    assert T.ruhige_ohne_schnelle_zooms([0.0, 1.0], [], 2.0) == [0.0, 1.0]
    assert T.ruhige_ohne_schnelle_zooms([], zooms, None) == []


def test_clip_messen_zoomfahrt_und_ruhige_fenster(monkeypatch, tmp_path):
    clip = tmp_path / "FX3_0070.MP4"
    clip.write_bytes(b"x")
    kb = _zoomreihe((2.5, 24, 24), (0.8, 24, 70), (1.7, 70, 70))                 # 125 Frames, schneller Zoom ab 2,5 s
    monkeypatch.setattr(T, "ffprobe", lambda p: _info(str(p), dauer=5.0))
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=len(kb), kb=[_kb(x) for x in kb]))
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "rtmd" and rec["zoomfahrt"] is True and len(rec["zooms"]) == 1
    z = rec["zooms"][0]
    assert z["urteil"] == "schnell" and (z["von_mm"], z["bis_mm"]) == (24.0, 70.0) and 2.3 < z["von_s"] < 2.5
    # 5 Hz über 125 Frames: 0,0 … 4,8 s plus der letzte Frame (4,96 s)
    assert len(rec["kb_verlauf"]) == 26 and rec["kb_verlauf"][0] == [0.0, 24.0] and rec["kb_verlauf"][-1] == [4.96, 70.0]
    # Stativ (Gyro 0): alle Fenster ruhig — bis auf die drei, die den schnellen Zoom schneiden (ab 1, 2 und 3 s)
    assert [f[0] for f in rec["fenster"]] == [0.0, 1.0, 2.0, 3.0, 4.0] and rec["ruhige_fenster"] == [0.0, 4.0]


def test_clip_messen_ohne_rtmd_brennweite_ohne_zooms(monkeypatch, tmp_path):
    clip = tmp_path / "DJI_0071.MOV"
    clip.write_bytes(b"x")
    _optisch_fakes(monkeypatch, seed=21)
    rec = T.clip_messen(clip, CFG)
    assert rec["quelle"] == "optisch" and rec["kb_verlauf"] == [] and rec["zooms"] == [] and rec["zoomfahrt"] is False
    fest = tmp_path / "FX3_0072.MP4"
    fest.write_bytes(b"x")
    monkeypatch.setattr(T, "datenspur_lesen", lambda p: _rtmd_puffer(frames=100))
    rec2 = T.clip_messen(fest, CFG)
    assert rec2["kb_verlauf"] == [[0.0, 71.6]] and rec2["zooms"] == [] and rec2["zoomfahrt"] is False


# --- Brennweite im Bereich: kb_am, kb_im_bereich, zooms_im_bereich, 2b-Werte, Texte (Spec 2026-09-21) -------------------

_ZOOM_REC = {"kb_mm": 48.0, "kb_verlauf": [[0.0, 24.0], [1.0, 24.0], [2.0, 48.0], [3.0, 48.0]],
             "zooms": [{"von_s": 1.0, "bis_s": 2.0, "von_mm": 24.0, "bis_mm": 48.0, "tempo_max": 85.2, "tempo_mittel": 69.3,
                        "ruck": 0.1, "ruckartig": False, "urteil": "schnell"},
                       {"von_s": 5.0, "bis_s": 6.0, "von_mm": 48.0, "bis_mm": 50.0, "tempo_max": 4.0, "tempo_mittel": 3.0,
                        "ruck": 0.1, "ruckartig": False, "urteil": "langsam"}]}


def test_kb_am_seiten_raender_und_ohne_verlauf():
    # Spanne 0,5 s auf dem 0,1-s-Raster, linear zwischen den Verlaufspunkten (1 s: 24 mm, 2 s: 48 mm)
    assert T.kb_am(_ZOOM_REC, 2.0, seite="ende") == 42.0           # 1,5–2,0 s: 36 … 48 → Median (40,8 + 43,2) / 2
    assert T.kb_am(_ZOOM_REC, 2.0, seite="anfang") == 48.0         # 2,0–2,5 s
    assert T.kb_am(_ZOOM_REC, 1.0, seite="ende") == 24.0
    assert T.kb_am(_ZOOM_REC, 1.0) == 24.6                         # mittig 0,75–1,25 s: 24, 24, 24, 25,2, 27,6, 30
    assert T.kb_am(_ZOOM_REC, 0.0, seite="ende") == 24.0 and T.kb_am(_ZOOM_REC, 10.0, seite="anfang") == 48.0
    assert T.kb_am({"kb_verlauf": [[0.0, 71.6]]}, 3.0, seite="ende") == 71.6    # Festbrennweite: ein Eintrag
    assert T.kb_am(None, 1.0) is None and T.kb_am({"kb_verlauf": []}, 1.0) is None
    assert T.kb_am({"kb_mm": 50.0}, 1.0) is None                   # Datensatz von vor der Umstellung: unbekannt


def test_kb_im_bereich_und_zooms_im_bereich():
    assert T.kb_im_bereich(_ZOOM_REC, 0.0, 3.0) == 36.0            # 11 × 24, 26,4 … 45,6, 11 × 48 → Mitte 36
    assert T.kb_im_bereich(_ZOOM_REC, 2.0, 3.0) == 48.0 and T.kb_im_bereich({}, 0.0, 1.0) is None
    schnell, langsam = _ZOOM_REC["zooms"]
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 1.5) == [schnell]
    assert T.zooms_im_bereich(_ZOOM_REC, 2.0, 5.0) == []           # Berühren zählt nicht
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 10.0) == [schnell]
    assert T.zooms_im_bereich(_ZOOM_REC, 0.0, 10.0, nur_schnelle=False) == [schnell, langsam]
    assert T.zooms_im_bereich({"kb_mm": 50.0}, 0.0, 10.0) == [] and T.zooms_im_bereich(None, 0.0, 1.0) == []


def test_abschnitt_brennweite_und_brennweite_text():
    assert T.abschnitt_brennweite(_ZOOM_REC, 0.0, 1.5) == {"brennweite_mm": 24.0, "zoom": "schnell"}
    assert T.abschnitt_brennweite(_ZOOM_REC, 5.5, 6.0) == {"brennweite_mm": 48.0, "zoom": "langsam"}
    assert T.abschnitt_brennweite(_ZOOM_REC, 3.0, 4.0) == {"brennweite_mm": 48.0, "zoom": "keiner"}
    assert T.abschnitt_brennweite({"kb_mm": 50.0}, 0.0, 1.0) == {"brennweite_mm": None, "zoom": None}
    assert T.brennweite_text(_ZOOM_REC) == "KB 24–48 mm, schneller Zoom"
    langsam = {**_ZOOM_REC, "zooms": _ZOOM_REC["zooms"][1:]}
    assert T.brennweite_text(langsam) == "KB 24–48 mm, langsamer Zoom"
    assert T.brennweite_text({"kb_mm": 71.6, "kb_verlauf": [[0.0, 71.6]], "zooms": []}) == "KB 71,6 mm"
    assert T.brennweite_text({"kb_mm": 50.0}) == "KB 50 mm"         # Altdatensatz ohne Verlauf
    assert T.brennweite_text({"kb_mm": None}) is None and T.brennweite_text(None) is None


def test_zoom_hinweise():
    rec = {"zooms": [{"von_s": 2.4, "bis_s": 3.1, "von_mm": 24.0, "bis_mm": 70.0, "tempo_max": 85.2, "tempo_mittel": 60.0,
                      "ruck": 0.2, "ruckartig": False, "urteil": "schnell"}]}
    assert T.zoom_hinweise("S07", rec, 2.0, 4.0) == ["S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 85 %/s)"]
    ruck = {"zooms": [{**rec["zooms"][0], "tempo_max": 14.6, "ruckartig": True}]}
    assert T.zoom_hinweise("S08", ruck, 0.0, 10.0) == ["S08: schneller Zoom 2,4–3,1 s (24 → 70 mm, 15 %/s, ruckartig)"]
    assert T.zoom_hinweise("S07", rec, 3.1, 5.0) == [] and T.zoom_hinweise("S07", None, 0.0, 1.0) == []
    # 6d-Zeitlupe (50 %): sichtbares Tempo halb so hoch — 85 → 43 %/s bleibt schnell (CFG: 20 %/s), 30 → 15 %/s nicht
    assert T.zoom_hinweise("S07", rec, 2.0, 4.0, tempo_faktor=0.5, cfg=CFG) == [
        "S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 43 %/s sichtbar bei 50 %)"]
    maessig = {"zooms": [{**rec["zooms"][0], "tempo_max": 30.0}]}
    assert T.zoom_hinweise("S09", maessig, 2.0, 4.0, tempo_faktor=0.5, cfg=CFG) == []
    # ruckartig bleibt schnell, egal wie langsam
    assert T.zoom_hinweise("S08", ruck, 0.0, 10.0, tempo_faktor=0.5, cfg=CFG) == [
        "S08: schneller Zoom 2,4–3,1 s (24 → 70 mm, 7 %/s sichtbar bei 50 %, ruckartig)"]
    # ohne cfg bleibt der Hinweis (Schwelle unbekannt → lieber melden)
    assert len(T.zoom_hinweise("S09", maessig, 2.0, 4.0, tempo_faktor=0.5)) == 1


# --- Brennweitenfolge: gleiche Brennweite, digitaler Zoom (Spec 2026-09-21, Abschnitt 2) -----------

def test_defaults_haben_brennweitenregel():
    cfg = load_config(Path("/nirgendwo"))["telemetrie"]
    assert cfg["brennweite_gleich_max"] == 0.20 and cfg["digitalzoom_faktor"] == 1.25 and cfg["digitalzoom_max"] == 1.5
    assert "brennweite_klassen_kb" not in cfg


@pytest.mark.parametrize("a,b,abstand,gleich", [
    (50, 55, 0.1, True), (24, 28, 0.1667, True), (35, 50, 0.4286, False), (70, 85, 0.2143, False),
    (50, 60, 0.2, False),                   # genau 20 %: nicht „unter 20 %"
    (50, 59.9, 0.198, True), (55, 50, 0.1, True),
])
def test_brennweite_abstand_und_gleich(a, b, abstand, gleich):
    assert T.brennweite_abstand(a, b) == abstand and T.gleiche_brennweite(a, b, 0.20) is gleich


@pytest.mark.parametrize("args,kw,erwartet", [
    ((50, 52, 1.0, 1.0), {}, ("b", 1.25)),                         # B länger: 1,25 reicht
    ((52, 50, 1.0, 1.0), {}, ("a", 1.25)),                         # A länger
    ((52, 50, 1.0, 1.0), {"a_erlaubt": False}, ("b", 1.3)),        # kürzerer mit Aufschlag: 1,25 × 52 / 50
    ((50, 52, 1.0, 1.0), {"b_erlaubt": False}, ("a", 1.3)),
    ((50, 50, 1.0, 1.0), {}, ("b", 1.25)),                         # Gleichstand → B
    ((50, 52, 1.0, 1.1), {}, ("b", 1.375)),                        # vorhandener Zoom: 1,1 × 1,25 (A bräuchte 1,43)
    ((50, 52, 1.0, 1.0), {"a_erlaubt": False, "b_erlaubt": False}, None),
])
def test_digitalzoom(args, kw, erwartet):
    assert T.digitalzoom(*args, CFG, **kw) == erwartet


def test_digitalzoom_grenze():
    assert T.digitalzoom(50, 52, 1.0, 1.1, {**CFG, "digitalzoom_max": 1.3}) is None     # 1,375 und 1,43 > 1,3
    assert T.digitalzoom(50, 52, 1.0, 1.0, {**CFG, "digitalzoom_max": 1.25}) == ("b", 1.25)   # Grenze zählt mit


def _shot(sid: str, rec_in: int, rec_out: int, kb_anfang: float | None, kb_ende: float | None,
          zoom: float | None = None) -> dict:
    return {"id": sid, "rec_in": rec_in, "rec_out": rec_out, "kb_anfang": kb_anfang, "kb_ende": kb_ende,
            "zoom_erzwungen": zoom}


def _zooms(folge: list[dict]) -> list[float]:
    return [e["zoom"] for e in folge]


def test_brennweitenfolge_automatik_verschieden_luecke_unbekannt():
    f = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0)], CFG)
    assert _zooms(f) == [1.0, 1.25] and f[0]["hinweis"] is None and f[1]["fehler"] is None
    assert f[1]["hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,25× auf S02"
    verschieden = T.brennweitenfolge([_shot("S01", 0, 50, 24.0, 24.0), _shot("S02", 50, 100, 50.0, 50.0)], CFG)
    assert _zooms(verschieden) == [1.0, 1.0] and verschieden[1]["hinweis"] is None
    luecke = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 60, 110, 50.0, 50.0)], CFG)
    assert _zooms(luecke) == [1.0, 1.0] and luecke[1]["hinweis"] is None
    unbekannt = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, None, None),
                                    _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(unbekannt) == [1.0, 1.0, 1.0] and all(e["hinweis"] is None for e in unbekannt)
    # Eingabe nicht in Record-Reihenfolge: geprüft wird nach rec_in, Ausgabe bleibt in Eingabe-Reihenfolge
    umgekehrt = T.brennweitenfolge([_shot("S02", 50, 100, 52.0, 52.0), _shot("S01", 0, 50, 50.0, 50.0)], CFG)
    assert [e["id"] for e in umgekehrt] == ["S02", "S01"] and _zooms(umgekehrt) == [1.25, 1.0]
    assert T.brennweitenfolge([], CFG) == []


def test_brennweitenfolge_spalte_zoom_erzwingt_und_verbietet():
    verbietet_b = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0, 1.0)], CFG)
    assert _zooms(verbietet_b) == [1.3, 1.0]                              # nur A: 1,25 × 52 / 50
    assert verbietet_b[1]["hinweis"] == "S02: 50 → 52 mm am Schnitt, Zoom 1,3× auf S01"
    beide = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0, 1.0), _shot("S02", 50, 100, 52.0, 52.0, 1.0)], CFG)
    assert _zooms(beide) == [1.0, 1.0]
    assert beide[1]["hinweis"] == "S02: gleiche Brennweite wie S01 (50/52 mm), Zoom nicht möglich (Spalte zoom)"
    erzwingt = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 52.0, 52.0, 1.4)], CFG)
    assert _zooms(erzwingt) == [1.0, 1.4] and erzwingt[1]["hinweis"] is None      # 50 / 72,8 mm: verschieden
    zu_gross = T.brennweitenfolge([_shot("S01", 0, 50, 24.0, 24.0, 1.6), _shot("S02", 60, 90, 50.0, 50.0, 0.9)], CFG)
    assert zu_gross[0]["fehler"] == "S01: Spalte zoom 1,6× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"
    assert zu_gross[1]["fehler"] == "S02: Spalte zoom 0,9× außerhalb 1,0–1,5× (telemetrie.digitalzoom_max)"


def test_brennweitenfolge_kette_a_schon_gezoomt_nur_b():
    # Faktor 1,1: S02 bekommt 1,1 (Gleichstand → B); S02 → S03: 52,3 × 1,1 = 57,53 mm gegen 50 mm = gleich (15 %).
    # A (S02) hat schon einen Zoom → nur B: 1,1 × 57,53 / 50 = 1,266 (A allein bräuchte nur 1,1 × 1,1 = 1,21)
    cfg = {**CFG, "digitalzoom_faktor": 1.1}
    f = T.brennweitenfolge([_shot("S01", 0, 50, 50.0, 50.0), _shot("S02", 50, 100, 50.0, 52.3),
                            _shot("S03", 100, 150, 50.0, 50.0)], cfg)
    assert _zooms(f) == [1.0, 1.1, 1.266]
    assert f[2]["hinweis"] == "S03: 57,5 → 50 mm am Schnitt, Zoom 1,266× auf S03"


def test_brennweitenfolge_kein_rueckfall_zum_vorgaenger():
    # S01 → S02: 62,5 / 50 mm = 25 %, verschieden. S02 → S03: 52 / 50 = gleich; A (S02) wäre billiger (1,25 < 1,3),
    # 50 × 1,25 = 62,5 mm machte aber den Schnitt S01 → S02 wieder gleich → nur B: 1,25 × 52 / 50 = 1,3
    f = T.brennweitenfolge([_shot("S01", 0, 50, 62.5, 62.5), _shot("S02", 50, 100, 50.0, 52.0),
                            _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(f) == [1.0, 1.0, 1.3] and f[2]["hinweis"] == "S03: 52 → 50 mm am Schnitt, Zoom 1,3× auf S03"
    ohne_vorgaenger = T.brennweitenfolge([_shot("S02", 50, 100, 50.0, 52.0), _shot("S03", 100, 150, 50.0, 50.0)], CFG)
    assert _zooms(ohne_vorgaenger) == [1.25, 1.0]                          # ohne S01 darf A den Zoom tragen


def test_brennweitenfolge_zoom_nicht_moeglich():
    f = T.brennweitenfolge([_shot("S11", 0, 50, 50.0, 50.0), _shot("S12", 50, 100, 52.0, 52.0)],
                           {**CFG, "digitalzoom_max": 1.2})
    assert _zooms(f) == [1.0, 1.0]
    assert f[1]["hinweis"] == "S12: gleiche Brennweite wie S11 (50/52 mm), Zoom nicht möglich (1,2×-Grenze)"
