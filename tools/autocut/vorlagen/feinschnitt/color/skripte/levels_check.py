"""Vorlage (Stand 15.09.2026): Pegel-Vorprüfung Proxy ↔ Original — liefert der Proxy wirklich S-Log3-Codewerte CV/1023?

Aufruf: tools/autocut/venv/bin/python _intern/color/skripte/levels_check.py   (nur lesen, Ausgabe auf stdout)
Wann: bei neuen Kameras, Codecs oder Proxy-Einstellungen, bevor die Analyse (extract.py …) läuft — colorlib.yuv_to_rgb setzt das
Ergebnis voraus. Je Probe (Clip, Frame) Original (3840×2160, 4:2:2 10 Bit) und Proxy (<Ordner>/Proxy/<Clip>.mov, 1920×1080 8 Bit)
dekodieren, 60×60-px-Blockmittel vergleichen und linear fitten: Y8 = k · Y10 + d, ebenso Cb.
Deutung: H1 Codes erhalten (k = 0,25, d = 0) | H2 Full → Legal (k = 219/1023 = 0,21408, d = 16; Chroma 224/1023, 128 − 512·224/1023).
Befund 15.09. (Referenz, FX3 und a7 IV): H2 mit rms 0,08 → Proxy als TV-Range dekodiert = CV/1023; Chroma ca. 2 % flacher.
Ausgabe je Probe: Y420 == Y444, Y-Spannen Original/Proxy (min/p1/p50/p99/max), Fit-Werte Y und Cb.
Herkunft: Taxodia-Session, Scratchpad color/levels_check.py
"""
import subprocess, numpy as np, sys

# ── ANPASSEN je Charge ─────────────────────────────
NAS = "<Footage-Ordner der Originale>"  # Ordner mit den Kamera-Unterordnern (darin Original-MP4 und Proxy/<Clip>.mov), ohne / am Ende
PROBEN = [  # (Kamera-Ordner/Clip ohne Endung, Quellframe); zeitgleiche Probe der Zweitkamera = Frame + Sync-Versatz (sync.json)
    # ("Kamera-B/FX3_0001", 3106),
]
FPS = 25  # Bildrate der Originale in fps (Zeitstempel aus dem Frame) — Standard (15.09.)
# ── Ende ANPASSEN ──────────────────────────────────

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

for clip, frame in PROBEN:
    orig = f"{NAS}/{clip.split('/')[0]}/{clip.split('/')[1]}.MP4"
    prox = f"{NAS}/{clip.split('/')[0]}/Proxy/{clip.split('/')[1]}.mov"
    bo = raw(orig, frame, FPS, "yuv422p10le", 3840, 2160, 10)
    yo, cbo, cro = planes(bo, 3840, 2160, 1920, 2160)
    bp = raw(prox, frame, FPS, "yuv420p", 1920, 1080, 8)
    yp, cbp, crp = planes(bp, 1920, 1080, 960, 540)
    bp444 = raw(prox, frame, FPS, "yuv444p", 1920, 1080, 8)
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
