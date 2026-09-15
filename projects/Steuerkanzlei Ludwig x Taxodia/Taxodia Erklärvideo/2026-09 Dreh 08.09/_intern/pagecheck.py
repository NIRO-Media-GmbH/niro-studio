"""Seitenbudget im Schnittplan-PDF prüfen (User 14.09.26: so viele Seiten wie nötig, gesamt max. 20).
Meldet außerdem fast leere Schlussseiten je Kapitel (< 900 Zeichen Text)."""
import re, sys
from pathlib import Path
from pypdf import PdfReader
pdf = Path(__file__).resolve().parent.parent / "Ergebnisse" / "O-Ton-Pläne" / "Taxodia-Schnittanweisungen.pdf"
r = PdfReader(str(pdf))
chapters, texts = {}, {}
for i, p in enumerate(r.pages, 1):
    t = p.extract_text() or ""
    head = t.splitlines()[0] if i > 1 else "Deckblatt"
    m = re.search(r"\|\s*(.+)$", head)
    k = m.group(1).strip() if m else head
    chapters.setdefault(k, []).append(i)
    texts[i] = len(t)
bad = len(r.pages) > 20
print(f"{len(r.pages)} Seiten (max. 20){'  <-- ÜBER BUDGET' if bad else ''}")
for k, v in chapters.items():
    last = v[-1]
    leer = len(v) > 1 and texts[last] < 900
    bad |= leer
    print(f"{len(v)} S. ({v[0]}–{v[-1]}): {k[:90]}{'  <-- Schlussseite fast leer (' + str(texts[last]) + ' Zeichen)' if leer else ''}")
sys.exit(1 if bad else 0)
