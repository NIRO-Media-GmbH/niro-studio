"""Prototyp Gegenprobe 17.09.: ExportLUT vs. Modell, Resolve-Standbilder vs. Rechnung, Kennwerte bisher/neu, Kontaktbogen."""
import json, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
sys.path.insert(0, str(HIER))
import colorlib as CL  # noqa: E402
import proto_messung as PM  # noqa: E402

TEST = Path("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/grading/test_2026-09-17")
STILLS = TEST / "stills"
OUT = HIER / "proto" / "vergleich"
OUT.mkdir(parents=True, exist_ok=True)
EINS3 = np.ones(3, np.float32)


# ---------- 1. ExportLUT gegen Modell ----------
def modell_lut(n1_offset, sat3, n=33):
    g = np.linspace(0, 1, n, dtype=np.float32)
    bb, gg, rr = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([rr, gg, bb], -1)
    y = rgb + np.asarray(n1_offset, np.float32)
    lum = (y * PM.LUMA).sum(-1, keepdims=True)
    y = lum + sat3 * (y - lum)
    return CL.apply_lut(np.clip(y, 0, 1), PM.LUT), rgb


def vergleich_lut(pfad, n1_offset, sat3=0.95):
    ist = CL.load_cube(str(pfad))
    soll, rgb = modell_lut(n1_offset, sat3)
    maske = (rgb >= 0.05).all(-1) & (rgb <= 0.80).all(-1)
    d = np.abs(ist - soll)[maske] * 255
    # Varianten: Saettigung mit anderen Luma-Gewichten (Rec.601) zum Eingrenzen
    return {"mittel_8bit": round(float(d.mean()), 3), "p95_8bit": round(float(np.percentile(d, 95)), 3),
            "max_8bit": round(float(d.max()), 3), "punkte": int(maske.sum())}


# ---------- 2. Standbilder ----------
def still(pfad):
    im = Image.open(pfad).convert("RGB").resize((960, 540), Image.BOX)
    return np.asarray(im).astype(np.float32) / 255


def grau(img):
    return cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)


def homographie(quelle, ziel):
    """quelle (Modellgeometrie) -> ziel (Resolve-Standbild); SIFT + RANSAC."""
    sift = cv2.SIFT_create(4000)
    # Kontrast angleichen fuer die Merkmalssuche (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    a, b = clahe.apply(grau(quelle)), clahe.apply(grau(ziel))
    ka, da = sift.detectAndCompute(a, None)
    kb, db = sift.detectAndCompute(b, None)
    if da is None or db is None:
        return None, 0
    paare = cv2.BFMatcher().knnMatch(da, db, k=2)
    gut = [m for m, n in (p for p in paare if len(p) == 2) if m.distance < 0.75 * n.distance]
    if len(gut) < 12:
        return None, len(gut)
    pa = np.float32([ka[m.queryIdx].pt for m in gut])
    pb = np.float32([kb[m.trainIdx].pt for m in gut])
    H, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 3.0)
    return H, int(inl.sum()) if inl is not None else 0


def delta_e_karte(a, b, maske, zelle=30):
    H, W = maske.shape
    werte = []
    for y in range(0, H - zelle + 1, zelle):
        for x in range(0, W - zelle + 1, zelle):
            m = maske[y:y + zelle, x:x + zelle]
            if m.mean() < 0.98:
                continue
            la = CL.disp_to_lab(a[y:y + zelle, x:x + zelle][m].mean(0))
            lb = CL.disp_to_lab(b[y:y + zelle, x:x + zelle][m].mean(0))
            werte.append(float(CL.de2000(la, lb)))
    w = np.array(werte)
    return {"zellen": len(w), "median": round(float(np.median(w)), 2), "mittel": round(float(w.mean()), 2),
            "p90": round(float(np.percentile(w, 90)), 2)}


def global_lab(a, b, maske):
    la = CL.disp_to_lab(a[maske]).mean(0)
    lb = CL.disp_to_lab(b[maske]).mean(0)
    return {"dL": round(float(lb[0] - la[0]), 2), "da": round(float(lb[1] - la[1]), 2), "db": round(float(lb[2] - la[2]), 2)}


def gegenprobe(modell_bild, still_bild):
    H, inl = homographie(modell_bild, still_bild)
    if H is None:
        return None
    warp = cv2.warpPerspective(modell_bild, H, (960, 540), flags=cv2.INTER_AREA)
    maske = cv2.warpPerspective(np.ones((540, 960), np.float32), H, (960, 540), flags=cv2.INTER_NEAREST) > 0.5
    maske = cv2.erode(maske.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    return {"inlier": inl, "de2000": delta_e_karte(warp, still_bild, maske), "global_resolve_minus_rechnung": global_lab(warp, still_bild, maske)}, warp


def kennwerte_still(img, boxen):
    haut, _, _ = PM.masken(boxen)
    L = CL.disp_to_lab(img)
    C = np.hypot(L[..., 1], L[..., 2])
    k = {"median_L": round(float(np.median(L[..., 0])), 1), "anteil_L98": round(float((L[..., 0] >= 98).mean()), 3),
         "anteil_L3": round(float((L[..., 0] <= 3).mean()), 3), "chroma_p95": round(float(np.percentile(C, 95)), 1)}
    if haut.sum() > 50:
        hl = L[haut]
        lo, hi = np.percentile(hl[:, 0], [20, 80])
        hl = hl[(hl[:, 0] >= lo) & (hl[:, 0] <= hi)]
        k.update(haut_L=round(float(np.median(hl[:, 0])), 1), haut_C=round(float(np.median(np.hypot(hl[:, 1], hl[:, 2]))), 1),
                 haut_h=round(float(np.degrees(np.arctan2(np.median(hl[:, 2]), np.median(hl[:, 1])))), 1))
    return k


def main():
    werte = json.load(open(HIER / "proto" / "werte.json"))
    plan = {f"V{p['spur']}_{p['start']}": p for p in json.load(open(HIER / "proto" / "plan_resolve.json"))}
    bericht = {"exportlut": {
        "probe444 (N1 0.02/0.01/0, Sat 0.95)": vergleich_lut(TEST / "exportlut_probe444.cube", [0.02, 0.01, 0.0]),
        "neu1372 FX3_0222": vergleich_lut(TEST / "exportlut_neu1372.cube", [float(v) for v in plan["V1_1372"]["n1"].split()]),
        "neu2576 C0246": vergleich_lut(TEST / "exportlut_neu2576.cube", [float(v) for v in plan["V3_2576"]["n1"].split()])},
        "items": {}}
    print(json.dumps(bericht["exportlut"], indent=1))
    # Gesichter auf den Standbildern
    fdir = OUT / "faces_still"
    fdir.mkdir(exist_ok=True)
    for f in STILLS.glob("*.png"):
        Image.open(f).convert("RGB").resize((960, 540), Image.BOX).save(fdir / (f.stem + ".jpg"), quality=92)
    boxen = PM.gesichter.__wrapped__(fdir) if hasattr(PM.gesichter, "__wrapped__") else None
    out = subprocess.run([str(PM.FACES), str(fdir)], capture_output=True, text=True, check=True).stdout
    boxen = {}
    for zeile in out.strip().splitlines():
        name, _, rest = zeile.partition("\t")
        boxen[name[:-4]] = [tuple(map(float, t.split(","))) for t in filter(None, rest.split(";")) if t != "ERR"]
    zeilen = []
    for key, e in werte.items():
        it = next(i for i in PM.ITEMS if i["key"] == key)
        f = it["still"]
        b_res, n_res = still(STILLS / f"bisher_{f}.png"), still(STILLS / f"neu_{f}.png")
        eintrag = {"werte": e["werte"], "kennwerte_resolve_bisher": kennwerte_still(b_res, boxen.get(f"bisher_{f}", [])),
                   "kennwerte_resolve_neu": kennwerte_still(n_res, boxen.get(f"neu_{f}", []))}
        # Quellbild-Suche +-2 fuer die Gegenprobe (B-Roll-Timing)
        bestes = None
        for dn in (0, -1, 1, -2, 2):
            n = e["still_frame"] + dn
            x = PM.decode(it["pfad"], n, it["fps"])
            modell = PM.render(x, e["werte"])
            r = gegenprobe(modell, n_res)
            if r is None:
                continue
            if bestes is None or r[0]["de2000"]["median"] < bestes[0]["de2000"]["median"]:
                bestes = (r[0], r[1], n, x)
            if it["art"] == "interview":
                break
        eintrag["gegenprobe_neu"] = {**bestes[0], "quellframe": bestes[2]} if bestes else "keine Ausrichtung"
        if it["art"] == "interview" and bestes:
            w = json.load(open("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/color/grading_vorschlag.json"))["cdl_je_kamera_und_set"][it["person"]][it["cam"]]["node1_gesamt_log_vor_LUT"]
            r_alt = gegenprobe(PM.render_alt(bestes[3], w), b_res)
            eintrag["gegenprobe_bisher_altes_modell"] = r_alt[0] if r_alt else "keine Ausrichtung"
        bericht["items"][key] = eintrag
        zeilen.append((key, it, e, b_res, n_res, bestes[1] if bestes else None, eintrag))
        print(key, json.dumps({k: v for k, v in eintrag.items() if k != "werte"}, ensure_ascii=False))
    json.dump(bericht, open(TEST / "gegenprobe_prototyp.json", "w"), indent=1, ensure_ascii=False)
    # Kontaktbogen: bisher (Resolve) | neu (Resolve) | neu (Rechnung, ausgerichtet)
    W, H = 640, 360
    bogen = Image.new("RGB", (3 * W, len(zeilen) * (H + 26) + 40), (18, 18, 18))
    d = ImageDraw.Draw(bogen)
    kopf = CL.font(22)
    for i, t in enumerate(["BISHER (Resolve-Standbild)", "NEU (Resolve-Standbild)", "NEU (Rechnung, zur Gegenprobe)"]):
        d.text((i * W + 10, 8), t, fill=(255, 255, 255), font=kopf)
    klein = CL.font(15)
    for r, (key, it, e, b_res, n_res, warp, ein) in enumerate(zeilen):
        y0 = 40 + r * (H + 26)
        for c, img in enumerate([b_res, n_res, warp if warp is not None else np.zeros_like(n_res)]):
            bogen.paste(Image.fromarray(CL.to_u8(img)).resize((W, H), Image.LANCZOS), (c * W, y0 + 26))
        kb, kn = ein["kennwerte_resolve_bisher"], ein["kennwerte_resolve_neu"]
        v = e["werte"]
        txt = (f"{it['clip']} @{it['still']}  Node01 e {v['e']:+.2f} R {v['wr']:+.2f} B {v['wb']:+.2f} | Bild-Median L* {kb['median_L']} → {kn['median_L']}"
               + (f" | Haut L* {kb.get('haut_L')} → {kn.get('haut_L')}, Winkel {kb.get('haut_h')}° → {kn.get('haut_h')}°" if 'haut_L' in kn else "")
               + f" | schwarz (L*≤3) {kb['anteil_L3']*100:.0f} % → {kn['anteil_L3']*100:.0f} %")
        gp = ein["gegenprobe_neu"]
        if isinstance(gp, dict):
            txt += f" | Gegenprobe ΔE Median {gp['de2000']['median']}"
        d.text((8, y0 + 5), txt, fill=(235, 235, 235), font=klein)
    bogen.save(TEST / "kontaktbogen_test_bisher_neu.jpg", quality=88)
    print("Bogen:", TEST / "kontaktbogen_test_bisher_neu.jpg")


if __name__ == "__main__":
    main()
