"""Vorlage (Stand 15.09.2026): Kopfposition A/B mit echtem Kopfraum setzen — Nachfolger von kopf_beide.py.

Anlass: User-Feedback „sein Kopf ist zu nah an der Oberkante" (Person A, a7-Nahe) — kopf_beide.py hatte den Kopfraum nur
aus der Gesichtsbox geschätzt.
Aufruf: tools/autocut/venv/bin/python _intern/begradigen/kopf_final.py [--ausfuehren]
Regeln (für alle Personen gleich, Standardwerte im ANPASSEN-Block):
- Seitlich: Kopfmitte in A (a7) und B (FX3) exakt gleich, X = ±250 px (4K; Seite je Clip aus kopf_beide.SEITE).
- A (a7-Nahe): Kopfraum über der echten Kopfoberkante (Vision-Personenmaske, kopf/kopf_oben.json) = 12 % der Bildhöhe.
- B (FX3-Totale): Kopfhöhe so nah an A wie möglich mit Zoom ≤ 1,45 und Kopfraum ≥ min(6 % Bildhöhe, ursprünglicher Kopfraum);
  geht das nicht, bleibt die Kopfhöhe wie begradigt und nur die Seite wird angeglichen.
- Zoom je Kamera = kleinster Wert ohne Rand; Begradigung (Rotation/Pitch/Yaw) bleibt. Stücke ohne a7 (z. B. CTA) wie FX3 mit
  Zielhöhe Y_OHNE_A7, Punch-in-Stücke × parameter_berechnen.PUNCH["zoom"].
Voraussetzung der Regeln: V2 (a7) ist die Nahe, V1 (FX3, Ton) die Totale — bei umgekehrter Brennweitenverteilung anpassen.
Eingaben: kopf_beide.daten() (Plan-Abgleich, live-Werte, Köpfe aus kopf/frames), kopf/kopf_oben.json (kopf_oben_messen.py),
  parameter.json, kopf_beide.json (deren „vorher" = begradigte Werte sind die Basis; siehe kopf_beide.py).
Ohne --ausfuehren nur Rechnung + Prüfbild kopf_final_vergleich.jpg (je Stück das mittlere Paar, dazu PRUEF_FRAMES) und
kopf_final_plan.json; mit --ausfuehren setzen + Readback + speichern, Bericht kopf_final.json (Regeln, je Stück Höhen/Zoom/
Kopfraum, je Item Vorher-Werte). Danach Gesichts-Check der Grafikebene wiederholen, kritische Stellen mit nachbesserung.py.
Richtwerte 15.09.: FX3-Zoom 1,15–1,31, wo A und B in der Höhe deckungsgleich wurden; sonst 1,44 mit 8–13 % Höhenversatz
(Stück ohne a7: 21 %), wenn die Totale den Kopf sehr hoch hatte.
Herkunft: Taxodia-Charge, _intern/begradigen/kopf_final.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kb", HIER / "kopf_beide.py")
kb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb)
ka, pb = kb.ka, kb.pb
W, H = kb.W, kb.H

# ── ANPASSEN je Charge ─────────────────────────────
X = 250  # Standard (15.09.): seitlicher Abstand der Kopfmitte zur Bildmitte in Timeline-px (bei 3840 breit), A und B gleich
KOPFRAUM_A = 0.12 * H  # Standard (15.09.): Kopfraum der a7-Nahen über der Kopfoberkante = 12 % der Bildhöhe
KOPFRAUM_B_MIN = 0.06 * H  # Standard (15.09.): Mindest-Kopfraum der FX3-Totalen (höchstens der ursprüngliche Kopfraum)
ZOOM_B_MAX = 1.45  # Standard (15.09.): größter Zoom der FX3-Totalen
Y_OHNE_A7 = None  # Zielhöhe der Kopfmitte in Timeline-px (− = über der Bildmitte) für FX3-Stücke ohne a7 (z. B. CTA); nur dann nötig
# Y_OHNE_A7 = -325.0   (15.09.: Zielhöhe der a7-Nahen aus kopf_beide, ≈ 15 % der Bildhöhe über der Mitte bei 2160 px)
PRUEF_FRAMES = ()  # Timeline-Frames (ab Timeline-Start) zusätzlich ins Prüfbild, z. B. die Stelle eines User-Screenshots
# PRUEF_FRAMES = (1234,)
# ── Ende ANPASSEN ──────────────────────────────────


def hm_fuer(w, kopf, ziel, z):
    basis = pb.resolve_h(w["Pitch"], w["Yaw"], w["RotationAngle"], 1.0, 0.0, 0.0)
    qx, qy = ka.abbilden(basis, kopf[0], kopf[1])
    return pb.resolve_h(w["Pitch"], w["Yaw"], w["RotationAngle"], z, ziel[0] - z * qx, -(ziel[1] - z * qy))


def fuellzoom(w, kopf, ziel):
    lo, hi = 1.0, 3.5
    if pb.deckt(hm_fuer(w, kopf, ziel, lo)) >= 0:
        return lo
    if pb.deckt(hm_fuer(w, kopf, ziel, hi)) < 0:
        return float("inf")
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if pb.deckt(hm_fuer(w, kopf, ziel, mid)) >= 0 else (mid, hi)
    return hi


def kopfraum(w, kopf, top, ziel, z):
    return ka.abbilden(hm_fuer(w, kopf, ziel, z), kopf[0], kopf[1] + top)[1] + H / 2


def a_ziel(w, kopf, top, sx):
    """Kopfhöhe Y so, dass der Kopfraum 12 % beträgt (Zoom hängt von Y ab → Suche über Y)."""
    beste = None
    for y in np.arange(-700, 200, 5.0):
        z = fuellzoom(w, kopf, (sx, y))
        if not np.isfinite(z):
            continue
        raum = kopfraum(w, kopf, top, (sx, y), z)
        if beste is None or abs(raum - KOPFRAUM_A) < abs(beste[2] - KOPFRAUM_A):
            beste = (y, z, raum)
    return beste


def b_ziel(w, kopf, top, sx, y_a, raum_orig):
    """Kopfhöhe so nah an y_a wie möglich (Zoom ≤ 1,45, Kopfraum ≥ min(6 %, Original))."""
    raum_min = min(KOPFRAUM_B_MIN, raum_orig)
    kandidaten = []
    for y in np.arange(-800, 200, 5.0):
        z = fuellzoom(w, kopf, (sx, y))
        if not np.isfinite(z) or z > ZOOM_B_MAX:
            continue
        raum = kopfraum(w, kopf, top, (sx, y), z)
        if raum >= raum_min:
            kandidaten.append((abs(y - y_a), z, y, raum))
    if not kandidaten:  # Fallback: Kopfhöhe wie begradigt, nur seitlich angleichen
        return None
    kandidaten.sort()
    return kandidaten[0][2], kandidaten[0][1], kandidaten[0][3]


def main() -> None:
    ausfuehren = "--ausfuehren" in sys.argv
    sys_argv = sys.argv
    sys.argv = ["x"]
    p, pm, tl, live, stuecke = kb.daten()
    sys.argv = sys_argv
    oben = json.loads((HIER / "kopf" / "kopf_oben.json").read_text())
    params = json.loads((HIER / "parameter.json").read_text())
    kb_alt = json.loads((HIER / "kopf_beide.json").read_text())
    straight = {("V1", e["start"]): e["vorher"] for e in kb_alt["v1"]} | {("V2", e["start"]): e["vorher"] for e in kb_alt["v2"]}

    def top_rel(v, kam):
        dauer = v.rec_out_f - v.rec_in_f
        vals = [oben[n]["top_px_rel"] for n in (f"{kam}_{v.rec_in_f + int((k + 1) * dauer / 6):05d}.jpg" for k in range(5)) if n in oben]
        return float(np.median(vals)) if vals else None

    neu_v1, neu_v2, info = {}, {}, []
    for s in stuecke:
        v = s["v1"]
        stem = Path(v.clip).stem
        sx = kb.SEITE[stem] * X
        wb = {**straight[("V1", v.rec_in_f)]}
        punch_in = params[stem]["resolve_punch_in"]  # None ohne Punch-in (parameter_berechnen.PUNCH = None)
        punch = punch_in is not None and abs(wb["ZoomX"] - punch_in["ZoomX"]) < 1e-3
        b_top = top_rel(v, "b")
        # Ursprünglicher Kopfraum der FX3 (nur begradigt)
        raum_b_orig = ka.abbilden(ka.h_von(params[stem]["resolve"]), s["b"][0], s["b"][1] + b_top)[1] + H / 2
        y_a = None
        if s["a"] is not None:
            a_top = top_rel(v, "a")
            wa = {**straight[("V2", s["a7"][0].rec_in_f)]}
            y_a, z_a, raum_a = a_ziel(wa, s["a"][:2], a_top, sx)
            for a7 in s["a7"]:
                w_piece = {**straight[("V2", a7.rec_in_f)]}
                neu_v2[a7.rec_in_f] = kb.werte_fuer(w_piece, s["a"][:2], (sx, y_a), z_a)
        if y_a is None and Y_OHNE_A7 is None:
            raise SystemExit(f"Stück {v.rec_in_f} ({stem}) ohne a7-Gegenstück — Y_OHNE_A7 im ANPASSEN-Block setzen, nichts geschrieben.")
        ziel_y = y_a if y_a is not None else Y_OHNE_A7
        erg = b_ziel(wb, s["b"][:2], b_top, sx, ziel_y, raum_b_orig)
        if erg is None:
            y_b = ka.abbilden(ka.h_von(params[stem]["resolve"]), *s["b"][:2])[1]
            z_b = fuellzoom(wb, s["b"][:2], (sx, y_b))
            raum_b = kopfraum(wb, s["b"][:2], b_top, (sx, y_b), z_b)
        else:
            y_b, z_b, raum_b = erg
        neu_v1[v.rec_in_f] = kb.werte_fuer(wb, s["b"][:2], (sx, y_b), z_b * (pb.PUNCH["zoom"] if punch else 1.0))
        info.append({"start": v.rec_in_f, "beat": v.beat_nr, "clip": stem, "a_y": None if y_a is None else round(float(y_a)),
                     "a_zoom": None if y_a is None else round(float(z_a), 3), "a_kopfraum": None if y_a is None else round(float(raum_a)),
                     "b_y": round(float(y_b)), "b_zoom": round(float(z_b), 3), "b_kopfraum": round(float(raum_b)),
                     "b_kopfraum_original": round(float(raum_b_orig)), "hoehenversatz": None if y_a is None else round(float(y_b - y_a))})
    for e in info:
        print(f"#{e['beat']:>2} @{e['start']:>5} {e['clip']:<9} A: Y {e['a_y']} Zoom {e['a_zoom']} Raum {e['a_kopfraum']} | "
              f"B: Y {e['b_y']} Zoom {e['b_zoom']} Raum {e['b_kopfraum']} (orig {e['b_kopfraum_original']}) | Versatz {e['hoehenversatz']}")
    # Prüfbild: je Stück das mittlere synchrone Paar, plus PRUEF_FRAMES (z. B. Screenshot-Stelle des Users)
    kacheln = []
    for s in stuecke:
        v = s["v1"]
        for f in sorted({v.rec_in_f + int(3 * (v.rec_out_f - v.rec_in_f) / 6)} | {g for g in PRUEF_FRAMES if v.rec_in_f <= g < v.rec_out_f}):
            b_jpg, a_jpg = ka.FRAMES / f"b_{f:05d}.jpg", ka.FRAMES / f"a_{f:05d}.jpg"
            if f in PRUEF_FRAMES:
                a7 = next((x for x in s["a7"] if x.rec_in_f <= f < x.rec_out_f), None)
                if a7 is not None and not a_jpg.exists():
                    ka.frame_holen(a7.clip, (a7.src_in_f + f - a7.rec_in_f) / ka.FPS, a_jpg)
                if not b_jpg.exists():
                    ka.frame_holen(v.clip, (v.src_in_f + f - v.rec_in_f) / ka.FPS, b_jpg)
            if not b_jpg.exists():
                continue
            paar = Image.new("RGB", (2 * ka.PW + 6, ka.PH), (30, 30, 30))
            a7 = next((x for x in s["a7"] if x.rec_in_f <= f < x.rec_out_f), s["a7"][0] if s["a7"] else None)
            bilder = [("A a7", ka.simulieren(a_jpg, ka.h_von(neu_v2[a7.rec_in_f])) if a7 is not None and a_jpg.exists() else Image.new("RGB", (ka.PW, ka.PH), (40, 40, 40)))]
            bilder.append(("B FX3", ka.simulieren(b_jpg, ka.h_von(neu_v1[v.rec_in_f]))))
            for n, (titel, im) in enumerate(bilder):
                d = ImageDraw.Draw(im)
                d.line([(0, ka.PH * 0.12), (ka.PW, ka.PH * 0.12)], fill=(0, 200, 255), width=1)
                d.text((10, 8), f"{titel} #{v.beat_nr} @{f}", fill=(255, 255, 0))
                paar.paste(im, (n * (ka.PW + 6), 0))
            kacheln.append(paar.resize((ka.PW + 3, ka.PH // 2)))
    bogen = Image.new("RGB", (2 * (ka.PW + 3) + 6, ((len(kacheln) + 1) // 2) * (ka.PH // 2 + 6)), (15, 15, 15))
    for i, k in enumerate(kacheln):
        bogen.paste(k, ((i % 2) * (ka.PW + 9), (i // 2) * (ka.PH // 2 + 6)))
    bogen.save(HIER / "kopf_final_vergleich.jpg", quality=86)
    bericht = {"regeln": {"X": X, "kopfraum_a7": KOPFRAUM_A, "kopfraum_fx3_min": KOPFRAUM_B_MIN, "zoom_fx3_max": ZOOM_B_MAX},
               "stuecke": info, "v1": [], "v2": []}
    for spur, neu in (("V1", neu_v1), ("V2", neu_v2)):
        for rec, w in sorted(neu.items()):
            x, jetzt, _, _ = live[(spur, rec)]
            eintrag = {"start": rec, "clip": Path(x.GetName()).stem, "vorher": jetzt, "neu": w}
            if ausfuehren:
                eintrag["gesetzt"] = bool(x.SetProperties({k: float(w[k]) for k in ka.KEYS}))
                rb = {k: float(x.GetProperty(k)) for k in ka.KEYS}
                eintrag["readback_ok"] = all(abs(rb[k] - w[k]) <= 1e-3 * max(1, abs(w[k])) for k in ka.KEYS)
            bericht[spur.lower()].append(eintrag)
    if ausfuehren:
        bericht["gespeichert"] = bool(pm.SaveProject())
        ok = sum(1 for e in bericht["v1"] + bericht["v2"] if e.get("gesetzt") and e.get("readback_ok"))
        print(f"gesetzt {ok}/{len(bericht['v1']) + len(bericht['v2'])}, gespeichert {bericht['gespeichert']}")
    (HIER / ("kopf_final.json" if ausfuehren else "kopf_final_plan.json")).write_text(json.dumps(bericht, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
