#!/usr/bin/env python3
"""Kontaktboegen fuer B-Roll-Kandidaten-Ordner (laut freigegebenem Konzept).

Sampling: pro Ordner die groessten N Clips (B-Roll: gross ~ ergiebig).
1 Frame alle 5 s (Clips < 60 s) bzw. 10 s, 240px breit, Kacheln 6x5.
Ausgabe: _intern/kontaktboegen/<kapitel>/<ordnerkuerzel>__<clip>.jpg
"""
import csv, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).parent
NAS = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/02_Projekte")
OUT = BASE / "kontaktboegen"

KAPITEL = {
 "kap1": [("Allgemeine B-Roll/Werkstatt B-Roll", 12), ("Schweißen und Flexxen", 12),
          ("02_B-Roll/Allgemeine Tätigkeiten", 12), ("05_Footage sortiert/Actioncam", 6)],
 "kap2": [("02_B-Roll/Teamfoto", 12), ("Jonathan und Nico chillen", 8)],
 "kap3": [("B-Roll/Bestellung für Kunde", 12), ("B-Roll/Waren einlagern", 10),
          ("B-Roll/Kunde holt Paket", 5), ("B-Roll/Ameise", 8), ("05_Footage sortiert/Lagerfootage", 10)],
 "kap4": [("02_B-Roll/Grüner LKW", 15), ("02_B-Roll/Fahrzeuge auf dem Hof", 15),
          ("02_B-Roll/Roter LKW", 10), ("02_B-Roll/Reisebus", 8), ("02_B-Roll/TGE", 8),
          ("Allgemeine B-Roll/LKW Fahren + anheben", 10), ("05_Footage sortiert/Drohnenfootage", 8)],
}

rows = [r for r in csv.DictReader(open(BASE / "scan.csv"))
        if "/Proxy/" not in r["relpath"] and "04_Exportiert" not in r["relpath"]
        and "05_Finale" not in r["relpath"]]

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")[:40]

jobs = []
for kap, folders in KAPITEL.items():
    for frag, limit in folders:
        cand = [r for r in rows if frag in r["relpath"]]
        cand.sort(key=lambda r: -float(r["size_gb"]))
        for r in cand[:limit]:
            jobs.append((kap, frag, r))

print(f"{len(jobs)} Kontaktboegen zu rendern", flush=True)

def render(job):
    kap, frag, r = job
    src = NAS / r["relpath"]
    dur = float(r["dur_min"]) * 60
    fps = "1/5" if dur < 60 else "1/10"
    dest_dir = OUT / kap
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f'{slug(frag.split("/")[-1])}__{Path(r["relpath"]).stem}.jpg'
    dest = dest_dir / name
    if dest.exists() and dest.stat().st_size > 0:
        return True, None
    # Nur Keyframes dekodieren (-skip_frame nokey) + HW-Decode: 10-50x schneller.
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-an",
         "-i", str(src),
         "-vf", f"fps={fps},scale=240:-2,tile=6x5", "-frames:v", "1", str(dest)],
        capture_output=True, text=True)
    if p.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
        return True, None
    return False, f"{r['relpath']}: {p.stderr.strip()[:120]}"

ok = fail = 0
with ThreadPoolExecutor(max_workers=4) as ex:
    for i, (good, err) in enumerate(ex.map(render, jobs), 1):
        if good:
            ok += 1
        else:
            fail += 1
            print(f"FEHLER {err}", flush=True)
        if i % 20 == 0:
            print(f"{i}/{len(jobs)} …", flush=True)
print(f"FERTIG: {ok} ok, {fail} Fehler -> {OUT}", flush=True)
