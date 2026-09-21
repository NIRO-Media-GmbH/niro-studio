"""Index-Nachlauf je Abschnitt (Stufe 2b): Einstellung, Perspektive, Brennweite, Bewegungsrichtung, Hauptmotiv, setup_hash.

Aufruf:
    venv/bin/python scripts/autocut_index_sections.py "<Charge>" [--limit N] [--parallel N] [--dry-run] [--force]

Liest broll_index.json + Frame-Cache (work/frames), schreibt den Clip-Cache und broll_index.json neu, Protokoll-Eintrag.
--dry-run: Clipzahl, Cache-Stand, Kostenschätzung — keine API-Kosten. Exit 1 bei Fehlern einzelner Clips, 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.index_sections import estimate_sections_cost, index_sections, needs_sections  # noqa: E402
from niro_autocut.telemetrie import finden, laden as telemetrie_laden  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut Stufe 2b: Index-Nachlauf je Abschnitt.")
    ap.add_argument("charge")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--parallel", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="auch Clips mit vorhandenen Abschnittsfeldern neu anfragen")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        index = ch.read_json("broll_index.json")
        if not index:
            raise AutoCutError(f"{ch.autocut / 'broll_index.json'} fehlt — erst autocut_index_broll.py.")
        scfg = ch.config["index_sections"]
        max_sections = int(scfg.get("max_sections", 5))
        clips = list(index.get("clips") or [])
        todo = clips[:args.limit] if args.limit else clips
        offen = [c for c in todo if args.force or needs_sections(c, max_sections)]
        print(f"Charge: {ch.root}\nModell: {ch.config['index']['model']} (effort {scfg.get('effort', 'medium')}), Kacheln {scfg['tile_px']} px, "
              f"{scfg['per_section']} je Abschnitt\nGesamt {len(clips)} Clips, dieser Lauf {len(todo)}, per API {len(offen)}.\n"
              f"Kosten: {estimate_sections_cost(offen, int(scfg['tile_px']), int(scfg['per_section']), max_sections)}\n")
        tele = telemetrie_laden(ch.autocut)
        # nur Datensätze mit Daten zählen (quelle „keine": keine Datenspur und nicht optisch gemessen)
        mit_tele = sum(1 for c in todo if (finden(tele, str(c["path"])) or {}).get("quelle") not in (None, "keine"))
        hinweis = ("" if mit_tele else " — erst scripts/autocut_telemetrie.py ausführen, dann kommen Perspektive Höhe "
                   "sowie Brennweite in mm und Zoom je Abschnitt aus den Metadaten.")
        print(f"Telemetrie: {mit_tele} von {len(todo)} Clips" + hinweis + "\n")
        if args.dry_run:
            print("Probelauf — nichts angefragt, nichts geschrieben.")
            return 0
        out = index_sections(ch, index, ch.config, limit=args.limit, parallel=args.parallel or int(scfg.get("parallel", 4)),
                             force=args.force)
        u = out["usage_summe"]
        zeilen = [f"Index-Nachlauf: {out['anzahl']} Clips ({out['cache_treffer']} Cache-Treffer, {len(out['fehler'])} Fehler, "
                  f"{out.get('reparaturen', 0)} Nachfragen wegen Schema-Verstoß)"
                  + (f", Testlauf --limit {args.limit}" if args.limit else ""),
                  f"Token Eingabe {u['input']} / Ausgabe {u['output']} / Cache gelesen {u['cache_read']}",
                  f"Telemetrie genutzt: {out['mit_telemetrie']} Clips (perspektive_hoehe aus Metadaten, "
                  f"brennweite_mm/zoom/bewegungsart/haltung je Abschnitt)",
                  f"Datei: {ch.autocut / 'broll_index.json'}"] + [f"Fehler: {f}" for f in out["fehler"][:10]]
        append_protokoll(ch, "Index-Nachlauf", zeilen)
        print("\n".join(zeilen))
        return 1 if out["fehler"] else 0
    except KeyboardInterrupt:
        print("\nAbgebrochen — fertige Clips liegen im Cache.", file=sys.stderr)
        return 130
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
