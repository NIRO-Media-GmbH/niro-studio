"""Utterances mit Timecodes aus dem Scribe-Cache bauen.

Pro Clip: Liste {speaker, von, bis, von_s, bis_s, text} — Sprecherwechsel
oder Pausen > 1,5 s trennen Utterances. Ausgabe: _intern/utterances.json
"""
from __future__ import annotations

import json
from pathlib import Path

INTERN = Path(__file__).resolve().parent
CACHE = INTERN / "cache"
INDEX = json.loads((INTERN / "transcripts_index.json").read_text(encoding="utf-8"))


def fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def utterances(words: list[dict]) -> list[dict]:
    out: list[dict] = []
    cur: list[dict] = []
    for w in words:
        if cur and (w.get("speaker") != cur[-1].get("speaker") or w["start"] - cur[-1]["end"] > 1.5):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return [
        {
            "speaker": u[0].get("speaker"),
            "von": fmt(u[0]["start"]), "bis": fmt(u[-1]["end"]),
            "von_s": round(u[0]["start"], 1), "bis_s": round(u[-1]["end"], 1),
            "text": " ".join(w["text"] for w in u).strip(),
        }
        for u in out
    ]


result = []
for rec in INDEX:
    if not rec.get("ok") or rec.get("n_words", 0) == 0:
        continue
    cached = json.loads((CACHE / f"{rec['fingerprint']}.scribe.json").read_text(encoding="utf-8"))
    result.append({
        "name": rec["name"], "standort": rec["standort"], "kategorie": rec["kategorie"],
        "person": rec["person"], "duration_s": rec["duration_s"],
        "utterances": utterances(cached["words"]),
    })

out = INTERN / "utterances.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
n_utt = sum(len(r["utterances"]) for r in result)
print(f"{len(result)} Clips, {n_utt} Utterances -> {out}")
