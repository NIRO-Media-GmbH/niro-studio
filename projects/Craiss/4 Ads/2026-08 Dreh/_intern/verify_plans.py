"""Alle Zitate + Timecodes der Craiss-Video-Plaene gegen die Wortdaten pruefen.

Prueft je Ablauf-Zeile:
  a) Clip existiert im Index
  b) Timecode-Bereich ist aufsteigend und liegt im Clip
  c) jedes Zitat-Fragment kommt im Ton dieses Bereichs vor (Toleranz 1,5 s)
  d) Sprecher-Reinheit: im Bereich spricht nur EIN Sprecher (sonst Warnung,
     weil Regie-/Fremdstimme mit im Schnittfenster liegt)

„Craiss" wird beim Vergleich auf die ASR-Verhoerer normalisiert
(Kreis/Greis/Kraiss/Preis/Greif), weil die Plaene korrekt „Craiss" schreiben.
"""
import json
import re
import sys
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh")
INTERN, PLANS = CH / "_intern", CH / "Ergebnisse/O-Ton-Pläne"

idx = {r["name"].rsplit(".", 1)[0]: r for r in
       json.loads((INTERN / "transcripts_index.json").read_text())}
cache: dict[str, list] = {}


def words(stem):
    if stem not in cache:
        fp = idx[stem]["fingerprint"]
        data = json.loads((INTERN / "cache" / f"{fp}.scribe.json").read_text())
        cache[stem] = [w for w in data["words"] if w["text"].strip()]
    return cache[stem]


VERHOERER = re.compile(r"\b(kreis|greis|kraiss|kraiß|preis|greif)\b")


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‚", "'")
    s = re.sub(r"[^a-zäöüß0-9]+", " ", s.lower()).strip()
    return VERHOERER.sub("craiss", s)


def secs(tc: str) -> float:
    m, s = tc.split(":")
    return int(m) * 60 + float(s.replace(",", "."))


# Quelle:  ... · <Ordner>/FX3_0781 · 00:15–00:20   (Ordner optional)
SRC = re.compile(r"·\s*(?:[^·|]*?/)?((?:FX3|a7MK4)[_0-9]*\d)\s*·\s*"
                 r"(?:≈)?(\d+:\d\d(?:,\d)?)\s*[–-]\s*(?:≈)?(\d+:\d\d(?:,\d)?)")

problems, warnings, checked = [], [], 0

for md in sorted(PLANS.glob("video-*.md")):
    for line in md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        quote_cell, src_cell = cells[2], cells[3]
        m = SRC.search(src_cell)
        if not m:
            if quote_cell and quote_cell != "—" and "„" in quote_cell:
                problems.append(f"{md.name}: Zitat ohne erkennbare Quelle -> {quote_cell[:60]}")
            continue
        stem, von, bis = m.groups()
        if stem not in idx:
            problems.append(f"{md.name}: Clip unbekannt {stem}")
            continue
        checked += 1
        a, b = secs(von), secs(bis)
        dur = idx[stem]["duration_s"]
        if b > dur + 1:
            problems.append(f"{md.name} [{stem} {von}-{bis}]: Ende nach Clipende ({dur}s)")
        if a >= b:
            problems.append(f"{md.name} [{stem} {von}-{bis}]: Bereich nicht aufsteigend")

        ws = words(stem)
        span_words = [w for w in ws if w["start"] >= a - 1.5 and w["end"] <= b + 1.5]
        span = norm(" ".join(w["text"] for w in span_words))

        # Fremdsprachige Grüße gibt die ASR nicht aus — im Plan als
        # „(nicht im Transkript)" markiert, hier bewusst nur Timecode prüfen.
        if "nicht im Transkript" in quote_cell:
            continue

        for frag in re.findall(r"„([^“”]+)[“”]", quote_cell):
            for part in re.split(r"\s*\[…\]\s*|\s*…\s*", frag):
                part = norm(part)
                if len(part) < 8:
                    continue
                if part not in span:
                    problems.append(
                        f"{md.name} [{stem} {von}-{bis}]: Zitat nicht im Bereich\n"
                        f"     erwartet: {part[:90]}\n"
                        f"     gefunden: {span[:90]}")

        sprecher = {w.get("speaker") for w in span_words if w.get("speaker")}
        if len(sprecher) > 1:
            warnings.append(f"{md.name} [{stem} {von}-{bis}]: "
                            f"{len(sprecher)} Sprecher im Fenster {sorted(sprecher)} "
                            f"— In/Out frame-genau setzen")

print(f"{checked} Quellenangaben geprüft.")
if warnings:
    print(f"\n{len(warnings)} HINWEIS(E) Sprecher-Reinheit:")
    for w in warnings:
        print("  ~", w)
if problems:
    print(f"\n{len(problems)} PROBLEM(E):")
    for p in problems:
        print("  !", p)
    sys.exit(1)
print("\nAlle Zitate wortgenau im angegebenen Timecode-Bereich belegt.")
