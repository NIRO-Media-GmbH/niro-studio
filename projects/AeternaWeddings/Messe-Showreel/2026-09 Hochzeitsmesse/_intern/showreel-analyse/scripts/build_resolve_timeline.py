"""Stufe E: plan.json → neue Timelines in Resolve (Freigabe: Schreiben erlaubt in „Messe Showreel“, nur anhängen).

Legt an: Bin „Claude Showreel <stamp>“, Timelines „Claude Showreel 5min <stamp>“ und
„Claude Showreel Reserve <stamp>“ (3840×2160, 25p, nur Video, harte Schnitte), Clipfarben je Kategorie,
blaue Block-Marker. Readback gegen den Plan, danach Timeline des Users wieder aktiv.
"""
import datetime
import json
import os
import sys

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
LIB = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
os.environ.setdefault("RESOLVE_SCRIPT_API", API)
os.environ.setdefault("RESOLVE_SCRIPT_LIB", LIB)
sys.path.append(os.path.join(API, "Modules"))
import DaVinciResolveScript as dvr  # noqa: E402

EXPECTED_PROJECT = "Messe Showreel"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PLAN = ARGS[0] if ARGS else ("/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/"
                             "2026-09 Hochzeitsmesse/_intern/showreel-analyse/plan.json")
PREFIX = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--name=")), "Claude Showreel")
NO_RESERVE = "--no-reserve" in sys.argv
SOURCES = {"t1": "Lea & Sebastian Hochzeit_V3.mp4", "t2": "Video_V4.mp4"}


def log(**kw):
    print(json.dumps(kw, ensure_ascii=False), flush=True)


plan = json.load(open(PLAN))
resolve = dvr.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
if project.GetName() != EXPECTED_PROJECT:
    log(fehler="Projektname weicht von der Freigabe ab – nichts geschrieben", projekt=project.GetName())
    sys.exit(2)
mp = project.GetMediaPool()
root = mp.GetRootFolder()
mpis = {}
for clip in root.GetClipList() or []:
    for film, name in SOURCES.items():
        if clip.GetName() == name:
            mpis[film] = clip
if set(mpis) != set(SOURCES):
    log(fehler="Quellclips nicht im Master-Bin gefunden", gefunden=list(mpis))
    sys.exit(2)

user_tl = project.GetCurrentTimeline()
user_folder = mp.GetCurrentFolder()
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H%M")
created = {}
try:
    bin_ = mp.AddSubFolder(root, f"{PREFIX} {stamp}")
    mp.SetCurrentFolder(bin_)

    def new_timeline(name):
        tl = mp.CreateEmptyTimeline(name)
        project.SetCurrentTimeline(tl)
        ok = [tl.SetSetting("useCustomSettings", "1"),
              tl.SetSetting("timelineResolutionWidth", "3840"),
              tl.SetSetting("timelineResolutionHeight", "2160"),
              tl.SetSetting("timelineFrameRate", "25")]
        log(schritt="Timeline angelegt", name=name, settings_ok=ok,
            res=f'{tl.GetSetting("timelineResolutionWidth")}x{tl.GetSetting("timelineResolutionHeight")}',
            fps=tl.GetSetting("timelineFrameRate"))
        return tl

    def append(tl, entries, end_delta):
        # end_delta = gemessene Mehrlänge bei endFrame = src_out (1 → endFrame ist inklusiv)
        infos = [{"mediaPoolItem": mpis[e["film"]], "startFrame": e["src_in"],
                  "endFrame": e["src_out"] - end_delta, "mediaType": 1, "trackIndex": 1}
                 for e in entries]
        items = mp.AppendToTimeline(infos) or []
        for it, e in zip(items, entries):
            it.SetClipColor(e["farbe"])
        return items

    # 1) Semantik von endFrame an einem Probeclip messen (eigenes Objekt, wird sofort wieder gelöscht)
    tl5 = new_timeline(f"{PREFIX} 5min {stamp}")
    created["5min"] = tl5
    probe = plan["showreel"][0]
    items = append(tl5, [probe], 0)
    measured = items[0].GetDuration() if items else None
    if measured is None or abs(measured - probe["frames"]) > 2:
        log(fehler="endFrame-Probe unplausibel – abgebrochen", soll=probe["frames"], gemessen=measured)
        sys.exit(2)
    end_delta = measured - probe["frames"]
    tl5.DeleteClips(items, False)
    log(schritt="endFrame-Probe", soll=probe["frames"], gemessen=measured, end_delta=end_delta,
        rest_items=len(tl5.GetItemListInTrack("video", 1) or []))

    # 2) Showreel komplett anhängen
    items = append(tl5, plan["showreel"], end_delta)
    start = tl5.GetStartFrame()
    rb = tl5.GetItemListInTrack("video", 1) or []
    mism = []
    pos = start
    for it, e in zip(rb, plan["showreel"]):
        if (it.GetStart() != pos or it.GetDuration() != e["frames"]
                or it.GetSourceStartFrame() != e["src_in"]):
            mism.append({"id": e["id"], "start": it.GetStart(), "soll_start": pos, "dauer": it.GetDuration(),
                         "soll_dauer": e["frames"], "src": it.GetSourceStartFrame(), "soll_src": e["src_in"]})
        pos += e["frames"]
    # Block-Marker (relativ zum Timeline-Start)
    off = 0
    for b in range(1, 9):
        block = [e for e in plan["showreel"] if e["block"] == b]
        note = " · ".join(f'{e["slot"]} {e["kategorie"]}' for e in block)
        tl5.AddMarker(off, "Blue", f"Block {b}", note, 1)
        off += sum(e["frames"] for e in block)
    log(schritt="Showreel gebaut", items=len(rb), soll=len(plan["showreel"]),
        ende=tl5.GetEndFrame() - start, soll_frames=sum(e["frames"] for e in plan["showreel"]),
        abweichungen=mism[:10], abweichungen_anzahl=len(mism), marker=len(tl5.GetMarkers() or {}))

    # 3) Reserve
    if NO_RESERVE:
        raise SystemExit(0)
    tlr = new_timeline(f"{PREFIX} Reserve {stamp}")
    created["reserve"] = tlr
    items_r = append(tlr, plan["reserve"], end_delta)
    off, last = 0, None
    for e in plan["reserve"]:
        if e["kategorie"] != last:
            tlr.AddMarker(off, "Blue", e["kategorie"], "", 1)
            last = e["kategorie"]
        off += e["frames"]
    log(schritt="Reserve gebaut", items=len(tlr.GetItemListInTrack("video", 1) or []), soll=len(plan["reserve"]))
finally:
    if user_tl is not None:
        project.SetCurrentTimeline(user_tl)
    if user_folder is not None:
        mp.SetCurrentFolder(user_folder)
    log(schritt="User-Timeline wieder aktiv", timeline=user_tl.GetName() if user_tl else None,
        angelegt={k: v.GetName() for k, v in created.items()})
