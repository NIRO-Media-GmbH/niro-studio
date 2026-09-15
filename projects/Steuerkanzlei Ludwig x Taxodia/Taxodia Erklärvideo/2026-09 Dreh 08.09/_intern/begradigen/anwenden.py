"""Begradigung (parameter.json) auf alle Interview-Items des Feinschnitts anwenden (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/anwenden.py [--ausfuehren]
V1 (FX3) und V2 (a7, auch deaktivierte Stücke): Zuordnung über den Clipnamen, daher unabhängig von zwischenzeitlichen
Timing-Änderungen des Users. Der CTA-Punch-in wird an seinen bisherigen Werten (Zoom 1,12, Pan −200) erkannt.
Items mit anderen, von Hand gesetzten Transform-Werten werden übersprungen und gemeldet. Transform-Eigenschaften gelten
auch auf nicht aktiven Timelines (kein Timeline-Wechsel). Ohne --ausfuehren nur Prüfung. Bericht: anwendung.json
(inkl. Vorher-Werte zum Zurücksetzen).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402

HIER = Path(__file__).resolve().parent
PROJEKT = "Taxodia 09.26"
TIMELINE = "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt"
KEYS = ("RotationAngle", "Pitch", "Yaw", "ZoomX", "ZoomY", "Pan", "Tilt")
NEUTRAL = {"RotationAngle": 0.0, "Pitch": 0.0, "Yaw": 0.0, "ZoomX": 1.0, "ZoomY": 1.0, "Pan": 0.0, "Tilt": 0.0}
PUNCH_ALT = {"RotationAngle": 0.0, "Pitch": 0.0, "Yaw": 0.0, "ZoomX": 1.12, "ZoomY": 1.12, "Pan": -200.0, "Tilt": 0.0}


def gleich(a: dict, b: dict, tol: float = 1e-3) -> bool:
    return all(abs(float(a[k]) - float(b[k])) <= tol * max(1.0, abs(float(b[k]))) for k in KEYS)


def main() -> None:
    par = json.loads((HIER / "parameter.json").read_text())
    r = RA.connect()
    pm = r.GetProjectManager()
    p = pm.GetCurrentProject()
    if p.GetName() != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{p.GetName()}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    tl = next((t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == TIMELINE), None)
    if tl is None:
        raise SystemExit("Feinschnitt nicht gefunden.")
    start = tl.GetStartFrame()
    ausfuehren = "--ausfuehren" in sys.argv
    bericht = {"projekt": p.GetName(), "timeline": TIMELINE, "items": [], "uebersprungen": []}
    for spur in (1, 2):
        for x in sorted(tl.GetItemListInTrack("video", spur) or [], key=lambda y: y.GetStart()):
            stem = Path(x.GetName()).stem
            if stem not in par:
                bericht["uebersprungen"].append((f"V{spur}", x.GetStart() - start, x.GetName(), "kein Interview-Clip"))
                continue
            vorher = {k: float(x.GetProperty(k)) for k in KEYS}
            if gleich(vorher, NEUTRAL):
                ziel, art = par[stem]["resolve"], "normal"
            elif gleich(vorher, PUNCH_ALT):
                ziel, art = par[stem]["resolve_punch_in"], "punch-in"
            elif gleich(vorher, par[stem]["resolve"]) or gleich(vorher, par[stem]["resolve_punch_in"]):
                bericht["items"].append({"spur": f"V{spur}", "start": x.GetStart() - start, "clip": stem, "art": "schon begradigt"})
                continue
            else:
                bericht["uebersprungen"].append((f"V{spur}", x.GetStart() - start, x.GetName(), f"eigene Transform-Werte {vorher}"))
                continue
            eintrag = {"spur": f"V{spur}", "start": x.GetStart() - start, "clip": stem, "art": art, "aktiv": bool(x.GetClipEnabled()),
                       "vorher": vorher, "ziel": ziel}
            if ausfuehren:
                eintrag["gesetzt"] = bool(x.SetProperties({k: float(v) for k, v in ziel.items()}))
                eintrag["readback_ok"] = gleich({k: float(x.GetProperty(k)) for k in KEYS}, ziel)
            bericht["items"].append(eintrag)
    if ausfuehren:
        bericht["gespeichert"] = bool(pm.SaveProject())
    arten = {}
    for e in bericht["items"]:
        arten[e["art"]] = arten.get(e["art"], 0) + 1
    bericht["zusammenfassung"] = {"arten": arten, "uebersprungen": len(bericht["uebersprungen"]),
                                  "fehler": [(e["spur"], e["start"]) for e in bericht["items"] if ausfuehren and "gesetzt" in e and not (e["gesetzt"] and e["readback_ok"])]}
    (HIER / ("anwendung.json" if ausfuehren else "anwendung_pruefung.json")).write_text(json.dumps(bericht, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(bericht["zusammenfassung"], ensure_ascii=False), "|", bericht["uebersprungen"][:5])


if __name__ == "__main__":
    main()
