"""Vorlage (Stand 15.09.2026): Wortgenaue In/Out-Punkte für eine Phrase aus dem Scribe-Cache.

Aufruf:  tools/autocut/venv/bin/python _intern/find_tc.py <clip-stem> "<phrase-anfang>" ["<phrase-ende>"] [--nach mm:ss]
Liest    _intern/transcripts_index.json (name, fingerprint) + _intern/cache/<fingerprint>.scribe.json.
Ausgabe: Timecode (mm:ss,d), Sprecher im Fenster, Kontext 3 s davor/danach
         (damit Regie-Stimmen direkt am In/Out auffallen).
Phrasen werden normalisiert verglichen (klein, nur a–z, äöüß, Ziffern); --nach sucht erst ab dieser Quellzeit.
Module:  load, secs (und fmt, locate) werden von _intern/plan_rows.py und weiteren Chargen-Skripten per Import genutzt.

Herkunft: Taxodia-Charge, _intern/find_tc.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

INTERN = Path(__file__).resolve().parent

# ── ANPASSEN je Charge ─────────────────────────────
# (keine chargen-spezifischen Werte)
# ── Ende ANPASSEN ──────────────────────────────────


def norm(s: str) -> list[str]:
    return re.sub(r"[^a-zäöüß0-9 ]", " ", s.lower()).split()


def fmt(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}".replace(".", ",")


def secs(tc: str) -> float:
    m, s = tc.split(":")
    return int(m) * 60 + float(s.replace(",", "."))


def load(stem: str) -> list[dict]:
    idx = json.loads((INTERN / "transcripts_index.json").read_text())
    rec = next(r for r in idx if r["name"].rsplit(".", 1)[0] == stem)
    data = json.loads((INTERN / "cache" / f"{rec['fingerprint']}.scribe.json").read_text())
    return [w for w in data["words"] if w["text"].strip()]


def locate(words, phrase, after_idx=-1, after_s=0.0):
    target = norm(phrase)
    flat = [(i, t) for i, w in enumerate(words) for t in norm(w["text"])]
    for k in range(len(flat) - len(target) + 1):
        i0 = flat[k][0]
        if i0 <= after_idx or words[i0]["start"] < after_s:
            continue
        if [t for _, t in flat[k:k + len(target)]] == target:
            return i0, flat[k + len(target) - 1][0]
    return None, None


def main() -> None:
    args = sys.argv[1:]
    after_s = 0.0
    if "--nach" in args:
        j = args.index("--nach")
        after_s = secs(args[j + 1])
        args = args[:j] + args[j + 2:]
    stem, start_phrase = args[0], args[1]
    end_phrase = args[2] if len(args) > 2 else None
    words = load(stem)
    a, b = locate(words, start_phrase, after_s=after_s)
    if a is None:
        sys.exit(f"NICHT GEFUNDEN in {stem}: {start_phrase!r}")
    if end_phrase:
        _, b = locate(words, end_phrase, after_idx=a - 1, after_s=words[a]["start"])
        if b is None:
            sys.exit(f"ENDE NICHT GEFUNDEN in {stem}: {end_phrase!r}")
    t0, t1 = words[a]["start"], words[b]["end"]
    sprecher = sorted({w.get("speaker") for w in words[a:b + 1]})
    print(f"{stem}  {fmt(t0)}–{fmt(t1)}  ({t0:.2f}–{t1:.2f} s, {t1 - t0:.1f} s)  Sprecher {sprecher}")
    print("  TEXT: " + " ".join(w["text"] for w in words[a:b + 1]))
    vor = [w for w in words[:a] if w["end"] >= t0 - 3]
    nach = [w for w in words[b + 1:] if w["start"] <= t1 + 3]
    if vor:
        print("  DAVOR: " + " ".join(f"{w['text']}[{(w.get('speaker') or '?')[-1]}]" for w in vor)
              + f"  (letztes Wortende {fmt(vor[-1]['end'])})")
    if nach:
        print("  DANACH: " + " ".join(f"{w['text']}[{(w.get('speaker') or '?')[-1]}]" for w in nach)
              + f"  (nächster Wortbeginn {fmt(nach[0]['start'])})")


if __name__ == "__main__":
    main()
