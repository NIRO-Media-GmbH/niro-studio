#!/usr/bin/env python3
"""
Vollständige Erfassung ALLER gelben Kästen — im ganzen Bild, nicht nur
im Untertitelband.

Hintergrund: `analyze_overlays.py` sucht nur, was den Untertitel räumlich
stört. Für die Dopplungsprüfung ist das zu eng — ein Kasten am oberen
Bildrand doppelt inhaltlich genauso (Video 2 öffnet mit „HAST DU LETZTES
JAHR" bei 23 % Höhe, während der Untertitel denselben Satz zeigt).

Deshalb hier bewusst lockerer: geringere Füllschwelle, damit auch
einblendende Kästen erfasst werden. Falsch-Positive sind in Kauf zu
nehmen — die Texte werden ohnehin von Hand gelesen.

Aufruf: python scan_all_boxes.py <video.mp4> [...]
"""

import json
import subprocess
import sys

import numpy as np

W, H = 540, 960
STEP = 3
FPS = 25

# Logo-Badge oben links ausklammern (weißer Kasten mit gelbem Wappen)
BADGE = {"y": 0.16, "x": 0.42}


def yellow(a):
    r = a[..., 0].astype(np.int16)
    g = a[..., 1].astype(np.int16)
    b = a[..., 2].astype(np.int16)
    return (r > 195) & (g > 160) & (g < 245) & (b < 100) & ((r - b) > 130)


def dark(a):
    """Dunkle Kästen mit hellem Text.

    Dritte Animationsart neben Gelb-Kasten und Hook: Video 2 zeigt bei
    27–30 s eine gestapelte Liste in fast schwarzen Kästen. Wer nur nach
    Gelb sucht, sieht sie nicht.
    """
    r = a[..., 0].astype(np.int16)
    g = a[..., 1].astype(np.int16)
    b = a[..., 2].astype(np.int16)
    mx = np.maximum(np.maximum(r, g), b)
    return (mx < 70) & ((mx - np.minimum(np.minimum(r, g), b)) < 30)


def boxes_in_frame(a, kind="yellow"):
    m = (yellow(a) if kind == "yellow" else dark(a))
    m[: int(H * BADGE["y"]), : int(W * BADGE["x"])] = False
    gray = a.mean(axis=2)
    if kind == "dark":
        # heller Text im dunklen Kasten statt dunkler im hellen
        gray = 255 - gray

    rows = m.sum(axis=1)
    hot = rows > (W * 0.05)
    out, start = [], None
    for y, v in enumerate(list(hot) + [False]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= 3:
                sub = m[start:y]
                cols = np.nonzero(sub.sum(axis=0) > 0)[0]
                x0, x1 = int(cols.min()), int(cols.max())
                bw, bh = x1 - x0 + 1, y - start
                fill = sub[:, x0:x1 + 1].mean()
                inner = gray[start:y, x0:x1 + 1]
                text_frac = ((inner < 120) & ~sub[:, x0:x1 + 1]).mean()
                if fill > 0.55 and bw > bh * 1.8 and text_frac > 0.02:
                    out.append((start / H, (y - 1) / H, x0 / W, x1 / W))
            start = None
    return out


def scan(path, kind="yellow"):
    cmd = ["ffmpeg", "-v", "error", "-i", path,
           "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
    hits, n = [], 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        if n % STEP == 0:
            a = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            for bx in boxes_in_frame(a, kind):
                hits.append((n / FPS, bx))
        n += 1
    p.stdout.close()
    p.wait()

    # nach vertikaler Lage gruppieren, damit oben und unten getrennt bleiben
    windows = []
    for t, (y0, y1, x0, x1) in hits:
        cur = None
        for w in windows:
            if abs(w["topFrac"] - y0) < 0.05 and t - w["endSec"] < 0.5:
                cur = w
                break
        if cur:
            cur["endSec"] = t
            cur["botFrac"] = max(cur["botFrac"], y1)
            cur["leftFrac"] = min(cur["leftFrac"], x0)
            cur["rightFrac"] = max(cur["rightFrac"], x1)
        else:
            windows.append({"startSec": t, "endSec": t, "topFrac": y0,
                            "botFrac": y1, "leftFrac": x0, "rightFrac": x1})

    return [w for w in windows if w["endSec"] - w["startSec"] >= 0.25]


if __name__ == "__main__":
    kinds = ["yellow", "dark"]
    res = {}
    for path in sys.argv[1:]:
        name = path.split("/")[-1]
        res[name] = {}
        print(f"\n=== {name}", file=sys.stderr)
        for kind in kinds:
            ws = sorted(scan(path, kind), key=lambda w: w["startSec"])
            res[name][kind] = ws
            label = "GELB" if kind == "yellow" else "DUNKEL"
            print(f"  -- {label} ({len(ws)})", file=sys.stderr)
            for w in ws:
                print(f"     {w['startSec']:6.2f}–{w['endSec']:6.2f}s   "
                      f"y {w['topFrac']:.1%}–{w['botFrac']:.1%}   "
                      f"x {w['leftFrac']:.1%}–{w['rightFrac']:.1%}",
                      file=sys.stderr)
    print(json.dumps(res, indent=2, ensure_ascii=False))
