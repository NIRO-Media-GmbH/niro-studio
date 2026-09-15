"""Vorlage (Stand 15.09.2026): Stand der Videospuren V1–V4 sichern — Positionen, aktiv/deaktiviert, Transform (Readback).

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/stand_lesen.py
Ausgabe: STAND_JSON mit aktiver Timeline und je Spur V1–V4 den Items (start, dauer, left [Frames ab Timeline-Start], clip,
         aktiv; auf V1/V2 zusätzlich RotationAngle, Pitch, Yaw, ZoomX, Pan, Tilt); Konsole: Items und aktive Items je Spur,
         aktive V2-Stücke (Start, Ende, letzte 4 Zeichen des Clips).
Nur lesend; bricht per assert ab, wenn nicht PROJEKT offen ist. Die Timeline wird per Name gesucht, muss nicht aktiv sein.
Zweck: Stand vor und nach einem eigenen Umbau vergleichen — hat der User inzwischen von Hand geändert, nichts überschreiben;
nach einem Abbruch fehlende eigene Items finden. STAND_JSON wird überschrieben (für Vorher/Nachher umbenennen).
Gemessen (Resolve 21.1): Transform-Eigenschaften lassen sich auch auf nicht aktiven Timelines lesen und setzen.

Herkunft: Taxodia-Charge, Session-Scratchpad stand_lesen.py
"""
import sys, json
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts (anderes Projekt offen → Abbruch)
NAME = "<Timeline-Name>"  # exakter Name der zu lesenden Timeline (z. B. die Feinschnitt-Timeline dieser Session)
STAND_JSON = Path(__file__).resolve().parent.parent / "autocut" / "stand.json"  # Ausgabedatei (_intern/autocut/stand.json)
# ── Ende ANPASSEN ──────────────────────────────────

r = RA.connect(); p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == PROJEKT, p.GetName()
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == NAME)
s = tl.GetStartFrame()
K = ("RotationAngle", "Pitch", "Yaw", "ZoomX", "Pan", "Tilt")
out = {"aktiv": p.GetCurrentTimeline().GetName(), "spuren": {}}
for idx in (1, 2, 3, 4):
    items = sorted(tl.GetItemListInTrack("video", idx) or [], key=lambda x: x.GetStart())
    out["spuren"][f"V{idx}"] = [{"start": x.GetStart() - s, "dauer": x.GetDuration(), "left": x.GetLeftOffset(), "clip": Path(x.GetName()).stem,
                                  "aktiv": bool(x.GetClipEnabled()), **({k: round(float(x.GetProperty(k)), 4) for k in K} if idx <= 2 else {})} for x in items]
json.dump(out, open(STAND_JSON, "w"), indent=1)
print("aktiv:", out["aktiv"])
for k, v in out["spuren"].items():
    print(k, len(v), "Items, aktiv:", sum(i["aktiv"] for i in v))
print("V2 aktive Stücke:", [(i["start"], i["start"] + i["dauer"], i["clip"][-4:]) for i in out["spuren"]["V2"] if i["aktiv"]])
