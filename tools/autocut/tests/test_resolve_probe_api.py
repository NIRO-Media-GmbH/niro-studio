"""resolve_probe_api.py gegen das Fake-Resolve: Volllauf mit Aufräumen, Projekt-Schutz (Exit 2), --keep,
Fehlerpfad (… FEHLER, nichts gelöscht), „behält_dauer"-Semantik, fehlendes Preset, User-Timeline."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from fake_resolve import FakeProject, FakeResolve, FakeTimeline
from niro_autocut import probe_media as PM
from niro_autocut.charge import Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe = _load("resolve_probe_api")
ALLE = ("volume", "normalize", "speed", "fades", "transition", "autoalign", "inactive", "quickexport", "alpha_import")


@pytest.fixture(autouse=True)
def _fake_defaults():
    FakeTimeline.inclusive = True
    FakeTimeline.speed_extends = True
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0
    yield
    FakeTimeline.inclusive = True
    FakeTimeline.speed_extends = True
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0


@pytest.fixture
def env(charge_dir: Path, monkeypatch) -> dict:
    """Charge + Fake-Resolve (Projekt „MCP MEK Test", 1920×1080); ffmpeg und True-Peak-Messung gepatcht."""
    ch = Charge.open(charge_dir)
    project = FakeProject("MCP MEK Test")
    project.settings.update({"timelineResolutionWidth": "1920", "timelineResolutionHeight": "1080"})
    fake = FakeResolve(project)
    work = ch.work / "probe_api"
    project.mp.fps_by_path[str(work / "zaehler_50p.mov")] = 50
    project.mp.alpha_by_path[str(work / "overlay_alpha.mov")] = "Straight"

    def fake_run(argv, **kw):
        Path(argv[-1]).write_bytes(b"synthetisch")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(PM.subprocess, "run", fake_run)
    monkeypatch.setattr(PM, "_which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(probe.RA, "connect", lambda: fake)
    monkeypatch.setattr(probe, "measure_true_peak", lambda path, in_s, dur_s: -12.0)
    return {"ch": ch, "project": project, "fake": fake, "dir": charge_dir}


def _autocut_bin(project: FakeProject):
    return next((f for f in project.mp.root.subs if f.name == "AutoCut"), None)


def test_full_run_ok_and_cleans_up(env, capsys):
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["ok"] is True and res["project"] == "MCP MEK Test" and res["resolve_version"] == "21.1.0.14"
    for k in ALLE:
        assert res[k].get("ok") is True, k
    sp = res["speed"]
    assert sp["gap"] == "verlängert" and sp["source_kept"] is True and sp["ripple"] == "verschiebt"
    assert sp["a"]["dauer_vorher"] == 50 and sp["a"]["dauer_nachher"] == 100
    assert sp["blocked"]["b_dauer_nachher"] == 50 and sp["blocked"]["c_start_nachher"] == sp["blocked"]["c_start_vorher"]
    assert res["normalize"]["soll"] == 9.0 and res["normalize"]["diff"] == 0.0
    assert res["autoalign"]["moved"] == "V2" and res["autoalign"]["delta_frames"] == -50
    assert res["alpha_import"]["alpha_mode"] == "Straight" and res["alpha_import"]["dauer"] == 50
    assert res["quickexport"]["status"] == "Render Complete" and res["quickexport"]["datei"] == "probe_api.mov"
    assert res["baseline"]["A"]["tracks"]["V4"]["name"] == "Grafik"
    assert res["timelines"] == {"A": res["timelines"]["A"], "B": res["timelines"]["A"] + " SYNC"}
    p = env["project"]
    assert p.timelines == [] and _autocut_bin(p).subs == []
    assert res["cleanup"] == {"timelines": True, "clips": True, "folders": True}
    assert "probe_api.json" in capsys.readouterr().out


def test_project_mismatch_exits_2_without_touching_resolve(env, capsys):
    rc = probe.main([str(env["dir"]), "--project", "Kundenprojekt"])
    assert rc == 2
    assert env["project"].timelines == [] and env["project"].mp.calls == []
    assert env["ch"].read_json("probe_api.json") is None
    assert "freigegeben" in capsys.readouterr().err


def test_keep_retains_timelines_and_bin(env):
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test", "--keep"])
    assert rc == 0
    names = [t.name for t in env["project"].timelines]
    assert len(names) == 2 and names[1] == names[0] + " SYNC" and names[0].startswith("AutoCut PROBE API ")
    assert [f.name for f in _autocut_bin(env["project"]).subs] == ["PROBE-API"]


def test_failure_renames_timelines_keeps_objects_and_exits_1(env, monkeypatch):
    def boom(h):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(probe, "measure_fades", boom)
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 1 and res["ok"] is False and "kaputt" in res["fehler"] and res["traceback"]
    names = [t.name for t in env["project"].timelines]
    assert len(names) == 2 and all(n.endswith(" FEHLER") for n in names)
    assert res["cleanup"] is None and _autocut_bin(env["project"]).subs[0].name == "PROBE-API"


def test_keeps_duration_semantics_is_classified_not_failed(env):
    FakeTimeline.speed_extends = False
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["speed"]["ok"] is True
    assert res["speed"]["gap"] == "behält_dauer" and res["speed"]["source_kept"] is False


def test_missing_preset_and_missing_mode_are_skipped(env):
    env["project"].quick_presets = ["YouTube"]
    FakeTimeline.NORMALIZE_MODES = ["Sample Peak Program"]
    try:
        rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    finally:
        FakeTimeline.NORMALIZE_MODES = ["Sample Peak Program", "True Peak", "ITU-R BS.1770-4", "EBU R128"]
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and "uebersprungen" in res["quickexport"] and "uebersprungen" in res["normalize"]


def test_user_timeline_is_restored(env):
    p = env["project"]
    user_tl = p.GetMediaPool().CreateEmptyTimeline("User Schnitt")
    assert probe.main([str(env["dir"]), "--project", "MCP MEK Test"]) == 0
    assert p.current is user_tl and p.timelines == [user_tl]


def test_charge_without_plan_exits_2(tmp_path, capsys):
    assert probe.main([str(tmp_path), "--project", "MCP MEK Test"]) == 2
    assert "Vorbedingung" in capsys.readouterr().err
