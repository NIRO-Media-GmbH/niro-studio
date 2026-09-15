"""SFX hörbar machen (User 15.09.: „die SFX Clips sind irgendwie nicht zu hören"): neue Clip-Gains aus pegel_neu.json setzen.
Ziel: SFX-Momentanlautheit −28 LUFS unter Sprache, −24 LUFS in sprachfreien Momenten, Spitze ≤ −10 dBFS.
Zuordnung je Platzierung: gleiche Spur + gleicher Clipname, nächstgelegener Start (≤ 200 Frames, falls der User verschoben hat)."""
import json, sys
from pathlib import Path
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA
HIER = Path(__file__).resolve().parent
neu = json.loads((HIER / "pegel_neu.json").read_text())
r = RA.connect(); pm = r.GetProjectManager(); p = pm.GetCurrentProject()
if p.GetName() != "Taxodia 09.26":
    raise SystemExit("Projekt nicht freigegeben — nichts geschrieben.")
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt")
s = tl.GetStartFrame()
ergebnis, fehler = [], []
benutzt = set()
for n in neu:
    idx = int(n["spur"][1])
    kand = [x for x in (tl.GetItemListInTrack("audio", idx) or []) if x.GetName() == n["sfx"] and x.GetUniqueId() not in benutzt]
    if not kand:
        fehler.append(("nicht gefunden", n["spur"], n["rec_frame"], n["sfx"])); continue
    x = min(kand, key=lambda y: abs((y.GetStart() - s) - n["rec_frame"]))
    if abs((x.GetStart() - s) - n["rec_frame"]) > 200:
        fehler.append(("zu weit verschoben", n["spur"], n["rec_frame"], x.GetStart() - s)); continue
    benutzt.add(x.GetUniqueId())
    vorher = float(x.GetProperty("AudioVolume"))
    ok = bool(x.SetProperties({"AudioVolume": float(n["gain_neu"])}))
    rb = float(x.GetProperty("AudioVolume"))
    ergebnis.append({"spur": n["spur"], "start": x.GetStart() - s, "sfx": n["sfx"], "vorher": vorher, "neu": n["gain_neu"], "gesetzt": ok, "readback": rb})
gesp = bool(pm.SaveProject())
(HIER / "pegel_anhebung.json").write_text(json.dumps({"gespeichert": gesp, "items": ergebnis, "fehler": fehler}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"gesetzt {sum(1 for e in ergebnis if e['gesetzt'] and abs(e['readback'] - e['neu']) < 0.11)}/{len(neu)} | Fehler {fehler} | gespeichert {gesp}")
