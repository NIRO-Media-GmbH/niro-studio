"""B-Roll v4: lineare Verstaerkung + Schatten-Toe (Flare) je Einsatz, Belichtung/WB je Clip, Einsatz nur dunkler bei Lichterschutz."""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import colorlib as CL
import proto_messung as PMalt
import proto_messung3 as PM3

LOOK = (1.05, 1.00)
P = 420 / 1023
LUMA = CL.LUMA.astype(np.float32)
LICHTER_L, LICHTER_ZUSATZ = 98.0, 0.02
SCHATTEN_L, SCHATTEN_MAX = 5.0, 0.05
FLARES = [round(0.0005 * i, 4) for i in range(0, 17)]  # 0 ... 0.008 linear


def expo(x, e, wr, wb, f=0.0):
    g = 2.0 ** np.array([e + wr, e, e + wb])
    with np.errstate(invalid="ignore", divide="ignore"):
        lin = CL.slog3_to_lin(x.astype(np.float64)) * g + f
        return np.nan_to_num(CL.lin_to_slog3(lin)).astype(np.float32)


def render(x, w, f=0.0):
    k, s = LOOK
    y = expo(x, w["e"], w["wr"], w["wb"], f)
    y = k * y + P * (1 - k)
    lum = (y * LUMA).sum(-1, keepdims=True)
    y = lum + s * (y - lum)
    return CL.apply_lut(np.clip(y, 0, 1).astype(np.float32), PM3.LUT)


def einsatz(auftrag):
    key, frames, clipw = auftrag
    xs = [PM3.decode(p, n, fps).astype(np.float32) for p, n, fps in frames]
    unclip = [x.max(-1) < PM3.SENSOR_CLIP for x in xs]
    L0 = [CL.disp_to_lab(render(x, {**clipw, "e": 0.0}))[..., 0] for x in xs]

    def zu_hell(e):
        for x, u, l0 in zip(xs, unclip, L0):
            le = CL.disp_to_lab(render(x, {**clipw, "e": e}))[..., 0]
            if float(((le >= LICHTER_L) & u).mean() - ((l0 >= LICHTER_L) & u).mean()) > LICHTER_ZUSATZ:
                return True
        return False
    e = clipw["e"]
    geschuetzt = False
    if e > 0 and zu_hell(e):
        lo, hi = 0.0, e
        while hi - lo > 0.02:
            m = (lo + hi) / 2
            if zu_hell(m):
                hi = m
            else:
                lo = m
        e, geschuetzt = lo, True
    w = {**clipw, "e": e}
    f_wahl = FLARES[-1]
    for f in FLARES:
        anteil = np.mean([float((CL.disp_to_lab(render(x, w, f))[..., 0] <= SCHATTEN_L).mean()) for x in xs])
        if anteil <= SCHATTEN_MAX:
            f_wahl = f
            break
    return key, {"e": round(e, 3), "wr": clipw["wr"], "wb": clipw["wb"], "flare": f_wahl, "lichterschutz": geschuetzt}


def main():
    snap = [i for i in json.load(open("proto/kopie_items.json"))["items"] if i["spur"] == 3]
    clips = json.load(open("proto/plan_broll_v3.json"))["clips"]
    auftraege = []
    for it in snap:
        frames = [(it["pfad"], int(round(it["src"] + round(q * (it["dauer"] - 1)) * it["tempo"] / 100 * it["fps"] / 25)), it["fps"]) for q in (0.2, 0.5, 0.8)]
        auftraege.append(((it["spur"], it["start"]), frames, clips[it["name"]]["werte"]))
    with ProcessPoolExecutor(12) as ex:
        ergebnis = dict(ex.map(einsatz, auftraege))
    plan = []
    for it in snap:
        w = ergebnis[(it["spur"], it["start"])]
        plan.append({"spur": 3, "start": it["start"], "name": it["name"], **w})
        print(f"V3 {it['start']:>5} {it['name']:<10} e {w['e']:+.2f} (Clip {clips[it['name']]['werte']['e']:+.2f}) R {w['wr']:+.2f} B {w['wb']:+.2f} Flare {w['flare']:.4f}{'  Lichterschutz' if w['lichterschutz'] else ''}")
    json.dump(plan, open("proto/plan_broll_v4.json", "w"), indent=1)


if __name__ == "__main__":
    main()
