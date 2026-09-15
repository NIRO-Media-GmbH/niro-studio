"""Vorlage (Stand 15.09.2026): Kontaktboegen: Log roh | Sony LC-709 | LC-709 + Angleich-CDL + Look-CDL (beide Log vor LUT).

Aufruf (im Ordner _intern/color/skripte): tools/autocut/venv/bin/python sheets.py fit3.json .. [TAG]
  Argumente: Fit-Ergebnis (fit.py), Zielordner (Standard skripte/sheets; „.." = _intern/color, wo der Vorschlag die Bögen erwartet),
  optionaler Zusatztext in der Kopfzeile.
Eingaben: <fit>.json, frames/*.npy (extract.py), faces.tsv (faces auf lutjpg/), ids.json (lutjpg.py). Personen = Sets im Fit.
Ausgaben: kontaktbogen_<Person>.jpg (6 Paare: FX3/a7 Log roh | LC-709 | LC-709 + Angleich + Look), gesichter_<Person>.jpg
(Gesichtsausschnitte nur LUT | final), kontaktbogen_BRoll.jpg (8 B-Roll-Frames, 4 × 2), uebersicht_final.jpg (je Person
Paar #2 und #5 final, darunter 8 B-Roll-Frames). Keine chargen-spezifischen Werte; braucht je Person 6 Paare mit Gesicht in
faces.tsv (erstes Gesicht je Frame) und genau 8 B-Roll-Frames in ids.json.
Herkunft: Taxodia-Session, Scratchpad color/sheets.py
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from colorlib import LUMA, LUTDIR, apply_lut, downscale, font, label, load_cube, to_u8, yuv_to_rgb

SP = os.path.dirname(os.path.abspath(__file__))
fit = json.load(open(sys.argv[1]))
OUT = sys.argv[2] if len(sys.argv) > 2 else f"{SP}/sheets"
TAG = sys.argv[3] if len(sys.argv) > 3 else ""
os.makedirs(OUT, exist_ok=True)
lut = load_cube(LUTDIR + fit["cfg"].get("lut", "SLog3SGamut3.CineToLC-709.cube"))
faces = {}
for line in open(f"{SP}/faces.tsv"):
    n, _, rest = line.rstrip("\n").partition("\t")
    faces[n[:-4]] = [tuple(map(float, p.split(","))) for p in rest.split(";")] if rest else []


def load_log(fid):
    return downscale(yuv_to_rgb(np.load(f"{SP}/frames/{fid}.npy")), 2).astype(np.float32)


def apply_cdl(x, p):
    p = np.asarray(p, np.float32)
    y = x * p[0:3] + p[3:6]
    if p[6] != 1.0:
        l = (y * LUMA.astype(np.float32)).sum(-1, keepdims=True)
        y = l + p[6] * (y - l)
    return y


def final(x, p_total):
    return apply_lut(np.clip(apply_cdl(x, p_total), 0, 1), lut)


def tile(arr, w, h, text=None, size=15):
    im = Image.fromarray(to_u8(arr)).resize((w, h), Image.LANCZOS)
    return label(im, text, size) if text else im


def header(width, text, sub=None, h=64):
    im = Image.new("RGB", (width, h), (18, 18, 18))
    d = ImageDraw.Draw(im)
    d.text((14, 8), text, fill=(255, 255, 255), font=font(26))
    if sub:
        d.text((14, 40), sub, fill=(190, 190, 190), font=font(16))
    return im


def colhead(width, labels, h=30):
    im = Image.new("RGB", (width, h), (40, 40, 40))
    d = ImageDraw.Draw(im)
    cw = width // len(labels)
    for i, t in enumerate(labels):
        d.text((i * cw + 10, 6), t, fill=(235, 235, 235), font=font(16))
    return im


def stack(parts, bg=(10, 10, 10)):
    W = max(p.width for p in parts); H = sum(p.height for p in parts)
    out = Image.new("RGB", (W, H), bg); y = 0
    for p in parts:
        out.paste(p, (0, y)); y += p.height
    return out


LOOKTXT = "Look-CDL (Log): slope {0:.3f} offset {1:.4f} sat {2:.2f}".format(fit["look_cdl_log"][0], fit["look_cdl_log"][3], fit["look_cdl_log"][6])
TW, TH = 400, 225
for person in fit["sets"]:
    st = fit["sets"][person]
    pB, pA = st["FX3_cdl_gesamt"], st["A7_cdl_gesamt"]
    rows = [header(TW * 6, f"{person} – FX3 (B-Cam, V1) und a7 IV (A-Cam, V2), zeitgleiche Frames",
                   f"LUT: Sony SLog3SGamut3.CineToLC-709  |  Angleich-CDL je Kamera + {LOOKTXT}  |  alle CDL im Log-Raum vor dem LUT {TAG}"),
            colhead(TW * 6, ["FX3  Log roh", "a7 IV  Log roh", "FX3  LC-709", "a7 IV  LC-709", "FX3  LUT+Angleich+Look", "a7 IV  LUT+Angleich+Look"])]
    fcrop = [header(280 * 4, f"{person} – Gesichter (Ausschnitt)", "links nur LUT, rechts LUT + Angleich + Look", h=60),
             colhead(280 * 4, ["FX3 LUT", "a7 LUT", "FX3 final", "a7 final"])]
    for i in range(1, 7):
        fb, fa = f"{person}_{i}_FX3", f"{person}_{i}_A7"
        xb, xa = load_log(fb), load_log(fa)
        lb, la = apply_lut(xb, lut), apply_lut(xa, lut)
        gb, ga = final(xb, pB), final(xa, pA)
        row = Image.new("RGB", (TW * 6, TH))
        for c, (img, t) in enumerate([(xb, f"#{i}"), (xa, None), (lb, None), (la, None), (gb, None), (ga, None)]):
            row.paste(tile(img, TW, TH, t), (c * TW, 0))
        rows.append(row)
        # Gesichts-Crops
        crow = Image.new("RGB", (280 * 4, 280))
        for c, (img, fid) in enumerate([(lb, fb), (la, fa), (gb, fb), (ga, fa)]):
            x0, y0, x1, y1, _ = faces[fid][0]
            H, W = img.shape[:2]
            cx, cy, s = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H, max((x1 - x0) * W, (y1 - y0) * H) * 1.25
            a, b = int(max(cx - s, 0)), int(max(cy - s, 0))
            crop = img[b:int(min(cy + s, H)), a:int(min(cx + s, W))]
            crow.paste(Image.fromarray(to_u8(crop)).resize((280, 280), Image.LANCZOS), (c * 280, 0))
        fcrop.append(crow)
    stack(rows).save(f"{OUT}/kontaktbogen_{person}.jpg", quality=90)
    stack(fcrop).save(f"{OUT}/gesichter_{person}.jpg", quality=90)

# B-Roll
pR = fit["broll"]["FX3A_cdl_gesamt"]
br = [i for i in json.load(open(f"{SP}/ids.json")) if i.startswith("BR")]
rows = [header(TW * 6, "B-Roll FX3A (50p) – 8 Shots aus broll_auswahl.json", f"LUT: Sony SLog3SGamut3.CineToLC-709  |  B-Roll-CDL + {LOOKTXT}  |  CDL im Log-Raum vor dem LUT {TAG}"),
        colhead(TW * 6, ["Log roh", "LC-709", "LUT+Angleich+Look", "Log roh", "LC-709", "LUT+Angleich+Look"])]
for r in range(4):
    row = Image.new("RGB", (TW * 6, TH))
    for k in range(2):
        fid = br[r * 2 + k]
        x = load_log(fid)
        for c, img in enumerate([x, apply_lut(x, lut), final(x, pR)]):
            row.paste(tile(img, TW, TH, fid if c == 0 else None), ((k * 3 + c) * TW, 0))
    rows.append(row)
stack(rows).save(f"{OUT}/kontaktbogen_BRoll.jpg", quality=90)

# Uebersicht final: je Person Paar #2 + #5, B-Roll 4 Shots
rows = [header(TW * 4, "Übersicht nach Angleich + Look (Sony LC-709)", "je Person zwei zeitgleiche Paare FX3 | a7 IV, darunter B-Roll FX3A"),
        colhead(TW * 4, ["FX3", "a7 IV", "FX3", "a7 IV"])]
for person in fit["sets"]:
    st = fit["sets"][person]
    row = Image.new("RGB", (TW * 4, TH))
    for k, i in enumerate([2, 5]):
        row.paste(tile(final(load_log(f"{person}_{i}_FX3"), st["FX3_cdl_gesamt"]), TW, TH, f"{person} #{i}"), (k * 2 * TW, 0))
        row.paste(tile(final(load_log(f"{person}_{i}_A7"), st["A7_cdl_gesamt"]), TW, TH), ((k * 2 + 1) * TW, 0))
    rows.append(row)
for r in range(2):
    row = Image.new("RGB", (TW * 4, TH))
    for k in range(4):
        fid = br[r * 4 + k]
        row.paste(tile(final(load_log(fid), pR), TW, TH, fid), (k * TW, 0))
    rows.append(row)
stack(rows).save(f"{OUT}/uebersicht_final.jpg", quality=90)
print("ok", OUT)
