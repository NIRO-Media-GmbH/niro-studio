"""CDL-Fit je Set im S-Log3-Raum (vor dem LUT).
Kette je Pixel: Log -> CDL_Kamera/Set -> Look-CDL (Log, Pivot 18 % Grau) -> Sony LC-709 -> Rec.709 -> Lab.
FX3: Neutralisierung (Wand hell + schwarzes Polo dunkel) + Belichtung (Kompromiss Haut-/Wand-Ziel).
a7:  Match auf die korrigierte FX3 (Haut, dunkle Kleidung, helles Hemd).
B-Roll FX3A: Neutralisierung (Waende) + Belichtung auf eigenes Haut-Ziel.
Physikalische Parameter: e (Blenden), wb_r/wb_b (Blenden rel. G), db_r/db_b (Slope-Delta rel. G, Pivot helle Wand),
dc (Kontrast-Delta um 18 % Grau), dsat (Saettigungs-Delta, nur a7)."""
import json, os, sys
import numpy as np
from scipy.optimize import least_squares
from colorlib import *

SP = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
LOOK = cfg.get("look", {"k": 1.15, "sat": 1.08, "exp": 0.0})
T_SKIN = cfg.get("t_skin", 69.0)
T_WALL = cfg.get("t_wall", 88.0)
W_WALL = cfg.get("w_wall", 0.5)
T_SKIN_BR = cfg.get("t_skin_broll", 38.0)
LAM_DB, LAM_DC, LAM_DSAT = cfg.get("lam_db", 30.0), cfg.get("lam_dc", 40.0), cfg.get("lam_dsat", 15.0)
OUTNAME = cfg.get("out", "fit_result.json")
P = float(lin_to_slog3(0.18))
W_PIV = float(lin_to_slog3(1.35))   # Pivot Schwarzabgleich: helle Wand (~log 0.63)

S = np.load(f"{SP}/samples.npz")
ids = json.load(open(f"{SP}/ids.json"))
lut = load_cube(LUTDIR + cfg.get("lut", "SLog3SGamut3.CineToLC-709.cube"))
rng = np.random.default_rng(3)
_CACHE = {}


def get(fid, k, n=1500):
    key = f"{fid}|{k}"
    if key not in _CACHE:
        x = S[key]
        if len(x) < 80:
            _CACHE[key] = None
        else:
            if len(x) > n:
                x = x[rng.choice(len(x), n, replace=False)]
            _CACHE[key] = x.astype(np.float64)
    return _CACHE[key]


def look_cdl(lk=LOOK):
    """Look als CDL im Log-Raum: Kontrast k um Pivot P, Belichtung exp (Blenden), Saettigung."""
    k = lk["k"]
    return np.r_[[k] * 3, [P * (1 - k) + lk.get("exp", 0.0) * STOP * k] * 3, lk["sat"]]


def apply_cdl(x, p):
    y = x * p[0:3] + p[3:6]
    if p[6] != 1.0:
        l = (y * LUMA).sum(-1, keepdims=True)
        y = l + p[6] * (y - l)
    return y


def compose(p_cam, p_look):
    """Exakt fuer Look mit gleichem Slope/Offset je Kanal und Power 1: Look(Cam(x))."""
    k, o = p_look[0], p_look[3]
    return np.r_[k * p_cam[0:3], k * p_cam[3:6] + o, p_cam[6] * p_look[6]]


def render(x, p, lk=LOOK, use_look=True):
    y = apply_cdl(x, compose(p, look_cdl(lk)) if use_look else p)
    return apply_lut(np.clip(y, 0, 1).astype(np.float32), lut).astype(np.float64)


def lab_mean(x, p, **kw):
    return disp_to_lab(render(x, p, **kw).mean(0))


IDENT = np.array([1, 1, 1, 0, 0, 0, 1], float)


def phys_to_cdl(q, dsat=0.0):
    e, wbr, wbb, dbr, dbb, dc = q
    s = np.array([1 + dbr, 1.0, 1 + dbb])
    c = 1 + dc
    wb = np.array([wbr, 0.0, wbb]) * STOP
    slope = c * s
    offset = c * (-s * W_PIV + W_PIV + wb + e * STOP - P) + P
    return np.r_[slope, offset, 1 + dsat]


LB6 = [-3.0, -1.5, -1.5, -0.2, -0.2, -0.25]
UB6 = [3.0, 1.5, 1.5, 0.2, 0.2, 0.35]
XS6 = [0.3, 0.1, 0.1, 0.03, 0.03, 0.05]


def reg(q):
    return [q[3] * LAM_DB, q[4] * LAM_DB, q[5] * LAM_DC]


def set_residuals(v, person):
    pB = phys_to_cdl(v[:6]); pA = phys_to_cdl(v[6:12], v[12])
    r = []
    for i in range(1, 7):
        fb, fa = f"{person}_{i}_FX3", f"{person}_{i}_A7"
        lb, la = lab_mean(get(fb, "skin"), pB), lab_mean(get(fa, "skin"), pA)
        r += list((la - lb) * [1.0, 1.5, 1.5])          # Match Haut
        r.append(lb[0] - T_SKIN)                          # Belichtung FX3 (Haut)
        db, da = get(fb, "dark"), get(fa, "dark")
        if db is not None and da is not None:
            ldb, lda = lab_mean(db, pB), lab_mean(da, pA)
            r += list((lda - ldb) * 0.6)                  # Match dunkle Kleidung
            if person != "Flammann":                      # schwarzes Polo neutral (Flammann: navy Blazer)
                r += list(ldb[1:] * 0.8) + list(lda[1:] * 0.4)
        bb, ba = get(fb, "bright"), get(fa, "bright")
        if person == "Flammann" and bb is not None and ba is not None:
            r += list(lab_mean(ba, pA) - lab_mean(bb, pB))  # Match helles Hemd
        wb = get(fb, "wall")
        if wb is not None:
            lw = lab_mean(wb, pB)
            r += list(lw[1:])                             # Wand FX3 neutral
            r.append((lw[0] - T_WALL) * W_WALL)           # Wand-Helligkeit (Kompromiss)
    r += reg(v[:6]) + reg(v[6:12]) + [v[12] * LAM_DSAT]
    return np.array(r)


BR_WALL_OK = {"BR14_C0253", "BR16_C0255", "BR24_C0261", "BR29_C0262", "BR11_C0251"}


def broll_residuals(q):
    p = phys_to_cdl(q)
    r = []
    for fid in [i for i in ids if i.startswith("BR")]:
        s = get(fid, "skin")
        if s is not None:
            r.append((lab_mean(s, p)[0] - T_SKIN_BR) * 0.5)
        w = get(fid, "wall")
        if w is not None and fid in BR_WALL_OK:
            r += list(lab_mean(w, p)[1:] * 0.8)
        d = get(fid, "dark")
        if d is not None:
            r += list(lab_mean(d, p)[1:] * 0.3)
    return np.array(r + reg(q))


def report_set(person, pB, pA, use_look):
    rows = []
    for i in range(1, 7):
        fb, fa = f"{person}_{i}_FX3", f"{person}_{i}_A7"
        row = {"frame": i}
        for k in ["skin", "dark", "bright"]:
            xb, xa = get(fb, k), get(fa, k)
            if xb is None or xa is None or (k == "bright" and person != "Flammann"):
                continue
            lb, la = lab_mean(xb, pB, use_look=use_look), lab_mean(xa, pA, use_look=use_look)
            row[k] = {"FX3": lb.round(1).tolist(), "A7": la.round(1).tolist(), "dE2000": round(float(de2000(lb, la)), 2)}
        w = get(fb, "wall")
        if w is not None:
            row["wand_FX3"] = lab_mean(w, pB, use_look=use_look).round(1).tolist()
        rows.append(row)
    summ = {}
    for k in ["skin", "dark", "bright"]:
        d = [r[k]["dE2000"] for r in rows if k in r]
        if d:
            summ[k] = {"dE2000_mittel": round(float(np.mean(d)), 2), "dE2000_max": round(float(np.max(d)), 2),
                       "Lab_FX3": np.mean([r[k]["FX3"] for r in rows if k in r], 0).round(1).tolist(),
                       "Lab_A7": np.mean([r[k]["A7"] for r in rows if k in r], 0).round(1).tolist()}
    summ["wand_FX3_Lab"] = np.mean([r["wand_FX3"] for r in rows if "wand_FX3" in r], 0).round(1).tolist()
    return summ, rows


NAMES = ["belichtung_blenden", "wb_r_blenden", "wb_b_blenden", "schwarz_slope_delta_r", "schwarz_slope_delta_b", "kontrast_delta"]

if __name__ == "__main__":
    res = {"cfg": cfg, "look": LOOK, "look_cdl_log": look_cdl().round(4).tolist(), "pivot_log": P, "w_pivot_log": W_PIV, "sets": {}}
    for person in ["Ludwig", "Flammann", "Hein"]:
        # Startwert a7-Belichtung aus Haut-Log-Differenz (G)
        gB = np.mean([np.median(get(f"{person}_{i}_FX3", "skin")[:, 1]) for i in range(1, 7)])
        gA = np.mean([np.median(get(f"{person}_{i}_A7", "skin")[:, 1]) for i in range(1, 7)])
        v0 = np.r_[0, 0, 0, 0, 0, 0, (gB - gA) / STOP, 0, 0, 0, 0, 0, 0.0]
        lbB, ubB = list(LB6), list(UB6)
        lbB[5], ubB[5] = -1e-4, 1e-4          # FX3 = Referenz: kein eigener Kontrast (macht der Look)
        lb = lbB + LB6 + [-0.3]; ub = ubB + UB6 + [0.3]
        sol = least_squares(set_residuals, v0, args=(person,), bounds=(lb, ub), x_scale=XS6 + XS6 + [0.05],
                            loss="soft_l1", f_scale=3.0, diff_step=1e-4, max_nfev=800)
        pB = phys_to_cdl(sol.x[:6]); pA = phys_to_cdl(sol.x[6:12], sol.x[12])
        before, _ = report_set(person, IDENT, IDENT, False)
        after, rows = report_set(person, pB, pA, True)
        res["sets"][person] = {
            "FX3_cdl_angleich": pB.round(4).tolist(), "A7_cdl_angleich": pA.round(4).tolist(),
            "FX3_cdl_gesamt": compose(pB, look_cdl()).round(4).tolist(), "A7_cdl_gesamt": compose(pA, look_cdl()).round(4).tolist(),
            "FX3_phys": dict(zip(NAMES, sol.x[:6].round(4).tolist())),
            "A7_phys": dict(zip(NAMES + ["saettigung_delta"], sol.x[6:13].round(4).tolist())),
            "vorher_nur_LUT": before, "nachher": after, "frames_nachher": rows, "cost": round(float(sol.cost), 2), "nfev": int(sol.nfev)}
        print(f"== {person}  cost {sol.cost:.1f} nfev {sol.nfev}  status {sol.status}")
        print("  FX3 phys:", {k: round(float(x), 3) for k, x in zip(NAMES, sol.x[:6])})
        print("  A7  phys:", {k: round(float(x), 3) for k, x in zip(NAMES + ["dsat"], sol.x[6:13])})
        print("  FX3 CDL:", pB.round(4), " A7 CDL:", pA.round(4))
        for k in ["skin", "dark", "bright"]:
            if k in before:
                print(f"  {k:6s} dE vorher {before[k]['dE2000_mittel']:5.2f}/{before[k]['dE2000_max']:5.2f}  nachher {after[k]['dE2000_mittel']:5.2f}/{after[k]['dE2000_max']:5.2f}   FX3 {after[k]['Lab_FX3']} A7 {after[k]['Lab_A7']}")
        print("  Wand FX3 vorher", before["wand_FX3_Lab"], "nachher", after["wand_FX3_Lab"])
        print("  Haut-dE je Frame:", [r["skin"]["dE2000"] for r in rows])
    lbR, ubR = list(LB6), list(UB6)
    lbR[5], ubR[5] = -1e-4, 1e-4
    sol = least_squares(broll_residuals, np.zeros(6), bounds=(lbR, ubR), x_scale=XS6, loss="soft_l1", f_scale=3.0, diff_step=1e-4, max_nfev=800)
    pBR = phys_to_cdl(sol.x)
    res["broll"] = {"FX3A_cdl_angleich": pBR.round(4).tolist(), "FX3A_cdl_gesamt": compose(pBR, look_cdl()).round(4).tolist(),
                    "FX3A_phys": dict(zip(NAMES, sol.x.round(4).tolist())), "shots": {}}
    print("== B-Roll FX3A phys:", {k: round(float(x), 3) for k, x in zip(NAMES, sol.x)}, "CDL", pBR.round(4))
    for fid in [i for i in ids if i.startswith("BR")]:
        row = {}
        for k in ["skin", "wall", "dark"]:
            x = get(fid, k)
            if x is not None:
                row[k] = {"vorher_nur_LUT": lab_mean(x, IDENT, use_look=False).round(1).tolist(), "nachher": lab_mean(x, pBR).round(1).tolist()}
        res["broll"]["shots"][fid] = row
        print("  ", fid, " | ".join(f"{k} {v['vorher_nur_LUT']}->{v['nachher']}" for k, v in row.items()))
    json.dump(res, open(f"{SP}/{OUTNAME}", "w"), indent=1)
