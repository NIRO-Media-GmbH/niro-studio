"""Gyroflow-Sidecars für die im Feinschnitt genutzten B-Roll-Shots (Spec 2026-09-22) → <clip>.gyroflow neben der
Mediendatei, _intern/autocut/gyroflow.json, Bericht Ergebnisse/Rohschnitt/gyroflow.md.

Aufruf:
    venv/bin/python scripts/autocut_gyroflow.py "<Charge>" [--force] [--dry-run]

Eingabe: _intern/autocut/gyroflow_clips.json (schreibt der Probelauf von feinschnitt_bauen.py) und
_intern/autocut/telemetrie.json. Rendert nie. Exit 1 bei Fehlern, 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.gyroflow import gyroflow_charge  # noqa: E402
from niro_autocut.gyroflow_bericht import bericht_md  # noqa: E402


def _json_laden(pfad: Path, erzeuger: str):
    """Zwischendatei lesen; eine kaputte gibt eine deutsche Meldung statt eines rohen Tracebacks."""
    if not pfad.exists():
        raise AutoCutError(f"{pfad} fehlt.\n{erzeuger}")
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        raise AutoCutError(f"{pfad} ist nicht lesbar ({type(e).__name__}: {e}).\n"
                           f"Datei löschen und neu erzeugen: {erzeuger}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Gyroflow-Sidecars für die genutzten B-Roll-Shots.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--force", action="store_true", help="Cache verwerfen und alle Sidecars neu erzeugen")
    ap.add_argument("--dry-run", action="store_true", help="nur nennen, was passieren würde")
    a = ap.parse_args(argv)

    try:
        ch = Charge.open_basis(a.charge)
        clips = _json_laden(
            ch.autocut / "gyroflow_clips.json",
            "Zuerst den Probelauf von _intern/feinschnitt_bauen.py laufen lassen — "
            "er schreibt die genutzten B-Roll-Shots aus der BROLL-Tabelle.")
        telemetrie = _json_laden(
            ch.autocut / "telemetrie.json",
            "Zuerst scripts/autocut_telemetrie.py für diese Charge laufen lassen.")

        if a.dry_run:
            print(f"{len(clips)} genutzte Shots, {len({c['datei'] for c in clips})} Quelldateien.")
            return 0

        erg = gyroflow_charge(ch, clips, telemetrie, ch.config, force=a.force)
        md = bericht_md(erg, clips)
        ziel = ch.ergebnisse / "gyroflow.md"
        ch.assert_writable(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(md, encoding="utf-8")
        print(md)
        append_protokoll(ch, "Gyroflow-Sidecars",
                         [f"{len(erg['clips'])} Sidecars, {len(erg['uebersprungen'])} übersprungen",
                          f"Bericht: {ziel}"])
        return 1 if any(c.get("fehler") for c in erg["clips"]) else 0
    except AutoCutError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
