"""Tests für plan.py — Cutter-Plan (Markdown-Tabelle) lesen."""
from __future__ import annotations

from pathlib import Path

import pytest

from niro_autocut import plan as P
from niro_autocut.charge import AutoCutError

FIX = Path(__file__).parent / "fixtures" / "plan_mek_auszug.md"


def test_parse_rows_and_types():
    pl = P.parse_plan(FIX)
    assert pl.ziel_laenge_s == 185 and pl.format_hint == "16:9"
    assert "Volkmarsen" in pl.verboten_text
    nrs = [r.nr for r in pl.rows]
    assert nrs[:5] == ["1", "2", "3", "4", "5"]
    typen = {r.nr: r.typ for r in pl.rows}
    assert typen["1"] == "oton" and typen["2"] == "vo" and typen["4"] == "bild" and typen["11"] == "bild"


def test_row_fields_and_hints():
    pl = P.parse_plan(FIX)
    r1 = next(r for r in pl.rows if r.nr == "1")
    assert r1.oton.startswith("„Weil das mein Job ist")
    assert r1.plan_dauer_s == 3
    assert r1.tc_hints[0]["stem"] == "FX3_9557" and abs(r1.tc_hints[0]["von_s"] - 217) < 0.01
    assert r1.tc_hints[0]["bis_s"] == 219
    assert "Sandra" in r1.quelle and r1.bild.startswith("Gehaltenes Gesicht")


def test_helpers():
    assert P.parse_mmss("03:37") == 217 and P.parse_mmss("1:02:03") == 3723
    assert P.parse_plan_dauer("Harter Schnitt danach. ~3 s") == 3
    assert P.parse_plan_dauer("~10 s") == 10 and P.parse_plan_dauer("kein Wert") is None
    hints = P.parse_tc_hints("Victoria · FX3_0544 · 21:15–21:17 + 21:21–21:33")
    assert [(h["stem"], h["von_s"], h["bis_s"]) for h in hints] == [("FX3_0544", 1275, 1277), ("FX3_0544", 1281, 1293)]
    assert P.parse_ziel_laenge("Ziellänge 90–120 s") == 120
    assert P.parse_ziel_laenge("Ziellänge ≈ 3:05 (12 Stimmen") == 185
    assert P.classify_row("VO: „Zwei Häuser…", "VO (Erzähler)", "x") == "vo"
    assert P.classify_row("—", "—", "Grafik (NIRO Motion): Marke") == "grafik"
    assert P.classify_row("—", "—", "Mavic: …") == "bild"
    assert P.classify_row('„Text"', "Anna · FX3_1", "Frontal") == "oton"


def test_fixture_header_and_material():
    pl = P.parse_plan(FIX)
    assert pl.titel.startswith("Imagefilm — „Zwei Häuser")
    assert pl.file == str(FIX)
    assert "BEIDE Roots erlaubt" in pl.material_text
    assert "**Verboten:**" in pl.material_text  # Verboten-Zeile gehört zum Material-Abschnitt
    assert not pl.verboten_text.startswith("**")  # verboten_text ist der reine Inhalt nach dem Label
    assert len(pl.rows) == 12


def test_all_fixture_rows_have_hints_where_oton():
    pl = P.parse_plan(FIX)
    for r in pl.rows:
        if r.typ == "oton":
            assert r.tc_hints, f"Zeile {r.nr} ohne Timecode-Hinweis"
            assert r.tc_hints[0]["stem"].startswith("FX3_")
            assert r.plan_dauer_s is not None
        else:
            assert r.tc_hints == []
    r10 = next(r for r in pl.rows if r.nr == "10")
    assert r10.tc_hints == [{"stem": "FX3_9651", "von_s": 40, "bis_s": 57}]


def test_tc_hints_tolerate_spaces_and_hms():
    hints = P.parse_tc_hints("…/FX3_9557.MP4 · 03:37 – 03:39")
    assert [(h["stem"], h["von_s"], h["bis_s"]) for h in hints] == [("FX3_9557", 217, 219)]
    hints = P.parse_tc_hints("DJI_0402 · 1:02:03")
    assert hints == [{"stem": "DJI_0402", "von_s": 3723, "bis_s": None}]
    assert P.parse_tc_hints("VO (Erzähler)") == []
    assert P.parse_tc_hints("") == []
    # Zeitangabe ohne vorher genannten Stem wird nicht zugeordnet
    assert P.parse_tc_hints("Sandra · 03:37–03:39") == []


def test_classify_does_not_mistake_words_for_vo():
    assert P.classify_row("„Vor allem das Team.", "Anna · FX3_1", "Frontal") == "oton"
    assert P.classify_row("Voll gut hier.", "Anna · FX3_1", "Frontal") == "oton"
    assert P.classify_row("", "VO (Erzähler)", "Montage") == "vo"
    assert P.classify_row("", "", "Endcard mit Logo") == "grafik"
    assert P.classify_row("", "", "") == "bild"
    # Markdown-Hervorhebung um „kein O-Ton" (Förch Messe, WLC) darf nicht als O-Ton durchgehen
    assert P.classify_row("*kein O-Ton*", "—", "Messe-Impressionen") == "bild"
    assert P.classify_row("— (kein O-Ton)", "Textkarte, belegt: Thomas · FX3_0305 · 02:26–02:58", "Textkarte") == "bild"


def test_ziel_laenge_variants():
    assert P.parse_ziel_laenge("Ziellänge: 90 s") == 90
    assert P.parse_ziel_laenge("Ziellänge 2:40–3:05") == 185
    assert P.parse_ziel_laenge("Ziellaenge 60s") == 60
    assert P.parse_ziel_laenge("kein Wert") is None
    assert P.parse_mmss("0:05") == 5


def test_parse_plan_dauer_variants():
    assert P.parse_plan_dauer("~2,5 s") == 2.5
    assert P.parse_plan_dauer("≈ 4 s") == 4
    assert P.parse_plan_dauer("Kürzpfad ~2:40") is None
    assert P.parse_plan_dauer("") is None


def test_table_ends_at_first_non_table_line(tmp_path):
    text = FIX.read_text(encoding="utf-8")
    text += "\n\n## Anhang\n\n| # | Szene | O-Ton | Quelle | Bild | Sound | Caption | Kommentar |\n|---|---|---|---|---|---|---|---|\n| 99 | Fremd | — | — | x | — | — | ~1 s |\n"
    p = tmp_path / "video-9-test.md"
    p.write_text(text, encoding="utf-8")
    pl = P.parse_plan(p)
    assert [r.nr for r in pl.rows][-1] == "12"


def test_parse_plan_without_table_raises(tmp_path):
    p = tmp_path / "video-9-leer.md"
    p.write_text("# Nur Kopf\n\n## Ziel & Story\nZiellänge 60 s\n", encoding="utf-8")
    with pytest.raises(AutoCutError, match="Ablauf-Tabelle"):
        P.parse_plan(p)


def test_to_dict_from_dict_roundtrip():
    pl = P.parse_plan(FIX)
    d = pl.to_dict()
    assert d["rows"][0]["nr"] == "1" and d["rows"][0]["tc_hints"][0]["stem"] == "FX3_9557"
    back = P.Plan.from_dict(d)
    assert back == pl
    assert P.PlanRow.from_dict(d["rows"][3]).typ == "bild"
