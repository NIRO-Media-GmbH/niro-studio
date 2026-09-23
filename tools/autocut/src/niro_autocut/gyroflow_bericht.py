"""Bericht zum Gyroflow-Lauf (Spec 2026-09-22): welche Clips ein Sidecar bekamen und welche warum nicht.

Was der Bericht **nicht** kann: Gyroflows tatsächlichen Beschnitt nennen. Die Zoom-Spalte zeigt den Deckel aus
``gyroflow.max_zoom`` als Obergrenze, nicht als Messwert — die Normierung der Zoom-Werte in der Projektdatei ist
ungeklärt (Spec Befund 1, Punkt 6), ``zoom_ist_lesen`` liefert darum immer den Rückfall. Das muss in der Anzeige
stehen, nicht nur im Docstring: eine nackte Zahl wie „1,20×" läse sich wie eine Messung."""
from __future__ import annotations

from pathlib import Path

from .gyroflow import norm_pfad


def _zoom_text(c: dict) -> str:
    """Zoomspalte je Clip. ``zoom_gedeckelt`` heißt heute immer „Deckelwert statt Messwert" — das muss dranstehen."""
    if c.get("zoom_ist") is None:
        return "—"
    wert = f"{float(c['zoom_ist']):.2f}".replace(".", ",")
    return f"≤ {wert}× (Deckelwert, nicht gemessen)" if c.get("zoom_gedeckelt") else f"{wert}×"


def bericht_md(erg: dict, clips: list[dict]) -> str:
    clips_ = erg.get("clips") or []
    uebersprungen = erg.get("uebersprungen") or []
    # Join über den vollen aufgelösten Pfad wie in gyroflow_charge — der Clip-Stamm allein ist nicht eindeutig:
    # Kartennummern setzen pro Karte/Dreh neu auf, zwei Quelldateien können denselben Stamm tragen.
    # norm_pfad auf beiden Seiten: Path.resolve() allein lässt NFD ≠ NFC stehen (siehe dessen Docstring).
    tempo50 = {norm_pfad(c["datei"]) for c in (clips or []) if c.get("tempo50")}
    fehler = [c for c in clips_ if c.get("fehler")]
    sidecars = [c for c in clips_ if c.get("sidecar")]

    z = [f"# Gyroflow — {len(sidecars)} Sidecars ({erg.get('stand', '')})", ""]
    # „stabilisiert" wäre zu viel versprochen: dieser Lauf schreibt Sidecars, angewendet werden sie erst im 6d-Bau.
    z.append(f"{len(sidecars)} von {len(clips_)} Clips mit Sidecar, "
             f"{len(uebersprungen)} übersprungen, {len(fehler)} mit Fehler. "
             f"Angewendet wird das erst beim Bau (6d, Fusion-Comp je Clip).")
    z += ["", "| Clip | Kamera | Haltung | Zoom | Tempo |", "|---|---|---|---|---|"]
    for c in clips_:
        tempo = "50 %" if c.get("path") and norm_pfad(c["path"]) in tempo50 else "100 %"
        z.append(f"| {c.get('clip')} | {c.get('kamera') or '—'} | {c.get('haltung') or '—'} | "
                 f"{_zoom_text(c)} | {tempo} |")

    if sidecars:
        # Bis 23.09. stand hier ein Abschnitt „Deckel griff", der jeden exportierten Clip aufführte und behauptete,
        # Gyroflow habe schwächer geglättet als möglich. Das ist ungemessen (und bei einem Stativ-Shot mit
        # max_zoom 105 fast sicher falsch). Stattdessen sagt der Bericht, was er weiß und was nicht.
        z += ["", "## Zoom — Obergrenze, kein Messwert", "",
              "Die Zoom-Spalte nennt `gyroflow.max_zoom` der jeweiligen Haltung. Was Gyroflow tatsächlich vom Rand "
              "nimmt, liest die Pipeline nicht zurück: die Normierung der Zoom-Werte in der Projektdatei ist "
              "ungeklärt (Spec 2026-09-22, Befund 1 Punkt 6). Der echte Beschnitt liegt darunter — bei ruhigen "
              "Stativ-Shots vermutlich deutlich.", "",
              "Dazu kommt der digitale Zoom der Brennweitenregel **obendrauf**; die beiden sind heute nicht "
              "verrechnet. Er geht bis `telemetrie.digitalzoom_max` (1,5), schlimmster Fall also 1,2 × 1,5 = 1,8× "
              "auf einer 4K-Quelle. Beurteilen lässt sich das derzeit nur am Bild."]

    if uebersprungen:
        z += ["", "## Übersprungen", ""]
        z += [f"- {Path(u['datei']).name} — {u['grund']}" for u in uebersprungen]

    if fehler:
        z += ["", "## Fehler", ""]
        z += [f"- {c.get('clip')} — {c['fehler']}" for c in fehler]

    return "\n".join(z) + "\n"
