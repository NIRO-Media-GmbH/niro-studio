"""Lippensync-Prüfung neuer Interview-Einstellungen gegen die Originalclips (NAS).
Je Einstellung: Kamera (FX3/a7MK4) per Template-Matching bestimmen, dann für jeden 2. Frame des Schnitts
den bestpassenden Quellframe im Fenster ±3 s um die ton-synchrone Erwartung suchen.
Δ = gefundene Quellzeit − erwartete Quellzeit (0 = lippensynchron)."""
import json, subprocess, unicodedata, sys
from pathlib import Path
import numpy as np, cv2

P = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
PR = next(p for p in P.iterdir() if unicodedata.normalize("NFC", p.name) == "Prüfen")
NEU = next(p for p in PR.iterdir() if p.name.endswith("_NEU.mov"))
idx = {r["name"].rsplit(".",1)[0]: r for r in json.load(open(P/"_intern/transcripts_index.json"))}
SW, SH = 960, 540          # Quelle 16:9
NW, NH = 540, 960          # Schnitt 9:16

def grab(path, start, dur, w, h):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(start,0):.3f}", "-t", f"{dur:.3f}", "-i", str(path),
           "-vf", f"fps=25,scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)

def feat(img):
    g = cv2.GaussianBlur(img, (0, 0), 1.2).astype(np.float32)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.magnitude(gx, gy)

def best_geometry(src_img, cut_img):
    sf = feat(src_img); best = (-1, None, None)
    for h in range(SH, int(SH*0.45), -6):
        w = int(round(h * 9 / 16))
        t = feat(cv2.resize(cut_img, (w, h), interpolation=cv2.INTER_AREA))
        r = cv2.matchTemplate(sf, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(r)
        if mx > best[0]: best = (mx, h, loc)
    return best

def check(label, cut_a, cut_b, fx_stem, a7_stem, off_fx, cam_off):
    print(f"\n===== {label}: Schnitt {cut_a:.2f}–{cut_b:.2f}, erwartet FX3 = t + {off_fx:.2f}")
    cut = grab(NEU, cut_a, cut_b - cut_a, NW, NH)
    mid = cut[len(cut)//2]; tmid = cut_a + (len(cut)//2)/25
    cands = {}
    for stem, off in ((fx_stem, off_fx), (a7_stem, off_fx - cam_off)):
        s = grab(idx[stem]["path"], tmid + off, 0.04, SW, SH)[0]
        cands[stem] = (best_geometry(s, mid), off)
        print(f"  Kamera {stem:<22} Score {cands[stem][0][0]:.3f} (Höhe {cands[stem][0][1]}, Pos {cands[stem][0][2]})")
    stem = max(cands, key=lambda k: cands[k][0][0]); (score, h, loc), off = cands[stem]
    print(f"  -> Quelle {stem}")
    win0 = cut_a + off - 3.0
    src = grab(idx[stem]["path"], win0, (cut_b - cut_a) + 6.0, SW, SH)
    srcf = [feat(x) for x in src]
    x0, y0 = loc; deltas = []
    for k in range(0, len(cut), 2):
        t_cut = cut_a + k/25; exp = t_cut + off
        best = (-1, None)
        for hh in sorted({min(SH, int(h*0.97)), min(SH, h), min(SH, int(h*1.03))}):
            ww = int(round(hh*9/16)); tf = feat(cv2.resize(cut[k], (ww, hh), interpolation=cv2.INTER_AREA))
            ya, yb = max(0, y0-30), min(SH, y0+hh+30); xa, xb = max(0, x0-40), min(SW, x0+ww+40)
            if yb - ya < hh or xb - xa < ww: ya, yb, xa, xb = 0, SH, 0, SW
            for j, sfj in enumerate(srcf):
                r = cv2.matchTemplate(sfj[ya:yb, xa:xb], tf, cv2.TM_CCOEFF_NORMED)
                mx = r.max()
                if mx > best[0]: best = (mx, j)
        t_src = win0 + best[1]/25
        deltas.append(t_src - exp)
        print(f"  Schnitt {t_cut:6.2f}s  erwartet {exp:8.2f}  gefunden {t_src:8.2f}  Δ {t_src-exp:+5.2f}s  Score {best[0]:.3f}")
    d = np.array(deltas)
    print(f"  => Median Δ {np.median(d):+.2f}s, Anteil |Δ|≤0,08 s: {np.mean(np.abs(d)<=0.081)*100:.0f} %")

which = sys.argv[1:] or ["kontrolle", "zoran", "christian"]
if "kontrolle" in which:
    check("KONTROLLE Christian Nah (im alten Schnitt synchron)", 21.30, 24.00, "FX3_9651", "a7MK4_20260624_9937", 27.62, 1.8)
if "zoran" in which:
    check("Zoran NEU Nahaufnahme", 11.56, 14.44, "FX3_9650", "a7MK4_20260624_9936", 142.42, 15.8)
if "christian" in which:
    check("Christian Ausstattung halbnah", 24.36, 28.56, "FX3_9651", "a7MK4_20260624_9937", 28.02, 1.8)
