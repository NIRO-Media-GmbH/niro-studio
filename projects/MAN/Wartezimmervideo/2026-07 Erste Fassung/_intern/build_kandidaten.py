#!/usr/bin/env python3
"""Interview-Kandidaten aus scan.csv: groesste Dateien je Dreh -> interview-kandidaten.md

Heuristik (Plan Task 2): je Dreh alle Dateien mit size_gb >= 3 ODER dur_min >= 8,
UND audio_kanaele >= 1; mindestens Top 10 je Dreh nach Groesse.
"""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
rows = [r for r in csv.DictReader(open(HERE / "scan.csv"))
        if "/Proxy/" not in r["relpath"]]
for r in rows:
    r["size_gb"] = float(r["size_gb"])
    r["dur_min"] = float(r["dur_min"])
    r["audio_kanaele"] = int(r["audio_kanaele"])

by_dreh = defaultdict(list)
for r in rows:
    by_dreh[r["dreh"]].append(r)

out = ["# Interview-Kandidaten — MAN Wartezimmervideo",
       "",
       "Heuristik: je Dreh size >= 3 GB ODER Dauer >= 8 min, mit Audio; mind. Top 10 nach Größe.",
       "Markierung durch David: Zeile mit `[OK]` (transkribieren) oder `[RAUS]` versehen.",
       ""]

for dreh in sorted(by_dreh):
    clips = sorted(by_dreh[dreh], key=lambda r: -r["size_gb"])
    kand = [r for r in clips if (r["size_gb"] >= 3 or r["dur_min"] >= 8)
            and r["audio_kanaele"] >= 1]
    top10 = [r for r in clips if r["audio_kanaele"] >= 1][:10]
    seen = {id(r) for r in kand}
    for r in top10:
        if id(r) not in seen:
            kand.append(r)
    kand.sort(key=lambda r: -r["size_gb"])
    ohne_audio = sum(1 for r in clips if r["audio_kanaele"] == 0)
    out.append(f"## {dreh}")
    out.append(f"{len(clips)} Videodateien gesamt, davon {ohne_audio} ohne Audiospur. "
               f"{len(kand)} Kandidaten:")
    out.append("")
    out.append("| Mark | # | Datei | GB | Min | Audio-Kanäle |")
    out.append("|---|---|---|---|---|---|")
    for i, r in enumerate(kand, 1):
        out.append(f"| [ ] | {i} | `{r['relpath']}` | {r['size_gb']:.1f} | "
                   f"{r['dur_min']:.1f} | {r['audio_kanaele']} |")
    out.append("")

dest = HERE / "interview-kandidaten.md"
dest.write_text("\n".join(out))
print(f"{dest} geschrieben.")
for dreh in sorted(by_dreh):
    clips = by_dreh[dreh]
    kand = [r for r in clips if ((r["size_gb"] >= 3 or r["dur_min"] >= 8)
            and r["audio_kanaele"] >= 1)]
    gb = sum(r["size_gb"] for r in kand)
    mins = sum(r["dur_min"] for r in kand)
    print(f"{dreh}: {len(kand)} Kandidaten (Heuristik), {gb:.0f} GB, {mins:.0f} min")
