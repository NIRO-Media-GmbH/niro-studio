"""Vorlage (Stand 15.09.2026): Bildlinien der Interview-Setups messen — Rollwinkel + Fluchtpunkte als Gegenprobe zu lage.json.

Aufruf: tools/transcribe/venv/bin/python _intern/begradigen/linien_messen.py   (braucht cv2 mit LSD)
Eingaben: proben.json (proben_waehlen.py; dieses venv hat kein rapidfuzz und lädt feinschnitt_bauen.py nicht),
  lage.json (lage_messen.py, Brennweite), ../color/grading_vorschlag.json (CDL je Person/Set und Kamera),
  Proxys <Clip-Ordner>/Proxy/<Clip-Stamm>.mov in W×H, ../gesichtscheck/faces (Vision-Gesichtsboxen), ../color/skripte/colorlib.py.
Je Interview-Clip 4 Proxy-Frames aus dem genutzten Bereich → Grade (CDL + LC-709, colorlib) → Graustufen → LSD-Liniensegmente
(≥ 90 px bei 1920×1080), Person maskiert (Vision-Gesichtsbox, nach unten und seitlich erweitert).
- Senkrechte (±12° zur Vertikalen): Fluchtpunkt per gewichteter Kleinste-Quadrate-Lösung → Rollwinkel an der Bildmitte
  und Neigung (Stürzen) über die Brennweite aus lage.json.
- Waagerechte (±15°): Fluchtpunkt → Gier (Yaw) nur aussagekräftig, wenn eine frontale Wand dominiert.
Ergebnis: frames/<Clip>_<n>.jpg, linien.json + Prüfbilder linien_<Clip>.jpg (Senkrechte grün, Waagerechte blau, Maske rot).
Nichts in Resolve. Optional: nur Gegenprobe, parameter_berechnen.py nutzt lage.json.
Befund (15.09.): Rollwinkel aus Bildlinien und aus dem Beschleunigungssensor stimmen bei Setups mit echten Architekturkanten
auf 0,1–0,3° überein; bei wenigen Senkrechten (kaum Architekturkanten) streut die Linienmessung deutlich stärker.
Herkunft: Taxodia-Charge, _intern/begradigen/linien_messen.py
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
sys.path.insert(0, str(INTERN / "color" / "skripte"))
import colorlib as CL  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
W, H = 1920, 1080  # Auflösung der Proxys in px (ffmpeg liefert Rohbilder in dieser Größe; fehlt der Proxy, muss das Original so groß sein)
SENSOR_BREITE_MM = {"FX3": 35.6, "a7MK4": 35.9}  # Standard (15.09.): Sensorbreite in mm; Clip-Stamm „FX3…" → FX3, sonst a7MK4
LUT_DATEI = "SLog3SGamut3.CineToLC-709.cube"  # Standard (15.09.): Sony-LUT in colorlib.LUTDIR, wie beim Grading der Charge
GRUPPE = {  # Clip-Stamm → (Person/Set, Kamera) = Schlüssel in grading_vorschlag.json["cdl_je_kamera_und_set"]
    # "FX3_0001": ("Person A", "FX3"),   (Kamera-Schlüssel wie im Grading-Vorschlag, z. B. "FX3" / "a7_IV")
}
# ── Ende ANPASSEN ──────────────────────────────────


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def frame(pfad: str, t: float) -> np.ndarray:
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", proxy(pfad), "-frames:v", "1", "-an",
                        "-f", "rawvideo", "-pix_fmt", "yuv444p", "-"], capture_output=True, check=True).stdout
    return CL.yuv_to_rgb(np.frombuffer(b, np.uint8).reshape(3, H, W)).astype(np.float32)


def fluchtpunkt(segs: np.ndarray) -> np.ndarray | None:
    """Homogener Punkt v, der Σ w (l·v)² minimiert (l = normierte Geraden, w = Länge); zentrierte Koordinaten."""
    if len(segs) < 3:
        return None
    p1 = np.c_[segs[:, 0] - W / 2, segs[:, 1] - H / 2, np.ones(len(segs))]
    p2 = np.c_[segs[:, 2] - W / 2, segs[:, 3] - H / 2, np.ones(len(segs))]
    l = np.cross(p1, p2)
    l /= np.linalg.norm(l[:, :2], axis=1, keepdims=True)
    w = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    A = (l * w[:, None]).T @ l
    _, vecs = np.linalg.eigh(A)
    return vecs[:, 0]


def main() -> None:
    # Probezeiten je Clip kommen aus dem Feinschnitt-Plan (autocut-venv schreibt proben.json; dieses venv hat kein rapidfuzz)
    proben = json.loads((HIER / "proben.json").read_text())
    fehlend = sorted({Path(c).stem for c in proben} - GRUPPE.keys())
    if fehlend:
        raise SystemExit(f"GRUPPE im ANPASSEN-Block fehlt für: {fehlend}")
    vorschlag = json.loads((INTERN / "color" / "grading_vorschlag.json").read_text())
    lage = json.loads((HIER / "lage.json").read_text())
    lut = CL.load_cube(CL.LUTDIR + LUT_DATEI)
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    out = {}
    bilder_dir = HIER / "frames"
    bilder_dir.mkdir(exist_ok=True)
    for clip, zeiten in sorted(proben.items()):
        stem = Path(clip).stem
        person, cam = GRUPPE[stem]
        w = vorschlag["cdl_je_kamera_und_set"][person][cam]["node1_gesamt_log_vor_LUT"]
        f_mm = lage[stem]["messungen"][0]["brennweite_mm"][0]
        f_px = f_mm / SENSOR_BREITE_MM["FX3" if stem.startswith("FX3") else "a7MK4"] * W
        alle_v, alle_h = [], []
        for n, t in enumerate(zeiten):
            rgb = CL.apply_lut(CL.cdl(frame(clip, t), w["slope"], w["offset"], (1, 1, 1), w["saturation"]), lut)
            u8 = CL.to_u8(rgb)
            jpg = bilder_dir / f"{stem}_{n}.jpg"
            Image.fromarray(u8).save(jpg, quality=92)
            gray = cv2.cvtColor(u8, cv2.COLOR_RGB2GRAY)
            segs = lsd.detect(gray)[0]
            segs = np.zeros((0, 4)) if segs is None else segs.reshape(-1, 4)
            laenge = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
            segs = segs[laenge >= 90]
            alle_v.append((jpg, segs))
        # Person maskieren: Gesichtsboxen aller Frames (Vision)
        tsv = subprocess.run([str(INTERN / "gesichtscheck" / "faces"), str(bilder_dir)], capture_output=True, text=True, check=True).stdout
        boxen = {}
        for z in tsv.splitlines():
            name, _, rest = z.partition("\t")
            if name.startswith(stem) and rest and rest != "ERR":
                boxen[name] = [tuple(map(float, b.split(","))) for b in rest.split(";")]
        v_segs, h_segs = [], []
        for jpg, segs in alle_v:
            maske = np.zeros((H, W), bool)
            for x0, y0, x1, y1, c in boxen.get(jpg.name, []):
                if c < 0.5:
                    continue
                bw, bh = (x1 - x0) * W, (y1 - y0) * H
                mx0, mx1 = int(max(0, x0 * W - 1.6 * bw)), int(min(W, x1 * W + 1.6 * bw))
                maske[int(max(0, y0 * H - 0.6 * bh)):, mx0:mx1] = True
            if not len(segs):
                continue
            mitte_x = ((segs[:, 0] + segs[:, 2]) / 2).astype(int).clip(0, W - 1)
            mitte_y = ((segs[:, 1] + segs[:, 3]) / 2).astype(int).clip(0, H - 1)
            frei = ~maske[mitte_y, mitte_x]
            s = segs[frei]
            winkel = np.degrees(np.arctan2(s[:, 3] - s[:, 1], s[:, 2] - s[:, 0])) % 180
            v_segs.append(s[np.abs(winkel - 90) <= 12])
            h_segs.append(s[(winkel <= 15) | (winkel >= 165)])
            # Prüfbild für das erste Frame
            if jpg.name.endswith("_0.jpg"):
                im = cv2.cvtColor(np.array(Image.open(jpg)), cv2.COLOR_RGB2BGR)
                im[maske] = (im[maske] * 0.55 + np.array([0, 0, 110])).astype(np.uint8)
                for x1_, y1_, x2_, y2_ in s[np.abs(winkel - 90) <= 12]:
                    cv2.line(im, (int(x1_), int(y1_)), (int(x2_), int(y2_)), (0, 255, 0), 3)
                for x1_, y1_, x2_, y2_ in s[(winkel <= 15) | (winkel >= 165)]:
                    cv2.line(im, (int(x1_), int(y1_)), (int(x2_), int(y2_)), (255, 128, 0), 3)
                cv2.imwrite(str(HIER / f"linien_{stem}.jpg"), cv2.resize(im, (960, 540)), [cv2.IMWRITE_JPEG_QUALITY, 85])
        V = np.vstack(v_segs) if v_segs else np.zeros((0, 4))
        Hs = np.vstack(h_segs) if h_segs else np.zeros((0, 4))
        erg = {"f_mm": f_mm, "f_px_1080": round(f_px, 1), "senkrechte": int(len(V)), "waagerechte": int(len(Hs))}
        # Rollwinkel: längengewichteter Median der Abweichung von der Senkrechten (Bild-y nach unten; + = oben nach rechts gekippt)
        if len(V):
            dx, dy = V[:, 2] - V[:, 0], V[:, 3] - V[:, 1]
            sgn = np.where(dy < 0, -1, 1)
            abw = np.degrees(np.arctan2(dx * sgn, dy * sgn))  # Winkel der nach unten zeigenden Richtung zur +y-Achse
            gew = np.hypot(dx, dy)
            o = np.argsort(abw)
            kum = np.cumsum(gew[o])
            erg["roll_median_grad"] = round(float(abw[o][np.searchsorted(kum, kum[-1] / 2)]), 3)
            vp = fluchtpunkt(V)
            if vp is not None:
                if abs(vp[2]) < 1e-12:
                    erg["vp_senkrecht"] = "unendlich"
                else:
                    x, y = vp[0] / vp[2], vp[1] / vp[2]
                    erg["vp_senkrecht_px"] = [round(float(x)), round(float(y))]
                    # Neigung aus Abstand des Fluchtpunkts: tan(pitch) = f / |VP|; Roll = Richtung zum VP
                    d = math.hypot(x, y)
                    erg["pitch_aus_vp_grad"] = round(math.degrees(math.atan2(f_px, d)) * (1 if y > 0 else -1), 3)
                    erg["roll_aus_vp_grad"] = round(math.degrees(math.atan2(x, y)) if y > 0 else math.degrees(math.atan2(-x, -y)), 3)
        if len(Hs) >= 3:
            vp = fluchtpunkt(Hs)
            if vp is not None and abs(vp[2]) > 1e-12:
                erg["vp_waagerecht_px"] = [round(float(vp[0] / vp[2])), round(float(vp[1] / vp[2]))]
        out[stem] = erg
        print(stem, json.dumps(erg, ensure_ascii=False), flush=True)
    (HIER / "linien.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
