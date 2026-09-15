import subprocess, numpy as np, sys

NAS = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Steuerkanzlei Ludwig x Taxodia/02_Projekte/01_Taxodia Erklärvideo/03_Medien/01_Footage"

def raw(path, frame, fps, pix_fmt, w, h, bpc):
    t = (frame - 0.25) / fps
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", path, "-frames:v", "1",
           "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"]
    b = subprocess.run(cmd, capture_output=True, check=True).stdout
    dt = np.uint16 if bpc > 8 else np.uint8
    return np.frombuffer(b, dtype=dt)

def planes(buf, w, h, cw, ch):
    y = buf[:w*h].reshape(h, w)
    cb = buf[w*h:w*h+cw*ch].reshape(ch, cw)
    cr = buf[w*h+cw*ch:w*h+2*cw*ch].reshape(ch, cw)
    return y, cb, cr

for clip, frame in [("Kamera-B/FX3_0222", 3106), ("Kamera-A/a7MK4_20260908_0118", 3106 + 986)]:
    orig = f"{NAS}/{clip.split('/')[0]}/{clip.split('/')[1]}.MP4"
    prox = f"{NAS}/{clip.split('/')[0]}/Proxy/{clip.split('/')[1]}.mov"
    bo = raw(orig, frame, 25, "yuv422p10le", 3840, 2160, 10)
    yo, cbo, cro = planes(bo, 3840, 2160, 1920, 2160)
    bp = raw(prox, frame, 25, "yuv420p", 1920, 1080, 8)
    yp, cbp, crp = planes(bp, 1920, 1080, 960, 540)
    bp444 = raw(prox, frame, 25, "yuv444p", 1920, 1080, 8)
    yp4, _, _ = planes(bp444, 1920, 1080, 1920, 1080)
    print(clip, "Y420==Y444:", np.array_equal(yp, yp4))
    # block means 60x60 px on proxy grid
    yo2 = yo.reshape(1080, 2, 1920, 2).mean(axis=(1, 3))
    B = 30
    a = yo2[:1080//B*B, :1920//B*B].reshape(1080//B, B, 1920//B, B).mean(axis=(1, 3)).ravel()
    p = yp[:1080//B*B, :1920//B*B].astype(float).reshape(1080//B, B, 1920//B, B).mean(axis=(1, 3)).ravel()
    print("orig 10bit Y range (min/p1/p50/p99/max):", yo.min(), np.percentile(yo, [1, 50, 99]).round(1), yo.max())
    print("proxy 8bit Y range  (min/p1/p50/p99/max):", yp.min(), np.percentile(yp, [1, 50, 99]).round(1), yp.max())
    # fit p = k*a + d
    A = np.vstack([a, np.ones_like(a)]).T
    k, d = np.linalg.lstsq(A, p, rcond=None)[0]
    res = p - (k*a + d)
    print(f"fit proxy8 = {k:.5f} * orig10 + {d:.3f}   (rms {np.sqrt((res**2).mean()):.3f})")
    print("  H1 codes preserved: k=0.25, d=0 | H2 full->legal: k=219/1023=%.5f, d=16" % (219/1023))
    # chroma
    cbo2 = cbo.reshape(1080, 2, 1920).mean(axis=1)  # 1080x1920 (422 -> vertical avg)
    cbp2 = np.repeat(np.repeat(cbp, 2, 0), 2, 1).astype(float)
    a = cbo2[:1080//B*B, :1920//B*B].reshape(1080//B, B, 1920//B, B).mean(axis=(1, 3)).ravel()
    p = cbp2[:1080//B*B, :1920//B*B].reshape(1080//B, B, 1920//B, B).mean(axis=(1, 3)).ravel()
    k, d = np.linalg.lstsq(np.vstack([a, np.ones_like(a)]).T, p, rcond=None)[0]
    print(f"Cb fit proxy8 = {k:.5f} * orig10 + {d:.3f}  (H1: 0.25,0 ; H2 full->legal: {224/1023:.5f}, {128-512*224/1023:.2f})")
