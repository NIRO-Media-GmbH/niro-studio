"""Ein Decode-Durchlauf je Film: Metriken je Sample (5 fps) + Vorschaubilder.

Aufruf: analyze_film.py <label> <quelldatei> <metrik-ordner> <frame-ordner>
Sample n entspricht Quellbild 5·n (25 fps). Ausgabe:
  <metrik-ordner>/<label>-samples.npy   float32 [t, luma, sharp, sharp_center, clip_hi, clip_lo, motion, sat]
  <metrik-ordner>/<label>-small.npy     uint8   [n, 36, 64] Graustufen für Struktur-Vergleiche
  <frame-ordner>/<label>/<n:06d>.jpg    640×360
"""
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

W, H, FPS = 960, 540, 5
label, src, mdir, fdir = sys.argv[1:5]
os.makedirs(mdir, exist_ok=True)
os.makedirs(os.path.join(fdir, label), exist_ok=True)

cmd = ["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox", "-i", src, "-an",
       "-vf", f"fps={FPS},scale={W}:{H}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**8)
size = W * H * 3
rows, smalls = [], []
prev = None
t0 = time.time()
n = 0
while True:
    buf = proc.stdout.read(size)
    if len(buf) < size:
        break
    img = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    f = img.astype(np.float32)
    g = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    sharp = float(lap.var())
    sharp_c = float(lap[H // 4:3 * H // 4, W // 4:3 * W // 4].var())
    sat = float((f.max(axis=2) - f.min(axis=2)).mean())
    small = np.asarray(Image.fromarray(g.astype(np.uint8)).resize((64, 36), Image.BILINEAR), np.uint8)
    motion = float(np.abs(small.astype(np.float32) - prev).mean()) if prev is not None else 0.0
    rows.append([n / FPS, float(g.mean()), sharp, sharp_c, float((g > 250).mean()), float((g < 6).mean()), motion, sat])
    smalls.append(small)
    Image.fromarray(img).resize((640, 360), Image.BILINEAR).save(os.path.join(fdir, label, f"{n:06d}.jpg"), quality=82)
    prev = small.astype(np.float32)
    n += 1
    if n % 1500 == 0:
        print(f"{label}: {n} Samples ({n / FPS / 60:.1f} min Quelle) nach {time.time() - t0:.0f} s", flush=True)
proc.wait()
np.save(os.path.join(mdir, f"{label}-samples.npy"), np.array(rows, np.float32))
np.save(os.path.join(mdir, f"{label}-small.npy"), np.stack(smalls))
print(f"{label}: fertig, {n} Samples, {time.time() - t0:.0f} s, ffmpeg exit {proc.returncode}", flush=True)
