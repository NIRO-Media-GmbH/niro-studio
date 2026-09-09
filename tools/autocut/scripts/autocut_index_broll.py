"""B-Roll-Clips der Charge per Claude-Vision indexieren (Stufe 2).

Aufruf:
    venv/bin/python scripts/autocut_index_broll.py "<Charge>" [--limit N] [--parallel N] [--dry-run] [--force]
                                                   [--extra PFAD ...]

Findet alle Clips unter <Footage>/Sortiert/B-Roll/** beider Standorte (aus den Interview-Pfaden des
Transkript-Index abgeleitet; --extra ergänzt weitere Wurzeln wie Mavic/Actioncam), meldet Clipzahl,
Cache-Stand und Kostenschätzung. --dry-run listet nur (keine Kosten). Sonst: Proxy → Szenenwechsel → Frames →
Kontaktbögen → Claude, je Clip gecacht in _intern/autocut/broll_index/<fingerprint>.json; --force fragt trotz
Cache neu an (nach Prompt-Änderung). Ctrl-C bricht ab, der nächste Lauf setzt am Cache fort.

Schreibt _intern/autocut/broll_index.json, Ergebnisse/Rohschnitt/broll-index.md und einen Protokoll-Eintrag.
NAS wird nur gelesen. Exit 1 bei Fehlern einzelner Clips (Index wird trotzdem geschrieben), 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.broll_index import (broll_roots, cached_record, discover_broll, estimate_cost,  # noqa: E402
                                      index_broll, render_broll_index_md)
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402


def _de(n: int) -> str:
    """Tausenderpunkt nach deutscher Schreibweise."""
    return f"{int(n):,}".replace(",", ".")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: B-Roll-Index per Claude-Vision (broll_index.json).")
    ap.add_argument("charge", help="Pfad zur Charge (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--limit", type=int, help="nur die ersten N Clips (Testlauf)")
    ap.add_argument("--parallel", type=int, help="parallele Anfragen (Standard: index.parallel aus der Config)")
    ap.add_argument("--dry-run", action="store_true", help="Clips nur auflisten, keine API-Kosten")
    ap.add_argument("--force", action="store_true", help="Cache ignorieren und alle Clips neu anfragen")
    ap.add_argument("--extra", nargs="+", metavar="PFAD", help="weitere B-Roll-Wurzeln (Mavic, Actioncam)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        icfg = ch.config["index"]
        parallel = args.parallel or int(icfg.get("parallel", 4))
        records = ch.load_index()
        print(f"Charge: {ch.root}\nModell: {icfg['model']} (effort {icfg.get('effort', 'medium')}), "
              f"Kacheln {icfg['tile_px']} px, Gitter {icfg['grid'][0]}x{icfg['grid'][1]}\n")
        roots = broll_roots(records, args.extra)
        if not roots:
            raise AutoCutError("Keine B-Roll-Wurzel ableitbar — die Interview-Pfade im Transkript-Index enthalten "
                               "keinen Ordner „Sortiert“. Mit --extra eine Wurzel angeben.")
        for r in roots:
            print(f"Wurzel: {r['root']}  [{r['standort'] or 'ohne Standort'}]  "
                  f"{'gefunden' if r['vorhanden'] else 'FEHLT — NAS gemountet?'}")
        clips = discover_broll(records, args.extra)
        if not clips:
            raise AutoCutError("Keine Videodateien unter den B-Roll-Wurzeln gefunden.")
        for standort, n in sorted(Counter(c["standort"] or "ohne Standort" for c in clips).items()):
            print(f"  {standort}: {n} Clips in {len({c['ordner'] for c in clips if (c['standort'] or 'ohne Standort') == standort})} Ordnern")
        cached = {c["path"] for c in clips if cached_record(ch, c["path"]) is not None}
        todo = clips[:args.limit] if args.limit else clips
        offen = [c for c in todo if args.force or c["path"] not in cached]
        print(f"\nGesamt {len(clips)} Clips, davon {len(cached)} im Cache. "
              f"Dieser Lauf: {len(todo)} Clips, {len(offen)} per API.\nKosten: {estimate_cost(len(offen))}\n")
        if args.dry_run:
            for c in clips:
                mark = "Cache" if c["path"] in cached else "neu  "
                print(f"  {mark}  {c['standort'] or '-':<11} {c['ordner']:<32} {Path(c['path']).name}")
            print("\nProbelauf — nichts angefragt, nichts geschrieben.")
            return 0
        out = index_broll(ch, clips, ch.config, limit=args.limit, parallel=parallel, force=args.force)
        md_path = ch.ergebnisse / "broll-index.md"
        ch.assert_writable(md_path)
        md_path.write_text(render_broll_index_md(out), encoding="utf-8")
        u = out["usage_summe"]
        print(f"\nGeschrieben: {ch.autocut / 'broll_index.json'} ({out['anzahl']} Clips in diesem Lauf, {out['clips_gesamt']} im Index, "
              f"{out['cache_treffer']} aus dem Cache, {len(out['fehler'])} Fehler)\n             {md_path}")
        print(f"Token: Eingabe {_de(u['input'])}, Ausgabe {_de(u['output'])}, Cache gelesen {_de(u['cache_read'])}, "
              f"Cache geschrieben {_de(u['cache_write'])}")
        if args.limit:
            print(f"Hinweis: Testlauf --limit {args.limit} — broll_index.json enthält weiterhin alle {out['clips_gesamt']} bekannten "
                  f"Clips, {out['anzahl']} davon aus diesem Lauf; für neue Clips ohne --limit starten.")
        zeilen = [f"B-Roll-Index: {out['anzahl']} Clips ({out['cache_treffer']} Cache-Treffer, {len(out['fehler'])} Fehler)"
                  + (f", Testlauf --limit {args.limit}, Index gesamt {out['clips_gesamt']} Clips" if args.limit else ""),
                  f"Modell {out['modell']} (effort {out['effort']}), Token Eingabe {u['input']} / Ausgabe {u['output']} / "
                  f"Cache gelesen {u['cache_read']}",
                  f"Dateien: {ch.autocut / 'broll_index.json'}, {md_path}"]
        zeilen += [f"Fehler: {f}" for f in out["fehler"][:10]]
        append_protokoll(ch, "B-Roll-Index", zeilen)
        if out["fehler"]:
            print("\nFEHLER bei " + str(len(out["fehler"])) + " Clips:\n  " + "\n  ".join(out["fehler"]), file=sys.stderr)
            return 1
    except KeyboardInterrupt:
        print("\nAbgebrochen — fertige Clips liegen im Cache, ein neuer Lauf setzt dort fort.", file=sys.stderr)
        return 130
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
