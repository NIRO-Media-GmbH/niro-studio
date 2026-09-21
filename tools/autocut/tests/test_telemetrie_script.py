"""autocut_telemetrie.py — CLI auf einer Fake-Charge: Lauf, Bericht, Protokoll, --dry-run, --ohne-optisch, Fehlerfälle."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SKRIPT = Path(__file__).resolve().parents[1] / "scripts" / "autocut_telemetrie.py"


def _lade():
    spec = importlib.util.spec_from_file_location("autocut_telemetrie", SKRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _charge_mit_clip(basis_charge: Path, tmp_path: Path) -> Path:
    clip = tmp_path / "nas" / "Mavic" / "DJI_0001.mp4"
    clip.parent.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    (ac / "inventar.json").write_text(
        json.dumps([{"ordner": "Mavic", "name": clip.name, "path": str(clip)}]), encoding="utf-8")
    return clip


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_lauf_schreibt_json_bericht_und_protokoll(basis_charge, tmp_path, capsys):
    _charge_mit_clip(basis_charge, tmp_path)
    skript = _lade()
    assert skript.main([str(basis_charge)]) == 0
    tele = json.loads((basis_charge / "_intern" / "autocut" / "telemetrie.json").read_text(encoding="utf-8"))
    assert len(tele) == 1 and tele[0]["quelle"] == "optisch"
    md = (basis_charge / "Ergebnisse" / "Rohschnitt" / "telemetrie.md").read_text(encoding="utf-8")
    assert md.startswith("# Kamera-Telemetrie") and "DJI_0001" in md
    assert "AutoCut: Telemetrie" in (basis_charge / "Protokoll.md").read_text(encoding="utf-8")
    out = capsys.readouterr().out
    assert "1 Clips" in out and "telemetrie.md" in out


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")
def test_dry_run_und_ohne_optisch(basis_charge, tmp_path):
    _charge_mit_clip(basis_charge, tmp_path)
    skript = _lade()
    assert skript.main([str(basis_charge), "--dry-run"]) == 0
    assert not (basis_charge / "_intern" / "autocut" / "telemetrie.json").exists()
    assert skript.main([str(basis_charge), "--ohne-optisch"]) == 0
    tele = json.loads((basis_charge / "_intern" / "autocut" / "telemetrie.json").read_text(encoding="utf-8"))
    assert tele[0]["quelle"] == "keine"


def test_fehler_ohne_charge_und_ohne_clips(basis_charge, tmp_path, capsys):
    skript = _lade()
    assert skript.main([str(tmp_path / "nirgendwo")]) == 1
    assert "FEHLER" in capsys.readouterr().err
    (basis_charge / "_intern" / "autocut").mkdir(parents=True)
    assert skript.main([str(basis_charge)]) == 1
    assert "Keine Clips" in capsys.readouterr().err
