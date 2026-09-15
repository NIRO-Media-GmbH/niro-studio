"""Nachbesserung nach Kontrolle (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/nachbesserung.py [--ausfuehren]
1. SFX-Verknüpfung: Einzel-Links (Grafik-Clip + ein SFX) haben sich gegenseitig ersetzt. Jetzt je Grafik-Clip alle
   zugehörigen SFX (A4/A5) in einem SetClipsLinked-Aufruf verknüpfen; Readback, dass jede SFX mit ihrem Grafik-Clip hängt.
2. Gesichtsabstand zur Karte „Bachelor Professional" (2881–3004): im a7-Stück 2812–3005 (Flammann) rückt der Kopf höher,
   bis der Gesichts-Check-Abstand ≥ 30 px (540p) = 60 px (1080p) hält; seitliche Position (±250) bleibt.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
spec = importlib.util.spec_from_file_location("kf", HIER / "kopf_final.py")
kf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kf)
kb, ka, pb = kf.kb, kf.ka, kf.pb
W, H = kf.W, kf.H
A7_STUECK = 2812
KARTE = (57, 378, 427, 481)  # Bachelor-Karte in 960×540 (Alpha-Maske, gemessen im Gesichts-Check)


def main() -> None:
    ausfuehren = "--ausfuehren" in sys.argv
    argv = sys.argv
    sys.argv = ["x"]
    p, pm, tl, live, stuecke = kb.daten()
    sys.argv = argv
    start = tl.GetStartFrame()
    out = {}
    # --- 1. SFX-Gruppen ---
    plan = json.loads((INTERN / "sfx" / "sfx_plan.json").read_text())
    elemente = {i.beat_nr: (i.rec_in_f, i.rec_out_f) for i in p["V4"]}
    v4 = tl.GetItemListInTrack("video", 4) or []
    audio = {(sp, x.GetStart() - start): x for sp, idx in (("A4", 4), ("A5", 5)) for x in (tl.GetItemListInTrack("audio", idx) or [])}
    gruppen = {}
    for e in plan:
        a, b = elemente[e["element"]]
        clip = next(x for x in v4 if x.GetLeftOffset() < b and a < x.GetLeftOffset() + x.GetDuration())
        versatz = (clip.GetStart() - start) - clip.GetLeftOffset()
        sfx = audio.get((e["spur"], e["rec_frame"] + versatz))
        if sfx is None:
            raise SystemExit(f"SFX {e['sfx_name']} bei {e['rec_frame']} nicht gefunden — erst prüfen.")
        gruppen.setdefault(e["element"], [clip]).append(sfx)
    out["sfx_gruppen"] = {k: len(v) - 1 for k, v in gruppen.items()}
    # --- 2. a7-Stück Flammann während der Bachelor-Karte ---
    s = next(s for s in stuecke if s["v1"].rec_in_f <= A7_STUECK < s["v1"].rec_out_f)
    stem = Path(s["v1"].clip).stem
    sx = kb.SEITE[stem] * kf.X
    x_a7, w_jetzt, _, _ = live[("V2", A7_STUECK)]
    kb_final = json.loads((HIER / "kopf_final.json").read_text())
    straight = next(e["vorher"] for e in json.loads((HIER / "kopf_beide.json").read_text())["v2"] if e["start"] == A7_STUECK)
    y_jetzt = next(e for e in kb_final["stuecke"] if e["start"] == s["v1"].rec_in_f)["a_y"]
    # Gesichtsboxen der Proben dieses Stücks (Vision) für den Abstand zur Karte
    tsv = kb.subprocess.run([str(INTERN / "gesichtscheck" / "faces"), str(ka.FRAMES)], capture_output=True, text=True, check=True).stdout
    boxen = {}
    for z in tsv.splitlines():
        name, _, rest = z.partition("\t")
        bb = [tuple(map(float, b.split(","))) for b in rest.split(";")] if rest and rest != "ERR" else []
        bb = [b for b in bb if b[4] >= 0.5]
        if bb and name.startswith("a_"):
            boxen[int(name[2:7])] = max(bb, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    proben = [f for f in boxen if 2881 <= f < 3004 or (s["v1"].rec_in_f <= f < s["v1"].rec_out_f)]

    def abstand(werte):
        hm = ka.h_von(werte)
        am_engsten = 1e9
        for f in proben:
            x0, y0, x1, y1, _ = boxen[f]
            ecken = [ka.abbilden(hm, (bx - 0.5) * W, (by - 0.5) * H) for bx, by in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            ex = [e[0] / 4 + 480 for e in ecken]
            ey = [e[1] / 4 + 270 for e in ecken]
            bw, bh = max(ex) - min(ex), max(ey) - min(ey)
            fx0, fx1, fy1 = min(ex) - 0.08 * bw, max(ex) + 0.08 * bw, max(ey) + 0.12 * bh
            dx = max(KARTE[0] - fx1, fx0 - KARTE[2], 0)
            dy = max(KARTE[1] - fy1, 0)
            am_engsten = min(am_engsten, (dx * dx + dy * dy) ** 0.5)
        return am_engsten

    ergebnis = None
    for dy in range(0, 201, 10):
        y = y_jetzt - dy
        z = kf.fuellzoom(straight, s["a"][:2], (sx, y))
        werte = kb.werte_fuer(straight, s["a"][:2], (sx, y), z)
        a = abstand(werte)
        top = next(v for n, v in json.loads((HIER / "kopf" / "kopf_oben.json").read_text()).items() if n.startswith("a_"))
        if a >= 34:
            ergebnis = (dy, werte, a)
            break
    if ergebnis is None:
        raise SystemExit("Kein Wert mit genug Abstand gefunden — nichts geschrieben.")
    dy, werte, a = ergebnis
    raum = kf.kopfraum(straight, s["a"][:2], float(np.median([v["top_px_rel"] for n, v in json.loads((HIER / "kopf" / "kopf_oben.json").read_text()).items()
                                                               if n.startswith("a_") and s["v1"].rec_in_f <= int(n[2:7]) < s["v1"].rec_out_f])),
                       (sx, y_jetzt - dy), werte["ZoomX"])
    out["a7_stueck"] = {"start": A7_STUECK, "hoeher_px_4k": dy, "abstand_540p": round(a, 1), "kopfraum_px": round(float(raum)),
                        "vorher": w_jetzt, "neu": werte}
    print(json.dumps(out, ensure_ascii=False))
    if not ausfuehren:
        return
    out["verknuepft"] = {k: bool(tl.SetClipsLinked(v, True)) for k, v in gruppen.items()}
    lose = []
    for k, v in gruppen.items():
        for sfx in v[1:]:
            ids = {i.GetUniqueId() for i in (sfx.GetLinkedItems() or [])}
            if v[0].GetUniqueId() not in ids:
                lose.append((k, sfx.GetStart() - start))
    out["sfx_ohne_link"] = lose
    out["a7_gesetzt"] = bool(x_a7.SetProperties({k: float(werte[k]) for k in ka.KEYS}))
    out["gespeichert"] = bool(pm.SaveProject())
    (HIER / "nachbesserung.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("verknuepft",)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
