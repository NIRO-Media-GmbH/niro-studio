from pypdf import PdfWriter
from niro_transcribe.pdf_extract import extract_text


def _make_pdf(path, pages):
    # pypdf kann leere Seiten schreiben; wir prüfen die Verkettungs-/Leselogik
    w = PdfWriter()
    for _ in pages:
        w.add_blank_page(width=200, height=200)
    with open(path, "wb") as f:
        w.write(f)


def test_extract_returns_string_per_page(tmp_path):
    pdf = tmp_path / "skript.pdf"
    _make_pdf(pdf, ["s1", "s2"])
    text = extract_text(pdf)
    assert isinstance(text, str)
    # zwei Seiten -> ein Seitentrenner
    assert text.count("\n\n") >= 1
