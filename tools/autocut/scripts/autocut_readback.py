"""Bau-Readback einer Timeline schreiben (Resolve nur lesend) — nach Vorlagen-Bauten (Stufe 3a/6d), damit die
Replay-Runde Handänderungen seit dem Bau erkennt (Spec docs/superpowers/specs/2026-09-16-autocut-replay-design.md, 2.5).

Aufruf:
    venv/bin/python scripts/autocut_readback.py "<Charge>" --timeline "<Name>"

Schreibt _intern/autocut/readback/<Titel>.json. Exit 0 = geschrieben, 2 = Voraussetzung fehlt.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import readback as RB  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Bau-Readback einer Timeline schreiben (Resolve nur lesend).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--timeline", required=True, help="exakter Timeline-Name")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open_basis(args.charge)
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
        tl = session.find_timeline(args.timeline)
        if tl is None:
            raise AutoCutError(f"Timeline '{args.timeline}' ist nicht im offenen Projekt '{session.project_name}'.")
        print(f"Bau-Readback: {RB.schreiben(ch, session, tl)}")
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
