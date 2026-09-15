import sys, json, numpy as np
sys.argv = ["fit.py", "cfg3.json"]
import fit
fit.S = np.load("samples_holdout.npz"); fit._CACHE.clear()
res = json.load(open("fit3.json"))
out = {}
for person in ["Ludwig", "Flammann", "Hein"]:
    st = res["sets"][person]
    pB, pA = np.array(st["FX3_cdl_angleich"]), np.array(st["A7_cdl_angleich"])
    rows = []
    for n in (1, 2, 3):
        fb, fa = f"{person}_H{n}_FX3", f"{person}_H{n}_A7"
        r = {"paar": f"{person}_H{n}"}
        for k in ["skin", "dark"] + (["bright"] if person == "Flammann" else []):
            xb, xa = fit.get(fb, k), fit.get(fa, k)
            if xb is None or xa is None: continue
            b0, a0 = fit.lab_mean(xb, fit.IDENT, use_look=False), fit.lab_mean(xa, fit.IDENT, use_look=False)
            b1, a1 = fit.lab_mean(xb, pB), fit.lab_mean(xa, pA)
            r[k] = {"dE_vorher": round(float(fit.de2000(b0, a0)), 2), "dE_nachher": round(float(fit.de2000(b1, a1)), 2), "Lab_FX3": b1.round(1).tolist(), "Lab_A7": a1.round(1).tolist()}
        w = fit.get(fb, "wall")
        if w is not None: r["wand_FX3_Lab"] = fit.lab_mean(w, pB).round(1).tolist()
        rows.append(r)
    out[person] = rows
    for r in rows:
        print(person, r["paar"], {k: (v["dE_vorher"], v["dE_nachher"]) for k, v in r.items() if isinstance(v, dict)}, "Wand", r.get("wand_FX3_Lab"))
json.dump(out, open("holdout_eval.json", "w"), indent=1)
