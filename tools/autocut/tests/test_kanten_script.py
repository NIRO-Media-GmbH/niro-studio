"""autocut_kanten.py Ende-zu-Ende: synthetischer Export + Schnappschuss → Befunde, Bericht, Bilder, Protokoll, Exit-Codes."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path

import numpy as np
import pytest
import yaml

from fake_resolve import FakeResolve
from niro_autocut.charge import DEFAULTS_FILE, Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kanten = _load("autocut_kanten")
CFG = yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8"))["kanten"]
SR, FPS, SPF, N = 48000, 25, 1920, 75
LANG = int(CFG["tonloch_min_frames"]) + 1


def _export(ziel: Path, tmp: Path) -> Path:
    """3 s, 25 fps, 160×90: Frame 40 schwarz; Ton mit Sprung genau an Frame 50 (links) und Stille ab Frame 60."""
    t = np.arange(N * SPF) / SR
    x = 0.2 * np.sin(2 * np.pi * 220 * t) + 0.05 * np.sin(2 * np.pi * 1500 * t)
    x = x + np.random.default_rng(7).normal(0, 0.0005, t.size)
    ton = np.stack([x, x], axis=1)
    ton[50 * SPF:, 0] += 0.3
    ton[60 * SPF:(60 + LANG) * SPF] = 0.0
    wav = tmp / "ton.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(ton, -1, 1) * 32767).astype("<i2").tobytes())
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc2=size=160x90:rate={FPS}:duration=3", "-i", str(wav),
                    "-vf", "drawbox=enable='eq(n,40)':color=black:t=fill", "-map", "0:v", "-map", "1:a",
                    "-c:v", "mpeg4", "-q:v", "2", "-g", "1", "-c:a", "pcm_s16le", "-shortest", str(ziel)], check=True)
    return ziel


def _snap(fx3: str, laenge: int = N) -> dict:
    def it(name, datei, start, dauer, quell_in, tempo=None):
        return {"name": name, "datei": datei, "start": start, "dauer": dauer, "quell_in": quell_in, "aktiv": True,
                "tempo": tempo}
    return {"quelle": "plan", "gelesen_am": "2026-09-16T12:00:00", "projekt": "Test", "timeline": "T", "fps": 25.0,
            "start_frame": 90000, "start_timecode": "01:00:00:00", "laenge": laenge, "spuren": {
                "V1": [it("v1", "/x/v1.MP4", 0, 50, 0, 100.0), it("v2", "/x/v2.MP4", 50, 25, 0, 100.0)],
                "A1": [it("FX3_0001.MP4", fx3, 0, 50, 0), it("FX3_0001.MP4", fx3, 50, 25, 35)]}}


def _quelle(pfad: str) -> None:
    """Rohclip FX3_0001: 3 s, Ton nur 1,0–1,6 s („Das ist meins." laut Scribe-Cache 1,0–2,0 s), sonst digital still."""
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=25:duration=3",
                    "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000:duration=3",
                    "-af", "volume='if(between(t,1.0,1.6),1,0)':eval=frame",
                    "-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le", "-f", "mov", pfad], check=True)


@pytest.fixture
def aufbau(charge_dir: Path, tmp_path: Path) -> dict:
    fx3 = Charge.open(charge_dir).load_index()[0]["path"]
    _quelle(fx3)
    export = _export(charge_dir / "Ergebnisse" / "Export" / "T.mov", tmp_path)
    rb = tmp_path / "snap.json"
    rb.write_text(json.dumps(_snap(fx3)), encoding="utf-8")
    return {"charge": charge_dir, "export": export, "readback": rb, "fx3": fx3, "tmp": tmp_path}


def test_befunde_bericht_bilder_protokoll(aufbau):
    ch = aufbau["charge"]
    assert kanten.main([str(ch), "--readback", str(aufbau["readback"])]) == 1
    erg = json.loads((ch / "_intern" / "autocut" / "kanten.json").read_text(encoding="utf-8"))
    assert [(b["art"], b["frame"]) for b in erg["befunde"]] == [
        ("Schwarzbild", 40), ("Knackser", 50), ("Wort angeschnitten", 50), ("Tonloch", 60)]
    assert erg["befunde"][3]["frames"] == LANG and erg["befunde"][2]["wort"] == "ist"
    assert erg["befunde"][2]["wert"] == 0.0 and Path(erg["befunde"][2]["bild"]).name == "kante_003_wort_01-00-02-00.png"
    assert all(b["bild"] and Path(b["bild"]).is_file() for b in erg["befunde"])
    assert Path(erg["befunde"][0]["bild"]).name == "kante_001_schwarzbild_01-00-01-15.png"
    bericht = (ch / "Ergebnisse" / "Rohschnitt" / "video-1-test-kanten.md").read_text(encoding="utf-8")
    assert "**4 Befunde**" in bericht and "01:00:02:00" in bericht
    assert (ch / "_intern" / "autocut" / "kanten_readback.json").is_file()
    assert "AutoCut: Kantenprüfung" in (ch / "Protokoll.md").read_text(encoding="utf-8")


def test_export_passt_nicht_oder_fehlt(aufbau, capsys):
    ch = aufbau["charge"]
    lang = aufbau["tmp"] / "lang.json"
    lang.write_text(json.dumps(_snap(aufbau["fx3"], laenge=80)), encoding="utf-8")
    assert kanten.main([str(ch), "--readback", str(lang), "--ohne-bilder"]) == 2
    assert "nicht aktuell" in capsys.readouterr().err
    aufbau["export"].unlink()
    assert kanten.main([str(ch), "--readback", str(aufbau["readback"])]) == 2
    assert "Kein Export für 'T'" in capsys.readouterr().err


def test_ohne_readback_liest_resolve_und_meldet_fehlende_timeline(aufbau, monkeypatch, capsys):
    ch = aufbau["charge"]
    (ch / "_intern" / "autocut" / "build.json").write_text(json.dumps({"timeline": "T", "video": "video-1-test.md"}),
                                                          encoding="utf-8")
    fr = FakeResolve()
    monkeypatch.setattr(kanten.RA, "connect", lambda: fr)
    assert kanten.main([str(ch)]) == 2
    err = capsys.readouterr().err
    assert "Timeline 'T' ist nicht im offenen Projekt" in err and "--readback" in err


def test_timeline_name_nimmt_neueste_datei(aufbau):
    ch = Charge.open(aufbau["charge"])
    (ch.autocut / "build.json").write_text(json.dumps({"timeline": "Roh"}), encoding="utf-8")
    (ch.autocut / "finalize.json").write_text(json.dumps({"timeline": "End", "status": "fehler"}), encoding="utf-8")
    (ch.autocut / "feinschnitt.json").write_text(json.dumps({"timeline": "Fein"}), encoding="utf-8")
    alt = time.time() - 100
    os.utime(ch.autocut / "build.json", (alt, alt))
    assert kanten.timeline_name(ch) == "Fein"
    os.utime(ch.autocut / "feinschnitt.json", (alt - 50, alt - 50))
    assert kanten.timeline_name(ch) == "Roh"          # finalize.json ohne status ok zählt nicht


def test_ohne_export_nur_wortkanten(aufbau):
    ch = aufbau["charge"]
    aufbau["export"].unlink()
    assert kanten.main([str(ch), "--readback", str(aufbau["readback"]), "--ohne-export"]) == 1
    erg = json.loads((ch / "_intern" / "autocut" / "kanten.json").read_text(encoding="utf-8"))
    assert [(b["art"], b["frame"]) for b in erg["befunde"]] == [("Wort angeschnitten", 50)]
    assert erg["export"] is None and Path(erg["befunde"][0]["bild"]).is_file()
    bericht = (ch / "Ergebnisse" / "Rohschnitt" / "video-1-test-kanten.md").read_text(encoding="utf-8")
    assert "nur Wortkanten" in bericht
