import json, sys
import numpy as np, cv2
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
sys.path.insert(0, ".")
import colorlib as CL
import proto_messung as PM
import proto_vergleich as PV

werte = json.load(open("proto/werte.json"))
bericht = json.load(open(PV.TEST / "gegenprobe_prototyp.json"))

def inv709(v):
    v = np.clip(v, 0, 1)
    return np.where(v < 0.081, v / 4.5, ((v + 0.099) / 1.099) ** (1 / 0.45))

HYP = {
    "identisch": lambda m: m,
    "Scene->709-A mit OOTF 1.2": lambda m: (inv709(m) ** 1.2) ** (1 / 1.961),
    "Scene->Gamma 2.4 ohne OOTF": lambda m: inv709(m) ** (1 / 2.4),
    "Gamma 2.4 -> 709-A (1.961)": lambda m: (np.clip(m, 0, 1) ** 2.4) ** (1 / 1.961),
    "709-A(1.961) -> Gamma 2.4": lambda m: (np.clip(m, 0, 1) ** 1.961) ** (1 / 2.4),
}
paare_m, paare_s, paare_x = [], [], []
for key in werte:
    it = next(i for i in PM.ITEMS if i["key"] == key)
    gp = bericht["items"][key]["gegenprobe_neu"]
    n = gp["quellframe"]
    x = PM.decode(it["pfad"], n, it["fps"])
    modell = PM.render(x, werte[key]["werte"])
    s = PV.still(PV.STILLS / f"neu_{it['still']}.png")
    H, _ = PV.homographie(modell, s)
    warp = cv2.warpPerspective(modell, H, (960, 540), flags=cv2.INTER_AREA)
    xw = cv2.warpPerspective(x, H, (960, 540), flags=cv2.INTER_AREA)
    maske = cv2.warpPerspective(np.ones((540, 960), np.float32), H, (960, 540), flags=cv2.INTER_NEAREST) > 0.5
    maske = cv2.erode(maske.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    # glatte Bereiche (Kanten raus, sonst Ausrichtungsfehler)
    g = cv2.cvtColor((warp * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    glatt = maske & (grad < np.percentile(grad[maske], 50))
    paare_m.append(warp[glatt]); paare_s.append(s[glatt]); paare_x.append((key, xw[glatt], werte[key]["werte"]))
M = np.concatenate(paare_m); S = np.concatenate(paare_s)
print("Pixel:", len(M))
print("Kennlinie G-Kanal (Modell -> Resolve, Median je Bin):")
for lo in np.arange(0.0, 1.0, 0.1):
    sel = (M[:, 1] >= lo) & (M[:, 1] < lo + 0.1)
    if sel.sum() > 200:
        print(f"  Modell {lo:.1f}-{lo+0.1:.1f}: Resolve {np.median(S[sel, 1]):.3f} (Modell-Median {np.median(M[sel, 1]):.3f}, n={sel.sum()})")
print("Hypothesen (mittlerer abs. Fehler in 8-Bit-Stufen, alle Kanaele):")
for name, f in HYP.items():
    print(f"  {name:<30} {np.abs(f(M) - S).mean() * 255:6.2f}")
# Gamma-Fit s = m^g
gs = np.arange(0.9, 1.5, 0.01)
fehler = [np.abs(np.clip(M, 0, 1) ** g - S).mean() * 255 for g in gs]
print(f"  bester Potenz-Fit s = m^{gs[int(np.argmin(fehler))]:.2f}: {min(fehler):.2f}")
# Hypothese Video-Pegel am Eingang: x' = (x*1023-64)/876
fehl_v, fehl_f = [], []
for (key, xw, v), s_px in zip(paare_x, paare_s):
    xv = (xw * 1023 - 64) / 876
    fehl_v.append(np.abs(PM.render(xv[None], v)[0] - s_px).mean() * 255)
    fehl_f.append(np.abs(PM.render(xw[None], v)[0] - s_px).mean() * 255)
print(f"  Eingang als Video-Pegel gelesen   {np.mean(fehl_v):6.2f}  (Full wie Modell: {np.mean(fehl_f):.2f})")
