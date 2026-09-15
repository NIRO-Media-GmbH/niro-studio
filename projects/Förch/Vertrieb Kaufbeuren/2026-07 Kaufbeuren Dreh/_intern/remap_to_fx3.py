"""Timecode-Remap a7MK4 → FX3 (Ton-Kamera) in den Kompakt-Plänen — WORT-genau.

Lädt Wort-Zeitstempel direkt aus dem Scribe-Cache (FX3-Dateien), lokalisiert
jede Zitat-Passage und schreibt die Quelle-Zelle um:
  <Person>/a7MK4_99xx · <alt>  →  <Person>/FX3_00xx · MM:SS–MM:SS
Nicht auffindbare Fragmente: FX3-Kontext um den besten Anker wird ausgegeben
(FX3-ASR hört anders → Zitat ggf. an FX3-Wortlaut anpassen).

Aufruf: venv/bin/python remap_to_fx3.py [--write]
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/Förch/Vertrieb Kaufbeuren/2026-07 Kaufbeuren Dreh")

FX3_FILE = {"adriano": "FX3_0078.MP4", "franzi": "FX3_0079.MP4",
            "friedrich": "FX3_0080.MP4", "thomas": "FX3_0081.MP4"}
FX3_NAME = {k: v[:-4] for k, v in FX3_FILE.items()}

VARIANTS = [
    ("foerch", "förch"), ("fuerich", "förch"), ("fürich", "förch"),
    ("fürch", "förch"), ("ferch", "förch"), ("körsch", "förch"),
    ("försch", "förch"), ("frörch", "förch"), ("schörgh", "förch"),
    ("menningen", "memmingen"), ("deuenstadt", "neuenstadt"),
    ("sechszehn", "sechzehn"),
]
FILLER = {"äh", "ähm", "mmm", "mmh", "hm", "mhm", "uuund", "uund"}
DIGITS = {"7": "sieben", "8": "acht", "16": "sechzehn", "17": "siebzehn",
          "23": "dreiundzwanzig", "70": "siebzig", "80": "achtzig",
          "200": "zweihundert", "33": "dreiunddreißig"}


def norm_word(w: str) -> str:
    s = unicodedata.normalize("NFC", w).lower().replace("'", "'")
    s = re.sub(r"[^a-z0-9äöüß]+", "", s)
    if s in DIGITS:
        s = DIGITS[s]
    for a, b in VARIANTS:
        s = s.replace(a, b)
    return s


def norm_tokens(s: str) -> list[str]:
    s = s.replace("--", " ").replace("-", " ").replace("–", " ")
    toks = [norm_word(w) for w in re.split(r"\s+", s)]
    return [t for t in toks if t and t not in FILLER]


class WordIndex:
    def __init__(self, person: str):
        src = FX3_FILE[person]
        words = None
        for f in (CH / "_intern" / "cache").glob("*.scribe.json"):
            d = json.loads(f.read_text())
            if Path(d.get("source_file", "")).name == src:
                words = d["words"]
                break
        if words is None:
            raise SystemExit(f"Cache für {src} nicht gefunden")
        # Cache-Wörter in normalisierte Subtokens expandieren (Bindestriche!),
        # jedes Subtoken behält start/end des Ursprungsworts.
        self.words = []
        self.tokens = []
        for w in words:
            for sub in norm_tokens(w["text"]):
                self.words.append(w)
                self.tokens.append(sub)
        self.joined = "\x01" + "\x01".join(self.tokens) + "\x01"

    def find(self, fragment: str):
        toks = norm_tokens(fragment)
        if len(toks) < 3:
            return None
        needle = "\x01" + "\x01".join(toks) + "\x01"
        pos = self.joined.find(needle)
        if pos < 0:
            return None
        start_i = self.joined[:pos + 1].count("\x01") - 1
        end_i = start_i + len(toks) - 1
        return self.words[start_i]["start"], self.words[end_i]["end"]

    def anchor_context(self, fragment: str, win: int = 30) -> str:
        """Längsten matchenden Token-Lauf finden und FX3-Wörter drumherum zeigen."""
        toks = norm_tokens(fragment)
        best = None
        for size in range(min(8, len(toks)), 2, -1):
            for off in range(0, len(toks) - size + 1):
                needle = "\x01" + "\x01".join(toks[off:off + size]) + "\x01"
                pos = self.joined.find(needle)
                if pos >= 0:
                    best = (self.joined[:pos + 1].count("\x01") - 1, size)
                    break
            if best:
                break
        if not best:
            return "  (kein Anker gefunden)"
        i, size = best
        lo, hi = max(0, i - win), min(len(self.words), i + size + win)
        t0 = self.words[lo]["start"]
        txt = " ".join(w["text"] for w in self.words[lo:hi])
        return f"  FX3 ab {fmt_s(t0)}: …{txt}…"


def fmt_s(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def remap_file(path: Path, write: bool, indexes: dict):
    lines = path.read_text().splitlines()
    report = []
    for ln, line in enumerate(lines):
        if not line.startswith("|") or "O-Ton wörtlich" in line or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or not cells[2].startswith("„"):
            continue
        quelle = cells[3]
        m = re.search(r"(Adriano|Franzi|Friedrich|Thomas)", quelle)
        mfile = re.search(r"(a7MK4_\d{4}|FX3_\d{4})", quelle)
        if not m or not mfile:
            continue
        person = m.group(1).lower()
        idx = indexes[person]
        q = cells[2].strip("„”\"").replace("[…]", "\x00")
        q = re.sub(r"\[[^\]]*\]", " ", q)
        frags = [f for f in q.split("\x00") if len(norm_tokens(f)) >= 3]
        hits = [idx.find(f) for f in frags]
        if not frags or any(h is None for h in hits):
            report.append(f"  !! Zeile {ln+1} [{person}]:")
            for f, h in zip(frags, hits):
                if h is None:
                    report.append(f"     fehlt: „{f.strip()[:60]}…\"")
                    report.append(idx.anchor_context(f))
            continue
        new_range = f"{fmt_s(hits[0][0])}–{fmt_s(hits[-1][1])}"
        new_quelle = quelle.replace(mfile.group(0), FX3_NAME[person])
        new_quelle = re.sub(r"\d\d:\d\d[–-]\d\d:\d\d(\s*\+\s*\d\d:\d\d[–-]\d\d:\d\d)*",
                            new_range, new_quelle, count=1)
        new_quelle = re.sub(r"\s*\+\s*\d\d:\d\d[–-]\d\d:\d\d", "", new_quelle)
        if new_quelle != quelle:
            cells[3] = new_quelle
            lines[ln] = "| " + " | ".join(cells) + " |"
            report.append(f"  OK Zeile {ln+1}: → {FX3_NAME[person]} · {new_range}")
    if write:
        path.write_text("\n".join(lines) + "\n")
    return report


def main():
    write = "--write" in sys.argv
    indexes = {p: WordIndex(p) for p in FX3_FILE}
    for f in sorted((CH / "Ergebnisse" / "O-Ton-Pläne").glob("video-*.md")):
        print(f.name)
        for r in remap_file(f, write, indexes):
            print(r)
    SCATTERED = [
        ("friedrich", "ungedeckelte Möglichkeiten"),
        ("friedrich", "Sonderausschüttungen"),
        ("friedrich", "Opel Astra"),
        ("friedrich", "kriegt jeder Neuverkäufer"),
        ("franzi", "aufm Lohnzettel"),
        ("franzi", "lohnt sich das finanziell"),
        ("franzi", "rund um die Uhr"),
        ("thomas", "Wir haben ein Fixgehalt"),
        ("adriano", "lohnt sich definitiv"),
        ("adriano", "kalte Wasser geschmissen"),
        ("adriano", "achtzehn Uhr telefonisch"),
        ("thomas", "Killerfliege"),
        ("friedrich", "InnoCenter"),
        ("thomas", "vier, fünf Kunden um mich"),
        ("thomas", "nur einer da sein"),
        ("thomas", "gelernter Textilkaufmann"),
        ("thomas", "ich hätte auch schon auf den Außendienst"),
        ("friedrich", "bisschen kleiner als alle anderen"),
        ("friedrich", "nicht so bekannt wie viele"),
        ("franzi", "Stati online stellen"),
        ("franzi", "um sieben, um acht noch mal raus"),
        ("adriano", "Und los"),
    ]
    print("\nVerstreute Referenzen (FX3, wortgenau):")
    for person, probe in SCATTERED:
        hit = indexes[person].find(probe)
        if hit:
            print(f"  {person:10} „{probe[:40]}\" → FX3 {fmt_s(hit[0])}–{fmt_s(hit[1])}")
        else:
            print(f"  {person:10} „{probe[:40]}\" → nicht im FX3-Transkript")
            print(indexes[person].anchor_context(probe, win=12))


if __name__ == "__main__":
    main()
