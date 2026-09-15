"""Szenen-Erkennung in Timeline 1 von „Messe Showreel“ (Freigabe User 2026-09-11: direkt in Timeline 1).

Ablauf: Projektname prüfen → Timeline 1 finden → vorher zählen → Timeline.DetectSceneCuts()
→ Item-Anzahl pollen bis stabil → Readback (Lücken, Abdeckung, Schnittliste) → JSON ablegen
→ Timeline des Users wieder aktivieren.
"""
import json
import os
import statistics
import sys
import time

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
os.environ.setdefault("RESOLVE_SCRIPT_API", API)
os.environ.setdefault("RESOLVE_SCRIPT_LIB", LIB)
sys.path.append(os.path.join(API, "Modules"))
import DaVinciResolveScript as dvr  # noqa: E402

EXPECTED_PROJECT = "Messe Showreel"
TIMELINE_NAME = sys.argv[1] if len(sys.argv) > 1 else "Timeline 1"
OUT = ("/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/"
       "2026-09 Hochzeitsmesse/_intern/cut-detection/"
       f"{TIMELINE_NAME.lower().replace(' ', '')}-scene-cuts.json")


def log(**kw):
    print(json.dumps(kw, ensure_ascii=False), flush=True)


def tc(frame, fps):
    f = int(round(frame))
    return f"{f // (3600 * fps):02d}:{f // (60 * fps) % 60:02d}:{f // fps % 60:02d}:{f % fps:02d}"


resolve = dvr.scriptapp("Resolve")
if resolve is None:
    log(fehler="Resolve nicht erreichbar")
    sys.exit(2)
project = resolve.GetProjectManager().GetCurrentProject()
name = project.GetName() if project else None
if name != EXPECTED_PROJECT:
    log(fehler="Projektname weicht von der Freigabe ab – nichts geschrieben", projekt=name)
    sys.exit(2)

tl = None
for i in range(1, project.GetTimelineCount() + 1):
    t = project.GetTimelineByIndex(i)
    if t.GetName() == TIMELINE_NAME:
        tl = t
        break
if tl is None:
    log(fehler=f"{TIMELINE_NAME} nicht gefunden")
    sys.exit(2)

fps = int(round(float(tl.GetSetting("timelineFrameRate"))))


def video_items():
    out = []
    for tr in range(1, tl.GetTrackCount("video") + 1):
        for it in tl.GetItemListInTrack("video", tr) or []:
            out.append({"track": tr, "start": it.GetStart(), "end": it.GetEnd(), "name": it.GetName()})
    return sorted(out, key=lambda x: (x["track"], x["start"]))


def audio_count():
    return sum(len(tl.GetItemListInTrack("audio", tr) or []) for tr in range(1, tl.GetTrackCount("audio") + 1))


before = video_items()
log(schritt="vorher", projekt=name, timeline=tl.GetName(), fps=fps,
    video_items=len(before), audio_items=audio_count())
if len(before) != 1:
    log(fehler="Erwartet genau 1 Video-Item in Timeline 1 – abgebrochen", video_items=len(before))
    sys.exit(2)

user_tl = project.GetCurrentTimeline()
switched = False
try:
    if user_tl is None or user_tl.GetUniqueId() != tl.GetUniqueId():
        project.SetCurrentTimeline(tl)
        switched = True

    t0 = time.time()
    ok = tl.DetectSceneCuts()
    log(schritt="DetectSceneCuts zurückgekehrt", ok=ok, sekunden=round(time.time() - t0, 1))

    # Falls die Analyse asynchron weiterläuft: pollen, bis die Anzahl 30 s stabil ist (max. 30 min).
    last, stable, deadline = -1, 0, time.time() + 30 * 60
    while time.time() < deadline:
        n = len(video_items())
        if n == last:
            stable += 1
        else:
            stable, last = 0, n
            log(schritt="poll", video_items=n, sekunden=round(time.time() - t0, 1))
        if stable >= 6:
            break
        time.sleep(5)

    after = video_items()
    durs = [it["end"] - it["start"] for it in after]
    gaps = [(a["end"], b["start"]) for a, b in zip(after, after[1:]) if b["start"] != a["end"]]
    cuts = [it["start"] for it in after[1:]]
    report = {
        "projekt": name, "timeline": tl.GetName(), "fps": fps,
        "quelle": before[0]["name"],
        "ok": ok, "sekunden": round(time.time() - t0, 1),
        "video_items_vorher": len(before), "video_items_nachher": len(after),
        "audio_items_nachher": audio_count(),
        "abdeckung_vorher": [before[0]["start"], before[0]["end"]],
        "abdeckung_nachher": [after[0]["start"], after[-1]["end"]] if after else None,
        "luecken": gaps[:20], "luecken_anzahl": len(gaps),
        "shot_dauer_frames": {"min": min(durs), "median": statistics.median(durs), "max": max(durs)} if durs else None,
        "schnitte": [{"frame": c, "tc": tc(c, fps)} for c in cuts],
        "shots": [{"nr": i + 1, "start_tc": tc(it["start"], fps), "end_tc": tc(it["end"], fps),
                   "frames": it["end"] - it["start"]} for i, it in enumerate(after)],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    summary = {k: v for k, v in report.items() if k not in ("schnitte", "shots")}
    summary["erste_schnitte"] = [c["tc"] for c in report["schnitte"][:10]]
    summary["json"] = OUT
    log(schritt="fertig", **summary)
finally:
    if switched and user_tl is not None:
        project.SetCurrentTimeline(user_tl)
        log(schritt="User-Timeline wieder aktiv", timeline=user_tl.GetName())
