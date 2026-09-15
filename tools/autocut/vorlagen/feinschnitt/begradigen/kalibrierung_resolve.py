"""Vorlage (Stand 15.09.2026): Resolve-Transform (Pitch/Yaw/Rotation/Zoom/Position) mit einem ArUco-Raster vermessen.

Optional: nur nötig, um das Modell in parameter_berechnen.resolve_h nachzuprüfen (z. B. nach einem Resolve-Update).
Aufruf: tools/autocut/venv/bin/python _intern/begradigen/kalibrierung_resolve.py <Schritt> — Schritte als eigene Prozesse
(der Standbild-Export braucht den Timecode aus einem vorigen Aufruf):
  aufbauen      → raster.png in den eigenen Bin BIN_PFAD, eigene Timeline NAME mit den VARIANTEN, Zustand des Users merken
  zeige <n>     → Kalibrier-Timeline aktiv, Playhead auf Variante n (danach zurueck)
  still <n>     → ExportCurrentFrameAsStill → kalibrierung/still_<n>.png — UNBRAUCHBAR für die Messung: das Standbild enthält
                  die Inspector-Transformationen nicht (15.09.: 12 identische Standbilder); nur zur Dokumentation behalten
  quickexport   → Kalibrier-Timeline kurz aktiv, RenderWithQuickExport (erste ProRes-Vorlage) → kalibrierung/kalibrierung_render.mov,
                  danach Timeline und Bin des Users zurück
  zurueck       → Timeline und Bin des Users wiederherstellen, speichern
  loeschen      → eigene Kalibrier-Timelines NAME/NAME_ALT löschen (nur diese Namen; nicht, solange eine davon aktiv ist)
Ablauf: raster_erzeugen.py → aufbauen → quickexport → Standbilder aus dem Render ziehen (Befehl in kalibrierung_auswerten.py)
→ kalibrierung_auswerten.py → loeschen → aufraeumen_begradigen.py (raster.png aus dem Media Pool) → Render lokal löschen (≈ 1,3 GB).
Eingaben: kalibrierung/raster.png, ../autocut/probe.json (AutoCut-Probe). Ausgaben: kalibrierung/zustand.json
(Timeline-Name + Bin-ID des Users), Render, Konsole mit Readback der gesetzten Transform-Werte.
Schutz: nur im freigegebenen Projekt PROJEKT (Name bei jedem Schritt geprüft), nur eigene Objekte, Zustand des Users wird vor
dem Aufbau gemerkt (bei Wiederholung der Zustand des ersten Versuchs) und wiederhergestellt.
Befunde (Resolve 21.1, 15.09.): Standbilder landen mit ihrer Standarddauer (5 s) in der Timeline, startFrame/endFrame greifen
nicht → LAENGE. Quick Export läuft synchron (Rückgabe JobStatus „Render Complete"), nimmt TargetDir/CustomName als Parameter
und lässt die Deliver-Einstellungen des Users unberührt; Vorlagen: H.264 Master, HyperDeck, H.265 Master, ProRes 422 HQ,
YouTube, Vimeo, TikTok, Presentations, Dropbox, Replay. Die Framerate der neuen Timeline muss zum Projekt passen.
Herkunft: Taxodia-Charge, _intern/begradigen/kalibrierung_resolve.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402

HIER = Path(__file__).resolve().parent / "kalibrierung"

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # in dieser Session freigegebenes Resolve-Projekt (Name exakt wie in Resolve)
NAME = "Claude Transform-Kalibrierung <JJJJ-MM-TT>"  # eigene Kalibrier-Timeline (darf noch nicht existieren)
NAME_ALT = "<Name eines früheren eigenen Kalibrier-Versuchs>"  # wird bei loeschen mit entfernt; Platzhalter lassen, wenn es keinen gibt
BIN_PFAD = ["AutoCut", "<video-kurz>"]  # eigener Media-Pool-Bin für raster.png (Bin des AutoCut-Laufs)
FPS = 25  # Framerate der eigenen Timeline = Projekt-/Feinschnitt-Framerate (feinschnitt_bauen.FPS)
W, H = 3840, 2160  # Auflösung der eigenen Timeline in px = Feinschnitt-Timeline (Pan/Tilt gelten in Timeline-Pixeln)
# ── Ende ANPASSEN ──────────────────────────────────

RASTER = HIER / "raster.png"
ZUSTAND = HIER / "zustand.json"
LAENGE = 5 * FPS  # Resolve setzt Standbilder mit ihrer Standarddauer (5 s) ein, startFrame/endFrame greifen nicht
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
    return f"01:00:{frame // FPS:02d}:{frame % FPS:02d}"


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("aufbauen", "zeige", "still", "quickexport", "zurueck", "loeschen"):
        raise SystemExit("Schritt fehlt: aufbauen | zeige <n> | still <n> | quickexport | zurueck | loeschen — nichts geschrieben.")
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
        folder = s.ensure_bin(BIN_PFAD)
        media = s.import_media([str(RASTER)], folder)
        tl = s.create_timeline(NAME, float(FPS), W, H, "01:00:00:00")
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
