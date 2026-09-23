"""autocut_gyroflow.py — CLI auf einer Fake-Charge: fehlende Eingaben, --dry-run, voller Lauf, Fehlerfall
(Spec 2026-09-22)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from test_gyroflow import _cli_attrappe

SKRIPT = Path(__file__).resolve().parents[1] / "scripts" / "autocut_gyroflow.py"


def _lade():
    spec = importlib.util.spec_from_file_location("autocut_gyroflow", SKRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _autocut(basis_charge: Path) -> Path:
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True, exist_ok=True)
    return ac


def _mit_eingaben(basis_charge: Path, tmp_path: Path, cli: str) -> Path:
    """Charge mit gyroflow_clips.json, telemetrie.json (ein rtmd-Clip) und config.yaml auf die gegebene CLI."""
    ac = _autocut(basis_charge)
    medien = tmp_path / "medien"
    medien.mkdir(exist_ok=True)
    v = medien / "FX3_0001.MP4"
    v.write_bytes(b"videodaten")
    (ac / "gyroflow_clips.json").write_text(json.dumps([{"datei": str(v), "tempo50": False}]), encoding="utf-8")
    (ac / "telemetrie.json").write_text(
        json.dumps([{"path": str(v), "clip": "FX3_0001", "kamera": "FX3", "haltung": "hand", "quelle": "rtmd"}]),
        encoding="utf-8")
    (ac / "config.yaml").write_text(f'gyroflow:\n  cli: "{cli}"\n', encoding="utf-8")
    return v


def test_fehlt_gyroflow_clips_json_meldet_datei_und_erzeugendes_skript(basis_charge, capsys):
    skript = _lade()
    assert skript.main([str(basis_charge)]) == 1
    err = capsys.readouterr().err
    assert "gyroflow_clips.json" in err and "feinschnitt_bauen.py" in err


def test_fehlt_telemetrie_json_meldet_datei_und_erzeugendes_skript(basis_charge, capsys):
    ac = _autocut(basis_charge)
    (ac / "gyroflow_clips.json").write_text("[]", encoding="utf-8")
    skript = _lade()
    assert skript.main([str(basis_charge)]) == 1
    err = capsys.readouterr().err
    assert "telemetrie.json" in err and "autocut_telemetrie.py" in err


def test_dry_run_schreibt_nichts_und_erzeugt_keinen_sidecar(basis_charge, tmp_path, capsys):
    v = _mit_eingaben(basis_charge, tmp_path, _cli_attrappe(tmp_path))
    skript = _lade()

    assert skript.main([str(basis_charge), "--dry-run"]) == 0

    assert "1 genutzte Shots, 1 Quelldateien." in capsys.readouterr().out
    assert not (basis_charge / "_intern" / "autocut" / "gyroflow.json").exists()
    assert not (basis_charge / "Ergebnisse" / "Rohschnitt" / "gyroflow.md").exists()
    assert not v.with_suffix(".gyroflow").exists()


def test_voller_lauf_schreibt_json_bericht_sidecar_und_protokoll(basis_charge, tmp_path, capsys):
    v = _mit_eingaben(basis_charge, tmp_path, _cli_attrappe(tmp_path))
    skript = _lade()

    assert skript.main([str(basis_charge)]) == 0

    erg = json.loads((basis_charge / "_intern" / "autocut" / "gyroflow.json").read_text(encoding="utf-8"))
    assert erg["clips"][0]["clip"] == "FX3_0001" and erg["clips"][0]["fehler"] is None
    md_pfad = basis_charge / "Ergebnisse" / "Rohschnitt" / "gyroflow.md"
    assert md_pfad.is_file() and "FX3_0001" in md_pfad.read_text(encoding="utf-8")
    assert v.with_suffix(".gyroflow").is_file()
    assert "AutoCut: Gyroflow-Sidecars" in (basis_charge / "Protokoll.md").read_text(encoding="utf-8")
    assert "FX3_0001" in capsys.readouterr().out


def test_fehlerhafter_clip_liefert_exit_1_und_bericht_nennt_fehler(basis_charge, tmp_path):
    nicht_exec = tmp_path / "nicht_exec.sh"
    nicht_exec.write_text('#!/bin/sh\necho "sollte nicht laufen"\n', encoding="utf-8")   # absichtlich nicht chmod +x
    v = _mit_eingaben(basis_charge, tmp_path, str(nicht_exec))
    skript = _lade()

    assert skript.main([str(basis_charge)]) == 1

    md = (basis_charge / "Ergebnisse" / "Rohschnitt" / "gyroflow.md").read_text(encoding="utf-8")
    assert "## Fehler" in md and "gyroflow.cli" in md
    assert not v.with_suffix(".gyroflow").exists()


def test_kaputte_gyroflow_clips_json_meldet_deutsch_statt_traceback(basis_charge, capsys):
    """Ein roher JSONDecodeError-Traceback ist keine Meldung, die dem Operator sagt, was zu tun ist."""
    ac = _autocut(basis_charge)
    (ac / "gyroflow_clips.json").write_text("{kaputt", encoding="utf-8")
    skript = _lade()

    assert skript.main([str(basis_charge)]) == 1

    err = capsys.readouterr().err
    assert "gyroflow_clips.json ist nicht lesbar" in err and "JSONDecodeError" in err
    assert "feinschnitt_bauen.py" in err


def test_kaputte_telemetrie_json_meldet_deutsch_statt_traceback(basis_charge, capsys):
    ac = _autocut(basis_charge)
    (ac / "gyroflow_clips.json").write_text("[]", encoding="utf-8")
    (ac / "telemetrie.json").write_text("nicht json", encoding="utf-8")
    skript = _lade()

    assert skript.main([str(basis_charge)]) == 1

    err = capsys.readouterr().err
    assert "telemetrie.json ist nicht lesbar" in err and "autocut_telemetrie.py" in err
