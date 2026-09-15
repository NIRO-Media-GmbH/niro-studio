"""Zeilenhöhe je Tabellenzelle so berechnen wie render_schnittplan_pdf.py.

Zeigt pro Plan die Zeilen, deren höchste Zelle mehr als N Textzeilen braucht
(Default 4) — dort kürzen, statt das Layout zu quetschen.
Aufruf: rowcheck.py [N]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/scripts")
from render_schnittplan_pdf import Doc, clean  # noqa: E402

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 4
PLANS = Path(__file__).resolve().parent.parent / "Ergebnisse" / "O-Ton-Pläne"


def weights_for(header: list[str]) -> list[float]:
    w = []
    for h in header:
        hl = h.lower()
        if any(k in hl for k in ("o-ton", "wortlaut", "sprechtext", "inhalt")):
            w.append(3.2)
        elif "kommentar" in hl or "warum" in hl:
            w.append(2.4)
        elif any(k in hl for k in ("bild", "b-roll", "caption", "grafik")):
            w.append(1.8)
        elif any(k in hl for k in ("quelle", "datei")):
            w.append(1.5)
        elif any(k in hl for k in ("von", "bis", "szene", "#")):
            w.append(0.9)
        else:
            w.append(1.4)
    return w


pdf = Doc("x")
pdf.add_page()
pdf.set_font("Helvetica", "", 7.5)

for md in sorted([*PLANS.glob("video-*.md"), *PLANS.glob("99-anhang-*.md"), *PLANS.glob("01-*.md")]):
    lines = md.read_text(encoding="utf-8").splitlines()
    i, total_lines, rows = 0, 0, 0
    report = []
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= {"-", ":"}:
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            w = weights_for(header)
            widths = [x / sum(w) * pdf.epw for x in w]
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                counts = []
                for c, cw in zip(cells, widths):
                    txt = clean(c)
                    n = len(pdf.multi_cell(cw - 1.6, 3.45, txt, dry_run=True, output="LINES"))
                    counts.append(n)
                h = max(counts)
                total_lines += h
                rows += 1
                if h > LIMIT:
                    worst = [header[k] for k, n in enumerate(counts) if n == h]
                    report.append(f"   #{cells[0]:<4} {h} Zeilen  (zu hoch: {', '.join(worst)}) {counts}")
                i += 1
            continue
        i += 1
    print(f"{md.name}: {rows} Tabellenzeilen, Summe {total_lines} Textzeilen (~{total_lines * 3.45 + rows * 1.6:.0f} mm)")
    for r in report:
        print(r)
