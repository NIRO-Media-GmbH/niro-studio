"""Vorlage (Stand 15.09.2026): Plan-Zeilen — exakter Scribe-Wortlaut je Bereich + Dauer + Sprecherfolge.

Aufruf:  tools/autocut/venv/bin/python _intern/plan_rows.py  -> druckt Zeilen und schreibt _intern/plan_rows.json
Liest    Scribe-Cache über _intern/find_tc.py (load, secs): _intern/transcripts_index.json + _intern/cache/*.scribe.json.
Schreibt _intern/plan_rows.json (nr, teil, szene, person, clip, bereiche, texte, dauer_s) → Eingabe für _intern/cutlist_aus_plan.py.
Bereiche je Zeile mit _intern/find_tc.py wortgenau suchen; mehrere Bereiche = echter Innenschnitt (ein Cut je Bereich).
Prüfen: Summe gegen die Ziellänge, Sprecherfolge (längste Folge derselben Person, max. 2 Takes hintereinander).
Die Sprecherfolge nutzt den ersten Buchstaben des Kurznamens → Kurznamen mit verschiedenen Anfangsbuchstaben wählen.
Läuft beim Import komplett durch (kein main) → nicht per importlib laden.
Fassungen: vor einer Kürzung die alte Fassung (plan_rows.py, cutlist_aus_plan.py) nach _intern/archiv/<JJJJ-MM-TT Fassung>/ kopieren.

Herkunft: Taxodia-Charge, _intern/plan_rows.py
"""
import json, sys
from itertools import groupby
from pathlib import Path
I = Path(__file__).resolve().parent
sys.path.insert(0, str(I))
from find_tc import load, secs  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
ROWS = [  # nr, teil, szene, person (Kurzname), clip (Stem der Ton-Kamera), bereiche ["mm:ss,d–mm:ss,d", …]; Grafik-Zeile: person/clip None, bereiche []
    # (1, 1, "Kaltstart", "Kurzname", "FX3_0001", ["02:03,3–02:05,1", "02:10,0–02:12,4"]),
]
EXTRA = {  # nr → Dauer [s] jeder Zeile ohne Clip (Titel, Endcard …) — Pflicht für jede Grafik-Zeile
    # 4: 3.0,
}
OPTIONAL = {  # nr → (Clip-Stem, "mm:ss,d–mm:ss,d") optionaler Zusatzbereich, erscheint nur im Bericht
    # 22: ("FX3_0001", "37:29,5–37:36,6"),
}
# ── Ende ANPASSEN ──────────────────────────────────

cache, out, total, seq = {}, [], 0.0, []
for nr, teil, szene, person, clip, bereiche in ROWS:
    texts, dur = [], 0.0
    if clip:
        ws = cache.setdefault(clip, load(clip))
        for b in bereiche:
            a, e = [secs(x) for x in b.split("–")]
            sel = [w for w in ws if w["start"] >= a - 0.05 and w["end"] <= e + 0.05]
            texts.append(" ".join(w["text"] for w in sel))
            dur += e - a
        seq.append(person[0])
    else:
        dur = EXTRA[nr]
    total += dur
    out.append({"nr": nr, "teil": teil, "szene": szene, "person": person, "clip": clip,
                "bereiche": bereiche, "texte": texts, "dauer_s": round(dur, 1)})
    print(f"#{nr:<2} T{teil} {szene:<24} {person or '-':<9} {clip or '-':<9} {' + '.join(bereiche):<42} {dur:5.1f}s")
    for t in texts:
        print(f"      „{t}“")
opt_s = sum(secs(b.split("–")[1]) - secs(b.split("–")[0]) for _, b in OPTIONAL.values())
opt_txt = f"{opt_s:.1f}".replace(".", ",")
print(f"\nSumme {total:.1f} s = {int(total // 60)}:{total % 60:04.1f}  (optional +{opt_txt} s: {OPTIONAL})")
print("Sprecherfolge:", " ".join(seq))
runs = max(len(list(g)) for _, g in groupby(seq))  # längste Folge gleicher Anfangsbuchstaben
print("längste Folge derselben Person:", runs)
(I / "plan_rows.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
