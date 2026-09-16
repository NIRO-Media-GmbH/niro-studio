"""autocut_replay.py gegen das Fake-Resolve: Vorschau, Vorbedingungen, Upload, Wiederherstellung (Task 7);
einsortiert, kommentare, finden (Task 8)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from fake_resolve import FakeItem, FakeProject, FakeResolve
from niro_autocut import replay as R
from niro_autocut import resolve_api as RA
from niro_autocut import wiedergabe as W
from niro_autocut.charge import Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
NAME = "AutoCut video-1 2026-09-17 1000"
PROJEKT = "Kunde Test"
RUHIG = "1\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920x1080\tKunde Test\n"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


replay = _load("autocut_replay")


@pytest.fixture
def welt(basis_charge, monkeypatch):
    fr = FakeResolve(FakeProject(PROJEKT))
    t = fr.p.mp.CreateEmptyTimeline(NAME)
    item = FakeItem("/nas/FX3_1.MP4")
    fr.p.mp.SetSelectedClip(item)
    fr.p.mp.AppendToTimeline([{"mediaPoolItem": item, "startFrame": 0, "endFrame": 99, "recordFrame": 90000,
                               "trackIndex": 1, "mediaType": 1}])
    t.AddMarker(10, "Blue", "#1 Hook", "", 1)
    user = fr.p.mp.CreateEmptyTimeline("User-Timeline")          # beim Start aktiv
    user_bin = fr.p.mp.AddSubFolder(fr.p.mp.root, "User-Bin")
    fr.p.mp.SetCurrentFolder(user_bin)
    monkeypatch.setattr(RA, "connect", lambda: fr)
    monkeypatch.setattr(W, "fenster_ausgabe", lambda timeout_s=90: RUHIG)
    monkeypatch.setattr(replay.time, "sleep", lambda s: None)
    return {"charge": basis_charge, "fake": fr, "tl": t, "user": user, "user_bin": user_bin}


def _hochladen(w, *extra):
    return replay.main([str(w["charge"]), "hochladen", "--project", PROJEKT, "--timeline", NAME, *extra])


def test_vorschau_laedt_nichts_hoch(welt, capsys):
    assert _hochladen(welt) == 0
    out = capsys.readouterr().out
    assert "Replay-Titel: AutoCut video-1 2026-09-17 1000.mp4" in out
    assert "Replay-Ordner: Autocut/Kunde A/Projekt B" in out and "Bitrate-Grenze 12000 kbit/s" in out
    assert "nichts hochgeladen" in out
    assert welt["fake"].p.quick_settings == [] and R.lade_uploads(Charge.open_basis(welt["charge"])) == []


@pytest.mark.parametrize("aufbau, meldung", [
    (lambda w: None, "freigegeben wurde 'Falsch'"),
    (lambda w: setattr(w["tl"], "mark_in_out", {"video": {"in": 0, "out": 50}}), "In/Out-Marken"),
    (lambda w: w["tl"].AddMarker(20, "FrameIO", "Marker 1", "alt", 1), "Replay-Marker"),
])
def test_vorbedingungen_exit_2(welt, capsys, aufbau, meldung):
    aufbau(welt)
    projekt = "Falsch" if "Falsch" in meldung else PROJEKT
    rc = replay.main([str(welt["charge"]), "hochladen", "--project", projekt, "--timeline", NAME, "--hochladen"])
    assert rc == 2 and meldung in capsys.readouterr().err
    assert welt["fake"].p.quick_settings == []


def test_timeline_fehlt_und_wiedergabe_exit_2(welt, monkeypatch, capsys):
    assert replay.main([str(welt["charge"]), "hochladen", "--project", PROJEKT, "--timeline", "fehlt"]) == 2
    assert "nicht im offenen Projekt" in capsys.readouterr().err
    monkeypatch.setattr(W, "fenster_ausgabe",
                        lambda timeout_s=90: RUHIG + "2\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920x1080\t\n")
    assert _hochladen(welt, "--hochladen") == 2
    assert "Vollbild-Wiedergabe" in capsys.readouterr().err and welt["fake"].p.quick_settings == []


def test_ohne_live_test_kein_upload(welt, capsys):
    cfg = welt["charge"] / "_intern" / "autocut" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("replay:\n  geprueft_am: null\n", encoding="utf-8")
    assert _hochladen(welt, "--hochladen") == 2
    assert "Live-Test fehlt" in capsys.readouterr().err and welt["fake"].p.quick_settings == []


def test_upload_ok(welt, capsys):
    fr = welt["fake"]
    assert _hochladen(welt, "--hochladen") == 0, capsys.readouterr()
    s = fr.p.quick_settings[-1]
    assert s["CustomName"] == NAME and s["EnableUpload"] is True and s["VideoQuality"] == 12000
    ch = Charge.open_basis(welt["charge"])
    e = R.upload_eintrag(ch)
    assert e["upload_status"] == "Upload Completed" and e["timeline"] == NAME and e["einsortiert_am"] is None
    assert e["replay_ordner"] == "Autocut/Kunde A/Projekt B" and e["datei"].endswith(f"{NAME}.mp4")
    snap = json.loads(Path(e["schnappschuss"]).read_text(encoding="utf-8"))
    assert snap["laenge"] == 100 and snap["marker"]["10"]["name"] == "#1 Hook"
    assert fr.p.current is welt["user"] and fr.p.mp.GetCurrentFolder() is welt["user_bin"] and fr.page == "edit"
    assert "Replay-Upload" in ch.protokoll.read_text(encoding="utf-8")


def test_upload_fehlgeschlagen_exit_1(welt, capsys):
    welt["fake"].p.upload_status = "Upload Failed"
    assert _hochladen(welt, "--hochladen") == 1
    assert "Internet-Konten" in capsys.readouterr().err
    assert R.upload_eintrag(Charge.open_basis(welt["charge"]))["upload_status"] == "Upload Failed"


def test_wiederherstellung_nach_ausnahme(welt, monkeypatch):
    fr = welt["fake"]

    def kaputt(preset, settings=None):
        fr.page = "deliver"
        fr.p.mp.SetCurrentFolder(fr.p.mp.root)
        raise RuntimeError("Resolve weg")

    monkeypatch.setattr(fr.p, "RenderWithQuickExport", kaputt)
    with pytest.raises(RuntimeError):
        _hochladen(welt, "--hochladen")
    assert fr.p.current is welt["user"] and fr.p.mp.GetCurrentFolder() is welt["user_bin"] and fr.page == "edit"


def test_wiederherstellung_trotz_openpage_fehler(welt, monkeypatch):
    """Wirft OpenPage beim Wiederherstellen selbst (reales Resolve kann das), darf das weder den ursprünglichen
    Fehler aus RenderWithQuickExport verdecken noch die Wiederherstellung von Timeline und Bin verhindern."""
    fr = welt["fake"]

    def kaputt(preset, settings=None):
        fr.page = "deliver"
        fr.p.mp.SetCurrentFolder(fr.p.mp.root)
        raise RuntimeError("Resolve weg")

    def openpage_kaputt(page):
        raise RuntimeError("OpenPage kaputt")

    monkeypatch.setattr(fr.p, "RenderWithQuickExport", kaputt)
    monkeypatch.setattr(fr, "OpenPage", openpage_kaputt)
    with pytest.raises(RuntimeError, match="Resolve weg"):
        _hochladen(welt, "--hochladen")
    assert fr.p.current is welt["user"] and fr.p.mp.GetCurrentFolder() is welt["user_bin"]


def _hochgeladen(w, capsys):
    assert _hochladen(w, "--hochladen") == 0
    capsys.readouterr()


def test_einsortiert_und_finden(welt, capsys):
    _hochgeladen(welt, capsys)
    assert replay.main([str(welt["charge"]), "einsortiert", "--titel", NAME]) == 0
    e = R.upload_eintrag(Charge.open_basis(welt["charge"]))
    assert e["einsortiert_am"] and e["replay_ordner"] == "Autocut/Kunde A/Projekt B"
    capsys.readouterr()
    assert replay.main([str(welt["charge"].parent), "finden", "--titel", f"{NAME}.mp4"]) == 0
    gefunden = json.loads(capsys.readouterr().out)
    assert gefunden["timeline"] == NAME and gefunden["charge"].endswith("2026-09 Dreh")
    assert replay.main([str(welt["charge"].parent), "finden", "--titel", "Fremdes Video.mp4"]) == 1
    assert replay.main([str(welt["charge"]), "einsortiert", "--titel", "gibt es nicht"]) == 2


def test_kommentare_api_neu_dann_bekannt(welt, capsys):
    _hochgeladen(welt, capsys)
    assert replay.main([str(welt["charge"]), "kommentare", "--warten", "0"]) == 1          # noch keine
    capsys.readouterr()
    welt["tl"].AddMarker(48, "FrameIO", "Marker 1", "Test 1: Schnitt früher", 1)
    assert replay.main([str(welt["charge"]), "kommentare", "--warten", "0"]) == 0
    ordner = next((welt["charge"] / "Material" / "Feedback").iterdir())
    assert ordner.name.endswith(f"Replay {NAME}")
    doc = json.loads((ordner / "kommentare.json").read_text(encoding="utf-8"))
    k = doc["kommentare"][0]
    assert (doc["anzahl"], doc["neu"], doc["lese_weg"], doc["veraendert_seit_upload"]) == (1, 1, "api", False)
    assert (k["frame"], k["tc"], k["text"], k["clips"][0]["quell_frame"]) == (48, "01:00:01:23", "Test 1: Schnitt früher", 48)
    assert doc["seit_bau_veraendert"] is None                                              # kein Bau-Readback
    assert "| 1 | ja | 01:00:01:23 |" in (ordner / "kommentare.md").read_text(encoding="utf-8")
    assert replay.main([str(welt["charge"]), "kommentare", "--warten", "0"]) == 1          # nichts Neues
    assert "Replay-Kommentare" in Charge.open_basis(welt["charge"]).protokoll.read_text(encoding="utf-8")


def test_kommentare_nach_handaenderung(welt, capsys):
    _hochgeladen(welt, capsys)
    welt["tl"].tl_items[0].start += 10
    welt["tl"].AddMarker(48, "FrameIO", "Marker 1", "Test", 1)
    assert replay.main([str(welt["charge"]), "kommentare", "--warten", "0"]) == 0
    ordner = next((welt["charge"] / "Material" / "Feedback").iterdir())
    doc = json.loads((ordner / "kommentare.json").read_text(encoding="utf-8"))
    assert doc["veraendert_seit_upload"] is True and doc["kommentare"][0]["frame_aktuell"] == 58


def test_kommentare_aus_chrome_json_ohne_resolve(welt, monkeypatch, capsys, tmp_path):
    _hochgeladen(welt, capsys)

    def kein_resolve():
        raise AssertionError("Resolve darf beim Chrome-Weg nicht verbunden werden")

    monkeypatch.setattr(RA, "connect", kein_resolve)
    datei = tmp_path / "chrome.json"
    datei.write_text(json.dumps({"quelle": "chrome", "kommentare": [
        {"von_s": 2.008, "text": "Kunde will anderen Take", "autor": "Kunde X", "zeichnung": True}]}), encoding="utf-8")
    assert replay.main([str(welt["charge"]), "kommentare", "--aus-json", str(datei)]) == 0
    ordner = next((welt["charge"] / "Material" / "Feedback").iterdir())
    doc = json.loads((ordner / "kommentare.json").read_text(encoding="utf-8"))
    k = doc["kommentare"][0]
    assert (doc["lese_weg"], doc["fremd"], k["frame"], k["fremd"], k["zeichnung"]) == ("chrome", 1, 50, True, True)
    assert doc["veraendert_seit_upload"] is None
