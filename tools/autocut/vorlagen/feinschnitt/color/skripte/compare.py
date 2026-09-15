"""Vorlage (Stand 15.09.2026): Look-Varianten nebeneinander (je Variante eigener Fit) — Bogen look_varianten.jpg zur Look-Wahl.

Aufruf (im Ordner _intern/color/skripte, nach fit.py mit cfg3/cfg2/cfg_b/cfg_c): tools/autocut/venv/bin/python compare.py ..
  Argument: Zielordner, muss existieren (Standard „sheets_v4"); „.." = _intern/color, wo der Vorschlag den Bogen erwartet.
Eingaben: Fit-Dateien aus variants (fit3.json, fit2.json, fit_b.json, fit_c.json), frames/*.npy (extract.py).
Ausgabe: <Ziel>/look_varianten.jpg — Spalten = Varianten, Zeilen = spec (Interview-Paar FX3 | a7 oder ein B-Roll-Frame).
Alle Varianten mit derselben CDL-Kette (Angleich + Look je Fit, Log vor LUT); Variante C nutzt den LUT aus ihrer cfg (TypeA).
Herkunft: Taxodia-Session, Scratchpad color/compare.py
"""
import json, numpy as np
from PIL import Image, ImageDraw
from colorlib import LUMA, LUTDIR, apply_lut, downscale, font, label, load_cube, to_u8, yuv_to_rgb

# ── ANPASSEN je Charge ─────────────────────────────
variants = [("D (Vorschlag)  LC-709 | Log-Kontrast 1.20 | Sat 1.03", "fit3.json"), ("A  LC-709 | Log-Kontrast 1.15 | Sat 1.08", "fit2.json"), ("B  LC-709 | Log-Kontrast 1.25 | Sat 1.10", "fit_b.json"), ("C  LC-709 TypeA | Kontrast 1.15 | Sat 1.05", "fit_c.json")]  # Standard (15.09.): Beschriftung, Fit-Datei
spec = [  # Zeilen: (Person-Kürzel, Paar-Nr. 1–6) für ein FX3 | a7-Paar oder (B-Roll-Frame-ID aus ids.json, None) für B-Roll
    # ("Person A", 2),
]
# ── Ende ANPASSEN ──────────────────────────────────

def load_log(fid): return downscale(yuv_to_rgb(np.load(f"frames/{fid}.npy")), 2).astype(np.float32)
def apply_cdl(x, p):
    p = np.asarray(p, np.float32); y = x * p[0:3] + p[3:6]
    l = (y * LUMA.astype(np.float32)).sum(-1, keepdims=True); return l + p[6] * (y - l)
luts = {}
TW, TH = 330, 186
W = len(variants) * 2 * TW
head = Image.new("RGB", (W, 36), (35, 35, 35)); d = ImageDraw.Draw(head)
for v, (name, _) in enumerate(variants):
    d.text((v * 2 * TW + 10, 8), name, fill=(240, 240, 240), font=font(18))
rows = [head]
for key, i in spec:
    row = Image.new("RGB", (W, TH), (0, 0, 0))
    for v, (name, fj) in enumerate(variants):
        fit = json.load(open(fj)); ln = fit["cfg"].get("lut", "SLog3SGamut3.CineToLC-709.cube")
        lut = luts.setdefault(ln, load_cube(LUTDIR + ln))
        if i is not None:
            st = fit["sets"][key]
            cells = [(f"{key}_{i}_FX3", st["FX3_cdl_gesamt"]), (f"{key}_{i}_A7", st["A7_cdl_gesamt"])]
        else:
            x = load_log(key); crop = x[:, 60:900]  # zwei Kacheln aus einem B-Roll-Frame: links/rechts
            cells = [(key, fit["broll"]["FX3A_cdl_gesamt"])]
        for c, (fid, p) in enumerate(cells):
            img = apply_lut(np.clip(apply_cdl(load_log(fid), p), 0, 1), lut)
            w = TW if i is not None else 2 * TW
            im = Image.fromarray(to_u8(img)).resize((w, TH if i is not None else int(w * 9 / 16)), Image.LANCZOS)
            if i is None:
                top = (im.height - TH) // 2; im = im.crop((0, top, w, top + TH))
            row.paste(im, ((v * 2 + c) * TW, 0))
        label(row, f"{key}" + (f" #{i}  FX3 | a7" if i else ""), 13, (v * 2 * TW + 6, 4))
    rows.append(row)
out = Image.new("RGB", (W, sum(r.height for r in rows))); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
import sys
out.save((sys.argv[1] if len(sys.argv) > 1 else "sheets_v4") + "/look_varianten.jpg", quality=90); print("ok")
