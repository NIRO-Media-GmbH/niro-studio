from __future__ import annotations

import unicodedata

import pytest

from niro_review import modell
from niro_review.ablage import json_schreiben


@pytest.mark.parametrize("name,titel", [
    ("Dold 02 Fokus Bagger und Kran – Entwurf v1.mp4", "Dold 02 Fokus Bagger und Kran"),
    ("Dold 12 Fokus Staplerfahrer (David, Sebastian) – Entwurf v1 (Claude 2026-09-17).mp4", "Dold 12 Fokus Staplerfahrer (David, Sebastian)"),
    ("03_Viele Sprachen, ein Team_V6.mp4", "03_Viele Sprachen, ein Team"),
    ("Taxodia-Weg Messe V2.mov", "Taxodia-Weg Messe"),
    ("Craiss 01 Testimonial - v3.mp4", "Craiss 01 Testimonial"),
    ("Video ohne Version.mp4", "Video ohne Version"),
    ("Version 5 Bericht.mp4", "Version 5 Bericht"),
])
def test_titel_aus_dateiname(name, titel):
    assert modell.titel_aus_dateiname(name) == titel


def test_titel_nfc():
    nfd = unicodedata.normalize("NFD", "Förch Azubi V1.mp4")
    assert modell.titel_aus_dateiname(nfd) == "Förch Azubi"


def test_sortierung():
    assert modell.sortierung_aus_titel("Dold 02 Fokus Bagger") == "02"
    assert modell.sortierung_aus_titel("13 140 Jahre") == "13"
    assert modell.sortierung_aus_titel("Taxodia-Weg Messe") == "Taxodia-Weg Messe"
    videos = [{"titel": "b", "sortierung": "b"}, {"titel": "Dold 10", "sortierung": "10"}, {"titel": "Dold 02", "sortierung": "02"}, {"titel": "A", "sortierung": "A"}]
    assert [v["titel"] for v in sorted(videos, key=modell.sortier_schluessel)] == ["Dold 02", "Dold 10", "A", "b"]


def test_video_und_versionen(tmp_path):
    ordner = modell.video_ordner("Dold", "Recruiting", "Dold 02 Fokus", tmp_path)
    assert ordner == tmp_path / "Dold" / "Recruiting" / "Dold 02 Fokus"
    assert modell.video_lesen(ordner) is None
    assert modell.versionsnummern(ordner) == [] and modell.naechste_version(ordner) == 1
    video = modell.video_anlegen(ordner, "Dold", "Recruiting", "Dold 02 Fokus", "projects/Dold/Recruiting/2026-07 Dreh")
    assert video["sortierung"] == "02" and video["freigegeben"] is None and modell.video_lesen(ordner)["titel"] == "Dold 02 Fokus"
    modell.version_schreiben(ordner, 1, {"nr": 1, "abgeschlossen": None})
    (ordner / "V3").mkdir()  # ohne version.json zählt nicht
    modell.version_schreiben(ordner, 2, {"nr": 2, "abgeschlossen": None})
    assert modell.versionsnummern(ordner) == [1, 2] and modell.naechste_version(ordner) == 3
    assert modell.version_lesen(ordner, 2)["nr"] == 2 and modell.version_lesen(ordner, 9) is None


def test_zustand_und_zaehler():
    video = {"freigegeben": None}
    assert modell.zustand(video, None) == "leer"
    assert modell.zustand(video, {"abgeschlossen": None}) == "review-offen"
    assert modell.zustand(video, {"abgeschlossen": {"am": "x", "von": "Jan"}}) == "bei-claude"
    assert modell.zustand({"freigegeben": {"am": "x", "von": "Jan"}}, {"abgeschlossen": None}) == "freigegeben"
    komm = {"kommentare": [
        {"status": "offen", "angelegt": "2026-09-18T10:00:00"},
        {"status": "rueckfrage", "angelegt": "2026-09-18T11:00:00"},
        {"status": "erledigt", "angelegt": "2026-09-18T12:00:00"},
    ]}
    assert modell.zaehler(komm, None) == {"offen": 2, "neu": 3, "gesamt": 3}
    assert modell.zaehler(komm, "2026-09-18T10:30:00") == {"offen": 2, "neu": 2, "gesamt": 3}
    assert modell.zaehler({}, None) == {"offen": 0, "neu": 0, "gesamt": 0}


def test_index_und_detail(tmp_path):
    (tmp_path / "_papierkorb").mkdir()
    o1 = modell.video_ordner("Dold", "Recruiting", "Dold 10 Hobelwerk", tmp_path)
    modell.video_anlegen(o1, "Dold", "Recruiting", "Dold 10 Hobelwerk", "projects/Dold/Recruiting/2026-07 Dreh")
    modell.version_schreiben(o1, 1, {"nr": 1, "angelegt": "2026-09-18T10:00:00", "abgeschlossen": None, "geholt_am": None, "fps": 25.0})
    json_schreiben(o1 / "V1" / "kommentare.json", {"naechste_id": 2, "kommentare": [{"id": "K1", "status": "offen", "angelegt": "2026-09-18T10:05:00"}]})
    o2 = modell.video_ordner("Dold", "Recruiting", "Dold 02 Fokus", tmp_path)
    modell.video_anlegen(o2, "Dold", "Recruiting", "Dold 02 Fokus", "projects/Dold/Recruiting/2026-07 Dreh")
    modell.version_schreiben(o2, 1, {"nr": 1, "angelegt": "2026-09-18T10:00:00", "abgeschlossen": {"am": "x", "von": "Jan"}, "geholt_am": None})
    modell.version_schreiben(o2, 2, {"nr": 2, "angelegt": "2026-09-18T12:00:00", "abgeschlossen": None, "geholt_am": None})
    (tmp_path / "Dold" / "Recruiting" / "Müll").mkdir()  # ohne video.json → ignoriert
    index = modell.index_bauen(tmp_path)
    assert [k["name"] for k in index["kunden"]] == ["Dold"]
    projekt = index["kunden"][0]["projekte"][0]
    assert projekt["name"] == "Recruiting" and [v["titel"] for v in projekt["videos"]] == ["Dold 02 Fokus", "Dold 10 Hobelwerk"]
    v02, v10 = projekt["videos"]
    assert v02["neueste"] == 2 and v02["versionen"] == [1, 2] and v02["zustand"] == "review-offen"
    assert v10["offen"] == 1 and v10["neu"] == 1 and v10["vorschau"] == "/media/Dold/Recruiting/Dold%2010%20Hobelwerk/V1/thumb.jpg"
    assert projekt["offen"] == 1 and projekt["bei_claude"] == 0
    detail = modell.video_detail(o2)
    assert detail["video"]["titel"] == "Dold 02 Fokus" and [v["nr"] for v in detail["versionen"]] == [1, 2]
    assert detail["versionen"][0]["kommentare"] == [] and detail["zustand"] == "review-offen"
    assert modell.index_bauen(tmp_path / "gibtsnicht") == {"kunden": []}


def test_bewertung_pruefen_und_sterne():
    b = modell.bewertung_pruefen(3, "  ok ", "Jan")
    assert b["sterne"] == 3 and b["text"] == "ok" and b["von"] == "Jan" and b["am"]
    assert modell.bewertung_pruefen(0, "", "Jan") is None and modell.bewertung_pruefen(None, "", "Jan") is None
    with pytest.raises(ValueError):
        modell.bewertung_pruefen(6, "", "Jan")
    with pytest.raises(ValueError):
        modell.bewertung_pruefen("drei", "", "Jan")
    assert modell.sterne_text(b) == "★★★☆☆ (3/5)" and modell.sterne_text(None) == "—"
