"""Nachprüfung unklarer Interview-Einstellungen: beide Kameras (FX3 + a7) und Zoomstufen, framegenaue Suche um die ton-synchrone Erwartung."""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, "_intern/review-testcut")
CH = Path("."); W = CH/"_intern/review-testcut"; CUT = CH/"Material/Testcut/MEK Test1.mov"
import importlib.util
spec = importlib.util.spec_from_file_location("sca", W/"synccheck_all.py")
src_txt = (W/"synccheck_all.py").read_text().split("report = []")[0]   # nur Setup (Tongitter, Hilfsfunktionen)
g = {}; exec(src_txt, g)
audio_offset, grab, meta, offs = g["audio_offset"], g["grab"], g["meta"], g["offs"]
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
pairs = {"FX3_9557": ["a7MK4_20260624_9889"], "FX3_9650": ["a7MK4_20260624_9936"], "FX3_9994": ["a7MK4_20260702_9985"], "FX3_9993": ["a7MK4_20260702_9984"],
         "FX3_9558": ["a7MK4_20260624_9890"], "FX3_9554": ["a7MK4_20260624_9888"], "FX3_9649": ["a7MK4_20260624_9935", "a7MK4_20260624_9934"],
         "FX3_9992": ["a7MK4_20260702_9983"], "FX3_9651": ["a7MK4_20260624_9937"], "FX3_9981": ["a7MK4_20260702_9966"], "FX3_9982": ["a7MK4_20260702_9967"]}
shots = [r for r in json.load(open(W/"shotsource.json")) if r["ordner"].startswith("Interview")]
def keyfor(cam):
    return next(k for k in meta if k.endswith(cam))
out = []
for s in shots:
    a, b = s["von"], s["bis"]
    ts = np.arange(a + 0.08, b - 0.08, 0.16)
    info = [audio_offset(t) for t in ts]
    stems = [x[1] for x in info if x[1]]
    if not stems: out.append(f"{a:6.2f}–{b:6.2f} keine Tonreferenz"); continue
    stem = max(set(stems), key=stems.count)
    cams = [stem] + pairs.get(stem, [])
    cutfr = grab(CUT, a, b - a, 320, 180)
    best_overall = None
    for cam in cams:
        k = keyfor(cam); m = meta[k]
        exp = []
        for t, (nm, st, off) in zip(ts, info):
            if off is None or st != stem: continue
            e = t + off if cam.startswith("FX3") else t + off - offs[f"{stem}|{cam}"]
            exp.append((t, e))
        if not exp: continue
        lo = min(e for _, e in exp) - 2.5; hi = max(e for _, e in exp) + 2.5
        src = grab(m["path"], lo, hi - lo, 320, 180)
        if len(src) == 0: continue
        srcf = [clahe.apply(x).astype(np.float32) for x in src]
        for zoom in (1.0, 1.1, 1.25, 1.4, 1.6):
            res = []
            for t, e in exp:
                kk = int(round((t - a) * 25))
                if kk >= len(cutfr): continue
                q = clahe.apply(cutfr[kk])
                tw, th = int(288 / zoom), int(162 / zoom)
                tp = cv2.resize(q[9:171, 16:304], (tw, th), interpolation=cv2.INTER_AREA).astype(np.float32)
                sc = [cv2.matchTemplate(f, tp, cv2.TM_CCOEFF_NORMED).max() for f in srcf]
                j = int(np.argmax(sc)); res.append((lo + j/25 - e, sc[j]))
            if not res: continue
            d = np.array([r[0] for r in res]); scs = np.array([r[1] for r in res])
            cand = (scs.mean(), cam, zoom, float(np.median(d)), float(np.mean(np.abs(d - np.median(d)) <= 0.081) * 100), len(d))
            if best_overall is None or cand[0] > best_overall[0]: best_overall = cand
    sc, cam, zoom, md, cons, n = best_overall
    line = f"{a:6.2f}–{b:6.2f} {stem}: beste Kamera {cam:<22} Zoom {zoom}  Median Δ {md:+5.2f}s  konsistent {cons:3.0f}%  Score Ø{sc:.2f} (n={n})"
    out.append(line); print(line, flush=True)
(W/"synccheck_retry.txt").write_text("\n".join(out))
