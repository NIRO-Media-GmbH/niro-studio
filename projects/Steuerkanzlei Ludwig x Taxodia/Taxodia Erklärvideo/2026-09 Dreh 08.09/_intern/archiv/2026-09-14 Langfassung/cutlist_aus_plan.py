"""AutoCut-Cutlist aus den geprüften Plan-Zeilen bauen (Taxodia, 14.09.2026).

Liest   _intern/autocut/cutlist.json (Entwurf von autocut_cutlist_draft.py: Szene, Bild, Kommentar,
        Caption, Sound), _intern/plan_rows.json (Bereiche je Zeile), Transkript-Index + Scribe-Cache.
Schreibt _intern/autocut/cutlist.json (überschreibt den Entwurf).

Regeln (prompts/cutlist.md + Plan):
- Ein Cut je Bereich der Quelle („+" = echter Innenschnitt, im Plan so festgelegt).
- in_s/out_s = exakte Wortgrenzen aus dem Scribe-Cache (Wörter, die im gerundeten Bereich ±0,05 s liegen).
- hart_in, wenn das vorige Wort näher als der Vorlauf (6 Frames) liegt oder der Cut nicht der erste ist;
  hart_out, wenn das nächste Wort näher als der Nachlauf (8 Frames) liegt oder der Cut nicht der letzte ist.
- Sperren mit exakten Bereichen aus der Material-Analyse (00-material-und-abweichungen.md).
"""
from __future__ import annotations

import json
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
INTERN = CH / "_intern"
FPS = 25.0
H_IN, H_OUT = 6 / FPS, 8 / FPS

idx = {r["name"].rsplit(".", 1)[0]: r for r in json.loads((INTERN / "transcripts_index.json").read_text())}


def words(stem: str) -> list[dict]:
    data = json.loads((INTERN / "cache" / f"{idx[stem]['fingerprint']}.scribe.json").read_text())
    return [w for w in data["words"] if w.get("type", "word") == "word" and w["text"].strip()]


def secs(tc: str) -> float:
    m, s = tc.split(":")
    return int(m) * 60 + float(s.replace(",", "."))


PERSON = {
    "Ludwig": ("Friedrich Ludwig", "Steuerberater, Steuerkanzlei Ludwig"),
    "Flammann": ("Jörn Flammann", "Gründer und Geschäftsführer, Taxodia"),
    "Hein": ("Jan Philipp Hein", "Steuersachbearbeiter, Steuerkanzlei Ludwig"),
}

SPERREN = [  # (Stem, von, bis, Grund)
    ("FX3_0222", "01:36,4", "01:39,4", "Veganer-Äußerung („Dann sind sie noch Veganer …“)"),
    ("FX3_0222", "02:10,0", "02:16,9", "Recruiter-Schelte („Geschäftsmodelle, die versuchen, dich erst mal auszunehmen …“)"),
    ("FX3_0222", "06:14,0", "06:24,1", "Veganer-Äußerung / Regie („nichts gegen Veganer“)"),
    ("FX3_0222", "11:34,0", "12:10,5", "„Alle Fachkräfte, die nur 'ne steuerliche Ausbildung haben, sind … gar nicht einsetzbar“ — widerspricht Taxodia-Kurs für StFA"),
    ("FX3_0222", "12:43,0", "14:16,6", "kein Ton (Mikrotausch)"),
    ("FX3_0222", "14:16,6", "15:05,9", "Crew-Gespräch mit Veganer-Äußerungen"),
    ("FX3_0222", "23:52,5", "24:31,6", "Kurspreise, Provision, Gehalt (nicht freigegeben)"),
    ("FX3_0222", "25:00,2", "25:17,7", "Preis 480 € (nicht auf der Website)"),
    ("FX3_0222", "31:18,6", "31:22,3", "Wettbewerbsaussage „nur noch uns in Süddeutschland“"),
    ("FX3_0223", "02:32,2", "03:17,0", "Fall der Landwirtin mit Note (Dritte)"),
    ("FX3_0223", "09:21,7", "09:28,0", "„Musterkurs … Wir finanzieren das“ (verwechselt Musterkurs und Einstieg)"),
    ("FX3_0223", "30:06,0", "30:27,7", "Durchfaller-Aussage"),
    ("FX3_0223", "33:05,4", "33:52,7", "Take mit Tür-Knall (Retake 34:13–34:45)"),
    ("FX3_0228", "00:11,1", "00:35,2", "Take 1 mit falschem Abschluss „Fachwirt Rechnungswesen“"),
]


def main() -> None:
    draft = json.loads((INTERN / "autocut" / "cutlist.json").read_text())
    rows = {str(r["nr"]): r for r in json.loads((INTERN / "plan_rows.json").read_text())}
    cache: dict[str, list[dict]] = {}
    beats = []
    for b in draft["beats"]:
        r = rows[b["nr"]]
        nb = dict(b)
        if r["clip"]:
            stem = r["clip"]
            ws = cache.setdefault(stem, words(stem))
            kurz = r["person"]
            nb["person"], nb["rolle"] = PERSON[kurz]
            nb["clip"] = idx[stem]["path"]
            cuts = []
            for k, bereich in enumerate(r["bereiche"]):
                a, e = [secs(x) for x in bereich.split("–")]
                sel = [i for i, w in enumerate(ws) if w["start"] >= a - 0.05 and w["end"] <= e + 0.05]
                if not sel:
                    raise SystemExit(f"#{b['nr']}: keine Wörter in {bereich}")
                i0, i1 = sel[0], sel[-1]
                in_s, out_s = float(ws[i0]["start"]), float(ws[i1]["end"])
                gap_in = in_s - float(ws[i0 - 1]["end"]) if i0 > 0 else 99.0
                gap_out = float(ws[i1 + 1]["start"]) - out_s if i1 + 1 < len(ws) else 99.0
                cuts.append({
                    "in_s": round(in_s, 3), "out_s": round(out_s, 3),
                    "text": " ".join(w["text"] for w in ws[i0:i1 + 1]),
                    "hart_in": bool(k > 0 or gap_in < H_IN),
                    "hart_out": bool(k < len(r["bereiche"]) - 1 or gap_out < H_OUT),
                })
            nb["cuts"] = cuts
            nb["plan_dauer_s"] = round(sum(c["out_s"] - c["in_s"] for c in cuts), 1)
        else:
            nb["typ"] = "grafik"
        beats.append(nb)
    sperren = [{"clip": idx[s]["path"], "von_s": secs(v), "bis_s": secs(z), "grund": g} for s, v, z, g in SPERREN]
    out = {
        "video": draft["video"],
        "ziel_laenge_s": 300,
        "fps": draft["fps"],
        "format": draft["format"],
        "pause_s": draft["pause_s"],
        "beats": beats,
        "sperren": sperren,
        "hinweise": [
            "Ziellänge laut User 14.09.2026: 4–5 min (ziel_laenge_s = oberer Wert 300).",
            "„[…]“ bedeutet in diesem Plan einen echten Innenschnitt: die Quelle nennt dann mehrere Bereiche mit „+“ → ein Cut je Bereich (abweichend vom Standard „durchgehend“, im Plan so festgelegt).",
            "Kamerapaare in media.json nach Person gruppiert (Material liegt nach Kamera getrennt in Kamera-A/Kamera-B).",
            "Textsperren ohne Zeit gegengelesen: keine Preise/Gehalt, kein „von Anfang an produktiv“, keine Veganer- oder Recruiter-Passage in den Cut-Texten.",
            "„die zwei Besten“ (#24) und Note 1,06 (#25) nur als O-Ton, keine Einblendung (nicht auf der Website).",
            "Titel (#4) und Endcard (#28) sind Grafik-Platzhalter (Motion); B-Roll bleibt leer (Stufe 3 ausgesetzt).",
        ],
    }
    (INTERN / "autocut" / "cutlist.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_cuts = sum(len(b.get("cuts") or []) for b in beats)
    print(f"cutlist.json: {len(beats)} Beats, {n_cuts} Cuts, {len(sperren)} Sperren")
    for b in beats:
        for c in b.get("cuts") or []:
            print(f"  #{b['nr']:<3} {Path(b['clip']).stem} {c['in_s']:8.3f}–{c['out_s']:8.3f} "
                  f"hart_in={int(c['hart_in'])} hart_out={int(c['hart_out'])}  {c['text'][:60]}")


if __name__ == "__main__":
    main()
