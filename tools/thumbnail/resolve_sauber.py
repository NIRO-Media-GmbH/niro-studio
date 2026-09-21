"""Thumbnail, Resolve-Schritt: eigene Kopie einer Timeline ohne Overlays → Quick Export „ProRes 422 HQ“ → aufräumen.
Spec: docs/superpowers/specs/2026-09-21-thumbnail-design.md („Bildquelle“). Regeln: tools/resolve/WORKFLOW-Resolve.md.

Nur im offenen, exakt genannten Projekt. Legt Bin „Claude Thumbnail <Datum>“ und Timeline „Claude Thumbnail <Video>
<Datum>“ an, schaltet darin Alpha-Clips, Clips ohne Mediendatei (Titel, Generatoren) und SafeZone-Clips sowie alle
Untertitel-Spuren ab, rendert und löscht Kopie und Bin wieder. Timeline, Playhead, Bin und Seite des Users werden
zurückgesetzt, auch nach einem Fehler. Wartet, solange der User abspielt.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402


class ResolveFehler(RuntimeError):
    pass


def _projekt(resolve):
    for _ in range(10):
        p = resolve.GetProjectManager().GetCurrentProject()
        if p is not None:
            return p
        time.sleep(1.0)
    raise ResolveFehler("Resolve liefert kein offenes Projekt.")


def _warten_bis_ruhe(proj, max_s: float = 300.0) -> None:
    t0 = time.time()
    while True:
        tl = proj.GetCurrentTimeline()
        if tl is None:
            return
        a = tl.GetCurrentTimecode()
        time.sleep(0.8)
        if tl.GetCurrentTimecode() == a:
            return
        if time.time() - t0 > max_s:
            raise ResolveFehler("Der User spielt seit 5 min ab — nichts geschrieben.")
        print("  Wiedergabe läuft — warte …", file=sys.stderr, flush=True)
        time.sleep(5)


def ist_overlay(item, spurname: str) -> bool:
    """Alpha-Clip (Remotion-Grafik/-Untertitel), Clip ohne Mediendatei (Text+, Titel, Generator), SafeZone-Spur oder Clip
    mit Composite-Modus ≠ Normal (Film Burns, Light Leaks im Modus Screen/Add — Wurst & Liebe 21.09.2026)."""
    if "SAFEZONE" in (spurname or "").upper():
        return True
    mpi = item.GetMediaPoolItem()
    if mpi is None:
        return True
    if (item.GetProperty("CompositeMode") or 0) not in (0, "0"):
        return True
    return (mpi.GetClipProperty("Alpha mode") or "None") not in ("None", "")


def einstellungen(tl, ausgenommen: set) -> list[dict]:
    """Sichtbare Einstellung je Frame = oberstes aktives Item, das kein Overlay ist → zusammenhängende Segmente."""
    start = int(tl.GetStartFrame())
    n = int(tl.GetEndFrame()) - start
    ebenen = []
    for k in range(int(tl.GetTrackCount("video")), 0, -1):
        for it in tl.GetItemListInTrack("video", k) or []:
            if it.GetUniqueId() in ausgenommen or not it.GetClipEnabled():
                continue
            ebenen.append((k, int(it.GetStart()) - start, int(it.GetEnd()) - start, it.GetName()))
    segmente: list[dict] = []
    for f in range(n):
        e = next((x for x in ebenen if x[1] <= f < x[2]), None)
        sid = f"V{e[0]}@{e[1]}" if e else "leer"
        if segmente and segmente[-1]["id"] == sid and segmente[-1]["ende"] == f:
            segmente[-1]["ende"] = f + 1
        else:
            segmente.append({"id": sid, "spur": f"V{e[0]}" if e else None, "clip": e[3] if e else None, "start": f, "ende": f + 1})
    return segmente


def _zuruecksetzen(proj, tl, tc) -> bool:
    if tl is None:
        return True
    ok = bool(proj.SetCurrentTimeline(tl))
    for _ in range(5):
        time.sleep(0.5)
        if not tc or tl.GetCurrentTimecode() == tc:
            break
        tl.SetCurrentTimecode(tc)
    return ok and (not tc or tl.GetCurrentTimecode() == tc)


def sauberer_master(projekt: str, timeline: str, video: str, ziel: Path) -> dict:
    resolve = RA.connect()
    proj = _projekt(resolve)
    if proj.GetName() != projekt:
        raise ResolveFehler(f"Offenes Projekt „{proj.GetName()}“ ≠ Freigabe „{projekt}“ — nichts geschrieben.")
    quelle = next((proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)
                   if proj.GetTimelineByIndex(i).GetName() == timeline), None)
    if quelle is None:
        raise ResolveFehler(f"Timeline „{timeline}“ fehlt.")
    _warten_bis_ruhe(proj)
    mp = proj.GetMediaPool()
    user_tl = proj.GetCurrentTimeline()
    user_tc = user_tl.GetCurrentTimecode() if user_tl else None
    user_bin = mp.GetCurrentFolder()
    user_seite = resolve.GetCurrentPage()
    anzahl = proj.GetTimelineCount()
    stempel = time.strftime("%Y-%m-%d %H%M")
    out: dict = {"projekt": proj.GetName(), "timeline": timeline,
                 "user": {"timeline": user_tl.GetName() if user_tl else None, "tc": user_tc,
                          "bin": user_bin.GetName() if user_bin else None, "seite": user_seite}}
    bin_ = kopie = None
    try:
        bin_ = mp.AddSubFolder(mp.GetRootFolder(), f"Claude Thumbnail {stempel}")
        if not bin_:
            raise ResolveFehler("Eigener Bin nicht angelegt.")
        mp.SetCurrentFolder(bin_)
        kopie = quelle.DuplicateTimeline(f"Claude Thumbnail {video} {stempel}")
        if not kopie:
            raise ResolveFehler("Kopie der Timeline nicht angelegt.")
        proj.SetCurrentTimeline(kopie)
        time.sleep(1.5)
        start = int(kopie.GetStartFrame())
        overlays, ids, fehler = [], set(), []
        for k in range(1, int(kopie.GetTrackCount("video")) + 1):
            spurname = kopie.GetTrackName("video", k)
            for it in kopie.GetItemListInTrack("video", k) or []:
                if not ist_overlay(it, spurname):
                    continue
                ids.add(it.GetUniqueId())
                overlays.append({"spur": f"V{k}", "start": int(it.GetStart()) - start, "ende": int(it.GetEnd()) - start,
                                 "name": it.GetName()})
                if it.GetClipEnabled():
                    it.SetClipEnabled(False)
                if it.GetClipEnabled():
                    fehler.append(f"V{k} {it.GetName()} @ {int(it.GetStart()) - start}")
        for k in range(1, int(kopie.GetTrackCount("subtitle")) + 1):
            kopie.SetTrackEnable("subtitle", k, False)
        if fehler:
            raise ResolveFehler(f"Overlays ließen sich nicht abschalten: {fehler[:5]}")
        out.update(frames=int(kopie.GetEndFrame()) - start, fps=float(kopie.GetSetting("timelineFrameRate")),
                   overlays=overlays, einstellungen=einstellungen(kopie, ids))
        ziel.mkdir(parents=True, exist_ok=True)
        name = f"{video}_sauber_{stempel.replace(' ', '_')}"
        res = proj.RenderWithQuickExport("ProRes 422 HQ", {"TargetDir": str(ziel), "CustomName": name, "EnableUpload": False})
        out["quick_export"] = res
        if (res or {}).get("JobStatus") != "Render Complete":
            raise ResolveFehler(f"Quick Export nicht fertig: {res}")
        dateien = sorted(ziel.glob(f"{name}*"))
        if len(dateien) != 1:
            raise ResolveFehler(f"Master nicht eindeutig: {dateien}")
        out["master"] = str(dateien[0])
    finally:
        out["ansicht_zurueck"] = _zuruecksetzen(proj, user_tl, user_tc)
        if kopie is not None:
            out["kopie_geloescht"] = bool(mp.DeleteTimelines([kopie]))
        if bin_ is not None:
            out["bin_geloescht"] = bool(mp.DeleteFolders([bin_]))
        if user_bin is not None:
            mp.SetCurrentFolder(user_bin)
        if user_seite and resolve.GetCurrentPage() != user_seite:
            resolve.OpenPage(user_seite)
        out["timelines_danach"] = proj.GetTimelineCount()
    if out["timelines_danach"] != anzahl or not out.get("kopie_geloescht") or not out.get("bin_geloescht"):
        raise ResolveFehler(f"Aufräumen unvollständig: {out}")
    return out
