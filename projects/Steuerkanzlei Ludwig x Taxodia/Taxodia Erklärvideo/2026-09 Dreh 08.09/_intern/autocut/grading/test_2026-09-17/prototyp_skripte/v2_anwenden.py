"""Node 01 neu (Blendengrenze aufgehoben, User 17.09.) fuer Items mit |de| > 0,05 oder |dR|/|dB| > 0,03; vorher Handaenderungs-Pruefung."""
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
TEST = Path("/Users/jansantos/NIRO Studio/projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/_intern/autocut/grading/test_2026-09-17")
LUTREL = "Sony/SLog3SGamut3.CineToLC-709.cube"
NAMEN = ["BALANCE", "ANGLEICH", "KONTRAST/SAT", "LUT", "HAND"]
EINS = "1.0000 1.0000 1.0000"
LUT = CL.load_cube(CL.LUTDIR + "SLog3SGamut3.CineToLC-709.cube")
P = 420 / 1023

v1 = {(i["spur"], i["start"]): i for i in json.load(open("proto/plan_alle.json"))["items"]}
v2 = {(i["spur"], i["start"]): i for i in json.load(open("proto/plan_alle_v2.json"))["items"]}
ziele = [k for k in v2 if abs(v2[k]["werte"]["e"] - v1[k]["werte"]["e"]) > 0.05
         or abs(v2[k]["werte"]["wr"] - v1[k]["werte"]["wr"]) > 0.03 or abs(v2[k]["werte"]["wb"] - v1[k]["werte"]["wb"]) > 0.03]


def modell_lut(n1, n=33):
    g = np.linspace(0, 1, n, dtype=np.float32)
    bb, gg, rr = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([rr, gg, bb], -1)
    y = rgb + np.array([float(v) for v in n1.split()], np.float32)
    y = 1.05 * y + P * (1 - 1.05)
    return CL.apply_lut(np.clip(y, 0, 1), LUT), rgb


def hand_geaendert_lut(item, n1_alt, pfad):
    if not item.ExportLUT(r.EXPORT_LUT_33PTCUBE, str(pfad)) or not pfad.exists():
        return None
    ist = CL.load_cube(str(pfad))
    soll, rgb = modell_lut(n1_alt)
    m = (rgb >= 0.05).all(-1) & (rgb <= 0.80).all(-1)
    return float(np.percentile(np.abs(ist - soll)[m] * 255, 95))


if W.status(W.fenster_ausgabe()) == "spielt_ab":
    sys.exit("Wiedergabe läuft — nichts geschrieben.")
r = RA.connect()
p = r.GetProjectManager().GetCurrentProject()
if p.GetName() != FREIGABE or p.IsRenderingInProgress():
    sys.exit(f"Projekt '{p.GetName()}' / Render läuft — nichts geschrieben.")
seite = r.GetCurrentPage()
k = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == KOPIE)
s = k.GetStartFrame()
akt = {(ti, x.GetStart() - s): x for ti in (1, 2, 3) for x in (k.GetItemListInTrack("video", ti) or [])}
cur = p.GetCurrentTimeline()
print("Seite:", seite, "| aktiv:", cur.GetName() if cur else None, "| Ziel-Items:", len(ziele), flush=True)
exp_dir = TEST / "exportlut_handcheck"
exp_dir.mkdir(exist_ok=True)
log = {"seite": seite, "items": []}
for key in sorted(ziele):
    x = akt.get(key)
    z = {"spur": key[0], "start": key[1], "name": v2[key]["name"], "e_alt": v1[key]["werte"]["e"], "e_neu": v2[key]["werte"]["e"]}
    if x is None or x.GetName() != v2[key]["name"]:
        z["status"] = "Item fehlt/anders — ausgelassen"
        log["items"].append(z); continue
    g = x.GetNodeGraph()
    struktur_ok = g.GetNumNodes() == 5 and [g.GetNodeLabel(i) for i in range(1, 6)] == NAMEN and g.GetLUT(4) == LUTREL and not g.GetToolsInNode(5)
    z["struktur_ok"] = struktur_ok
    if not struktur_ok:
        z["status"] = "Baum verändert (Nodes/Namen/LUT/Hand-Node) — ausgelassen"
        log["items"].append(z); continue
    if seite == "color":
        p95 = hand_geaendert_lut(x, v1[key]["n1"], exp_dir / f"V{key[0]}_{key[1]}.cube")
        z["exportlut_p95"] = None if p95 is None else round(p95, 2)
        if p95 is None or p95 > 2.0:
            z["status"] = "Grade weicht vom gesetzten Stand ab (von Hand geändert?) — ausgelassen"
            log["items"].append(z); continue
    z["n1_neu"] = v2[key]["n1"]
    z["gesetzt"] = bool(x.SetCDL({"NodeIndex": 1, "Slope": EINS, "Offset": v2[key]["n1"], "Power": EINS, "Saturation": 1.0}))
    g = x.GetNodeGraph()
    z["readback_ok"] = g.GetNumNodes() == 5 and g.GetLUT(4) == LUTREL
    z["status"] = "gesetzt" if z["gesetzt"] and z["readback_ok"] else "FEHLER"
    log["items"].append(z)
    print(f"V{key[0]} {key[1]:>5} {z['name']:<10} e {z['e_alt']:+.2f} → {z['e_neu']:+.2f}  {z['status']}  {z.get('exportlut_p95', '')}", flush=True)
    if z["status"] == "FEHLER":
        break
log["gespeichert"] = bool(r.GetProjectManager().SaveProject())
json.dump(log, open(TEST / "einsatz_v2_ohne_blendengrenze.json", "w"), indent=1, ensure_ascii=False)
from collections import Counter
print(Counter(z["status"] for z in log["items"]), "| gespeichert:", log["gespeichert"])
