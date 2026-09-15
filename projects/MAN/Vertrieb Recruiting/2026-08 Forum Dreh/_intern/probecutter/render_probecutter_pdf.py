"""Einmal-Renderer: Probecutter-Guide-PDF (MAN Gesamtvideo, V5).

Bewusste Abweichung vom Standard-Schnittplan-Format (Erklaer-PDF fuer
Probecutter, Auftrag David 01.09.2026) — KEIN neuer Workflow, gehoert nur
zu dieser Charge. Basis-Konventionen (fpdf2, cp1252-clean, A4 quer,
Tabellen-Gewichte) uebernommen aus tools/transcribe/scripts/
render_schnittplan_pdf.py.

Zwei-Pass-Render: Pass 1 zaehlt die Kapitel-Startseiten, Pass 2 schreibt
das Inhaltsverzeichnis fest auf Seite 2 (deterministisches Layout, daher
identische Seitenzahlen).

Aufruf: tools/transcribe/venv/bin/python render_probecutter_pdf.py
Liest:  ../../Ergebnisse/O-Ton-Pläne/Probecutter/*.md
Schreibt: ../../Ergebnisse/O-Ton-Pläne/Probecutter/
          MAN-Gesamtvideo-Probecutter-Guide.pdf
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

CHARGE = Path(__file__).resolve().parents[2]
SRC = CHARGE / "Ergebnisse" / "O-Ton-Pläne" / "Probecutter"
OUT = SRC / "MAN-Gesamtvideo-Probecutter-Guide.pdf"

INK = (25, 25, 25)
GREY = (110, 110, 110)
LIGHT = (243, 243, 243)

TEILE = {
    "A": ("TEIL A - VORBEREITUNG", (0, 95, 158)),
    "B": ("TEIL B - DER SCHNITT", (228, 0, 43)),
    "C": ("TEIL C - FINISHING", (60, 60, 59)),
    "F": ("FRAGEN", (200, 140, 0)),
}

CHAPTERS = [
    ("A", "01-auftrag.md"),
    ("A", "02-plan-lesen.md"),
    ("A", "03-material.md"),
    ("A", "04-premiere-setup.md"),
    ("B", "05-schnittplan.md"),
    ("B", "06-sperren.md"),
    ("C", "07-color-grading.md"),
    ("C", "08-untertitel.md"),
    ("C", "09-grafiken-jan.md"),
    ("C", "10-musik.md"),
    ("C", "11-export.md"),
    ("F", "12-faq.md"),
]

BOX_STYLES = {  # typ -> (label, balken, fuellung)
    "merk": ("GUT ZU WISSEN", (0, 95, 158), (226, 238, 248)),
    "achtung": ("ACHTUNG", (228, 0, 43), (253, 232, 232)),
    "tipp": ("TIPP", (76, 140, 43), (228, 241, 223)),
    "jan": ("AN JAN WENDEN", (200, 140, 0), (250, 240, 215)),
}

TITEL = "MAN Vertrieb - Das Gesamtvideo"
UNTERTITEL = "Schnittplan & Guide für deinen Probetag"
STAND = "Stand: 01.09.2026  ·  NIRO Media  ·  Ansprechpartner: Jan"
WARNBOX = (
    "ERST LESEN, DANN SCHNEIDEN. Die Timecodes gelten nur für FX3-Dateien. "
    "Keine Vergütungs- und Vertragsthemen ins Video (Kapitel 6). "
    "Bei Fragen: FAQ hinten - dann Jan."
)


def clean(s: str) -> str:
    repl = {
        "→": "->", "≠": "!=", "←": "<-", "✓": "[OK]", "✗": "[X]", "—": "-", "–": "-",
        "…": "...", "„": '"', "“": '"', "”": '"', "‘": "'", "’": "'", "‚": "'",
        "×": "x", "•": "-", "✅": "[OK]", "❌": "[X]", "⚠": "!", "️": "",
        "−": "-", "≈": "ca. ", "≤": "<=", "≥": ">=",
        "**": "", "`": "",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s.encode("cp1252", errors="replace").decode("cp1252")


class Doc(FPDF):
    def __init__(self):
        super().__init__(orientation="L", format="A4")
        self.core_fonts_encoding = "windows-1252"
        self.set_auto_page_break(True, margin=12)
        self.set_margins(11, 13, 11)
        self.suppress_header = True
        self.teil_key = "A"
        self.chapter_label = ""
        self.toc_entries: list[tuple[str, str, str, int]] = []

    # --- Rahmen ---------------------------------------------------------
    def header(self):
        if self.suppress_header:
            return
        name, col = TEILE[self.teil_key]
        self.set_fill_color(*col)
        self.rect(0, 0, 6, 210, style="F")
        self.set_y(6)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*col)
        self.cell(0, 4, clean(name), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GREY)
        self.cell(0, 4, clean(self.chapter_label), align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(215, 215, 215)
        self.set_line_width(0.2)
        self.line(self.l_margin, 11.5, self.w - self.r_margin, 11.5)
        self.set_y(14)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 5, clean(f"{TITEL}  ·  Seite {self.page_no()}"), align="C")

    def reset_style(self):
        self.set_text_color(*INK)
        self.set_draw_color(185, 185, 185)
        self.set_line_width(0.2)
        self.set_fill_color(255, 255, 255)

    def need(self, h: float):
        if self.get_y() + h > self.page_break_trigger:
            self.add_page()

    # --- Bausteine ------------------------------------------------------
    def h1(self, s: str, nr: str):
        _, col = TEILE[self.teil_key]
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*col)
        self.cell(13, 10, nr, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_text_color(*INK)
        self.multi_cell(0, 10, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y() + 0.5
        self.set_draw_color(*col)
        self.set_line_width(0.8)
        self.line(self.l_margin, y, self.l_margin + 42, y)
        self.reset_style()
        self.ln(4)

    def h2(self, s: str):
        self.need(16)
        _, col = TEILE[self.teil_key]
        self.ln(1.5)
        self.set_font("Helvetica", "B", 12.5)
        self.set_text_color(*col)
        self.multi_cell(0, 6, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.reset_style()
        self.ln(1.2)

    def h3(self, s: str):
        self.need(13)
        self.ln(0.8)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 5, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.8)

    def para(self, s: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*INK)
        self.multi_cell(0, 4.7, clean(s), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.4)

    def bullet(self, s: str):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*INK)
        self.set_x(self.l_margin + 3.5)
        self.multi_cell(self.epw - 3.5, 4.7, clean("-  " + s),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.4)

    def box(self, typ: str, text: str):
        label, bar, fill = BOX_STYLES.get(typ, BOX_STYLES["merk"])
        self.set_font("Helvetica", "", 9.5)
        inner_w = self.epw - 14
        lines = self.multi_cell(inner_w, 4.6, clean(text), dry_run=True,
                                output="LINES")
        h = len(lines) * 4.6 + 11
        self.need(h + 2)
        y0 = self.get_y() + 1
        self.set_fill_color(*fill)
        self.rect(self.l_margin, y0, self.epw, h, style="F")
        self.set_fill_color(*bar)
        self.rect(self.l_margin, y0, 2.2, h, style="F")
        self.set_xy(self.l_margin + 6, y0 + 2.5)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*bar)
        self.cell(0, 4, clean(label), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_xy(self.l_margin + 6, self.get_y() + 0.6)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*INK)
        self.multi_cell(inner_w, 4.6, clean(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y0 + h + 2.5)
        self.reset_style()

    def md_table(self, header: list[str], rows: list[list[str]]):
        self.reset_style()
        n = len(header)
        weights = []
        for h in header:
            hl = h.lower()
            if "o-ton" in hl:
                weights.append(3.4)
            elif "quelle" in hl:
                weights.append(2.2)
            elif "kommentar" in hl or "warum" in hl or "musik-verhalten" in hl:
                weights.append(1.9)
            elif "bild" in hl or "einsatz" in hl or "beispiel" in hl:
                weights.append(1.7)
            elif hl in ("#", "ca.", "nr"):
                weights.append(0.45)
            elif "was drinsteht" in hl or "wert" in hl or "wo es liegt" in hl:
                weights.append(2.0)
            else:
                weights.append(1.1)
        widths = [w / sum(weights) * self.epw for w in weights]
        size = 7.6 if any("o-ton" in h.lower() for h in header) else 8.6
        line_h = 3.55 if size < 8 else 4.0
        self.set_fill_color(*LIGHT)
        with self.table(col_widths=widths, borders_layout="ALL",
                        line_height=line_h, text_align="LEFT", padding=1.0,
                        repeat_headings=1) as t:
            hr = t.row()
            self.set_font("Helvetica", "B", size)
            for h in header:
                hr.cell(clean(h))
            self.set_font("Helvetica", "", size)
            self.set_fill_color(255, 255, 255)
            for row in rows:
                r = t.row()
                for i in range(n):
                    r.cell(clean(row[i] if i < len(row) else ""))
        self.ln(2.5)


def render_markdown(pdf: Doc, md: str, nr: str):
    lines = md.splitlines()
    buf: list[str] = []

    def flush():
        if buf:
            pdf.para(" ".join(buf))
            buf.clear()

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            flush()
            i += 1
            continue
        if s.startswith(":::"):
            flush()
            typ = s[3:].strip() or "merk"
            i += 1
            btxt = []
            while i < len(lines) and lines[i].strip() != ":::":
                btxt.append(lines[i].strip())
                i += 1
            i += 1
            pdf.box(typ, " ".join(b for b in btxt if b))
            continue
        if s.startswith("|") and i + 1 < len(lines) and \
                re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            flush()
            header = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            pdf.md_table(header, rows)
            continue
        if s.startswith("# "):
            flush()
            pdf.h1(s[2:], nr)
        elif s.startswith("## "):
            flush()
            pdf.h2(s[3:])
        elif s.startswith("### "):
            flush()
            pdf.h3(s[4:])
        elif s.startswith(("- ", "* ")):
            flush()
            pdf.bullet(s[2:])
        else:
            buf.append(s)
        i += 1
    flush()


def render_toc_page(pdf: Doc, entries):
    pdf.set_y(22)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*INK)
    pdf.cell(0, 10, "Inhalt", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    last_teil = None
    for teil, nr, title, page in entries:
        name, col = TEILE[teil]
        if teil != last_teil:
            pdf.ln(1.5)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*col)
            pdf.cell(0, 6, clean(name), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            last_teil = teil
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*INK)
        pdf.set_x(pdf.l_margin + 6)
        pdf.cell(150, 5.8, clean(f"{nr}  {title}"),
                 new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 5.8, f"Seite {page}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 4.6, clean(
        "Tipp: Im PDF-Reader die Lesezeichen-Leiste öffnen - jedes Kapitel "
        "ist dort verlinkt."), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.reset_style()


def build(toc_data) -> Doc:
    pdf = Doc()

    # Seite 1 — Deckblatt
    pdf.add_page()
    _, col_b = TEILE["B"]
    pdf.set_fill_color(*col_b)
    pdf.rect(0, 0, 297, 5, style="F")
    pdf.ln(38)
    pdf.set_font("Helvetica", "B", 30)
    pdf.set_text_color(*INK)
    pdf.cell(0, 13, clean(TITEL), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*col_b)
    pdf.cell(0, 9, clean(UNTERTITEL), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 7, clean(STAND), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(16)
    pdf.set_fill_color(253, 232, 232)
    pdf.set_draw_color(*col_b)
    pdf.set_line_width(0.6)
    pdf.set_x(48)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*col_b)
    pdf.multi_cell(pdf.epw - 74, 6.5, clean(WARNBOX), border=1, fill=True,
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.reset_style()

    # Seite 2 — Inhaltsverzeichnis (Pass 1: leer, Pass 2: echt)
    pdf.add_page()
    if toc_data is not None:
        render_toc_page(pdf, toc_data)

    # Kapitel
    pdf.suppress_header = False
    for idx, (teil, fname) in enumerate(CHAPTERS, start=1):
        md = (SRC / fname).read_text(encoding="utf-8")
        first = next((l for l in md.splitlines() if l.startswith("# ")), fname)
        title = first.lstrip("# ").strip()
        nr = f"{idx}."
        pdf.teil_key = teil
        pdf.chapter_label = f"{nr} {title}"
        pdf.add_page()
        pdf.start_section(clean(f"{nr} {title}"), level=0)
        pdf.toc_entries.append((teil, nr, title, pdf.page_no()))
        render_markdown(pdf, md, nr)
    return pdf


def main() -> None:
    pass1 = build(None)
    final = build(pass1.toc_entries)
    if [e[3] for e in final.toc_entries] != [e[3] for e in pass1.toc_entries]:
        raise SystemExit("Seitenzahlen zwischen Pass 1 und Pass 2 verschoben!")
    final.output(str(OUT))
    print(f"PDF geschrieben: {OUT} ({final.page_no()} Seiten)")


if __name__ == "__main__":
    main()
