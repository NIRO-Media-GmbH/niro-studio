"""Zitat-/Timecode-Verifikation der Schnittplaene gegen utterances.json.

Prueft pro `…FX3_xxxx.MP4 · MM:SS–MM:SS`-Referenz mit Zitat in derselben
Tabellenzeile bzw. Bullet:
  a) Clip existiert, Range liegt in der Clipdauer
  b) jedes Zitat-Segment (Split an […] / je Teilsatz) findet sich normalisiert
     im Utterance-Text des Clips
  c) das gefundene Segment liegt (mit Toleranz) im zitierten Zeitfenster
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

CHARGE = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
utt = json.loads((CHARGE / "_intern/utterances.json").read_text(encoding="utf-8"))
clips = {r["name"]: r for r in utt}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.lower()
    s = re.sub(r"[„“”\"'’‚`«»]", "", s)
    s = re.sub(r"[^a-zäöüß0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def mmss(t: str) -> float:
    m, s = t.split(":")
    return int(m) * 60 + int(s)

# Wortliste pro Clip mit Zeitfenstern (aus Utterances rekonstruiert)
clip_words: dict[str, list[tuple[str, float, float]]] = {}
for r in utt:
    words = []
    for u in r["utterances"]:
        toks = norm(u["text"]).split()
        if not toks:
            continue
        span = u["bis_s"] - u["von_s"]
        for i, w in enumerate(toks):
            t0 = u["von_s"] + span * i / max(len(toks), 1)
            t1 = u["von_s"] + span * (i + 1) / max(len(toks), 1)
            words.append((w, t0, t1))
    clip_words[r["name"]] = words

def find_segment(clip: str, seg: str):
    """Suche normalisierte Wortfolge; gib (start_s, end_s) des besten Fundes."""
    toks = norm(seg).split()
    if len(toks) < 3:
        return None, "zu kurz fuer Pruefung"
    words = clip_words[clip]
    wtoks = [w for w, _, _ in words]
    n, m = len(wtoks), len(toks)
    hits = []
    for i in range(n - m + 1):
        window = wtoks[i:i + m]
        same = sum(1 for a, b in zip(window, toks) if a == b)
        if same / m >= 0.85:
            hits.append((same / m, words[i][1], words[i + m - 1][2]))
    if not hits:
        return None, "NICHT GEFUNDEN"
    hits.sort(reverse=True)
    return (hits[0][1], hits[0][2]), f"match {hits[0][0]:.0%}"

REF = re.compile(r"(FX3_\d{4})\.MP4 · (\d{2}:\d{2})–(\d{2}:\d{2})")

report = []
plan_dir = CHARGE / "Ergebnisse/O-Ton-Pläne"
for f in sorted(plan_dir.glob("video-*.md")):
    for line in f.read_text(encoding="utf-8").splitlines():
        refs = REF.findall(line)
        if not refs:
            continue
        quotes = re.findall(r"„([^“]+)“", line)
        for name, t0, t1 in refs:
            clip = f"{name}.MP4"
            if clip not in clips:
                report.append(f"{f.name}: {clip} UNBEKANNT")
                continue
            dur = clips[clip]["duration_s"]
            a, b = mmss(t0), mmss(t1)
            if b > dur + 2:
                report.append(f"{f.name}: {clip} {t0}–{t1} ueberschreitet Clipdauer {dur:.0f}s")
            for q in quotes:
                for seg in [s.strip() for s in q.split("[…]") if len(s.strip()) > 12]:
                    res, info = find_segment(clip, seg)
                    tag = f"{f.name} | {clip} {t0}–{t1} | '{seg[:60]}…'"
                    if res is None:
                        if info != "zu kurz fuer Pruefung":
                            report.append(f"FEHLT  {tag}")
                        continue
                    s0, s1 = res
                    if s0 < a - 8 or s1 > b + 8:
                        report.append(
                            f"ZEIT?  {tag} — gefunden bei {int(s0//60):02d}:{int(s0%60):02d}–{int(s1//60):02d}:{int(s1%60):02d} ({info})"
                        )
if report:
    print(f"{len(report)} Befund(e):")
    print("\n".join(report))
    sys.exit(1)
print("ALLE ZITATE/TIMECODES OK")
