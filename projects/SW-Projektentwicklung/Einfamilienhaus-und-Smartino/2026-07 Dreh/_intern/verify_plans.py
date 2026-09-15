"""Alle Zitate + Timecodes der Video-Plaene gegen die Wortdaten pruefen."""
import json, re, sys
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
          "Einfamilienhaus-und-Smartino/2026-07 Dreh")
INTERN, PLANS = CH / "_intern", CH / "Ergebnisse/O-Ton-Pläne"

STEM = {"a7_0091": "a7MK4_20260721_0091", "a7_0092": "a7MK4_20260721_0092"}
def stem_of(short):
    if short.startswith("a7_"):
        return "a7MK4_20260721_" + short[3:]
    return short

idx = {r["name"].rsplit(".", 1)[0]: r for r in
       json.loads((INTERN / "transcripts_index.json").read_text())}
cache = {}
def words(stem):
    if stem not in cache:
        fp = idx[stem]["fingerprint"]
        data = json.loads((INTERN / "cache" / f"{fp}.scribe.json").read_text())
        cache[stem] = [w for w in data["words"] if w["text"].strip()]
    return cache[stem]

def norm(s):
    s = s.replace("’", "'").replace("‚", "'")
    return re.sub(r"[^a-zäöüß0-9]+", " ", s.lower()).strip()

def secs(tc):
    m, s = tc.split(":")
    return int(m) * 60 + int(s)

SRC = re.compile(r"·\s*(?:[\w/]*?/)?((?:a7_|FX3_)\d+)\s*·\s*(\d+:\d\d)[–-](\d+:\d\d)")
problems, checked = [], 0

for md in sorted(PLANS.glob("video-*.md")):
    for line in md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        quote_cell = cells[2] if len(cells) > 2 else ""
        m = SRC.search(cells[3] if len(cells) > 3 else "")
        if not m:
            continue
        short, von, bis = m.groups()
        stem = stem_of(short)
        if stem not in idx:
            problems.append(f"{md.name}: Clip unbekannt {short}"); continue
        checked += 1
        a, b = secs(von), secs(bis)
        dur = idx[stem]["duration_s"]
        if b > dur + 1:
            problems.append(f"{md.name} [{short} {von}-{bis}]: Ende nach Clipende ({dur}s)")
        if a >= b:
            problems.append(f"{md.name} [{short} {von}-{bis}]: Bereich nicht aufsteigend")
        # Zitat-Fragmente gegen den Ton im Bereich pruefen
        span = norm(" ".join(w["text"] for w in words(stem)
                             if w["start"] >= a - 1.2 and w["end"] <= b + 1.2))
        for frag in re.findall(r"„([^“”]+)[“”]", quote_cell):
            for part in re.split(r"\s*\[…\]\s*|\s*…\s*", frag):
                part = norm(part)
                if len(part) < 12:
                    continue
                if part not in span:
                    problems.append(
                        f"{md.name} [{short} {von}-{bis}]: Zitat nicht im Bereich: "
                        f"...{part[:70]}...")

print(f"{checked} Quellen-Zeilen geprueft")
if problems:
    print(f"\n{len(problems)} PROBLEME:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("Alle Zitate und Timecodes belegt.")
