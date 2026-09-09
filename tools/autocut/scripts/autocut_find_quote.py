"""Zitat im Transkript eines Clips finden — Hilfsskript für Claude beim Bau der Cutlist.

Aufruf:
    venv/bin/python scripts/autocut_find_quote.py "<Charge>" --clip FX3_9557 --text "…" [--near 03:37] [--all] [--min-score 0.7]

Ausgabe (JSON, beste zuerst):
    ohne --all   ein Objekt: gefunden, clip, start_s, end_s, score, text, speaker, segmente, hinweise
    mit  --all   bis zu 10 Kandidaten für das erste Fragment (start_s, end_s, score, text, speaker)

Exit 2, wenn das Zitat nicht gefunden wurde. Liest nur; schreibt nichts in die Charge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.align import align_quote, find_quote, find_span, split_fragments  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.quote_align import fmt as mmss  # noqa: E402

ALL_MIN_SCORE = 0.6   # Kandidatenliste (--all) ist bewusst großzügiger als align_min_score


def parse_near(s: str) -> float:
    """„03:37", „03:37,5", „1:03:37" oder reine Sekunden „217.5" → Sekunden."""
    try:
        parts = [float(p.replace(",", ".")) for p in s.strip().split(":")]
    except ValueError:
        parts = []
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise AutoCutError(f"Zeitangabe nicht lesbar: „{s}“ (erwartet mm:ss, mm:ss,d, h:mm:ss oder Sekunden)")


def clip_words(charge: Charge, clip: str) -> tuple[dict, list[dict]]:
    """Index-Eintrag und Cache-Wörter zum Clip (Name, Stem oder voller Pfad)."""
    key = clip.strip().lower()
    hits = [rec for rec in charge.load_index()
            if rec["name"].lower() == key or Path(rec["name"]).stem.lower() == key
            or rec["path"].lower() == key or Path(rec["path"]).stem.lower() == key]
    if not hits:
        raise AutoCutError(f"Clip {clip} nicht im Transkript-Index der Charge ({charge.intern / 'transcripts_index.json'}).")
    if len(hits) > 1:
        raise AutoCutError(f"Clip {clip} ist im Index mehrdeutig — bitte den vollen Pfad angeben:\n"
                           + "\n".join("  " + h["path"] for h in hits))
    rec = hits[0]
    cached = charge.cache_transcript(rec["fingerprint"])
    if not cached or not cached.get("words"):
        raise AutoCutError(f"Kein Transkript im Cache für {rec['name']} (Fingerprint {rec['fingerprint']}).")
    return rec, cached["words"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Zitat wortgenau im Transkript eines Clips finden.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--clip", required=True, help="Clip-Name, Stem (FX3_9557) oder voller Pfad")
    ap.add_argument("--text", required=True, help="Zitat aus dem Cutter-Plan (mit „[…]“ für Auslassungen)")
    ap.add_argument("--near", help="mm:ss-Hinweis aus dem Plan; entscheidet bei mehreren Takes")
    ap.add_argument("--all", action="store_true", help="bis zu 10 Kandidaten für das erste Fragment zeigen")
    ap.add_argument("--min-score", type=float,
                    help=f"Mindest-Score (Standard: align_min_score aus der Config, mit --all {ALL_MIN_SCORE})")
    a = ap.parse_args()

    ch = Charge.open(a.charge)
    rec, words = clip_words(ch, a.clip)
    near = parse_near(a.near) if a.near else None
    min_score = a.min_score if a.min_score is not None else float(ch.config["align_min_score"])

    if a.all:
        frags = split_fragments(a.text)
        if not frags:
            raise AutoCutError("Zitat enthält nach dem Säubern keinen Text.")
        all_min = a.min_score if a.min_score is not None else ALL_MIN_SCORE
        cands = find_span(words, frags[0], near_s=near, min_score=all_min)[:10]
        if not cands:
            print(json.dumps({"gefunden": False, "clip": rec["path"], "fragment": frags[0], "min_score": all_min,
                              "hinweis": f"Kein Kandidat mit Score ≥ {all_min} — Zitat und Clip prüfen oder --min-score senken."},
                             ensure_ascii=False))
            sys.exit(2)
        for m in cands:
            print(json.dumps({"start_s": m.start_s, "end_s": m.end_s, "start": mmss(m.start_s), "end": mmss(m.end_s),
                              "score": round(m.score, 3), "text": m.text, "speaker": m.speaker}, ensure_ascii=False))
        return

    m = find_quote(words, a.text, near_s=near, min_score=min_score)
    if m is None:
        raw = align_quote(words, a.text, near, min_score=min_score)
        hinweise = list(raw.flags) if raw is not None else []
        print(json.dumps({"gefunden": False, "clip": rec["path"], "min_score": min_score, "hinweise": hinweise,
                          "hinweis": "Mit --all Kandidaten anzeigen oder --min-score senken"}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps({"gefunden": True, "clip": rec["path"], "start_s": m.start_s, "end_s": m.end_s,
                      "start": mmss(m.start_s), "end": mmss(m.end_s), "score": round(m.score, 3),
                      "text": m.text, "speaker": m.speaker,
                      "segmente": [{"in_s": s[0], "out_s": s[1], "text": s[2]} for s in m.segments],
                      "hinweise": m.flags}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except AutoCutError as e:
        sys.exit(f"FEHLER: {e}")
