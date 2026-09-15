"""Vorlage (Stand 15.09.2026): Prüf-Render der Begradigung auswerten — Rest-Neigung der Senkrechten und schwarze Ränder je Stück.

Aufruf: tools/transcribe/venv/bin/python _intern/begradigen/pruefung_auswerten.py   (braucht cv2 mit LSD und ffmpeg)
Eingaben: pruefung/pruefung_render.mov + pruefung/plan.json (pruefung_resolve.py export), ../gesichtscheck/faces.
Je Stück das mittlere Frame (i·N + N/2) → pruefung/p_<i>.png (Render-Auflösung) und pruefung/jpg/p_<ii>.jpg (1920×1080):
- schwarze Randpixel: 3-px-Rand des Renders mit höchstem Kanalwert ≤ 2 (8 bit); > 0 = Rand nicht gedeckt (oder dunkles Motiv)
- Senkrechte: LSD auf 1080p (≥ 70 px, ±8° zur Vertikalen), Person maskiert (Vision-Gesichtsbox seitlich ±0,9 Breiten, ab
  0,3 Höhen über dem Gesicht nach unten), längengewichteter Median der Abweichung (+ = oben nach rechts gekippt)
Schreibt pruefung/auswertung.json {Clip-Stamm: {ohne|mit|punch: {senkrechte, roll_median, schwarze_randpixel}}} und
Vergleichsbögen pruefung/vergleich_<Kamera>.jpg (je Clip: ohne | mit) und vergleich_punch.jpg (ohne | punch), gelbe
Hilfslinien alle 80 px. Nichts in Resolve.
Danach: pruefung_resolve.py loeschen → aufraeumen_begradigen.py → pruefung_render.mov und p_*.png lokal löschen.
Befund (15.09.): roll_median ist nur bei vielen Senkrechten verlässlich (80 Senkrechte: +0,1°, 4 Senkrechte: +0,9°) —
die Vergleichsbögen immer zusätzlich ansehen.
Herkunft: Taxodia-Session, inline im Session-Transkript (15.09.2026, kein eigenes Skript)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
AUS = HIER / "pruefung"

# ── ANPASSEN je Charge ─────────────────────────────
# keine eigenen Werte: Stücke und Reihenfolge kommen aus pruefung/plan.json (pruefung_resolve.py)
# ── Ende ANPASSEN ──────────────────────────────────

N = 10  # Frames je Prüfstück, wie pruefung_resolve.N


def main() -> None:
    plan = json.loads((AUS / "plan.json").read_text())
    for i in range(len(plan)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AUS / "pruefung_render.mov"), "-vf", f"select=eq(n\\,{i * N + N // 2})",
                        "-frames:v", "1", "-update", "1", str(AUS / f"p_{i}.png")], check=True)
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    faces_bin = str(INTERN / "gesichtscheck" / "faces")
    # Gesichtsmasken per Vision auf 1080p-JPEGs
    (AUS / "jpg").mkdir(exist_ok=True)
    for i in range(len(plan)):
        im = cv2.imread(str(AUS / f"p_{i}.png"))
        cv2.imwrite(str(AUS / "jpg" / f"p_{i:02d}.jpg"), cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 92])
    tsv = subprocess.run([faces_bin, str(AUS / "jpg")], capture_output=True, text=True).stdout
    boxen = {z.split("\t")[0]: [tuple(map(float, b.split(","))) for b in z.split("\t")[1].split(";")] if "\t" in z and z.split("\t")[1] not in ("", "ERR") else [] for z in tsv.splitlines()}
    W, H = 1920, 1080
    erg = {}
    for i, x in enumerate(plan):
        full = cv2.imread(str(AUS / f"p_{i}.png"))
        rand = np.concatenate([full[:3].reshape(-1, 3), full[-3:].reshape(-1, 3), full[:, :3].reshape(-1, 3), full[:, -3:].reshape(-1, 3)])
        schwarz = int((rand.max(axis=1) <= 2).sum())
        img = cv2.imread(str(AUS / "jpg" / f"p_{i:02d}.jpg"), cv2.IMREAD_GRAYSCALE)
        segs = lsd.detect(img)[0].reshape(-1, 4)
        L = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
        segs, L = segs[L >= 70], L[L >= 70]
        maske = np.zeros((H, W), bool)
        for x0, y0, x1, y1, c in boxen.get(f"p_{i:02d}.jpg", []):
            if c < 0.5:
                continue
            bw, bh = (x1 - x0) * W, (y1 - y0) * H
            maske[int(max(0, y0 * H - 0.3 * bh)):, int(max(0, x0 * W - 0.9 * bw)):int(min(W, x1 * W + 0.9 * bw))] = True
        mx = ((segs[:, 0] + segs[:, 2]) / 2).astype(int).clip(0, W - 1)
        my = ((segs[:, 1] + segs[:, 3]) / 2).astype(int).clip(0, H - 1)
        segs, L = segs[~maske[my, mx]], L[~maske[my, mx]]
        dx, dy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
        sgn = np.where(dy < 0, -1, 1)
        abw = np.degrees(np.arctan2(dx * sgn, dy * sgn))
        v = np.abs(abw) <= 8
        a, w = abw[v], L[v]
        o = np.argsort(a)
        kum = np.cumsum(w[o])
        med = float(a[o][np.searchsorted(kum, kum[-1] / 2)]) if len(a) else None
        erg.setdefault(x["stem"], {})[x["art"]] = {"senkrechte": int(v.sum()), "roll_median": None if med is None else round(med, 2),
                                                   "schwarze_randpixel": schwarz}
    for stem, d in erg.items():
        print(stem, d)
    (AUS / "auswertung.json").write_text(json.dumps(erg, indent=1), encoding="utf-8")
    # Vergleichsbögen: je Clip ohne | mit (nach Kamera-Präfix des Clip-Stamms), Punch-in-Stücke ohne | punch
    kacheln = []
    for i, x in enumerate(plan):
        im = cv2.resize(cv2.imread(str(AUS / f"p_{i}.png")), (960, 540), interpolation=cv2.INTER_AREA)
        for gx in range(0, 960, 80):
            cv2.line(im, (gx, 0), (gx, 539), (0, 255, 255), 1)
        cv2.putText(im, f"{x['stem']} {x['art']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
        cv2.putText(im, f"{x['stem']} {x['art']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        kacheln.append(im)
    index = {(x["stem"], x["art"]): i for i, x in enumerate(plan)}
    boegen: dict[str, list] = {}
    for stem in dict.fromkeys(x["stem"] for x in plan):
        for art, bogen in (("mit", stem.split("_")[0]), ("punch", "punch")):
            if (stem, "ohne") in index and (stem, art) in index:
                reihe = np.concatenate([kacheln[index[(stem, "ohne")]], np.full((540, 8, 3), 30, np.uint8), kacheln[index[(stem, art)]]], axis=1)
                boegen.setdefault(bogen, []).append(reihe)
    for bogen, reihen in boegen.items():
        cv2.imwrite(str(AUS / f"vergleich_{bogen}.jpg"), np.concatenate(reihen, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("Vergleichsbögen:", sorted(boegen))


if __name__ == "__main__":
    main()
