"""Exakte In/Out-Timecodes fuer ein Zitat aus den Wort-Zeitstempeln holen.

Aufruf:  python3 _intern/zitat_timecode.py FX3_0305 "ich bin Holztaxi oder Baumschubser"
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "cache"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9äöüß]+", " ", s.lower()).strip()


def tc(x: float) -> str:
    return f"{int(x) // 60:02d}:{int(x) % 60:02d}"


def main() -> None:
    clip, quote = sys.argv[1], sys.argv[2]
    treffer = []
    for f in glob.glob(str(CACHE / "*.scribe.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        if clip not in Path(d.get("source_file", "")).name:
            continue
        words, toks = [], []
        for w in d["words"]:
            for teil in norm(w["text"]).split():
                words.append(w)
                toks.append(teil)
        ziel = norm(quote).split()
        n = len(ziel)
        for i in range(len(toks) - n + 1):
            if toks[i:i + n] == ziel:
                treffer.append((Path(d["source_file"]).name, words[i]["start"], words[i + n - 1]["end"]))
    if not treffer:
        print("KEIN TREFFER — Wortlaut pruefen")
        return
    for name, a, b in treffer:
        print(f"{name}  {tc(a)}–{tc(b)}   ({a:.2f}–{b:.2f} s)")


if __name__ == "__main__":
    main()
