"""Vorlage (Stand 15.09.2026): Musik-Analyse für Schnitt-Übergänge — Tempo, Beat-Raster, Lautheitsverlauf, Abschnitte.

Aufruf: tools/autocut/venv/bin/python _intern/musik_analyse.py
Liest alle WAVs in Material/Musik/, schreibt _intern/musik/analyse.json und druckt je Track:
Tempo (Onset-Autokorrelation), Beat-Raster (erste Zählzeit), Lautheitsverlauf in 2-s-Schritten (RMS dBFS),
Helligkeit (Spektral-Schwerpunkt), Abschnittsgrenzen (Energie-/Klangwechsel, mindestens 8 s auseinander, auf ganze Takte gerundet).
Grundlage für MUSIK_PLAN in feinschnitt_bauen.py (Übergänge auf Taktgrenzen) und für musik/sprung_berechnen.py (takt_s).
Hinweis: gemessen, nicht gehört — Übergänge vor der Abnahme gegenhören. Nur Dateien mit Endung „.wav" (klein geschrieben).
Herkunft: Taxodia-Charge, _intern/musik_analyse.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import find_peaks

CH = Path(__file__).resolve().parent.parent
MUSIK = CH / "Material" / "Musik"
OUT = CH / "_intern" / "musik"
HOP = 512  # Standard (15.09.): Analyse-Hop in Samples (Fenster 2048)

# ── ANPASSEN je Charge ─────────────────────────────
# nichts anzupassen: analysiert alle WAVs in Material/Musik/ der Charge
# ── Ende ANPASSEN ──────────────────────────────────


def lade(pfad: Path) -> tuple[int, np.ndarray]:
    sr, x = wavfile.read(pfad)
    if x.dtype == np.int32:
        x = x.astype(np.float32) / 2 ** 31
    elif x.dtype == np.int16:
        x = x.astype(np.float32) / 2 ** 15
    if x.ndim == 2:
        x = x.mean(axis=1)
    return sr, x


def analyse(pfad: Path) -> dict:
    sr, x = lade(pfad)
    n = len(x) // HOP
    frames = x[: n * HOP].reshape(n, HOP)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    # Spektrum je Block (Fenster 2048, Hop 512) für Onset + Schwerpunkt
    win = 2048
    pad = np.pad(x, (0, win))
    idx = np.arange(0, n * HOP, HOP)
    spec = np.abs(np.fft.rfft(np.stack([pad[i:i + win] * np.hanning(win) for i in idx]), axis=1))
    freqs = np.fft.rfftfreq(win, 1 / sr)
    flux = np.maximum(np.diff(np.log1p(spec), axis=0), 0).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    centroid = (spec * freqs).sum(axis=1) / (spec.sum(axis=1) + 1e-9)
    fps_env = sr / HOP
    # Tempo: Autokorrelation der Onset-Kurve im Bereich 60–160 BPM
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    bpm_lags = (lags >= fps_env * 60 / 160) & (lags <= fps_env * 60 / 60)
    best = lags[bpm_lags][np.argmax(ac[bpm_lags])]
    bpm = 60 * fps_env / best
    if bpm < 80:  # Halbierung vermeiden: bevorzugt 80–160
        bpm *= 2
    beat_s = 60 / bpm
    # Beat-Phase: Summe der Onset-Stärke auf dem Raster maximieren
    period = fps_env * beat_s
    phasen = np.linspace(0, period, 40, endpoint=False)
    scores = [flux[np.clip(np.round(np.arange(p, len(flux), period)).astype(int), 0, len(flux) - 1)].sum() for p in phasen]
    phase_s = phasen[int(np.argmax(scores))] / fps_env
    takt_s = 4 * beat_s
    # Verlauf in 2-s-Schritten
    step = int(2 * fps_env)
    verlauf = []
    for i in range(0, n, step):
        r = rms[i:i + step]
        c = centroid[i:i + step]
        verlauf.append({"t": round(i / fps_env, 1), "db": round(float(20 * np.log10(r.mean() + 1e-9)), 1),
                        "hell_hz": int(c.mean())})
    # Abschnittswechsel: Novelty aus geglätteter Energie + Schwerpunkt (4-s-Kern, Spitzen ≥ 8 s auseinander), auf Taktgrenzen gerundet
    k = int(4 * fps_env)
    feat = np.stack([20 * np.log10(rms + 1e-9), centroid / 1000], axis=1)
    kern = np.ones(k) / k
    glatt = np.stack([np.convolve(feat[:, j], kern, mode="same") for j in range(feat.shape[1])], axis=1)
    nov = np.zeros(n)
    for i in range(k, n - k):
        nov[i] = np.abs(glatt[i + k // 2] - glatt[i - k // 2]).sum()
    peaks, _ = find_peaks(nov, distance=int(8 * fps_env), prominence=np.percentile(nov, 90) * 0.5)
    grenzen = []
    for p in peaks:
        t = p / fps_env
        takte = round((t - phase_s) / takt_s)
        grenzen.append(round(phase_s + takte * takt_s, 2))
    gesamt_db = float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9))
    return {"datei": pfad.name, "dauer_s": round(len(x) / sr, 2), "bpm": round(bpm, 1), "beat_s": round(beat_s, 4),
            "erste_zaehlzeit_s": round(phase_s, 3), "takt_s": round(takt_s, 3), "rms_gesamt_db": round(gesamt_db, 1),
            "abschnitte_s": sorted(set(grenzen)), "verlauf_2s": verlauf}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    alle = []
    for p in sorted(MUSIK.glob("*.wav")):
        a = analyse(p)
        alle.append(a)
        print(f"\n== {a['datei']}  {a['dauer_s']} s  ~{a['bpm']} BPM  Takt {a['takt_s']} s  1. Zählzeit {a['erste_zaehlzeit_s']} s  RMS {a['rms_gesamt_db']} dB")
        print("   Abschnittswechsel (s):", a["abschnitte_s"])
        zeile = []
        for v in a["verlauf_2s"]:
            balken = "#" * max(0, int((v["db"] + 40) / 1.5))
            zeile.append(f"   {v['t']:6.1f}s {v['db']:6.1f} dB {v['hell_hz']:5d} Hz {balken}")
        print("\n".join(zeile))
    if not alle:
        raise SystemExit(f"Keine WAVs in {MUSIK} — Musik als .wav nach Material/Musik legen.")
    (OUT / "analyse.json").write_text(json.dumps(alle, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
