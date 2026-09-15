"""Ähm-Schnittliste für die TA-Szenen (André, HiServ) aus den Cache-Transkripten.

Kunde: „Könnt Ihr bei André (HiServ) das ÄHM rausschneiden?"
Ausgabe: Ergebnisse/Transkripte/TA-aehm-liste.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CHARGE = Path(__file__).resolve().parent.parent
INDEX = CHARGE / "_intern" / "transcripts_index.json"
CACHE = CHARGE / "_intern" / "cache"
OUT = CHARGE / "Ergebnisse" / "Transkripte" / "TA-aehm-liste.md"
OFFSETS = json.loads((CHARGE / "_intern" / "timeline_offsets.json").read_text(encoding="utf-8"))

FILLER = re.compile(r"^(ähm+|äh+)[.,!?…]*$", re.IGNORECASE)
VOM_KUNDEN = {"TA4", "TA6", "TA9", "TA12", "TA14", "TA21", "TA22", "TA23", "TA24"}


def mmss_t(sec: float) -> str:
    m = int(sec) // 60
    s = sec - m * 60
    return f"{m}:{s:04.1f}".replace(".", ",")


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    ta = [r for r in index if r.get("ok") and r["camera"] == "TA"]
    ta.sort(key=lambda r: int(re.search(r"\d+", r["name"]).group()))

    lines = [
        "# TA (André, HiServ) — Ähm-Schnittliste",
        "",
        "Kundenwunsch: alle Ähms rausschneiden. **TL von/bis = Position in der",
        "DaVinci-Gesamttimeline** (alle Szenen als EIN Video, A→M→S→TA→TP —",
        "s. `00-timeline-referenz.md`); m:ss,Zehntel, von = Wortbeginn, bis =",
        "Wortende — an der Wellenform feinjustieren. ★ = vom Kunden ausgewählt.",
        "",
    ]
    total = 0
    summary = []
    for rec in ta:
        szene = Path(rec["name"]).stem
        words = json.loads(
            (CACHE / f"{rec['fingerprint']}.scribe.json").read_text(encoding="utf-8")
        )["words"]
        hits = []
        for i, w in enumerate(words):
            if FILLER.match(w["text"].strip()):
                before = " ".join(x["text"].strip() for x in words[max(0, i - 2):i])
                after = " ".join(x["text"].strip() for x in words[i + 1:i + 3])
                hits.append((w, before, after))
        star = " ★" if szene in VOM_KUNDEN else ""
        summary.append((szene + star, len(hits)))
        total += len(hits)
        if not hits:
            continue
        start = OFFSETS[szene]["start"]
        lines += [f"## {szene}{star} — {len(hits)}× · TL ab {mmss_t(start)}", "",
                  "| TL von | TL bis | Wort | Kontext |", "|---|---|---|---|"]
        for w, before, after in hits:
            ctx = f"…{before} **[{w['text'].strip()}]** {after}…".replace("|", "\\|")
            lines.append(
                f"| {mmss_t(start + w['start'])} | {mmss_t(start + w['end'])} | {w['text'].strip()} | {ctx} |"
            )
        lines.append("")

    lines += ["## Zusammenfassung", "", "| Szene | Ähms |", "|---|---|"]
    lines += [f"| {sz} | {n} |" for sz, n in summary]
    lines += ["", f"**Gesamt: {total} Ähms in {len(ta)} TA-Szenen.**", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"geschrieben: {OUT} ({total} Treffer)")


if __name__ == "__main__":
    main()
