"""Vorlage (Stand 15.09.2026): Spektrogramm-Kontaktbögen für die SFX-Vorauswahl — Sichtprüfung statt Namen.

Aufruf: PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python _intern/sfx/sfx_spektren.py <bogen-name> "<Datei 1>" "<Datei 2>" …
  Dateien = Feld „name" aus analyse/sfx_metriken.json (vorher sfx_analyse.py); unbekannte Namen werden gemeldet und übersprungen.
Je Datei: log-frequentes Spektrogramm 40 Hz–20 kHz (dB relativ zum Datei-Maximum, 70 dB Umfang), weiße Hüllkurve (RMS 10 ms,
0 … −60 dB), Zeitraster in Frames (25 fps: Marke je 5 Frames, volle Linie je 25 Frames; unter 1,5 s Fenster zusätzlich je Frame); Fenster per SPEKTRUM_MAX_S, Kopfzeile mit Messwerten aus sfx_metriken.json.
Schreibt _intern/sfx/analyse/spektren/<bogen-name>.png (2 Spalten).
Bewährt (15.09.): ein Bogen je Rolle bzw. Kandidatengruppe (kurze Whooshes, weiche Whooshes, Swishes, Pops/Clicks, UI-Töne,
Riser/Shimmer, Varianten einer Serie); sichtbar werden harter Stopp, Swell-Form, Tonlinien, tieffrequente Plopps, Tremolo.
Herkunft: Taxodia-Charge, _intern/sfx/sfx_spektren.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── ANPASSEN je Charge ─────────────────────────────
# (keine Chargenwerte; angezeigtes Zeitfenster per Umgebungsvariable SPEKTRUM_MAX_S, Standard 3,0 s)
# ── Ende ANPASSEN ──────────────────────────────────

HIER = Path(__file__).resolve().parent
SR = 48000
W, H, KOPF = 760, 230, 34
MAX_S = float(os.environ.get("SPEKTRUM_MAX_S", "3.0"))  # angezeigter Zeitbereich (längere Dateien werden abgeschnitten, Hinweis im Kopf)

ANKER = np.array([[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66], [245, 125, 21], [250, 193, 39], [252, 255, 164]], float)


def farbe(v: np.ndarray) -> np.ndarray:
    v = np.clip(v, 0, 1) * (len(ANKER) - 1)
    i = np.minimum(v.astype(int), len(ANKER) - 2)
    t = (v - i)[..., None]
    return (ANKER[i] * (1 - t) + ANKER[i + 1] * t).astype(np.uint8)


def lade(pfad: str) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", pfad, "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def kachel(m: dict) -> Image.Image:
    x = lade(m["pfad_nas"])
    dauer = len(x) / SR
    x = x[: int(MAX_S * SR)]
    nfft, hop = 2048, 240  # 5 ms Hop
    xp = np.pad(x, (nfft // 2, nfft))
    idx = np.arange(0, len(x), hop)
    win = np.hanning(nfft)
    S = np.abs(np.fft.rfft(np.stack([xp[i:i + nfft] * win for i in idx]), axis=1)) ** 2
    f = np.fft.rfftfreq(nfft, 1 / SR)
    db = 10 * np.log10(S + 1e-14)
    db = db - db.max()
    # log-Frequenzachse
    fy = np.geomspace(40, 20000, H)
    spalten = np.array([np.interp(fy, f, zeile) for zeile in db])  # (T, H)
    t_px = np.linspace(0, MAX_S, W)
    ti = np.minimum((t_px / (hop / SR)).astype(int), len(spalten) - 1)
    img = spalten[ti].T[::-1]  # (H, W), hohe Frequenzen oben
    img[:, t_px > len(x) / SR] = -200
    rgb = farbe((img + 70) / 70)
    bild = Image.new("RGB", (W, H + KOPF), (18, 18, 18))
    bild.paste(Image.fromarray(rgb), (0, KOPF))
    d = ImageDraw.Draw(bild)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
    # Zeitraster
    for k in range(int(MAX_S * 25) + 1):  # Raster je Frame (40 ms), dicke Linie je 5 Frames, volle Linie je 25 Frames
        px = int(k / 25 / MAX_S * (W - 1))
        if MAX_S > 1.5 and k % 5:
            continue
        lang = KOPF + H if k % 25 == 0 else (KOPF + 14 if k % 5 == 0 else KOPF + 5)
        d.line([(px, KOPF), (px, lang)], fill=(160, 160, 160) if k % 5 == 0 else (90, 90, 90), width=1)
    # Frequenz-Marken
    for fm in (100, 1000, 5000, 10000):
        py = KOPF + int((1 - np.log(fm / 40) / np.log(20000 / 40)) * (H - 1))
        d.line([(0, py), (8, py)], fill=(200, 200, 200))
        d.text((10, py - 7), f"{fm // 1000}k" if fm >= 1000 else str(fm), fill=(200, 200, 200), font=font)
    # Hüllkurve
    p = x ** 2
    wn = int(0.01 * SR)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    st = np.arange(0, max(1, len(p) - wn), int(0.005 * SR))
    env = 10 * np.log10((cs[st + wn] - cs[st]) / wn + 1e-14)
    env -= env.max()
    pts = [(int((s / SR) / MAX_S * (W - 1)), KOPF + int(np.clip(-e / 60, 0, 1) * (H - 1))) for s, e in zip(st, env)]
    if len(pts) > 1:
        d.line(pts, fill=(255, 255, 255), width=1)
    kopf = (f"{m['name'][:52]}  [{m['bin'].split('/')[-1]}]  {dauer:.2f}s{f' (bis {MAX_S:g} s)' if dauer > MAX_S else ''}  pk {m['peak_dbfs']} dBFS  "
            f"M {m['lufs_momentan_max']} LUFS")
    kopf2 = (f"on {m['t_onset_s']}  -3dB {m['t_minus3_s']}  peak {m['t_peak_s']}  -20dB {m['t_ende_20db_s']}  -40dB {m['t_ende_40db_s']}  "
             f"cen {m['schwerpunkt_hz']} Hz  flat {m['flachheit']}  ton {m['tonanteil']}")
    d.text((4, 2), kopf, fill=(235, 235, 235), font=font)
    d.text((4, 17), kopf2, fill=(180, 180, 180), font=font)
    return bild


def main() -> None:
    name, dateien = sys.argv[1], sys.argv[2:]
    met = {m["name"]: m for m in json.loads((HIER / "analyse" / "sfx_metriken.json").read_text())}
    kacheln = []
    for n in dateien:
        if n not in met:
            print("fehlt in Metriken:", n)
            continue
        kacheln.append(kachel(met[n]))
    spalten = 2
    zeilen = (len(kacheln) + spalten - 1) // spalten
    bogen = Image.new("RGB", (spalten * (W + 8), zeilen * (H + KOPF + 8)), (0, 0, 0))
    for i, k in enumerate(kacheln):
        bogen.paste(k, ((i % spalten) * (W + 8), (i // spalten) * (H + KOPF + 8)))
    out = HIER / "analyse" / "spektren"
    out.mkdir(parents=True, exist_ok=True)
    bogen.save(out / f"{name}.png")
    print(out / f"{name}.png", bogen.size)


if __name__ == "__main__":
    main()
