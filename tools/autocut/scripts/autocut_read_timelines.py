"""Alle Timelines des offenen Resolve-Projekts lesen (Items je Spur, Marker, Settings) → eine JSON-Datei.

Grundlage für Stufe 4 (Schnitt-Profil) und die Korrektur-Schleife. Resolve wird NUR gelesen.

Aufruf:
    venv/bin/python scripts/autocut_read_timelines.py "<Ausgabe.json>" [--project-current] [--only NAME ...] [--limit N]

--project-current  liest das gerade geöffnete Projekt (Standard; andere Quellen kommen mit Stufe 4)
--only             nur Timelines mit diesen Namen
--limit            höchstens N Timelines (Testläufe)

Die Ausgabe darf nur unter tools/autocut/profile/ oder in einer Charge liegen
(<Charge>/_intern/autocut/… oder <Charge>/Ergebnisse/Rohschnitt/…). Exit 0 ok, 1 Fehler.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import TOOL_ROOT, AutoCutError  # noqa: E402

PROFILE_DIR = TOOL_ROOT / "profile"
CHARGE_SUBDIRS = (("_intern", "autocut"), ("Ergebnisse", "Rohschnitt"))


def output_allowed(path: str | Path) -> Path:
    """Erlaubte Ausgabeorte: tools/autocut/profile/** oder <Charge>/_intern/autocut/** bzw. Ergebnisse/Rohschnitt/**."""
    p = Path(path).expanduser().resolve()
    if p.suffix.lower() != ".json":
        raise AutoCutError(f"Ausgabe muss eine .json-Datei sein: {p}")
    if str(p).startswith(str(PROFILE_DIR.resolve()) + "/"):
        return p
    parts = p.parts
    for a, b in CHARGE_SUBDIRS:
        for i in range(len(parts) - 2):
            if parts[i] == a and parts[i + 1] == b:
                charge_root = Path(*parts[:i])
                if (charge_root / "Ergebnisse" / "O-Ton-Pläne").is_dir():
                    return p
    raise AutoCutError(f"Schreiben verweigert: {p}\nErlaubt sind nur {PROFILE_DIR}/… oder in einer Charge "
                       f"unter _intern/autocut/… bzw. Ergebnisse/Rohschnitt/….")


def read_all(session: RA.ResolveSession, only: list[str] | None = None, limit: int | None = None,
             log=lambda s: None) -> dict:
    timelines = session.list_timelines()
    if only:
        wanted = set(only)
        timelines = [t for t in timelines if t.GetName() in wanted]
        fehlend = sorted(wanted - {t.GetName() for t in timelines})
        if fehlend:
            raise AutoCutError("Timeline(s) nicht im Projekt: " + ", ".join(fehlend))
    if limit:
        timelines = timelines[:limit]
    out = {"project": session.project_name, "project_id": session.project_id, "resolve_version": session.version,
           "gelesen_am": _dt.datetime.now().isoformat(timespec="seconds"),
           "fps_projekt": session.project.GetSetting("timelineFrameRate"), "timelines": []}
    for i, t in enumerate(timelines, 1):
        log(f"[{i}/{len(timelines)}] {t.GetName()}")
        out["timelines"].append(session.read_timeline(t))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: alle Timelines des offenen Resolve-Projekts als JSON lesen.")
    ap.add_argument("ausgabe", help="Ziel-JSON (unter tools/autocut/profile/ oder in einer Charge)")
    ap.add_argument("--project-current", action="store_true", default=True,
                    help="das geöffnete Projekt lesen (Standard)")
    ap.add_argument("--only", nargs="+", metavar="NAME", help="nur diese Timelines")
    ap.add_argument("--limit", type=int, help="höchstens N Timelines")
    args = ap.parse_args(argv)
    try:
        out_path = output_allowed(args.ausgabe)
        session = RA.ResolveSession(RA.connect())
        print(f"Resolve {session.version}, Projekt '{session.project_name}' — lese Timelines …", file=sys.stderr)
        data = read_all(session, args.only, args.limit, log=lambda s: print("  " + s, file=sys.stderr))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        n_items = sum(t["n_items"] for t in data["timelines"])
        print(f"{len(data['timelines'])} Timelines, {n_items} Items → {out_path}")
        for t in data["timelines"]:
            v = sum(1 for k in t["tracks"] if k.startswith("V"))
            a = sum(1 for k in t["tracks"] if k.startswith("A"))
            print(f"  {t['name'][:50]:<50} V{v} A{a} {t['n_items']:>5} Items {len(t['markers']):>4} Marker")
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
