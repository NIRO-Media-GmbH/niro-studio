import json, os, numpy as np
from PIL import Image
exec(open("extract.py").read().split("jobs, manifest = [], []")[0])  # Pfade, media, sync, tl, PAIRS, off, grab
from colorlib import *
used = {(m["person"], m["FX3"]["src_frame"]) for m in json.load(open("manifest.json")) if "person" in m}
v1 = [i for i in tl["items"] if i["track"] == "V1"]; v2 = [i for i in tl["items"] if i["track"] == "V2"]
jobs, man = [], []
for person, (fx3, a7) in PAIRS.items():
    o = off[(fx3, a7)]; c = []
    for a in v1:
        if os.path.basename(a["clip"]) != fx3: continue
        for b in v2:
            if os.path.basename(b["clip"]) != a7: continue
            lo, hi = max(a["rec_in_f"], b["rec_in_f"]), min(a["rec_out_f"], b["rec_out_f"])
            if hi - lo < 20: continue
            rec = lo + int(0.2 * (hi - lo))
            c.append((rec, a["src_in_f"] + rec - a["rec_in_f"], b["src_in_f"] + rec - b["rec_in_f"], a["beat_nr"]))
    c.sort()
    pick = [c[i] for i in sorted(set(np.linspace(0, len(c) - 1, 3).round().astype(int)))]
    fx3p = next(v["proxy"]["path"] for k, v in media["clips"].items() if os.path.basename(k) == fx3)
    a7p = next(v["proxy"]["path"] for k, v in media["clips"].items() if os.path.basename(k) == a7)
    for n, (rec, ff, fa, beat) in enumerate(pick, 1):
        assert fa == ff + round(o * 25)
        fid = f"{person}_H{n}"
        jobs += [(fx3p, (ff - 0.25) / 25, f"{OUT}/{fid}_FX3.npy"), (a7p, (fa - 0.25) / 25, f"{OUT}/{fid}_A7.npy")]
        man.append({"id": fid, "person": person, "beat": beat, "rec_frame": rec, "FX3": {"clip": fx3, "src_frame": ff}, "A7": {"clip": a7, "src_frame": fa}})
for j in jobs: grab(*j)
lut = load_cube(LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
os.makedirs("lutjpg_h", exist_ok=True); ids = []
for m in man:
    for cam in ("FX3", "A7"):
        fid = f"{m['id']}_{cam}"; ids.append(fid)
        Image.fromarray(to_u8(apply_lut(yuv_to_rgb(np.load(f"frames/{fid}.npy")), lut))).save(f"lutjpg_h/{fid}.jpg", quality=92)
json.dump(ids, open("ids_holdout.json", "w")); json.dump(man, open("manifest_holdout.json", "w"), indent=1)
print([ (m["id"], m["beat"], m["FX3"]["src_frame"], m["A7"]["src_frame"]) for m in man])
