"""telemetrie_kalibrierung.py — Achsen/Vorzeichen/Faktor/Spearman aus synthetischen Gyro-↔-optisch-Paaren."""
from __future__ import annotations

import math

import numpy as np
import pytest

from niro_autocut import telemetrie_kalibrierung as K
from niro_autocut.charge import Charge
from test_telemetrie import CFG, _info, _kb, _rtmd_puffer, _zoomreihe


def _messung(rng, kamera: str, faktor: float, n: int = 100, kb: float = 36.0, rauschen: float = 0.05,
            wackel: float = 1.0) -> dict:
    """Optische Verschiebung = faktor · (−Gyro-y für dx, +Gyro-x für dy) · k + Rauschen; Gyro-z unkorreliert."""
    k = math.pi / 180.0 * K.f_px(kb) / K.ZIEL_FPS
    rate = np.stack([rng.normal(0, 3 * wackel, n), rng.normal(0, 4 * wackel, n), rng.normal(0, 2, n)], axis=1)
    opt = np.stack([-faktor * rate[:, 1] * k + rng.normal(0, rauschen, n),
                    faktor * rate[:, 0] * k + rng.normal(0, rauschen, n)], axis=1)
    return {"path": f"/nas/{kamera}_{rng.integers(1e6)}.MP4", "clip": "c", "kamera": kamera, "kb_mm": kb, "k": k,
            "rate": rate.tolist(), "opt": opt.tolist()}


def test_auswerten_findet_achsen_vorzeichen_faktor():
    rng = np.random.default_rng(5)
    mess = [_messung(rng, "FX3", 1.0, wackel=w) for w in np.linspace(0.2, 2.0, 12)] + \
           [_messung(rng, "a7IV", 0.6, wackel=w) for w in np.linspace(0.2, 2.0, 12)]
    erg = K.auswerten_kalibrierung(mess, CFG)
    fx = erg["kameras"]["FX3"]
    assert (fx["achse_schwenk"] == 1 and fx["vorzeichen_schwenk"] == -1 and fx["achse_tilt"] == 0
           and fx["vorzeichen_tilt"] == 1)
    assert abs(fx["px_faktor"] - 1.0) < 0.1 and fx["spearman"] > 0.9 and fx["belastbar"] is True and fx["clips"] == 12
    a7 = erg["kameras"]["a7IV"]
    assert abs(a7["px_faktor"] - 0.6) < 0.1 and a7["belastbar"] is True
    e = erg["empfehlung"]
    assert (e["achsen"] == {"schwenk": 1, "tilt": 0} and e["vorzeichen"] == {"schwenk": -1, "tilt": 1}
           and e["optisch_fuer"] == [])
    assert abs(e["px_faktor"]["a7IV"] - 0.6) < 0.1


def test_auswerten_markiert_unbelastbare_kamera():
    rng = np.random.default_rng(6)
    mess = []
    for _ in range(20):                                          # 20 Clips: Zufalls-Spearman ≥ 0,7 praktisch ausgeschlossen
        m = _messung(rng, "DJI", 1.0)
        m["opt"] = rng.normal(0, 1, (100, 2)).tolist()          # optisch hat nichts mit dem Gyro zu tun
        mess.append(m)
    erg = K.auswerten_kalibrierung(mess, CFG)
    assert erg["kameras"]["DJI"]["belastbar"] is False and erg["empfehlung"]["optisch_fuer"] == ["DJI"]


def test_auswerten_klammert_saettigung_aus_und_vergleicht_cv2():
    rng = np.random.default_rng(7)
    mess = [_messung(rng, "FX3", 1.0) for _ in range(6)]
    mess[0]["opt"] = (np.array(mess[0]["opt"]) + 70.0).tolist()          # gesättigte Frames (> 40 px) zählen nicht
    ruhe = {m["clip"] + str(i): 0.0 for i, m in enumerate(mess)}
    for i, m in enumerate(mess):
        m["clip"] = m["clip"] + str(i)
        ruhe[m["clip"]] = K.wackeln_bewegung(np.array(m["opt"]))[0] * 1.02  # cv2-Wert ≈ numpy-Wert
    erg = K.auswerten_kalibrierung(mess, CFG, ruhe=ruhe)
    assert erg["kameras"]["FX3"]["clips"] == 5 and abs(erg["kameras"]["FX3"]["px_faktor"] - 1.0) < 0.15
    assert (erg["cv2_vergleich"]["n"] == 5
           and abs(erg["cv2_vergleich"]["verhaeltnis_median"] - 1.02) < 0.01 and erg["cv2_vergleich"]["r"] > 0.99)


def _zoom_im_fenster(monkeypatch, tmp_path, faktor: float = 0.6) -> dict | None:
    """FX3-Clip 12 s in 50p: 7 s bei 24 mm, Zoom auf 72 mm in 7–8 s, danach 72 mm; Kalibrierfenster 7–11 s mit der
    Zoomfahrt am Anfang (Sample 350 = 25-fps-Frame 175). Optisch = faktor · Schwenk (Gyro-y, Vorzeichen −), jede
    rtmd-Probe über ihre eigene Brennweite gerechnet — unabhängig vom Code; der Clip-Median (24 mm) liegt neben dem
    Fenster (72 mm)."""
    fps, von_s = 50.0, 7.0
    kb = np.array(_zoomreihe((7.0, 24, 24), (1.0, 24, 72), (4.0, 72, 72), fps=fps)[:600])
    gyro_y = np.random.default_rng(11).integers(-400, 400, len(kb)) / 65.5         # Skala 65,5: genau darstellbar
    beitrag = -faktor * gyro_y / fps * math.pi / 180.0 * 480.0 * kb / 36.0            # px je 50p-Sample
    dx = beitrag[350:550].reshape(100, 2).sum(axis=1)                                 # 2 Samples je 25-fps-Frame
    opt = np.stack([dx, np.zeros(100)], axis=1)
    puffer = b"".join(_rtmd_puffer(frames=1, proben=40, gyro_y=w, kb=_kb(mm)) for w, mm in zip(gyro_y, kb))
    clip = tmp_path / "FX3_0080.MP4"
    clip.write_bytes(b"x")
    monkeypatch.setattr(K, "ffprobe", lambda p: _info(str(p), fps=fps, dauer=12.0))
    monkeypatch.setattr(K, "datenspur_lesen", lambda p: puffer)
    monkeypatch.setattr(K, "graustufen", lambda *a: None)
    monkeypatch.setattr(K, "verschiebungen", lambda bilder: opt)
    return K.clip_kalibrieren(clip, CFG, von_s)


def test_kalibrierung_rechnet_zoom_im_fenster_mit_der_brennweite_je_frame(monkeypatch, tmp_path):
    """Spec 2026-09-25 für den Kalibrierweg: Gyro-px mit der Brennweite je Frame im Fenster wie ``clip_messen`` —
    mit dem Clip-Median (eine Brennweite für den ganzen Clip) kam hier 1,59 statt 0,6 heraus."""
    m = _zoom_im_fenster(monkeypatch, tmp_path, faktor=0.6)
    erg = K.auswerten_kalibrierung([m], CFG)
    assert erg["kameras"]["FX3"]["px_faktor"] == pytest.approx(0.6, abs=0.005)


def test_kalibrierung_klammert_saettigung_aus_ohne_die_brennweiten_zu_verschieben(monkeypatch, tmp_path):
    """Gesättigte Frames am Fensteranfang (in der Zoomfahrt) fallen raus; jeder übrige Frame behält sein ``k``."""
    m = _zoom_im_fenster(monkeypatch, tmp_path, faktor=0.6)
    opt = np.array(m["opt"])
    opt[:10, 0] += 50.0                                                  # ≥ 40 px: Phasenkorrelation gesättigt
    m["opt"] = opt.tolist()
    fx = K.auswerten_kalibrierung([m], CFG)["kameras"]["FX3"]
    assert fx["frames"] == 89 and fx["px_faktor"] == pytest.approx(0.6, abs=0.005)


def test_kalibrierung_nennt_die_brennweite_im_fenster(monkeypatch, tmp_path):
    """``kb_mm`` (Fortschritt, ``clips`` in telemetrie_kalibrierung.json) = Median im gemessenen Fenster."""
    assert _zoom_im_fenster(monkeypatch, tmp_path)["kb_mm"] == 72.0


def test_tabelle_und_leer():
    erg = K.auswerten_kalibrierung([], CFG)
    assert erg["kameras"] == {} and "keine Clips" in K.tabelle(erg)
    rng = np.random.default_rng(8)
    erg = K.auswerten_kalibrierung([_messung(rng, "FX3", 1.0) for _ in range(3)], CFG)
    t = K.tabelle(erg)
    assert "FX3" in t and "px_faktor" in t and "Spearman" in t


def test_kalibrieren_haelt_bei_unerwarteten_fehlern_durch(monkeypatch, basis_charge):
    """Abweichung vom Task-Brief (Global Constraint „je Clip nie abbrechen"): kalibrieren fängt wie
    telemetrie_charge jede Ausnahme je Clip ab, nicht nur AutoCutError — ein ValueError aus clip_kalibrieren
    (z. B. ein unlesbares Sidecar-XML oder ein numpy-/Parse-Fehler auf einer ungewöhnlichen Datenspur) darf
    den Lauf nicht abbrechen; die Kalibrierung von hunderten NAS-Clips (Task 7) muss trotzdem durchlaufen."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    ch = Charge.open_basis(basis_charge)
    rng = np.random.default_rng(9)
    gut = _messung(rng, "FX3", 1.0)

    def fake(path, cfg, von_s, dauer_s):
        if "kaputt" in str(path):
            raise ValueError("Datenspur unlesbar")
        return gut

    monkeypatch.setattr(K, "clip_kalibrieren", fake)
    clips = [{"path": "/nas/FX3_gut.MP4", "ordner": "x"}, {"path": "/nas/FX3_kaputt.MP4", "ordner": "x"}]
    erg = K.kalibrieren(ch, clips, CFG, melden=lambda *a, **k: None)
    assert len(erg["fehler"]) == 1 and "ValueError" in erg["fehler"][0]
    assert (ac / "telemetrie_kalibrierung.json").exists()
