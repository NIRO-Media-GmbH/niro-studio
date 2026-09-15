"""Selbstprüfung plan.json: je Block ein Bogen mit Anfangs- und Endbild jedes Shots (nächstes 5-fps-Sample
innerhalb des Fensters) → Blenden, Schwarzbilder, Szenensprünge im Fenster werden sichtbar.

Aufruf: check_plan.py [plan.json] [ausgabeordner]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SCR = "/private/tmp/claude-501/-Users-jansantos-NIRO-Studio/8134ca39-169a-4a0c-8512-9571e81da50f/scratchpad"
PLAN = sys.argv[1] if len(sys.argv) > 1 else ("/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/"
                                              "2026-09 Hochzeitsmesse/_intern/showreel-analyse/plan.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else f"{SCR}/plan_check"
os.makedirs(OUT, exist_ok=True)
plan = json.load(open(PLAN))
font = ImageFont.load_default(size=20)
FW, FH, LAB, COLS = 320, 180, 26, 3
for b in range(1, 9):
    shots = [p for p in plan["showreel"] if p["block"] == b]
    rows = max(1, (len(shots) + COLS - 1) // COLS)
    sheet = Image.new("RGB", (COLS * (2 * FW + 8), rows * (FH + LAB)), (15, 15, 15))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(shots):
        x, y = (i % COLS) * (2 * FW + 8), (i // COLS) * (FH + LAB)
        first = -(-p["src_in"] // 5)            # erstes Sample im Fenster
        last = (p["src_out"] - 1) // 5          # letztes Sample im Fenster
        for m, n in enumerate((first, last)):
            path = f"{SCR}/frames/{p['film']}/{n:06d}.jpg"
            if os.path.exists(path):
                sheet.paste(Image.open(path).resize((FW, FH)), (x + m * FW, y + LAB))
        d.text((x + 4, y + 3), f"{p['slot']:>2} {p['kategorie'][:14]} {p['id']} W{p['wert']} {p['frames']}f",
               fill=(255, 220, 120), font=font)
    sheet.save(f"{OUT}/check_block_{b}.png")
print("Prüfbögen:", OUT)
