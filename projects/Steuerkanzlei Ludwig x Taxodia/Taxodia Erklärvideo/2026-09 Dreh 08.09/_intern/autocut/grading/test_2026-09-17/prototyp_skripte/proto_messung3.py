"""Prototyp Grading-Test 17.09.: Messung Belichtung + Weissabgleich je Test-Clip (Spec 2026-09-17, Design 5 vereinfacht).

Ablauf: Originale dekodieren (10 Bit, 960x540) -> LUT-Vorschau -> Vision-Gesichter -> je Bild 3 Runden WB/Belichtung
-> Clip-Wert = Median -> Renders (nur LUT, neu, alt fuer Interviews) am Standbild-Frame -> werte.json.
Abweichungen vom Spec (Prototyp): WB-Runde 1 nimmt die 20 % farbarmsten Pixel statt C* <= 12; kein Mischlicht-2-Means;
Node 02 neutral (auch a7).
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
import colorlib as CL  # noqa: E402

SP = Path(__file__).resolve().parent / "proto"
for d in ("frames", "faces_in", "render"):
    (SP / d).mkdir(parents=True, exist_ok=True)
FACES = Path(__file__).resolve().parent / "faces"
LUT = CL.load_cube(CL.LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
P = 420.0 / 1023.0
STOP = float(CL.STOP)
LUMA = CL.LUMA.astype(np.float32)
LOOK = (1.05, 1.00)  # Kontrast, Saettigung (Node 03, Startwerte Look-Profil)
PROFIL = dict(haut_L=65.0, neutral_hell_L=88.0, neutral_hell_min=0.05, bild_L=50.0, bild_staerke=0.7, bild_ohne_ab_L=90.0,
              lichter_L=98.0, lichter_zusatz=0.02, grenze_e=8.0, ziel_a=0.0, ziel_b=2.0, neutral_L=(30.0, 95.0),
              neutral_min=0.02, haut_winkel=(45.0, 70.0), haut_winkel_ziel=57.5, grenze_w=1.0, gesicht_min=0.004)
NAS = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Steuerkanzlei Ludwig x Taxodia/02_Projekte/01_Taxodia Erklärvideo/03_Medien/01_Footage/"
ITEMS = [
    dict(key="V1_1372_FX3_0222", clip="FX3_0222", pfad=NAS + "Kamera-B/FX3_0222.MP4", start=1372, dauer=242, src=7003, fps=25, tempo=100, still=1540, art="interview", person="Ludwig", cam="FX3"),
    dict(key="V1_971_FX3_0228", clip="FX3_0228", pfad=NAS + "Kamera-B/FX3_0228.MP4", start=971, dauer=278, src=1222, fps=25, tempo=100, still=1010, art="interview", person="Hein", cam="FX3"),
    dict(key="V1_1788_FX3_0223", clip="FX3_0223", pfad=NAS + "Kamera-B/FX3_0223.MP4", start=1788, dauer=347, src=1479, fps=25, tempo=100, still=1850, art="interview", person="Flammann", cam="FX3"),
    dict(key="V2_652_a7_0118", clip="a7MK4_20260908_0118", pfad=NAS + "Kamera-A/a7MK4_20260908_0118.MP4", start=652, dauer=72, src=14820, fps=25, tempo=100, still=680, art="interview", person="Ludwig", cam="a7_IV"),
    dict(key="V3_2169_C0242", clip="C0242", pfad=NAS + "B-Roll/C0242.MP4", start=2169, dauer=62, src=116, fps=50, tempo=50, still=2200, art="broll"),
    dict(key="V3_2576_C0246", clip="C0246", pfad=NAS + "B-Roll/C0246.MP4", start=2576, dauer=78, src=631, fps=50, tempo=50, still=2615, art="broll"),
    dict(key="V3_4167_C0255", clip="C0255", pfad=NAS + "B-Roll/C0255.MP4", start=4167, dauer=134, src=5513, fps=50, tempo=50, still=4234, art="broll"),
    dict(key="V3_5038_C0261", clip="C0261", pfad=NAS + "B-Roll/C0261.MP4", start=5038, dauer=58, src=12245, fps=50, tempo=100, still=5067, art="broll"),
]


def quellframe(it, f):
    return int(round(it["src"] + (f - it["start"]) * it["tempo"] / 100 * it["fps"] / 25))


def decode(pfad, n, fps):
    """Originalbild n (10 Bit 4:2:2, full range wie orig_check.py) -> S-Log3-CV/1023 RGB 960x540 float32."""
    cache = SP / "frames" / f"{Path(pfad).stem}_{n}.npy"
    if cache.exists():
        return np.load(cache).astype(np.float32)
    t = (n - 0.25) / fps
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", pfad, "-frames:v", "1", "-f", "rawvideo",
                        "-pix_fmt", "yuv422p10le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(b, np.uint16)
    Y = a[:3840 * 2160].reshape(2160, 3840).astype(np.float32)
    Cb = a[3840 * 2160:3840 * 2160 + 1920 * 2160].reshape(2160, 1920).astype(np.float32)
    Cr = a[3840 * 2160 + 1920 * 2160:].reshape(2160, 1920).astype(np.float32)
    y = Y.reshape(540, 4, 960, 4).mean((1, 3)) / 1023
    pb = (Cb.reshape(540, 4, 960, 2).mean((1, 3)) - 512) / 1023
    pr = (Cr.reshape(540, 4, 960, 2).mean((1, 3)) - 512) / 1023
    r = y + 2 * (1 - CL.KR) * pr
    bb = y + 2 * (1 - CL.KB) * pb
    g = (y - CL.KR * r - CL.KB * bb) / CL.KG
    x = np.stack([r, g, bb], -1).astype(np.float32)
    np.save(cache, x.astype(np.float16))
    return x


SENSOR_CLIP = 888 / 1023  # FX3/FX3A S-Log3-Clip-Plateau CV 891 (gemessen 17.09.)


def belichtung_linear(x, e, wr, wb):
    """Echte Belichtung: lineare Verstaerkung je Kanal in S-Log3 (Schwarz bleibt schwarz)."""
    g = (2.0 ** np.array([e + wr, e, e + wb])).astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        lin = CL.slog3_to_lin(x.astype(np.float64)) * g
        return np.nan_to_num(CL.lin_to_slog3(lin)).astype(np.float32)


def render(x, v, look=LOOK):
    k, s = look
    y = belichtung_linear(x, v["e"], v["wr"], v["wb"])
    y = k * y + P * (1 - k)
    lum = (y * LUMA).sum(-1, keepdims=True)
    y = lum + s * (y - lum)
    return CL.apply_lut(np.clip(y, 0, 1).astype(np.float32), LUT)


def render_alt(x, w):
    return CL.apply_lut(CL.cdl(x, w["slope"], w["offset"], (1, 1, 1), w["saturation"]).astype(np.float32), LUT)


def lab(x, v):
    return CL.disp_to_lab(render(x, v)).astype(np.float32)


def bisekt(fn, ziel, lo=-8.0, hi=8.0, tol=0.01):
    flo, fhi = fn(lo), fn(hi)
    if ziel <= flo:
        return lo
    if ziel >= fhi:
        return hi
    while hi - lo > tol:
        m = (lo + hi) / 2
        if fn(m) < ziel:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def gesichter(key_n_liste):
    out = subprocess.run([str(FACES), str(SP / "faces_in")], capture_output=True, text=True, check=True).stdout
    boxen = {}
    for zeile in out.strip().splitlines():
        name, _, rest = zeile.partition("\t")
        bs = []
        for teil in filter(None, rest.split(";")):
            if teil == "ERR":
                continue
            x0, y0, x1, y1, c = map(float, teil.split(","))
            bs.append((x0, y0, x1, y1, c))
        boxen[name[:-4]] = bs
    return boxen


def masken(boxen, H=540, W=960):
    haut = np.zeros((H, W), bool)
    gesicht_gross = np.zeros((H, W), bool)
    anteil = 0.0
    for x0, y0, x1, y1, c in boxen:
        if (x1 - x0) * (y1 - y0) < PROFIL["gesicht_min"] or c < 0.5:
            continue
        anteil += (x1 - x0) * (y1 - y0)
        w, h = x1 - x0, y1 - y0
        haut[int((y0 + 0.35 * h) * H):int((y0 + 0.80 * h) * H), int((x0 + 0.25 * w) * W):int((x0 + 0.75 * w) * W)] = True
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        gesicht_gross[int(max(0, cy - 0.75 * h) * H):int(min(1, cy + 0.75 * h) * H),
                      int(max(0, cx - 0.75 * w) * W):int(min(1, cx + 0.75 * w) * W)] = True
    return haut, gesicht_gross, anteil


def messe_bild(x, boxen):
    haut_m, gross_m, g_anteil = masken(boxen)
    hat_gesicht = haut_m.sum() > 50
    v = {"e": 0.0, "wr": 0.0, "wb": 0.0}
    hinweise = []
    unclip = x.max(-1) < SENSOR_CLIP
    for runde in range(3):
        # ---- Weissabgleich ----
        L = lab(x, v)
        C = np.hypot(L[..., 1], L[..., 2])
        eligible = (L[..., 0] >= PROFIL["neutral_L"][0]) & (L[..., 0] <= PROFIL["neutral_L"][1]) & (L[..., 0] < 97) & unclip & ~gross_m
        if runde == 0:
            thr = np.percentile(C[eligible], 20) if eligible.sum() > 1000 else 0
            kand = eligible & (C <= thr)
        else:
            kand = eligible & (C <= (8.0 if runde == 1 else 5.0))
            if kand.mean() < PROFIL["neutral_min"] and eligible.sum() > 1000:
                kand = eligible & (C <= np.percentile(C[eligible], 20))
                hinweise.append(f"R{runde}: Neutral-Anker nur relativ")
        anteil_neutral = float(kand.mean())
        wb_anker = None
        if anteil_neutral >= PROFIL["neutral_min"]:
            xs = x[kand]
            cs = C[kand]
            xs = xs[cs <= np.median(cs)]
            if len(xs) > 20000:
                xs = xs[np.random.default_rng(runde).choice(len(xs), 20000, replace=False)]

            def ab(wr, wb):
                l = CL.disp_to_lab(render(xs[None], {**v, "wr": wr, "wb": wb})[0])
                return np.array([np.median(l[:, 1]), np.median(l[:, 2])])
            w = np.array([v["wr"], v["wb"]])
            ziel = np.array([PROFIL["ziel_a"], PROFIL["ziel_b"]])
            for _ in range(4):
                f0 = ab(*w)
                J = np.column_stack([(ab(w[0] + 0.02, w[1]) - f0) / 0.02, (ab(w[0], w[1] + 0.02) - f0) / 0.02])
                try:
                    w = w - np.linalg.solve(J, f0 - ziel)
                except np.linalg.LinAlgError:
                    break
                w = np.clip(w, -PROFIL["grenze_w"], PROFIL["grenze_w"])
            v["wr"], v["wb"] = float(w[0]), float(w[1])
            wb_anker = "neutral"
            if hat_gesicht:
                hs = x[haut_m]
                lh = CL.disp_to_lab(render(hs[None], v)[0])
                h_haut = float(np.degrees(np.arctan2(np.median(lh[:, 2]), np.median(lh[:, 1]))))
                if h_haut < PROFIL["haut_winkel"][0] - 5 or h_haut > PROFIL["haut_winkel"][1] + 5:
                    hinweise.append(f"Mischlicht/Haut ausserhalb ({h_haut:.0f} Grad) - Gesicht von Hand")
                if False:
                    # Mischlicht: Neutralflaechen und Gesicht haben verschiedenes Licht -> Gesicht entscheidet (Warm-Kalt-Achse)
                    def hue_m(t):
                        l = CL.disp_to_lab(render(hs[None], {**v, "wr": v["wr"] + t, "wb": v["wb"] - t})[0])
                        return float(np.degrees(np.arctan2(np.median(l[:, 2]), np.median(l[:, 1]))))
                    raster = np.arange(-1.0, 1.0 + 1e-6, 0.02)
                    t = float(raster[int(np.argmin([abs(hue_m(t) - PROFIL["haut_winkel_ziel"]) for t in raster]))])
                    v["wr"] = float(np.clip(v["wr"] + t, -PROFIL["grenze_w"], PROFIL["grenze_w"]))
                    v["wb"] = float(np.clip(v["wb"] - t, -PROFIL["grenze_w"], PROFIL["grenze_w"]))
                    wb_anker = "haut_mischlicht"
                    hinweise.append(f"Mischlicht (Haut {h_haut:.0f}°)")
        elif hat_gesicht:
            xs = x[haut_m]

            def hue(t):
                l = CL.disp_to_lab(render(xs[None], {**v, "wr": t, "wb": -t})[0])
                return float(np.degrees(np.arctan2(np.median(l[:, 2]), np.median(l[:, 1]))))
            raster = np.arange(-PROFIL["grenze_w"], PROFIL["grenze_w"] + 1e-6, 0.02)
            t = float(raster[int(np.argmin([abs(hue(t) - PROFIL["haut_winkel_ziel"]) for t in raster]))])
            v["wr"], v["wb"] = float(t), float(-t)
            wb_anker = "haut"
        # ---- Belichtung ----
        L0 = lab(x, {**v, "e": 0.0})
        if hat_gesicht:
            hs = x[haut_m]
            lh = CL.disp_to_lab(render(hs[None], {**v, "e": 0.0})[0])[:, 0]
            lo_, hi_ = np.percentile(lh, [20, 80])
            hs = hs[(lh >= lo_) & (lh <= hi_)]
            e = bisekt(lambda e: float(np.median(CL.disp_to_lab(render(hs[None], {**v, "e": e})[0])[:, 0])), PROFIL["haut_L"])
            e_anker = "haut"
        else:
            C0 = np.hypot(L0[..., 1], L0[..., 2])
            hell = L0[..., 0] >= np.percentile(L0[..., 0], 60)
            nh = (C0 <= 8) & hell & unclip & (L0[..., 0] < 97)
            if nh.mean() >= PROFIL["neutral_hell_min"]:
                xs = x[nh]
                e = bisekt(lambda e: float(np.median(CL.disp_to_lab(render(xs[None], {**v, "e": e})[0])[:, 0])), PROFIL["neutral_hell_L"])
                e_anker = "neutral_hell"
            else:
                xs = x[L0[..., 0] < PROFIL["bild_ohne_ab_L"]]
                e_voll = bisekt(lambda e: float(np.median(CL.disp_to_lab(render(xs[None], {**v, "e": e})[0])[:, 0])), PROFIL["bild_L"])
                e = PROFIL["bild_staerke"] * e_voll
                e_anker = "bild"
        clip0 = float(((L0[..., 0] >= PROFIL["lichter_L"]) & unclip).mean())
        geschuetzt = False
        while e > 0:
            clip_e = float(((lab(x, {**v, "e": e})[..., 0] >= PROFIL["lichter_L"]) & unclip).mean())
            if clip_e - clip0 <= PROFIL["lichter_zusatz"]:
                break
            e -= 0.05
            geschuetzt = True
        v["e"] = float(np.clip(e, -PROFIL["grenze_e"], PROFIL["grenze_e"]))
    if geschuetzt:
        hinweise.append("Lichterschutz")
    return {**v, "e_anker": e_anker, "wb_anker": wb_anker, "anteil_neutral": round(anteil_neutral, 3),
            "gesicht": bool(hat_gesicht), "hinweise": sorted(set(hinweise))}


def kennwerte(x, v, boxen, renderer):
    haut_m, gross_m, _ = masken(boxen)
    d = renderer(x)
    L = CL.disp_to_lab(d)
    C = np.hypot(L[..., 1], L[..., 2])
    k = {"median_L": round(float(np.median(L[..., 0])), 1), "anteil_L98": round(float((L[..., 0] >= 98).mean()), 3),
         "anteil_L3": round(float((L[..., 0] <= 3).mean()), 3), "chroma_p95": round(float(np.percentile(C, 95)), 1)}
    if haut_m.sum() > 50:
        hl = L[haut_m]
        lo_, hi_ = np.percentile(hl[:, 0], [20, 80])
        hl = hl[(hl[:, 0] >= lo_) & (hl[:, 0] <= hi_)]
        k.update(haut_L=round(float(np.median(hl[:, 0])), 1), haut_C=round(float(np.median(np.hypot(hl[:, 1], hl[:, 2]))), 1),
                 haut_h=round(float(np.degrees(np.arctan2(np.median(hl[:, 2]), np.median(hl[:, 1])))), 1))
    return k


def main():
    vorschlag = json.load(open("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/color/grading_vorschlag.json"))
    auftraege = []
    for it in ITEMS:
        it["mess_frames"] = [quellframe(it, it["start"] + round(q * (it["dauer"] - 1))) for q in (0.2, 0.5, 0.8)]
        it["still_frame"] = quellframe(it, it["still"])
        for n in it["mess_frames"] + [it["still_frame"]]:
            auftraege.append((it, n))
    with ThreadPoolExecutor(8) as ex:
        bilder = list(ex.map(lambda a: (a[0]["key"], a[1], decode(a[0]["pfad"], a[1], a[0]["fps"])), auftraege))
    X = {(k, n): x for k, n, x in bilder}
    for (k, n), x in X.items():
        Image.fromarray(CL.to_u8(render(x, {"e": 0, "wr": 0, "wb": 0}, (1.0, 1.0)))).save(SP / "faces_in" / f"{k}__{n}.jpg", quality=90)
    boxen = gesichter(None)
    ergebnis = {}
    for it in ITEMS:
        je_bild = [messe_bild(X[(it["key"], n)], boxen.get(f"{it['key']}__{n}", [])) for n in it["mess_frames"]]
        clip = {k: float(np.median([b[k] for b in je_bild])) for k in ("e", "wr", "wb")}
        xs = X[(it["key"], it["still_frame"])]
        bx = boxen.get(f"{it['key']}__{it['still_frame']}", [])
        neu = kennwerte(xs, clip, bx, lambda x: render(x, clip))
        nur_lut = kennwerte(xs, clip, bx, lambda x: render(x, {"e": 0, "wr": 0, "wb": 0}, (1.0, 1.0)))
        eintrag = {"item": {k: it[k] for k in ("key", "clip", "start", "dauer", "still", "art") if k in it},
                   "mess_frames": it["mess_frames"], "still_frame": it["still_frame"], "je_bild": je_bild,
                   "werte": {k: round(v, 3) for k, v in clip.items()}, "kennwerte_nur_lut": nur_lut, "kennwerte_neu": neu}
        np.save(SP / "render" / f"{it['key']}_neu.npy", render(xs, clip).astype(np.float32))
        np.save(SP / "render" / f"{it['key']}_nurlut.npy", render(xs, {"e": 0, "wr": 0, "wb": 0}, (1.0, 1.0)).astype(np.float32))
        if it["art"] == "interview":
            w = vorschlag["cdl_je_kamera_und_set"][it["person"]][it["cam"]]["node1_gesamt_log_vor_LUT"]
            eintrag["kennwerte_alt"] = kennwerte(xs, clip, bx, lambda x: render_alt(x, w))
            np.save(SP / "render" / f"{it['key']}_alt.npy", render_alt(xs, w).astype(np.float32))
        else:
            eintrag["kennwerte_alt_ohne_trim"] = kennwerte(xs, clip, bx, lambda x: render_alt(x, vorschlag["b_roll_FX3A"]["node1_gesamt_log_vor_LUT"]))
        ergebnis[it["key"]] = eintrag
        print(f"{it['key']:<22} e {clip['e']:+.2f} wr {clip['wr']:+.2f} wb {clip['wb']:+.2f} | Anker "
              f"{[b['e_anker'] for b in je_bild]}/{[b['wb_anker'] for b in je_bild]} | neu {neu} | nurLUT {nur_lut}", flush=True)
    json.dump(ergebnis, open(SP / "werte.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
