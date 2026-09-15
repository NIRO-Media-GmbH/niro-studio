"""Vorlage (Stand 15.09.2026): Gegenprobe auf den 10-Bit-Originalen — hält der A/B-Angleich außerhalb der 8-Bit-Proxys?

Aufruf (im Ordner _intern/color/skripte, nach fit.py cfg3.json): tools/autocut/venv/bin/python orig_check.py
Je Person Paar #2 (manifest.json): Original-Frame (XAVC 3840×2160, 4:2:2 10 Bit, nur lesen) und Proxy-Frame mit der Gesamt-CDL aus
fit3.json + LC-709 graden, Haut-Lab in der Gesichtsbox (faces.tsv, Hautfilter wie measure.py) vergleichen.
Eingaben: fit3.json, manifest.json, faces.tsv, frames/*.npy, Originale unter NAS/<Kamera-Ordner>/<Clip>.
Ausgabe: orig_check.json — je „<Person>_2": FX3/A7 {haut_Lab_original, haut_Lab_proxy, dE2000_original_vs_proxy,
log_mittlere_abw_rgb}, dE2000_FX3_vs_A7_auf_Originalen → export_vorschlag.py (gegenprobe_10bit_original_paar_2).
Befund 15.09. (Referenz): nach dem Grade Haut 0,6–1,2 dE2000 Proxy ↔ Original (Original minimal gelber, b* ca. +1).
Herkunft: Taxodia-Session, Scratchpad color/orig_check.py
"""
import json, subprocess, numpy as np
from colorlib import KB, KG, KR, LUMA, LUTDIR, apply_lut, de2000, disp_to_lab, downscale, load_cube, yuv_to_rgb

# ── ANPASSEN je Charge ─────────────────────────────
NAS = "<Footage-Ordner der Originale>"  # Ordner mit den Kamera-Unterordnern der Original-MP4s (NAS oder SSD, ohne / am Ende)
KAMERA_ORDNER = {"FX3": "Kamera-B", "A7": "Kamera-A"}  # Unterordner je Kamera im Footage-Ordner — Standard (15.09.): B = FX3, A = a7
FPS = 25  # Bildrate der Interview-Originale in fps (Zeitstempel aus src_frame) — Standard (15.09.)
# ── Ende ANPASSEN ──────────────────────────────────

fit = json.load(open("fit3.json")); man = {m["id"]: m for m in json.load(open("manifest.json")) if "person" in m}
lut = load_cube(LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
faces = {l.split("\t")[0][:-4]: [tuple(map(float, p.split(","))) for p in l.rstrip("\n").split("\t")[1].split(";")] for l in open("faces.tsv")}
def orig_rgb(path, frame):
    t = (frame - 0.25) / FPS
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "yuv422p10le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(b, np.uint16)
    Y = a[:3840 * 2160].reshape(2160, 3840).astype(np.float32)
    Cb = a[3840 * 2160:3840 * 2160 + 1920 * 2160].reshape(2160, 1920).astype(np.float32)
    Cr = a[3840 * 2160 + 1920 * 2160:].reshape(2160, 1920).astype(np.float32)
    y = Y.reshape(540, 4, 960, 4).mean((1, 3)) / 1023
    pb = (Cb.reshape(540, 4, 960, 2).mean((1, 3)) - 512) / 1023
    pr = (Cr.reshape(540, 4, 960, 2).mean((1, 3)) - 512) / 1023
    r = y + 2 * (1 - KR) * pr; bb = y + 2 * (1 - KB) * pb; g = (y - KR * r - KB * bb) / KG
    return np.stack([r, g, bb], -1)
def grade(x, p):
    p = np.asarray(p, np.float32); y = x * p[:3] + p[3:6]
    l = (y * LUMA.astype(np.float32)).sum(-1, keepdims=True); y = l + p[6] * (y - l)
    return apply_lut(np.clip(y, 0, 1), lut)
def skin_lab(disp, fid):
    H, W = disp.shape[:2]; x0, y0, x1, y1, _ = faces[fid][0]
    X0, X1, Y0, Y1 = x0 * W, x1 * W, y0 * H, y1 * H; w, h = X1 - X0, Y1 - Y0
    sub = disp[int(Y0 + 0.32 * h):int(Y1 - 0.1 * h), int(X0 + 0.2 * w):int(X1 - 0.2 * w)].reshape(-1, 3)
    yv = (sub * LUMA).sum(-1); mx, mn = sub.max(-1), sub.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    m = (yv > 0.12) & (yv < 0.97) & (sub[:, 0] >= sub[:, 1] * 0.97) & (sub[:, 1] >= sub[:, 2] * 0.8) & (sat > 0.04) & (sat < 0.65)
    return disp_to_lab(sub[m].mean(0))
out = {}
for person, i in [(person, 2) for person in fit["sets"]]:
    st = fit["sets"][person]; m = man[f"{person}_{i}"]; row = {}
    for cam, key, folder in [("FX3", "FX3_cdl_gesamt", KAMERA_ORDNER["FX3"]), ("A7", "A7_cdl_gesamt", KAMERA_ORDNER["A7"])]:
        fid = f"{person}_{i}_{cam}"
        xo = orig_rgb(f"{NAS}/{folder}/{m[cam]['clip']}", m[cam]["src_frame"])
        xp = downscale(yuv_to_rgb(np.load(f"frames/{fid}.npy")), 2).astype(np.float32)
        lo, lp = skin_lab(grade(xo, st[key]), fid), skin_lab(grade(xp, st[key]), fid)
        diff_log = np.abs(xo - xp).mean(axis=(0, 1))
        row[cam] = {"haut_Lab_original": lo.round(1).tolist(), "haut_Lab_proxy": lp.round(1).tolist(), "dE2000_original_vs_proxy": round(float(de2000(lo, lp)), 2), "log_mittlere_abw_rgb": diff_log.round(4).tolist()}
    row["dE2000_FX3_vs_A7_auf_Originalen"] = round(float(de2000(np.array(row["FX3"]["haut_Lab_original"]), np.array(row["A7"]["haut_Lab_original"]))), 2)
    out[f"{person}_{i}"] = row
    print(person, json.dumps(row))
json.dump(out, open("orig_check.json", "w"), indent=1)
