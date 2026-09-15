"""Wörter mit Zeitstempel und Sprecher in einem Fenster. Aufruf: woerter.py <clip> <mm:ss> <mm:ss>"""
import json, sys
from pathlib import Path
I = Path(__file__).resolve().parent
def secs(tc):
    m, s = tc.split(":"); return int(m) * 60 + float(s.replace(",", "."))
clip, a, b = sys.argv[1], secs(sys.argv[2]), secs(sys.argv[3])
rec = next(r for r in json.loads((I / "transcripts_index.json").read_text()) if r["name"].startswith(clip))
ws = [w for w in json.loads((I / "cache" / f"{rec['fingerprint']}.scribe.json").read_text())["words"] if w["text"].strip()]
line = []
for w in ws:
    if w["end"] >= a and w["start"] <= b:
        m, s = divmod(w["start"], 60); m2, s2 = divmod(w["end"], 60)
        line.append(f"{w['text']}[{int(m):02d}:{s:04.1f}-{s2:04.1f}|{(w.get('speaker') or '?')[-1]}]")
print(f"{clip} {sys.argv[2]}–{sys.argv[3]}: " + " ".join(line))
