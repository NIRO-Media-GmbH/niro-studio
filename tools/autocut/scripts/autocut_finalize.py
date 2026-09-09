"""Stufe 5: roh-Timeline finalisieren (Pegel True Peak −3 je FX3-Clip, Zeitlupen, End-Timeline) — Spec v2 Abschnitt 4.

Aufruf:
    venv/bin/python scripts/autocut_finalize.py "<Charge>" [--keep-roh]

Liest build.json, timeline.json, broll_build.json (optional), probe_xml.json (Pflicht). Schreibt ton.json, work/xml/*,
finalize.json, ergänzt Ergebnisse/Rohschnitt/<video>-rohschnitt.md um den Pegel-Abschnitt, Protokoll-Eintrag.
Resolve: exportiert die roh-Timeline, importiert die End-Timeline, löscht danach NUR die eigene roh-Timeline (ohne --keep-roh).
Exit 0 = fertig, 1 = Fehler (End-Timeline „… FEHLER“, roh bleibt), 2 = Vorbedingung fehlt.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.finalize import finalize  # noqa: E402
from niro_autocut.report import merge_section, render_pegel  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut Stufe 5: roh-Timeline finalisieren (Pegel, Zeitlupe, End-Timeline).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--keep-roh", action="store_true", help="roh-Timeline nach Erfolg behalten")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        build = ch.read_json("build.json") or {}
        if build.get("status") != "ok" or not ch.read_json("timeline.json"):
            print(f"FEHLER: {ch.autocut / 'build.json'} fehlt/nicht ok — erst scripts/autocut_build.py.", file=sys.stderr)
            return 2
        if not (ch.read_json("probe_xml.json") or {}).get("level_import_ok"):
            print(f"FEHLER: {ch.autocut / 'probe_xml.json'} fehlt oder level_import_ok=false — erst scripts/resolve_probe_xml.py.",
                  file=sys.stderr)
            return 2
        session = RA.ResolveSession(RA.connect(), probe=ch.read_json("probe.json"), path_map=ch.config.get("path_map"))
        print(f"Resolve {session.version}, Projekt '{session.project_name}' — roh-Timeline '{build['timeline']}'")
        try:
            out = finalize(ch, session, ch.config, keep_roh=args.keep_roh)
        except AutoCutError as e:
            zeilen = [str(e).splitlines()[0]]
            if (ch.autocut / "finalize.json").exists():
                zeilen.append(f"Details: {ch.autocut / 'finalize.json'}")
            append_protokoll(ch, "Finalisieren FEHLER", zeilen)
            print(f"FEHLER: {e}", file=sys.stderr)
            return 1
        video = Path(str(build.get("video") or "video")).stem
        rep = ch.ergebnisse / f"{video}-rohschnitt.md"
        ton = ch.read_json("ton.json") or {}
        if rep.exists():
            ch.assert_writable(rep)
            rep.write_text(merge_section(rep.read_text(encoding="utf-8"), "## Pegel", render_pegel(ton)), encoding="utf-8")
        zeilen = [f"End-Timeline „{out['timeline']}“ aus „{out['timeline_roh']}“: {out['items_geprueft']} Items geprüft, "
                  f"{out['levels_set']} Pegel (True Peak {ton.get('ziel_dbtp', -3)} dBTP), {out['speeds_set']} Zeitlupen, "
                  f"{out['markers']} Marker, roh {'gelöscht' if out['roh_geloescht'] else 'behalten'}",
                  f"Dateien: {ch.autocut / 'finalize.json'}, {ch.autocut / 'ton.json'}, {out['xml_final']}"]
        zeilen += [f"Warnung: {w}" for w in out["warnings"][:10]]
        append_protokoll(ch, "Finalisieren", zeilen)
        print("\n".join(zeilen))
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
