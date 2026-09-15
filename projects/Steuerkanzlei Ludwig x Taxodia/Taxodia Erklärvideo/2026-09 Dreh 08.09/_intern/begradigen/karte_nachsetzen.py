"""Offene Nachbesserung (Flammann a7 2812–3005, Kopf 40 px höher wegen Bachelor-Karte) setzen, sobald Resolve Schreibzugriffe
wieder annimmt: alle 30 s ein Versuch, höchstens 15 min. Nur dieses eine eigene Item; Readback + Speichern (15.09.2026)."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA
HIER = Path(__file__).resolve().parent
K = ("RotationAngle", "Pitch", "Yaw", "ZoomX", "ZoomY", "Pan", "Tilt")
nb = json.loads((HIER / "nachbesserung.json").read_text())
neu, vorher = nb["a7_stueck"]["neu"], nb["a7_stueck"]["vorher"]
for versuch in range(30):
    r = RA.connect(); pm = r.GetProjectManager(); p = pm.GetCurrentProject()
    if p is None or p.GetName() != "Taxodia 09.26":
        print("Projekt nicht offen/freigegeben — Abbruch"); sys.exit(2)
    tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt")
    s = tl.GetStartFrame()
    x = next((i for i in tl.GetItemListInTrack("video", 2) if i.GetStart() - s == 2812), None)
    if x is None:
        print("a7-Stück 2812 nicht mehr da (vom User geändert) — nichts gesetzt"); sys.exit(3)
    jetzt = {k: float(x.GetProperty(k)) for k in K}
    if any(abs(jetzt[k] - vorher[k]) > 1e-3 * max(1, abs(vorher[k])) for k in K):
        print("Transform inzwischen von Hand geändert — nichts gesetzt:", jetzt); sys.exit(4)
    if x.SetProperties({k: float(neu[k]) for k in K}):
        rb = {k: float(x.GetProperty(k)) for k in K}
        ok = all(abs(rb[k] - neu[k]) <= 1e-3 * max(1, abs(neu[k])) for k in K)
        print(f"Versuch {versuch + 1}: gesetzt, Readback {ok}, gespeichert {pm.SaveProject()}", rb)
        if ok:
            kf = json.loads((HIER / "kopf_final.json").read_text())
            for e in kf["v2"]:
                if e["start"] == 2812:
                    e["neu"] = neu; e["nachbesserung"] = "Kopf 40 px höher wegen Bachelor-Karte (nachgesetzt)"
            (HIER / "kopf_final.json").write_text(json.dumps(kf, ensure_ascii=False, indent=1), encoding="utf-8")
            nb["a7_gesetzt"] = True; nb["hinweis"] = f"nachgesetzt nach {versuch + 1} Versuchen"
            (HIER / "nachbesserung.json").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
            sys.exit(0)
    print(f"Versuch {versuch + 1}: Resolve lehnt ab", flush=True)
    time.sleep(30)
sys.exit(1)
