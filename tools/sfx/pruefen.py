"""Abschlussprüfung der SFX-Library (nur lesend).

- jede Plan-Zeile hat genau eine Datei, keine fremden/übrigen Dateien, keine .teil-Reste
- Dauer der Kopie = Dauer des Originals (ffprobe), Titel-Tag lesbar
- Originale auf dem NAS unverändert (Größe + Änderungszeit wie beim Scan)
- Katalog hat eine Zeile pro Datei

    venv/bin/python pruefen.py
"""
import csv
import json
import os
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from config import DATA, LIBRARY


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags=title", "-of", "json", p],
                       capture_output=True, text=True, timeout=120)
    d = json.loads(r.stdout or "{}").get("format", {})
    return float(d.get("duration") or 0), (d.get("tags") or {}).get("title", "")


def main():
    plan = json.load(open(DATA / "plan.json"))
    stand = json.load(open(DATA / "build_stand.json"))
    fehler = []

    nfc = lambda p: unicodedata.normalize("NFC", p)  # SMB speichert Namen zerlegt (NFD)
    erwartet = {nfc(os.path.join(LIBRARY, stand[e["key"]]["ziel"])): e for e in plan
                if e["key"] in stand and stand[e["key"]].get("von_hand") not in ("entfernt", "fehlt")}
    fehler += [f"nicht gebaut: {e['ziel']}" for e in plan if e["key"] not in stand]
    vorhanden = set()
    for dirpath, _, files in os.walk(LIBRARY):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if fn.endswith(".teil"):
                fehler.append(f"Teildatei übrig: {p}")
            elif "/_intern/" not in p and not fn.startswith(("_", ".")):
                vorhanden.add(nfc(p))
    fehler += [f"fehlt: {p}" for p in set(erwartet) - vorhanden]
    fehler += [f"unerwartet: {p}" for p in vorhanden - set(erwartet)]

    pfade = sorted(set(erwartet) & vorhanden)
    with ThreadPoolExecutor(8) as ex:
        ergebnisse = dict(zip(pfade, ex.map(probe, pfade)))
    for p, (dauer, titel) in ergebnisse.items():
        e = erwartet[p]
        if abs(dauer - e["dauer"]) > 0.1:
            fehler.append(f"Dauer {dauer:.2f} ≠ {e['dauer']:.2f}: {p}")
        if not titel and p.lower().endswith((".wav", ".mp3", ".m4a")) and not stand[e["key"]].get("unveraendert"):
            fehler.append(f"kein Titel-Tag: {p}")

    scan = {}
    for line in open(DATA / "nas_scan.tsv", encoding="utf-8"):
        size, mtime, pfad = line.rstrip("\n").split("\t", 2)
        scan[pfad] = (int(size), int(mtime))
    originale = {f for e in plan for f in e["fundstellen"]}
    for f in originale:
        st = os.stat(f)
        if (st.st_size, int(st.st_mtime)) != scan.get(f):
            fehler.append(f"Original verändert?: {f}")

    with open(LIBRARY / "_Katalog.csv", encoding="utf-8-sig") as fh:
        zeilen = list(csv.reader(fh, delimiter=";"))[1:]
    if len(zeilen) != len(pfade):
        fehler.append(f"Katalog: {len(zeilen)} Zeilen, {len(pfade)} Dateien")

    groesse = sum(os.path.getsize(p) for p in pfade)
    print(f"{len(pfade)} Dateien ({groesse / 1e9:.1f} GB) geprüft, {len(originale)} Originale unverändert geprüft")
    print(f"{len(fehler)} Befunde")
    for f in fehler[:50]:
        print("  -", f)


if __name__ == "__main__":
    main()
