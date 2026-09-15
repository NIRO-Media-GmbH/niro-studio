"""WLC Schnittanweisungen -> PDF (A4 quer, fpdf2).

Liest die finalen Markdown-Plaene aus Ergebnisse/O-Ton-Plaene/ und baut eine
Gesamt-PDF mit Deckblatt + Grundlagen + 6 Video-Kapiteln.
Bekannte fpdf2-Fallen beachtet: core_fonts_encoding windows-1252,
multi_cell mit new_x/new_y, Unicode-Zeichen ersetzen.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

CHARGE = Path(__file__).resolve().parent.parent
PLAENE = CHARGE / "Ergebnisse" / "O-Ton-Pläne"

INK = (20, 20, 20)
ACCENT = (200, 16, 46)      # WLC/Wuerth-Rot
GREY = (110, 110, 110)
LIGHT = (243, 243, 243)
ADEL = (0, 90, 160)         # Adelsheim-Blau
KUPF = (0, 130, 60)         # Kupferzell-Gruen


def clean(s: str) -> str:
    repl = {
        "→": "->", "≠": "!=", "←": "<-", "✓": "[OK]", "✗": "[X]",
        "—": "-", "–": "-", "…": "...", "„": '"',
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "×": "x", "•": "-", "✅": "[OK]", "❌": "[X]",
        "⚠": "!", "️": "", "**": "", "`": "",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s.encode("cp1252", errors="replace").decode("cp1252")


class Doc(FPDF):
    def __init__(self):
        super().__init__(orientation="L", format="A4")
        self.core_fonts_encoding = "windows-1252"
        self.set_auto_page_break(True, margin=11)
        self.set_margins(10, 10, 10)
        self.video_title = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, clean(f"WLC Würth Logistik - Recruiting-Videos - Schnittanweisungen  |  {self.video_title}"),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def footer(self):
        self.set_y(-11)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, f"NIRO Media - Seite {self.page_no()}", align="C")

    def h1(self, s: str, color=INK):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*color)
        self.multi_cell(0, 8, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h2(self, s: str):
        self.ln(1.2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ACCENT)
        self.multi_cell(0, 5.5, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def para(self, s: str, size=9, style="", color=INK):
        self.set_font("Helvetica", style, size)
        self.set_text_color(*color)
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
        # Spaltengewichte: O-Ton/Wortlaut + Kommentar breit, Timecodes schmal
        weights = []
        for h in header:
            hl = h.lower()
            if any(k in hl for k in ("o-ton", "wortlaut", "sprechtext", "inhalt", "problem")):
                weights.append(3.2)
            elif "kommentar" in hl or "warum" in hl or "fix" in hl or "einschätzung" in hl.replace("ae", "ä"):
                weights.append(2.4)
            elif any(k in hl for k in ("bild", "b-roll", "caption", "grafik", "was stattdessen")):
                weights.append(1.8)
            elif any(k in hl for k in ("quelle", "datei")):
                weights.append(1.5)
            elif any(k in hl for k in ("von", "bis", "szene", "#")):
                weights.append(0.9)
            else:
                weights.append(1.4)
        total = sum(weights)
        widths = [w / total * self.epw for w in weights]

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
                r = t.row()
                for i in range(n):
                    r.cell(clean(row[i] if i < len(row) else ""))
        self.ln(2)


def parse_md_table(lines: list[str], i: int):
    header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    i += 2  # skip separator
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return header, rows, i


def render_markdown(pdf: Doc, md: str):
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("|"):
            if i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
                header, rows, i = parse_md_table(lines, i)
                pdf.md_table(header, rows)
                continue
            pdf.para(s)
            i += 1
            continue
        if s.startswith("# "):
            pdf.h1(s[2:])
        elif s.startswith("## "):
            pdf.h2(s[3:])
        elif s.startswith("### "):
            pdf.h2(s[4:])
        elif s.startswith(("- ", "* ")):
            pdf.bullet(s[2:])
        elif re.match(r"^\d+\. ", s):
            pdf.para(s)
        else:
            pdf.para(s)
        i += 1


def standort_color(name: str):
    if "Adelsheim" in name:
        return ADEL
    if "Kupferzell" in name:
        return KUPF
    return ACCENT


def build(out_path: Path, video_files: list[Path], grundlagen_md: str, anhang_md: str | None = None):
    pdf = Doc()

    # ---- Deckblatt ----
    pdf.add_page()
    pdf.ln(28)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*INK)
    pdf.cell(0, 12, "WLC Würth Logistik", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 10, "Recruiting-Videos - Schnittanweisungen", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 7, "6 Videos - Dreh 18.05. (Adelsheim) & 20.05. (Kupferzell)",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.cell(0, 7, "NIRO Media - Stand: 08.07.2026", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(14)
    # Warnbox Standort-Trennung
    pdf.set_fill_color(255, 235, 235)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.6)
    x, y, w = 40, pdf.get_y(), pdf.epw - 56
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*ACCENT)
    pdf.multi_cell(w, 6.5, clean(
        "WICHTIGSTE REGEL - STANDORT-TRENNUNG\n"
        "Jedes Video gehört zu GENAU EINEM Standort (Adelsheim ODER Kupferzell). "
        "Es darf ausschließlich Bild- und Tonmaterial dieses Standorts verwendet werden - "
        "kein einziger Clip vom jeweils anderen Standort. Einzige Ausnahme: Video 6 (Employer-Brand) "
        "darf beide Standorte mischen. Die Regel gilt für O-Töne, B-Roll, Atmos und Schnittbilder."),
        border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.reset_style()

    # ---- Grundlagen ----
    pdf.video_title = "Projekt-Grundlagen"
    pdf.add_page()
    render_markdown(pdf, grundlagen_md)

    # ---- Videos ----
    for f in video_files:
        md = f.read_text(encoding="utf-8")
        first = next((l for l in md.splitlines() if l.startswith("# ")), f.stem)
        pdf.video_title = first.lstrip("# ").strip()
        pdf.add_page()
        # Standort-Farbbalken
        col = standort_color(first)
        pdf.set_fill_color(*col)
        pdf.rect(pdf.l_margin, pdf.get_y(), pdf.epw, 1.6, style="F")
        pdf.reset_style()
        pdf.ln(4)
        render_markdown(pdf, md)

    if anhang_md:
        pdf.video_title = "Anhang"
        pdf.add_page()
        render_markdown(pdf, anhang_md)

    pdf.output(str(out_path))
    print(f"PDF geschrieben: {out_path}")


if __name__ == "__main__":
    grundlagen = (PLAENE / "01-projekt-grundlagen.md").read_text(encoding="utf-8")
    anhang = (PLAENE / "99-anhang-ungenutztes-material.md").read_text(encoding="utf-8")
    videos = sorted(PLAENE.glob("video-[1-6]-*.md"))
    if len(videos) != 6:
        sys.exit(f"Erwarte 6 Video-Plaene, gefunden: {[v.name for v in videos]}")
    build(PLAENE / "WLC-Schnittanweisungen.pdf", videos, grundlagen, anhang)
