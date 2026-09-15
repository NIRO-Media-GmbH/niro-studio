"""Neue B-Roll-Shots der Fassung NEU in Quellclips (Proxys) wiederfinden -> Standort-Nachweis."""
import json, subprocess, unicodedata, os
from pathlib import Path
import numpy as np, cv2
P = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
IDX = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/autocut/broll_index.json")
PR = next(p for p in P.iterdir() if unicodedata.normalize("NFC", p.name) == "Prüfen")
NEU = next(p for p in PR.iterdir() if p.name.endswith("_NEU.mov"))
SW, SH = 480, 270
def feat(img):
    g = cv2.GaussianBlur(img, (0, 0), 1.0).astype(np.float32)
    return cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
def grab(path, fps, w, h, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + ["-i", str(path)] + (["-t", str(t)] if t else []) + \
          ["-vf", f"fps={fps},scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)
targets = {"Christian Profil Untersicht 34,7 s": 34.70, "CT Lunge 35,6 s": 35.60, "ABIOMED-Monitor 40,9 s": 40.90, "Hand Bedienfeld 41,7 s": 41.70}
tfeat = {}
for name, t in targets.items():
    fr = grab(NEU, 25, 270, 480, ss=t, t=0.04)[0]
    tfeat[name] = [(h, feat(cv2.resize(fr, (int(round(h*9/16)), h), interpolation=cv2.INTER_AREA))) for h in range(270, 110, -12)]
clips = [c for c in json.load(open(IDX))["clips"]
         if (c["standort"] == "Standort 1" and c["ordner"] in ("Röntgenanalyse", "Special Gerät", "Intensivstation", "Fahrrad", "Verwaltung"))
         or (c["standort"] == "Standort 2" and c["ordner"] in ("Intensivstation", "Beatmungszimmer"))]
print(len(clips), "Kandidaten-Clips")
best = {n: [] for n in targets}
for c in clips:
    src = c["proxy"] if c.get("proxy") and os.path.exists(c["proxy"]) else c["path"]
    fr = grab(src, 2, SW, SH)
    if len(fr) == 0: continue
    ff = [feat(x) for x in fr]
    for n in targets:
        top = (-1, 0, 0)
        for j, f in enumerate(ff):
            for h, tf in tfeat[n]:
                mx = cv2.matchTemplate(f, tf, cv2.TM_CCOEFF_NORMED).max()
                if mx > top[0]: top = (mx, j / 2, h)
        best[n].append((top[0], c["standort"], c["ordner"], c["datei"], top[1], c["beschreibung_kurz"]))
for n in targets:
    print(f"\n## {n}")
    for s, st, o, dt, tt, b in sorted(best[n], reverse=True)[:4]:
        print(f"  Score {s:.3f} | {st} | {o:<16} | {dt:<24} @ {tt:5.1f}s | {b[:70]}")
