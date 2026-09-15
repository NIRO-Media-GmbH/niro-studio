import subprocess, os, glob, json  # Gesichts-Check Overlay: Vision-Boxen (faces.swift) gegen Alpha-Maske der Grafikspur
import numpy as np
from PIL import Image

FC = os.path.dirname(os.path.abspath(__file__))  # faces_win.tsv + alpha/ liegen neben dem Skript
ALPHA = "/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/_intern/grafik-komplett/pruef_1080_alpha.mov"
WINDOWS = [("ortsmarke",414,110),("weaning",942,115),("weiterbildung",1205,95),("notaufnahme",1412,100),("cac",1587,115),
           ("zusammenschluss",1860,85),("intensivmarien",2105,76),("lehrkrankenhaus",2533,92),("intensivelisabeth",3097,100)]
faces = {}
for line in open(os.path.join(FC, "faces_win.tsv")):
    name, _, rest = line.rstrip("\n").partition("\t")
    boxes = []
    if rest and rest != "ERR":
        for part in rest.split(";"):
            x0,y0,x1,y1,c = map(float, part.split(","))
            boxes.append((x0,y0,x1,y1,c))
    faces[name] = boxes

os.makedirs(os.path.join(FC, "alpha"), exist_ok=True)
report = {}
W, H = 1920, 1080
for wid, start, dur in WINDOWS:
    out = os.path.join(FC, "alpha", f"{wid}_%04d.png")
    if not glob.glob(os.path.join(FC, "alpha", f"{wid}_*.png")):
        subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",f"{start/25:.3f}","-i",ALPHA,"-t",f"{dur/25:.3f}",
                        "-vf","select=not(mod(n\\,2)),alphaextract,format=gray","-pix_fmt","gray","-vsync","0","-start_number","0",out], check=True)
    rows = []
    for k in range((dur+1)//2):
        fa = os.path.join(FC, "alpha", f"{wid}_{k:04d}.png")
        fj = f"{wid}_{k:04d}.jpg"
        if not os.path.exists(fa): continue
        a = np.array(Image.open(fa).convert("L"))
        m = a > 128
        if not m.any():
            rows.append((start+2*k, None, faces.get(fj, []), None)); continue
        ys, xs = np.where(m)
        gb = (xs.min(), ys.min(), xs.max(), ys.max())  # px at 1920x1080
        mind = None
        for (x0,y0,x1,y1,c) in faces.get(fj, []):
            fx0, fy0, fx1, fy1 = x0*W, y0*H, x1*W, y1*H
            # Kinn/Haar-Puffer: Box um 12 % der Gesichtshöhe nach unten, 8 % seitlich erweitern
            bh, bw = fy1-fy0, fx1-fx0
            fx0 -= 0.08*bw; fx1 += 0.08*bw; fy1 += 0.12*bh
            dx = max(gb[0]-fx1, fx0-gb[2], 0)
            dy = max(gb[1]-fy1, fy0-gb[3], 0)
            d = (dx**2+dy**2)**0.5
            if dx == 0 and dy == 0:
                # Überlappung: Maskenpixel innerhalb der Gesichtsbox zählen
                sub = m[int(max(fy0,0)):int(min(fy1,H)), int(max(fx0,0)):int(min(fx1,W))]
                d = -float(sub.sum())
            mind = d if mind is None else min(mind, d)
        rows.append((start+2*k, gb, faces.get(fj, []), mind))
    report[wid] = rows

for wid, rows in report.items():
    ds = [r[3] for r in rows if r[3] is not None]
    n_faces = sum(1 for r in rows if r[2])
    worst = min(ds) if ds else None
    bad = [(r[0], round(r[3],1)) for r in rows if r[3] is not None and r[3] < 60]
    print(f"{wid:18s} frames={len(rows):3d} mit_gesicht={n_faces:3d} min_abstand_px={'—' if worst is None else round(worst,1)}  kritisch(<60px)={bad[:12]}")
json.dump({k:[(r[0], None if r[1] is None else [int(v) for v in r[1]], r[2], r[3]) for r in v] for k,v in report.items()},
          open(os.path.join(FC,"report.json"),"w"))
