"""replay.py: Namen, Versionen, Replay-Ordner, Bitrate-Grenze, Upload-Log (Spec 2026-09-16)."""
from __future__ import annotations

import re

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
    with pytest.raises(AutoCutError, match="Kein Upload"):
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
    with pytest.raises(AutoCutError, match="steht nicht"):
        R.setze_einsortiert(ch, "C", "x")


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
    R.speichere_upload(Charge.open_basis(basis_charge), {"titel": "X", "timeline": "X", "hochgeladen_am": "2026-09-17T10:00:00"})
    R.speichere_upload(Charge.open_basis(zweite), {"titel": "X", "timeline": "X neu", "hochgeladen_am": "2026-10-01T10:00:00"})
    charge, e = R.finde_upload(basis_charge.parent, "X.mp4")
    assert charge.name == "2026-10 Zweiter Dreh" and e["timeline"] == "X neu"
    assert R.finde_upload(basis_charge.parent, "Y.mp4") is None


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
