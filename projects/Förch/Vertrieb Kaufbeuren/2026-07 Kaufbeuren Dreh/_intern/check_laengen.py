# -*- coding: utf-8 -*-
"""Längen-Realismus-Check: Ablauf-Tabellen der video-*.md parsen,
O-Ton-Wörter zählen (2,4 W/s), +1 s je Szenenwechsel, +3 s Endcard,
gegen Ziellänge aus 'Ziel & Story' halten."""
import re, glob, os

BASE = "/Users/jansantos/NIRO Studio/projects/Förch/Vertrieb Kaufbeuren/2026-07 Kaufbeuren Dreh/Ergebnisse/O-Ton-Pläne"
RATE = 2.4  # Wörter/Sekunde

def parse_target(text):
    m = re.search(r"Ziellänge\s*~?\s*(\d+)(?:\s*[–-]\s*(\d+))?\s*s", text)
    if not m:
        return None
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    return lo, hi

def clean_quote(cell):
    cell = cell.strip()
    if cell in ("—", "-", "") or cell.startswith("— ("):
        return ""
    # […]-Marker und Auslassungs-„…" raus
    cell = cell.replace("[…]", " ").replace("…", " ")
    # Anführungszeichen/Regie raus
    cell = re.sub(r"[„“”‚‘’\"']", " ", cell)
    return cell

def count_words(cell):
    txt = clean_quote(cell)
    if not txt:
        return 0
    words = [w for w in re.split(r"\s+", txt) if re.search(r"[A-Za-zÄÖÜäöüß0-9]", w)]
    return len(words)

for path in sorted(glob.glob(os.path.join(BASE, "video-*.md"))):
    text = open(path, encoding="utf-8").read()
    tgt = parse_target(text)
    rows = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| #"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            if re.match(r"^\|[-\s|]+$", line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                rows.append(cells)
    n_rows = len(rows)
    endcard_rows = [r for r in rows if ("Endcard" in r[1] or "Abbinder" in r[1])]
    caption_only = [r for r in rows if count_words(r[2]) == 0 and r not in endcard_rows]
    total_words = sum(count_words(r[2]) for r in rows)
    speech_s = total_words / RATE
    changes = n_rows - 1  # Szenenwechsel
    est = speech_s + changes * 1.0 + 3.0  # Endcard pauschal 3 s
    name = os.path.basename(path)
    per_row = ", ".join(f"#{r[0]}:{count_words(r[2])}W" for r in rows)
    print(f"== {name}")
    print(f"   Zeilen: {n_rows} (davon Endcard/Abbinder: {len(endcard_rows)}, Caption-only: {len(caption_only)})")
    print(f"   Wörter je Beat: {per_row}")
    print(f"   Summe {total_words} W -> {speech_s:.1f} s Sprache + {changes} s Wechsel + 3 s Endcard = {est:.1f} s")
    if tgt:
        lo, hi = tgt
        over = (est - hi) / hi * 100
        under = (est - lo) / lo * 100
        print(f"   Ziel: {lo}–{hi} s | Abw. zur Obergrenze: {over:+.0f} % | zur Untergrenze: {under:+.0f} %")
    else:
        print("   Ziel: NICHT GEFUNDEN")
    print()
