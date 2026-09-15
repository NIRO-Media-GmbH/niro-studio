"""Vorlage (Stand 15.09.2026): Kopfposition beider Perspektiven (FX3 B + a7 A) auf eine gemeinsame, personenübergreifend einheitliche Stelle legen.

User-Wunsch (15.09.2026): „Du kannst auch beide verschieben um sie anzugleichen … so wie es am besten aussieht und relativ
einheitlich über alle Personen hinweg ist".
Aufruf: tools/autocut/venv/bin/python _intern/begradigen/kopf_beide.py [--ziel=X,Y_a7,Y_fx3] [--ausfuehren]
Daten: synchrone Proxy-Frames aus kopf_angleichen.py (kopf/frames, Apple Vision), Transform-Werte live aus Resolve;
Abbruch, wenn V1/V2 vom Feinschnitt-Plan abweichen.
1. Kopf je Kamera und FX3-Stück (Median über 5 synchrone Zeitpunkte), Gesichtshöhe für den Kopfraum.
2. Gemeinsames Ziel T = (s·X, Y) für alle Personen (s = SEITE je Clip), gesucht auf einem Raster: je Stück kleinster Zoom
   beider Kameras mit voller Bildfüllung und Kopfraum (Schädeldach geschätzt aus KOPF_OBEN bleibt KOPFRAUM px im Bild);
   Bewertung = 90-%-Wert des jeweils größeren Zooms + Mittelwert, leichte Vorliebe für Augen nahe der oberen Drittellinie.
   --ziel=X,Y_a7,Y_fx3 (px @Timeline, Mitte = 0, − = oben): seitlich exakt gleich, Höhe je Perspektive vorgegeben.
3. Je Item: Begradigung (Rotation/Pitch/Yaw) bleibt, Zoom + Position neu. Stücke ohne a7 (z. B. CTA) auf dasselbe Ziel,
   Punch-in-Stücke behalten ihren Faktor parameter_berechnen.PUNCH["zoom"].
Ohne --ausfuehren nur Rechnung + Prüfbild kopf_beide_vergleich_X<X>_a<Y_a7>_b<Y_fx3>.jpg und kopf_beide_plan.json;
mit --ausfuehren setzen + Readback + speichern, Bericht kopf_beide.json (inkl. Vorher-Werte).
Wichtig für kopf_final.py/nachbesserung.py: deren Basis sind die „vorher"-Werte (= begradigt) aus kopf_beide.json. Ohne
Zwischenschritt in Resolve: kopf_beide.py ohne --ausfuehren laufen lassen und kopf_beide_plan.json als kopf_beide.json
kopieren. kopf_beide.json danach nie mehr überschreiben (sonst wären die „vorher"-Werte nicht mehr begradigt).
Überholt durch kopf_final.py (Kopfraum per Gesichtsbox geschätzt, 20 px reichten nicht); Modul `kb` (daten, werte_fuer,
SEITE, subprocess, ka, pb, W, H) für kopf_final.py und nachbesserung.py.
Herkunft: Taxodia-Charge, _intern/begradigen/kopf_beide.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ka", HIER / "kopf_angleichen.py")
ka = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ka)
fb, pb, RA = ka.fb, ka.pb, ka.RA
W, H = ka.W, ka.H

# ── ANPASSEN je Charge ─────────────────────────────
SEITE = {  # Clip-Stamm → Seite der Kopfmitte: +1 = rechts der Bildmitte, −1 = links (nach Blickrichtung, Blickraum vor dem Gesicht);
    # "FX3_0001": 1, "a7MK4_JJJJMMTT_0001": 1,   (Pflicht für jeden FX3-Clip auf V1; a7-Einträge nur zur Doku im Bericht)
}
KOPFRAUM = 20.0  # Standard (15.09.): px (Timeline) über dem geschätzten Schädeldach müssen im Bild bleiben
KOPF_OBEN = 0.95  # Standard (15.09.): Schädeldach ≈ 0,95 Gesichtshöhen über der Kopfmitte (Vision-Box: Brauen bis Kinn); Personenmaske ergab ≈ 1,0
# ── Ende ANPASSEN ──────────────────────────────────


def zmin(w: dict, kopf: tuple, gesicht_h: float, ziel: tuple, z_start: float = 1.0) -> float:
    basis = pb.resolve_h(w["Pitch"], w["Yaw"], w["RotationAngle"], 1.0, 0.0, 0.0)
    qx, qy = ka.abbilden(basis, kopf[0], kopf[1])

    def deckt(z):
        tx, ty = ziel[0] - z * qx, ziel[1] - z * qy
        return pb.deckt(pb.resolve_h(w["Pitch"], w["Yaw"], w["RotationAngle"], z, tx, -ty)) >= 0

    # Füllung wird mit mehr Zoom leichter, der Kopfraum schwerer → erst kleinster füllender Zoom, dann Kopfraum prüfen
    if deckt(z_start):
        z = z_start
    else:
        lo, hi = z_start, 3.5
        if not deckt(hi):
            return float("inf")
        for _ in range(28):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if deckt(mid) else (mid, hi)
        z = hi
    oben = ziel[1] - z * KOPF_OBEN * gesicht_h
    return z if oben >= -H / 2 + KOPFRAUM else float("inf")


def werte_fuer(w: dict, kopf: tuple, ziel: tuple, z: float) -> dict:
    basis = pb.resolve_h(w["Pitch"], w["Yaw"], w["RotationAngle"], 1.0, 0.0, 0.0)
    qx, qy = ka.abbilden(basis, kopf[0], kopf[1])
    z = z + 0.0008
    return {**w, "ZoomX": round(z, 4), "ZoomY": round(z, 4), "Pan": round(ziel[0] - z * qx, 1), "Tilt": round(-(ziel[1] - z * qy), 1)}


def daten():
    tl_json, shots = fb.lade()
    p, _ = fb.plan(tl_json, shots)
    fehlend = sorted({Path(v.clip).stem for v in p["V1"]} - SEITE.keys())
    if fehlend:
        raise SystemExit(f"SEITE im ANPASSEN-Block von kopf_beide.py fehlt für: {fehlend} — nichts geschrieben.")
    r = RA.connect()
    pm = r.GetProjectManager()
    proj = pm.GetCurrentProject()
    if proj.GetName() != fb.PROJEKT:
        raise SystemExit("Projekt nicht freigegeben — nichts geschrieben.")
    tl = next(t for t in (proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)) if t and t.GetName() == ka.TIMELINE)
    start = tl.GetStartFrame()
    live = {}
    for idx in (1, 2):
        for x in tl.GetItemListInTrack("video", idx) or []:
            live[(f"V{idx}", x.GetStart() - start)] = (x, {k: float(x.GetProperty(k)) for k in ka.KEYS}, x.GetLeftOffset(), x.GetDuration())
    for spur, liste in (("V1", p["V1"]), ("V2", p["V2_voll"])):
        for it in liste:
            e = live.get((spur, it.rec_in_f))
            if e is None or e[2] != it.src_in_f or e[3] != it.rec_out_f - it.rec_in_f:
                raise SystemExit(f"{spur} bei {it.rec_in_f} weicht vom Plan ab — erst abstimmen.")
    tsv = subprocess.run([str(ka.INTERN / "gesichtscheck" / "faces"), str(ka.FRAMES)], capture_output=True, text=True, check=True).stdout
    kopf = {}
    for z in tsv.splitlines():
        name, _, rest = z.partition("\t")
        boxen = [tuple(map(float, b.split(","))) for b in rest.split(";")] if rest and rest != "ERR" else []
        boxen = [b for b in boxen if b[4] >= 0.5]
        if boxen:
            x0, y0, x1, y1, _ = max(boxen, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            kopf[name] = (((x0 + x1) / 2 - 0.5) * W, ((y0 + y1) / 2 - 0.08 * (y1 - y0) - 0.5) * H, (y1 - y0) * H)
    # Stücke: FX3-Item + zugehörige a7-Stücke, Köpfe als Median der synchronen Proben
    stuecke = []
    for v in p["V1"]:
        a7 = [s for s in p["V2_voll"] if s.rec_in_f < v.rec_out_f and v.rec_in_f < s.rec_out_f]
        dauer = v.rec_out_f - v.rec_in_f
        fs = [v.rec_in_f + int((k + 1) * dauer / 6) for k in range(5)]
        b = [kopf[f"b_{f:05d}.jpg"] for f in fs if f"b_{f:05d}.jpg" in kopf]
        a = [kopf[f"a_{f:05d}.jpg"] for f in fs if f"a_{f:05d}.jpg" in kopf]
        if not b:
            # Stück ohne a7 (z. B. CTA): eigene Proben holen
            for f in fs:
                jpg = ka.FRAMES / f"b_{f:05d}.jpg"
                ka.frame_holen(v.clip, (v.src_in_f + f - v.rec_in_f) / ka.FPS, jpg)
            continue
        stuecke.append({"v1": v, "a7": a7, "b": tuple(np.median(np.array(b), axis=0)), "a": tuple(np.median(np.array(a), axis=0)) if a else None})
    # Stücke ohne a7: Proben wurden ggf. gerade geholt → Gesichter nachladen
    fehlende = [v for v in p["V1"] if not any(s["v1"] is v for s in stuecke)]
    if fehlende:
        tsv = subprocess.run([str(ka.INTERN / "gesichtscheck" / "faces"), str(ka.FRAMES)], capture_output=True, text=True, check=True).stdout
        for z in tsv.splitlines():
            name, _, rest = z.partition("\t")
            boxen = [tuple(map(float, bb.split(","))) for bb in rest.split(";")] if rest and rest != "ERR" else []
            boxen = [bb for bb in boxen if bb[4] >= 0.5]
            if boxen:
                x0, y0, x1, y1, _ = max(boxen, key=lambda bb: (bb[2] - bb[0]) * (bb[3] - bb[1]))
                kopf[name] = (((x0 + x1) / 2 - 0.5) * W, ((y0 + y1) / 2 - 0.08 * (y1 - y0) - 0.5) * H, (y1 - y0) * H)
        for v in fehlende:
            dauer = v.rec_out_f - v.rec_in_f
            b = [kopf[f"b_{v.rec_in_f + int((k + 1) * dauer / 6):05d}.jpg"] for k in range(5) if f"b_{v.rec_in_f + int((k + 1) * dauer / 6):05d}.jpg" in kopf]
            if b:
                stuecke.append({"v1": v, "a7": [], "b": tuple(np.median(np.array(b), axis=0)), "a": None})
    stuecke.sort(key=lambda s: s["v1"].rec_in_f)
    return p, pm, tl, live, stuecke


def main() -> None:
    ausfuehren = "--ausfuehren" in sys.argv
    p, pm, tl, live, stuecke = daten()
    erzwungen = [a for a in sys.argv if a.startswith("--ziel=")]
    if erzwungen:
        # --ziel=X,Y_a7,Y_fx3: seitlich exakt gleich, Höhe je Perspektive (a7-Nahe: Augen auf der oberen Drittellinie)
        X, Ya, Yb = (int(v) for v in erzwungen[0].split("=")[1].split(","))
    else:
        # Rastersuche gemeinsames Ziel (gleiche Höhe in beiden Perspektiven)
        kandidaten = []
        for X in range(0, 901, 50):
            for Y in range(-700, -149, 25):
                zs, maxe = [], []
                for s_ in stuecke:
                    stem_b = Path(s_["v1"].clip).stem
                    ziel = (SEITE[stem_b] * X, Y)
                    wb = live[("V1", s_["v1"].rec_in_f)][1]
                    zb = zmin({**wb, "ZoomX": 1.0}, s_["b"][:2], s_["b"][2], ziel)
                    za = 1.0
                    if s_["a"] is not None:
                        wa = live[("V2", s_["a7"][0].rec_in_f)][1]
                        za = zmin({**wa, "ZoomX": 1.0}, s_["a"][:2], s_["a"][2], ziel)
                    zs += [zb, za]
                    maxe.append(max(zb, za))
                if not np.all(np.isfinite(maxe)):
                    continue
                score = float(np.percentile(maxe, 90)) + 0.5 * float(np.mean(zs)) + 0.0006 * abs(Y - 30 - (-H / 6)) + 0.0002 * abs(X - 450)
                kandidaten.append((score, X, Y, float(np.percentile(maxe, 90)), float(np.mean(zs)), float(max(maxe))))
        kandidaten.sort()
        for k in kandidaten[:8]:
            print(f"  {k[0]:.3f}  X ±{k[1]}  Y {k[2]}  p90 {k[3]:.3f}  Mittel {k[4]:.3f}  max {k[5]:.3f}")
        _, X, Y, *_ = kandidaten[0]
        Ya = Yb = Y
    # Werte je Item
    params = json.loads((HIER / "parameter.json").read_text())
    neu_v1, neu_v2 = {}, {}
    for s_ in stuecke:
        v = s_["v1"]
        stem_b = Path(v.clip).stem
        ziel_b, ziel_a = (SEITE[stem_b] * X, Yb), (SEITE[stem_b] * X, Ya)
        wb = live[("V1", v.rec_in_f)][1]
        punch_in = params[stem_b]["resolve_punch_in"]  # None ohne Punch-in (parameter_berechnen.PUNCH = None)
        punch = punch_in is not None and abs(wb["ZoomX"] - punch_in["ZoomX"]) < 1e-3
        zb = zmin({**wb, "ZoomX": 1.0}, s_["b"][:2], s_["b"][2], ziel_b)
        if punch:
            zb *= pb.PUNCH["zoom"]
        neu_v1[v.rec_in_f] = werte_fuer(wb, s_["b"][:2], ziel_b, zb)
        for a7 in s_["a7"]:
            wa = live[("V2", a7.rec_in_f)][1]
            if s_["a"] is not None:
                neu_v2[a7.rec_in_f] = werte_fuer(wa, s_["a"][:2], ziel_a, zmin({**wa, "ZoomX": 1.0}, s_["a"][:2], s_["a"][2], ziel_a))
    if not all(np.isfinite(w["ZoomX"]) for w in list(neu_v1.values()) + list(neu_v2.values())):
        raise SystemExit("Ziel nicht für alle Stücke machbar (Kopfraum/Füllung) — anderes Ziel wählen.")
    zb_all = [w["ZoomX"] for w in neu_v1.values()]
    za_all = [w["ZoomX"] for w in neu_v2.values()]
    print(f"Ziel: X ±{X}, a7 Y {Ya}, FX3 Y {Yb} · FX3 Zoom {min(zb_all):.3f}–{max(zb_all):.3f} · a7 Zoom {min(za_all):.3f}–{max(za_all):.3f}")
    for stem in sorted({Path(s_["v1"].clip).stem for s_ in stuecke}):
        zz = [neu_v1[s_["v1"].rec_in_f]["ZoomX"] for s_ in stuecke if Path(s_["v1"].clip).stem == stem]
        print(f"  {stem}: Zoom {min(zz):.3f}–{max(zz):.3f}")
    for stem in sorted({Path(a7.clip).stem for s_ in stuecke for a7 in s_["a7"]}):
        zz = [neu_v2[a7.rec_in_f]["ZoomX"] for s_ in stuecke for a7 in s_["a7"] if Path(a7.clip).stem == stem and a7.rec_in_f in neu_v2]
        if zz:
            print(f"  {stem}: Zoom {min(zz):.3f}–{max(zz):.3f}")
    # Prüfbild: je FX3-Stück ein synchrones Paar
    kacheln = []
    for s_ in stuecke:
        v = s_["v1"]
        f = v.rec_in_f + int(3 * (v.rec_out_f - v.rec_in_f) / 6)
        b_jpg, a_jpg = ka.FRAMES / f"b_{f:05d}.jpg", ka.FRAMES / f"a_{f:05d}.jpg"
        if not b_jpg.exists():
            continue
        sx = SEITE[Path(v.clip).stem] * X
        bilder = []
        if s_["a7"] and a_jpg.exists():
            a7 = next((x for x in s_["a7"] if x.rec_in_f <= f < x.rec_out_f), s_["a7"][0])
            bilder.append(("A a7", ka.simulieren(a_jpg, ka.h_von(neu_v2[a7.rec_in_f])), neu_v2[a7.rec_in_f]["ZoomX"], Ya))
        else:
            bilder.append(("—", Image.new("RGB", (ka.PW, ka.PH), (40, 40, 40)), 0.0, Ya))
        bilder.append(("B FX3", ka.simulieren(b_jpg, ka.h_von(neu_v1[v.rec_in_f])), neu_v1[v.rec_in_f]["ZoomX"], Yb))
        paar = Image.new("RGB", (2 * ka.PW + 6, ka.PH), (30, 30, 30))
        for n, (titel, im, zoom, yz) in enumerate(bilder):
            zx, zy = sx / (W / ka.PW) + ka.PW / 2, yz / (H / ka.PH) + ka.PH / 2
            d = ImageDraw.Draw(im)
            d.line([(zx - 30, zy), (zx + 30, zy)], fill=(255, 40, 40), width=2)
            d.line([(zx, zy - 30), (zx, zy + 30)], fill=(255, 40, 40), width=2)
            d.line([(0, ka.PH / 3), (ka.PW, ka.PH / 3)], fill=(0, 200, 255), width=1)
            d.text((10, 8), f"{titel} #{v.beat_nr} @{v.rec_in_f} Zoom {zoom:.2f}", fill=(255, 255, 0))
            paar.paste(im, (n * (ka.PW + 6), 0))
        kacheln.append(paar.resize((ka.PW + 3, ka.PH // 2)))
    bogen = Image.new("RGB", (2 * (ka.PW + 3) + 6, ((len(kacheln) + 1) // 2) * (ka.PH // 2 + 6)), (15, 15, 15))
    for i, k in enumerate(kacheln):
        bogen.paste(k, ((i % 2) * (ka.PW + 9), (i // 2) * (ka.PH // 2 + 6)))
    bogen.save(HIER / f"kopf_beide_vergleich_X{X}_a{Ya}_b{Yb}.jpg", quality=86)
    bericht = {"ziel": {"X": X, "Y_a7": Ya, "Y_fx3": Yb, "seiten": SEITE}, "v1": [], "v2": []}
    for spur, neu in (("V1", neu_v1), ("V2", neu_v2)):
        for rec, w in sorted(neu.items()):
            x, vorher, _, _ = live[(spur, rec)]
            eintrag = {"start": rec, "clip": Path(x.GetName()).stem, "vorher": vorher, "neu": w}
            if ausfuehren:
                eintrag["gesetzt"] = bool(x.SetProperties({k: float(w[k]) for k in ka.KEYS}))
                rb = {k: float(x.GetProperty(k)) for k in ka.KEYS}
                eintrag["readback_ok"] = all(abs(rb[k] - w[k]) <= 1e-3 * max(1, abs(w[k])) for k in ka.KEYS)
            bericht[spur.lower()].append(eintrag)
    if ausfuehren:
        bericht["gespeichert"] = bool(pm.SaveProject())
        ok = sum(1 for e in bericht["v1"] + bericht["v2"] if e.get("gesetzt") and e.get("readback_ok"))
        print(f"gesetzt {ok}/{len(bericht['v1']) + len(bericht['v2'])}, gespeichert {bericht['gespeichert']}")
    (HIER / ("kopf_beide.json" if ausfuehren else "kopf_beide_plan.json")).write_text(json.dumps(bericht, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
