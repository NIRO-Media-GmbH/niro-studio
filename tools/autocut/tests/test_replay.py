"""replay.py: Namen, Versionen, Replay-Ordner, Bitrate-Grenze, Upload-Log (Spec 2026-09-16)."""
from __future__ import annotations

import re
import unicodedata

import pytest
import yaml

from niro_autocut import replay as R
from niro_autocut.charge import DEFAULTS_FILE, TOOL_ROOT, AutoCutError, Charge


def test_titel_ohne_unsichere_zeichen():
    assert R.titel("AutoCut video-1 2026-09-15 1149 Feinschnitt") == "AutoCut video-1 2026-09-15 1149 Feinschnitt"
    assert R.titel("V1: Hook/Endcard?") == "V1- Hook-Endcard-"
    with pytest.raises(AutoCutError):
        R.titel("   ")


@pytest.mark.parametrize("alt, neu", [
    ("01_Dein_erster_Tag_bei_uns_V3", "01_Dein_erster_Tag_bei_uns_V4"),
    ("Reel_V9", "Reel_V10"),
    ("AutoCut video-1 2026-09-15 1149 Feinschnitt", "AutoCut video-1 2026-09-15 1149 Feinschnitt V2"),
    ("AutoCut video-1 2026-09-15 1149 Feinschnitt V2", "AutoCut video-1 2026-09-15 1149 Feinschnitt V3")])
def test_naechste_version(alt, neu):
    assert R.naechste_version(alt) == neu


def test_naechste_version_verweigert_roh_timelines():
    """F3: Roh-Timelines nie umbenennen — sonst findet readback.laden/autocut_finalize.py sie nach SetName nicht
    mehr (namensbasierte Buchführung bricht)."""
    with pytest.raises(AutoCutError, match="Roh-Timeline"):
        R.naechste_version("AutoCut video-1 2026-09-17 1000 (roh)")


def test_replay_ordner_aus_config(basis_charge):
    ch = Charge.open_basis(basis_charge)
    assert R.replay_ordner(ch) == "Autocut/Kunde A/Projekt B"
    ch.config["replay"]["ordner"] = ["Autocut", "{kunde} – {projekt}"]
    assert R.replay_ordner(ch) == "Autocut/Kunde A – Projekt B"


def test_video_quality_nur_ueber_1080p():
    cfg = {"video_quality_ueber_1080p": 12000}
    assert R.video_quality(1920, 1080, cfg) == 0
    assert R.video_quality(1080, 1920, cfg) == 0
    assert R.video_quality(3840, 2160, cfg) == 12000
    assert R.video_quality(None, None, cfg) == 0


def test_upload_log_speichern_lesen_einsortieren(basis_charge):
    ch = Charge.open_basis(basis_charge)
    assert R.lade_uploads(ch) == [] and R.nicht_einsortiert(ch) == []
    with pytest.raises(AutoCutError, match="Kein erfolgreicher Upload"):
        R.upload_eintrag(ch)
    R.speichere_upload(ch, {"titel": "A", "timeline": "A", "hochgeladen_am": "2026-09-17T10:00:00",
                            "upload_status": "Upload Completed"})
    R.speichere_upload(ch, {"titel": "B", "timeline": "B", "hochgeladen_am": "2026-09-17T11:00:00",
                            "upload_status": "Upload Completed"})
    assert R.upload_eintrag(ch)["titel"] == "B"
    assert R.upload_eintrag(ch, timeline="A")["titel"] == "A"
    assert [e["titel"] for e in R.nicht_einsortiert(ch)] == ["A", "B"]
    e = R.setze_einsortiert(ch, "A", "Autocut/Kunde A/Projekt B", zeit="2026-09-17T12:00:00")
    assert e["einsortiert_am"] == "2026-09-17T12:00:00" and e["replay_ordner"] == "Autocut/Kunde A/Projekt B"
    assert [x["titel"] for x in R.nicht_einsortiert(ch)] == ["B"]
    with pytest.raises(AutoCutError, match="Kein erfolgreicher Upload"):
        R.setze_einsortiert(ch, "C", "x")


def test_gescheiterte_uploads_werden_ignoriert(basis_charge):
    """F1-Regression: upload_eintrag/setze_einsortiert/finde_upload wählen nur erfolgreiche Uploads — ein späterer
    gescheiterter Versuch darf den erfolgreichen älteren nicht verdecken. ist_hochgeladen schützt weiterhin bei
    falsch geformtem JSON (keine Liste); lade_uploads meldet kaputtes JSON als AutoCutError mit Pfad."""
    ch = Charge.open_basis(basis_charge)
    R.speichere_upload(ch, {"titel": "A", "timeline": "A", "hochgeladen_am": "2026-09-17T10:00:00",
                            "upload_status": "Upload Completed"})
    R.speichere_upload(ch, {"titel": "A", "timeline": "A", "hochgeladen_am": "2026-09-17T11:00:00",
                            "upload_status": "Upload Failed"})
    assert R.upload_eintrag(ch)["hochgeladen_am"] == "2026-09-17T10:00:00"
    e = R.setze_einsortiert(ch, "A", "Autocut/Kunde A/Projekt B")
    assert e["hochgeladen_am"] == "2026-09-17T10:00:00"
    (basis_charge.parent / "2026-10 Zweiter Dreh").mkdir()
    charge, gefunden = R.finde_upload(basis_charge.parent, "A.mp4")
    assert charge == basis_charge and gefunden["hochgeladen_am"] == "2026-09-17T10:00:00"

    uploads_json = basis_charge / "_intern" / "replay" / "uploads.json"
    uploads_json.write_text("{}", encoding="utf-8")
    assert R.ist_hochgeladen(basis_charge, "irgendwas") is True      # gültiges JSON, aber keine Liste

    uploads_json.write_text("{kaputt", encoding="utf-8")
    with pytest.raises(AutoCutError, match=r"uploads\.json ist kaputt"):
        R.lade_uploads(Charge.open_basis(basis_charge))


def test_ist_hochgeladen(basis_charge):
    ch = Charge.open_basis(basis_charge)
    assert R.ist_hochgeladen(basis_charge, "A") is False
    R.speichere_upload(ch, {"titel": "A", "timeline": "A (roh)", "hochgeladen_am": "2026-09-17T10:00:00"})
    assert R.ist_hochgeladen(basis_charge, "A (roh)") is True and R.ist_hochgeladen(basis_charge, "B") is False
    (basis_charge / "_intern" / "replay" / "uploads.json").write_text("{kaputt", encoding="utf-8")
    assert R.ist_hochgeladen(basis_charge, "B") is True          # im Zweifel schützen


def test_finde_upload_ueber_chargen(basis_charge):
    zweite = basis_charge.parent / "2026-10 Zweiter Dreh"
    zweite.mkdir()
    R.speichere_upload(Charge.open_basis(basis_charge), {"titel": "X", "timeline": "X", "hochgeladen_am": "2026-09-17T10:00:00",
                                                          "upload_status": "Upload Completed"})
    R.speichere_upload(Charge.open_basis(zweite), {"titel": "X", "timeline": "X neu", "hochgeladen_am": "2026-10-01T10:00:00",
                                                    "upload_status": "Upload Completed"})
    charge, e = R.finde_upload(basis_charge.parent, "X.mp4")
    assert charge.name == "2026-10 Zweiter Dreh" and e["timeline"] == "X neu"
    assert R.finde_upload(basis_charge.parent, "Y.mp4") is None


def test_finde_upload_verlangt_projekt_ordner(basis_charge):
    """M1: Wird der Chargen-Ordner statt des Projekt-Ordners übergeben (enthält selbst _intern/replay/uploads.json),
    gibt es eine klare Meldung statt eines stillen „nicht gefunden"."""
    ch = Charge.open_basis(basis_charge)
    R.speichere_upload(ch, {"titel": "X", "timeline": "X", "hochgeladen_am": "2026-09-17T10:00:00",
                            "upload_status": "Upload Completed"})
    with pytest.raises(AutoCutError, match="Projekt-Ordner angeben"):
        R.finde_upload(basis_charge, "X.mp4")


def test_finde_upload_nfc_normalisiert(basis_charge):
    """M1: Der Titelvergleich ist NFC-normalisiert (Chrome kann eine andere Unicode-Normalform liefern)."""
    ch = Charge.open_basis(basis_charge)
    komponiert = "Café Video"
    zerlegt = unicodedata.normalize("NFD", komponiert)
    assert zerlegt != komponiert
    R.speichere_upload(ch, {"titel": zerlegt, "timeline": "X", "hochgeladen_am": "2026-09-17T10:00:00",
                            "upload_status": "Upload Completed"})
    charge, e = R.finde_upload(basis_charge.parent, komponiert + ".mp4")
    assert charge == basis_charge and e["timeline"] == "X"


@pytest.mark.parametrize("form_log, form_eingabe", [("NFD", "NFC"), ("NFC", "NFD")])
def test_upload_eintrag_und_einsortiert_nfc_normalisiert(basis_charge, form_log, form_eingabe):
    """Rest-Review Punkt 6: --titel wird von der Replay-Seite abgetippt — upload_eintrag(titel_=…) und
    setze_einsortiert vergleichen wie finde_upload NFC-normalisiert, egal welche Seite zerlegt vorliegt."""
    ch = Charge.open_basis(basis_charge)
    titel = "Café Übergabe"
    R.speichere_upload(ch, {"titel": unicodedata.normalize(form_log, titel), "timeline": "X",
                            "hochgeladen_am": "2026-09-17T10:00:00", "upload_status": "Upload Completed"})
    eingabe = unicodedata.normalize(form_eingabe, titel)
    assert R.upload_eintrag(ch, titel_=eingabe)["timeline"] == "X"
    R.setze_einsortiert(ch, eingabe, "Autocut/Kunde A/Projekt B", zeit="2026-09-17T12:00:00")
    assert R.lade_uploads(ch)[0]["einsortiert_am"] == "2026-09-17T12:00:00"


def test_finde_upload_kaputtes_json_einer_charge(basis_charge):
    """M1: Ein kaputtes uploads.json einer Charge → AutoCutError mit Pfad statt rohem JSONDecodeError."""
    zweite = basis_charge.parent / "2026-10 Zweiter Dreh"
    (zweite / "_intern" / "replay").mkdir(parents=True)
    kaputt = zweite / "_intern" / "replay" / "uploads.json"
    kaputt.write_text("{kaputt", encoding="utf-8")
    with pytest.raises(AutoCutError, match=re.escape(str(kaputt))):
        R.finde_upload(basis_charge.parent, "X.mp4")


def test_feedback_ordner(basis_charge):
    ch = Charge.open_basis(basis_charge)
    p = R.feedback_ordner(ch, {"titel": "X", "hochgeladen_am": "2026-09-17T10:00:00"})
    assert p == ch.root / "Material" / "Feedback" / "2026-09-17 Replay X"


def test_defaults_haben_replay_block():
    cfg = yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["replay"]
    assert cfg["quickexport_preset"] == "Replay" and cfg["dropbox_marker"] == {"color": "FrameIO"}
    assert cfg["ordner"] == ["Autocut", "{kunde}", "{projekt}"] and cfg["geprueft_am"]
    assert cfg["frameio_marker_beim_upload"] in ("sperren", "erlauben") and cfg["version_weg"] in ("neubau", "kopie")


def test_kein_code_loescht_marker():
    """Spec 2.6: Replay-Marker nie löschen — kein Skript, kein Modul, keine Vorlage ruft Marker-Löschfunktionen auf."""
    muster = re.compile(r"DeleteMarkersByColor|DeleteMarkerAtFrame|DeleteMarkerByCustomData")
    treffer = [str(p) for ordner in ("scripts", "src", "vorlagen") for p in (TOOL_ROOT / ordner).rglob("*.py")
               if muster.search(p.read_text(encoding="utf-8"))]
    assert treffer == []
