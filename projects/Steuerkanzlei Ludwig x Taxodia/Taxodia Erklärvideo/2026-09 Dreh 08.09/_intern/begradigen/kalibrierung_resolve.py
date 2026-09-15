"""Resolve-Transform (Pitch/Yaw/Rotation/Zoom/Position) mit einem ArUco-Raster vermessen (Taxodia, 15.09.2026).

Aufruf (tools/autocut/venv/bin/python), Schritte als eigene Prozesse (Standbild-Export braucht den Timecode aus einem
vorigen Aufruf):
  kalibrierung_resolve.py aufbauen      → eigener Bin-Import raster.png, eigene Timeline mit VARIANTEN, Zustand merken
  kalibrierung_resolve.py zeige <n>     → Kalibrier-Timeline aktiv, Playhead auf Variante n
  kalibrierung_resolve.py still <n>     → ExportCurrentFrameAsStill → kalibrierung/still_<n>.png
  kalibrierung_resolve.py zurueck       → Timeline und Bin des Users wiederherstellen, speichern
  kalibrierung_resolve.py loeschen      → eigene Kalibrier-Timeline löschen (nur diese, Name + Session-Zustand geprüft)
Nur im freigegebenen Projekt „Taxodia 09.26"; nur eigene Objekte.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402

HIER = Path(__file__).resolve().parent / "kalibrierung"
PROJEKT = "Taxodia 09.26"
NAME = "Claude Transform-Kalibrierung 2026-09-15 b"
NAME_ALT = "Claude Transform-Kalibrierung 2026-09-15"  # erster Versuch (Standbilder haben feste 125 Frames)
RASTER = HIER / "raster.png"
ZUSTAND = HIER / "zustand.json"
LAENGE = 125  # Resolve setzt Standbilder mit ihrer Standarddauer (5 s) ein, startFrame/endFrame greifen nicht
VARIANTEN = [
    {},
    {"RotationAngle": 5.0},
    {"Pitch": 0.1},
    {"Yaw": 0.1},
    {"Pitch": 0.3},
    {"ZoomX": 1.2, "ZoomY": 1.2},
    {"Pan": 200.0, "Tilt": 100.0},
    {"RotationAngle": 5.0, "Pitch": 0.1, "Yaw": 0.1, "ZoomX": 1.2, "ZoomY": 1.2, "Pan": 200.0, "Tilt": 100.0},
    {"Pitch": -0.1},
    {"Yaw": -0.2},
    {"Pitch": 0.1, "Yaw": 0.1},
    {"RotationAngle": 5.0, "Pitch": 0.1},
]


def sitzung():
    s = RA.ResolveSession(RA.connect(), probe=json.loads((HIER.parent.parent / "autocut" / "probe.json").read_text()))
    if s.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    return s


def tc(frame: int) -> str:
    return f"01:00:{frame // 25:02d}:{frame % 25:02d}"


def main() -> None:
    cmd = sys.argv[1]
    s = sitzung()
    proj, mp = s.project, s.media_pool
    if cmd == "aufbauen":
        if s.find_timeline(NAME):
            raise SystemExit("Kalibrier-Timeline existiert schon.")
        user_tl, user_bin = proj.GetCurrentTimeline(), mp.GetCurrentFolder()
        if ZUSTAND.exists() and user_tl is not None and user_tl.GetName().startswith("Claude Transform-Kalibrierung"):
            alt = json.loads(ZUSTAND.read_text())  # Zustand des Users aus dem ersten Versuch behalten
            user_tl, user_bin = s.find_timeline(alt["user_timeline"]), next((f for f in s.all_folders() if f.GetUniqueId() == alt.get("user_bin_id")), None)
        ZUSTAND.write_text(json.dumps({"user_timeline": user_tl.GetName() if user_tl else None,
                                       "user_bin": user_bin.GetName() if user_bin else None,
                                       "user_bin_id": user_bin.GetUniqueId() if user_bin else None}, ensure_ascii=False))
        folder = s.ensure_bin(["AutoCut", "video-1-taxodia-weg"])
        media = s.import_media([str(RASTER)], folder)
        tl = s.create_timeline(NAME, 25.0, 3840, 2160, "01:00:00:00")
        start = int(tl.GetStartFrame())
        items = [Item("V1", str(RASTER), 0, LAENGE, i * LAENGE, (i + 1) * LAENGE, True, f"v{i}", "kalib", True) for i in range(len(VARIANTEN))]
        added = s.append_items(tl, items, media, start)
        ok = [bool(x.SetProperties(v)) if v else True for x, v in zip(added, VARIANTEN)]
        rb = [{k: x.GetProperty(k) for k in ("RotationAngle", "Pitch", "Yaw", "ZoomX", "ZoomY", "Pan", "Tilt")} for x in added]
        print(json.dumps({"timeline": NAME, "items": len(added), "gesetzt": ok, "readback": rb}, ensure_ascii=False))
    elif cmd == "zeige":
        n = int(sys.argv[2])
        tl = s.find_timeline(NAME)
        if proj.GetCurrentTimeline().GetName() != NAME:
            proj.SetCurrentTimeline(tl)
        print("Timecode gesetzt:", tl.SetCurrentTimecode(tc(n * LAENGE + LAENGE // 2)), tl.GetCurrentTimecode())
    elif cmd == "still":
        n = int(sys.argv[2])
        time.sleep(0.8)
        ziel = HIER / f"still_{n}.png"
        ok = proj.ExportCurrentFrameAsStill(str(ziel))
        print("Still", n, ok, ziel.exists(), proj.GetCurrentTimeline().GetCurrentTimecode())
    elif cmd == "quickexport":
        # Standbild-Export enthält die Inspector-Transformationen nicht (15.09.: 12 identische Stills) → echter Render.
        # Quick Export nimmt Ziel und Namen als Parameter und lässt die Deliver-Einstellungen des Users unberührt.
        z = json.loads(ZUSTAND.read_text())
        tl = s.find_timeline(NAME)
        vorlagen = proj.GetQuickExportRenderPresets() or []
        vorlage = next((v for v in vorlagen if "prores" in v.lower()), None) or next((v for v in vorlagen if "264" in v), None)
        print("Vorlagen:", vorlagen, "→", vorlage, flush=True)
        try:
            proj.SetCurrentTimeline(tl)
            time.sleep(1.0)
            status = proj.RenderWithQuickExport(vorlage, {"TargetDir": str(HIER), "CustomName": "kalibrierung_render", "EnableUpload": False})
            print("Quick Export:", status, flush=True)
        finally:
            user = s.find_timeline(z["user_timeline"]) if z["user_timeline"] else None
            if user is not None:
                proj.SetCurrentTimeline(user)
            ordner = next((f for f in s.all_folders() if f.GetUniqueId() == z.get("user_bin_id")), None)
            if ordner is not None:
                mp.SetCurrentFolder(ordner)
            print("zurück:", proj.GetCurrentTimeline().GetName(), mp.GetCurrentFolder().GetName())
    elif cmd == "zurueck":
        z = json.loads(ZUSTAND.read_text())
        tl = s.find_timeline(z["user_timeline"]) if z["user_timeline"] else None
        if tl is not None:
            proj.SetCurrentTimeline(tl)
        ordner = next((f for f in s.all_folders() if f.GetUniqueId() == z.get("user_bin_id")), None)
        if ordner is not None:
            mp.SetCurrentFolder(ordner)
        print(json.dumps({"aktiv": proj.GetCurrentTimeline().GetName(), "bin": mp.GetCurrentFolder().GetName(),
                          "gespeichert": s.save_project()}, ensure_ascii=False))
    elif cmd == "loeschen":
        tls = [t for t in (s.find_timeline(NAME), s.find_timeline(NAME_ALT)) if t is not None]
        if not tls:
            raise SystemExit("Keine Kalibrier-Timeline.")
        if proj.GetCurrentTimeline().GetName() in (NAME, NAME_ALT):
            raise SystemExit("Kalibrier-Timeline ist aktiv — erst zurueck.")
        print("gelöscht:", [t.GetName() for t in tls], mp.DeleteTimelines(tls), "gespeichert:", s.save_project())


if __name__ == "__main__":
    main()
