#!/usr/bin/env python3
"""
Findet je Ad das Hook-Fenster: die Sekunden am Anfang, in denen bereits
gelber Text (ohne Kasten) im Bild steht.

Dort darf kein Untertitel gesetzt werden — sonst steht Text auf Text.
Anders als die Keyword-Kästen ist der Hook-Text nicht flächig, deshalb
zählt hier die reine Menge gelber Pixel im mittleren Bildbereich.
"""

import json
import subprocess
import sys

import numpy as np

W, H = 540, 960
FPS = 25
SCAN_SEC = 12


def yellow(a):
    r = a[..., 0].astype(np.int16)
    g = a[..., 1].astype(np.int16)
    b = a[..., 2].astype(np.int16)
    return (r > 200) & (g > 165) & (g < 240) & (b < 90) & ((r - b) > 140)


def hook_window(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-t", str(SCAN_SEC),
           "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 8)
    hits = []
    n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        a = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        # Grosszügiger Bereich: der Hook sitzt nicht immer im Mittelband —
        # in Video 2 steht er bei 23–27 % und wurde mit dem früheren
        # Fenster (30–75 %) komplett übersehen. Badge oben links und der
        # untere Rand bleiben aussen vor.
        m = yellow(a[int(H * 0.18):int(H * 0.85), :])
        m[:int(H * 0.03), :int(W * 0.45)] = False
        hits.append((n / FPS, int(m.sum())))
        n += 1
    p.stdout.close()
    p.wait()

    # zusammenhängende Läufe statt nur min/max — sonst verschmilzt
    # der Hook mit den nachfolgenden Keyword-Kästen zu einem Block
    runs, start, prev = [], None, None
    for t, c in hits:
        on = c > 900
        if on and start is None:
            start = t
        elif not on and start is not None:
            if prev - start >= 0.3:
                runs.append((round(start, 2), round(prev, 2)))
            start = None
        if on:
            prev = t
    if start is not None and prev - start >= 0.3:
        runs.append((round(start, 2), round(prev, 2)))
    return runs


def subtract_boxes(runs, boxes):
    """Läufe verwerfen, die im Wesentlichen ein Keyword-Kasten sind."""
    out = []
    for a, b in runs:
        covered = 0.0
        for bx in boxes:
            lo, hi = max(a, bx["startSec"]), min(b, bx["endSec"])
            if hi > lo:
                covered += hi - lo
        if covered < (b - a) * 0.6:
            out.append((a, b))
    return out


if __name__ == "__main__":
    ov = {}
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        ov = {v["video"]: v["boxes"] for v in json.load(open(sys.argv[1]))}
        paths = sys.argv[2:]
    else:
        paths = sys.argv[1:]

    out = {}
    for path in paths:
        name = path.split("/")[-1]
        runs = hook_window(path)
        clean = subtract_boxes(runs, ov.get(name, []))
        out[name] = ({"hookStartSec": clean[0][0], "hookEndSec": clean[-1][1]}
                     if clean else None)
        print(f"{name}\n   roh:    {runs}\n   ohne Kästen: {clean}", file=sys.stderr)
    print(json.dumps(out, indent=2, ensure_ascii=False))
