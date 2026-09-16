"""readback.py + autocut_readback.py: Bau-Readback schreiben und laden (Fake-Resolve)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from fake_resolve import FakeItem, FakeProject, FakeResolve
from niro_autocut import readback as RB
from niro_autocut import resolve_api as RA
from niro_autocut.charge import Charge

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
NAME = "AutoCut video-1 2026-09-17 1000"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_mit_timeline():
    fr = FakeResolve(FakeProject("Kunde Test"))
    t = fr.p.mp.CreateEmptyTimeline(NAME)
    item = FakeItem("/nas/FX3_1.MP4")
    fr.p.mp.SetSelectedClip(item)
    fr.p.mp.AppendToTimeline([{"mediaPoolItem": item, "startFrame": 0, "endFrame": 99, "recordFrame": 90000,
                               "trackIndex": 1, "mediaType": 1}])
    t.AddMarker(10, "Blue", "#1 Hook", "", 1)
    return fr, t


def test_schreiben_und_laden(basis_charge):
    ch = Charge.open_basis(basis_charge)
    fr, t = _fake_mit_timeline()
    p = RB.schreiben(ch, RA.ResolveSession(fr), t)
    assert p == ch.autocut / "readback" / f"{NAME}.json"
    snap = RB.laden(ch, NAME)
    assert snap["timeline"] == NAME and snap["laenge"] == 100 and snap["projekt"] == "Kunde Test"
    assert snap["spuren"]["V1"][0]["start"] == 0 and snap["spuren"]["V1"][0]["dauer"] == 100
    assert snap["marker"]["10"]["name"] == "#1 Hook"
    assert RB.laden(ch, "gibt es nicht") is None


def test_skript(basis_charge, monkeypatch, capsys):
    fr, t = _fake_mit_timeline()
    monkeypatch.setattr(RA, "connect", lambda: fr)
    skript = _load("autocut_readback")
    assert skript.main([str(basis_charge), "--timeline", NAME]) == 0
    assert (basis_charge / "_intern" / "autocut" / "readback" / f"{NAME}.json").is_file()
    assert skript.main([str(basis_charge), "--timeline", "fehlt"]) == 2
    assert "nicht im offenen Projekt" in capsys.readouterr().err
