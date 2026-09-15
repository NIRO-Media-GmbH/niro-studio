import json, os, numpy as np
from PIL import Image
from colorlib import *
SP = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(f"{SP}/manifest.json"))
BR_SEL = [2, 7, 11, 14, 16, 21, 24, 29]
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
