"""Tests für die Skripte aus Task 8 gegen das Fake-Resolve: resolve_probe.py, autocut_build.py,
autocut_export_xml.py, autocut_read_timelines.py (kein echtes Resolve, kein NAS)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from fake_resolve import FakeProject, FakeResolve, FakeTimeline
from niro_autocut import resolve_api as RA
from niro_autocut import telemetrie as TM
from niro_autocut.charge import AutoCutError, Charge
from niro_autocut.cutlist import cutlist_hash

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe = _load("resolve_probe")
build = _load("autocut_build")
export = _load("autocut_export_xml")
readtl = _load("autocut_read_timelines")
place = _load("autocut_place_broll")


@pytest.fixture(autouse=True)
def _fake_defaults():
    FakeTimeline.inclusive = True
    FakeTimeline.reject_beyond_end = False
    yield
    FakeTimeline.inclusive = True
    FakeTimeline.reject_beyond_end = False


@pytest.fixture
def mek(charge_dir: Path, tmp_path: Path) -> dict:
    """Charge mit media.json, sync.json, cutlist.json, verify.json; Clip-Dateien existieren (leer)."""
    ch = Charge.open(charge_dir)
    fx = str(tmp_path / "nas" / "Interviews" / "Anna" / "FX3_0001.MP4")
    a7 = str(tmp_path / "nas" / "Interviews" / "Anna" / "a7MK4_0001.MP4")
    for p in (fx, a7):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_bytes(b"")
    (Path(fx).parent / "Proxy").mkdir(exist_ok=True)
    media = {"format": {"fps": 25.0, "width": 3840, "height": 2160, "orientation": "16:9"},
             "clips": {fx: {"original": {"nb_frames": 7500, "duration_s": 300.0, "fps": 25.0}, "proxy_path": str(Path(fx).parent / "Proxy" / "FX3_0001.mov"),
                            "kamera": "FX3", "rolle": "ton", "ordner": "Anna"},
                       a7: {"original": {"nb_frames": 8000, "duration_s": 320.0, "fps": 25.0}, "proxy_path": None,
                            "kamera": "a7MK4", "rolle": "kontext", "ordner": "Anna"}},
             "ordner": {"Anna": {"ton": [fx], "kontext": [a7]}}}
    sync = {"fps": 25, "paare": [{"ref": fx, "other": a7, "offset_s": 2.0, "offset_frames": 50, "confidence": 12.0,
                                  "overlap_ref": [0.0, 300.0], "drift_frames": 0.0, "ok": True, "note": ""}]}
    cutlist = {"video": "video-1-test.md", "ziel_laenge_s": 5.0, "fps": 25, "format": "16:9", "pause_s": 1.0,
               "beats": [{"nr": "1", "szene": "Hook", "typ": "oton", "person": "Anna", "clip": fx,
                          "cuts": [{"in_s": 1.0, "out_s": 2.0, "text": "Das ist meins."}]},
                         {"nr": "2", "szene": "Endcard", "typ": "grafik", "platzhalter_s": 2.0}],
               "sperren": [], "hinweise": []}
    ch.write_json("media.json", media)
    ch.write_json("sync.json", sync)
    cpath = ch.write_json("cutlist.json", cutlist)
    ch.write_json("verify.json", {"cutlist_hash": cutlist_hash(cpath), "ok": True, "errors": [], "warnings": []})
    return {"ch": ch, "fx": fx, "a7": a7, "dir": charge_dir}


# --- resolve_probe.py ---------------------------------------------------------

def test_probe_measures_and_deletes_own_timeline(mek, monkeypatch, capsys):
    fake = FakeResolve(FakeProject("MEK"))
    monkeypatch.setattr(RA, "connect", lambda: fake)
    assert probe.main([str(mek["dir"])]) == 0
    p = mek["ch"].read_json("probe.json")
    assert p["ok"] is True and p["end_frame_inclusive"] is True and p["record_frame_absolute"] is True
    assert all(p["checks"].values()) and p["marker_keys"] == [0, 36] and p["timeline_geloescht"] is True
    assert p["fenster"] == [250, 322] and p["offset_frames"] == 50 and p["sync_paar"] is True
    assert fake.p.timelines == [] and p["timeline"].startswith("AutoCut PROBE ")
    assert [c for c in fake.p.mp.calls if c[0] == "DeleteTimelines"][0][1] == [p["timeline"]]
    # Bin AutoCut/PROBE bleibt, Medien darin, FX3-Proxy verknüpft
    root = fake.p.mp.root
    assert [f.name for f in root.subs[0].subs] == ["PROBE"] and len(root.subs[0].subs[0].clips) == 2
    assert p["proxy_FX3_0001"] is True and p["proxy_a7MK4_0001"] is None
    assert "PROBE OK" in capsys.readouterr().out


def test_probe_detects_exclusive_semantics(mek, monkeypatch):
    FakeTimeline.inclusive = False
    fake = FakeResolve()
    monkeypatch.setattr(RA, "connect", lambda: fake)
    assert probe.main([str(mek["dir"]), "--keep"]) == 0
    p = mek["ch"].read_json("probe.json")
    assert p["ok"] is True and p["end_frame_inclusive"] is False and p["measure_duration"] == 49
    assert len(fake.p.timelines) == 1 and p["timeline_geloescht"] is False    # --keep


def test_probe_failure_keeps_timeline_as_fehler(mek, monkeypatch, capsys):
    fake = FakeResolve()
    monkeypatch.setattr(RA, "connect", lambda: fake)

    def boom(*a, **k):
        raise RuntimeError("API kaputt")
    monkeypatch.setattr(probe, "measure_end_frame", boom)
    assert probe.main([str(mek["dir"])]) == 1
    p = mek["ch"].read_json("probe.json")
    assert p["ok"] is False and "API kaputt" in p["fehler"] and p["traceback"]
    assert p["end_frame_inclusive"] if "end_frame_inclusive" in p else True     # nicht gemessen → kein Schlüssel
    assert "end_frame_inclusive" not in p
    assert fake.p.timelines[0].name.endswith(" FEHLER") and p["timeline"].endswith(" FEHLER")
    assert "FEHLGESCHLAGEN" in capsys.readouterr().err


def test_probe_pick_pair_and_window():
    media = {"format": {"fps": 25}, "clips": {"/fx": {"original": {"nb_frames": 400}}, "/a7": {"original": {"nb_frames": 400}}},
             "ordner": {"X": {"ton": ["/fx"], "kontext": ["/a7"]}}}
    pair = probe.pick_pair(media, None, None)
    assert pair == {"ref": "/fx", "other": "/a7", "offset_frames": 0, "overlap_ref": [0.0, 0.0], "sync": False}
    assert probe.pick_window(pair, media, 25) == (250, 322)
    pair["offset_frames"] = -240          # a7 beginnt 240 Frames später → Fenster muss ≥ 240 starten und in a7 passen
    assert probe.pick_window(pair, media, 25) == (250, 322)
    pair["offset_frames"] = 200           # a7 endet früher: 250+72+200 > 400 → früheres Fenster
    assert probe.pick_window(pair, media, 25) == (25, 97)
    with pytest.raises(AutoCutError, match="Fenster"):
        probe.pick_window(dict(pair, offset_frames=5000), media, 25)
    with pytest.raises(AutoCutError, match="Kamerapaar"):
        probe.pick_pair({"ordner": {"Y": {"ton": ["/fx"], "kontext": []}}}, None, None)


def test_probe_restores_user_timeline_after_success(mek, monkeypatch):
    """WORKFLOW-AutoCut.md „User-Timeline wiederherstellen": gilt auch für resolve_probe.py (main ruft
    session.restore_user_timeline() in einem finally nach run_probe auf)."""
    fake = FakeResolve(FakeProject("MEK"))
    user_tl = fake.p.mp.CreateEmptyTimeline("User")     # Timeline, in der der User gerade arbeitet
    monkeypatch.setattr(RA, "connect", lambda: fake)
    assert probe.main([str(mek["dir"])]) == 0
    assert fake.p.GetCurrentTimeline() is user_tl       # trotz eigener Probe-Timeline (angelegt + gelöscht) wieder aktiv


def test_probe_restores_user_timeline_after_failure(mek, monkeypatch):
    fake = FakeResolve(FakeProject("MEK"))
    user_tl = fake.p.mp.CreateEmptyTimeline("User")
    monkeypatch.setattr(RA, "connect", lambda: fake)

    def boom(*a, **k):
        raise RuntimeError("API kaputt")
    monkeypatch.setattr(probe, "measure_end_frame", boom)
    assert probe.main([str(mek["dir"])]) == 1
    assert fake.p.GetCurrentTimeline() is user_tl       # auch im Fehlerfall (Probe-Timeline bleibt „… FEHLER" stehen)


# --- autocut_build.py ---------------------------------------------------------

def test_build_end_to_end_with_fake(mek, monkeypatch, capsys):
    fake = FakeResolve(FakeProject("MEK"))
    monkeypatch.setattr(RA, "connect", lambda: fake)
    ch = mek["ch"]
    assert build.main([str(mek["dir"]), "--dry-run"]) == 0
    assert ch.read_json("timeline.json") is None and not fake.p.timelines
    ch.write_json("probe.json", {"ok": True, "end_frame_inclusive": True})
    rc = build.main([str(mek["dir"])])
    out = capsys.readouterr().out
    assert rc == 0, out
    t = fake.p.timelines[0]
    assert t.name.startswith("AutoCut video-1-test 20") and t.tracks == {"video": 3, "audio": 1}
    tl = ch.read_json("timeline.json")
    assert tl["timeline"] == t.name and tl["start_frame"] == 90000 and tl["end_frame_inclusive"] is True
    assert tl["fps"] == 25.0 and len(tl["items"]) == 3 and tl["beats"][1]["typ"] == "grafik" and tl["video"] == "video-1-test.md"
    b = ch.read_json("build.json")
    assert b["status"] == "ok" and b["items"] == 3 and b["markers"] == 2 and b["project"] == "MEK"
    assert b["saved"] is True and b["cutlist_hash"] == cutlist_hash(ch.autocut / "cutlist.json")
    assert b["laenge"] == "00:05" and b["laenge_frames"] == 114 and b["bin"] == "AutoCut/video-1-test"
    assert b["bericht"] is None or Path(b["bericht"]).is_file()
    assert b["bau_readback"] and Path(b["bau_readback"]).is_file()
    # Items: V1/A1 (Handles 6/8 Frames um 1,0–2,0 s), V2 mit +50; recordFrame absolut; kein A2 mehr
    assert [(i["trackIndex"], i["mediaType"], i["startFrame"], i["recordFrame"]) for i in t.items] == [
        (1, 1, 19, 90000), (1, 2, 19, 90000), (2, 1, 69, 90000)]
    assert [x.enabled for x in t.tl_items] == [True, True, True]
    assert [m[0] for m in t.markers] == [0, 64]           # #2 Endcard bei 39 (Item-Ende) + 25 (Pause) = 64
    prot = ch.protokoll.read_text(encoding="utf-8")
    assert "AutoCut: Rohschnitt" in prot and t.name in prot and "3 Items" in prot
    assert "Timeline '" in out and "SaveProject ok" in out


def test_build_refuses_unverified_or_changed_cutlist(mek, monkeypatch, capsys):
    connected = []
    monkeypatch.setattr(RA, "connect", lambda: connected.append(1))
    ch = mek["ch"]
    cl = ch.read_json("cutlist.json"); cl["beats"][0]["szene"] = "Geändert"; ch.write_json("cutlist.json", cl)
    assert build.main([str(mek["dir"])]) == 2 and "autocut_verify" in capsys.readouterr().err
    v = ch.read_json("verify.json"); v["cutlist_hash"] = cutlist_hash(ch.autocut / "cutlist.json"); v["ok"] = False
    v["errors"] = ["x"]; ch.write_json("verify.json", v)
    assert build.main([str(mek["dir"])]) == 2 and "nicht ok" in capsys.readouterr().err
    (ch.autocut / "verify.json").unlink()
    assert build.main([str(mek["dir"])]) == 2
    assert connected == [] and ch.read_json("build.json") is None


def test_build_renames_timeline_on_api_failure(mek, monkeypatch, capsys):
    fake = FakeResolve()
    monkeypatch.setattr(RA, "connect", lambda: fake)
    orig_append = RA.ResolveSession.append_items

    def broken(self, timeline, items, media_items, start_frame):
        raise TypeError("Resolve-API: unerwarteter Rückgabewert")
    monkeypatch.setattr(RA.ResolveSession, "append_items", broken)
    assert build.main([str(mek["dir"])]) == 1
    err = capsys.readouterr().err
    assert "FEHLER" in err and "umbenannt" in err
    t = fake.p.timelines[0]
    assert t.name.endswith(" FEHLER")
    b = mek["ch"].read_json("build.json")
    assert b["status"] == "fehler" and b["timeline"] == t.name and b["timeline_umbenannt"] is True
    assert "TypeError" in b["fehler"] and b["traceback"]
    assert mek["ch"].read_json("timeline.json") is None
    assert "Rohschnitt FEHLER" in mek["ch"].protokoll.read_text(encoding="utf-8")
    monkeypatch.setattr(RA.ResolveSession, "append_items", orig_append)


def test_build_precondition_messages(mek, monkeypatch, capsys):
    monkeypatch.setattr(RA, "connect", lambda: FakeResolve())
    ch = mek["ch"]
    Path(mek["fx"]).unlink()
    assert build.main([str(mek["dir"])]) == 2 and "NAS" in capsys.readouterr().err
    Path(mek["fx"]).write_bytes(b"")
    (ch.autocut / "sync.json").unlink()
    assert build.main([str(mek["dir"])]) == 0
    b = ch.read_json("build.json")
    assert any("sync.json fehlt" in w for w in b["warnings"]) and any("probe.json fehlt" in w for w in b["warnings"])
    assert b["items"] == 2      # ohne Sync kein V2/A2
    (ch.autocut / "media.json").unlink()
    assert build.main([str(mek["dir"])]) == 2 and "autocut_prepare" in capsys.readouterr().err


def test_build_dry_run_finds_clips_via_path_map_when_originals_unreachable(mek, capsys, tmp_path):
    """Kern-Szenario von path_map (Critical 1): die Originalpfade (NAS) sind nicht erreichbar, nur die gemappten
    (SSD-)Dateien liegen auf der Platte. Gegenprobe zuerst: ohne path_map bleibt check_files beim ungemappten
    Pfad und bricht weiterhin ab; erst mit path_map in config.yaml läuft --dry-run durch."""
    ch = mek["ch"]
    nas_root = str(tmp_path / "nas")
    ssd_root = str(tmp_path / "ssd")
    for src in (mek["fx"], mek["a7"]):
        dst = Path(src.replace(nas_root, ssd_root))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"")
        Path(src).unlink()
    assert build.main([str(mek["dir"]), "--dry-run"]) == 2
    assert "nicht erreichbar" in capsys.readouterr().err
    (ch.autocut / "config.yaml").write_text(f'path_map:\n  "{nas_root}": "{ssd_root}"\n', encoding="utf-8")
    assert build.main([str(mek["dir"]), "--dry-run"]) == 0
    assert "Probelauf" in capsys.readouterr().out


def test_build_reports_missing_report_module_cleanly(mek, monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_report(name, *a, **k):
        if name == "niro_autocut.report" or (name == "niro_autocut" and a and a[2] and "report" in a[2]):
            raise ImportError("kein report")
        return real_import(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", no_report)
    monkeypatch.setattr(RA, "connect", lambda: FakeResolve())
    assert build.main([str(mek["dir"])]) == 0
    b = mek["ch"].read_json("build.json")
    assert b["bericht"] is None and "report.py" in b["bericht_hinweis"]


def test_build_uses_roh_suffix_and_single_audio_track(mek, monkeypatch, capsys):
    fake = FakeResolve(FakeProject("MEK"))
    monkeypatch.setattr(RA, "connect", lambda: fake)
    ch = mek["ch"]
    ch.write_json("probe.json", {"ok": True, "end_frame_inclusive": True})
    rc = build.main([str(mek["dir"])])
    assert rc == 0
    b = json.loads((mek["dir"] / "_intern" / "autocut" / "build.json").read_text())
    assert b["timeline"].endswith(" (roh)") and b["roh"] is True
    assert b["timeline_final"] == b["timeline"][: -len(" (roh)")]
    t = fake.p.timelines[-1]
    assert t.tracks == {"video": 3, "audio": 1}


# --- autocut_export_xml.py ----------------------------------------------------

def test_export_uses_build_json_and_writes_to_rohschnitt(mek, monkeypatch, capsys):
    fake = FakeResolve()
    monkeypatch.setattr(RA, "connect", lambda: fake)
    ch = mek["ch"]
    assert export.main([str(mek["dir"])]) == 2                     # noch kein Bau
    assert build.main([str(mek["dir"]), "--name", "AutoCut video-1-test 2026-09-04 0905 (roh)"]) == 0
    assert export.main([str(mek["dir"])]) == 0
    out = ch.ergebnisse / "AutoCut video-1-test 2026-09-04 0905 (roh).xml"
    assert out.read_text().startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5">')
    assert fake.p.timelines[0].exports[-1][1] == FakeResolve.EXPORT_FCP_7_XML
    assert ch.read_json("build.json")["export"]["fcp7xml"]["pfad"] == str(out)
    assert export.main([str(mek["dir"]), "--otio"]) == 0 and (ch.ergebnisse / "AutoCut video-1-test 2026-09-04 0905 (roh).otio").exists()
    assert export.main([str(mek["dir"]), "--timeline", "gibt es nicht"]) == 1
    assert "nicht im Projekt" in capsys.readouterr().err
    assert export.safe_filename("A/B:C") == "A-B-C"
    assert "AutoCut: Export" in ch.protokoll.read_text(encoding="utf-8")


def test_export_prefers_finalized_timeline(charge_dir, monkeypatch):
    ch = Charge.open(charge_dir)
    ch.write_json("build.json", {"status": "ok", "timeline": "AutoCut v 2026-09-04 1530 (roh)"})
    ch.write_json("finalize.json", {"status": "ok", "timeline": "AutoCut v 2026-09-04 1530"})
    fake = FakeResolve()
    fake.p.mp.CreateEmptyTimeline("AutoCut v 2026-09-04 1530")
    monkeypatch.setattr(RA, "connect", lambda: fake)
    rc = export.main([str(charge_dir)])
    assert rc == 0 and (ch.ergebnisse / "AutoCut v 2026-09-04 1530.xml").exists()


# --- autocut_read_timelines.py -----------------------------------------------

def test_read_timelines_output_guard_and_content(mek, monkeypatch, tmp_path, capsys):
    fake = FakeResolve(FakeProject("MEK"))
    monkeypatch.setattr(RA, "connect", lambda: fake)
    ch = mek["ch"]
    with pytest.raises(AutoCutError, match="verweigert"):
        readtl.output_allowed(tmp_path / "irgendwo.json")
    with pytest.raises(AutoCutError, match="json"):
        readtl.output_allowed(ch.autocut / "x.txt")
    assert readtl.output_allowed(ch.autocut / "timelines_readback.json") == (ch.autocut / "timelines_readback.json").resolve()
    assert readtl.output_allowed(ch.ergebnisse / "t.json").name == "t.json"
    assert readtl.output_allowed(readtl.PROFILE_DIR / "archiv" / "mek.json").parent.name == "archiv"
    assert readtl.main([str(tmp_path / "irgendwo.json")]) == 1

    assert build.main([str(mek["dir"]), "--name", "AutoCut video-1-test 2026-09-04 0905 (roh)"]) == 0
    out = ch.autocut / "timelines_readback.json"
    assert readtl.main([str(out), "--project-current"]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["project"] == "MEK" and len(data["timelines"]) == 1
    t = data["timelines"][0]
    assert t["name"] == "AutoCut video-1-test 2026-09-04 0905 (roh)" and t["n_items"] == 3
    assert t["tracks"]["V2"]["items"][0]["enabled"] is True and t["markers"]["0"]["name"] == "#1 Hook"
    assert readtl.main([str(out), "--only", "fehlt"]) == 1
    assert readtl.main([str(out), "--limit", "1"]) == 0
    assert "1 Timelines, 3 Items" in capsys.readouterr().out


# --- resolve_probe_xml.py -----------------------------------------------------

def test_probe_xml_runs_against_fake(charge_dir, monkeypatch):
    import importlib.util
    from fake_resolve import FakeResolve
    from niro_autocut.charge import Charge
    from niro_autocut.resolve_api import ResolveSession
    spec = importlib.util.spec_from_file_location("probe_xml", SCRIPTS / "resolve_probe_xml.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ch = Charge.open(charge_dir)
    fx = str(charge_dir.parent / "nas" / "Interviews" / "Anna" / "FX3_0001.MP4")
    media = {"format": {"fps": 25, "width": 3840, "height": 2160},
             "clips": {fx: {"proxy_path": None, "original": {"nb_frames": 7500}}}, "ordner": {"Anna": {"ton": [fx], "kontext": []}}}
    index = {"clips": [{"path": "/nas/B-Roll/Flur/FX3_9.MP4", "datei": "FX3_9.MP4", "fps": 50.0, "dauer_s": 8.0, "proxy": None}]}
    fr = FakeResolve()
    fr.p.mp.fps_by_path["/nas/B-Roll/Flur/FX3_9.MP4"] = "50"
    s = ResolveSession(fr)
    res = mod.run_probe_xml(ch, s, media, index, "AutoCut PROBE XML 120000", keep=False)
    assert res["level_import_ok"] is True and res["speed_import_ok"] is True and res["ok"] is True
    assert res["cleanup"] == {"timelines": True, "clips": True, "folders": True}
    assert (ch.autocut / "probe_xml.json").exists() is False    # schreibt das Skript-main, nicht run_probe_xml
    # Belege fürs Finalisieren (Live 04.09.: vier „Spurname … nicht gesetzt“ auf der importierten End-Timeline):
    # lässt sich der Spurname auf dem Import-Handle setzen, und auf dem frisch geholten GetCurrentTimeline-Handle?
    assert res["tracknames_survive"] is False                      # Fake importiert wie Resolve ohne Spurnamen
    assert res["trackname_set_on_import_handle"] is True and res["trackname_set_on_current_handle"] is True


# --- autocut_place_broll.py (v2: Raster → Plan v2 → Prüfung → Bau) -----------

def _broll_clip(tmp_path: Path, name: str, einstellung: str, ansicht: str, brennweite: str) -> dict:
    """Ein B-Roll-Clip (Original + Proxy als echte, leere Dateien) mit den Abschnittsfeldern des Nachlaufs."""
    p = tmp_path / "nas" / "B-Roll" / "Flur" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    (p.parent / "Proxy").mkdir(exist_ok=True)
    (p.parent / "Proxy" / (p.stem + ".mov")).write_bytes(b"y")
    return {"path": str(p), "datei": name, "ordner": "Flur", "standort": "Standort 1", "dauer_s": 12.0, "fps": 25.0,
            "maengel": [], "qualitaet_gesamt": 4, "personen": {"blick_in_kamera": False},
            "abschnitte": [{"von_s": 0, "bis_s": 12, "verwendbar": True, "qualitaet": 4, "einstellung": einstellung,
                            "perspektive_hoehe": "Augenhöhe", "perspektive_ansicht": ansicht, "brennweite": brennweite,
                            "bewegungsrichtung": "keine", "hauptmotiv": "Flur", "setup_hash": "0" * 16}]}


def _place_setup(charge_dir: Path, tmp_path: Path) -> tuple[Charge, str]:
    """Charge für Stufe 3 v2: Index (drei Flur-Clips), Cutlist, verify, timeline.json, build.json und Plan v2.

    Timeline: Beat 1 (O-Ton, 0–58 Frames = 2,32 s) ist automatisch Ganz-Gesicht (kürzer als full_face_beat_max_s),
    Beat 2 (VO-Platzhalter, 83–283) ist die einzige Lücke danach → Strecke 1 = 58–283 Frames (9,0 s), die drei
    3-s-Shots aus „Standort 1/Flur" füllen sie lückenlos (der letzte wird vom Code auf die Reststrecke gekürzt)."""
    ch = Charge.open(charge_dir)
    index = {"clips": [_broll_clip(tmp_path, "FX3_1.MP4", "Totale", "ohne Person", "weit"),
                       _broll_clip(tmp_path, "FX3_2.MP4", "Halbnah", "seitlich", "normal"),
                       _broll_clip(tmp_path, "FX3_3.MP4", "Detail", "ohne Person", "tele")]}
    ch.write_json("broll_index.json", index)
    cutlist = {"video": "video-1-test.md", "ziel_laenge_s": None, "fps": 25, "format": "16:9", "pause_s": 1.0,
               "beats": [{"nr": "1", "szene": "Hook", "typ": "oton", "person": "Anna", "clip": "/x/FX3.MP4",
                          "cuts": [{"in_s": 1.0, "out_s": 2.0, "text": "Das ist meins."}]},
                         {"nr": "2", "szene": "VO", "typ": "vo", "platzhalter_s": 8.0}],
               "sperren": [], "hinweise": []}
    cpath = ch.write_json("cutlist.json", cutlist)
    ch.write_json("verify.json", {"cutlist_hash": cutlist_hash(cpath), "ok": True, "errors": [], "warnings": []})
    name = "AutoCut video-1-test 2026-09-04 0905 (roh)"
    ch.write_json("timeline.json", {"fps": 25, "total_frames": 283, "markers": [], "timeline": name,
                                    "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 58, "person": "Anna"},
                                              {"nr": "2", "typ": "vo", "rec_in_f": 83, "rec_out_f": 283, "person": None}]})
    ch.write_json("build.json", {"status": "ok", "timeline": name})
    plan = {"version": 2, "video": "video-1-test.md", "fenster": [], "strecken": [
        {"nr": 1, "szenen": [{"ordner": "Standort 1/Flur", "shots": [
            {"clip": "Flur/FX3_1.MP4", "in_s": 0.0, "out_s": 3.0, "grund": "Totale"},
            {"clip": "Flur/FX3_2.MP4", "in_s": 1.0, "out_s": 4.0, "grund": "Halbnah"},
            {"clip": "Flur/FX3_3.MP4", "in_s": 0.0, "out_s": 5.0, "grund": "Detail"}]}]}]}
    (charge_dir / "_intern" / "autocut" / "broll_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return ch, name


def test_place_v2_raster_verify_build(charge_dir, tmp_path, monkeypatch, capsys):
    """Stufe 3 v2: --raster (Fenster/Strecken) → Plan v2 → --verify-only → Bau gegen das Fake-Resolve (Aufbau: _place_setup)."""
    ch, name = _place_setup(charge_dir, tmp_path)

    rc = place.main([str(charge_dir), "--raster"])
    out = capsys.readouterr().out
    assert rc == 0, out
    rpath = charge_dir / "_intern" / "autocut" / "raster.json"
    assert rpath.exists() and (ch.ergebnisse / "video-1-test-raster.md").exists()
    r = json.loads(rpath.read_text(encoding="utf-8"))
    assert [(s["nr"], s["von_f"], s["bis_f"]) for s in r["strecken"]] == [(1, 58, 283)]

    rc = place.main([str(charge_dir), "--verify-only"])
    out = capsys.readouterr().out
    assert rc == 0, out
    v = ch.read_json("broll_verify.json")
    assert v["ok"] is True and v["n_items"] == 3

    fake = FakeResolve(FakeProject("MEK"))
    t = fake.p.mp.CreateEmptyTimeline(name)
    t.tracks = {"video": 2, "audio": 2}
    monkeypatch.setattr(RA, "connect", lambda: fake)
    rc = place.main([str(charge_dir)])
    out = capsys.readouterr().out
    assert rc == 0, out
    bb = ch.read_json("broll_build.json")
    assert bb["status"] == "ok" and len(bb["items"]) == 3 and bb["markers"][0]["color"] == "Cyan"
    assert len(bb["placed"]) == 3 and bb["items"][0]["tempo"] == 1
    assert bb["bau_readback"] and Path(bb["bau_readback"]).is_file()
    assert t.tracks["video"] == 3 and len(t.items) == 3
    assert (ch.ergebnisse / "video-1-test-broll.md").exists()
    assert "B-Roll-Layout v2 auf V3" in ch.protokoll.read_text(encoding="utf-8")


def _place_telemetrie(ch: Charge, tmp_path: Path, kb: dict, zooms: dict | None = None) -> None:
    """telemetrie.json für die Flur-Clips der Stufe-3-Fixture, genau dort, wo TM.laden() sie sucht
    (`_intern/autocut/`). Der ``config_hash`` ist der der Charge — seit der Fix-Welle überspringen Regel 3b
    und 3c Datensätze, die mit anderen Schwellen gemessen wurden."""
    h = TM.config_hash(ch.config["telemetrie"])
    recs = []
    for name, mm in kb.items():
        p = tmp_path / "nas" / "B-Roll" / "Flur" / name
        recs.append({"path": str(p), "clip": p.stem, "quelle": "rtmd", "fps": 25.0, "dauer_s": 12.0,
                     "fenster_s": 2.0, "config_hash": h, "kb_verlauf": [[0.0, mm]],
                     "zooms": (zooms or {}).get(name, []), "fenster": []})
    ch.write_json("telemetrie.json", recs)


def test_place_v2_verify_only_laesst_telemetrie_regeln_wirklich_anschlagen(charge_dir, tmp_path, capsys):
    """Fix-Welle, Fund I1: die Produktionsverdrahtung — autocut_place_broll.py lädt telemetrie.json und gibt
    sie zusammen mit dem telemetrie:-Config-Block an verify_layout — war von keinem Test gedeckt. Die
    Stufe-3-Fixture hatte kein telemetrie.json, TM.laden() lieferte [] und alle drei Regeln waren in jedem
    End-to-End-Test wirkungslos: man konnte `tele` an der Aufrufstelle streichen, ohne dass die Suite es merkte.

    FX3_1 und FX3_2 tragen hier dieselbe KB-Brennweite und stoßen in Strecke 1 direkt aneinander; FX3_2 trägt
    zusätzlich eine schnelle Zoomfahrt im genutzten Bereich (1,0-4,0 s). --verify-only muss beides melden und
    mit Exit 1 enden."""
    ch, _ = _place_setup(charge_dir, tmp_path)
    schnell = [{"von_s": 2.0, "bis_s": 3.0, "von_mm": 74.1, "bis_mm": 25.4, "tempo_max": 242.0,
                "tempo_mittel": 180.0, "urteil": "schnell"}]
    _place_telemetrie(ch, tmp_path, {"FX3_1.MP4": 25.0, "FX3_2.MP4": 25.0, "FX3_3.MP4": 70.0},
                      zooms={"FX3_2.MP4": schnell})
    rc = place.main([str(charge_dir), "--verify-only"])
    out = capsys.readouterr().out
    assert rc == 1, out
    v = ch.read_json("broll_verify.json")
    assert v["ok"] is False
    assert any("dieselbe KB-Brennweite" in e and "FX3_1.MP4" in e and "FX3_2.MP4" in e for e in v["errors"]), v["errors"]
    assert any("schneller Zoom" in e and "FX3_2.MP4" in e for e in v["errors"]), v["errors"]
    assert "dieselbe KB-Brennweite" in out
    # Gegenprobe: mit auseinanderliegenden Brennweiten und ohne Zoomfahrt läuft dieselbe Charge wieder durch —
    # der Exit 1 oben kommt wirklich von den Telemetrie-Regeln, nicht von der Fixture.
    _place_telemetrie(ch, tmp_path, {"FX3_1.MP4": 25.0, "FX3_2.MP4": 50.0, "FX3_3.MP4": 100.0})
    rc = place.main([str(charge_dir), "--verify-only"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert ch.read_json("broll_verify.json")["ok"] is True


def test_place_v2_build_names_v3_when_user_has_another_timeline_open(charge_dir, tmp_path, monkeypatch, capsys):
    """Der User arbeitet parallel in einer anderen Timeline (Eiserne Regel: User-Timeline wiederherstellen). Resolve
    setzt Spurnamen nur auf der aktiven Timeline — der Bau muss die roh-Timeline erst aktivieren, sonst bleibt V3
    unbenannt (Live-Warnung „Spurname V3='B-Roll' nicht gesetzt")."""
    ch, name = _place_setup(charge_dir, tmp_path)
    fake = FakeResolve(FakeProject("MEK"))
    t = fake.p.mp.CreateEmptyTimeline(name)
    t.tracks = {"video": 2, "audio": 2}
    user_tl = fake.p.mp.CreateEmptyTimeline("Schnitt David")      # macht die User-Timeline aktiv
    assert fake.p.current is user_tl
    monkeypatch.setattr(RA, "connect", lambda: fake)
    rc = place.main([str(charge_dir)])
    out = capsys.readouterr().out
    assert rc == 0, out
    bb = ch.read_json("broll_build.json")
    assert t.GetTrackName("video", 3) == "B-Roll"
    assert not any("Spurname" in w for w in bb["warnings"]), bb["warnings"]
    assert len(t.items) == 3 and fake.p.current is user_tl        # gebaut, User-Timeline wiederhergestellt


def test_place_v2_build_refuses_uploaded_timeline(charge_dir, tmp_path, monkeypatch, capsys):
    """F2 (Schluss-Review): Ist die Ziel-Timeline schon nach Replay hochgeladen (uploads.json), darf Stufe 3 nicht
    mehr in sie schreiben — sonst kollidiert der V3-Bau mit der hochgeladenen roh-Timeline. Für weitere Stufen
    braucht es eine neue Version per Neubau; der Lauf darf Resolve dafür gar nicht erst verbinden."""
    ch, name = _place_setup(charge_dir, tmp_path)
    uploads_dir = charge_dir / "_intern" / "replay"
    uploads_dir.mkdir(parents=True)
    (uploads_dir / "uploads.json").write_text(json.dumps([
        {"titel": "T", "timeline": name, "projekt": "MEK", "hochgeladen_am": "2026-09-17T10:00:00",
         "upload_status": "Upload Completed"}]), encoding="utf-8")

    def kein_resolve():
        raise AssertionError("Resolve darf nach einem Upload der Ziel-Timeline nicht mehr verbunden werden")

    monkeypatch.setattr(RA, "connect", kein_resolve)

    rc = place.main([str(charge_dir), "--verify-only"])
    out = capsys.readouterr().out
    assert rc == 0, out                                            # Prüfen bleibt erlaubt, es ist Resolve-frei

    rc = place.main([str(charge_dir)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "hochgeladen" in err and "nicht mehr ändern" in err
    assert ch.read_json("broll_build.json") is None                # keine V3-Items gebaut


@pytest.mark.parametrize("log", ["gescheitert", "kein JSON", "keine Liste"])
def test_place_v2_build_upload_schutz_meldung_bei_unklarem_log(charge_dir, tmp_path, monkeypatch, capsys, log):
    """Rest-Review Punkt 5: replay.ist_hochgeladen schützt auch bei nur gescheiterten Upload-Einträgen und bei
    nicht auswertbarem uploads.json (im Zweifel schützen). Die Meldung darf dann keinen erfolgten Upload behaupten,
    sondern nennt das Log zum Prüfen."""
    ch, name = _place_setup(charge_dir, tmp_path)
    uploads_json = charge_dir / "_intern" / "replay" / "uploads.json"
    uploads_json.parent.mkdir(parents=True)
    gescheitert = json.dumps([{"titel": "T", "timeline": name, "projekt": "MEK", "hochgeladen_am": "2026-09-17T10:00:00",
                               "upload_status": "Upload Failed"}])
    uploads_json.write_text({"kein JSON": "{kaputt", "keine Liste": "{}"}.get(log, gescheitert), encoding="utf-8")

    def kein_resolve():
        raise AssertionError("Resolve darf bei geschützter Ziel-Timeline nicht verbunden werden")

    monkeypatch.setattr(RA, "connect", kein_resolve)
    rc = place.main([str(charge_dir)])
    err = capsys.readouterr().err
    assert rc == 1 and ch.read_json("broll_build.json") is None
    assert "ist nach Replay hochgeladen" not in err
    assert str(uploads_json) in err and "prüfen" in err


def test_place_v2_compact_and_v1_plan_rejected(charge_dir, capsys):
    """--compact nutzt compact_index_v2; ein Plan im alten (v1) Format wird mit Hinweis auf --raster abgelehnt."""
    ch = Charge.open(charge_dir)
    ch.write_json("broll_index.json", {"clips": [_broll_clip(charge_dir.parent, "FX3_1.MP4", "Totale", "ohne Person", "weit")]})
    assert place.main([str(charge_dir), "--compact"]) == 0
    k = ch.read_json("broll_index_kompakt.json")
    assert k["clips"][0]["abschnitte"][0]["einstellung"] == "Totale" and "perspektive" in k["clips"][0]["abschnitte"][0]

    cutlist = {"video": "video-1-test.md", "fps": 25, "format": "16:9", "pause_s": 1.0,
               "beats": [{"nr": "1", "szene": "Hook", "typ": "oton", "person": "Anna",
                          "cuts": [{"in_s": 1.0, "out_s": 2.0}]}]}
    cpath = ch.write_json("cutlist.json", cutlist)
    ch.write_json("verify.json", {"cutlist_hash": cutlist_hash(cpath), "ok": True, "errors": [], "warnings": []})
    ch.write_json("timeline.json", {"fps": 25, "total_frames": 58, "markers": [], "timeline": "AutoCut x",
                                    "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 58, "person": "Anna"}]})
    ch.write_json("broll_plan.json", {"video": "video-1-test.md", "beats": [{"beat_nr": "1", "items": []}]})
    assert place.main([str(charge_dir), "--verify-only"]) == 1
    assert "raster" in capsys.readouterr().err


def _v1_charge_for_raster(charge_dir: Path, ch: Charge) -> None:
    """Charge mit einem alten (v1) broll_plan.json — genau die Form, die auf der echten MEK-Charge lag, als
    --raster noch daran scheiterte."""
    ch.write_json("broll_index.json", {"clips": []})
    cutlist = {"video": "video-1-test.md", "fps": 25, "format": "16:9", "pause_s": 1.0,
               "beats": [{"nr": "1", "szene": "Hook", "typ": "oton", "person": "Anna",
                          "cuts": [{"in_s": 1.0, "out_s": 2.0}]}]}
    cpath = ch.write_json("cutlist.json", cutlist)
    ch.write_json("verify.json", {"cutlist_hash": cutlist_hash(cpath), "ok": True, "errors": [], "warnings": []})
    # total_frames deutlich länger als der (automatisch volle) Hook-Beat allein: sonst wäre der Gesichtsanteil
    # 100 % — außerhalb der harten Grenze (12-23 %), die raster() seit der Review-Fix-Welle selbst meldet, und
    # diese Fixture soll nur die v1-Plan-Toleranz von --raster prüfen, nicht den Gesichtsanteil.
    ch.write_json("timeline.json", {"fps": 25, "total_frames": 300, "markers": [], "timeline": "AutoCut x",
                                    "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 58, "person": "Anna"}]})
    ch.write_json("broll_plan.json", {"video": "video-1-test.md", "beats": [{"beat_nr": "1", "items": []}]})


def test_place_v2_raster_tolerates_stale_v1_plan(charge_dir, capsys):
    """--raster darf an einem alten (v1) broll_plan.json nicht scheitern — genau der Fehler, den --raster beheben
    soll, wenn er selbst erst nach dem Laden des vorhandenen Plans geprüft wird. Außerhalb --raster bleibt der
    v1-Plan weiterhin ein harter Fehler mit Hinweis auf --raster."""
    ch = Charge.open(charge_dir)
    _v1_charge_for_raster(charge_dir, ch)

    rc = place.main([str(charge_dir), "--raster"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Standardfenstern" in out
    assert (charge_dir / "_intern" / "autocut" / "raster.json").exists()

    rc = place.main([str(charge_dir), "--verify-only"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "raster" in err


def test_place_v2_missing_broll_config_key_reported_without_crash(charge_dir, monkeypatch, capsys):
    """Fehlt der effektiven B-Roll-Konfiguration ein Pflichtschlüssel, meldet verify_layout das als Config:-Fehler;
    die separate Fenster-/Platzierungs-Neuberechnung im Skript (für `placed`) muss das erkennen und überspringen,
    statt mit demselben unvollständigen cfg_broll einen rohen KeyError zu werfen."""
    ch = Charge.open(charge_dir)
    ch.write_json("broll_index.json", {"clips": []})
    cutlist = {"video": "video-1-test.md", "fps": 25, "format": "16:9", "pause_s": 1.0,
               "beats": [{"nr": "1", "szene": "Hook", "typ": "oton", "person": "Anna",
                          "cuts": [{"in_s": 1.0, "out_s": 2.0}]}]}
    cpath = ch.write_json("cutlist.json", cutlist)
    ch.write_json("verify.json", {"cutlist_hash": cutlist_hash(cpath), "ok": True, "errors": [], "warnings": []})
    ch.write_json("timeline.json", {"fps": 25, "total_frames": 58, "markers": [], "timeline": "AutoCut x",
                                    "beats": [{"nr": "1", "typ": "oton", "rec_in_f": 0, "rec_out_f": 58, "person": "Anna"}]})
    ch.write_json("broll_plan.json", {"version": 2, "video": "video-1-test.md", "fenster": [], "strecken": []})

    orig = place.effective_broll_cfg

    def kaputt(ch_, profile):
        text, cfg = orig(ch_, profile)
        cfg = dict(cfg)
        del cfg["window_min_s"]
        return text, cfg
    monkeypatch.setattr(place, "effective_broll_cfg", kaputt)

    rc = place.main([str(charge_dir), "--verify-only"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "Config: broll.window_min_s fehlt" in out


def test_place_v2_build_v3_refuses_foreign_timeline():
    """Nur AutoCut-Timelines werden angefasst: die Namensprüfung in build_v3 feuert vor jedem Resolve-Zugriff
    (Bin anlegen, Medien importieren, Tracks, Speichern) — eine leere Items-/Marker-Liste und ein leerer Index
    dürfen keinen anderen Fehler zuerst auslösen."""
    session = RA.ResolveSession(FakeResolve())
    cfg = {"resolve": {"timeline_prefix": "AutoCut"}}
    with pytest.raises(AutoCutError, match="nicht von AutoCut angelegt"):
        place.build_v3(session, "Fremde Timeline", "video-1", [], [], {}, cfg)


def test_check_shot_files_reports_missing_original(tmp_path: Path):
    missing = str(tmp_path / "nas" / "B-Roll" / "Flur" / "FX3_missing.MP4")
    probs = place.check_shot_files([{"clip": missing}], {"clips": []})
    assert len(probs) == 1 and "nicht gefunden" in probs[0]


def test_check_shot_files_reports_missing_proxy(tmp_path: Path):
    p = tmp_path / "nas" / "B-Roll" / "Flur" / "FX3_1.MP4"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    probs = place.check_shot_files([{"clip": str(p)}], {"clips": [{"path": str(p), "proxy": None}]})
    assert len(probs) == 1 and "kein Proxy" in probs[0]


def test_check_shot_files_uses_map_path_for_original_and_proxy(tmp_path: Path):
    """Original und Proxy liegen nur am gemappten (SSD-)Ort; der (NAS-)Originalpfad in placed/index existiert
    nicht (Critical 2). Mit map_path müssen beide Prüfungen am gemappten Pfad laufen und nichts melden; ohne
    map_path bleibt der Pfad ungemappt und die Original-Prüfung schlägt fehl."""
    nas_root = tmp_path / "nas"
    ssd_root = tmp_path / "ssd"
    nas_clip = str(nas_root / "B-Roll" / "Flur" / "FX3_2.MP4")
    ssd_dir = ssd_root / "B-Roll" / "Flur"
    ssd_dir.mkdir(parents=True, exist_ok=True)
    (ssd_dir / "FX3_2.MP4").write_bytes(b"x")
    (ssd_dir / "Proxy").mkdir()
    (ssd_dir / "Proxy" / "FX3_2.mov").write_bytes(b"x")

    def to_ssd(p):
        return str(p).replace(str(nas_root), str(ssd_root))

    placed = [{"clip": nas_clip}]
    index = {"clips": [{"path": nas_clip, "proxy": None}]}
    assert place.check_shot_files(placed, index, map_path=to_ssd) == []
    without = place.check_shot_files(placed, index)
    assert len(without) == 1 and "nicht gefunden" in without[0]


def test_check_shot_files_uses_map_path_for_index_proxy(tmp_path: Path):
    """Minor 2: der Index-Proxy-Zweig (``proxy_mp = map_path(proxy) ...``) war ungetestet — alle drei
    bisherigen Tests setzen den Index-Proxy auf None bzw. ein leeres Clips-Array, der Zweig wurde nie
    betreten. Der Index-Proxy-Name weicht hier absichtlich von der proxy_for-Konvention ab (``anders.mov``
    statt ``<stem>.mov``) und liegt nicht in einem Proxy/-Ordner neben dem Original — nur der gemappte
    Index-Proxy (``proxy_mp``) kann die Prüfung also bestehen, der proxy_for-Rückfall hilft hier nicht."""
    nas_root = tmp_path / "nas"
    ssd_root = tmp_path / "ssd"
    nas_clip = str(nas_root / "B-Roll" / "Flur" / "FX3_3.MP4")
    nas_proxy = str(nas_root / "B-Roll" / "Flur" / "anders.mov")
    ssd_dir = ssd_root / "B-Roll" / "Flur"
    ssd_dir.mkdir(parents=True, exist_ok=True)
    (ssd_dir / "FX3_3.MP4").write_bytes(b"x")
    (ssd_dir / "anders.mov").write_bytes(b"x")
    assert not (ssd_dir / "Proxy").exists()                        # kein Proxy-Ordner neben dem Original

    def to_ssd(p):
        return str(p).replace(str(nas_root), str(ssd_root))

    placed = [{"clip": nas_clip}]
    index = {"clips": [{"path": nas_clip, "proxy": nas_proxy}]}
    assert place.check_shot_files(placed, index, map_path=to_ssd) == []


def test_check_shot_files_missing_proxy_message_uses_mapped_path(tmp_path: Path):
    """Minor 3: die "kein Proxy"-Meldung muss wie die Schwester-Meldung (Zeile darüber) den gemappten Ordner
    nennen, nicht den unerreichbaren NAS-Ordner."""
    nas_root = tmp_path / "nas"
    ssd_root = tmp_path / "ssd"
    nas_clip = str(nas_root / "B-Roll" / "Flur" / "FX3_4.MP4")
    ssd_dir = ssd_root / "B-Roll" / "Flur"
    ssd_dir.mkdir(parents=True, exist_ok=True)
    (ssd_dir / "FX3_4.MP4").write_bytes(b"x")

    def to_ssd(p):
        return str(p).replace(str(nas_root), str(ssd_root))

    placed = [{"clip": nas_clip}]
    index = {"clips": [{"path": nas_clip, "proxy": None}]}
    probs = place.check_shot_files(placed, index, map_path=to_ssd)
    assert len(probs) == 1 and "kein Proxy" in probs[0]
    assert str(ssd_dir) in probs[0] and str(nas_root) not in probs[0]


def test_build_uses_path_map_and_existing_media_items(mek, monkeypatch, tmp_path):
    """config.yaml path_map: die Charge kennt NAS-Pfade, der Media Pool hat die SSD-Items — kein Import nötig.
    Die Original-(NAS-)Dateien existieren absichtlich nicht mehr: nur die gemappten (SSD-)Pfade liegen auf der
    Platte, damit dieser Test wirklich über path_map läuft statt zufällig über den (noch vorhandenen) NAS-Pfad."""
    ch = mek["ch"]
    nas_root = str(tmp_path / "nas")
    ssd_root = str(tmp_path / "ssd")
    (ch.autocut / "config.yaml").write_text(f'path_map:\n  "{nas_root}": "{ssd_root}"\n', encoding="utf-8")
    p = FakeProject()
    mp = p.GetMediaPool()
    for src in (mek["fx"], mek["a7"]):
        dst = Path(src.replace(nas_root, ssd_root))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"")
        Path(src).unlink()
        mp.ImportMedia([str(dst)])
    mp.calls.clear()
    monkeypatch.setattr(build.RA, "connect", lambda: FakeResolve(p))
    assert build.main([str(mek["dir"])]) == 0
    assert not any(c[0] == "ImportMedia" for c in mp.calls)
    tl = p.timelines[-1]
    assert tl.GetItemListInTrack("video", 1)
