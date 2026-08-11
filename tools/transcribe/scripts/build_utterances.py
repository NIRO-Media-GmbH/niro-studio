"""Utterances mit Timecodes aus dem Scribe-Cache bauen (generisch).

Aufruf:  venv/bin/python scripts/build_utterances.py "<Chargen-Ordner>"
Erwartet: <Charge>/_intern/transcripts_index.json + <Charge>/_intern/cache/
Schreibt: <Charge>/_intern/utterances.json

Pro Clip: Liste {speaker, von, bis, von_s, bis_s, text} — Sprecherwechsel
oder Pausen > 1,5 s trennen Utterances. Timecodes = Position in der Datei.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def utterances(words: list[dict]) -> list[dict]:
    out: list[list[dict]] = []
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


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Aufruf: build_utterances.py <Chargen-Ordner>")
    intern = Path(sys.argv[1]) / "_intern"
    index = json.loads((intern / "transcripts_index.json").read_text(encoding="utf-8"))
    result = []
    for rec in index:
        if not rec.get("ok") or rec.get("n_words", 0) == 0:
            continue
        cached = json.loads(
            (intern / "cache" / f"{rec['fingerprint']}.scribe.json").read_text(encoding="utf-8")
        )
        result.append({
            "name": rec["name"], "standort": rec.get("standort"),
            "kategorie": rec.get("kategorie"), "person": rec.get("person"),
            "duration_s": rec.get("duration_s"),
            "utterances": utterances(cached["words"]),
        })
    out = intern / "utterances.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(r["utterances"]) for r in result)
    print(f"{len(result)} Clips, {n} Utterances -> {out}")


if __name__ == "__main__":
    main()
