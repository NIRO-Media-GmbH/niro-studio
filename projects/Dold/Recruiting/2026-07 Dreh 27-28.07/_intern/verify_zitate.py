"""Batch-Verifikation: alle Zitate der video-*.md wortgenau gegen den Scribe-Cache.

Prueft pro Zitat: (a) Wortlaut existiert exakt im angegebenen Clip,
(b) Fundstelle liegt im angegebenen Zeitfenster (+/- 8 s Toleranz),
(c) [..]-Segmente stehen in der richtigen Reihenfolge.

Aufruf:  python3 _intern/verify_zitate.py
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / "_intern" / "cache"
PLAENE = BASE / "Ergebnisse" / "O-Ton-Pläne"
TOL = 8.0  # Sekunden Toleranz um das angegebene Fenster

ELLIPSIS = re.compile(r"\[…\]|\[\.\.\.\]|…")
CLIP = re.compile(r"(FX3_\d+|a7MK4_\d+_\d+)")
SPAN = re.compile(r"(\d{1,2}):(\d{2})[–-](\d{1,2}):(\d{2})")


FILLER = {"äh", "ähm", "hm", "mhm", "hmm"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9äöüß]+", " ", s.lower()).strip()


def toks_of(s: str) -> list[str]:
    return [t for t in norm(s).split() if t not in FILLER]


def load_cache() -> dict[str, list[dict]]:
    by_clip: dict[str, list[dict]] = {}
    for f in glob.glob(str(CACHE / "*.scribe.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        name = Path(d.get("source_file", "")).name
        m = CLIP.search(name)
        if m:
            by_clip.setdefault(m.group(1), []).append(d)
    return by_clip


def tokens(d: dict) -> tuple[list[str], list[dict]]:
    toks, words = [], []
    for w in d["words"]:
        for teil in norm(w["text"]).split():
            if teil in FILLER:
                continue
            toks.append(teil)
            words.append(w)
    return toks, words


def find_seq(toks: list[str], words: list[dict], ziel: list[str], start_at: int = 0):
    n = len(ziel)
    for i in range(start_at, len(toks) - n + 1):
        if toks[i : i + n] == ziel:
            return i, words[i]["start"], words[i + n - 1]["end"]
    return None


def check(quote: str, clip: str, von_s: float | None, bis_s: float | None,
          by_clip: dict) -> list[str]:
    errs = []
    if clip not in by_clip:
        return [f"Clip {clip} nicht im Cache"]
    segs = [toks_of(s) for s in ELLIPSIS.split(quote)]
    segs = [s for s in segs if s]
    best = None
    for d in by_clip[clip]:
        toks, words = tokens(d)
        pos, ok, t0, t1 = 0, True, None, None
        for seg in segs:
            hit = find_seq(toks, words, seg, pos)
            if not hit:
                ok = False
                break
            i, a, b = hit
            t0 = a if t0 is None else t0
            t1 = b
            pos = i + len(seg)
        if ok:
            best = (t0, t1)
            break
    if not best:
        # Diagnose: welches Segment fehlt?
        for k, seg in enumerate(segs):
            found = any(find_seq(*tokens(d), seg) for d in by_clip[clip])
            if not found:
                frag = " ".join(seg[:8])
                errs.append(f"Segment {k+1} NICHT gefunden: \"{frag}…\"")
        if not errs:
            errs.append("Segmente einzeln ok, aber nicht in dieser Reihenfolge")
        return errs
    t0, t1 = best
    if von_s is not None and (t0 < von_s - TOL or (bis_s and t1 > bis_s + TOL)):
        errs.append(f"Zeitfenster: gefunden {t0:.0f}-{t1:.0f}s, angegeben {von_s:.0f}-{bis_s:.0f}s")
    return errs


def main() -> None:
    by_clip = load_cache()
    total, bad = 0, 0
    for md in sorted(PLAENE.glob("video-*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            if "„" not in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.strip().startswith("|") and len(cells) >= 8:
                # Tabellenzeile: Zitat NUR aus O-Ton-Spalte, Clip/Zeit aus Quell-Spalte
                pairs = [(cells[2], cells[3])]
            else:
                # Bullet/Fliesstext: ganze Zeile, ggf. mehrere Clip-Kandidaten
                pairs = [(line, line)]
            for qcell, scell in pairs:
                quotes = re.findall(r"„(.+?)[\"“”]", qcell)
                clips = CLIP.findall(scell) or CLIP.findall(line)
                if not quotes or not clips:
                    continue
                spans = SPAN.findall(scell) or SPAN.findall(line)
                von_s = bis_s = None
                if len(spans) == 1:  # nur bei eindeutigem Fenster pruefen
                    von_s = int(spans[0][0]) * 60 + int(spans[0][1])
                    bis_s = int(spans[0][2]) * 60 + int(spans[0][3])
                for q in quotes:
                    if len(norm(q).split()) < 4:  # Kurz-Strings nicht pruefen
                        continue
                    if sum(c.isupper() for c in q if c.isalpha()) > 0.6 * max(
                        1, sum(c.isalpha() for c in q)
                    ):
                        continue  # Karten/Captions in Grossbuchstaben
                    total += 1
                    errlists = [check(q, c, von_s, bis_s, by_clip) for c in clips]
                    if all(errlists):  # in keinem Kandidaten-Clip sauber gefunden
                        bad += 1
                        print(f"\n[{md.name}] {'/'.join(clips)}  „{q[:60]}…“")
                        for e in errlists[0]:
                            print(f"   -> {e}")
    print(f"\n{total} Zitate geprueft, {bad} Fehler.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
