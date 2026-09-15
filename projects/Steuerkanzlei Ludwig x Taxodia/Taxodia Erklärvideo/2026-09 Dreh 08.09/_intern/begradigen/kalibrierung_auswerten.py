"""Kalibrier-Standbilder aus Resolve auswerten: Homographie je Transform-Variante (Taxodia, 15.09.2026).

Aufruf: tools/transcribe/venv/bin/python _intern/begradigen/kalibrierung_auswerten.py
ArUco-Ecken (IDs) im Standbild ↔ Ecken im Rasterbild → Homographie H (Raster-Pixel → Standbild-Pixel), dazu die zentrierte
Form Hc = T⁻¹·H·T (Ursprung Bildmitte, y nach unten). Schreibt kalibrierung/homographien.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HIER = Path(__file__).resolve().parent / "kalibrierung"
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
