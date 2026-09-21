"""telemetrie.py — Kennzahlen (synthetische Verläufe), Clip-Messung, Cache, Charge-Lauf, 2b/6d-Helfer (Task 4)."""
from __future__ import annotations

import json
import math
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
       "hand_hf_anteil_min": 0.35, "brennweite_klassen_kb": [30, 60], "pitch_klassen_grad": [-60, -8, 8],
       "achsen": {"schwenk": 1, "tilt": 0}, "vorzeichen": {"schwenk": -1, "tilt": 1, "pitch": 1},
       "px_faktor": {"FX3": 1.0, "a7IV": 1.0}, "optisch_fuer": [], "optisch_breite": 480, "parallel": 2}


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
    brennweiten = [T.brennweitenklasse(k, [30, 60]) for k in (24, 30, 50, 60, 71.6, 283.8)]
    assert brennweiten == ["weit", "normal", "normal", "normal", "tele", "tele"]
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


def _rtmd_puffer(frames: int = 100, proben: int = 80, gyro_y: float = 0.0, acc=(0.0, 1.15, 0.0),
                 kb: bytes = bytes.fromhex("c2cc")) -> bytes:
    """Synthetische Datenspur: je Frame ein Sample mit konstantem Gyro (°/s um y) und Schwerkraftvektor."""
    def imu(v):
        out = struct.pack(">II", proben, 6)
        for _ in range(proben):
            out += struct.pack(">hhh", *v)
        return out
    g = imu((0, int(round(gyro_y * 65.5)), 0))
    a = imu(tuple(int(round(x * 8192)) for x in acc))
    tags = {R.TAG_GYRO: g, R.TAG_GYRO_SKALA: struct.pack(">f", 65.5), R.TAG_ACC: a,
            R.TAG_ACC_SKALA: struct.pack(">f", 8192.0),
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: kb, R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"),
            R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    return R.paket_bauen(tags) * frames


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
    assert rec["brennweitenklasse"] == "tele" and rec["pitch_grad"] == 0.0 and rec["perspektive_hoehe"] == "Augenhöhe"
    assert rec["bewegungsart"] == "schwenk_rechts"          # Gyro-y +10 °/s → dx negativ (vorzeichen −1) → Inhalt nach links
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
    assert (rec["quelle"] == "optisch" and rec["kb_mm"] == 71.6 and rec["brennweitenklasse"] == "tele"
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
