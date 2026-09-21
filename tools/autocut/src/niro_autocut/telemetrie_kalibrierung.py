"""Kalibrierung Gyro ↔ optisch (Spec 2026-09-19, Abschnitt Kalibrierung): beide Messwege auf demselben Fenster je Clip.

Je Kamera: Achse und Vorzeichen für Schwenk (→ dx) und Tilt (→ dy) aus der Korrelation der Gyro-Raten mit der optischen
Verschiebung, Kamerafaktor (IBIS-Dämpfung) als robuste Steigung Gyro-px → optisch-px, Rangkorrelation (Spearman) der
Wackel-Werte je Clip; Gegenprobe der numpy-Phasenkorrelation gegen vorhandene cv2-Werte (``ruhe.json``).
Frames mit |optisch| ≥ 40 px zählen nicht (Phasenkorrelation sättigt; Stichprobe 21.09.).
"""
from __future__ import annotations

import datetime as _dt
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from .charge import AutoCutError
from .media import ffprobe
from .rtmd import auswerten, datenspur_lesen, kamera_erkennen, samples, sidecar_modell
from .telemetrie import ZIEL_FPS, f_px, gyro_je_frame, wackeln_bewegung
from .telemetrie_optisch import graustufen, verschiebungen

SAETTIGUNG_PX = 40.0
MIN_FRAMES = 10
BELASTBAR_AB = 0.7


def clip_kalibrieren(path: str | Path, cfg: dict, von_s: float, dauer_s: float = 4.0) -> dict | None:
    """Gyro-Raten je 25-fps-Frame (roh, 3 Achsen) und optische Verschiebung über dasselbe Fenster; None ohne
    Gyro/Brennweite."""
    p = Path(path)
    info = ffprobe(p)
    buf = datenspur_lesen(p)
    if not buf:
        return None
    d = auswerten(samples(buf))
    if len(d.gyro) == 0 or d.proben_je_sample <= 0 or not d.kb_mm:
        return None
    i0 = int(round(von_s * info.fps))
    i1 = int(round((von_s + dauer_s) * info.fps))
    gyro = d.gyro[i0 * d.proben_je_sample:i1 * d.proben_je_sample]
    rate = gyro_je_frame(gyro, d.proben_je_sample, info.fps, imu_hz=d.imu_hz)
    opt = verschiebungen(graustufen(p, ZIEL_FPS, von_s, dauer_s, int(cfg["optisch_breite"]),
                                    int(round(int(cfg["optisch_breite"]) * 9 / 16))))
    m = min(len(rate) - 1, len(opt))
    if m < MIN_FRAMES:
        return None
    kb = float(np.median(d.kb_mm))
    return {"path": str(p), "clip": p.stem, "kamera": kamera_erkennen(p, sidecar_modell(p)), "kb_mm": round(kb, 1),
            "k": math.pi / 180.0 * f_px(kb, int(cfg["optisch_breite"])) / ZIEL_FPS,
            "rate": rate[:m].tolist(), "opt": opt[:m].tolist()}


def _korrelation(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def auswerten_kalibrierung(messungen: list[dict], cfg: dict, ruhe: dict | None = None) -> dict:
    """Je Kamera Achsen/Vorzeichen, px_faktor (Median der Steigungen je Clip), Spearman; Empfehlung für defaults.yaml."""
    kameras: dict[str, dict] = {}
    for kam in sorted({m["kamera"] for m in messungen}):
        ms = [m for m in messungen if m["kamera"] == kam]
        rates, opts, clips = [], [], []
        for m in ms:
            rate, opt = np.array(m["rate"], float), np.array(m["opt"], float)
            ok = (np.abs(opt) < SAETTIGUNG_PX).all(axis=1)
            if ok.sum() < MIN_FRAMES:
                continue
            rates.append(rate[ok] * m["k"])
            opts.append(opt[ok])
            clips.append(m)
        if not clips:
            continue
        r_all, o_all = np.concatenate(rates), np.concatenate(opts)
        r_dx = [_korrelation(r_all[:, a], o_all[:, 0]) for a in range(3)]
        achse_s = int(np.argmax(np.abs(r_dx)))
        vz_s = 1 if r_dx[achse_s] >= 0 else -1
        r_dy = [_korrelation(r_all[:, a], o_all[:, 1]) if a != achse_s else 0.0 for a in range(3)]
        achse_t = int(np.argmax(np.abs(r_dy)))
        vz_t = 1 if r_dy[achse_t] >= 0 else -1
        steigungen, wg, wo = [], [], []
        for r, o in zip(rates, opts):
            pred = np.stack([vz_s * r[:, achse_s], vz_t * r[:, achse_t]], axis=1)
            nenner = float((pred ** 2).sum())
            if nenner > 0:
                steigungen.append(float((pred * o).sum() / nenner))
            wg.append(wackeln_bewegung(pred)[0])
            wo.append(wackeln_bewegung(o)[0])
        faktor = float(np.median(steigungen)) if steigungen else 1.0
        rho = float(spearmanr(wg, wo).statistic) if len(wg) >= 3 else 0.0
        if math.isnan(rho):
            rho = 0.0
        kameras[kam] = {"clips": len(clips), "frames": int(len(r_all)), "achse_schwenk": achse_s,
                        "vorzeichen_schwenk": vz_s, "r_schwenk": round(r_dx[achse_s], 3), "achse_tilt": achse_t,
                        "vorzeichen_tilt": vz_t, "r_tilt": round(r_dy[achse_t], 3), "px_faktor": round(faktor, 3),
                        "spearman": round(rho, 3), "belastbar": bool(rho >= BELASTBAR_AB)}
        kameras[kam]["empfehlung"] = (f"px_faktor {kameras[kam]['px_faktor']}, Spearman {kameras[kam]['spearman']}"
                                     + ("" if kameras[kam]["belastbar"] else " → optisch_fuer"))
    # Empfehlung: Achsen/Vorzeichen aus der belastbaren Kamera mit den meisten Frames, Faktor je Kamera
    belastbar = {k: v for k, v in kameras.items() if v["belastbar"]}
    basis = max(belastbar.values(), key=lambda v: v["frames"]) if belastbar else None
    empfehlung = {"achsen": {"schwenk": basis["achse_schwenk"], "tilt": basis["achse_tilt"]}
                  if basis else dict(cfg["achsen"]),
                  "vorzeichen": {"schwenk": basis["vorzeichen_schwenk"], "tilt": basis["vorzeichen_tilt"]} if basis else
                  {"schwenk": cfg["vorzeichen"]["schwenk"], "tilt": cfg["vorzeichen"]["tilt"]},
                  "px_faktor": {k: v["px_faktor"] for k, v in belastbar.items()},
                  "optisch_fuer": sorted(k for k, v in kameras.items() if not v["belastbar"])}
    cv2 = None
    if ruhe:
        paare = [(wackeln_bewegung(np.array(m["opt"], float))[0], float(ruhe[m["clip"]])) for m in messungen
                 if m["clip"] in ruhe and ruhe[m["clip"]] is not None and (np.abs(np.array(m["opt"])) < SAETTIGUNG_PX).all()]
        if paare:
            a, b = np.array(paare).T
            verh = np.median(b[a > 0] / a[a > 0]) if (a > 0).any() else float("nan")
            cv2 = {"n": len(paare), "r": round(_korrelation(a, b), 4), "verhaeltnis_median": round(float(verh), 3)}
    return {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"), "anzahl": len(messungen), "kameras": kameras,
            "empfehlung": empfehlung, "cv2_vergleich": cv2}


def kalibrieren(ch, clips: list[dict], cfg: dict, dauer_s: float = 4.0, parallel: int | None = None,
                melden=print) -> dict:
    """Alle Clips messen (Fenster ab ``von_s`` aus ``_intern/sichtung/katalog.json``, sonst 0,5 s), auswerten,
    JSON schreiben."""
    katalog = Path(ch.intern) / "sichtung" / "katalog.json"
    von: dict[str, float] = {}
    ruhe: dict[str, float] | None = None
    if katalog.exists():
        von = {r["clip"]: float(r.get("von_s", 0.5)) for r in json.loads(katalog.read_text(encoding="utf-8"))}
    ruhe_pfad = Path(ch.intern) / "sichtung" / "ruhe.json"
    if ruhe_pfad.exists():
        ruhe = {r["clip"]: r.get("jitter") for r in json.loads(ruhe_pfad.read_text(encoding="utf-8")) if "jitter" in r}
    messungen, fehler = [], []
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel or cfg.get("parallel", 2))))
    try:
        futs = {ex.submit(clip_kalibrieren, c["path"], cfg, von.get(Path(c["path"]).stem, 0.5), dauer_s): c
               for c in clips}
        for i, fut in enumerate(as_completed(futs), 1):
            name = Path(futs[fut]["path"]).name
            try:
                m = fut.result()
            except Exception as e:
                # Wie telemetrie_charge (Task 4): jede Ausnahme eines einzelnen Clips (nicht nur AutoCutError —
                # z. B. ein OSError aus einem unlesbaren Sidecar-XML in sidecar_modell oder ein numpy-/Parse-Fehler
                # auf einer ungewöhnlichen Datenspur) bricht den Lauf nicht ab; KeyboardInterrupt bleibt ausgenommen
                # (kein Exception-Subtyp) und läuft in den except-Block der äußeren Schleife weiter.
                meldung = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
                fehler.append(f"{name}: {meldung}")
                melden(f"[{i}/{len(clips)}] FEHLER {name}: {meldung}", flush=True)
                continue
            if m is None:
                melden(f"[{i}/{len(clips)}] {name}: ohne Gyro/Brennweite oder zu kurz — übersprungen", flush=True)
                continue
            messungen.append(m)
            melden(f"[{i}/{len(clips)}] {name}: {len(m['rate'])} Frames, KB {m['kb_mm']} mm", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    erg = auswerten_kalibrierung(messungen, cfg, ruhe)
    erg["fehler"] = fehler
    erg["clips"] = [{"clip": m["clip"], "kamera": m["kamera"], "kb_mm": m["kb_mm"], "frames": len(m["rate"]),
                     "wackeln_optisch": round(wackeln_bewegung(np.array(m["opt"]))[0], 3)} for m in messungen]
    ch.write_json("telemetrie_kalibrierung.json", erg)
    return erg


def tabelle(erg: dict) -> str:
    if not erg.get("kameras"):
        return "Kalibrierung: keine Clips mit Gyro und Brennweite."
    z = [f"{'Kamera':<8} {'Clips':>5} {'Frames':>7} {'Schwenk':>9} {'r':>6} {'Tilt':>7} {'r':>6} "
        f"{'px_faktor':>9} {'Spearman':>8}  belastbar"]
    for k, v in erg["kameras"].items():
        z.append(f"{k:<8} {v['clips']:>5} {v['frames']:>7} "
                 f"{('xyz'[v['achse_schwenk']] + ('+' if v['vorzeichen_schwenk'] > 0 else '−')):>9} "
                 f"{v['r_schwenk']:>6.2f} "
                 f"{('xyz'[v['achse_tilt']] + ('+' if v['vorzeichen_tilt'] > 0 else '−')):>7} {v['r_tilt']:>6.2f} "
                 f"{v['px_faktor']:>9.3f} {v['spearman']:>8.2f}  {'ja' if v['belastbar'] else 'NEIN → optisch_fuer'}")
    e = erg["empfehlung"]
    z.append(f"\nEmpfehlung defaults.yaml telemetrie: achsen {e['achsen']}, vorzeichen {e['vorzeichen']}, "
             f"px_faktor {e['px_faktor']}, "
             f"optisch_fuer {e['optisch_fuer']}")
    if erg.get("cv2_vergleich"):
        c = erg["cv2_vergleich"]
        z.append(f"Gegenprobe cv2 (ruhe.json): {c['n']} Clips, r = {c['r']}, "
                 f"Verhältnis cv2/numpy Median {c['verhaeltnis_median']}")
    return "\n".join(z)
