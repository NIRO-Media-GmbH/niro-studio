from __future__ import annotations

import pytest

from niro_review import kommentare as km
from niro_review.ablage import ReviewFehler


def daten_mit(*texte):
    d = {"naechste_id": 1, "kommentare": []}
    for t in texte:
        km.anlegen(d, "Jan", t, frame=10)
    return d


def test_anlegen_ids_und_felder():
    d = {"naechste_id": 1, "kommentare": []}
    k1 = km.anlegen(d, "Jan", "  Schmatzer raus ", frame=50)
    k2 = km.anlegen(d, "Jan", "Zu hektisch")
    k3 = km.anlegen(d, "David", "Bereich", frame=10, bis_frame=40)
    assert [k["id"] for k in d["kommentare"]] == ["K1", "K2", "K3"] and d["naechste_id"] == 4
    assert k1["text"] == "Schmatzer raus" and k1["frame"] == 50 and k1["bis_frame"] is None and k1["status"] == "offen"
    assert k2["frame"] is None and k3["bis_frame"] == 40 and k1["antworten"] == [] and k1["antwort_claude"] is None
    with pytest.raises(ReviewFehler):
        km.anlegen(d, "Jan", "   ")
    with pytest.raises(ReviewFehler):
        km.anlegen(d, "Jan", "x", frame=-1)
    k4 = km.anlegen(d, "Jan", "Out vor In", frame=30, bis_frame=20)
    assert k4["bis_frame"] is None


def test_aendern_und_loeschen_nur_autor():
    d = daten_mit("a", "b")
    km.aendern(d, "K1", "Jan", text="neu")
    assert d["kommentare"][0]["text"] == "neu" and d["kommentare"][0]["geaendert"]
    with pytest.raises(ReviewFehler):
        km.aendern(d, "K1", "David", text="fremd")
    km.aendern(d, "K1", "David", status="erledigt")  # Status darf jeder
    assert d["kommentare"][0]["status"] == "erledigt"
    with pytest.raises(ReviewFehler):
        km.aendern(d, "K1", "Jan", status="umgesetzt")
    with pytest.raises(ReviewFehler):
        km.loeschen(d, "K2", "David")
    km.loeschen(d, "K2", "Jan")
    assert [k["id"] for k in d["kommentare"]] == ["K1"]
    with pytest.raises(ReviewFehler):
        km.finden(d, "K9")


def test_antworten():
    d = daten_mit("a")
    a = km.antworten(d, "K1", "Claude", "Umgesetzt in V2")
    assert d["kommentare"][0]["antworten"] == [a] and a["autor"] == "Claude"
    with pytest.raises(ReviewFehler):
        km.antworten(d, "K1", "Claude", " ")


def test_umsetzung_alles_oder_nichts():
    d = daten_mit("a", "b", "c")
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt"}, "K9": {"status": "umgesetzt"}}, 25.0)
    assert all(k["status"] == "offen" for k in d["kommentare"])
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"status": "kaputt"}}, 25.0)
    with pytest.raises(ReviewFehler):
        km.umsetzung_anwenden(d, {"K1": {"tc_neu": "3:12"}}, 25.0)
    ids = km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt", "antwort": "Schmatzer weg", "tc_neu": "00:00:03:12"},
                                    "K2": {"status": "rueckfrage", "antwort": "Welche Stelle?"},
                                    "K3": {"antwort": "nur Notiz", "frame_neu": 7}}, 25.0)
    assert ids == ["K1", "K2", "K3"]
    k1, k2, k3 = d["kommentare"]
    assert k1["status"] == "umgesetzt" and k1["antwort_claude"] == "Schmatzer weg" and k1["frame_neu"] == 87 and k1["tc_neu"] == "00:00:03:12"
    assert k2["status"] == "rueckfrage" and k3["status"] == "offen" and k3["frame_neu"] == 7 and k3["tc_neu"] == "00:00:00:07"


def test_sortiert_und_neu():
    d = {"naechste_id": 1, "kommentare": []}
    km.anlegen(d, "Jan", "spät", frame=500)
    km.anlegen(d, "Jan", "allgemein")
    km.anlegen(d, "Jan", "früh", frame=5)
    for i, k in enumerate(d["kommentare"]):
        k["angelegt"] = f"2026-09-18T10:0{i}:00"
    assert [k["text"] for k in km.sortiert(d["kommentare"])] == ["allgemein", "früh", "spät"]
    assert km.ist_neu(d["kommentare"][0], None)
    assert not km.ist_neu(d["kommentare"][0], "2026-09-18T10:00:30")
    assert km.ist_neu(d["kommentare"][1], "2026-09-18T10:00:30")
    d["kommentare"][0]["antworten"].append({"autor": "Jan", "text": "doch", "angelegt": "2026-09-18T11:00:00"})
    assert km.ist_neu(d["kommentare"][0], "2026-09-18T10:30:00")
    d["kommentare"][0]["antworten"][0]["autor"] = "Claude"
    assert not km.ist_neu(d["kommentare"][0], "2026-09-18T10:30:00")


def test_export():
    video = {"titel": "Dold 02 Fokus", "charge": "projects/Dold/Recruiting/2026-07 Dreh", "kunde": "Dold", "projekt": "Recruiting"}
    version = {"nr": 1, "fps": 25.0, "dauer_s": 23.04, "frames": 576, "breite": 2160, "hoehe": 3840, "notiz": "v1",
               "abgeschlossen": {"am": "2026-09-18T14:41:00", "von": "Jan"}, "geholt_am": None}
    d = {"naechste_id": 1, "kommentare": []}
    km.anlegen(d, "Jan", "Schmatzer | raus", frame=50)
    km.anlegen(d, "Jan", "Insgesamt\nzu hektisch")
    km.anlegen(d, "Jan", "Bereich", frame=100, bis_frame=150)
    km.antworten(d, "K1", "Claude", "erledigt in V2")
    km.umsetzung_anwenden(d, {"K1": {"status": "umgesetzt", "antwort": "weg", "tc_neu": "00:00:01:00"}}, 25.0)
    md = km.export_md(video, version, d, None, "18.09.2026")
    assert md.startswith("# Review-Kommentare „Dold 02 Fokus“ V1 (18.09.2026, abgeschlossen 18.09.2026 14:41 von Jan)")
    assert "| 1 | K2 | — | — | Insgesamt zu hektisch |  | offen | neu |" in md
    assert "| 2 | K1 | 00:00:02:00 |  | Schmatzer \\| raus | Claude: weg → V2 00:00:01:00 / Claude: erledigt in V2 | umgesetzt | neu |" in md
    assert "| 3 | K3 | 00:00:04:00 | bis 00:00:06:00 | Bereich |  | offen | neu |" in md
    js = km.export_json(video, version, d, "2026-09-18T10:00:00")
    assert js["quelle"] == "niro-review" and js["titel"] == "Dold 02 Fokus" and js["version"] == 1 and js["fps"] == 25.0
    assert [k["id"] for k in js["kommentare"]] == ["K2", "K1", "K3"] and js["kommentare"][1]["tc"] == "00:00:02:00"
    assert js["kommentare"][2]["tc_bis"] == "00:00:06:00" and all(k["neu"] for k in js["kommentare"])
    leer = km.export_md(video, version, {"naechste_id": 1, "kommentare": []}, None, "18.09.2026")
    assert "Keine Kommentare." in leer
