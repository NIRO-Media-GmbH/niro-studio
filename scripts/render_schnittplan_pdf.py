"""Schnittanweisungs-PDF aus Markdown-Plaenen bauen (generisch, fpdf2).

Aufruf:  venv/bin/python scripts/render_schnittplan_pdf.py "<Chargen-Ordner>"
Liest:   <Charge>/Ergebnisse/O-Ton-Pläne/01-projekt-grundlagen.md  (Übersichtsseite)
         <Charge>/Ergebnisse/O-Ton-Pläne/video-*.md                (Video-Kapitel, sortiert)
         <Charge>/Ergebnisse/O-Ton-Pläne/99-anhang-*.md            (optional)
         <Charge>/_intern/pdf_meta.json                            (optional: titel, untertitel,
                                                                    warnbox, stand, kapitel_farben)
Schreibt: <Charge>/Ergebnisse/O-Ton-Pläne/Schnittanweisungen.pdf (oder meta["dateiname"])

Format-Konvention (NIRO-Standard, siehe WORKFLOW-Schnittplan.md):
- A4 quer; 1 Übersichtsseite; MAX 2 Seiten pro Video (Datei-Richtwert < 6.000 Zeichen).
- fpdf2-Fallen: core_fonts_encoding windows-1252, multi_cell mit new_x/new_y,
  Unicode-Sonderzeichen vorher ersetzen (clean()).
- Zeilen-Marker in Tabellen (Umbau-/Review-Pläne): enthält eine Zelle
  "[NEU]" / "[FIX]" / "[CHECK]", wird die ganze Zeile grün/orange/blau
  hinterlegt (Marker-Text bleibt sichtbar; Priorität NEU > FIX > CHECK).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

INK = (20, 20, 20)
ACCENT = (200, 16, 46)
GREY = (110, 110, 110)
LIGHT = (243, 243, 243)
ROW_MARKS = {  # Marker -> Zeilen-Hintergrund
    "[NEU]": (213, 235, 206),    # grün: neu einbauen
    "[FIX]": (250, 226, 202),    # orange: an Bestehendem ändern
    "[CHECK]": (218, 231, 246),  # blau: nur prüfen/bestätigen
}


def clean(s: str) -> str:
    repl = {
        "→": "->", "≠": "!=", "←": "<-", "✓": "[OK]", "✗": "[X]", "—": "-", "–": "-",
        "…": "...", "„": '"', "“": '"', "”": '"', "‘": "'", "’": "'",
        "×": "x", "•": "-", "✅": "[OK]", "❌": "[X]", "⚠": "!", "️": "",
        "−": "-", "≈": "ca. ", "≤": "<=", "≥": ">=",
        "**": "", "`": "",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s.encode("cp1252", errors="replace").decode("cp1252")


class Doc(FPDF):
    def __init__(self, kopfzeile: str):
        super().__init__(orientation="L", format="A4")
        self.core_fonts_encoding = "windows-1252"
        self.set_auto_page_break(True, margin=11)
        self.set_margins(10, 10, 10)
        self.kopfzeile = kopfzeile
        self.video_title = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, clean(f"{self.kopfzeile}  |  {self.video_title}"),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def footer(self):
        self.set_y(-11)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, f"NIRO Media - Seite {self.page_no()}", align="C")

    def h1(self, s: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*INK)
        self.multi_cell(0, 8, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h2(self, s: str):
        self.ln(1.2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ACCENT)
        self.multi_cell(0, 5.5, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def para(self, s: str, size=9):
        self.set_font("Helvetica", "", size)
        self.set_text_color(*INK)
        self.multi_cell(0, 4.2, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.8)

    def bullet(self, s: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*INK)
        self.set_x(self.l_margin + 3)
        self.multi_cell(self.epw - 3, 4.2, clean("- " + s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def reset_style(self):
        self.set_text_color(*INK)
        self.set_draw_color(185, 185, 185)
        self.set_line_width(0.2)
        self.set_fill_color(255, 255, 255)

    def md_table(self, header: list[str], rows: list[list[str]]):
        self.reset_style()
        n = len(header)
        weights = []
        for h in header:
            hl = h.lower()
            if any(k in hl for k in ("o-ton", "wortlaut", "sprechtext", "inhalt")):
                weights.append(3.2)
            elif "kommentar" in hl or "warum" in hl:
                weights.append(2.4)
            elif any(k in hl for k in ("bild", "b-roll", "caption", "grafik")):
                weights.append(1.8)
            elif any(k in hl for k in ("quelle", "datei")):
                weights.append(1.5)
            elif any(k in hl for k in ("von", "bis", "szene", "#")):
                weights.append(0.9)
            else:
                weights.append(1.4)
        widths = [w / sum(weights) * self.epw for w in weights]
        self.set_font("Helvetica", "", 7.5)
        self.set_fill_color(*LIGHT)
        with self.table(col_widths=widths, borders_layout="ALL", line_height=3.45,
                        text_align="LEFT", padding=0.8, repeat_headings=1) as t:
            hr = t.row()
            self.set_font("Helvetica", "B", 7.5)
            for h in header:
                hr.cell(clean(h))
            self.set_font("Helvetica", "", 7.5)
            self.set_fill_color(255, 255, 255)
            for row in rows:
                mark = next((col for m, col in ROW_MARKS.items()
                             if any(m in cell for cell in row)), None)
                style = FontFace(fill_color=mark) if mark else None
                r = t.row()
                for i in range(n):
                    r.cell(clean(row[i] if i < len(row) else ""), style=style)
        self.ln(2)


def render_markdown(pdf: Doc, md: str):
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            pdf.md_table(header, rows)
            continue
        if s.startswith("# "):
            pdf.h1(s[2:])
        elif s.startswith("## ") or s.startswith("### "):
            pdf.h2(s.lstrip("# "))
        elif s.startswith(("- ", "* ")):
            pdf.bullet(s[2:])
        else:
            pdf.para(s)
        i += 1


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Aufruf: render_schnittplan_pdf.py <Chargen-Ordner>")
    charge = Path(sys.argv[1])
    plaene = charge / "Ergebnisse" / "O-Ton-Pläne"
    meta_path = charge / "_intern" / "pdf_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    titel = meta.get("titel", charge.parent.parent.name)
    untertitel = meta.get("untertitel", "Schnittanweisungen")
    kopfzeile = f"{titel} - {untertitel}"
    farben = {k: tuple(v) for k, v in meta.get("kapitel_farben", {}).items()}

    pdf = Doc(kopfzeile)

    # Deckblatt
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*INK)
    pdf.cell(0, 12, clean(titel), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 10, clean(untertitel), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 7, clean(meta.get("stand", "NIRO Media")), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    if meta.get("warnbox"):
        pdf.ln(14)
        pdf.set_fill_color(255, 235, 235)
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.6)
        pdf.set_x(40)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*ACCENT)
        pdf.multi_cell(pdf.epw - 56, 6.5, clean(meta["warnbox"]),
                       border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.reset_style()

    # Übersicht + Kapitel + Anhang
    kapitel = [plaene / "01-projekt-grundlagen.md"]
    kapitel += sorted(plaene.glob("video-*.md"))
    kapitel += sorted(plaene.glob("99-anhang-*.md"))
    for f in kapitel:
        if not f.exists():
            continue
        md = f.read_text(encoding="utf-8")
        first = next((l for l in md.splitlines() if l.startswith("# ")), f.stem)
        pdf.video_title = first.lstrip("# ").strip()
        pdf.add_page()
        for key, col in farben.items():
            if key in first:
                pdf.set_fill_color(*col)
                pdf.rect(pdf.l_margin, pdf.get_y(), pdf.epw, 1.6, style="F")
                pdf.reset_style()
                pdf.ln(4)
                break
        render_markdown(pdf, md)

    out = plaene / meta.get("dateiname", "Schnittanweisungen.pdf")
    pdf.output(str(out))
    print(f"PDF geschrieben: {out}")


if __name__ == "__main__":
    main()
