"""Framegenaue Zuordnung neue Fassung -> alte Fassung (Video 3, Review 14.09.).
Graustufen 36x64 je Frame (25 fps), je neuem Frame bester alter Frame per mittlerer absoluter Differenz.
Ausgabe: Segmente mit konstantem Versatz (Δ = neu - alt) bzw. 'kein Treffer' (neues Material / Schwarz)."""
import subprocess, sys, unicodedata, json
from pathlib import Path
import numpy as np

PROJECT = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
PR = next(p for p in PROJECT.iterdir() if unicodedata.normalize("NFC", p.name) == "Prüfen")
ALT = next(p for p in PR.iterdir() if p.name.endswith("_720p.mp4"))
NEU = next(p for p in PR.iterdir() if p.name.endswith("_NEU.mov"))
W, H = 36, 64

def frames(path):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps=25,scale={W}:{H}:flags=area,format=gray",
           "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H * W).astype(np.float32)
    return a

alt, neu = frames(ALT), frames(NEU)
print(f"alt {len(alt)} Frames, neu {len(neu)} Frames")
best, dist, second = [], [], []
for i in range(0, len(neu), 64):
    chunk = neu[i:i+64]
    d = np.abs(chunk[:, None, :] - alt[None, :, :]).mean(axis=2)   # (64, n_alt)
    idx = d.argmin(axis=1)
    best.extend(idx.tolist()); dist.extend(d[np.arange(len(chunk)), idx].tolist())
best = np.array(best); dist = np.array(dist)
np.save(PROJECT / "_intern/review-v3-neu/framematch_best.npy", best)
np.save(PROJECT / "_intern/review-v3-neu/framematch_dist.npy", dist)
luma = neu.mean(axis=1)
TH = 6.0
segs = []
cur = None
for k in range(len(neu)):
    ok = dist[k] < TH and luma[k] > 8
    off = k - best[k] if ok else None
    key = ("match", off) if ok else ("none", None)
    if cur and cur["key"][0] == key[0] and (key[0] == "none" or abs(cur["key"][1] - off) <= 1):
        cur["end"] = k; cur["d"].append(dist[k])
    else:
        if cur: segs.append(cur)
        cur = {"key": key, "start": k, "end": k, "d": [dist[k]]}
segs.append(cur)
out = []
for s in segs:
    a, b = s["start"] / 25, (s["end"] + 1) / 25
    if s["key"][0] == "match":
        off = s["key"][1] / 25
        line = f"neu {a:6.2f}–{b:6.2f} ({b-a:5.2f}s) = alt {a-off:6.2f}–{b-off:6.2f}   Δ(neu−alt) {off:+6.2f}s   MAD Ø{np.mean(s['d']):.1f}"
    else:
        dark = luma[s['start']:s['end']+1].mean()
        line = f"neu {a:6.2f}–{b:6.2f} ({b-a:5.2f}s) = KEIN TREFFER in alt   (Luma Ø{dark:.0f}, MAD Ø{np.mean(s['d']):.1f})"
    out.append(line); print(line)
(PROJECT / "_intern/review-v3-neu/framematch.txt").write_text("\n".join(out))
# Welche alten Frames kommen in neu gar nicht mehr vor?
used = np.zeros(len(alt), bool)
for k in range(len(neu)):
    if dist[k] < TH and luma[k] > 8: used[best[k]] = True
print("\n--- alte Abschnitte, die in neu NICHT mehr vorkommen (≥0,2 s):")
run = None
for j in range(len(alt) + 1):
    miss = j < len(alt) and not used[j]
    if miss and run is None: run = j
    if not miss and run is not None:
        if (j - run) >= 5: print(f"alt {run/25:6.2f}–{j/25:6.2f} ({(j-run)/25:5.2f}s)")
        run = None
