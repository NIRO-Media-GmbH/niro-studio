"""Grading-Vorschlag (grading_vorschlag.json) auf die Feinschnitt-Timeline anwenden und gegenprüfen (Taxodia, 15.09.2026).

Aufruf (tools/autocut/venv/bin/python):
  _intern/color/grading_anwenden.py --test     → nur das erste V1-Item (FX3_0222) graden, LUT exportieren, mit Modell vergleichen
  _intern/color/grading_anwenden.py --alle     → alle Items auf V1–V3 graden (V4 Grafik bleibt unberührt), Readback, Prüf-LUTs je Gruppe

Umsetzung (Variante A des Vorschlags): Node 1 = SetCDL (Gesamt-CDL je Kamera/Set, Log vor LUT) + SetLUT Sony LC-709.
Nur eigene Timeline-Items im Projekt „Taxodia 09.26", aktive Farbversion (lokal) des Items; Media-Pool-Clips bleiben unverändert.
Keine neue Farbversion: die Stabilisierung könnte an der Version hängen. Prüfung: Resolve exportiert den Clip-Grade als 33er-LUT;
der wird mit CDL → Sony-LUT (colorlib, trilinear) im Bereich echter S-Log3-Werte (0,05–0,80) verglichen.
Schreibt _intern/color/grading_einsatz.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HIER = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
sys.path.insert(0, str(HIER / "skripte"))
from niro_autocut import resolve_api as RA  # noqa: E402
import colorlib as CL  # noqa: E402

PROJEKT = "Taxodia 09.26"
TIMELINE = "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt"
LUT_REL = "Sony/SLog3SGamut3.CineToLC-709.cube"
LUT_ABS = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/" + LUT_REL
GRUPPEN = {"FX3_0222": ("Ludwig", "FX3"), "a7MK4_20260908_0118": ("Ludwig", "a7_IV"), "FX3_0223": ("Flammann", "FX3"),
           "a7MK4_20260908_0119": ("Flammann", "a7_IV"), "FX3_0228": ("Hein", "FX3"), "a7MK4_20260908_0752": ("Hein", "a7_IV")}


def cdl_fuer(vorschlag: dict, clipname: str) -> tuple[str, dict]:
    stem = Path(clipname).stem
    if stem in GRUPPEN:
        person, cam = GRUPPEN[stem]
        return f"{person} {cam}", vorschlag["cdl_je_kamera_und_set"][person][cam]["node1_gesamt_log_vor_LUT"]
    if stem.startswith("C0"):
        b = vorschlag["b_roll_FX3A"]
        werte = b.get("node1_gesamt_log_vor_LUT") or b.get("cdl_gesamt") or b
        return "B-Roll FX3A", werte
    raise SystemExit(f"Clip {clipname}: keine Gruppe im Vorschlag — nichts geschrieben.")


def mit_trim(w: dict, blenden: float) -> dict:
    """Belichtungs-Trim in Blenden vor der CDL: Offset += k · STOP · Slope (S-Log3, 1 Blende = 0,07695)."""
    if not blenden:
        return w
    return {**w, "offset": [o + blenden * CL.STOP * s for o, s in zip(w["offset"], w["slope"])], "resolve_SetCDL": None}


def resolve_cdl(w: dict) -> dict:
    r = w.get("resolve_SetCDL") or {}
    return {"NodeIndex": 1, "Slope": r.get("Slope") or " ".join(f"{v:.4f}" for v in w["slope"]),
            "Offset": r.get("Offset") or " ".join(f"{v:.4f}" for v in w["offset"]),
            "Power": r.get("Power") or "1.0000 1.0000 1.0000", "Saturation": float(r.get("Saturation", w.get("saturation", 1.0)))}


def modell_vergleich(cube_pfad: Path, w: dict) -> dict:
    ist = CL.load_cube(str(cube_pfad))  # [b,g,r,3]
    n = ist.shape[0]
    g = np.linspace(0, 1, n, dtype=np.float32)
    bb, gg, rr = np.meshgrid(g, g, g, indexing="ij")
    rgb = np.stack([rr, gg, bb], -1)
    soll = CL.apply_lut(CL.cdl(rgb, w["slope"], w["offset"], w.get("power", (1, 1, 1)), w.get("saturation", 1.0)), CL.load_cube(LUT_ABS))
    maske = (rgb >= 0.05).all(-1) & (rgb <= 0.80).all(-1)
    d = np.abs(ist - soll)[maske] * 255
    dz = np.abs(ist - soll).reshape(-1, 3).max(-1) * 255
    return {"punkte": int(maske.sum()), "mittel_8bit": round(float(d.mean()), 2), "p95_8bit": round(float(np.percentile(d, 95)), 2),
            "max_8bit": round(float(d.max()), 2), "max_gesamtwuerfel_8bit": round(float(dz.max()), 2)}


def main() -> None:
    modus = "--alle" if "--alle" in sys.argv else "--test"
    vorschlag = json.loads((HIER / "grading_vorschlag.json").read_text())
    r = RA.connect()
    pm = r.GetProjectManager()
    p = pm.GetCurrentProject()
    if p.GetName() != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{p.GetName()}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    tl = next((t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == TIMELINE), None)
    if tl is None:
        raise SystemExit("Feinschnitt-Timeline nicht gefunden — nichts geschrieben.")
    start = tl.GetStartFrame()
    spuren = next((a.split("=")[1].split(",") for a in sys.argv if a.startswith("--spuren=")), ["V1", "V2", "V3"])
    items = [(f"V{i}", x) for i in (1, 2, 3) if f"V{i}" in spuren
             for x in sorted(tl.GetItemListInTrack("video", i) or [], key=lambda y: y.GetStart())]
    if modus == "--test":
        items = items[:1]
    trims_pfad = HIER / "broll_trims.json"
    trims = {int(k): v["blenden"] for k, v in json.loads(trims_pfad.read_text()).items()} if trims_pfad.exists() else {}
    out = {"projekt": p.GetName(), "timeline": TIMELINE, "modus": modus, "aktiv": p.GetCurrentTimeline().GetName(), "items": []}
    export = HIER / "resolve_export"
    export.mkdir(exist_ok=True)
    geprueft = set()
    for spur, x in items:
        gruppe, w = cdl_fuer(vorschlag, x.GetName())
        if spur == "V3" and (x.GetStart() - start) in trims:
            w = mit_trim(w, trims[x.GetStart() - start])
        graph = x.GetNodeGraph()
        vorher = {"nodes": graph.GetNumNodes(), "lut": graph.GetLUT(1), "version": x.GetCurrentVersion()}
        ok_cdl = bool(x.SetCDL(resolve_cdl(w)))
        ok_lut = bool(graph.SetLUT(1, LUT_REL)) or bool(graph.SetLUT(1, LUT_ABS))
        eintrag = {"spur": spur, "start": x.GetStart() - start, "clip": x.GetName(), "gruppe": gruppe, "vorher": vorher,
                   "cdl_gesetzt": ok_cdl, "lut_gesetzt": ok_lut, "lut_readback": x.GetNodeGraph().GetLUT(1)}
        if gruppe not in geprueft and ok_cdl and ok_lut:
            pfad = export / f"{gruppe.replace(' ', '_')}.cube"
            if x.ExportLUT(r.EXPORT_LUT_33PTCUBE, str(pfad)) and pfad.exists():
                eintrag["vergleich_modell"] = modell_vergleich(pfad, w)
                geprueft.add(gruppe)
            else:
                eintrag["vergleich_modell"] = "ExportLUT fehlgeschlagen"
        out["items"].append(eintrag)
        print(f"{spur} {eintrag['start']:>5} {x.GetName():<28} {gruppe:<16} CDL {ok_cdl} LUT {ok_lut} {eintrag.get('vergleich_modell', '')}", flush=True)
    out["gespeichert"] = bool(pm.SaveProject())
    out["fehlgeschlagen"] = [(e["spur"], e["start"]) for e in out["items"] if not (e["cdl_gesetzt"] and e["lut_gesetzt"])]
    (HIER / "grading_einsatz.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "items"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
