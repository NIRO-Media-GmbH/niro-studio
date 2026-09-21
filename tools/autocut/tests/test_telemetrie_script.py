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


# --- Final Review (21.09.2026): volle Clip-Liste an telemetrie_charge, Bericht aus der ganzen telemetrie.json (I3) -------

def _charge_mit_inventar(basis_charge: Path) -> Path:
    """Charge mit inventar.json (ein Pfad doppelt) und einer telemetrie.json aus einem früheren Volllauf."""
    ac = basis_charge / "_intern" / "autocut"
    ac.mkdir(parents=True)
    inventar = [{"ordner": "FX3", "path": "/nas/FX3/FX3_1.MP4"}, {"ordner": "FX3b", "path": "/nas/FX3/FX3_1.MP4"},
                {"ordner": "FX30", "path": "/nas/FX30/C0001.MP4"}]
    (ac / "inventar.json").write_text(json.dumps(inventar), encoding="utf-8")
    alt = [{"path": "/nas/FX3/FX3_1.MP4", "clip": "FX3_1", "kamera": "FX3", "quelle": "rtmd", "wackeln": 0.1,
            "fenster": [], "ruhige_fenster": [], "fehler": None},
           {"path": "/nas/FX30/C0001.MP4", "clip": "C0001", "kamera": "Sony ILME-FX30", "quelle": "rtmd", "wackeln": 0.2,
            "fenster": [], "ruhige_fenster": [], "fehler": None}]
    (ac / "telemetrie.json").write_text(json.dumps(alt), encoding="utf-8")
    return ac


def test_cli_uebergibt_volle_liste_und_baut_bericht_aus_ganzer_telemetrie_json(basis_charge, monkeypatch, capsys):
    ac = _charge_mit_inventar(basis_charge)
    skript = _lade()
    gesehen: dict = {}

    def fake(ch, clips, cfg, limit=None, **kw):
        gesehen.update(clips=list(clips), limit=limit)
        return {"clips": [json.loads((ac / "telemetrie.json").read_text(encoding="utf-8"))[0]], "fehler": [],
                "cache_treffer": 0, "gemessen": 1, "gesamt": 2}

    monkeypatch.setattr(skript, "telemetrie_charge", fake)
    assert skript.main([str(basis_charge), "--limit", "1"]) == 0
    assert len(gesehen["clips"]) == 3 and gesehen["limit"] == 1          # nicht vorher geschnitten, Dublette inklusive
    out = capsys.readouterr().out
    assert "2 Clips, dieser Lauf 1" in out                                # eindeutige Pfade
    md = (basis_charge / "Ergebnisse" / "Rohschnitt" / "telemetrie.md").read_text(encoding="utf-8")
    assert "2 Clips" in md and "FX3_1" in md and "C0001" in md             # ganze telemetrie.json, nicht nur der Teil-Lauf


def test_cli_kalibrieren_bekommt_deduplizierte_liste(basis_charge, monkeypatch):
    _charge_mit_inventar(basis_charge)
    skript = _lade()
    from niro_autocut import telemetrie_kalibrierung as K
    gesehen: dict = {}

    def fake(ch, clips, cfg, parallel=None, **kw):
        gesehen["clips"] = [c["path"] for c in clips]
        return {"anzahl": len(clips), "kameras": {}, "empfehlung": {}, "fehler": []}

    monkeypatch.setattr(K, "kalibrieren", fake)
    monkeypatch.setattr(K, "tabelle", lambda erg: "Tabelle")
    assert skript.main([str(basis_charge), "--kalibrieren"]) == 0
    assert gesehen["clips"] == ["/nas/FX3/FX3_1.MP4", "/nas/FX30/C0001.MP4"]
    assert skript.main([str(basis_charge), "--kalibrieren", "--limit", "1"]) == 0
    assert gesehen["clips"] == ["/nas/FX3/FX3_1.MP4"]
