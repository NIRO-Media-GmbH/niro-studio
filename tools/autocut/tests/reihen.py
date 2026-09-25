"""Synthetische Frame-Reihen (``verschiebung``) für die Tests der Spec 2026-09-25 (Schnittkanten frame-genau).
Wie ``fake_resolve.py`` ein Helfer-Modul, kein Test."""
from __future__ import annotations


def reihe(*stuecke, t0_s: float = 0.0, fps: float = 25.0) -> dict:
    """``verschiebung`` aus Stücken ``(dauer_s, dx, dy[, zitter])``: je Frame konstante Verschiebung in px @480;
    ``zitter`` wechselt dx von Frame zu Frame um ± zitter (Mittel aus |Δdx| und |Δdy| = zitter)."""
    dx: list[float] = []
    dy: list[float] = []
    for st in stuecke:
        dauer, x, y = st[:3]
        zitter = st[3] if len(st) > 3 else 0.0
        for i in range(int(round(dauer * fps))):
            dx.append(round(x + (zitter if i % 2 else -zitter), 2))
            dy.append(round(y, 2))
    return {"fps": fps, "t0_s": t0_s, "dx": dx, "dy": dy}


def rec(*stuecke, t0_s: float = 0.0, zooms: list | None = None, dauer_s: float | None = None) -> dict:
    """Telemetrie-Datensatz mit Reihe, für stabile_bereiche/ruhe_je_frame/kanten_befunde."""
    return {"verschiebung": reihe(*stuecke, t0_s=t0_s), "zooms": list(zooms or []), "dauer_s": dauer_s}
