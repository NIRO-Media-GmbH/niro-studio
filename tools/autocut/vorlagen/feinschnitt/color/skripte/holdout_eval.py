"""Vorlage (Stand 15.09.2026): Hold-out-Bewertung — Angleich-CDLs aus fit3.json auf die Hold-out-Paare anwenden, dE2000 vorher/nachher.

Aufruf (im Ordner _intern/color/skripte, nach holdout_extract.py + measure.py … samples_holdout.npz): tools/autocut/venv/bin/python holdout_eval.py
Lädt fit.py als Modul mit cfg3.json (braucht samples.npz, ids.json) und tauscht die Stichproben gegen samples_holdout.npz.
Keine eigenen ANPASSEN-Werte: Personen = Sets in fit3.json, helles Hemd = fit.HELLES_HEMD.
Ausgabe: holdout_eval.json — je Person Liste der Paare <Person>_H<n> mit skin/dark/bright {dE_vorher (nur LUT), dE_nachher
(Angleich + Look), Lab_FX3, Lab_A7} und wand_FX3_Lab → export_vorschlag.py (hold_out_3_paare).
Herkunft: Taxodia-Session, Scratchpad color/holdout_eval.py
"""
import sys, json, numpy as np
sys.argv = ["fit.py", "cfg3.json"]
import fit
fit.S = np.load("samples_holdout.npz"); fit._CACHE.clear()
res = json.load(open("fit3.json"))
out = {}
for person in res["sets"]:
    st = res["sets"][person]
    pB, pA = np.array(st["FX3_cdl_angleich"]), np.array(st["A7_cdl_angleich"])
    rows = []
    for n in (1, 2, 3):
        fb, fa = f"{person}_H{n}_FX3", f"{person}_H{n}_A7"
        r = {"paar": f"{person}_H{n}"}
        for k in ["skin", "dark"] + (["bright"] if person in fit.HELLES_HEMD else []):
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
