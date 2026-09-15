"""Zitat- und Timecode-Verifikation der Kompakt-Pläne — wortgenau gegen FX3.

Ton-Kamera = FX3 (David 2026-08-07). Prüft pro video-*.md jede O-Ton-Zelle:
- alle Fragmente (getrennt durch […]) existieren im FX3-Wortstrom der Person
  (Normalisierung identisch zu remap_to_fx3.py: Filler, Förch-Varianten,
  Ziffern↔Zahlwörter, Bindestrich-Split);
- der erste Timecode der Quelle-Zelle liegt ±4 s an der wortgenauen Fundstelle.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CH = Path("/Users/jansantos/NIRO Studio/projects/Förch/Vertrieb Kaufbeuren/2026-07 Kaufbeuren Dreh")
sys.path.insert(0, str(CH / "_intern"))
from remap_to_fx3 import FX3_FILE, WordIndex, norm_tokens  # noqa: E402


def mmss_to_s(t: str) -> int:
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def check_file(path: Path, indexes: dict) -> list[str]:
    errors = []
    for ln, line in enumerate(path.read_text().splitlines(), 1):
        if not line.startswith("|") or line.startswith("|---") or "O-Ton wörtlich" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or not cells[2].startswith("„") or "kein O-Ton" in cells[2]:
            continue
        quelle = cells[3]
        m = re.search(r"(Adriano|Franzi|Friedrich|Thomas)", quelle)
        if not m:
            errors.append(f"{path.name}:{ln} keine Person erkennbar")
            continue
        person = m.group(1).lower()
        idx = indexes[person]
        if "a7MK4" in quelle:
            errors.append(f"{path.name}:{ln} [{person}] Quelle referenziert noch a7MK4!")
        q = cells[2].strip("„”\"").replace("[…]", "\x00")
        q = re.sub(r"\[[^\]]*\]", " ", q)
        frags = [f for f in q.split("\x00") if len(norm_tokens(f)) >= 3]
        hits = [idx.find(f) for f in frags]
        for f, h in zip(frags, hits):
            if h is None:
                errors.append(f"{path.name}:{ln} [{person}] Fragment fehlt in FX3: „{f.strip()[:60]}…\"")
        if frags and all(h is not None for h in hits):
            tm = re.search(r"(\d\d:\d\d)[–-](\d\d:\d\d)", quelle)
            if tm:
                stated = mmss_to_s(tm.group(1))
                computed = hits[0][0]
                if abs(stated - computed) > 4:
                    errors.append(
                        f"{path.name}:{ln} [{person}] Timecode {tm.group(1)} passt nicht "
                        f"zur Fundstelle ({int(computed)//60:02d}:{int(computed)%60:02d})")
    return errors


def main() -> None:
    indexes = {p: WordIndex(p) for p in FX3_FILE}
    total = 0
    for f in sorted((CH / "Ergebnisse" / "O-Ton-Pläne").glob("video-*.md")):
        errs = check_file(f, indexes)
        total += len(errs)
        print(("OK          " if not errs else f"{len(errs)} PROBLEME  ") + f.name)
        for e in errs:
            print("   ", e)
    print(f"\nGesamt: {total} Probleme")


if __name__ == "__main__":
    main()
