"""B-Roll final (User 17.09.): lineare Verstaerkung als 1D-LUT in Node 01 (CDL Node 01 neutral), ein Wert je Clip,
Lichterschutz-Toleranz 5 % (ohne Sensor-Clip), keine Blendengrenze, kein Toe. Nur V3 der Grading-Test-Kopie."""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/color/skripte")
from niro_autocut import resolve_api as RA
from niro_autocut import wiedergabe as W
import colorlib as CL

FREIGABE = "Taxodia 09.26"
KOPIE = "AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test"
LUTROOT = Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT")
LUTREL_DIR = "NIRO Grading/Taxodia 09.26"
SONY = "Sony/SLog3SGamut3.CineToLC-709.cube"
NAMEN = ["BALANCE", "ANGLEICH", "KONTRAST/SAT", "LUT", "HAND"]
EINS, NULL = "1.0000 1.0000 1.0000", "0.0000 0.0000 0.0000"
TEST = Path("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/grading/test_2026-09-17")
N1D = 4096

clips = json.load(open("proto/plan_broll_t05.json"))["clips"]
snap = [i for i in json.load(open("proto/kopie_items.json"))["items"] if i["spur"] == 3]
v2 = {(i["spur"], i["start"]): i for i in json.load(open("proto/plan_alle_v2.json"))["items"]}


def lut_1d(e, wr, wb):
    x = np.linspace(0.0, 1.0, N1D)
    g = 2.0 ** np.array([e + wr, e, e + wb])
    with np.errstate(invalid="ignore", divide="ignore"):
        y = np.stack([CL.lin_to_slog3(CL.slog3_to_lin(x) * gc) for gc in g], -1)
    return np.clip(np.nan_to_num(y), 0.0, 1.0)


# 1) LUTs schreiben
(LUTROOT / LUTREL_DIR).mkdir(parents=True, exist_ok=True)
lut_je_clip = {}
for name, c in sorted(clips.items()):
    w = c["werte"]
    datei = f"{Path(name).stem}_e{w['e']:+.2f}_r{w['wr']:+.2f}_b{w['wb']:+.2f}.cube"
    y = lut_1d(w["e"], w["wr"], w["wb"])
    with open(LUTROOT / LUTREL_DIR / datei, "w") as fh:
        fh.write(f'TITLE "NIRO BALANCE {Path(name).stem} e {w["e"]:+.2f} R {w["wr"]:+.2f} B {w["wb"]:+.2f} (lineare Verstaerkung S-Log3)"\n')
        fh.write(f"LUT_1D_SIZE {N1D}\n")
        for r, g, b in y:
            fh.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    lut_je_clip[name] = f"{LUTREL_DIR}/{datei}"
print("LUTs:", len(lut_je_clip))

# 2) Resolve
if W.status(W.fenster_ausgabe()) == "spielt_ab":
    sys.exit("Wiedergabe läuft — nichts geschrieben.")
r = RA.connect()
p = r.GetProjectManager().GetCurrentProject()
if p.GetName() != FREIGABE or p.IsRenderingInProgress():
    sys.exit("Projekt/Render — nichts geschrieben.")
print("RefreshLUTList:", p.RefreshLUTList())
seite = r.GetCurrentPage()
k = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == KOPIE)
s = k.GetStartFrame()
akt = {x.GetStart() - s: x for x in (k.GetItemListInTrack("video", 3) or [])}
cur = p.GetCurrentTimeline()
tc = cur.GetCurrentTimecode() if cur else None
print("Seite", seite, "| aktiv", cur.GetName() if cur else None, "| TC", tc, flush=True)
log = {"seite": seite, "tc_user": tc, "items": []}
for it in snap:
    x = akt.get(it["start"])
    z = {"start": it["start"], "name": it["name"], "werte": clips[it["name"]]["werte"], "lut1": lut_je_clip[it["name"]]}
    if x is None or x.GetName() != it["name"] or x.GetLeftOffset() != it["left"] or x.GetDuration() != it["dauer"]:
        z["status"] = "Item fehlt/anders — ausgelassen"; log["items"].append(z); continue
    g = x.GetNodeGraph()
    if not (g.GetNumNodes() == 5 and [g.GetNodeLabel(i) for i in range(1, 6)] == NAMEN and g.GetLUT(4) == SONY and not g.GetToolsInNode(5) and not g.GetLUT(1)):
        z["status"] = "Baum verändert — ausgelassen"; log["items"].append(z); continue
    z["cdl1_neutral"] = bool(x.SetCDL({"NodeIndex": 1, "Slope": EINS, "Offset": NULL, "Power": EINS, "Saturation": 1.0}))
    z["lut1_gesetzt"] = bool(x.GetNodeGraph().SetLUT(1, z["lut1"]))
    z["lut1_readback"] = x.GetNodeGraph().GetLUT(1)
    z["status"] = "gesetzt" if z["cdl1_neutral"] and z["lut1_gesetzt"] and z["lut1_readback"] == z["lut1"] else "FEHLER"
    log["items"].append(z)
    print(f"V3 {it['start']:>5} {it['name']:<10} e {z['werte']['e']:+.2f} {z['status']} {z['lut1_readback']}", flush=True)
    if z["status"] == "FEHLER":
        break
log["gespeichert"] = bool(r.GetProjectManager().SaveProject())
json.dump(log, open(TEST / "einsatz_broll_final_lut1d.json", "w"), indent=1, ensure_ascii=False)
from collections import Counter
print(Counter(z["status"] for z in log["items"]), "| gespeichert", log["gespeichert"])
