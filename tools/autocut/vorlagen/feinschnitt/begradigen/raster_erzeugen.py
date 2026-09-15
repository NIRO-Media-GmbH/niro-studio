"""Vorlage (Stand 15.09.2026): ArUco-Raster für die Vermessung der Resolve-Transformation erzeugen.

Aufruf: tools/transcribe/venv/bin/python _intern/begradigen/raster_erzeugen.py   (braucht cv2 mit aruco)
Schreibt _intern/begradigen/kalibrierung/raster.png (W×H, weiß, Marker DICT_4X4_250, GROESSE px, Raster ABSTAND px)
und kalibrierung/raster.json {"W", "H", "ecken": {Marker-ID: [[x, y] oben links, oben rechts, unten rechts, unten links]}}
und prüft, dass alle Marker im eigenen Bild erkannt werden. Nichts in Resolve.
Weiter: kalibrierung_resolve.py aufbauen (importiert raster.png) → … → kalibrierung_auswerten.py (liest raster.json).
Herkunft: Taxodia-Session, inline im Session-Transkript (15.09.2026, kein eigenes Skript)
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

HIER = Path(__file__).resolve().parent / "kalibrierung"

# ── ANPASSEN je Charge ─────────────────────────────
W, H = 3840, 2160  # Auflösung der Feinschnitt-Timeline in px (= kalibrierung_resolve.W/H, parameter_berechnen.W/H)
GROESSE, ABSTAND = 150, 300  # Standard (15.09.): Markergröße und Rasterabstand in px (bei 3840×2160: 12 × 7 = 84 Marker)
# ── Ende ANPASSEN ──────────────────────────────────


def main() -> None:
    HIER.mkdir(parents=True, exist_ok=True)
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    img = np.full((H, W), 255, np.uint8)
    ecken = {}
    mid = 0
    ys = list(range(105, H - GROESSE, ABSTAND))
    xs = list(range(120, W - GROESSE, ABSTAND))
    for y in ys:
        for x in xs:
            m = cv2.aruco.generateImageMarker(d, mid, GROESSE)
            img[y:y + GROESSE, x:x + GROESSE] = m
            ecken[mid] = [[x, y], [x + GROESSE, y], [x + GROESSE, y + GROESSE], [x, y + GROESSE]]
            mid += 1
    cv2.imwrite(str(HIER / "raster.png"), img)
    (HIER / "raster.json").write_text(json.dumps({"W": W, "H": H, "ecken": ecken}), encoding="utf-8")
    det = cv2.aruco.ArucoDetector(d, cv2.aruco.DetectorParameters())
    c, ids, _ = det.detectMarkers(img)
    print("Marker gesetzt:", mid, "erkannt:", 0 if ids is None else len(ids), "Raster", len(xs), "x", len(ys))


if __name__ == "__main__":
    main()
