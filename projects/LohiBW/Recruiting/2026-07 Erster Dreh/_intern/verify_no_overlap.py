#!/usr/bin/env python3
"""
Endabnahme: prüft am gerenderten Ergebnis, dass Untertitel und die
bestehenden Keyword-Kästen sich nie überschneiden.

Nicht der Plan wird geprüft, sondern die Alphaspur der fertigen Overlays —
Frame für Frame gegen die gemessenen Kastenfenster aus overlays.json.
Ein Treffer heißt: an dieser Stelle liegt Untertiteltext im selben
vertikalen Bereich wie ein Kasten.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

CHARGE = Path(__file__).resolve().parents[1]
INTERN = CHARGE / "_intern"
ALPHA = INTERN / "work" / "alpha"

W, H = 270, 480          # Alpha grob abtasten reicht für Lagevergleich
FPS = 25
MARGIN = 0.005           # 0,5 % Toleranz für Schattenausläufer


def alpha_rows(path):
    """Je Frame die vertikale Ausdehnung des Untertiteltexts (Anteil 0-1)."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path),
           "-vf", f"alphaextract,scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 8)
    n = 0
    while True:
        buf = p.stdout.read(W * H)
        if len(buf) < W * H:
            break
        a = np.frombuffer(buf, np.uint8).reshape(H, W)
        # nur Glyphenkörper, weicher Schatten bleibt aussen vor
        rows = np.nonzero((a > 170).sum(axis=1) > 0)[0]
        yield n, (rows.min() / H, rows.max() / H) if len(rows) else None
        n += 1
    p.stdout.close()
    p.wait()


def main():
    ov = {v["video"]: v for v in json.loads((INTERN / "overlays.json").read_text())}
    titles = sorted(ov.keys())

    total_hits = 0
    for i, name in enumerate(titles, start=1):
        mov = ALPHA / f"untertitel-{i}.mov"
        if not mov.exists():
            sys.exit(f"fehlt: {mov}")
        boxes = ov[name]["boxes"]

        hits, frames_with_text = [], 0
        for n, span in alpha_rows(mov):
            if span is None:
                continue
            frames_with_text += 1
            t = n / FPS
            top, bot = span
            for b in boxes:
                if not (b["startSec"] <= t <= b["endSec"]):
                    continue
                if bot + MARGIN < b["topFrac"] or top - MARGIN > b["botFrac"]:
                    continue
                hits.append((t, top, bot, b))

        status = "SAUBER" if not hits else f"{len(hits)} ÜBERSCHNEIDUNGEN"
        print(f"Video {i}: {frames_with_text:4d} Frames mit Untertitel — {status}")
        for t, top, bot, b in hits[:6]:
            print(f"    {t:6.2f}s  Text {top:.1%}–{bot:.1%}  vs. Kasten "
                  f"{b['topFrac']:.1%}–{b['botFrac']:.1%}")
        total_hits += len(hits)

    print()
    if total_hits:
        sys.exit(f"FEHLGESCHLAGEN — {total_hits} Überschneidungen")
    print("ABNAHME BESTANDEN — keine einzige Überschneidung in allen vier Ads")


if __name__ == "__main__":
    main()
