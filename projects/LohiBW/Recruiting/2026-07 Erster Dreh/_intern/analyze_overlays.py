#!/usr/bin/env python3
"""
Vermisst die bereits eingebauten Animationen in den LohiBW-Ads.

Zweck: die Untertitel-Animation darf sich nicht mit den vorhandenen
gelben Keyword-Boxen und dem Logo-Badge überschneiden. Das Script
liefert pro Video die belegten Zeitfenster + vertikalen Zonen sowie
den exakten Gelbton.

Aufruf:  python analyze_overlays.py <video.mp4> [...]
Ausgabe: JSON nach stdout + Klartext-Bilanz nach stderr.
"""

import json
import subprocess
import sys
from collections import Counter

import numpy as np

W, H = 540, 960          # Analyse-Auflösung (Video ist 2160x3840)
STEP = 5                 # jeden 5. Frame → 5 Samples/Sek bei 25 fps
FPS = 25

# Strenge Maske: kräftiges, gesättigtes Gelb wie in den Boxen.
# Haut/Holz/Pflanzen fallen raus, weil dort B relativ hoch bzw.
# die Sättigung deutlich geringer ist.
def yellow_mask(a):
    r = a[..., 0].astype(np.int16)
    g = a[..., 1].astype(np.int16)
    b = a[..., 2].astype(np.int16)
    return (r > 200) & (g > 165) & (g < 240) & (b < 90) & (abs(r - g) < 80) & ((r - b) > 140)


def bands_from_mask(m, gray, min_frac=0.06, min_rows=4):
    """Echte Keyword-Kästen finden.

    Ein Kasten ist ein satt gefülltes, achsenparalleles Rechteck mit
    dunklem Text darin. Szenen-Gelb (Empfangstheke, blondes Haar,
    Pflanzen) erfüllt das nicht und fliegt hier raus.
    """
    rows = m.sum(axis=1)
    hot = rows > (m.shape[1] * min_frac)
    out, start = [], None
    for y, v in enumerate(list(hot) + [False]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= min_rows:
                sub = m[start:y]
                cols = np.nonzero(sub.sum(axis=0) > 0)[0]
                x0, x1 = int(cols.min()), int(cols.max())
                bw, bh = x1 - x0 + 1, y - start
                fill = sub[:, x0:x1 + 1].mean()
                # Text im Kasten: dunkle Pixel dort, wo kein Gelb ist
                inner = gray[start:y, x0:x1 + 1]
                inner_yellow = sub[:, x0:x1 + 1]
                dark = ((inner < 110) & ~inner_yellow).mean()
                if fill > 0.72 and dark > 0.04 and bw > bh * 2.2:
                    out.append({"y0": start, "y1": y - 1, "x0": x0, "x1": x1})
            start = None
    return out


def read_frames(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path,
           "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
    n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        if n % STEP == 0:
            yield n, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        n += 1
    p.stdout.close()
    p.wait()


def analyze(path):
    colors = Counter()
    events = []          # (frame, band) für jedes Sample
    badge_rows = []

    for n, a in read_frames(path):
        m = yellow_mask(a)
        if m.sum() < 200:
            events.append((n, []))
            continue
        gray = a.mean(axis=2)
        bands = bands_from_mask(m, gray)
        if bands:
            for bd in bands:
                px = a[bd["y0"]:bd["y1"] + 1, bd["x0"]:bd["x1"] + 1][
                    m[bd["y0"]:bd["y1"] + 1, bd["x0"]:bd["x1"] + 1]]
                colors.update(map(tuple, px[::11]))
        # Badge = Band ganz oben (y < 15 % der Höhe)
        keep = []
        for bd in bands:
            if bd["y1"] < H * 0.15:
                badge_rows.append(bd)
            else:
                keep.append(bd)
        events.append((n, keep))

    # Zeitfenster bilden: aufeinanderfolgende Samples mit Boxen zusammenfassen
    windows, cur = [], None
    for n, bands in events:
        if bands:
            y0 = min(b["y0"] for b in bands)
            y1 = max(b["y1"] for b in bands)
            x0 = min(b["x0"] for b in bands)
            x1 = max(b["x1"] for b in bands)
            if cur is None:
                cur = {"f0": n, "f1": n, "y0": y0, "y1": y1, "x0": x0, "x1": x1,
                       "widths": [x1 - x0]}
            else:
                cur["f1"] = n
                cur["y0"] = min(cur["y0"], y0)
                cur["y1"] = max(cur["y1"], y1)
                cur["x0"] = min(cur["x0"], x0)
                cur["x1"] = max(cur["x1"], x1)
                cur["widths"].append(x1 - x0)
        else:
            # kurze Lücken (< 0.4 s) überbrücken, damit Ein-/Ausblenden nicht trennt
            if cur is not None and (n - cur["f1"]) > FPS * 0.4:
                windows.append(cur)
                cur = None
    if cur is not None:
        windows.append(cur)

    for w in windows:
        # Zwei Kästen direkt hintereinander verschmelzen sonst still zu
        # einem Fenster — und beim Abgleich gegen die Untertitel liest man
        # dann nur den ersten Text. Sprunghafte Breitenwechsel verraten sie.
        #
        # ACHTUNG, nur ein Hinweis, kein Beweis: Einblend-Animationen
        # treiben die Zahl nach oben, gleich breite Kästen nacheinander
        # bleiben unentdeckt (so passiert bei V1 1,8–4,4 s). Verlässlich
        # ist nur, das Fenster im Sekundentakt auszuschneiden und die
        # Texte zu lesen.
        widths = w.pop("widths")
        changes = sum(
            1 for a, b in zip(widths, widths[1:])
            if abs(b - a) > W * 0.05
        )
        w["boxCount"] = changes + 1

        w["startSec"] = round(w["f0"] / FPS, 2)
        w["endSec"] = round(w["f1"] / FPS, 2)
        w["topFrac"] = round(w["y0"] / H, 4)
        w["botFrac"] = round(w["y1"] / H, 4)
        w["leftFrac"] = round(w["x0"] / W, 4)
        w["rightFrac"] = round(w["x1"] / W, 4)
        for k in ("f0", "f1", "y0", "y1", "x0", "x1"):
            del w[k]

    badge = None
    if badge_rows:
        badge = {
            "topFrac": round(min(b["y0"] for b in badge_rows) / H, 4),
            "botFrac": round(max(b["y1"] for b in badge_rows) / H, 4),
            "leftFrac": round(min(b["x0"] for b in badge_rows) / W, 4),
            "rightFrac": round(max(b["x1"] for b in badge_rows) / W, 4),
            "samples": len(badge_rows),
        }

    top = [(f"#{r:02X}{g:02X}{b:02X}", c) for (r, g, b), c in colors.most_common(5)]
    return {"video": path.split("/")[-1], "yellowTop": top, "badge": badge, "boxes": windows}


if __name__ == "__main__":
    res = [analyze(p) for p in sys.argv[1:]]
    print(json.dumps(res, indent=2, ensure_ascii=False))
    for r in res:
        print(f"\n=== {r['video']}", file=sys.stderr)
        print(f"  Gelb: {r['yellowTop'][:3]}", file=sys.stderr)
        print(f"  Badge: {r['badge']}", file=sys.stderr)
        for w in r["boxes"]:
            multi = ("   ⚠ MEHRERE KÄSTEN (%d) — Texte einzeln lesen!"
                     % w["boxCount"]) if w["boxCount"] > 1 else ""
            print(f"  Box {w['startSec']:6.2f}-{w['endSec']:6.2f}s   "
                  f"y {w['topFrac']:.1%}-{w['botFrac']:.1%}   "
                  f"x {w['leftFrac']:.1%}-{w['rightFrac']:.1%}{multi}",
                  file=sys.stderr)
