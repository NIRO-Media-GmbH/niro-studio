"""Plan-Zeilen: exakter Scribe-Wortlaut je Bereich + Dauer + Sprecherfolge.
Aufruf: plan_rows.py  -> druckt Zeilen und schreibt _intern/plan_rows.json"""
import json, sys
from pathlib import Path
I = Path(__file__).resolve().parent
sys.path.insert(0, str(I))
from find_tc import load, secs  # noqa: E402

# Kurzfassung 15.09.2026 (User: 1 min kürzer, alle wichtigen Aussagen bleiben). Langfassung 14.09. mit 28 Zeilen:
# _intern/archiv/2026-09-14 Langfassung/plan_rows.py. Gestrichen: Hof und Kurs, Nicht allein, Schnelle Antwort,
# Vor der Prüfung (alt #15, #16, #17, #22 → Anhang A17–A20). Gekürzt: Kanzlei und Hein ohne Namensvorstellung
# (Bauchbinde), Ampel ohne Einleitung „um einen guten Überblick …“, CTA Kanzleien ohne „im Zeitalter des
# Fachkräftemangels … die Arbeit bleibt liegen“.
ROWS = [  # nr, teil, szene, person, clip, bereiche
    (1, 1, "Kaltstart", "Ludwig", "FX3_0222", ["02:03,3–02:05,1"]),
    (2, 1, "Kaltstart", "Flammann", "FX3_0223", ["03:47,9–03:53,3"]),
    (3, 1, "Kaltstart", "Hein", "FX3_0228", ["15:43,1–15:46,0"]),
    (4, 1, "Titel", None, None, []),
    (5, 1, "Die Kanzlei", "Ludwig", "FX3_0222", ["07:58,2–08:05,6"]),
    (6, 1, "Die Suche", "Ludwig", "FX3_0222", ["09:14,4–09:25,9"]),
    (7, 1, "Hein stellt sich vor", "Hein", "FX3_0228", ["00:48,7–00:59,7"]),
    (8, 1, "Die Entscheidung", "Ludwig", "FX3_0222", ["04:25,9–04:29,8", "04:40,1–04:49,5"]),
    (9, 1, "Taxodia", "Flammann", "FX3_0223", ["00:51,9–01:12,7"]),
    (10, 1, "Studium reicht nicht", "Hein", "FX3_0228", ["02:01,8–02:17,1"]),
    (11, 1, "Bachelor Professional", "Flammann", "FX3_0223", ["11:41,9–11:59,2"]),
    (12, 1, "Der Einstieg", "Flammann", "FX3_0223", ["10:14,1–10:19,3", "10:27,1–10:29,3", "10:45,2–10:53,5"]),
    (13, 1, "Die Rechnung", "Ludwig", "FX3_0222", ["24:32,1–24:42,3"]),
    (14, 1, "Lernwoche", "Hein", "FX3_0228", ["03:43,8–03:49,1"]),
    (15, 1, "Mitarbeit", "Hein", "FX3_0228", ["09:03,4–09:10,9"]),
    (16, 2, "Ampel", "Flammann", "FX3_0223", ["22:23,9–22:24,3", "22:33,7–22:36,7", "22:46,0–23:04,9"]),
    (17, 2, "Kanzlei wird informiert", "Ludwig", "FX3_0222", ["22:33,7–22:37,4"]),
    (18, 2, "Faire Abrechnung", "Ludwig", "FX3_0222", ["22:14,1–22:17,3"]),
    (19, 2, "Zweifel an online", "Hein", "FX3_0228", ["05:03,2–05:15,4", "05:21,2–05:23,6"]),
    (20, 2, "Ergebnis", "Flammann", "FX3_0223", ["29:40,4–29:56,0"]),
    (21, 2, "Die Note", "Hein", "FX3_0228", ["13:29,1–13:32,8"]),
    (22, 2, "CTA Kanzleien", "Flammann", "FX3_0223", ["36:59,5–37:00,5", "37:09,2–37:12,5", "37:15,4–37:23,8"]),
    (23, 2, "CTA Kandidaten", "Hein", "FX3_0228", ["21:35,2–21:45,4"]),
    (24, 2, "Endcard", None, None, []),
]
EXTRA = {4: 3.0, 24: 7.0}
OPTIONAL = {22: ("FX3_0223", "37:29,5–37:36,6")}

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
print(f"\nSumme {total:.1f} s = {int(total // 60)}:{total % 60:04.1f}  (optional +7,1 s: {OPTIONAL})")
print("Sprecherfolge:", " ".join(seq))
runs = max(len(r) for r in "".join(seq).replace("LF", "L F").replace("FL", "F L").replace("LH", "L H").replace("HL", "H L").replace("FH", "F H").replace("HF", "H F").split())
print("längste Folge derselben Person:", runs)
(I / "plan_rows.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
