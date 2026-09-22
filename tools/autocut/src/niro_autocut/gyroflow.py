"""Gyroflow-Stabilisierung für B-Roll (Spec 2026-09-22): Projektdatei je genutzter Quelldatei neben die Mediendatei,
angewendet per OFX im Schnitt. Kein Render, keine zweite Medienhaltung.

Das Glättungs-Preset kommt aus der Telemetrie (``haltung``), nicht aus einem Festwert. Gyroflows eigener Zoom wird über
``max_zoom`` (Prozent, 100 = kein Beschnitt) so gedeckelt, dass der Brennweitenregel ihre ``digitalzoom_faktor``
garantiert bleiben — deshalb braucht es keine Rückkopplung zwischen beiden Beschnitten.
"""
from __future__ import annotations

import hashlib
import json

from .charge import AutoCutError

CLI_STANDARD = "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
HALTUNG_VORSICHTIG = "stativ"   # Rückfall ohne Telemetrie: wenig glätten, wenig Rand nehmen


def pruefe_deckel(cfg: dict) -> None:
    """Bricht ab, wenn ein ``max_zoom`` der Brennweitenregel ihren Sollzoom nehmen würde.

    ``max_zoom`` ≤ ``digitalzoom_max`` / ``digitalzoom_faktor`` × 100. Wer ``digitalzoom_*`` ändert, muss ``max_zoom``
    mitziehen — sonst stecken beide Beschnitte zusammen über ``digitalzoom_max``."""
    tele = cfg.get("telemetrie") or {}
    faktor, obergrenze = tele.get("digitalzoom_faktor"), tele.get("digitalzoom_max")
    if not faktor or not obergrenze:
        raise AutoCutError("telemetrie.digitalzoom_faktor und telemetrie.digitalzoom_max fehlen in der Config.")
    grenze = float(obergrenze) / float(faktor) * 100.0
    for haltung, wert in ((cfg.get("gyroflow") or {}).get("max_zoom") or {}).items():
        if float(wert) > grenze + 1e-9:
            raise AutoCutError(
                f"gyroflow.max_zoom[{haltung}] = {wert} überschreitet {grenze:.0f} "
                f"(= digitalzoom_max {obergrenze} / digitalzoom_faktor {faktor} × 100).\n"
                f"Entweder max_zoom senken oder telemetrie.digitalzoom_max anheben.")


def preset_fuer(rec: dict, cfg: dict) -> dict:
    """Telemetrie-Datensatz → Gyroflow-Preset. Ohne ``haltung`` gilt die vorsichtigste Stufe."""
    gf = cfg.get("gyroflow") or {}
    haltung = rec.get("haltung") or HALTUNG_VORSICHTIG
    glaettung = (gf.get("glaettung") or {}).get(haltung)
    max_zoom = (gf.get("max_zoom") or {}).get(haltung)
    if glaettung is None or max_zoom is None:
        raise AutoCutError(f"gyroflow.glaettung/max_zoom kennen die Haltung {haltung!r} nicht.")
    return {"version": 2,
            "stabilization": {"smoothing_params": [{"name": "smoothness", "value": float(glaettung)}],
                              "max_zoom": float(max_zoom)}}


def preset_hash(preset: dict) -> str:
    """12 Hex-Zeichen über den Preset-Inhalt; hängt nicht an der Schlüsselreihenfolge."""
    return hashlib.sha1(json.dumps(preset, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
