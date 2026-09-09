"""Zuletzt gebaute AutoCut-Timeline aus Resolve exportieren (FCP7-XML für Premiere-Probecutter; alternativ OTIO/EDL).

Aufruf:
    venv/bin/python scripts/autocut_export_xml.py "<Charge>" [--otio | --edl] [--timeline "<Name>"]

Liest    <Charge>/_intern/autocut/build.json (Timeline-Name des letzten Baus) — oder --timeline.
Schreibt <Charge>/Ergebnisse/Rohschnitt/<Timeline-Name>.xml|.otio|.edl, Export-Vermerk in build.json, Protokoll.
Resolve: nur lesend (Timeline.Export schreibt die Datei auf die Platte, ändert nichts im Projekt).
Exit 0 = exportiert, 1 = Fehler, 2 = kein Bau vorhanden.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402

EXT = {"fcp7xml": ".xml", "otio": ".otio", "edl": ".edl"}
_UNSAFE = re.compile(r'[/\\:*?"<>|]+')


def safe_filename(name: str) -> str:
    return _UNSAFE.sub("-", name).strip() or "timeline"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: gebaute Timeline als FCP7-XML (oder OTIO/EDL) exportieren.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--timeline", help="Timeline-Name (Standard: aus build.json)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--otio", action="store_true", help="OpenTimelineIO statt FCP7-XML")
    g.add_argument("--edl", action="store_true", help="CMX-EDL statt FCP7-XML")
    args = ap.parse_args(argv)
    kind = "otio" if args.otio else "edl" if args.edl else "fcp7xml"
    try:
        ch = Charge.open(args.charge)
        build = ch.read_json("build.json") or {}
        fin = ch.read_json("finalize.json") or {}
        name = args.timeline or (fin.get("timeline") if fin.get("status") == "ok" else None) or build.get("timeline")
        if not name:
            print(f"FEHLER: {ch.autocut / 'build.json'} fehlt oder nennt keine Timeline — erst scripts/autocut_build.py "
                  f"ausführen oder --timeline angeben.", file=sys.stderr)
            return 2
        if not args.timeline and fin.get("status") != "ok" and build.get("status") != "ok":
            print(f"FEHLER: weder Finalisierung noch Bau ok (Bau-Status '{build.get('status')}', Finalisierungs-Status "
                  f"'{fin.get('status')}'; Timeline '{name}') — mit --timeline gezielt exportieren oder neu bauen/finalisieren.",
                  file=sys.stderr)
            return 2
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
        timeline = session.find_timeline(name)
        if timeline is None:
            raise AutoCutError(f"Timeline '{name}' nicht im Projekt '{session.project_name}' gefunden — richtiges "
                               f"Projekt geöffnet?")
        out = ch.ergebnisse / (safe_filename(name) + EXT[kind])
        ch.assert_writable(out)
        path = session.export_timeline(timeline, out, kind)
        stamp = _dt.datetime.now().isoformat(timespec="seconds")
        if build.get("timeline") == name:
            exports = dict(build.get("export") or {})
            exports[kind] = {"pfad": str(path), "exportiert_am": stamp}
            ch.write_json("build.json", {**build, "export": exports})
        append_protokoll(ch, "Export", [f"Timeline '{name}' als {kind} exportiert: {path}"])
        print(f"Exportiert ({kind}): {path}")
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
