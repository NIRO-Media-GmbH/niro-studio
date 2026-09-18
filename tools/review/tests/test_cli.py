from __future__ import annotations

import json
import shutil

import pytest

from niro_review import cli
from niro_review import kommentare as km
from niro_review import modell
from niro_review.ablage import json_lesen, json_schreiben

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg fehlt")


def lauf(*argv):
    return cli.main([str(a) for a in argv])


def test_link():
    assert cli.link("Dold", "Recruiting") == "http://localhost:4711/#/Dold/Recruiting"
    assert cli.link("Dold", "Recruiting", "Dold 02 Fokus", 4800) == "http://localhost:4800/#/Dold/Recruiting/Dold%2002%20Fokus"


def test_hinzufuegen_fehler_ohne_nas(wurzeln, monkeypatch, tmp_path, testvideo_h264):
    monkeypatch.setenv("NIRO_REVIEW_ROOT", str(tmp_path / "weg" / "review"))
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264) == 2


@ffmpeg
def test_hinzufuegen_kopie_und_folgeversion(wurzeln, testvideo_h264, capsys):
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--notiz", "Entwurf v1") == 0
    out = capsys.readouterr().out
    assert "Dold 02 Fokus Bagger und Kran V1" in out and "http://localhost:4711/#/Dold/Recruiting/Dold%2002%20Fokus%20Bagger%20und%20Kran" in out
    ordner = wurzeln["review"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran"
    video = json_lesen(ordner / "video.json")
    assert video["charge"] == wurzeln["charge_rel"] and video["sortierung"] == "02"
    v1 = json_lesen(ordner / "V1" / "version.json")
    assert v1["nr"] == 1 and v1["umkodiert"] is False and v1["frames"] == 50 and v1["fps"] == 25.0 and v1["notiz"] == "Entwurf v1"
    assert v1["basis"] is None and v1["abgeschlossen"] is None and v1["geholt_am"] is None and v1["quelle"]
    assert (ordner / "V1" / "video.mp4").stat().st_size == testvideo_h264.stat().st_size
    assert (ordner / "V1" / "thumb.jpg").stat().st_size > 1000
    assert json_lesen(ordner / "V1" / "kommentare.json") == {"naechste_id": 1, "kommentare": []}
    assert (wurzeln["cache"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran" / "V1" / "video.mp4").is_file()
    # zweite Version: nächste Nummer, gleicher Titel über --video
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran") == 0
    assert modell.versionsnummern(ordner) == [1, 2] and json_lesen(ordner / "V2" / "version.json")["basis"] == 1
    # belegte Nummer
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1") == 1
    assert "nächste freie: V3" in capsys.readouterr().err
    # fehlende Datei
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", "/gibt/es/nicht.mp4") == 1


@ffmpeg
def test_hinzufuegen_umkodieren_und_stapel(wurzeln, testvideo_mpeg4, testvideo_h264, tmp_path):
    ordner = tmp_path / "exporte"
    ordner.mkdir()
    shutil.copy2(testvideo_mpeg4, ordner / "Taxodia-Weg Messe V2.mov")
    shutil.copy2(testvideo_h264, ordner / "Taxodia-Weg Kurz V1.mp4")
    (ordner / "_render_log.json").write_text("{}", encoding="utf-8")
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--ordner", ordner, "--muster", "*.m*", "--version", "1") == 0
    projekt = wurzeln["review"] / "Dold" / "Recruiting"
    assert sorted(p.name for p in projekt.iterdir()) == ["Taxodia-Weg Kurz", "Taxodia-Weg Messe"]
    v = json_lesen(projekt / "Taxodia-Weg Messe" / "V1" / "version.json")
    assert v["umkodiert"] is True and v["encoder"] in ("h264_videotoolbox", "libx264") and v["frames"] in (49, 50, 51)
    assert json_lesen(projekt / "Taxodia-Weg Kurz" / "V1" / "version.json")["umkodiert"] is False


@ffmpeg
def test_kommentare_umsetzung_status_entfernen(wurzeln, testvideo_h264, capsys):
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264) == 0
    ordner = wurzeln["review"] / "Dold" / "Recruiting" / "Dold 02 Fokus Bagger und Kran"
    # keine Kommentare → Exit 1, kein Export
    assert lauf("kommentare", wurzeln["charge_rel"]) == 1
    assert not (wurzeln["charge"] / "Material").exists()
    # Kommentare wie aus der Oberfläche
    daten = km.laden(ordner / "V1")
    km.anlegen(daten, "Jan", "Schmatzer raus", frame=25)
    km.anlegen(daten, "Jan", "Insgesamt zu hektisch")
    km.speichern(ordner / "V1", daten)
    v = modell.version_lesen(ordner, 1)
    v["abgeschlossen"] = {"am": "2026-09-18T14:41:00", "von": "Jan"}
    modell.version_schreiben(ordner, 1, v)
    assert lauf("kommentare", "Dold/Recruiting") == 0
    out = capsys.readouterr().out
    assert "2 neu" in out and "K1" in out and "00:00:01:00" in out and "abgeschlossen" in out
    feedback = list((wurzeln["charge"] / "Material" / "Feedback").iterdir())
    assert len(feedback) == 1 and feedback[0].name.endswith("Review Dold 02 Fokus Bagger und Kran V1")
    md = (feedback[0] / "kommentare.md").read_text(encoding="utf-8")
    assert "| K1 | 00:00:01:00 |" in md and "Insgesamt zu hektisch" in md
    js = json_lesen(feedback[0] / "kommentare.json")
    assert js["version"] == 1 and len(js["kommentare"]) == 2 and js["charge"] == wurzeln["charge_rel"]
    assert modell.version_lesen(ordner, 1)["geholt_am"]
    # nichts Neues mehr → 1; --alle → 0 und Export erneut
    assert lauf("kommentare", wurzeln["charge_rel"]) == 1
    assert lauf("kommentare", wurzeln["charge_rel"], "--alle") == 0
    # Umsetzung mit neuer Version
    umsetzung = wurzeln["repo"] / "umsetzung.json"
    json_schreiben(umsetzung, {"K1": {"status": "umgesetzt", "antwort": "Schmatzer weg", "tc_neu": "00:00:00:20"},
                               "K2": {"status": "rueckfrage", "antwort": "Welche Stellen genau?"}})
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran",
                "--umsetzung", umsetzung, "--notiz", "v2") == 0
    k = {x["id"]: x for x in km.laden(ordner / "V1")["kommentare"]}
    assert k["K1"]["status"] == "umgesetzt" and k["K1"]["frame_neu"] == 20 and k["K2"]["status"] == "rueckfrage"
    assert modell.version_lesen(ordner, 2)["basis"] == 1
    # unbekannte ID → Exit 1, keine Version angelegt
    json_schreiben(umsetzung, {"K9": {"status": "umgesetzt"}})
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", testvideo_h264, "--video", "Dold 02 Fokus Bagger und Kran", "--umsetzung", umsetzung) == 1
    assert modell.versionsnummern(ordner) == [1, 2]
    # umsetzung / antworten als eigene Befehle
    json_schreiben(umsetzung, {"K2": {"status": "umgesetzt", "antwort": "jetzt klar"}})
    assert lauf("umsetzung", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1", "--datei", umsetzung) == 0
    assert lauf("antworten", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "1", "--kommentar", "K2", "--text", "Danke") == 0
    k2 = km.finden(km.laden(ordner / "V1"), "K2")
    assert k2["status"] == "umgesetzt" and k2["antworten"][-1] == {**k2["antworten"][-1], "autor": "Claude", "text": "Danke"}
    # status
    assert lauf("status", "Dold/Recruiting") == 0
    out = capsys.readouterr().out
    assert "Dold 02 Fokus Bagger und Kran" in out and "V2" in out and "review-offen" in out
    # entfernen → Papierkorb
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran", "--version", "2") == 0
    assert modell.versionsnummern(ordner) == [1]
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Dold 02 Fokus Bagger und Kran") == 0
    assert not ordner.exists()
    korb = list((wurzeln["review"] / "_papierkorb").iterdir())
    assert len(korb) == 2
    assert lauf("entfernen", wurzeln["charge_rel"], "--video", "Gibt es nicht") == 1


def test_hinzufuegen_alpha_abgelehnt(wurzeln, tmp_path, monkeypatch):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg fehlt")
    import subprocess
    alpha = tmp_path / "overlay.mov"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=25:duration=1",
                    "-vf", "format=yuva444p10le", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(alpha)], check=True)
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", alpha) == 1
    assert lauf("hinzufuegen", wurzeln["charge_rel"], "--datei", alpha, "--trotzdem") == 0
