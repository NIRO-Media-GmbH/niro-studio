"""Lippensync je Frame (korrigierte Passagenwahl): Δ-Verlauf über die Einstellung, beide Kameras, Zoom je Frame frei."""
import json, subprocess
from pathlib import Path
import numpy as np, cv2
CH = Path("."); W = CH/"_intern/review-testcut"; CUT = CH/"Material/Testcut/MEK Test1.mov"
g = {}; exec((W/"synccheck_all.py").read_text().split("def audio_offset")[0], g)
grids, grab, meta, offs = g["grids"], None, g["meta"], g["offs"]
def grab(path, ss, dur, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(ss,0):.3f}", "-t", f"{dur:.3f}", "-i", str(path), "-vf", f"fps=25,scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)
def audio_offset(t):
    inside = [x for x in grids if x[1] <= t <= x[2] and x[4]]
    cand = inside or sorted([x for x in grids if x[4]], key=lambda x: min(abs(t - x[1]), abs(t - x[2])))[:1]
    name, a, b, stem, gr = cand[0]
    tt = np.array([p[0] for p in gr]); oo = np.array([p[1] for p in gr])
    return name, stem, float(oo[np.argmin(np.abs(tt - t))])
pairs = {"FX3_9557": ["a7MK4_20260624_9889"], "FX3_9650": ["a7MK4_20260624_9936"], "FX3_9994": ["a7MK4_20260702_9985"], "FX3_9993": ["a7MK4_20260702_9984"],
         "FX3_9558": ["a7MK4_20260624_9890"], "FX3_9554": ["a7MK4_20260624_9888"], "FX3_9649": ["a7MK4_20260624_9935", "a7MK4_20260624_9934"],
         "FX3_9992": ["a7MK4_20260702_9983"], "FX3_9651": ["a7MK4_20260624_9937"], "FX3_9981": ["a7MK4_20260702_9966"], "FX3_9982": ["a7MK4_20260702_9967"]}
keyfor = lambda cam: next(k for k in meta if k.endswith(cam))
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
shots = [r for r in json.load(open(W/"shotsource.json")) if r["ordner"].startswith("Interview")]
summary = []
for s in shots:
    a, b = s["von"], s["bis"]
    ts = np.arange(a + 0.04, b - 0.04, 0.12)
    info = [audio_offset(t) for t in ts]
    stem = max(set(x[1] for x in info), key=[x[1] for x in info].count)
    cutfr = grab(CUT, a, b - a, 320, 180)
    # Kamera wählen: Mittelframe gegen beide Kameras bei erwarteter Zeit ±3 s, Zoom 1.0–1.6
    tm = (a + b) / 2; _, _, om = audio_offset(tm)
    best = None
    for cam in [stem] + pairs[stem]:
        e = tm + om - (0 if cam.startswith("FX3") else offs[f"{stem}|{cam}"])
        src = grab(meta[keyfor(cam)]["path"], e - 3, 6, 320, 180)
        if len(src) == 0: continue
        srcf = [clahe.apply(x).astype(np.float32) for x in src]
        q = clahe.apply(cutfr[min(len(cutfr)-1, int((tm - a) * 25))])
        for zoom in (1.0, 1.1, 1.25, 1.4, 1.6, 1.8):
            tp = cv2.resize(q[9:171, 16:304], (int(288/zoom), int(162/zoom)), interpolation=cv2.INTER_AREA).astype(np.float32)
            sc = max(cv2.matchTemplate(f, tp, cv2.TM_CCOEFF_NORMED).max() for f in srcf)
            if best is None or sc > best[0]: best = (sc, cam, zoom)
    sc0, cam, zoom = best
    exp = [(t, t + off - (0 if cam.startswith("FX3") else offs[f"{stem}|{cam}"])) for t, (_, st, off) in zip(ts, info)]
    lo = min(e for _, e in exp) - 3; hi = max(e for _, e in exp) + 3
    src = grab(meta[keyfor(cam)]["path"], lo, hi - lo, 320, 180); srcf = [clahe.apply(x).astype(np.float32) for x in src]
    rows = []
    for t, e in exp:
        k = int(round((t - a) * 25))
        if k >= len(cutfr): continue
        q = clahe.apply(cutfr[k]); bestf = (-1, 0)
        for zz in sorted({max(1.0, zoom - 0.1), zoom, zoom + 0.1}):
            tp = cv2.resize(q[9:171, 16:304], (int(288/zz), int(162/zz)), interpolation=cv2.INTER_AREA).astype(np.float32)
            sc = [cv2.matchTemplate(f, tp, cv2.TM_CCOEFF_NORMED).max() for f in srcf]
            j = int(np.argmax(sc))
            if sc[j] > bestf[0]: bestf = (sc[j], j)
        rows.append((t, lo + bestf[1]/25 - e, bestf[0]))
    d = np.array([r[1] for r in rows]); scs = np.array([r[2] for r in rows])
    good = np.abs(d) <= 0.081
    line = f"{a:6.2f}–{b:6.2f} {stem} Kamera {cam} Zoom {zoom}: synchron {good.mean()*100:3.0f}% | Score Ø{scs.mean():.2f}"
    bad = [r for r in rows if abs(r[1]) > 0.081 and r[2] > 0.8]
    if bad:
        line += " | abweichend: " + ", ".join(f"{r[0]:.2f}s Δ{r[1]:+.2f}" for r in bad[:8])
    summary.append(line); print(line, flush=True)
(W/"synccheck_detail.txt").write_text("\n".join(summary))
