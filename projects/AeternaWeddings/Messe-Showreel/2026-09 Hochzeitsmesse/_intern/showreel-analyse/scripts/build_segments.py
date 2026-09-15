"""Stufe C: Segmente aus DetectSceneCuts-Shots + Metriken, Fehlschnitt-Merge, Technik-Flags, Kontaktbögen.

Aufruf: build_segments.py [--calibrate]
Ausgabe: <ANALYSE>/segments.json, <SCR>/vision/sheet_###.png + <SCR>/vision/manifest.json
Quellbild-Konvention: Quellbild = Timeline-Frame − 90000; Sample n = Quellbild 5·n.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CHARGE = "/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/2026-09 Hochzeitsmesse"
ANALYSE = f"{CHARGE}/_intern/showreel-analyse"
CUTS = f"{CHARGE}/_intern/cut-detection"
SCR = "/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/8134ca39-169a-4a0c-8512-9571e81da50f/scratchpad"
FILMS = {
    "t1": {"json": "timeline1-scene-cuts.json", "paar": "Lea & Sebastian",
           "src": "/Volumes/personal_folder/Jan/JS/Lea Hochzeit/Lea & Sebastian Hochzeit_V3.mp4"},
    "t2": {"json": "timeline2-scene-cuts.json", "paar": "Jessica & Dominik",
           "src": "/Volumes/personal_folder/Jan/JS/Video_V4.mp4"},
}
FALSE_CUT_CORR = 0.8    # Struktur-Korrelation ±1 s um den Schnitt ≥ Schwelle → Fehlschnitt
MIN_USABLE_FRAMES = 32  # nutzbare Länge nach Randabstand; kürzer passt in keinen Slot


def tc2f(tc):
    h, m, s, fr = map(int, tc.split(":"))
    return ((h * 60 + m) * 60 + s) * 25 + fr


def znorm(a):
    a = a.astype(np.float32)
    return (a - a.mean()) / (a.std() + 1e-6)


def corr(a, b):
    return float((znorm(a) * znorm(b)).mean())


calibrate = "--calibrate" in sys.argv
segments = []
for label, film in FILMS.items():
    if calibrate and not os.path.exists(f"{ANALYSE}/{label}-small.npy"):
        print(label, "noch nicht analysiert – übersprungen")
        continue
    S = np.load(f"{ANALYSE}/{label}-samples.npy")
    small = np.load(f"{ANALYSE}/{label}-small.npy")
    nS = len(S)
    shots = json.load(open(f"{CUTS}/{film['json']}"))["shots"]
    ranges = [(tc2f(s["start_tc"]) - 90000, tc2f(s["end_tc"]) - 90000) for s in shots]

    def sample_at(frame):
        return max(0, min(nS - 1, int(round(frame / 5))))

    # Schnitt-Korrelationen ~1 s vom Schnitt entfernt (Überblendungen würden direkt am Schnitt
    # ähnliche Mischbilder liefern); beste Paarung aus je 2 Samples, innerhalb des jeweiligen Shots
    cut_corr = []
    for (a0, a1), (b0, b1) in zip(ranges, ranges[1:]):
        before = sorted({sample_at(max(a0 + 2, a1 - 25)), sample_at(max(a0 + 2, a1 - 15))})
        after = sorted({sample_at(min(b1 - 3, b0 + 25)), sample_at(min(b1 - 3, b0 + 15))})
        cut_corr.append(max(corr(small[i], small[j]) for i in before for j in after))
    # Blitz-Sandwich: sehr kurzer Shot, Bild davor ≈ Bild danach → beide Schnitte falsch
    false_cut = [c >= FALSE_CUT_CORR for c in cut_corr]
    sandwich = [False] * len(cut_corr)
    for k in range(1, len(ranges) - 1):
        s0, s1 = ranges[k]
        if s1 - s0 <= 12:
            i, j = sample_at(ranges[k - 1][1] - 3), sample_at(ranges[k + 1][0] + 3)
            if corr(small[i], small[j]) >= FALSE_CUT_CORR - 0.1:
                false_cut[k - 1] = false_cut[k] = True
                sandwich[k - 1] = sandwich[k] = True

    if calibrate:
        cc = np.array(cut_corr)
        print(label, "Schnitte", len(cc), "Korrelation Perzentile 10/25/50/75/90:",
              np.round(np.percentile(cc, [10, 25, 50, 75, 90]), 2),
              "| ≥ Schwelle:", int((cc >= FALSE_CUT_CORR).sum()), "| als falsch markiert gesamt:", sum(false_cut))

    # Schnittart: harter Schnitt = ein einzelner Bewegungssprung im ±3-Sample-Fenster → Rand 4 Frames,
    # sonst (Überblendung, unklar) → Rand 15 Frames
    mot = S[:, 6]

    def boundary_edge(c):
        i = sample_at(c)
        win = mot[max(1, i - 3):min(nS - 1, i + 3) + 1]
        if len(win) < 3:
            return 15
        srt = np.sort(win)[::-1]
        return 4 if (srt[0] >= 2.0 * max(1e-6, float(np.median(win))) and srt[1] <= 0.6 * srt[0]) else 15

    edges = [boundary_edge(ranges[k + 1][0]) for k in range(len(ranges) - 1)]
    if calibrate:
        print(label, "harte Schnitte:", edges.count(4), "| weiche/unklare:", edges.count(15))

    # Segmente bilden (mit Randabstand je Seite)
    seg_ranges, seg_edges = [], []
    cur, cur_in = list(ranges[0]), 4
    for k, fc in enumerate(false_cut):
        if fc:
            cur[1] = ranges[k + 1][1]
        else:
            seg_ranges.append(tuple(cur))
            seg_edges.append((cur_in, edges[k]))
            cur, cur_in = list(ranges[k + 1]), edges[k]
    seg_ranges.append(tuple(cur))
    seg_edges.append((cur_in, 4))

    for idx, (f0, f1) in enumerate(seg_ranges):
        edge_in, edge_out = seg_edges[idx]
        i0, i1 = int(np.ceil((f0 + 3) / 5)), int((f1 - 3) // 5)
        rows = S[i0:i1 + 1] if i1 >= i0 else S[sample_at((f0 + f1) / 2):sample_at((f0 + f1) / 2) + 1]
        luma, sharp_c, clip_hi, motion, sat = rows[:, 1], rows[:, 3], rows[:, 4], rows[:, 6], rows[:, 7]
        flags = []
        if (luma < 14).mean() > 0.5:
            flags.append("schwarz")
        if (luma > 215).mean() > 0.3 or (clip_hi > 0.35).mean() > 0.3:
            flags.append("weiss_blitz")
        if f1 - f0 - edge_in - edge_out < MIN_USABLE_FRAMES:
            flags.append("zu_kurz")
        segments.append({
            "id": f"{label}-{idx + 1:03d}", "film": label, "paar": film["paar"],
            "src_start": int(f0), "src_end": int(f1), "frames": int(f1 - f0),
            "edge_in": edge_in, "edge_out": edge_out,
            "merged_shots": sum(1 for r in ranges if r[0] >= f0 and r[1] <= f1),
            "luma_med": round(float(np.median(luma)), 1), "sharp_c_med": round(float(np.median(sharp_c)), 1),
            "motion_med": round(float(np.median(motion)), 2), "motion_max": round(float(motion.max()), 2),
            "sat_med": round(float(np.median(sat)), 1), "tech_flags": flags,
            # zusammengeführte (vermutlich falsche) Schnitte im Segment: [Quellframe, Korrelation, Blitz-Sandwich]
            "internal_cuts": [[int(ranges[k + 1][0]), round(cut_corr[k], 2), sandwich[k]]
                              for k in range(len(cut_corr)) if f0 < ranges[k + 1][0] < f1],
        })
    print(label, "Shots", len(ranges), "→ Segmente", len(seg_ranges),
          "| technisch aussortiert:", sum(1 for s in segments if s["film"] == label and s["tech_flags"]))

if calibrate:
    sys.exit(0)

json.dump(segments, open(f"{ANALYSE}/segments.json", "w"), ensure_ascii=False, indent=1)

# Kontaktbögen: 6 Segmente je Bogen, je 3 Frames (20/50/80 %) à 480×270 + Kennung
vis = f"{SCR}/vision"
os.makedirs(vis, exist_ok=True)
for old in os.listdir(vis):
    if old.startswith("sheet_") and old.endswith(".png"):
        os.remove(os.path.join(vis, old))
cands = [s for s in segments if not s["tech_flags"]]
font = ImageFont.load_default(size=26)
TW, TH, LAB = 480, 270, 34
manifest = []
for b in range(0, len(cands), 6):
    group = cands[b:b + 6]
    sheet = Image.new("RGB", (TW * 3, (TH + LAB) * len(group)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for r, seg in enumerate(group):
        y = r * (TH + LAB)
        draw.text((8, y + 3), f"{seg['id']}   {seg['frames'] / 25:.1f} s", fill=(255, 220, 120), font=font)
        for c, q in enumerate((0.2, 0.5, 0.8)):
            n = int(round((seg["src_start"] + q * seg["frames"]) / 5))
            p = f"{SCR}/frames/{seg['film']}/{n:06d}.jpg"
            if os.path.exists(p):
                sheet.paste(Image.open(p).resize((TW, TH)), (c * TW, y + LAB))
    name = f"sheet_{b // 6 + 1:03d}.png"
    sheet.save(f"{vis}/{name}")
    manifest.append({"sheet": name, "ids": [s["id"] for s in group]})
json.dump(manifest, open(f"{vis}/manifest.json", "w"), indent=1)
print("Kandidaten:", len(cands), "| Bögen:", len(manifest))
