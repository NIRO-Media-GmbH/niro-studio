"""gyroflow.py — Preset aus der Telemetrie, Deckel-Prüfung, Sidecar-Pfad, Clip-Export, Charge-Lauf (Spec 2026-09-22)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from niro_autocut import gyroflow as G
from niro_autocut.charge import AutoCutError

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
