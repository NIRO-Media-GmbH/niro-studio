"""Transform-Werte zum Begradigen je Interview-Clip berechnen (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/parameter_berechnen.py
Grundlage:
- lage.json: Schwerkraftvektor aus dem Sony-Beschleunigungssensor (Achsen x links, y oben, z vorwärts; Rollvorzeichen gegen
  Bildlinien geprüft) und Brennweite (KB-äquivalent) → Kameraneigung (Rollen + Nicken) je Clip (Median der Messstellen).
- Resolve-Modell aus der Kalibrierung (kalibrierung/homographien.json, Rest < 0,3 px), Mitte = Ursprung, y nach unten:
  H = T(Pan, −Tilt) · Zoom · R(θ) · P,  R(θ) = [[cos, sin], [−sin, cos]] (θ = RotationAngle, + = gegen den Uhrzeigersinn),
  P = [[1,0,0],[0,1,0],[2·Yaw/W, −2·Pitch/H, 1]] (Keystone um die Bildmitte, wird zuerst angewendet).
Ideal: virtuelle, waagerechte Kamera am selben Ort → H_ideal = K·R_level·K⁻¹. Daraus Pitch/Yaw (Perspektivzeile) und θ.
Die Verschiebung der idealen Kamera (−F·tanβ, bis ~400 px) wird bewusst nicht übernommen: der Bildausschnitt bleibt.
Zoom = kleinster Wert ohne schwarze Ränder; Pan/Tilt in ±1 % der Bildbreite/-höhe optimiert, um den Zoom zu senken.
CTA-Punch-in (#22) = Begradigung · 1,12 mit Pan −200. Schreibt parameter.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HIER = Path(__file__).resolve().parent
W, H = 3840.0, 2160.0
PUNCH = {"zoom": 1.12, "pan": -200.0}


def rotation_zwischen(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(np.dot(a, b))
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


def resolve_h(pitch: float, yaw: float, theta_grad: float, zoom: float, pan: float, tilt: float) -> np.ndarray:
    t = math.radians(theta_grad)
    P = np.array([[1, 0, 0], [0, 1, 0], [2 * yaw / W, -2 * pitch / H, 1]])
    RZ = np.array([[zoom * math.cos(t), zoom * math.sin(t), 0], [-zoom * math.sin(t), zoom * math.cos(t), 0], [0, 0, 1]])
    T = np.array([[1, 0, pan], [0, 1, -tilt], [0, 0, 1]])
    return T @ RZ @ P


def deckt(Hm: np.ndarray) -> float:
    """> 0, wenn das Ausgabebild vollständig aus Quellpixeln besteht (Reserve in Quellpixeln); < 0 = schwarzer Rand."""
    inv = np.linalg.inv(Hm)
    reserve = []
    for x, y in ((-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)):
        q = inv @ np.array([x, y, 1.0])
        if q[2] <= 0:
            return -1e9
        qx, qy = q[0] / q[2], q[1] / q[2]
        reserve += [W / 2 - abs(qx), H / 2 - abs(qy)]
    return min(reserve)


def min_zoom(pitch, yaw, theta, pan, tilt, basis=1.0) -> float:
    lo, hi = basis, basis * 1.5
    if deckt(resolve_h(pitch, yaw, theta, lo, pan, tilt)) >= 0:
        return lo
    for _ in range(60):
        mid = (lo + hi) / 2
        if deckt(resolve_h(pitch, yaw, theta, mid, pan, tilt)) >= 0:
            hi = mid
        else:
            lo = mid
    return hi


def main() -> None:
    lage = json.loads((HIER / "lage.json").read_text())
    out = {}
    for stem, d in lage.items():
        acc = np.median(np.array([m["acc_mittel_g"] for m in d["messungen"]]), axis=0)
        kb = float(np.median([m["kb_mm"][0] for m in d["messungen"]]))
        F = kb / 36.0 * W
        up_cam = np.array([-acc[0], -acc[1], acc[2]])          # Sony (x links, y oben, z vorwärts) → Kamera (x rechts, y unten, z vorwärts)
        roll = math.degrees(math.atan2(up_cam[0], -up_cam[1]))  # + = Welt-Oben kippt im Bild nach rechts
        nick = math.degrees(math.atan2(up_cam[2], math.hypot(up_cam[0], up_cam[1])))  # + = Kamera schaut nach oben
        R = rotation_zwischen(up_cam, np.array([0.0, -1.0, 0.0]))
        K = np.diag([F, F, 1.0])
        Hi = K @ R @ np.linalg.inv(K)
        Hi /= Hi[2, 2]
        g1, g2 = Hi[2, 0], Hi[2, 1]
        P = np.array([[1, 0, 0], [0, 1, 0], [g1, g2, 1]])
        A = Hi @ np.linalg.inv(P)
        L = A[:2, :2]
        theta = math.degrees(math.atan2(L[0, 1] - L[1, 0], L[0, 0] + L[1, 1]))
        pitch, yaw = -g2 * H / 2, g1 * W / 2
        # Zoom minimal, Position in ±1 % zur Entlastung
        bester = (min_zoom(pitch, yaw, theta, 0.0, 0.0), 0.0, 0.0)
        for pan in np.linspace(-W * 0.01, W * 0.01, 9):
            for tilt in np.linspace(-H * 0.01, H * 0.01, 9):
                z = min_zoom(pitch, yaw, theta, float(pan), float(tilt))
                if z < bester[0] - 1e-4:
                    bester = (z, float(pan), float(tilt))
        zoom, pan, tilt = round(bester[0] + 0.0005, 4), round(bester[1], 1), round(bester[2], 1)  # + kleine Reserve
        # Punch-in-Variante (CTA #22 liegt auf FX3_0223)
        z_p = PUNCH["zoom"] * zoom
        pan_p, tilt_p = PUNCH["pan"] + PUNCH["zoom"] * pan, PUNCH["zoom"] * tilt
        if deckt(resolve_h(pitch, yaw, theta, z_p, pan_p, tilt_p)) < 0:
            z_p = min_zoom(pitch, yaw, theta, pan_p, tilt_p, basis=z_p) + 0.0005
        # Kontrolle: verbleibende Neigung der Senkrechten nach Resolve-Transform (Fluchtpunkt der Welt-Senkrechten)
        Hr = resolve_h(pitch, yaw, theta, zoom, pan, tilt)
        vp_welt = K @ (up_cam * -1)  # Bildpunkt des Welt-Unten-Fluchtpunkts (homogen)
        vp_neu = Hr @ vp_welt
        rest_roll = math.degrees(math.atan2(vp_neu[0], vp_neu[1])) if abs(vp_neu[2]) < 1e-12 else math.degrees(math.atan2(vp_neu[0] / vp_neu[2], vp_neu[1] / vp_neu[2]))
        out[stem] = {"acc_median_g": [round(float(v), 4) for v in acc], "kb_mm": kb, "F_px_4k": round(F, 1),
                     "kamera_roll_grad": round(roll, 3), "kamera_nick_grad": round(nick, 3),
                     "resolve": {"RotationAngle": round(theta, 3), "Pitch": round(pitch, 5), "Yaw": round(yaw, 5),
                                 "ZoomX": zoom, "ZoomY": zoom, "Pan": pan, "Tilt": tilt},
                     "resolve_punch_in": {"RotationAngle": round(theta, 3), "Pitch": round(pitch, 5), "Yaw": round(yaw, 5),
                                          "ZoomX": round(z_p, 4), "ZoomY": round(z_p, 4), "Pan": round(pan_p, 1), "Tilt": round(tilt_p, 1)},
                     "ausschnitt_verlust_prozent": round((1 - 1 / zoom) * 100, 2),
                     "kontrolle_rest_neigung_grad": round(((rest_roll + 90) % 180) - 90, 4)}
        print(stem, json.dumps(out[stem], ensure_ascii=False))
    (HIER / "parameter.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
