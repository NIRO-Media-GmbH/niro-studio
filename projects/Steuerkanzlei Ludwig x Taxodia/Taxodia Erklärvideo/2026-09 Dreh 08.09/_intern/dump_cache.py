"""Transkripte aus dem Scribe-Cache lesen (index-basiert, überlebt Verschieben).

Aufruf:
  dump_cache.py                 -> Übersicht (Ordner, Datei, Länge, Wörter, Sprecher)
  dump_cache.py <stem>          -> Volltext mit Utterance-Timecodes + Sprecher
  dump_cache.py <stem> von bis  -> nur Ausschnitt (Sekunden oder mm:ss)
  dump_cache.py --head N        -> erste N Zeichen je Clip (Selbstvorstellungen)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INTERN = Path(__file__).resolve().parent


def fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"


def secs(x: str) -> float:
    if ":" in x:
        m, s = x.split(":")
        return int(m) * 60 + float(s)
    return float(x)


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
    index = json.loads((INTERN / "transcripts_index.json").read_text())
    got = []
    for rec in sorted(index, key=lambda r: (r["kategorie"], r["name"])):
        f = INTERN / "cache" / f"{rec['fingerprint']}.scribe.json"
        if rec.get("ok") and f.exists():
            got.append((rec, json.loads(f.read_text())))
    return got


def main() -> None:
    args = sys.argv[1:]
    got = load_all()

    if args and args[0] == "--head":
        n = int(args[1]) if len(args) > 1 else 900
        for rec, c in got:
            print("=" * 78)
            print(f"{rec['kategorie']}/{rec['name']} [{rec['kamera']}]")
            print(" ".join(w["text"] for w in c["words"])[:n])
        return

    if args:
        stem = args[0]
        a = secs(args[1]) if len(args) > 1 else 0.0
        b = secs(args[2]) if len(args) > 2 else 1e9
        for rec, c in got:
            if rec["name"].rsplit(".", 1)[0] == stem or rec["name"] == stem:
                for u in utterances(c["words"]):
                    if u[-1]["end"] < a or u[0]["start"] > b:
                        continue
                    txt = " ".join(w["text"] for w in u).strip()
                    print(f"[{fmt(u[0]['start'])}-{fmt(u[-1]['end'])}] "
                          f"{u[0].get('speaker', '?')}: {txt}")
                return
        sys.exit(f"nicht im Cache: {stem}")

    print(f"{'ORDNER':<42} {'DATEI':<27} {'LÄNGE':>6} {'WÖRTER':>6}  SPRECHER (Wörter)")
    for rec, c in got:
        ws = [w for w in c["words"] if w["text"].strip()]
        dur = ws[-1]["end"] if ws else 0
        cnt: dict[str, int] = {}
        for w in ws:
            cnt[w.get("speaker") or "?"] = cnt.get(w.get("speaker") or "?", 0) + 1
        sp = ", ".join(f"{k}:{v}" for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]))
        print(f"{rec['kategorie']:<42} {rec['name']:<27} {fmt(dur):>6} {len(ws):>6}  {sp}")
    print(f"\n{len(got)} Clips im Cache")


if __name__ == "__main__":
    main()
