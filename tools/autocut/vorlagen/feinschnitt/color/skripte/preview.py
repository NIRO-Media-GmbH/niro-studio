"""Vorlage (Stand 15.09.2026): Schnellvorschau der Analyse-Frames (Log roh | Sony LC-709) — Sichtung vor dem Fit.

Aufruf (im Ordner _intern/color/skripte): tools/autocut/venv/bin/python preview.py
Eingaben: manifest.json + frames/*.npy (extract.py). Keine chargen-spezifischen Werte (Personen kommen aus manifest.json).
Ausgaben: preview/<Person>.jpg (je Paar FX3 log | a7 log | FX3 LC-709 | a7 LC-709), preview/broll_all.jpg (alle B-Roll-Shots
mit LC-709, 6 Spalten × 5 Zeilen = höchstens 30 Shots). Aus broll_all.jpg die 8 Fit-Shots für lutjpg.BR_SEL wählen: Shots mit
Haut und/oder hellen, neutralen Wänden, verschiedene Clips und Lichtsituationen. Legt auch preview/ an (measure.py schreibt dorthin).
Herkunft: Taxodia-Session, Scratchpad color/preview.py
"""
import json, os, numpy as np
from PIL import Image
from colorlib import LUTDIR, apply_lut, downscale, label, load_cube, to_u8, yuv_to_rgb
SP = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(f"{SP}/manifest.json"))
lut = load_cube(LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
def get(fid):
    return downscale(yuv_to_rgb(np.load(f"{SP}/frames/{fid}.npy")), 4)  # 480x270
os.makedirs(f"{SP}/preview", exist_ok=True)
for person in dict.fromkeys(m["person"] for m in man if "person" in m):
    ids = [m["id"] for m in man if m.get("person") == person]
    W, H = 480, 270
    sheet = Image.new("RGB", (W * 4, H * len(ids)), (20, 20, 20))
    for r, fid in enumerate(ids):
        for c, cam in enumerate(["FX3", "A7"]):
            x = get(f"{fid}_{cam}")
            sheet.paste(label(Image.fromarray(to_u8(x)), f"{fid} {cam} log", 14), (c * W, r * H))
            sheet.paste(label(Image.fromarray(to_u8(apply_lut(x, lut))), f"{fid} {cam} LC-709", 14), ((2 + c) * W, r * H))
    sheet.save(f"{SP}/preview/{person}.jpg", quality=85)
br = [m for m in man if "broll_nr" in m]
W, H = 384, 216
sheet = Image.new("RGB", (W * 6, H * 5), (20, 20, 20))
for i, m in enumerate(br):
    x = downscale(yuv_to_rgb(np.load(f"{SP}/frames/{m['id']}.npy")), 5)
    sheet.paste(label(Image.fromarray(to_u8(apply_lut(x, lut))), m["id"], 14), ((i % 6) * W, (i // 6) * H))
sheet.save(f"{SP}/preview/broll_all.jpg", quality=85)
print("ok")
