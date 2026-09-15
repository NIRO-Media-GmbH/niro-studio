"""Sprecher-Reinheit: zitierte Bereiche duerfen nur vom Haupt-Sprecher (Fabrice) stammen.
Haupt-Sprecher je Clip = der mit den meisten Woertern (traegt die gescripteten Takes)."""
import json, re, sys
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
          "Einfamilienhaus-und-Smartino/2026-07 Dreh")
INTERN, PLANS = CH / "_intern", CH / "Ergebnisse/O-Ton-Pläne"
utt = {r["name"].rsplit(".", 1)[0]: r for r in
       json.loads((INTERN / "utterances.json").read_text())}

def stem_of(s):
    return "a7MK4_20260721_" + s[3:] if s.startswith("a7_") else s

def secs(tc):
    m, s = tc.split(":"); return int(m) * 60 + int(s)

SRC = re.compile(r"·\s*(?:[\w/]*?/)?((?:a7_|FX3_)\d+)\s*·\s*(\d+:\d\d)[–-](\d+:\d\d)")
problems, ok = [], 0

for md in sorted(PLANS.glob("video-*.md")):
    for line in md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        m = SRC.search(cells[3] if len(cells) > 3 else "")
        if not m:
            continue
        short, von, bis = m.groups()
        rec = utt[stem_of(short)]
        # Haupt-Sprecher des Clips
        wc = {}
        for u in rec["utterances"]:
            wc[u["speaker"]] = wc.get(u["speaker"], 0) + len(u["text"].split())
        main = max(wc, key=wc.get)
        a, b = secs(von), secs(bis)
        fremd = [u for u in rec["utterances"]
                 if u["speaker"] != main and u["bis_s"] > a + 0.6 and u["von_s"] < b - 0.6]
        if fremd:
            problems.append(f"{md.name} [{short} {von}-{bis}]: Fremdsprecher im Bereich -> "
                            + "; ".join(f"{u['von']}-{u['bis']} \"{u['text'][:55]}\"" for u in fremd[:2]))
        else:
            ok += 1

print(f"{ok} Bereiche sprecher-rein")
if problems:
    print(f"\n{len(problems)} PROBLEME:")
    for p in problems: print(" -", p)
    sys.exit(1)
print("Kein Regie-Ton in zitierten Bereichen.")
