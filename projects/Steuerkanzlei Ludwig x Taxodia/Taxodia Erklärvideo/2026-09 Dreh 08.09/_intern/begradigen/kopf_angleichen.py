"""B-Perspektive (FX3, V1) so verschieben, dass der Kopf dort liegt, wo er in der A-Perspektive (a7, V2) ist; Zoom füllt das Bild.
(User 15.09.2026: „Verschiebe die B Perspektive so dass der Kopf da liegt wo er bei der A Perspektive ist, nutze dann Zoom
um das gesamte Bild zu füllen".)

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/kopf_angleichen.py [--ausfuehren]
- Transformwerte aller V1/V2-Items live aus Resolve (nur lesen); V1-Stück ↔ a7-Stück über den Feinschnitt-Plan (V2_voll).
- Je FX3-Stück 5 synchrone Zeitpunkte: Proxy-Frame FX3 + a7 → Apple Vision (größtes Gesicht) → Kopfmitte.
  Ziel = a7-Kopf nach dessen Resolve-Transform (Ausgabebild). FX3: Begradigung (Rotation/Pitch/Yaw) bleibt, neu sind
  Zoom Z und Position t mit Z·R·P(Kopf_FX3) + t = Ziel; Z = kleinster Wert, bei dem das Bild ganz gefüllt ist.
- Modell aus der Kalibrierung (parameter_berechnen.resolve_h). Stücke ohne a7 (CTA #22) bleiben unverändert.
- Prüfbild kopf_vergleich.jpg: A (a7) | B neu (FX3), simuliert mit demselben Modell, Fadenkreuz auf der Zielposition.
Ohne --ausfuehren nur Rechnung + Prüfbild. Bericht: kopf_parameter.json / kopf_anwendung.json (mit Vorher-Werten).
"""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402

spec = importlib.util.spec_from_file_location("fb", INTERN / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
spec2 = importlib.util.spec_from_file_location("pb", HIER / "parameter_berechnen.py")
pb = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(pb)

TIMELINE = "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt"
KEYS = ("RotationAngle", "Pitch", "Yaw", "ZoomX", "ZoomY", "Pan", "Tilt")
W, H = 3840.0, 2160.0
PW, PH = 960, 540  # Prüf-Frames
PROBEN = 5
FRAMES = HIER / "kopf" / "frames"


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def frame_holen(pfad: str, t: float, ziel: Path) -> None:
    if not ziel.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", proxy(pfad), "-frames:v", "1",
                        "-vf", f"scale={PW}:{PH}", "-q:v", "3", str(ziel)], check=True)


def h_von(werte: dict) -> np.ndarray:
    return pb.resolve_h(werte["Pitch"], werte["Yaw"], werte["RotationAngle"], werte["ZoomX"], werte["Pan"], werte["Tilt"])


def abbilden(hm: np.ndarray, x: float, y: float) -> tuple[float, float]:
    q = hm @ np.array([x, y, 1.0])
    return q[0] / q[2], q[1] / q[2]


def zoom_und_position(werte: dict, kopf_src: tuple[float, float], ziel: tuple[float, float]) -> tuple[float, float, float]:
    """Kleinstes Z (≥ 1) mit voller Bildfüllung, wenn Z·R·P(Kopf) + t = Ziel. Rückgabe (Z, Pan, Tilt)."""
    basis = pb.resolve_h(werte["Pitch"], werte["Yaw"], werte["RotationAngle"], 1.0, 0.0, 0.0)
    qx, qy = abbilden(basis, *kopf_src)

    def hm(z):
        tx, ty = ziel[0] - z * qx, ziel[1] - z * qy
        return pb.resolve_h(werte["Pitch"], werte["Yaw"], werte["RotationAngle"], z, tx, -ty)

    lo, hi = 1.0, 4.0
    if pb.deckt(hm(lo)) >= 0:
        z = lo
    else:
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if pb.deckt(hm(mid)) >= 0 else (mid, hi)
        z = hi
    z = z + 0.0008  # Reserve gegen Rundung in Resolve
    return z, ziel[0] - z * qx, -(ziel[1] - z * qy)


def simulieren(jpg: Path, hm4k: np.ndarray) -> Image.Image:
    """Resolve-Transform auf ein 960×540-Proxybild anwenden (für das Prüfbild; Rand außerhalb der Quelle = Magenta)."""
    s = W / PW
    C = np.array([[1, 0, PW / 2], [0, 1, PH / 2], [0, 0, 1.0]])
    S = np.diag([s, s, 1.0])
    M = C @ np.linalg.inv(S) @ hm4k @ S @ np.linalg.inv(C)
    inv = np.linalg.inv(M)
    inv /= inv[2, 2]
    img = Image.open(jpg).convert("RGB")
    grund = Image.new("RGB", img.size, (255, 0, 255))
    maske = Image.new("L", img.size, 255).transform((PW, PH), Image.PERSPECTIVE, tuple(inv.ravel()[:8]), Image.BILINEAR)
    bild = img.transform((PW, PH), Image.PERSPECTIVE, tuple(inv.ravel()[:8]), Image.BILINEAR)
    grund.paste(bild, (0, 0), maske)
    return grund


def main() -> None:
    ausfuehren = "--ausfuehren" in sys.argv
    tl_json, shots = fb.lade()
    p, fehler = fb.plan(tl_json, shots)
    r = RA.connect()
    pm = r.GetProjectManager()
    proj = pm.GetCurrentProject()
    if proj.GetName() != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{proj.GetName()}' ≠ Freigabe '{fb.PROJEKT}' — nichts geschrieben.")
    tl = next(t for t in (proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)) if t and t.GetName() == TIMELINE)
    start = tl.GetStartFrame()
    live = {}
    for idx in (1, 2):
        for x in tl.GetItemListInTrack("video", idx) or []:
            live[(f"V{idx}", x.GetStart() - start)] = (x, {k: float(x.GetProperty(k)) for k in KEYS}, x.GetLeftOffset(), x.GetDuration())
    # Plan und Timeline müssen übereinstimmen (keine Handänderungen an V1/V2)
    for spur, liste in (("V1", p["V1"]), ("V2", p["V2_voll"])):
        for it in liste:
            eintrag = live.get((spur, it.rec_in_f))
            if eintrag is None or eintrag[2] != it.src_in_f or eintrag[3] != it.rec_out_f - it.rec_in_f:
                raise SystemExit(f"{spur} bei {it.rec_in_f} weicht vom Plan ab — Timeline wurde geändert, erst abstimmen.")
    FRAMES.mkdir(parents=True, exist_ok=True)
    auftraege = []
    for v in p["V1"]:
        a7 = [s for s in p["V2_voll"] if s.rec_in_f < v.rec_out_f and v.rec_in_f < s.rec_out_f]
        if not a7:
            continue
        dauer = v.rec_out_f - v.rec_in_f
        for k in range(PROBEN):
            f = v.rec_in_f + int((k + 1) * dauer / (PROBEN + 1))
            s = next((s for s in a7 if s.rec_in_f <= f < s.rec_out_f), None)
            if s is None:
                continue
            fx3_jpg, a7_jpg = FRAMES / f"b_{f:05d}.jpg", FRAMES / f"a_{f:05d}.jpg"
            frame_holen(v.clip, (v.src_in_f + f - v.rec_in_f) / 25, fx3_jpg)
            frame_holen(s.clip, (s.src_in_f + f - s.rec_in_f) / 25, a7_jpg)
            auftraege.append((v, s, f, fx3_jpg, a7_jpg))
    tsv = subprocess.run([str(INTERN / "gesichtscheck" / "faces"), str(FRAMES)], capture_output=True, text=True, check=True).stdout
    kopf = {}
    for z in tsv.splitlines():
        name, _, rest = z.partition("\t")
        boxen = [tuple(map(float, b.split(","))) for b in rest.split(";")] if rest and rest != "ERR" else []
        boxen = [b for b in boxen if b[4] >= 0.5]
        if boxen:
            x0, y0, x1, y1, c = max(boxen, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            # Kopfmitte: Gesichtsbox-Mitte, leicht nach oben (Stirn/Haare) — gleich für beide Kameras
            kopf[name] = (((x0 + x1) / 2 - 0.5) * W, ((y0 + y1) / 2 - 0.08 * (y1 - y0) - 0.5) * H, (x1 - x0) * W)
    ergebnis = []
    for v in p["V1"]:
        proben = [a for a in auftraege if a[0] is v and a[3].name in kopf and a[4].name in kopf]
        if not proben:
            continue
        x_v, werte_v, _, _ = live[("V1", v.rec_in_f)]
        ziele, koepfe = [], []
        for _, s, f, fx3_jpg, a7_jpg in proben:
            _, werte_a, _, _ = live[("V2", s.rec_in_f)]
            ziele.append(abbilden(h_von(werte_a), *kopf[a7_jpg.name][:2]))
            koepfe.append(kopf[fx3_jpg.name][:2])
        ziel = tuple(np.median(np.array(ziele), axis=0))
        kopf_src = tuple(np.median(np.array(koepfe), axis=0))
        z, pan, tilt = zoom_und_position(werte_v, kopf_src, ziel)
        neu = {**werte_v, "ZoomX": round(z, 4), "ZoomY": round(z, 4), "Pan": round(pan, 1), "Tilt": round(tilt, 1)}
        # Kontrolle: Kopf nach neuem Transform
        kontrolle = abbilden(h_von(neu), *kopf_src)
        streu = float(np.max(np.linalg.norm(np.array(ziele) - np.array(ziel), axis=1)))
        ergebnis.append({"start": v.rec_in_f, "ende": v.rec_out_f, "beat": v.beat_nr, "clip": Path(v.clip).stem, "proben": len(proben),
                         "ziel_kopf_px": [round(ziel[0]), round(ziel[1])], "b_kopf_quelle_px": [round(kopf_src[0]), round(kopf_src[1])],
                         "abweichung_nachher_px": round(math.dist(kontrolle, ziel), 2), "ziel_streuung_px": round(streu, 1),
                         "vorher": werte_v, "neu": neu, "_probe": (proben[len(proben) // 2][3], proben[len(proben) // 2][4],
                                                                   proben[len(proben) // 2][1].rec_in_f)})
    for e in ergebnis:
        print(f"#{e['beat']:>2} {e['start']:>5}–{e['ende']:<5} {e['clip']:<9} Ziel {e['ziel_kopf_px']} ← B-Kopf {e['b_kopf_quelle_px']} | "
              f"Zoom {e['vorher']['ZoomX']:.3f} → {e['neu']['ZoomX']:.3f}, Pan {e['neu']['Pan']:+.0f}, Tilt {e['neu']['Tilt']:+.0f} | "
              f"Rest {e['abweichung_nachher_px']} px, Streuung Ziel {e['ziel_streuung_px']} px")
    # Prüfbild: je Person die ersten 3 Stücke
    kacheln = []
    for e in ergebnis:
        fx3_jpg, a7_jpg, a7_start = e["_probe"]
        _, werte_a, _, _ = live[("V2", a7_start)]
        a_img = simulieren(a7_jpg, h_von(werte_a))
        b_img = simulieren(fx3_jpg, h_von(e["neu"]))
        zx, zy = e["ziel_kopf_px"][0] / (W / PW) + PW / 2, e["ziel_kopf_px"][1] / (H / PH) + PH / 2
        paar = Image.new("RGB", (2 * PW + 6, PH), (30, 30, 30))
        for n, im in enumerate((a_img, b_img)):
            d = ImageDraw.Draw(im)
            d.line([(zx - 40, zy), (zx + 40, zy)], fill=(255, 40, 40), width=3)
            d.line([(zx, zy - 40), (zx, zy + 40)], fill=(255, 40, 40), width=3)
            d.text((10, 8), f"{'A a7' if n == 0 else 'B FX3 neu'} #{e['beat']} @{e['start']}  Zoom {e['neu']['ZoomX']:.3f}", fill=(255, 255, 0))
            paar.paste(im, (n * (PW + 6), 0))
        kacheln.append(paar.resize((PW + 3, PH // 2)))
    bogen = Image.new("RGB", (2 * (PW + 3) + 6, ((len(kacheln) + 1) // 2) * (PH // 2 + 6)), (15, 15, 15))
    for i, k in enumerate(kacheln):
        bogen.paste(k, ((i % 2) * (PW + 9), (i // 2) * (PH // 2 + 6)))
    bogen.save(HIER / "kopf_vergleich.jpg", quality=86)
    for e in ergebnis:
        e.pop("_probe")
    (HIER / "kopf_parameter.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1), encoding="utf-8")
    if not ausfuehren:
        return
    bericht = []
    for e in ergebnis:
        x, werte_jetzt, _, _ = live[("V1", e["start"])]
        if any(abs(werte_jetzt[k] - e["vorher"][k]) > 1e-4 for k in KEYS):
            bericht.append({**e, "gesetzt": False, "grund": "Transform inzwischen geändert"})
            continue
        ok = bool(x.SetProperties({k: float(e["neu"][k]) for k in KEYS}))
        rb = {k: float(x.GetProperty(k)) for k in KEYS}
        bericht.append({**e, "gesetzt": ok, "readback_ok": all(abs(rb[k] - e["neu"][k]) <= 1e-3 * max(1, abs(e["neu"][k])) for k in KEYS)})
    gespeichert = bool(pm.SaveProject())
    (HIER / "kopf_anwendung.json").write_text(json.dumps({"gespeichert": gespeichert, "items": bericht}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gesetzt {sum(1 for b in bericht if b.get('gesetzt') and b.get('readback_ok'))}/{len(bericht)}, gespeichert {gespeichert}")


if __name__ == "__main__":
    main()
