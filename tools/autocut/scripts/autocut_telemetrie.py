"""Kamera-Telemetrie je Clip (Gyro, Beschleunigung, Brennweite aus der Sony-rtmd-Spur; optischer Rückfall) →
<Charge>/_intern/autocut/telemetrie.json, Cache telemetrie/<fingerprint>.json, Bericht Ergebnisse/Rohschnitt/telemetrie.md.

Aufruf:
    venv/bin/python scripts/autocut_telemetrie.py "<Charge>" [--ordner <Pfad> ...] [--limit N] [--force] [--ohne-optisch]
                                                   [--schaerfe] [--parallel N] [--dry-run] [--kalibrieren]

Clip-Quelle: --ordner, sonst broll_index.json, inventar.json, B-Roll-Wurzeln des Transkript-Index, media.json.
--kalibrieren misst Gyro und optischen Weg auf demselben 4-s-Fenster je Clip und schreibt telemetrie_kalibrierung.json
(Achsen, Vorzeichen, px_faktor je Kamera, Spearman; Werte für defaults.yaml). Exit 1 bei Fehlern, 130 bei Abbruch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.telemetrie import clips_eindeutig, clips_finden, laden, telemetrie_charge  # noqa: E402
from niro_autocut.telemetrie_bericht import bericht_md  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Kamera-Telemetrie je Clip (telemetrie.json + Bericht).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--ordner", nargs="+", help="Videoordner statt der Chargen-Quellen (rekursiv)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--force", action="store_true", help="Cache je Clip verwerfen und neu messen")
    ap.add_argument("--ohne-optisch", action="store_true",
                    help="Clips ohne Datenspur nicht optisch messen (quelle: keine)")
    ap.add_argument("--schaerfe", action="store_true",
                    help="Schärfe je Fenster auch bei rtmd-Clips messen (dekodiert 480×270)")
    ap.add_argument("--parallel", type=int)
    ap.add_argument("--dry-run", action="store_true", help="nur Clip-Liste und Quelle zeigen, nichts messen oder schreiben")
    ap.add_argument("--kalibrieren", action="store_true",
                    help="Gyro ↔ optisch auf demselben Fenster (telemetrie_kalibrierung.json)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open_basis(args.charge)
        cfg = ch.config["telemetrie"]
        clips = clips_finden(ch, args.ordner)
        eindeutig = clips_eindeutig(clips)
        todo = eindeutig[:args.limit] if args.limit else eindeutig
        print(f"Charge: {ch.root}\n{len(eindeutig)} Clips" + (f", dieser Lauf {len(todo)}" if args.limit else "")
              + f" · Ordner: {', '.join(sorted({c['ordner'] or '(Wurzel)' for c in eindeutig})[:8])}\n")
        if args.dry_run:
            print("Probelauf — nichts gemessen, nichts geschrieben.")
            return 0
        if args.kalibrieren:
            from niro_autocut.telemetrie_kalibrierung import kalibrieren, tabelle
            erg = kalibrieren(ch, todo, cfg, parallel=args.parallel)
            print(tabelle(erg))
            append_protokoll(ch, "Telemetrie-Kalibrierung",
                             [f"{erg['anzahl']} Clips, Datei {ch.autocut / 'telemetrie_kalibrierung.json'}"]
                             + [f"{k}: {v['empfehlung']}" for k, v in erg["kameras"].items()])
            return 0
        # volle Liste + limit: telemetrie_charge dedupliziert, schneidet und ergänzt telemetrie.json (Teil-Lauf kürzt nicht)
        out = telemetrie_charge(ch, clips, cfg, limit=args.limit, force=args.force, ohne_optisch=args.ohne_optisch,
                                parallel=args.parallel, schaerfe=args.schaerfe)
        # Bericht aus der ganzen telemetrie.json, nicht nur aus diesem (Teil-)Lauf
        md = bericht_md(laden(ch.autocut), f"{ch.kunde} / {ch.projekt} / {ch.root.name}", ch.read_json("broll_index.json"))
        ziel = ch.ergebnisse / "telemetrie.md"
        ch.assert_writable(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(md, encoding="utf-8")
        zeilen = [f"Telemetrie: {len(out['clips'])} Clips "
                  f"({out['gemessen']} gemessen, {out['cache_treffer']} Cache-Treffer, "
                  f"{len(out['fehler'])} Fehler; telemetrie.json gesamt {out['gesamt']})"
                  + (f", Testlauf --limit {args.limit}" if args.limit else ""),
                  f"Dateien: {ch.autocut / 'telemetrie.json'}, {ziel}"] + [f"Fehler: {f}" for f in out["fehler"][:10]]
        append_protokoll(ch, "Telemetrie", zeilen)
        print("\n" + "\n".join(zeilen))
        return 1 if out["fehler"] else 0
    except KeyboardInterrupt:
        print("\nAbgebrochen — fertige Clips liegen im Cache (telemetrie/).", file=sys.stderr)
        return 130
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    except ImportError as e:
        print(f"FEHLER: {e} — Kalibrierung noch nicht verfügbar.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
