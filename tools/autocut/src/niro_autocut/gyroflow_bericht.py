"""Bericht zum Gyroflow-Lauf (Spec 2026-09-22): welche Clips ein Sidecar bekamen, welche warum nicht, wo der
Zoom-Deckel griff. Der Deckel hält den Rand-Haushalt ohnehin ein — die Liste zeigt, wo Gyroflow schwächer glättete
als es könnte, damit der User entscheiden kann, telemetrie.digitalzoom_max anzuheben."""
from __future__ import annotations

from pathlib import Path

from .gyroflow import norm_pfad


def bericht_md(erg: dict, clips: list[dict]) -> str:
    clips_ = erg.get("clips") or []
    uebersprungen = erg.get("uebersprungen") or []
    # Join über den vollen aufgelösten Pfad wie in gyroflow_charge — der Clip-Stamm allein ist nicht eindeutig:
    # Kartennummern setzen pro Karte/Dreh neu auf, zwei Quelldateien können denselben Stamm tragen.
    # norm_pfad auf beiden Seiten: Path.resolve() allein lässt NFD ≠ NFC stehen (siehe dessen Docstring).
    tempo50 = {norm_pfad(c["datei"]) for c in (clips or []) if c.get("tempo50")}
    fehler = [c for c in clips_ if c.get("fehler")]
    gedeckelt = [c for c in clips_ if c.get("zoom_gedeckelt")]
    sidecars = [c for c in clips_ if c.get("sidecar")]

    z = [f"# Gyroflow — {len(sidecars)} Sidecars ({erg.get('stand', '')})", ""]
    z.append(f"{len(clips_) - len(fehler)} von {len(clips_)} Clips stabilisiert, "
             f"{len(uebersprungen)} übersprungen, {len(fehler)} mit Fehler.")
    z += ["", "| Clip | Kamera | Haltung | Zoom | Tempo |", "|---|---|---|---|---|"]
    for c in clips_:
        zoom = "—" if c.get("zoom_ist") is None else f"{c['zoom_ist']:.2f}×"
        if c.get("zoom_gedeckelt"):
            zoom += " (gedeckelt)"
        tempo = "50 %" if c.get("path") and norm_pfad(c["path"]) in tempo50 else "100 %"
        z.append(f"| {c.get('clip')} | {c.get('kamera') or '—'} | {c.get('haltung') or '—'} | {zoom} | {tempo} |")

    if gedeckelt:
        z += ["", "## Deckel griff", "",
              "Bei diesen Clips glättet Gyroflow schwächer, als es könnte — der Rand ist ausgereizt. "
              "Mehr Glättung gäbe es nur über ein höheres `telemetrie.digitalzoom_max`.", ""]
        z += [f"- {c.get('clip')} ({c.get('haltung') or '—'})" for c in gedeckelt]

    if uebersprungen:
        z += ["", "## Übersprungen", ""]
        z += [f"- {Path(u['datei']).name} — {u['grund']}" for u in uebersprungen]

    if fehler:
        z += ["", "## Fehler", ""]
        z += [f"- {c.get('clip')} — {c['fehler']}" for c in fehler]

    return "\n".join(z) + "\n"
