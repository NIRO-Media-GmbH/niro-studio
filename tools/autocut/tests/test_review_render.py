"""review_render: Titel/Stufe/Format, Queue-Lauf gegen das Fake-Resolve (Wiederherstellung, Stillstand-Stopp), Playhead."""
from __future__ import annotations

from pathlib import Path

import pytest

from fake_resolve import FakeProject, FakeResolve
from niro_autocut import review_render as RR
from niro_autocut.charge import AutoCutError


@pytest.mark.parametrize("name,titel", [
    ("AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)", "video-1-taxodia-weg"),
    ("AutoCut video-1-taxodia-weg 2026-09-15 0941", "video-1-taxodia-weg"),
    ("AutoCut Aftermovie 2026-09-18 1220 Feinschnitt", "Aftermovie"),
    ("AutoCut Aftermovie 2026-09-18 1220 Feinschnitt V2", "Aftermovie"),
    ("Taxodia-Weg Messe V2", "Taxodia-Weg Messe"),
    ("01 - Vorstellung Wurst & Liebe_V1", "01 - Vorstellung Wurst & Liebe"),
    ("03_Viele Sprachen, ein Team_V6", "03_Viele Sprachen, ein Team"),
    ("Dold 02 Fokus Bagger und Kran – Entwurf v1 (Claude 2026-09-17)", "Dold 02 Fokus Bagger und Kran"),
    ("Hochformat_Timeline_01", "Hochformat_Timeline_01"),
    ("V3", "V3"),
])
def test_titel_aus_timeline(name, titel):
    assert RR.titel_aus_timeline(name) == titel


@pytest.mark.parametrize("name,stufe", [
    ("AutoCut x 2026-09-18 1220 (roh)", "Rohschnitt (roh)"),
    ("AutoCut x 2026-09-18 1220 Feinschnitt", "Feinschnitt"),
    ("AutoCut x 2026-09-18 1220 Finalisiert", "Finalisiert"),
    ("Dold 02 – Entwurf v1", "Entwurf"),
    ("03_Viele Sprachen, ein Team_V6", "V6"),
    ("Taxodia-Weg Messe V2", "V2"),
    ("Hochformat_Timeline_01", "Stand"),
])
def test_stufe(name, stufe):
    assert RR.stufe_aus_timeline(name) == stufe


def test_zielformat():
    assert RR.zielformat(2160, 3840) == (1080, 1920)
    assert RR.zielformat(3840, 2160) == (1920, 1080)
    assert RR.zielformat(1080, 1920) == (1080, 1920)
    assert RR.zielformat(1920, 1080) == (1920, 1080)
    assert RR.zielformat(4096, 2160) == (1920, 1012)
    assert RR.zielformat(None, None) == (1920, 1080)


def test_notiz_und_dateiname():
    assert RR.notiz_bauen("Feinschnitt", "AutoCut x", "P", "") == "Feinschnitt · Timeline „AutoCut x“ · Projekt „P“"
    assert RR.notiz_bauen("V2", "T", "P", " Musik neu ").endswith(" · Musik neu")
    assert RR.render_dateiname("A/B: C") == "A-B- C"


def _welt(tmp_path):
    fr = FakeResolve(FakeProject("Kunde Test"))
    t1 = fr.p.mp.CreateEmptyTimeline("AutoCut video-1 2026-09-18 1000 (roh)")
    t2 = fr.p.mp.CreateEmptyTimeline("AutoCut video-2 2026-09-18 1001 (roh)")
    user = fr.p.mp.CreateEmptyTimeline("User-Timeline")
    fr.p.SetCurrentTimeline(user)
    return fr, t1, t2, user


def test_queue_rendern_zwei_jobs(tmp_path):
    fr, t1, t2, user = _welt(tmp_path)
    ziel = tmp_path / "Review"
    meldungen = []
    b = RR.queue_rendern(fr, fr.p, {t1.name: t1, t2.name: t2}, ziel, {t1.name: (1080, 1920), t2.name: (1920, 1080)},
                         schlafen=lambda s: None, uhr=iter(range(0, 1000)).__next__, melden=meldungen.append)
    assert set(b["jobs"]) == {t1.name, t2.name} and all(s["JobStatus"] == "Complete" for s in b["jobs"].values())
    assert b["gestoppt"] is None and b["preset_gesichert"] and b["preset_geladen"] and b["preset_geloescht"]
    assert (ziel / f"{t1.name}.mp4").is_file() and (ziel / f"{t2.name}.mp4").is_file()
    assert fr.p.renders[0][0] == ("mp4", "H265") and fr.p.renders[0][2:] == (1080, 1920) and fr.p.renders[1][2:] == (1920, 1080)
    assert fr.p.render_jobs == {} and fr.p.render_presets == []          # eigene Jobs weg, Sicherung geladen + gelöscht
    assert fr.p.render_settings_calls[-1] == {"SelectAllFrames": True}     # Reset noch auf der eigenen Timeline
    assert fr.page == "edit" and fr.p.rendering_started == [["job-1", "job-2"]]
    assert meldungen and "2/2 fertig" in meldungen[-1]


def test_queue_rendern_stopp_bei_stillstand(tmp_path):
    fr, t1, _, _ = _welt(tmp_path)

    def start_ohne_fortschritt(job_ids=None, interactive=False):
        for jid in job_ids or []:
            fr.p.render_jobs[jid]["status"] = {"JobStatus": "Rendering", "CompletionPercentage": 0}
        return True

    fr.p.StartRendering = start_ohne_fortschritt
    zeit = [0.0]

    def uhr():
        zeit[0] += 10.0
        return zeit[0]

    b = RR.queue_rendern(fr, fr.p, {t1.name: t1}, tmp_path / "Review", {t1.name: (1080, 1920)},
                         schlafen=lambda s: None, uhr=uhr, melden=lambda s: None)
    assert b["gestoppt"] and fr.p.render_stopped and fr.p.render_jobs == {} and fr.p.render_presets == []


def test_queue_rendern_raeumt_liegengebliebene_jobs(tmp_path):
    fr, t1, _, _ = _welt(tmp_path)
    ziel = tmp_path / "Review"
    fr.p.SetCurrentTimeline(t1)
    fr.p.SetRenderSettings({"TargetDir": str(ziel), "CustomName": "alt"})
    alt = fr.p.AddRenderJob()
    fr.p.SetRenderSettings({"TargetDir": str(tmp_path / "fremd"), "CustomName": "fremd"})
    fremd = fr.p.AddRenderJob()
    b = RR.queue_rendern(fr, fr.p, {t1.name: t1}, ziel, {t1.name: (1080, 1920)}, schlafen=lambda s: None,
                         uhr=iter(range(0, 1000)).__next__, melden=lambda s: None)
    assert b["jobs_uebrig_geloescht"] == 1 and alt not in fr.p.render_jobs and fremd in fr.p.render_jobs


def test_queue_rendern_fehler_raeumt_auf(tmp_path):
    fr, t1, _, _ = _welt(tmp_path)
    fr.p.AddRenderJob = lambda: ""
    with pytest.raises(AutoCutError):
        RR.queue_rendern(fr, fr.p, {t1.name: t1}, tmp_path / "Review", {t1.name: (1080, 1920)}, schlafen=lambda s: None,
                         uhr=iter(range(0, 1000)).__next__, melden=lambda s: None)
    assert fr.page == "edit" and fr.p.render_presets == [] and getattr(fr.p, "render_jobs", {}) == {}


def test_playhead_ruhig():
    class T:
        def __init__(self, folge):
            self.folge = list(folge)

        def GetCurrentTimecode(self):
            return self.folge.pop(0) if len(self.folge) > 1 else self.folge[0]

    assert RR.playhead_ruhig(None) is True
    assert RR.playhead_ruhig(T(["01:00:00:00", "01:00:00:00"]), schlafen=lambda s: None, uhr=iter(range(100)).__next__) is True
    assert RR.playhead_ruhig(T(["a", "b", "c", "c"]), schlafen=lambda s: None, uhr=iter(range(100)).__next__, melden=lambda s: None) is True
    laeuft = T([str(i) for i in range(1000)])
    assert RR.playhead_ruhig(laeuft, schlafen=lambda s: None, uhr=iter(range(0, 10000, 30)).__next__, max_s=60, melden=lambda s: None) is False
