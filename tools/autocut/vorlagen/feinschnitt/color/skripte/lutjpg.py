"""Vorlage (Stand 15.09.2026): Analyse-Frames mit Sony LC-709 als JPG für die Gesichtserkennung + Frame-Liste ids.json schreiben.

Aufruf (im Ordner _intern/color/skripte):
  tools/autocut/venv/bin/python lutjpg.py
  ../../gesichtscheck/faces lutjpg > faces.tsv     (Binärdatei aus gesichtscheck/faces.swift, Build-Befehl dort)
Eingaben: manifest.json + frames/*.npy (extract.py). Ausgaben: lutjpg/<id>.jpg (1920×1080), ids.json (alle Paar-Frames
„<Person>_<n>_FX3/_A7" + die B-Roll-Frames aus BR_SEL) → gelesen von measure.py, fit.py, sheets.py.
sheets.py und compare.py setzen genau 8 B-Roll-Frames voraus (Kontaktbogen 4 × 2, Übersicht 2 × 4).
Herkunft: Taxodia-Session, Scratchpad color/lutjpg.py
"""
import json, os, numpy as np
from PIL import Image
from colorlib import LUTDIR, apply_lut, load_cube, to_u8, yuv_to_rgb

# ── ANPASSEN je Charge ─────────────────────────────
BR_SEL = [  # B-Roll-Shot-Nummern (broll_auswahl.json „nr") für den B-Roll-Fit, genau 8, gewählt in preview/broll_all.jpg
    # 2, 7, 11, 14, 16, 21, 24, 29,
]
# ── Ende ANPASSEN ──────────────────────────────────

SP = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(f"{SP}/manifest.json"))
lut = load_cube(LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
os.makedirs(f"{SP}/lutjpg", exist_ok=True)
ids = []
for m in man:
    if "person" in m:
        ids += [f"{m['id']}_FX3", f"{m['id']}_A7"]
    elif m["broll_nr"] in BR_SEL:
        ids.append(m["id"])
for fid in ids:
    x = yuv_to_rgb(np.load(f"{SP}/frames/{fid}.npy"))
    Image.fromarray(to_u8(apply_lut(x, lut))).save(f"{SP}/lutjpg/{fid}.jpg", quality=92)
json.dump(ids, open(f"{SP}/ids.json", "w"))
print(len(ids))
