"""Vorlage (Stand 15.09.2026): Hold-out-Paare ziehen — 3 weitere zeitgleiche FX3/a7-Paare je Person, die der Fit nicht gesehen hat.

Aufruf (im Ordner _intern/color/skripte, nach extract.py):
  tools/autocut/venv/bin/python holdout_extract.py
  ../../gesichtscheck/faces lutjpg_h > faces_h.tsv
  tools/autocut/venv/bin/python measure.py ids_holdout.json samples_holdout.npz faces_h.tsv
  tools/autocut/venv/bin/python holdout_eval.py
Übernimmt Pfade, JSON-Daten, PAIRS, FPS, off und grab aus extract.py (Teil vor der Zeile, die jobs und manifest anlegt, per exec),
keine eigenen ANPASSEN-Werte. Auswahl: je Person 3 Paare gleichmäßig über alle V1/V2-Überlappungen ≥ 20 Frames, Zeitpunkt
20 % in die Überlappung (die Fit-Paare liegen in der Mitte); Sync-Kontrolle wie extract.py.
Ausgaben: frames/<Person>_H<n>_FX3/_A7.npy, lutjpg_h/<id>.jpg (LC-709), ids_holdout.json, manifest_holdout.json.
Grenze: nur teilweise unabhängig (andere Zeitpunkte, teils in denselben Beats).
Herkunft: Taxodia-Session, Scratchpad color/holdout_extract.py
"""
import json, os, numpy as np
from PIL import Image
_kopf = {"__file__": os.path.abspath("extract.py")}
exec(open("extract.py").read().split("jobs, manifest = [], []")[0], _kopf)  # Pfade, media, sync, tl, PAIRS, off, grab
media, tl, PAIRS, FPS, off, grab, OUT = (_kopf[k] for k in ("media", "tl", "PAIRS", "FPS", "off", "grab", "OUT"))
from colorlib import LUTDIR, apply_lut, load_cube, to_u8, yuv_to_rgb
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
        assert fa == ff + round(o * FPS)
        fid = f"{person}_H{n}"
        jobs += [(fx3p, (ff - 0.25) / FPS, f"{OUT}/{fid}_FX3.npy"), (a7p, (fa - 0.25) / FPS, f"{OUT}/{fid}_A7.npy")]
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
