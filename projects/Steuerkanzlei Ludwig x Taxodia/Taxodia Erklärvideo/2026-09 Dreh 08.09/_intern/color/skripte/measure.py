"""Messregionen je Frame: Haut (Gesichtsbox innen), dunkle Kleidung, helles Hemd, neutrale Wand.
Speichert Pixel-Stichproben im Log-Raum (S-Log3 CV/1023) fuer die Fits + Debug-Masken."""
import json, os
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter
from colorlib import *

SP = os.path.dirname(os.path.abspath(__file__))
import sys
IDS_FILE = sys.argv[1] if len(sys.argv) > 1 else "ids.json"
NPZ = sys.argv[2] if len(sys.argv) > 2 else "samples.npz"
ids = json.load(open(f"{SP}/{IDS_FILE}"))
lut = load_cube(LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
faces = {}
for line in open(f"{SP}/" + (sys.argv[3] if len(sys.argv) > 3 else "faces.tsv")):
    name, _, rest = line.rstrip("\n").partition("\t")
    boxes = []
    for part in rest.split(";") if rest and rest != "ERR" else []:
        x0, y0, x1, y1, c = map(float, part.split(","))
        boxes.append((x0, y0, x1, y1, c))
    faces[name[:-4]] = boxes

rng = np.random.default_rng(7)
W, H = 960, 540
os.makedirs(f"{SP}/masks", exist_ok=True)


def sample(arr, mask, n=4000):
    idx = np.flatnonzero(mask.ravel())
    if idx.size == 0:
        return np.zeros((0, 3), np.float32)
    if idx.size > n:
        idx = rng.choice(idx, n, replace=False)
    return arr.reshape(-1, 3)[idx]


def ycc(rgb):
    y = (rgb * LUMA).sum(-1)
    cb = (rgb[..., 2] - y) / (2 * (1 - KB))
    cr = (rgb[..., 0] - y) / (2 * (1 - KR))
    return y, cb, cr


out = {}
for fid in ids:
    log = downscale(yuv_to_rgb(np.load(f"{SP}/frames/{fid}.npy")), 2)
    disp = apply_lut(log, lut)
    y, cb, cr = ycc(disp)
    mx, mn = disp.max(-1), disp.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    yy, xx = np.mgrid[0:H, 0:W]
    broll = fid.startswith("BR")
    skin = np.zeros((H, W), bool); dark = np.zeros((H, W), bool); bright = np.zeros((H, W), bool)
    person = np.zeros((H, W), bool)
    for (x0, y0, x1, y1, c) in faces.get(fid, []):
        X0, X1, Y0, Y1 = x0 * W, x1 * W, y0 * H, y1 * H
        w, h = X1 - X0, Y1 - Y0
        cx = (X0 + X1) / 2
        inner = (xx > X0 + 0.2 * w) & (xx < X1 - 0.2 * w) & (yy > Y0 + 0.32 * h) & (yy < Y1 - 0.1 * h)
        skinlike = (y > 0.12) & (y < 0.97) & (disp[..., 0] >= disp[..., 1] * 0.97) & (disp[..., 1] >= disp[..., 2] * 0.80) \
                   & (sat > 0.04) & (sat < 0.65)
        skin |= inner & skinlike
        # strenger Haut-Test fuer den Ausschluss im Oberkoerper (Haende/Arme), damit fast neutrale Polos nicht rausfallen
        skin_strict = (y > 0.12) & (disp[..., 0] > disp[..., 1] * 1.02) & (disp[..., 1] >= disp[..., 2]) & (sat > 0.12) & (sat < 0.65)
        torso = (xx > cx - 0.9 * w) & (xx < cx + 0.9 * w) & (yy > Y1 + 0.6 * h) & (yy < Y1 + 2.2 * h) & ~skin_strict
        if torso.sum() > 200:
            thr_d = np.percentile(y[torso], 30)          # dunkelste 30 % des Oberkoerpers (belichtungsunabhaengig)
            dark |= torso & (y <= thr_d) & (y > 0.004)
        shirt = (xx > cx - 0.45 * w) & (xx < cx + 0.55 * w) & (yy > Y1 + 0.5 * h) & (yy < Y1 + 2.2 * h) & ~skin_strict
        if fid.startswith("Flammann") and shirt.sum() > 200:
            thr_b = np.percentile(y[shirt], 75)          # hellste 25 % im Hemdbereich
            bright |= shirt & (y >= thr_b) & (y < 0.97) & (sat < 0.35)
        person |= (xx > X0 - 2.2 * w) & (xx < X1 + 2.2 * w) & (yy > Y0 - 0.6 * h)
    # Wand/neutral: hell, glatt, wenig Chroma, ausserhalb Person, nicht geclippt
    ys = np.sqrt(np.maximum(uniform_filter(y ** 2, 9) - uniform_filter(y, 9) ** 2, 0))
    chroma = np.hypot(cb, cr)
    cand = (~person) & (y > 0.40) & (y < 0.93) & (ys < 0.012) & (mx < 0.985)
    wall = np.zeros((H, W), bool)
    if cand.sum() > 500:
        thr = np.percentile(chroma[cand], 40)
        wall = cand & (chroma <= thr)
    rec = {"skin": sample(log, skin), "dark": sample(log, dark), "bright": sample(log, bright), "wall": sample(log, wall),
           "n": {"skin": int(skin.sum()), "dark": int(dark.sum()), "bright": int(bright.sum()), "wall": int(wall.sum())}}
    out[fid] = rec
    # Debug-Maske: Haut rot, dunkel blau, hell gruen, Wand gelb
    dbg = to_u8(disp).copy()
    for m, col in [(wall, (255, 220, 0)), (skin, (255, 0, 0)), (dark, (0, 120, 255)), (bright, (0, 220, 0))]:
        dbg[m] = (0.45 * dbg[m] + 0.55 * np.array(col)).astype(np.uint8)
    Image.fromarray(dbg).resize((480, 270)).save(f"{SP}/masks/{fid}.jpg", quality=85)
    print(fid, rec["n"])

np.savez_compressed(f"{SP}/{NPZ}", **{f"{fid}|{k}": v[k] for fid, v in out.items() for k in ("skin", "dark", "bright", "wall")})
json.dump({fid: v["n"] for fid, v in out.items()}, open(f"{SP}/{NPZ}.n.json", "w"), indent=1)

# Uebersicht Masken
sheet = Image.new("RGB", (480 * 6, 270 * ((len(ids) + 5) // 6)), (0, 0, 0))
for i, fid in enumerate(ids):
    im = label(Image.open(f"{SP}/masks/{fid}.jpg"), fid, 13)
    sheet.paste(im, ((i % 6) * 480, (i // 6) * 270))
sheet.save(f"{SP}/preview/masks_{IDS_FILE[:-5]}.jpg", quality=80)
