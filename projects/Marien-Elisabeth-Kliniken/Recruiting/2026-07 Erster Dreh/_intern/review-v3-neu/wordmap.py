"""Wörter der neuen Fassung den Quellclips zuordnen (Scribe-Cache) -> Versatz Schnitt→Quelle je Wort."""
import json, re, sys
from pathlib import Path
P = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
idx = {r["name"].rsplit(".",1)[0]: r for r in json.load(open(P/"_intern/transcripts_index.json"))}
def norm(s): return re.sub(r"[^a-zäöüß0-9]", "", s.lower())
def words_src(stem):
    c = json.load(open(P/"_intern/cache"/f"{idx[stem]['fingerprint']}.scribe.json"))
    return [w for w in c["words"] if w["text"].strip()]
neu = [w for w in json.load(open(P/"_intern/review-v3-neu/scribe_neu.json"))["words"] if w["text"].strip()]
def span(ws, a, b): return [w for w in ws if w["start"] >= a - 1e-6 and w["end"] <= b + 1e-6]
def align(seg, src, s_from, s_to, label):
    s = span(src, s_from, s_to)
    print(f"\n== {label}")
    j = 0
    for w in seg:
        k = next((i for i in range(j, len(s)) if norm(s[i]["text"]) == norm(w["text"]) and norm(w["text"])), None)
        if k is None:
            print(f"  neu {w['start']:6.2f} {w['text']:<20} -> (kein Quellwort)"); continue
        off = s[k]["start"] - w["start"]
        print(f"  neu {w['start']:6.2f}–{w['end']:6.2f} {w['text']:<20} -> src {s[k]['start']:7.2f}–{s[k]['end']:7.2f}  Versatz {off:8.2f}")
        j = k + 1
    # auch Quellwörter im Bereich zeigen, die im Schnitt fehlen
    used = set()
    print("  Quelle im Bereich:", " ".join(f"{x['text']}[{x['start']:.2f}]" for x in s))
align(span(neu, 10.0, 17.6), words_src("FX3_9650"), 148.0, 162.0, "Zoran NEU (9650)")
align(span(neu, 19.8, 29.3), words_src("FX3_9651"), 45.0, 58.0, "Christian Ausstattung (9651)")
align(span(neu, 32.8, 35.0), words_src("FX3_9650"), 160.0, 168.0, "Zoran Augenhöhe (9650)")
align(span(neu, 35.3, 42.0), words_src("FX3_9649"), 722.0, 740.0, "Katja Monitor (9649)")
align(span(neu, 42.4, 49.3), words_src("FX3_9650"), 535.0, 550.0, "Zoran an die Hand (9650)")
align(span(neu, 50.3, 57.1), words_src("FX3_9651"), 400.0, 412.0, "Christian CTA (9651)")
align(span(neu, 0.0, 5.1), words_src("FX3_9652"), 25.0, 36.0, "Hook (9652)")
