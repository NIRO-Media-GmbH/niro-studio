"""autocut_schnittbild.py: Clip- und Export-Modus, Zeitangaben, Fehler."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

from niro_autocut.charge import AutoCutError, Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sb = _load("autocut_schnittbild")


def _video(pfad: Path) -> Path:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=25:duration=3",
                    "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=3",
                    "-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le", "-f", "mov", str(pfad)], check=True)
    return pfad


def test_sekunden():
    assert sb.sekunden("12.5") == 12.5 and sb.sekunden("01:02,5") == 62.5 and sb.sekunden("1:02:03.5") == 3723.5
    with pytest.raises(AutoCutError):
        sb.sekunden("x")
    with pytest.raises(AutoCutError):
        sb.sekunden("1:2:3:4")


def test_clip_modus(charge_dir, capsys):
    ch = Charge.open(charge_dir)
    _video(Path(ch.load_index()[0]["path"]))
    assert sb.main([str(charge_dir), "--clip", "FX3_0001.MP4", "--von", "0.5", "--bis", "0:01.8"]) == 0
    ziel = Path(capsys.readouterr().out.strip())
    assert ziel == ch.work / "schnittbild" / "FX3_0001_0.50-1.80.png" and ziel.is_file()
    assert sb.main([str(charge_dir), "--clip", "fehlt.MP4", "--von", "0", "--bis", "1"]) == 2
    assert "nicht im Transkript-Index" in capsys.readouterr().err
    assert sb.main([str(charge_dir), "--clip", "FX3_0001.MP4", "--von", "0"]) == 2
    assert "--von und --bis" in capsys.readouterr().err


def test_export_modus(charge_dir, tmp_path, capsys):
    ch = Charge.open(charge_dir)
    export = _video(tmp_path / "T.mov")
    assert sb.main([str(charge_dir), "--render", str(export), "--tc", "01:00:01:00"]) == 2
    assert "Schnappschuss fehlt" in capsys.readouterr().err
    fx3 = ch.load_index()[0]["path"]
    snap = {"quelle": "plan", "gelesen_am": "x", "projekt": "P", "timeline": "T", "fps": 25.0, "start_frame": 0,
            "start_timecode": "01:00:00:00", "laenge": 75, "spuren": {
                "V1": [{"name": "v", "datei": "v", "start": 0, "dauer": 30, "quell_in": 0, "aktiv": True, "tempo": 100.0},
                       {"name": "w", "datei": "w", "start": 30, "dauer": 45, "quell_in": 0, "aktiv": True, "tempo": 100.0}],
                "A1": [{"name": "FX3_0001.MP4", "datei": fx3, "start": 0, "dauer": 75, "quell_in": 0, "aktiv": True,
                        "tempo": None}]}}
    ch.write_json("kanten_readback.json", snap)
    assert sb.main([str(charge_dir), "--render", str(export), "--tc", "01:00:01:05"]) == 0
    ziel = Path(capsys.readouterr().out.strip())
    assert ziel.name == "export_01-00-01-05.png" and ziel.is_file()
    assert sb.main([str(charge_dir), "--render", str(export), "--frame", "500"]) == 2
    assert "außerhalb" in capsys.readouterr().err
