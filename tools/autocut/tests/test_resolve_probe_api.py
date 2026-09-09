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
    FakeTimeline.speed_extends = False
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0
    yield
    FakeTimeline.inclusive = True
    FakeTimeline.speed_extends = False
    FakeTimeline.fades_need_active = False
    FakeTimeline.align_moves = "V2"
    FakeTimeline.align_offset_frames = -50
    FakeTimeline.tpk_dbfs = -12.0


@pytest.fixture
def env(charge_dir: Path, monkeypatch) -> dict:
    """Charge + Fake-Resolve (Projekt „MCP MEK Test", Projektauflösung bleibt beim Fake-Default 3840×2160);
    ffmpeg und True-Peak-Messung gepatcht."""
    ch = Charge.open(charge_dir)
    project = FakeProject("MCP MEK Test")
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
    assert sp["gap"] == "behält_dauer" and sp["source_kept"] is False and sp["ripple"] == "verschiebt"
    assert sp["a"]["dauer_vorher"] == 50 and sp["a"]["dauer_nachher"] == 50 and sp["a"]["src_nachher"] == [0, 50]
    assert sp["blocked"]["b_dauer_nachher"] == 50 and sp["blocked"]["c_start_nachher"] == sp["blocked"]["c_start_vorher"]
    assert res["normalize"]["soll"] == 9.0 and res["normalize"]["diff"] == 0.0
    assert res["autoalign"]["moved"] == "V2" and res["autoalign"]["delta_frames"] == -50
    assert res["alpha_import"]["alpha_mode"] == "Straight" and res["alpha_import"]["dauer"] == 50
    assert res["quickexport"]["status"] == "Render Complete" and res["quickexport"]["datei"] == "probe_api.mov"
    assert res["baseline"]["A"]["tracks"]["V4"]["name"] == "Grafik"
    assert (res["baseline"]["A"]["width"], res["baseline"]["A"]["height"]) == (3840, 2160)   # Projektauflösung, kein useCustomSettings
    assert res["timelines"]["A"].startswith("AutoCut PROBE API ") and res["timelines"]["B"] == res["timelines"]["A"] + " SYNC"
    p = env["project"]
    assert p.timelines == [] and _autocut_bin(p).subs == []
    assert res["cleanup"] == {"timelines": True, "clips": True, "folders": True}
    assert "probe_api.json" in capsys.readouterr().out


def test_cleanup_spares_objects_of_earlier_runs(env):
    p = env["project"]
    mp = p.GetMediaPool()
    root = mp.GetRootFolder()
    ac = mp.AddSubFolder(root, "AutoCut")
    alt = mp.AddSubFolder(ac, "PROBE-API")
    mp.SetCurrentFolder(alt)
    work = env["ch"].work / "probe_api"
    work.mkdir(parents=True, exist_ok=True)
    (work / "ton_25p.mov").write_bytes(b"alt")
    alter_clip = mp.ImportMedia([str(work / "ton_25p.mov")])[0]          # Clip eines früheren Laufs
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["ok"] is True
    assert [f.name for f in ac.subs] == ["PROBE-API"]                       # Bin bleibt
    assert alter_clip in alt.clips                                          # fremder Clip bleibt
    assert not any(c.path.endswith(("zaehler_50p.mov", "overlay_alpha.mov")) for c in alt.clips)  # eigene Importe weg
    assert res["cleanup"]["timelines"] is True and "uebersprungen" in str(res["cleanup"]["folders"])


def test_project_mismatch_exits_2_without_touching_resolve(env, capsys):
    rc = probe.main([str(env["dir"]), "--project", "Kundenprojekt"])
    assert rc == 2
    assert env["project"].timelines == [] and env["project"].mp.calls == []
    assert env["ch"].read_json("probe_api.json") is None
    assert "freigegeben" in capsys.readouterr().err


def test_fps_mismatch_exits_2_without_changes(env, capsys):
    env["project"].settings["timelineFrameRate"] = "30"
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    assert rc == 2 and env["project"].timelines == [] and env["project"].mp.calls == []
    assert "fps" in capsys.readouterr().err


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
    user_tl = env["project"].GetMediaPool().CreateEmptyTimeline("User Schnitt")
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 1 and res["ok"] is False and "kaputt" in res["fehler"] and res["traceback"]
    names = [t.name for t in env["project"].timelines if "PROBE API" in t.name]
    assert len(names) == 2 and all(n.endswith(" FEHLER") for n in names)
    assert res["cleanup"] is None and _autocut_bin(env["project"]).subs[0].name == "PROBE-API"
    assert env["project"].current is user_tl


def test_partial_build_marks_created_timeline_as_fehler(env, monkeypatch):
    orig = probe.RA.ResolveSession.create_timeline

    def flaky(self, name, *a, **k):
        if name.endswith(" SYNC"):
            raise RuntimeError("SYNC kaputt")
        return orig(self, name, *a, **k)

    monkeypatch.setattr(probe.RA.ResolveSession, "create_timeline", flaky)
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    names = [t.name for t in env["project"].timelines]
    assert rc == 1 and len(names) == 1 and names[0].endswith(" FEHLER")


def test_failed_mandatory_measure_keeps_objects_for_inspection(env, monkeypatch):
    monkeypatch.setattr(probe, "measure_volume",
                        lambda h: {"ok": False, "soll": 9.0, "ist": None, "enabled": False, "set_returned": False})
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 1 and res["ok"] is False and res["fehler"] is None
    assert "uebersprungen" in res["cleanup"]
    names = [t.name for t in env["project"].timelines]
    assert len(names) == 2 and not any(n.endswith(" FEHLER") for n in names)
    assert [f.name for f in _autocut_bin(env["project"]).subs] == ["PROBE-API"]


def test_extending_semantics_is_classified_not_failed(env):
    FakeTimeline.speed_extends = True
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["speed"]["ok"] is True
    assert res["speed"]["gap"] == "verlängert" and res["speed"]["source_kept"] is True


def test_missing_preset_and_missing_mode_are_skipped(env):
    env["project"].quick_presets = ["YouTube"]
    FakeTimeline.NORMALIZE_MODES = ["Sample Peak Program"]
    try:
        rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    finally:
        FakeTimeline.NORMALIZE_MODES = ["Sample Peak Program", "True Peak", "ITU-R BS.1770-4", "EBU R128"]
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and "uebersprungen" in res["quickexport"] and "uebersprungen" in res["normalize"]


def test_stale_render_file_does_not_count(env):
    target = env["ch"].work / "probe_api" / "render"
    target.mkdir(parents=True, exist_ok=True)
    (target / "probe_api.mov").write_bytes(b"alt")
    env["project"].RenderWithQuickExport = lambda preset, settings=None: {"JobStatus": "Render Failed", "Error": "Test"}
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["quickexport"]["ok"] is False and res["quickexport"]["datei"] is None
    assert not (target / "probe_api.mov").exists()


def test_result_is_written_even_with_non_primitive_values(env, monkeypatch):
    monkeypatch.setattr(probe, "measure_transition", lambda h: {"ok": True, "typ": "transition", "dauer": 12, "obj": object()})
    rc = probe.main([str(env["dir"]), "--project", "MCP MEK Test"])
    res = env["ch"].read_json("probe_api.json")
    assert rc == 0 and res["transition"]["obj"].startswith("<object object")


def test_user_timeline_is_restored(env):
    p = env["project"]
    user_tl = p.GetMediaPool().CreateEmptyTimeline("User Schnitt")
    assert probe.main([str(env["dir"]), "--project", "MCP MEK Test"]) == 0
    assert p.current is user_tl and p.timelines == [user_tl]


def test_charge_without_plan_exits_2(tmp_path, capsys):
    assert probe.main([str(tmp_path), "--project", "MCP MEK Test"]) == 2
    assert "Vorbedingung" in capsys.readouterr().err
