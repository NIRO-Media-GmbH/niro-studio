"""Seiten je Kapitel im Schnittplan-PDF zählen (Budget: 1 Übersicht, max 4 je Video — User 14.09.26: 3–4 Seiten ok, wenn es sich besser liest)."""
import re, sys
from pathlib import Path
from pypdf import PdfReader
pdf = Path(__file__).resolve().parent.parent / "Ergebnisse" / "O-Ton-Pläne" / "Rappold-Schnittanweisungen.pdf"
r = PdfReader(str(pdf))
counts = {}
for i, p in enumerate(r.pages, 1):
    head = (p.extract_text() or "").splitlines()[0] if i > 1 else "Deckblatt"
    m = re.search(r"\|\s*(.+)$", head)
    counts.setdefault(m.group(1).strip() if m else head, []).append(i)
print(f"{len(r.pages)} Seiten")
bad = False
for k, v in counts.items():
    lim = 1 if ("Übersicht" in k or k == "Deckblatt") else (4 if k.startswith("Video") else 3)
    flag = "  <-- ÜBER BUDGET" if len(v) > lim else ""
    bad |= bool(flag)
    print(f"{len(v)} S. ({v[0]}–{v[-1]}): {k[:80]}{flag}")
sys.exit(1 if bad else 0)
