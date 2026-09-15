"""Vorlage (Stand 15.09.2026): AutoCut-Cutlist aus den geprüften Plan-Zeilen bauen.

Aufruf:  tools/autocut/venv/bin/python _intern/cutlist_aus_plan.py
Liest    _intern/autocut/cutlist.json (Entwurf von autocut_cutlist_draft.py: Szene, Bild, Kommentar,
         Caption, Sound), _intern/plan_rows.json (Bereiche je Zeile, aus _intern/plan_rows.py),
         Transkript-Index _intern/transcripts_index.json + Scribe-Cache _intern/cache/<fingerprint>.scribe.json.
Schreibt _intern/autocut/cutlist.json (überschreibt den Entwurf — Entwurf vorher z. B. als cutlist_entwurf.json sichern).
Danach   autocut_verify.py (neuer Hash in verify.json), sonst verweigert autocut_build.py den Bau.

Regeln (prompts/cutlist.md + Plan):
- Ein Cut je Bereich der Quelle („+" = echter Innenschnitt, im Plan so festgelegt).
- in_s/out_s = exakte Wortgrenzen aus dem Scribe-Cache (Wörter, die im gerundeten Bereich ±0,05 s liegen).
- hart_in, wenn das vorige Wort näher als der Vorlauf (6 Frames) liegt oder der Cut nicht der erste ist;
  hart_out, wenn das nächste Wort näher als der Nachlauf (8 Frames) liegt oder der Cut nicht der letzte ist.
- Sperren mit exakten Bereichen aus der Material-Analyse (00-material-und-abweichungen.md).
- Beat-Nummern des Entwurfs = nr in plan_rows.json; Kurznamen („person") in plan_rows.json = Schlüssel in PERSON.

Herkunft: Taxodia-Charge, _intern/cutlist_aus_plan.py
"""
from __future__ import annotations

import json
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
INTERN = CH / "_intern"

# ── ANPASSEN je Charge ─────────────────────────────
FPS = 25.0  # Timeline-Bildrate [fps] (media.json → format); Standard (15.09.)
H_IN, H_OUT = 6 / FPS, 8 / FPS  # Vorlauf 6 / Nachlauf 8 Frames [s] → Schwelle für hart_in/hart_out; Standard (15.09.)
ZIEL_LAENGE_S: float | None = None  # Ziellänge [s] → cutlist.json „ziel_laenge_s" (Konzept/User); None = Wert aus dem Entwurf

PERSON = {  # Kurzname aus plan_rows.py → (voller Name, Rolle/Firma) für Bauchbinde, Marker und Bericht
    # "Kurzname": ("Vorname Nachname", "Rolle, Firma"),
}

SPERREN = [  # (Stem, von, bis, Grund) — Clip-Stem der Ton-Kamera, Zeiten mm:ss,d aus 00-material-und-abweichungen.md
    # ("FX3_0001", "01:36,4", "01:39,4", "Grund der Sperre (z. B. Preise nicht freigegeben)"),
]

HINWEISE = [  # → cutlist.json „hinweise": Ziellänge/Fassung, Kamerapaare, gegengelesene Textsperren, Aussagen nur als O-Ton, Platzhalter, enge Anschlüsse
    "„[…]“ bedeutet in diesem Plan einen echten Innenschnitt: die Quelle nennt dann mehrere Bereiche mit „+“ → ein Cut je "
    "Bereich (abweichend vom Standard „durchgehend“, im Plan so festgelegt).",  # Standard (15.09.)
    # "Enge Anschlüsse gegenhören: #<nr> „<letztes Wort>“ → „<erstes Wort>“ (kaum Pause, keine Zweitkamera → Punch-in).",
]
# ── Ende ANPASSEN ──────────────────────────────────

idx = {r["name"].rsplit(".", 1)[0]: r for r in json.loads((INTERN / "transcripts_index.json").read_text())}


def words(stem: str) -> list[dict]:
    data = json.loads((INTERN / "cache" / f"{idx[stem]['fingerprint']}.scribe.json").read_text())
    return [w for w in data["words"] if w.get("type", "word") == "word" and w["text"].strip()]


def secs(tc: str) -> float:
    m, s = tc.split(":")
    return int(m) * 60 + float(s.replace(",", "."))


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
        "ziel_laenge_s": ZIEL_LAENGE_S if ZIEL_LAENGE_S is not None else draft.get("ziel_laenge_s"),
        "fps": draft["fps"],
        "format": draft["format"],
        "pause_s": draft["pause_s"],
        "beats": beats,
        "sperren": sperren,
        "hinweise": HINWEISE,
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
