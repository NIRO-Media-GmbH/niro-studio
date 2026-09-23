"""gyroflow.py — Preset aus der Telemetrie, Deckel-Prüfung, Sidecar-Pfad, Clip-Export, Charge-Lauf (Spec 2026-09-22)."""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from niro_autocut import gyroflow as G
from niro_autocut.charge import AutoCutError, load_config

CFG = {
    "gyroflow": {
        "cli": "/Applications/Gyroflow.app/Contents/MacOS/gyroflow",
        "zeitueberschreitung_s": 300,
        "glaettung": {"stativ": 0.2, "gimbal": 0.4, "hand": 0.7},
        "max_zoom": {"stativ": 105, "gimbal": 110, "hand": 120},
    },
    "telemetrie": {"digitalzoom_faktor": 1.25, "digitalzoom_max": 1.5},
}


def test_deckel_haelt_die_ungleichung_ein():
    G.pruefe_deckel(CFG)   # 120 ≤ 1.5 / 1.25 × 100 = 120 — Gleichheit ist erlaubt


def test_echte_defaults_halten_den_deckel_ein():
    """Stolperdraht auf die echten Zahlen: die CFG-Attrappe oben muss von Hand nachgezogen werden, defaults.yaml
    nicht. Vorbild: tests/test_telemetrie.py::test_defaults_haben_brennweitenregel. Wer max_zoom oder
    telemetrie.digitalzoom_* ändert, soll es hier merken und nicht erst am ersten echten Chargenlauf."""
    cfg = load_config(Path("/nirgendwo"))
    assert cfg["gyroflow"]["max_zoom"] == {"stativ": 105, "gimbal": 110, "hand": 120}
    assert cfg["gyroflow"]["glaettung"] == {"stativ": 0.2, "gimbal": 0.4, "hand": 0.7}
    assert cfg["telemetrie"]["digitalzoom_faktor"] == 1.25 and cfg["telemetrie"]["digitalzoom_max"] == 1.5
    G.pruefe_deckel(cfg)
    # Jede Haltung in glaettung braucht ein max_zoom und umgekehrt — sonst wirft preset_fuer beim ersten Clip.
    assert set(cfg["gyroflow"]["glaettung"]) == set(cfg["gyroflow"]["max_zoom"])


def test_deckel_zu_hoch_bricht_ab():
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["max_zoom"]["hand"] = 130
    with pytest.raises(AutoCutError, match="max_zoom"):
        G.pruefe_deckel(cfg)


def test_preset_nimmt_glaettung_und_deckel_der_haltung():
    p = G.preset_fuer({"haltung": "hand"}, CFG)
    assert p["version"] == 2
    st = p["stabilization"]
    assert st["max_zoom"] == 120
    assert {"name": "smoothness", "value": 0.7} in st["smoothing_params"]


def test_preset_ohne_haltung_nimmt_die_vorsichtigste_stufe():
    p = G.preset_fuer({"haltung": None}, CFG)
    assert p["stabilization"]["max_zoom"] == 105
    assert {"name": "smoothness", "value": 0.2} in p["stabilization"]["smoothing_params"]


def test_preset_hash_haengt_am_inhalt_nicht_an_der_reihenfolge():
    a = G.preset_fuer({"haltung": "gimbal"}, CFG)
    b = json.loads(json.dumps(a))
    assert G.preset_hash(a) == G.preset_hash(b)
    assert len(G.preset_hash(a)) == 12
    assert G.preset_hash(a) != G.preset_hash(G.preset_fuer({"haltung": "hand"}, CFG))


def test_sidecar_liegt_neben_der_mediendatei(tmp_path: Path):
    v = tmp_path / "FX3_0001.MP4"
    v.write_bytes(b"x")
    p = G.sidecar_pfad(v, {str(v)})
    assert p == tmp_path / "FX3_0001.gyroflow"


def test_sidecar_verweigert_unbekannte_datei(tmp_path: Path):
    v = tmp_path / "FX3_0001.MP4"
    v.write_bytes(b"x")
    with pytest.raises(AutoCutError, match="nicht in telemetrie.json"):
        G.sidecar_pfad(v, set())


def test_sidecar_verweigert_fehlende_datei(tmp_path: Path):
    v = tmp_path / "gibtsnicht.MP4"
    with pytest.raises(AutoCutError, match="nicht gefunden"):
        G.sidecar_pfad(v, {str(v)})


def test_sidecar_verweigert_gyroflow_datei_selbst(tmp_path: Path):
    v = tmp_path / "FX3_0001.gyroflow"
    v.write_bytes(b"x")
    with pytest.raises(AutoCutError, match="bereits eine .gyroflow"):
        G.sidecar_pfad(v, {str(v)})


def _cli_attrappe(tmp_path: Path) -> str:
    """Ausführbare Attrappe: schreibt neben die Eingabedatei eine .gyroflow-Datei und zählt die Aufrufe."""
    p = tmp_path / "gyroflow_fake.sh"
    p.write_text(
        '#!/bin/sh\n'
        'echo "$@" >> "$(dirname "$1")/aufrufe.log"\n'
        'out="${1%.*}.gyroflow"\n'
        'printf \'{"version":2,"stabilization":{"max_zoom":120.0}}\' > "$out"\n',
        encoding="utf-8")
    p.chmod(0o755)
    return str(p)


def _charge(tmp_path: Path):
    from niro_autocut.charge import Charge
    root = tmp_path / "2026-09 Testdreh"
    (root / "_intern" / "autocut").mkdir(parents=True)
    (root / "Ergebnisse" / "Rohschnitt").mkdir(parents=True)
    return Charge(root=root, intern=root / "_intern", autocut=root / "_intern" / "autocut",
                  work=root / "_intern" / "autocut" / "work", ergebnisse=root / "Ergebnisse" / "Rohschnitt",
                  plaene=root / "Ergebnisse" / "O-Ton-Pläne", protokoll=root / "Protokoll.md", config=CFG)


def test_clip_export_schreibt_sidecar_neben_die_mediendatei(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    rec, aus_cache = G.clip_export(ch, v, {"haltung": "hand", "kamera": "FX3"}, cfg, {str(v)})

    assert aus_cache is False
    assert rec["fehler"] is None
    assert Path(rec["sidecar"]) == medien / "FX3_0001.gyroflow"
    assert (medien / "FX3_0001.gyroflow").is_file()
    assert "--export-project 2" in (medien / "aufrufe.log").read_text(encoding="utf-8")


def test_clip_export_nimmt_beim_zweiten_lauf_den_cache(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})
    _, aus_cache = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert aus_cache is True
    assert (medien / "aufrufe.log").read_text(encoding="utf-8").count("--export-project") == 1


def test_clip_export_misst_neu_wenn_sich_das_preset_aendert(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})
    _, aus_cache = G.clip_export(ch, v, {"haltung": "gimbal"}, cfg, {str(v)})

    assert aus_cache is False


def test_clip_export_meldet_fehler_statt_abzubrechen(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    kaputt = tmp_path / "kaputt.sh"
    kaputt.write_text('#!/bin/sh\necho "kein Gyro gefunden" >&2\nexit 1\n', encoding="utf-8")
    kaputt.chmod(0o755)
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = str(kaputt)

    rec, _ = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert rec["fehler"] and "kein Gyro" in rec["fehler"]
    assert rec["sidecar"] is None


def test_clip_export_meldet_nicht_executable_statt_abzubrechen(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    nicht_exec = tmp_path / "nicht_exec.sh"
    nicht_exec.write_text('#!/bin/sh\necho "sollte nicht laufen"\n', encoding="utf-8")
    # Deliberately do NOT chmod executable
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = str(nicht_exec)

    rec, _ = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert rec["fehler"] and "gyroflow.cli" in rec["fehler"]
    assert rec["sidecar"] is None


def test_clip_export_retry_nach_fehler_benoetigt_neu_export(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    nicht_exec = tmp_path / "nicht_exec.sh"
    nicht_exec.write_text('#!/bin/sh\necho "sollte nicht laufen"\n', encoding="utf-8")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = str(nicht_exec)

    # Erster Lauf schlägt fehl
    rec1, _ = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})
    assert rec1["fehler"]

    # Zweiter Lauf mit korrektem CLI (sollte nicht aus Cache kommen, sondern neu exportieren)
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    rec2, aus_cache = G.clip_export(ch, v, {"haltung": "hand"}, cfg, {str(v)})

    assert aus_cache is False
    assert rec2["fehler"] is None
    assert rec2["sidecar"] is not None


def test_zoom_ist_faellt_auf_den_deckel_zurueck():
    wert, gedeckelt = G.zoom_ist_lesen({"gyro_source": {}}, 120.0)
    assert wert == pytest.approx(1.20)
    assert gedeckelt is True


def test_zoom_ist_rechnet_prozent_in_faktor_um():
    # adaptive_zoom_fovs liegen als dekodierte Liste vor; Maximum zählt
    projekt = {"gyro_source": {"adaptive_zoom_fovs_dekodiert": [1.02, 1.11, 1.07]}}
    wert, gedeckelt = G.zoom_ist_lesen(projekt, 120.0)
    assert wert == pytest.approx(1.11)
    assert gedeckelt is False


def test_zoom_ist_meldet_wenn_der_deckel_griff():
    projekt = {"gyro_source": {"adaptive_zoom_fovs_dekodiert": [1.19, 1.20]}}
    wert, gedeckelt = G.zoom_ist_lesen(projekt, 120.0)
    assert wert == pytest.approx(1.20)
    assert gedeckelt is True


def test_charge_lauf_fasst_mehrfach_genutzte_dateien_zusammen(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    clips = [{"datei": str(v), "tempo50": False}, {"datei": str(v), "tempo50": True}]
    tele = [{"path": str(v), "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, clips, tele, cfg)

    assert len(erg["clips"]) == 1
    assert (medien / "aufrufe.log").read_text(encoding="utf-8").count("--export-project") == 1
    assert json.loads((ch.autocut / "gyroflow.json").read_text(encoding="utf-8"))["clips"][0]["clip"] == "FX3_0001"


def test_charge_lauf_ueberspringt_clips_ohne_gyrospur(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "ZV_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    tele = [{"path": str(v), "clip": "ZV_0001", "kamera": "ZV-E10", "haltung": "hand", "quelle": "keine"}]

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], tele, cfg)

    assert erg["clips"] == []
    assert erg["uebersprungen"][0]["grund"] == "keine Gyrospur"
    assert not (medien / "aufrufe.log").exists()


def test_charge_lauf_ueberspringt_stabilized_dateien(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "DJI_0001_stabilized.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    tele = [{"path": str(v), "clip": "DJI_0001_stabilized", "kamera": "DJI", "haltung": "gimbal", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], tele, cfg)

    assert erg["uebersprungen"][0]["grund"] == "Avata-Export (_stabilized)"


def test_charge_lauf_ueberspringt_clips_ohne_telemetrie(tmp_path: Path):
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0009.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], [], cfg)

    assert erg["uebersprungen"][0]["grund"] == "kein Telemetrie-Eintrag"


def test_charge_lauf_prueft_den_deckel_vor_dem_ersten_export(tmp_path: Path):
    ch = _charge(tmp_path)
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["max_zoom"]["hand"] = 130
    with pytest.raises(AutoCutError, match="max_zoom"):
        G.gyroflow_charge(ch, [], [], cfg)


def test_charge_lauf_fuellt_zoom_ist_aus_dem_deckel_rueckfall(tmp_path: Path):
    """Ohne dekodierte Messwerte liefert zoom_ist_lesen den Deckel als Faktor — das füllt zoom_ist/zoom_gedeckelt
    je erfolgreich exportiertem Clip statt sie bei None zu belassen (siehe Docstring von zoom_ist_lesen)."""
    ch = _charge(tmp_path)
    medien = tmp_path / "medien"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    tele = [{"path": str(v), "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, [{"datei": str(v), "tempo50": False}], tele, cfg)

    rec = erg["clips"][0]
    assert rec["zoom_ist"] == pytest.approx(1.20)
    assert rec["zoom_gedeckelt"] is True


# --- Unicode-Normalisierung der Pfad-Joins (Review-Fund, 23.09.2026) ----------------------------------------

def test_norm_pfad_fasst_nfd_und_nfc_zusammen():
    """macOS liefert Dateinamen teils in NFD; Path.resolve() rechnet die Unicode-Form nicht um. Ohne NFC greift
    jeder Join über den Pfad still daneben, sobald ein Kunden- oder Ortsordner einen Umlaut trägt."""
    nfc = "/medien/Grünwald/FX3_0001.MP4"
    nfd = unicodedata.normalize("NFD", nfc)
    assert nfd != nfc                                  # die Strings sind wirklich verschieden
    assert G.norm_pfad(nfd) == G.norm_pfad(nfc)
    assert G.norm_pfad(nfc) == unicodedata.normalize("NFC", str(Path(nfc).resolve()))


def test_charge_lauf_findet_telemetrie_auch_bei_abweichender_unicode_form(tmp_path: Path):
    """Shot-Liste in NFD, telemetrie.json in NFC (oder umgekehrt) — derselbe Clip. Ohne NFC-Normalisierung
    meldete der Lauf „kein Telemetrie-Eintrag" für einen Clip, der offensichtlich Telemetrie hat."""
    ch = _charge(tmp_path)
    medien = tmp_path / "Drehort Grünwald"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)

    nfc = unicodedata.normalize("NFC", str(v))
    nfd = unicodedata.normalize("NFD", str(v))
    assert nfc != nfd
    tele = [{"path": nfc, "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, [{"datei": nfd, "tempo50": False}], tele, cfg)

    assert erg["uebersprungen"] == []
    assert len(erg["clips"]) == 1 and erg["clips"][0]["fehler"] is None


def test_charge_lauf_dedupliziert_ueber_die_unicode_form_hinweg(tmp_path: Path):
    """Dieselbe Datei einmal in NFC und einmal in NFD in der Shot-Liste ist ein Clip, nicht zwei."""
    ch = _charge(tmp_path)
    medien = tmp_path / "Drehort Grünwald"
    medien.mkdir()
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    cfg = json.loads(json.dumps(CFG))
    cfg["gyroflow"]["cli"] = _cli_attrappe(tmp_path)
    nfc, nfd = unicodedata.normalize("NFC", str(v)), unicodedata.normalize("NFD", str(v))
    tele = [{"path": nfc, "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]

    erg = G.gyroflow_charge(ch, [{"datei": nfc, "tempo50": False}, {"datei": nfd, "tempo50": True}], tele, cfg)

    assert erg["uebersprungen"] == []
    assert len(erg["clips"]) == 1
    assert (medien / "aufrufe.log").read_text(encoding="utf-8").count("--export-project") == 1
