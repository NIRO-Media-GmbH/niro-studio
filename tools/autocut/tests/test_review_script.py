"""autocut_review.py gegen das Fake-Resolve und eine temporäre Review-Wurzel: Vorschau, Freigabe, Marken, Render + Ablage,
Wiederherstellung, --datei, --umsetzung, Exit-Codes."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from fake_resolve import FakeItem, FakeProject, FakeResolve
from niro_autocut import resolve_api as RA
from niro_autocut import wiedergabe as W

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PROJEKT = "Kunde Test"
NAME = "AutoCut video-1 2026-09-18 1000 (roh)"
RUHIG = "1\tDaVinci Resolve\tlayer=0\tonscreen=true\t1920x1080\tKunde Test\n"
ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg fehlt")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


review = _load("autocut_review")


def _testvideo(ziel: Path) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x180:rate=25:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(ziel)], check=True)
    return ziel


@pytest.fixture
def welt(basis_charge, monkeypatch, tmp_path):
    fr = FakeResolve(FakeProject(PROJEKT))
    t = fr.p.mp.CreateEmptyTimeline(NAME)
    item = FakeItem("/nas/FX3_1.MP4")
    fr.p.mp.SetSelectedClip(item)
    fr.p.mp.AppendToTimeline([{"mediaPoolItem": item, "startFrame": 0, "endFrame": 99, "recordFrame": 90000,
                               "trackIndex": 1, "mediaType": 1}])
    user = fr.p.mp.CreateEmptyTimeline("User-Timeline")
    user.SetCurrentTimecode("01:00:05:00")
    user_bin = fr.p.mp.AddSubFolder(fr.p.mp.root, "User-Bin")
    fr.p.mp.SetCurrentFolder(user_bin)
    monkeypatch.setattr(RA, "connect", lambda: fr)
    monkeypatch.setattr(W, "fenster_ausgabe", lambda timeout_s=90: RUHIG)
    monkeypatch.setattr(review.RR, "TAKT_S", 0)
    monkeypatch.setattr(review.RR.time, "sleep", lambda s: None)
    (basis_charge / "_intern" / "autocut").mkdir(parents=True)
    (basis_charge / "_intern" / "autocut" / "build.json").write_text(json.dumps({"timeline": NAME, "status": "ok"}), encoding="utf-8")
    nas = tmp_path / "nas" / "NIRO Studio"
    nas.mkdir(parents=True)
    monkeypatch.setenv("NIRO_STUDIO_REPO", str(tmp_path))
    monkeypatch.setenv("NIRO_STUDIO_NAS", str(nas))
    monkeypatch.delenv("NIRO_REVIEW_ROOT", raising=False)
    monkeypatch.setenv("NIRO_REVIEW_CACHE", str(tmp_path / "cache"))
    # Fake-Render schreibt ein echtes MP4, damit ffprobe/ffmpeg der Review-Ablage etwas vorfinden
    if shutil.which("ffmpeg"):
        orig = fr.p.StartRendering

        def start(job_ids=None, interactive=False):
            ok = orig(job_ids, interactive)
            for jid in job_ids or []:
                pass
            for fmt, out, b, h in fr.p.renders:
                _testvideo(Path(out))
            return ok

        fr.p.StartRendering = start
    return {"charge": basis_charge, "fake": fr, "tl": t, "user": user, "user_bin": user_bin, "review": nas / "review"}


def _lauf(w, *extra):
    return review.main([str(w["charge"]), "--project", PROJEKT, *extra])


def _timeline_mit_clip(w, name: str):
    fr = w["fake"]
    t = fr.p.mp.CreateEmptyTimeline(name)
    item = FakeItem("/nas/FX3_1.MP4")
    fr.p.mp.AppendToTimeline([{"mediaPoolItem": item, "startFrame": 0, "endFrame": 99, "recordFrame": 90000,
                               "trackIndex": 1, "mediaType": 1}])
    fr.p.SetCurrentTimeline(w["user"])
    return t


def _review_versionen(w, titel: str, n: int) -> Path:
    """V1…Vn eines Videos liegen schon im Review (frühere Ablagen)."""
    ordner = w["review"] / "Kunde A" / "Projekt B" / titel
    for nr in range(1, n + 1):
        (ordner / f"V{nr}").mkdir(parents=True)
        (ordner / f"V{nr}" / "version.json").write_text(json.dumps({"nr": nr}), encoding="utf-8")
    (ordner / "video.json").write_text(json.dumps({"titel": titel, "kunde": "Kunde A", "projekt": "Projekt B"}), encoding="utf-8")
    return ordner


def test_vorschau_rendert_nichts(welt, capsys):
    assert _lauf(welt, "--vorschau") == 0
    out = capsys.readouterr().out
    assert "Review „video-1“ V1 (nächste Version) · Stufe „Rohschnitt (roh)“" in out and "3840×2160 → 1920×1080" in out
    assert "00:00:04:00 (100 Frames @ 25 fps)" in out
    assert "nichts gerendert" in out and not (welt["charge"] / "Ergebnisse" / "Export" / "Review").exists()
    assert welt["fake"].p.renders == []


def test_vorschau_nennt_naechste_review_version_nicht_die_timeline_version(welt, capsys):
    # Klebl 25.09.: Timeline „01 - Tiefbau_V3“, im Review lagen V1–V8 → abgelegt wurde V9, die Vorschau zeigte „(V3)“
    _timeline_mit_clip(welt, "video-1_V3")
    _review_versionen(welt, "video-1", 8)
    assert _lauf(welt, "--timeline", "video-1_V3", "--vorschau") == 0
    out = capsys.readouterr().out
    assert "„video-1_V3“ → Review „video-1“ V9 (nächste Version) · Stufe „Stand“" in out and "(V3)" not in out
    # zwei Timelines desselben Videos in einem Lauf → fortlaufend
    assert _lauf(welt, "--timeline", "video-1_V3", "--timeline", NAME, "--vorschau") == 0
    out = capsys.readouterr().out
    assert "Review „video-1“ V9 (nächste Version)" in out and "Review „video-1“ V10 (nächste Version)" in out


@ffmpeg
def test_ablage_ohne_version_nimmt_naechste_review_version(welt, capsys):
    _timeline_mit_clip(welt, "video-1_V3")
    ordner = _review_versionen(welt, "video-1", 8)
    assert _lauf(welt, "--timeline", "video-1_V3") == 0
    assert "„video-1_V3“ → Review „video-1“ V9" in capsys.readouterr().out
    v9 = json.loads((ordner / "V9" / "version.json").read_text(encoding="utf-8"))
    assert v9["nr"] == 9 and v9["notiz"] == f"Stand · Timeline „video-1_V3“ · Projekt „{PROJEKT}“"


def test_falsches_projekt_und_marken(welt, capsys):
    assert review.main([str(welt["charge"]), "--project", "Anderes"]) == 1
    assert "freigegeben wurde 'Anderes'" in capsys.readouterr().err
    welt["tl"].mark_in_out = {"video": {"in": 10, "out": 20}}
    assert _lauf(welt) == 1
    assert "In/Out-Marken" in capsys.readouterr().err
    assert welt["tl"].mark_in_out == {"video": {"in": 10, "out": 20}}     # nichts gelöscht


def test_ohne_nas(welt, monkeypatch, capsys):
    monkeypatch.setenv("NIRO_REVIEW_ROOT", str(welt["charge"] / "weg" / "review"))
    assert _lauf(welt) == 2
    assert "NAS nicht verbunden" in capsys.readouterr().err


def test_wiedergabe_blockt(welt, monkeypatch, capsys):
    monkeypatch.setattr(W, "fenster_ausgabe", lambda timeout_s=90: RUHIG + "2\tDaVinci Resolve\tlayer=0\tonscreen=true\t2560x1440\t\n")
    assert _lauf(welt) == 1
    assert "Vollbild-Wiedergabe" in capsys.readouterr().err


@ffmpeg
def test_render_und_ablage(welt, capsys):
    assert _lauf(welt, "--notiz", "erster Rohschnitt") == 0
    out = capsys.readouterr().out
    assert "Review „video-1“ V1" in out and "http://localhost:4711/#/Kunde%20A/Projekt%20B/video-1" in out
    assert "⚠️ 50 Frames im Render, 100 in der Timeline" in out      # Fake-Render ist 2 s, Timeline 100 Frames
    fr = welt["fake"]
    assert fr.p.renders[0][0] == ("mp4", "H265") and fr.p.renders[0][2:] == (1920, 1080)
    assert Path(fr.p.renders[0][1]) == welt["charge"] / "Ergebnisse" / "Export" / "Review" / f"{NAME}.mp4"
    # Wiederherstellung: Timeline, Playhead, Bin, Seite; Queue leer, Preset zurück
    assert fr.p.current is welt["user"] and welt["user"].GetCurrentTimecode() == "01:00:05:00"
    assert fr.p.mp.GetCurrentFolder() is welt["user_bin"] and fr.page == "edit"
    assert fr.p.render_jobs == {} and fr.p.render_presets == []
    # Review-Ablage auf der (temporären) NAS-Wurzel
    ordner = welt["review"] / "Kunde A" / "Projekt B" / "video-1"
    video = json.loads((ordner / "video.json").read_text(encoding="utf-8"))
    assert video["charge"] == "projects/Kunde A/Projekt B/2026-09 Dreh" and video["kunde"] == "Kunde A"
    v1 = json.loads((ordner / "V1" / "version.json").read_text(encoding="utf-8"))
    assert v1["notiz"] == f"Rohschnitt (roh) · Timeline „{NAME}“ · Projekt „{PROJEKT}“ · erster Rohschnitt"
    assert v1["frames"] == 50 and (ordner / "V1" / "video.mp4").is_file() and (ordner / "V1" / "thumb.jpg").is_file()
    protokoll = (welt["charge"] / "Protokoll.md").read_text(encoding="utf-8")
    assert "AutoCut: Review-Ablage" in protokoll and "Review „video-1“ V1" in protokoll
    # zweiter Bau desselben Videos → V2 mit Umsetzung der V1-Kommentare
    from niro_review import kommentare as km
    daten = km.laden(ordner / "V1")
    km.anlegen(daten, "Jan", "Schmatzer raus", frame=10)
    km.speichern(ordner / "V1", daten)
    ums = welt["charge"] / "umsetzung.json"
    ums.write_text(json.dumps({"K1": {"status": "umgesetzt", "antwort": "weg", "tc_neu": "00:00:00:05"}}), encoding="utf-8")
    fein = fr.p.mp.CreateEmptyTimeline("AutoCut video-1 2026-09-18 1100 Feinschnitt")
    fr.p.SetCurrentTimeline(welt["user"])
    assert _lauf(welt, "--timeline", fein.name, "--umsetzung", str(ums)) == 0
    assert "Review „video-1“ V2" in capsys.readouterr().out
    v2 = json.loads((ordner / "V2" / "version.json").read_text(encoding="utf-8"))
    assert v2["basis"] == 1 and v2["notiz"].startswith("Feinschnitt · ")
    assert km.finden(km.laden(ordner / "V1"), "K1")["status"] == "umgesetzt"


@ffmpeg
def test_datei_ohne_resolve(welt, monkeypatch, capsys):
    monkeypatch.setattr(RA, "connect", lambda: (_ for _ in ()).throw(AssertionError("Resolve darf nicht angesprochen werden")))
    datei = _testvideo(welt["charge"] / "Ergebnisse" / "Export" / "Review" / "01 - Vorstellung Wurst & Liebe_V1.mp4")
    assert review.main([str(welt["charge"]), "--datei", str(datei), "--notiz", "vom MacBook"]) == 0
    out = capsys.readouterr().out
    assert "→ Review „01 - Vorstellung Wurst & Liebe“ V1 (Kopie" in out and "Wurst%20%26%20Liebe" in out
    v1 = json.loads((welt["review"] / "Kunde A" / "Projekt B" / "01 - Vorstellung Wurst & Liebe" / "V1" / "version.json").read_text(encoding="utf-8"))
    assert v1["notiz"].startswith("Stand · Timeline „01 - Vorstellung Wurst & Liebe_V1“") and v1["notiz"].endswith("vom MacBook")
    assert review.main([str(welt["charge"]), "--datei", str(welt["charge"] / "fehlt.mp4")]) == 1


def test_umsetzung_nur_eine_timeline(welt, capsys):
    ums = welt["charge"] / "u.json"
    ums.write_text("{}", encoding="utf-8")
    assert _lauf(welt, "--timeline", NAME, "--timeline", "User-Timeline", "--umsetzung", str(ums)) == 1
    assert "genau einer Timeline" in capsys.readouterr().err
