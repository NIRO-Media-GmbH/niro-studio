import json, subprocess, sys
from pathlib import Path
from multiprocessing import Pool
import numpy as np, cv2
sys.path.insert(0, "_intern/review-testcut")
import shotsource as S
if __name__ == "__main__":
    W = S.W; meta = json.load(open(W/"bank_meta.json"))
    segs = [(5.84, 6.56), (6.56, 6.96), (6.96, 7.24), (23.04, 24.92), (39.08, 40.72), (40.72, 42.28), (60.56, 62.00), (63.48, 64.80), (64.80, 66.92), (91.40, 92.80), (95.08, 96.04)]
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4)); SRC = S.CH/"Material/Testcut/MEK Test1.mov"
    queries = []
    for a, b in segs:
        for frac in (0.3, 0.7):
            t = a + (b - a) * frac
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(SRC), "-frames:v", "1", "-vf", f"scale={S.BW}:{S.BH}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
            queries.append((round(t, 2), clahe.apply(np.frombuffer(fr, np.uint8).reshape(S.BH, S.BW))))
    with Pool(14, initializer=S._init, initargs=(meta,)) as pool:
        res = dict(pool.imap_unordered(S.match, queries))
    bym = {m["key"]: m for m in meta}
    for a, b in segs:
        for t in sorted(t for t in res if a <= t < b):
            top = res[t]
            sc, key, st, zs = top[0]; m = bym[key]
            print(f"{a:6.2f}–{b:6.2f} @{t:6.2f}: {sc:.3f} {m['standort']:<11} {m['ordner']:<34} {m['datei']:<26} @{st:6.1f}s | 2.: {top[1][1]} {top[1][0]:.3f}")
