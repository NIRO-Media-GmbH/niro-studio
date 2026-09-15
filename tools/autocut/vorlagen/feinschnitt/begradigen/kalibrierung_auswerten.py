r"""Vorlage (Stand 15.09.2026): Kalibrier-Standbilder aus Resolve auswerten — Homographie je Transform-Variante.

Aufruf: tools/transcribe/venv/bin/python _intern/begradigen/kalibrierung_auswerten.py   (braucht cv2 mit aruco)
Eingaben: kalibrierung/raster.json (raster_erzeugen.py) und kalibrierung/still_<n>.png je Variante n in der Reihenfolge von
  kalibrierung_resolve.VARIANTEN. Die Standbilder kommen aus dem Quick-Export-Render (Mitte jeder Variante = n·LAENGE + LAENGE/2,
  bei 25 fps LAENGE = 125), weil ExportCurrentFrameAsStill die Inspector-Transformationen nicht enthält (zsh, im Ordner kalibrierung/):
    rm -f still_*.png; for n in {0..11}; do f=$((n*125+62)); ffmpeg -v error -y -i kalibrierung_render.mov -vf "select=eq(n\,$f)" -frames:v 1 -update 1 "still_$n.png"; done
ArUco-Ecken (IDs, Subpixel-verfeinert) im Standbild ↔ Ecken im Rasterbild → Homographie H (Raster-Pixel → Standbild-Pixel),
dazu die zentrierte Form Hc = T⁻¹·H·T (Ursprung Bildmitte, y nach unten).
Schreibt kalibrierung/homographien.json {Variante: {marker, rest_px_mittel, rest_px_max, H, Hc}}. Nichts in Resolve.
Ergebnis 15.09.2026 (Resolve 21.1, Rest < 0,3 px) → parameter_berechnen.resolve_h:
  H = T(Pan, −Tilt) · Zoom · R(θ) · P,  R(θ) = [[cos, sin], [−sin, cos]] (θ = RotationAngle in Grad, + = gegen den Uhrzeigersinn),
  P = Trapezverzerrung um die Bildmitte mit Perspektivzeile [2·Yaw/W, −2·Pitch/H, 1], zuerst angewendet;
  Pan + = rechts, Tilt + = oben, beide in Timeline-Pixeln.
Herkunft: Taxodia-Charge, _intern/begradigen/kalibrierung_auswerten.py
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HIER = Path(__file__).resolve().parent / "kalibrierung"

# ── ANPASSEN je Charge ─────────────────────────────
# keine eigenen Werte: Rastergröße aus kalibrierung/raster.json, Variantennamen in der Reihenfolge von kalibrierung_resolve.VARIANTEN
# ── Ende ANPASSEN ──────────────────────────────────

VARIANTEN = ["identitaet", "rot5", "pitch0.1", "yaw0.1", "pitch0.3", "zoom1.2", "pan200_tilt100", "kombi", "pitch-0.1",
             "yaw-0.2", "pitch0.1_yaw0.1", "rot5_pitch0.1"]


def main() -> None:
    raster = json.loads((HIER / "raster.json").read_text())
    W, H = raster["W"], raster["H"]
    T = np.array([[1, 0, W / 2], [0, 1, H / 2], [0, 0, 1]], float)
    det = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250), cv2.aruco.DetectorParameters())
    out = {}
    for n, name in enumerate(VARIANTEN):
        img = cv2.imread(str(HIER / f"still_{n}.png"), cv2.IMREAD_GRAYSCALE)
        ecken, ids, _ = det.detectMarkers(img)
        if ids is None:
            print(name, "keine Marker")
            continue
        quelle, ziel = [], []
        for c, i in zip(ecken, ids.ravel()):
            # Subpixel-Verfeinerung der vier Ecken
            pts = cv2.cornerSubPix(img, c.reshape(4, 1, 2).astype(np.float32), (5, 5), (-1, -1),
                                   (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.01)).reshape(4, 2)
            quelle += raster["ecken"][str(int(i))]
            ziel += pts.tolist()
        q, z = np.array(quelle, float), np.array(ziel, float)
        Hm, _ = cv2.findHomography(q, z, 0)
        Hm /= Hm[2, 2]
        rest = np.linalg.norm(cv2.perspectiveTransform(q.reshape(-1, 1, 2), Hm).reshape(-1, 2) - z, axis=1)
        Hc = np.linalg.inv(T) @ Hm @ T
        Hc /= Hc[2, 2]
        out[name] = {"marker": int(len(ids)), "rest_px_mittel": round(float(rest.mean()), 3), "rest_px_max": round(float(rest.max()), 3),
                     "H": Hm.tolist(), "Hc": Hc.tolist()}
        np.set_printoptions(precision=6, suppress=True)
        print(f"== {name}: {len(ids)} Marker, Rest {rest.mean():.3f}/{rest.max():.3f} px\n{Hc}")
    (HIER / "homographien.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
