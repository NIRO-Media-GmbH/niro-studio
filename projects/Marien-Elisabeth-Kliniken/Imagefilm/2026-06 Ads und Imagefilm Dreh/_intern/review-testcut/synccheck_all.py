"""Lippensync aller Interview-Einstellungen im Testcut: Tonversatz per Kreuzkorrelation gegen FX3, Bild framegenau im Kamera-Proxy suchen."""
import json, subprocess
from pathlib import Path
import numpy as np, cv2
CH = Path("."); W = CH/"_intern/review-testcut"
CUT = CH/"Material/Testcut/MEK Test1.mov"
idx = {r["name"].rsplit(".",1)[0]: r for r in json.load(open(CH/"_intern/transcripts_index.json"))}
meta = {m["key"]: m for m in json.load(open(W/"bank_meta.json"))}
offs = json.load(open(W/"cam_offsets.json"))
shots = [r for r in json.load(open(W/"shotsource.json")) if r["ordner"].startswith("Interview")]
passages = [("Sandra", 20.2, 26.3, "FX3_9557", 200, 230), ("Zoran", 28.3, 33.2, "FX3_9650", 290, 315), ("Ramona", 34.1, 39.9, "FX3_9994", 455, 475),
            ("Jessi", 40.9, 47.7, "FX3_9993", 310, 330), ("Marina", 48.2, 51.8, "FX3_9558", 208, 226), ("Martina", 53.4, 66.4, "FX3_9554", 315, 340),
            ("Simona", 67.3, 73.6, "FX3_9649", 470, 490), ("Alina", 77.6, 87.0, "FX3_9992", 390, 418), ("Christian", 88.1, 96.4, "FX3_9651", 168, 192),
            ("Ramona", 96.4, 103.6, "FX3_9994", 170, 195), ("Johanna", 103.6, 110.9, "FX3_9981", 212, 236), ("Marcel", 111.9, 122.1, "FX3_9982", 440, 464),
            ("Katja", 123.1, 130.9, "FX3_9649", 495, 520)]
SR = 16000
def pcm(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.3f}"] if ss is not None else []) + ["-i", str(path)] + (["-t", f"{t:.3f}"] if t else []) + ["-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)
cut = pcm(CUT)
grids = []
for name, a, b, stem, sa, sb in passages:
    src = pcm(idx[stem]["path"], sa, sb - sa); c2 = np.concatenate([[0], np.cumsum(src**2)]); g = []
    for t in np.arange(a, b - 0.4, 0.1):
        seg = cut[int(t*SR):int((t+0.4)*SR)]
        if np.linalg.norm(seg) < 1e-3: continue
        n = 1 << int(np.ceil(np.log2(len(src) + len(seg))))
        corr = np.fft.irfft(np.fft.rfft(src, n) * np.fft.rfft(seg[::-1], n), n)[len(seg)-1:len(src)]
        en = np.sqrt(c2[len(seg):len(seg)+len(corr)] - c2[:len(corr)]) * np.linalg.norm(seg) + 1e-12
        nc = corr / en; k = int(np.argmax(nc))
        if nc[k] > 0.6: g.append((t, sa + k/SR - t))
    grids.append((name, a, b, stem, g))
def audio_offset(t):
    for name, a, b, stem, g in grids:
        if a - 1.5 <= t <= b + 3.5 and g:
            tt = np.array([x[0] for x in g]); oo = np.array([x[1] for x in g])
            return name, stem, float(oo[np.argmin(np.abs(tt - t))])
    return None, None, None
def grab(path, ss, dur, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(ss,0):.3f}", "-t", f"{dur:.3f}", "-i", str(path), "-vf", f"fps=25,scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
report = []
for s in shots:
    a, b = s["von"], s["bis"]; key = s["key"]; m = meta[key]
    cam = key.split("_", 2)[2]  # FX3_9557 oder a7MK4_...
    ts = np.arange(a + 0.08, b - 0.08, 0.16)
    exp = []
    for t in ts:
        name, stem, off = audio_offset(t)
        if off is None: exp.append(None); continue
        fx_time = t + off
        if cam.startswith("FX3"):
            if cam != stem: exp.append(("CAMERA≠AUDIO", cam, stem)); continue
            exp.append(fx_time)
        else:
            k = f"{stem}|{cam}"
            if k not in offs: exp.append(("KEIN VERSATZ", cam, stem)); continue
            exp.append(fx_time - offs[k])
    valid = [(t, e) for t, e in zip(ts, exp) if isinstance(e, float)]
    if not valid:
        report.append(f"{a:6.2f}–{b:6.2f} {cam:<22} keine Tonreferenz ({exp[:1]})"); continue
    lo = min(e for _, e in valid) - 2.5; hi = max(e for _, e in valid) + 2.5
    src = grab(m["path"], lo, hi - lo, 320, 180)
    srcf = [clahe.apply(x).astype(np.float32) for x in src]
    cutfr = grab(CUT, a, b - a, 320, 180)
    deltas = []
    for t, e in valid:
        k = int(round((t - a) * 25))
        if k >= len(cutfr): continue
        q = clahe.apply(cutfr[k]); tp = q[9:171, 16:304].astype(np.float32)
        scores = [cv2.matchTemplate(f, tp, cv2.TM_CCOEFF_NORMED).max() for f in srcf]
        j = int(np.argmax(scores)); found = lo + j / 25
        deltas.append((found - e, scores[j]))
    d = np.array([x[0] for x in deltas]); sc = np.array([x[1] for x in deltas])
    ok = np.mean(np.abs(d - np.median(d)) <= 0.081) * 100
    line = f"{a:6.2f}–{b:6.2f} {cam:<22} Median Δ {np.median(d):+5.2f}s  konsistent {ok:3.0f}%  Score Ø{sc.mean():.2f}  (n={len(d)})"
    report.append(line); print(line, flush=True)
(W/"synccheck_all.txt").write_text("\n".join(report))
