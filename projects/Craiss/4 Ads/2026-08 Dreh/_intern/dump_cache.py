"""Alle bereits gecachten Transkripte auflisten — unabhängig vom Index.

Aufruf:
  dump_cache.py            -> Übersicht (Datei, Kamera, Länge, Wortzahl)
  dump_cache.py <stem>     -> Volltext eines Clips mit Utterance-Timecodes
  dump_cache.py --head N   -> erste N Zeichen jedes Clips (Selbstvorstellungen)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INTERN = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh/_intern")
FOOTAGE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Craiss Generation Logistik GmbH & Co. KG/02_Projekte/01_Projekt-4 Ads/"
    "03_Medien/01_Footage/Sortiert/Interviews"
)

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/src")
from niro_transcribe.footage.transcribe_clips import clip_fingerprint


def fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def utterances(words):
    out, cur = [], []
    for w in words:
        if not w["text"].strip():
            continue
        if cur and (w.get("speaker") != cur[-1].get("speaker")
                    or w["start"] - cur[-1]["end"] > 1.5):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def load_all():
    """(Pfad, Cache-Dict) für jeden Clip, der schon im Cache liegt.

    Bevorzugt transcripts_index.json (enthält den Fingerprint) — der ist
    unabhängig davon, wohin die Clips auf dem NAS sortiert wurden. Nur wenn
    kein Index existiert, wird pfadbasiert gesucht (Erstlauf)."""
    got = []
    index_path = INTERN / "transcripts_index.json"
    if index_path.exists():
        for rec in sorted(json.loads(index_path.read_text()),
                          key=lambda r: (r.get("vorordner") or "", r["name"])):
            f = INTERN / "cache" / f"{rec['fingerprint']}.scribe.json"
            if f.exists():
                got.append((Path(rec["path"]), json.loads(f.read_text())))
        return got
    for p in sorted(FOOTAGE.rglob("*.MP4")):
        f = INTERN / "cache" / f"{clip_fingerprint(p)}.scribe.json"
        if f.exists():
            got.append((p, json.loads(f.read_text())))
    return got


def main() -> None:
    args = sys.argv[1:]
    got = load_all()

    if args and args[0] == "--head":
        n = int(args[1]) if len(args) > 1 else 900
        for p, c in got:
            vor = p.parent.name if p.parent != FOOTAGE else "-"
            print("=" * 78)
            print(f"{vor}/{p.name}")
            print(" ".join(w["text"] for w in c["words"])[:n])
        return

    if args:
        stem = args[0]
        for p, c in got:
            if p.stem == stem or p.name == stem:
                for u in utterances(c["words"]):
                    txt = " ".join(w["text"] for w in u).strip()
                    print(f"[{fmt(u[0]['start'])}-{fmt(u[-1]['end'])}] "
                          f"{u[0].get('speaker','?')}: {txt}")
                return
        sys.exit(f"nicht im Cache: {stem}")

    print(f"{'ORDNER':<8} {'DATEI':<27} {'LÄNGE':>7} {'WÖRTER':>7}  SPRECHER")
    for p, c in got:
        vor = p.parent.name if p.parent != FOOTAGE else "-"
        ws = [w for w in c["words"] if w["text"].strip()]
        dur = ws[-1]["end"] if ws else 0
        sp = sorted({w.get("speaker") for w in ws if w.get("speaker")})
        print(f"{vor:<8} {p.name:<27} {fmt(dur):>7} {len(ws):>7}  {len(sp)}")
    print(f"\n{len(got)}/24 im Cache")


if __name__ == "__main__":
    main()
