"""Review-Ablage nach dem Bau: Timeline über die Render-Queue rendern (H.265, lange Kante ≤ 1920 px) und als Version in
NIRO Review ablegen (tools/review). Ohne Quick Export — der blieb am 18.09.2026 bei 4K-Hochkant-Timelines bei 0 fps stehen
und ließ Resolve abstürzen (tools/resolve/WORKFLOW-Resolve.md). Rezept aus der Wurst-&-Liebe-Charge (resolve_review_render.py).

Reine Logik hier (Titel, Stufe, Zielformat, Queue-Lauf gegen ein Projekt-Objekt), Aufruf in scripts/autocut_review.py.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from .charge import AutoCutError
from .resolve_api import bin_name_for

MAX_KANTE = 1920
STALL_S = 90.0          # ohne Fortschritt → Queue stoppen (Absturz-Vorstufe 18.09.: Job bei 0 fps)
TAKT_S = 3.0
STUFEN_WORTE = ("feinschnitt", "finalisiert", "final", "rohschnitt", "roh", "entwurf", "grading", "review")
_ROH_RE = re.compile(r"\s*\(roh\)\s*$", re.IGNORECASE)
_VERSION_RE = re.compile(r"\s*(?:[–\-_]\s*)?(?:entwurf\s*)?v\d+\s*$", re.IGNORECASE)
_CLAUDE_RE = re.compile(r"\s*[\(\[]\s*claude[^\)\]]*[\)\]]\s*$", re.IGNORECASE)
_STUFE_RE = re.compile(r"\s*[–\-_]?\s*(?:" + "|".join(STUFEN_WORTE) + r")\s*$", re.IGNORECASE)
_STEMPEL_RE = re.compile(r"\s+\d{4}-\d{2}-\d{2} \d{4}(?=\s|$)")


def titel_aus_timeline(name: str, prefix: str = "AutoCut") -> str:
    """Stabiler Video-Titel über alle Bau-Stufen: Präfix, Zeitstempel, „(roh)“, Versionsmarke, „(Claude …)“ und
    Stufenwort am Ende weg. „AutoCut video-1-taxodia-weg 2026-09-15 0941 (roh)“ → „video-1-taxodia-weg“;
    „Taxodia-Weg Messe V2“ → „Taxodia-Weg Messe“; „AutoCut Aftermovie 2026-09-18 1220 Feinschnitt“ → „Aftermovie“."""
    t = name.strip()
    if prefix and t.startswith(prefix + " "):
        t = bin_name_for(t, prefix)
    t = _STEMPEL_RE.sub("", t)          # Zeitstempel auch mitten im Namen („… 2026-09-18 1220 Feinschnitt“)
    for _ in range(3):
        t = _CLAUDE_RE.sub("", t)
        t = _ROH_RE.sub("", t)
        t = _VERSION_RE.sub("", t)
        t = _STUFE_RE.sub("", t)
    t = t.strip(" -–_")
    return t or name.strip()


def stufe_aus_timeline(name: str) -> str:
    """Bau-Stufe für die Notiz. Eine Versionsmarke im Namen („01 - Tiefbau_V3“) ist die Resolve-Zählung, keine Stufe:
    als „V3“ vorn in der Notiz las sie sich wie die Review-Version (Klebl 25.09.2026: abgelegt als V9)."""
    n = name.lower()
    if _ROH_RE.search(name):
        return "Rohschnitt (roh)"
    if "feinschnitt" in n:
        return "Feinschnitt"
    if "final" in n:
        return "Finalisiert"
    if "entwurf" in n:
        return "Entwurf"
    return "Stand"


def zielformat(breite: int | None, hoehe: int | None, max_kante: int = MAX_KANTE) -> tuple[int, int]:
    """Timeline-Format auf max_kante lange Kante verkleinern (nie vergrößern), beide Seiten gerade."""
    b, h = int(breite or 1920), int(hoehe or 1080)
    lang = max(b, h)
    if lang > max_kante:
        f = max_kante / lang
        b, h = int(round(b * f)), int(round(h * f))
    return b - b % 2, h - h % 2


def notiz_bauen(stufe: str, timeline: str, projekt: str, zusatz: str = "") -> str:
    n = f"{stufe} · Timeline „{timeline}“ · Projekt „{projekt}“"
    return f"{n} · {zusatz.strip()}" if zusatz and zusatz.strip() else n


def render_dateiname(timeline: str) -> str:
    return timeline.replace("/", "-").replace(":", "-").strip()


def frames_zaehlen(datei: Path) -> int | None:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(datei)], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except (ValueError, IndexError):
        return None


def queue_rendern(resolve, projekt, timelines: dict, ziel: Path, formate: dict, codec: str = "H265",
                  schlafen=time.sleep, uhr=time.monotonic, melden=print) -> dict:
    """Je Timeline ein Queue-Job (ganze Timeline, MP4/<codec>, Zielformat), alle in einem StartRendering; wartet, bis
    alle fertig sind oder STALL_S ohne Fortschritt vergehen. Deliver-Preset des Users wird gesichert und danach geladen,
    eigene Jobs (auch liegengebliebene mit gleichem Zielordner) gelöscht, Seite wieder die alte.

    timelines: {name: Timeline-Objekt}; formate: {name: (breite, hoehe)}. Rückgabe {"jobs": {name: status}, "sekunden",
    "gestoppt", "preset_geladen"}. Timeline/Playhead des Users stellt der Aufrufer wieder her (Session kennt sie)."""
    seite = resolve.GetCurrentPage()
    sicherung = f"Claude Sicherung {time.strftime('%Y-%m-%d %H%M%S')}"
    bericht: dict = {"jobs": {}, "gestoppt": None, "preset_gesichert": bool(projekt.SaveAsNewRenderPreset(sicherung))}
    jobs: list[tuple[str, str]] = []
    try:
        resolve.OpenPage("deliver")
        for name, tl in timelines.items():
            if not projekt.SetCurrentTimeline(tl):
                raise AutoCutError(f"Timeline '{name}' ließ sich nicht aktivieren — nichts gerendert.")
            schlafen(0.8)
            if not projekt.SetCurrentRenderFormatAndCodec("mp4", codec):
                raise AutoCutError(f"Format mp4/{codec} nicht setzbar — nichts gerendert.")
            b, h = formate[name]
            ok = projekt.SetRenderSettings({"SelectAllFrames": True, "TargetDir": str(ziel), "CustomName": render_dateiname(name),
                                            "ExportVideo": True, "ExportAudio": True, "FormatWidth": int(b), "FormatHeight": int(h)})
            if not ok:
                raise AutoCutError(f"SetRenderSettings für '{name}' abgelehnt — nichts gerendert.")
            job = projekt.AddRenderJob()
            if not job:
                raise AutoCutError(f"AddRenderJob für '{name}' ohne Job-ID — nichts gerendert.")
            jobs.append((name, job))
        t0 = uhr()
        if not projekt.StartRendering([j for _, j in jobs], False):
            raise AutoCutError("StartRendering lieferte False (Deliver-Seite aktiv? Render läuft?) — nichts gerendert.")
        letzter_fortschritt, stand = uhr(), None
        while True:
            schlafen(TAKT_S)
            st = {name: (projekt.GetRenderJobStatus(j) or {}) for name, j in jobs}
            fertig = sum(1 for s in st.values() if s.get("JobStatus") in ("Complete", "Failed", "Cancelled"))
            neu = (fertig, sum(int(s.get("CompletionPercentage") or 0) for s in st.values()))
            if neu != stand:
                stand, letzter_fortschritt = neu, uhr()
                melden(f"  Render {fertig}/{len(jobs)} fertig, {neu[1] // max(1, len(jobs))} %")
            if fertig == len(jobs):
                break
            if uhr() - letzter_fortschritt > STALL_S:
                projekt.StopRendering()
                bericht["gestoppt"] = f"{int(STALL_S)} s ohne Fortschritt — Queue gestoppt"
                break
        bericht["sekunden"] = round(uhr() - t0, 1)
        for name, j in jobs:
            bericht["jobs"][name] = dict(projekt.GetRenderJobStatus(j) or {})
    finally:
        for _, j in jobs:
            projekt.DeleteRenderJob(j)
        rest = [j for j in (projekt.GetRenderJobList() or []) if str(j.get("TargetDir") or "") == str(ziel)]
        bericht["jobs_uebrig_geloescht"] = sum(1 for j in rest if projekt.DeleteRenderJob(j.get("JobId")))
        bericht["preset_geladen"] = bool(projekt.LoadRenderPreset(sicherung))
        bericht["preset_geloescht"] = bool(projekt.DeleteRenderPreset(sicherung))
        projekt.SetRenderSettings({"SelectAllFrames": True})   # noch auf der eigenen Timeline, nie auf der des Users
        if seite:
            resolve.OpenPage(seite)
    return bericht


def playhead_ruhig(timeline, schlafen=time.sleep, uhr=time.monotonic, max_s: float = 60.0, melden=print) -> bool:
    """True, sobald der Playhead der aktiven Timeline zwei Messungen lang steht (User spielt nicht ab)."""
    if timeline is None:
        return True
    t0 = uhr()
    while True:
        a = timeline.GetCurrentTimecode()
        schlafen(0.8)
        if timeline.GetCurrentTimecode() == a:
            return True
        if uhr() - t0 > max_s:
            return False
        melden("  Wiedergabe läuft — warte …")
        schlafen(4.0)
