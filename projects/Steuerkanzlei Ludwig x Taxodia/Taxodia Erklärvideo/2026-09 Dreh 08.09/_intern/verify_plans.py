"""Alle Zitate + Timecodes der Taxodia-Pläne gegen die Scribe-Wortdaten prüfen.

Aufruf: verify_plans.py [Ordner mit video-*.md]   (Default: Ergebnisse/O-Ton-Pläne)

Prüft je Tabellenzeile mit Quelle `… · <Ordner>/<Datei> · mm:ss,d–mm:ss,d`:
  a) Clip existiert im Index, ist FX3 (= Ton-Kamera laut User 14.09.)
  b) Timecode-Bereich aufsteigend und innerhalb der Clipdauer
  c) jedes „Zitat-Fragment" (an […] getrennt) steht im Ton dieses Bereichs
     (Wörter, die das Fenster ±1,5 s berühren — Scribe dehnt Wortgrenzen)
  d) Sprecher-Reinheit: im Fenster nur EIN Diarisations-Sprecher, sonst Hinweis
  e) Schutz gegen Leerlauf: Zeile mit Clip-Quelle, aber ohne erkanntes Zitat = Problem
Mehrere Bereiche in einer Quelle („01:52,9–01:58,5 + 02:05,7–02:09,7") werden
zusammen als ein Fenster-Set geprüft.

Abweichung zur Rappold-Vorlage: Zitate enden in den Markdowns mit ASCII-" —
der alte Regex erwartete nur “/” und erkannte deshalb kein einziges Zitat.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
INTERN = CH / "_intern"
PLANS = Path(sys.argv[1]) if len(sys.argv) > 1 else CH / "Ergebnisse" / "O-Ton-Pläne"
TOL = 1.5

idx = {r["name"].rsplit(".", 1)[0]: r for r in
       json.loads((INTERN / "transcripts_index.json").read_text())}
_cache: dict[str, list] = {}


def words(stem: str) -> list[dict]:
    if stem not in _cache:
        data = json.loads((INTERN / "cache" / f"{idx[stem]['fingerprint']}.scribe.json").read_text())
        _cache[stem] = [w for w in data["words"] if w["text"].strip()]
    return _cache[stem]


# ASR-Verhörer -> Schreibweise im Plan
ALIAS = [
    (r"\bheyn\b", "hein"), (r"\btaxudo\b", "taxodia"), (r"\bfachagrawert\b", "fachagrarwirt"),
    (r"\bflamand\b", "flammann"), (r"\blüttig\b", "ludwig"), (r"\blückig\b", "ludwig"),
]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).replace("’", "'").replace("‚", "'")
    s = re.sub(r"[^a-zäöüß0-9]+", " ", s.lower()).strip()
    for pat, rep in ALIAS:
        s = re.sub(pat, rep, s)
    return re.sub(r"\s+", " ", s)


def secs(tc: str) -> float:
    m, s = tc.split(":")
    return int(m) * 60 + float(s.replace(",", "."))


CLIP = re.compile(r"((?:FX3|a7MK4)_[0-9_]*\d)")
RANGE = re.compile(r"(\d+:\d\d(?:,\d)?)\s*[–-]\s*(\d+:\d\d(?:,\d)?)")
QUOTE = re.compile(r"„([^“”\"]+)[\"“”]")

problems, warnings, checked, fragments = [], [], 0, 0

for md in sorted([*PLANS.glob("video-*.md"), *PLANS.glob("99-anhang-*.md")]):
    for line in md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0] in ("#", "---") or set(cells[0]) <= {"-", ":"}:
            continue
        quote_cell, src_cell = cells[2], cells[3]
        m = CLIP.search(src_cell)
        zitate = QUOTE.findall(quote_cell)
        if not m:
            if zitate:
                problems.append(f"{md.name} #{cells[0]}: Zitat ohne Clip-Quelle -> {quote_cell[:60]}")
            continue
        if not zitate:
            problems.append(f"{md.name} #{cells[0]}: Clip-Quelle, aber kein Zitat erkannt -> {quote_cell[:60]}")
            continue
        stem = m.group(1)
        if stem not in idx:
            problems.append(f"{md.name} #{cells[0]}: Clip unbekannt {stem}")
            continue
        ranges = [(secs(a), secs(b)) for a, b in RANGE.findall(src_cell[m.end():])]
        if not ranges:
            problems.append(f"{md.name} #{cells[0]}: kein Timecode bei {stem}")
            continue
        checked += 1
        if idx[stem]["kamera"] != "FX3":
            problems.append(f"{md.name} #{cells[0]}: {stem} ist NICHT die Ton-Kamera (FX3)")
        dur = idx[stem]["duration_s"]
        ws = words(stem)
        span_words = []
        for a, b in ranges:
            if a >= b:
                problems.append(f"{md.name} #{cells[0]} [{stem}]: Bereich nicht aufsteigend")
            if b > dur + 1:
                problems.append(f"{md.name} #{cells[0]} [{stem}]: Ende {b:.1f}s nach Clipende ({dur}s)")
            span_words += [w for w in ws if w["end"] >= a - TOL and w["start"] <= b + TOL]
        span = norm(" ".join(w["text"] for w in span_words))
        for frag in zitate:
            for part in re.split(r"\s*\[…\]\s*|\s*\[\.\.\.\]\s*", frag):
                p = norm(part)
                if len(p) < 6:
                    continue
                fragments += 1
                if p not in span:
                    problems.append(
                        f"{md.name} #{cells[0]} [{stem} {src_cell[m.end():].strip()[:40]}]: Zitat nicht im Bereich\n"
                        f"     erwartet: {p[:100]}\n"
                        f"     gefunden: {span[:160]}")
        inner = [w for w in ws for a, b in ranges if w["start"] >= a - 0.05 and w["end"] <= b + 0.05]
        sprecher = {w.get("speaker") for w in inner if w.get("speaker")}
        if len(sprecher) > 1:
            warnings.append(f"{md.name} #{cells[0]} [{stem}]: {len(sprecher)} Sprecher im Fenster "
                            f"{sorted(sprecher)} — Regie-Stimme? frame-genau schneiden")

print(f"{checked} Quellenangaben, {fragments} Zitat-Fragmente geprüft in {PLANS}.")
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
