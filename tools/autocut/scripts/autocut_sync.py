"""Kamerapaare der Charge synchronisieren (Waveform-Kreuzkorrelation) → <Charge>/_intern/autocut/sync.json.

Aufruf:
    venv/bin/python scripts/autocut_sync.py "<Charge>" [--ordner "Johanna_Notaufnahme" ...]

Voraussetzung: media.json aus autocut_prepare.py. Audio der Originale wird als 16-kHz-Mono-WAV nach
_intern/autocut/work/audio extrahiert (gecacht per Fingerprint; NAS nur lesend).
Mit --ordner werden nur diese Interview-Ordner gerechnet, die übrigen Paare der vorhandenen sync.json bleiben.

Exit 1, wenn ein gerechneter Interview-Ordner mit Kamerapaaren ohne ok-Paar bleibt — sync.json wird
trotzdem geschrieben (Warnung, kein Abbruch). Ordner ohne a7-Clip zählen nicht als Fehler.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.sync import sync_charge  # noqa: E402


def print_table(sync: dict) -> None:
    rows = sync.get("paare", [])
    if not rows:
        print("Keine Kamerapaare gerechnet.")
        return
    head = f"{'Ordner':<34} {'FX3':<12} {'a7':<24} {'Frames':>7} {'Sek.':>8} {'Konf':>6} {'Drift':>6}  ok  Hinweis"
    print(head)
    print("-" * len(head))
    for p in rows:
        folder = Path(p["ref"]).parent.name
        print(f"{folder[:34]:<34} {Path(p['ref']).stem[:12]:<12} {Path(p['other']).stem[:24]:<24} "
              f"{p['offset_frames']:>+7d} {p['offset_s']:>+8.3f} {p['confidence']:>6.1f} {p['drift_frames']:>+6.2f}  "
              f"{'ja' if p['ok'] else 'NEIN'}  {p.get('note', '')}")


def ordner_ohne_ok(media: dict, sync: dict, nur_ordner: list[str] | None) -> list[str]:
    """Interview-Ordner mit Kamerapaaren, aber ohne ok-Paar (nur gerechnete Ordner)."""
    ok_folders = {Path(p["ref"]).parent.name for p in sync.get("paare", []) if p["ok"]}
    out = []
    for folder, grp in media.get("ordner", {}).items():
        if nur_ordner and folder not in nur_ordner:
            continue
        if grp.get("ton") and grp.get("kontext") and folder not in ok_folders:
            out.append(folder)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Kamerapaare synchronisieren (sync.json).")
    ap.add_argument("charge", help="Pfad zur Charge (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--ordner", nargs="+", help="nur diese Interview-Ordner rechnen (Rest aus sync.json übernehmen)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        media = ch.read_json("media.json")
        if not media:
            raise AutoCutError(f"{ch.autocut / 'media.json'} fehlt — erst scripts/autocut_prepare.py ausführen.")
        print(f"Charge: {ch.root}\nAudio:  {ch.work / 'audio'} (Cache per Fingerprint)\n")
        sync = sync_charge(ch, media, nur_ordner=args.ordner)
        print()
        print_table(sync)
        print(f"\nGeschrieben: {ch.autocut / 'sync.json'} ({len(sync['paare'])} Paare, "
              f"{sum(1 for p in sync['paare'] if p['ok'])} ok)")
        for folder, grp in media.get("ordner", {}).items():
            if (not args.ordner or folder in args.ordner) and grp.get("ton") and not grp.get("kontext"):
                print(f"Hinweis: {folder} hat keinen a7-Clip — V2 bleibt dort leer.")
        fehl = ordner_ohne_ok(media, sync, args.ordner)
        if fehl:
            print("WARNUNG: kein ok-Paar in: " + ", ".join(fehl)
                  + "\n  Versatz dort von Hand prüfen oder Rückfallebene Resolve-AutoSync (nur auf Anweisung).",
                  file=sys.stderr)
            return 1
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
