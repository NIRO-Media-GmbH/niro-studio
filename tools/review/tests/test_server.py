from __future__ import annotations

import http.client
import json
import threading
import time

import pytest

from niro_review import kommentare as km
from niro_review import modell
from niro_review.server import ReviewServer


@pytest.fixture
def ui(tmp_path):
    ui = tmp_path / "ui"
    ui.mkdir()
    (ui / "index.html").write_text("<!doctype html><title>NIRO Review</title>", encoding="utf-8")
    (ui / "app.js").write_text("console.log('x')", encoding="utf-8")
    (tmp_path / "geheim.txt").write_text("nein", encoding="utf-8")
    return ui


def _starten(wurzel, cache, ui):
    srv = ReviewServer(("127.0.0.1", 0), wurzel, cache, ui=ui, index_ttl=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


@pytest.fixture
def srv(wurzeln, ui):
    s = _starten(wurzeln["review"], wurzeln["cache"], ui)
    yield s
    s.shutdown()
    s.server_close()


def anfrage(srv, methode, pfad, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
    h = dict(headers or {})
    daten = None
    if body is not None:
        daten = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    c.request(methode, pfad, body=daten, headers=h)
    r = c.getresponse()
    inhalt = r.read()
    c.close()
    return r.status, {k.lower(): v for k, v in r.getheaders()}, inhalt


def js(srv, methode, pfad, body=None):
    status, _, inhalt = anfrage(srv, methode, pfad, body)
    return status, json.loads(inhalt.decode("utf-8") or "{}")


def video_anlegen(wurzeln, titel="Dold 02 Fokus", nr=1):
    ordner = modell.video_ordner("Dold", "Recruiting", titel, wurzeln["review"])
    if not modell.video_lesen(ordner):
        modell.video_anlegen(ordner, "Dold", "Recruiting", titel, wurzeln["charge_rel"])
    vo = modell.version_ordner(ordner, nr)
    vo.mkdir(parents=True, exist_ok=True)
    (vo / "video.mp4").write_bytes(b"0123456789" * 1000)
    (vo / "thumb.jpg").write_bytes(b"\xff\xd8bild")
    km.speichern(vo, {"naechste_id": 1, "kommentare": []})
    modell.version_schreiben(ordner, nr, {"nr": nr, "angelegt": "2026-09-18T10:00:00", "von": "Studio-Mac", "fps": 25.0,
                                          "frames": 50, "dauer_s": 2.0, "breite": 320, "hoehe": 180, "notiz": "",
                                          "basis": nr - 1 if nr > 1 else None, "abgeschlossen": None, "geholt_am": None})
    return ordner


def test_zustand_und_ui(srv, wurzeln):
    status, daten = js(srv, "GET", "/api/zustand")
    assert status == 200 and daten["nas_verbunden"] is True and daten["wurzel"] == str(wurzeln["review"])
    status, h, inhalt = anfrage(srv, "GET", "/")
    assert status == 200 and h["content-type"].startswith("text/html") and b"NIRO Review" in inhalt
    assert anfrage(srv, "GET", "/ui/app.js")[0] == 200
    assert anfrage(srv, "GET", "/ui/../geheim.txt")[0] == 404
    assert anfrage(srv, "GET", "/ui/fehlt.js")[0] == 404
    assert anfrage(srv, "GET", "/nix")[0] == 404


def test_index_und_video(srv, wurzeln):
    assert js(srv, "GET", "/api/index") == (200, {"kunden": []})
    video_anlegen(wurzeln)
    status, daten = js(srv, "GET", "/api/index?frisch=1")
    assert status == 200 and daten["kunden"][0]["projekte"][0]["videos"][0]["titel"] == "Dold 02 Fokus"
    status, daten = js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")
    assert status == 200 and daten["versionen"][0]["nr"] == 1 and daten["zustand"] == "review-offen"
    assert daten["versionen"][0]["video_url"] == "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/video.mp4"
    assert js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Fehlt")[0] == 404
    assert js(srv, "GET", "/api/video?kunde=..&projekt=Recruiting&video=x")[0] == 404


def test_kommentar_roundtrip(srv, wurzeln):
    ordner = video_anlegen(wurzeln)
    basis = {"kunde": "Dold", "projekt": "Recruiting", "video": "Dold 02 Fokus", "version": 1}
    status, k = js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "Schmatzer raus", "frame": 50})
    assert status == 200 and k["id"] == "K1" and k["frame"] == 50 and k["status"] == "offen"
    status, k2 = js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "Bereich", "frame": 10, "bis_frame": 30})
    assert status == 200 and k2["bis_frame"] == 30
    assert js(srv, "POST", "/api/kommentar", {**basis, "autor": "Jan", "text": "  "})[0] == 400
    assert js(srv, "POST", "/api/kommentar", {**basis, "version": 7, "autor": "Jan", "text": "x"})[0] == 404
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K1", "autor": "David", "text": "fremd"})
    assert status == 400
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K1", "autor": "David", "status": "erledigt"})
    assert status == 200 and daten["status"] == "erledigt"
    status, daten = js(srv, "POST", "/api/antwort", {**basis, "id": "K1", "autor": "Jan", "text": "doch offen"})
    assert status == 200 and daten["autor"] == "Jan"
    status, daten = js(srv, "POST", "/api/kommentar/aendern", {**basis, "id": "K2", "autor": "Jan", "loeschen": True})
    assert status == 200 and daten["geloescht"] == "K2"
    gespeichert = km.laden(modell.version_ordner(ordner, 1))
    assert [k["id"] for k in gespeichert["kommentare"]] == ["K1"] and gespeichert["kommentare"][0]["antworten"][0]["text"] == "doch offen"
    status, daten = js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")
    assert daten["versionen"][0]["kommentare"][0]["status"] == "erledigt"


def test_abschliessen_und_freigeben(srv, wurzeln):
    ordner = video_anlegen(wurzeln)
    basis = {"kunde": "Dold", "projekt": "Recruiting", "video": "Dold 02 Fokus", "version": 1, "autor": "Jan"}
    status, daten = js(srv, "POST", "/api/version/abschliessen", basis)
    assert status == 200 and daten["abgeschlossen"]["von"] == "Jan"
    status, daten = js(srv, "POST", "/api/kommentar", {**basis, "text": "zu spät", "frame": 1})
    assert status == 409 and "abgeschlossen" in daten["fehler"]
    assert js(srv, "GET", "/api/index")[1]["kunden"][0]["projekte"][0]["videos"][0]["zustand"] == "bei-claude"
    assert js(srv, "POST", "/api/version/wieder_oeffnen", basis)[1]["abgeschlossen"] is None
    assert js(srv, "POST", "/api/kommentar", {**basis, "text": "geht wieder", "frame": 1})[0] == 200
    status, daten = js(srv, "POST", "/api/video/freigeben", basis)
    assert status == 200 and daten["freigegeben"]["von"] == "Jan" and modell.video_lesen(ordner)["freigegeben"]["von"] == "Jan"
    assert js(srv, "GET", "/api/video?kunde=Dold&projekt=Recruiting&video=Dold%2002%20Fokus")[1]["zustand"] == "freigegeben"
    assert js(srv, "POST", "/api/video/freigabe_zuruecknehmen", basis)[1]["freigegeben"] is None
    assert js(srv, "POST", "/api/unbekannt", basis)[0] == 404


def test_media_range_und_cache(srv, wurzeln):
    video_anlegen(wurzeln)
    pfad = "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/video.mp4"
    status, h, inhalt = anfrage(srv, "GET", pfad)
    assert status == 200 and len(inhalt) == 10000 and h["accept-ranges"] == "bytes" and h["content-type"] == "video/mp4"
    assert h["x-quelle"] == "nas"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=0-99"})
    assert status == 206 and len(inhalt) == 100 and h["content-range"] == "bytes 0-99/10000" and h["content-length"] == "100"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=9990-"})
    assert status == 206 and inhalt == b"0123456789" and h["content-range"] == "bytes 9990-9999/10000"
    status, h, inhalt = anfrage(srv, "GET", pfad, headers={"Range": "bytes=-10"})
    assert status == 206 and inhalt == b"0123456789"
    status, h, _ = anfrage(srv, "GET", pfad, headers={"Range": "bytes=20000-"})
    assert status == 416 and h["content-range"] == "bytes */10000"
    status, h, inhalt = anfrage(srv, "HEAD", pfad)
    assert status == 200 and inhalt == b"" and h["content-length"] == "10000"
    cache_datei = wurzeln["cache"] / "Dold" / "Recruiting" / "Dold 02 Fokus" / "V1" / "video.mp4"
    for _ in range(50):
        if cache_datei.is_file() and cache_datei.stat().st_size == 10000:
            break
        time.sleep(0.05)
    assert cache_datei.is_file() and cache_datei.stat().st_size == 10000
    status, h, _ = anfrage(srv, "GET", pfad, headers={"Range": "bytes=0-9"})
    assert status == 206 and h["x-quelle"] == "cache"
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/thumb.jpg")[1]["content-type"] == "image/jpeg"
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Dold%2002%20Fokus/V1/version.json")[0] == 404
    assert anfrage(srv, "GET", "/media/../geheim.txt")[0] == 404
    assert anfrage(srv, "GET", "/media/Dold/Recruiting/Fehlt/V1/video.mp4")[0] == 404


def test_ohne_nas_503(tmp_path, ui):
    s = _starten(tmp_path / "weg" / "review", tmp_path / "cache", ui)
    try:
        status, daten = js(s, "GET", "/api/index")
        assert status == 503 and "NAS" in daten["fehler"]
        assert js(s, "GET", "/api/zustand")[1]["nas_verbunden"] is False
        assert js(s, "POST", "/api/kommentar", {"kunde": "a", "projekt": "b", "video": "c", "version": 1, "autor": "x", "text": "y"})[0] == 503
        assert anfrage(s, "GET", "/")[0] == 200
    finally:
        s.shutdown()
        s.server_close()
