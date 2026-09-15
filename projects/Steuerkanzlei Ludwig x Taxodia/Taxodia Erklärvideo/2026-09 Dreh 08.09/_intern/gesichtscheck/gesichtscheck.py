"""Gesichts-Check Grafikebene v2 über dem Feinschnitt (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/gesichtscheck/gesichtscheck.py
Für jedes 2. Frame, in dem die Grafikebene sichtbar, aber nicht deckend ist: oberstes Bild laut Feinschnitt-Plan
(V3 B-Roll > V2 a7 > V1 FX3, mit Tempo und Punch-in) aus den Proxys holen, Gesichter per Apple Vision (faces.swift)
finden und gegen die Alpha-Maske (> 50 %) der Grafik prüfen. Gesichtsbox +8 % seitlich, +12 % Kinn.
Kritisch: Maske in der Box oder Abstand < 30 px (540p) = 60 px (1080p). Ergebnis: bericht.json + Prüfbilder kritisch_*.jpg
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

GC = Path(__file__).resolve().parent
CH = GC.parent.parent
W, H = 960, 540
KRITISCH_PX = 30

spec = importlib.util.spec_from_file_location("fb", GC.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def oberstes_bild(p: dict, f: int):
    """(Spur, Datei, Quellsekunde, Punch-in?) des sichtbaren Bilds unter der Grafik."""
    for m, it in zip(sorted(p["v3_meta"], key=lambda z: z["rec_in_f"]), sorted(p["V3"], key=lambda i: i.rec_in_f)):
        if it.rec_in_f <= f < it.rec_out_f:
            schritt = 1 if m["langsam"] else 2  # 50p-Quelle: 50 % = 1 Quellbild je Timeline-Frame
            return "V3", it.clip, (it.src_in_f + schritt * (f - it.rec_in_f)) / 50.0, False, it.rec_in_f
    for spur in ("V2", "V1"):
        for it in p[spur]:
            if it.rec_in_f <= f < it.rec_out_f:
                punch = spur == "V1" and it.beat_nr == fb.PUNCH_IN["beat"] and it.rec_in_f == sorted(
                    [i for i in p["V1"] if i.beat_nr == fb.PUNCH_IN["beat"]], key=lambda i: i.rec_in_f)[fb.PUNCH_IN["index"]].rec_in_f
                return spur, it.clip, (it.src_in_f + f - it.rec_in_f) / 25.0, punch, it.rec_in_f
    return None


def main() -> None:
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    if fehler:
        raise SystemExit(f"Plan fehlerhaft: {fehler}")
    al = json.loads(fb.ALPHA_JSON.read_text())
    amin, amean = al["alpha_min"], al["alpha_mean"]
    frames = [f for f in range(0, fb.ENDE, 2) if amean[f] > 0.3 and amin[f] < fb.DECKEND_AB]
    print(f"{len(frames)} Prüf-Frames mit sichtbarer, nicht deckender Grafik")
    bg = GC / "bild"
    am = GC / "alpha"
    bg.mkdir(exist_ok=True)
    am.mkdir(exist_ok=True)
    lagen = {f: oberstes_bild(p, f) for f in frames}
    # Cache nur gültig, solange an dem Frame dieselbe Quelle oben liegt (Plan-Änderungen invalidieren)
    idx_pfad = bg / "index.json"
    alt = json.loads(idx_pfad.read_text()) if idx_pfad.exists() else {}
    neu = {str(f): None if lagen[f] is None else f"{lagen[f][1]}@{lagen[f][2]:.3f}" for f in frames}
    for k, sig in neu.items():
        if alt.get(k) != sig and (bg / f"f_{int(k):05d}.jpg").exists():
            (bg / f"f_{int(k):05d}.jpg").unlink()
    idx_pfad.write_text(json.dumps(neu))
    # Vollbild-Übergänge (Wipe/Iris einer deckenden Grafik) sind gewollte Blenden, keine Karten über Gesichtern
    deckend = [amin[f] >= fb.DECKEND_AB for f in range(fb.ENDE)]
    nahe_deckend = [any(deckend[max(0, f - 12):f + 13]) for f in range(fb.ENDE)]

    def ist_uebergang(f: int) -> bool:
        return nahe_deckend[f] and amean[f] >= 30

    def hole_bild(f: int) -> None:
        ziel = bg / f"f_{f:05d}.jpg"
        if ziel.exists() or lagen[f] is None:
            return
        spur, datei, t, _, _ = lagen[f]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", proxy(datei), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", "-q:v", "3", str(ziel)], check=True)

    # Grafik-Alpha: zusammenhängende Läufe je ein ffmpeg-Aufruf
    laeufe, s0, prev = [], None, None
    for f in frames:
        if s0 is None:
            s0 = f
        elif f != prev + 2:
            laeufe.append((s0, prev + 1))
            s0 = f
        prev = f
    if s0 is not None:
        laeufe.append((s0, prev + 1))

    def hole_alpha(lauf: tuple[int, int]) -> None:
        a, b = lauf
        ziel = am / f"a_{a:05d}_{b:05d}.npy"
        if ziel.exists():
            return
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a / 25:.3f}", "-i", str(fb.GRAFIK), "-frames:v", str(b - a),
                            "-vf", f"alphaextract,scale={W}:{H},format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                           capture_output=True, check=True)
        arr = np.frombuffer(r.stdout, np.uint8).reshape(-1, H, W)[::2]
        np.save(ziel, arr > 128)

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(hole_bild, frames))
        list(ex.map(hole_alpha, laeufe))
    masken = {}
    for a, b in laeufe:
        arr = np.load(am / f"a_{a:05d}_{b:05d}.npy")
        for k, f in enumerate(range(a, b, 2)):
            if k < len(arr):
                masken[f] = arr[k]
    tsv = subprocess.run([str(GC / "faces"), str(bg)], capture_output=True, text=True, check=True).stdout
    gesichter = {}
    for zeile in tsv.splitlines():
        name, _, rest = zeile.partition("\t")
        boxen = []
        if rest and rest != "ERR":
            for teil in rest.split(";"):
                x0, y0, x1, y1, c = map(float, teil.split(","))
                boxen.append((x0 * W, y0 * H, x1 * W, y1 * H, c))
        gesichter[int(name[2:7])] = boxen
    # Transform der Interview-Items (Begradigung inkl. Punch-in, kalibriertes Resolve-Modell) auf die Gesichtsboxen anwenden
    param_pfad = GC.parent / "begradigen" / "parameter.json"
    transform = json.loads(param_pfad.read_text()) if param_pfad.exists() else {}
    spec_pb = importlib.util.spec_from_file_location("pb", GC.parent / "begradigen" / "parameter_berechnen.py")
    pb = importlib.util.module_from_spec(spec_pb)
    spec_pb.loader.exec_module(pb)
    pz = fb.PUNCH_IN["props"]

    kopf_pfad = GC.parent / "begradigen" / "kopf_final.json"
    je_item = {}
    if kopf_pfad.exists():
        kb = json.loads(kopf_pfad.read_text())
        for spur_ in ("v1", "v2"):
            for e in kb.get(spur_, []):
                je_item[(spur_.upper(), e["start"])] = e["neu"]

    def box_transformieren(box, stem, punch, spur=None, item_start=None):
        werte = je_item.get((spur, item_start)) or (transform.get(stem) or {}).get("resolve_punch_in" if punch else "resolve")
        if werte is None:
            if not punch:
                return box
            werte = {"Pitch": 0, "Yaw": 0, "RotationAngle": 0, "ZoomX": pz["ZoomX"], "Pan": pz["Pan"], "Tilt": 0}
        hm = pb.resolve_h(werte["Pitch"], werte["Yaw"], werte["RotationAngle"], werte["ZoomX"], werte["Pan"], werte["Tilt"])
        s = 3840 / W
        pts = []
        for bx, by in ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])):
            q = hm @ np.array([(bx - W / 2) * s, (by - H / 2) * s, 1.0])
            pts.append((q[0] / q[2] / s + W / 2, q[1] / q[2] / s + H / 2))
        xs, ys = [p_[0] for p_ in pts], [p_[1] for p_ in pts]
        return min(xs), min(ys), max(xs), max(ys)

    rows, kritisch = [], []
    for f in frames:
        if f not in masken or lagen[f] is None:
            continue
        m = masken[f]
        dist = distance_transform_edt(~m) if m.any() else None
        spur, datei, t, punch, item_start = lagen[f]
        for x0, y0, x1, y1, c in gesichter.get(f, []):
            if c < 0.5:
                continue
            if spur in ("V1", "V2"):
                x0, y0, x1, y1 = box_transformieren((x0, y0, x1, y1), Path(datei).stem, punch, spur, item_start)
            bw, bh = x1 - x0, y1 - y0
            bx0, bx1 = int(max(0, x0 - 0.08 * bw)), int(min(W, x1 + 0.08 * bw))
            by0, by1 = int(max(0, y0)), int(min(H, y1 + 0.12 * bh))
            if bx1 <= bx0 or by1 <= by0 or dist is None:
                continue
            ueberlapp = int(m[by0:by1, bx0:bx1].sum())
            abstand = -ueberlapp if ueberlapp else float(dist[by0:by1, bx0:bx1].min())
            row = {"frame": f, "tc": fb.tc(f), "spur": spur, "clip": Path(datei).stem, "box": [bx0, by0, bx1, by1],
                   "konfidenz": round(c, 2), "abstand_px_540p": round(abstand, 1), "vollbild_uebergang": ist_uebergang(f)}
            rows.append(row)
            if abstand < KRITISCH_PX and not row["vollbild_uebergang"]:
                kritisch.append(row)
    uebergaenge = sorted({r["frame"] for r in rows if r["vollbild_uebergang"] and r["abstand_px_540p"] < KRITISCH_PX})
    print(f"Gesichter geprüft: {len(rows)} in {len({r['frame'] for r in rows})} Frames; kritisch: {len(kritisch)} "
          f"(Wipes deckender Vollbild-Grafiken über Gesichtern, gewollt: {len(uebergaenge)} Frames)")
    # je zusammenhängendem Fenster das schlimmste Frame als Prüfbild
    fenster = []
    for r in sorted(kritisch, key=lambda r: r["frame"]):
        if fenster and r["frame"] - fenster[-1][-1]["frame"] <= 12:
            fenster[-1].append(r)
        else:
            fenster.append([r])
    for fen in fenster:
        worst = min(fen, key=lambda r: r["abstand_px_540p"])
        f = worst["frame"]
        rgba = GC / f"g_{f:05d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{f / 25:.3f}", "-i", str(fb.GRAFIK), "-frames:v", "1",
                        "-vf", f"scale={W}:{H},format=rgba", str(rgba)], check=True)
        b = worst["box"]
        out = GC / f"kritisch_{f:05d}.jpg"
        subprocess.run(["magick", str(bg / f"f_{f:05d}.jpg"), str(rgba), "-composite", "-fill", "none", "-stroke", "red",
                        "-strokewidth", "3", "-draw", f"rectangle {b[0]},{b[1]},{b[2]},{b[3]}",
                        "-font", "/System/Library/Fonts/Supplemental/Arial.ttf", "-fill", "yellow", "-stroke", "none",
                        "-undercolor", "#000000A0", "-pointsize", "22", "-annotate", "+8+24",
                        f"{worst['tc']} ({f}) {worst['spur']} {worst['clip']} Abstand {worst['abstand_px_540p']} px · {len(fen)} Treffer "
                        f"{fen[0]['frame']}–{fen[-1]['frame']}", str(out)], check=True)
        rgba.unlink()
        print(f"  KRITISCH {worst['tc']} Frames {fen[0]['frame']}–{fen[-1]['frame']} {worst['spur']} {worst['clip']}: "
              f"min {worst['abstand_px_540p']} px → {out.name}")
    (GC / "bericht.json").write_text(json.dumps({"pruef_frames": len(frames), "gesichter": rows, "kritisch": kritisch},
                                                ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
