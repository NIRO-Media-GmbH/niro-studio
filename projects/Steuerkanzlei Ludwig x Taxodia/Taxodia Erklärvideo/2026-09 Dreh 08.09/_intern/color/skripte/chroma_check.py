import numpy as np
import importlib.util, sys
spec = importlib.util.spec_from_file_location("lc", "levels_check.py")
src = open("levels_check.py").read().split("for clip, frame in")[0]
ns = {}; exec(src, ns)
raw, planes, NAS = ns["raw"], ns["planes"], ns["NAS"]
for clip, frame in [("Kamera-B/FX3_0222", 12048), ("Kamera-A/a7MK4_20260908_0118", 12048 + 986)]:
    d, s = clip.split("/")
    bo = raw(f"{NAS}/{d}/{s}.MP4", frame, 25, "yuv422p10le", 3840, 2160, 10)
    yo, cbo, cro = planes(bo, 3840, 2160, 1920, 2160)
    bp = raw(f"{NAS}/{d}/Proxy/{s}.mov", frame, 25, "yuv444p", 1920, 1080, 8)
    yp, cbp, crp = planes(bp, 1920, 1080, 1920, 1080)
    B = 40
    def blk(a):
        a = a.astype(float); h, w = a.shape
        return a[:h//B*B, :w//B*B].reshape(h//B, B, w//B, B).mean(axis=(1, 3)).ravel()
    for nm, o, p in [("Cb", cbo.reshape(1080, 2, 1920).mean(1), cbp), ("Cr", cro.reshape(1080, 2, 1920).mean(1), crp)]:
        a = blk(o) - 512; q = blk(p) - 128
        # total least squares slope through origin-centred data
        A = np.vstack([a - a.mean(), q - q.mean()])
        w, v = np.linalg.eigh(A @ A.T); k_tls = v[1, 1] / v[0, 1]
        sel = np.abs(a) > np.percentile(np.abs(a), 80)
        k_ratio = np.median(q[sel] / a[sel])
        print(clip, nm, f"TLS slope {k_tls:.4f}  median ratio (top20% |chroma|) {k_ratio:.4f}   224/1023={224/1023:.4f} 219/1023={219/1023:.4f}  std orig {a.std():.2f}")
