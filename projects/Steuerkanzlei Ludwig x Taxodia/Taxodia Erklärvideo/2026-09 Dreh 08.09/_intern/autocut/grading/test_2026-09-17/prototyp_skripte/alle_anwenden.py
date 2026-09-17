"""Schreibt den 5-Node-Baum mit Look C auf alle V1-V3-Items der Grading-Test-Kopie (Freigabe User 17.09.: „kannst alle so machen")."""
import json, sys, time
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA
from niro_autocut import wiedergabe as W

FREIGABE = "Taxodia 09.26"
KOPIE = "AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test"
TEST = "/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/grading/test_2026-09-17/"
DRX = TEST + "T3_basis5_ohne_vorschau.drx"
LUT = "Sony/SLog3SGamut3.CineToLC-709.cube"
NAMEN = ["BALANCE", "ANGLEICH", "KONTRAST/SAT", "LUT", "HAND"]
EINS, NULL = "1.0000 1.0000 1.0000", "0.0000 0.0000 0.0000"
N3 = {"NodeIndex": 3, "Slope": "1.0500 1.0500 1.0500", "Offset": "-0.0205 -0.0205 -0.0205", "Power": EINS, "Saturation": 1.0}

plan = json.load(open("proto/plan_alle.json"))
snap = {(i["spur"], i["start"]): i for i in json.load(open("proto/kopie_items.json"))["items"]}
status = W.status(W.fenster_ausgabe())
if status == "spielt_ab":
    sys.exit("Wiedergabe läuft — nichts geschrieben.")
r = RA.connect()
p = r.GetProjectManager().GetCurrentProject()
if p.GetName() != FREIGABE:
    sys.exit(f"Offenes Projekt '{p.GetName()}' ≠ Freigabe — nichts geschrieben.")
if p.IsRenderingInProgress():
    sys.exit("Resolve rendert — nichts geschrieben.")
k = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == KOPIE)
s = k.GetStartFrame()
aktuell = {}
for ti in (1, 2, 3):
    for x in k.GetItemListInTrack("video", ti) or []:
        aktuell[(ti, x.GetStart() - s)] = x
abw = [key for key in set(snap) | set(aktuell)
       if key not in snap or key not in aktuell or aktuell[key].GetName() != snap[key]["name"]
       or aktuell[key].GetDuration() != snap[key]["dauer"] or aktuell[key].GetLeftOffset() != snap[key]["left"]]
if abw:
    sys.exit(f"Kopie hat sich seit dem Einlesen geändert ({len(abw)} Abweichungen, z. B. {sorted(abw)[:5]}) — nichts geschrieben.")
print("Wiedergabe:", status, "| Projekt ok | Kopie unverändert | Items:", len(plan["items"]), flush=True)
log = {"projekt": p.GetName(), "kopie": KOPIE, "look": plan["look"], "start": time.strftime("%H:%M:%S"), "items": []}
t0 = time.time()
for e in sorted(plan["items"], key=lambda e: (e["spur"], e["start"])):
    x = aktuell[(e["spur"], e["start"])]
    z = {"spur": e["spur"], "start": e["start"], "name": e["name"], "aktiv": e["aktiv"], "quelle": e["quelle"], "n1": e["n1"]}
    z["drx"] = bool(x.GetNodeGraph().ApplyGradeFromDRX(DRX, 0))
    z["n1_ok"] = bool(x.SetCDL({"NodeIndex": 1, "Slope": EINS, "Offset": e["n1"], "Power": EINS, "Saturation": 1.0}))
    z["n2_ok"] = bool(x.SetCDL({"NodeIndex": 2, "Slope": EINS, "Offset": NULL, "Power": EINS, "Saturation": 1.0}))
    z["n3_ok"] = bool(x.SetCDL(N3))
    z["lut_ok"] = bool(x.GetNodeGraph().SetLUT(4, LUT))
    g = x.GetNodeGraph()
    z["readback_ok"] = g.GetNumNodes() == 5 and [g.GetNodeLabel(i) for i in range(1, 6)] == NAMEN and g.GetLUT(4) == LUT
    log["items"].append(z)
    if not all(z[f] for f in ("drx", "n1_ok", "n2_ok", "n3_ok", "lut_ok", "readback_ok")):
        log["abbruch"] = z
        break
log["gespeichert"] = bool(r.GetProjectManager().SaveProject())
log["dauer_s"] = round(time.time() - t0, 1)
log["ok"] = sum(1 for z in log["items"] if z["readback_ok"])
json.dump(log, open(TEST + "einsatz_alle_lookC.json", "w"), indent=1, ensure_ascii=False)
cur = p.GetCurrentTimeline()
print(json.dumps({k2: v for k2, v in log.items() if k2 != "items"}, ensure_ascii=False),
      "| aktiv:", cur.GetName() if cur else None, "| Bin:", p.GetMediaPool().GetCurrentFolder().GetName())
