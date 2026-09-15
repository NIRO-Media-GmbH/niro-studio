"""Wortgenaue Timecodes fuer eine Phrase in einem Clip finden.
Aufruf: find_tc.py <clip-stem> "<phrase-anfang>" ["<phrase-ende>"]
"""
import json, re, sys
from pathlib import Path

INTERN = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
              "Einfamilienhaus-und-Smartino/2026-07 Dreh/_intern")

def norm(s):
    return re.sub(r"[^a-zäöüß0-9 ]", "", s.lower()).split()

def fmt(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"

def load(stem):
    idx = json.loads((INTERN / "transcripts_index.json").read_text())
    rec = next(r for r in idx if r["name"].rsplit(".", 1)[0] == stem)
    cached = json.loads((INTERN / "cache" / f"{rec['fingerprint']}.scribe.json").read_text())
    return [w for w in cached["words"] if w["text"].strip()]

def locate(words, phrase, after=-1):
    target = norm(phrase)
    toks = [(i, norm(w["text"])) for i, w in enumerate(words)]
    flat = [(i, t) for i, ts in toks for t in ts]
    for k in range(len(flat) - len(target) + 1):
        if flat[k][0] > after and [t for _, t in flat[k:k + len(target)]] == target:
            return flat[k][0], flat[k + len(target) - 1][0]
    return None, None

stem, start_phrase = sys.argv[1], sys.argv[2]
end_phrase = sys.argv[3] if len(sys.argv) > 3 else None
words = load(stem)
a, _ = locate(words, start_phrase)
if a is None:
    sys.exit(f"NICHT GEFUNDEN in {stem}: {start_phrase!r}")
if end_phrase:
    _, b = locate(words, end_phrase, after=a)
    if b is None:
        sys.exit(f"ENDE NICHT GEFUNDEN in {stem}: {end_phrase!r}")
else:
    b = a
print(f"{stem}  {fmt(words[a]['start'])}-{fmt(words[b]['end'])}   "
      f"({words[a]['start']:.1f}s - {words[b]['end']:.1f}s)")
print("  " + " ".join(w["text"] for w in words[a:b + 1])[:300])
