#!/usr/bin/env python3
"""Sammler: Tagesstand dieses Macs nach berichte/<Tag>/<Mac>.md (+ <Mac>.patch für heute), danach berichte/ übers NAS
abgleichen. Spec: docs/superpowers/specs/2026-09-17-tagesbericht-design.md

  python3 tools/tagesbericht/sammler.py                 heute und gestern neu schreiben, dann berichte/ abgleichen
  … --tag 2026-09-16 | --tag gestern | --tag heute      nur diesen Tag
  … --still                                             keine Ausgabe auf stdout
  … --ohne-abgleich                                     studio_abgleich.sh --berichte nicht aufrufen
  … --hook                                              SessionStart-Hook: still, Abgleich mit 8 s Zeitlimit, einzige
                                                        Ausgabe ist der Hinweis auf einen fehlenden Tagesbericht
Endet immer mit 0; Fehler stehen auf stderr."""
from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from bericht import Tagesstand, rendern
from chargen_stand import chargen_stand
from gedaechtnis_stand import gedaechtnis_stand
from git_stand import git_stand, sicherung
from sitzungen_stand import sitzungen_stand
from umgebung import Umgebung, tag_parsen, umgebung_laden

ABGLEICH_ZEITLIMIT = 120.0
ABGLEICH_ZEITLIMIT_HOOK = 8.0
HINWEIS_TAGE = 7
STAND_MUSTER = re.compile(r"Sitzungen (\d+) · Commits (\d+)")


def tagesstand(umg: Umgebung, tag: date, jetzt: datetime) -> Tagesstand:
    notizen, fehler = gedaechtnis_stand(umg.gedaechtnis, tag)
    return Tagesstand(mac=umg.mac, tag=tag, stand=jetzt, repo=str(umg.repo),
                      git=git_stand(umg.repo, tag), chargen=chargen_stand(umg.repo, tag),
                      sitzungen=sitzungen_stand(umg.sitzungsordner(), tag, umg.repo), notizen=notizen, fehler=fehler)


def schreiben(ziel: Path, text: str) -> None:
    """Über eine Temp-Datei im selben Ordner und os.replace — parallele Läufe stören sich nicht."""
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(ziel.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, ziel)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def abgleichen(umg: Umgebung, zeitlimit: float, still: bool) -> None:
    """`sh tools/studio_abgleich.sh --berichte` mit Zeitlimit; bei Überschreitung die ganze Prozessgruppe beenden."""
    ersatz = os.environ.get("NIRO_SAMMLER_ABGLEICH_CMD")
    skript = umg.repo / "tools" / "studio_abgleich.sh"
    if ersatz:
        befehl = [ersatz]
    elif skript.is_file():
        befehl = ["sh", str(skript), "--berichte"]
    else:
        return
    try:
        prozess = subprocess.Popen(befehl, cwd=str(umg.repo), stdout=subprocess.DEVNULL if still else None,
                                   stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        print(f"Sammler: Abgleich nicht gestartet: {e}", file=sys.stderr)
        return
    try:
        prozess.wait(timeout=zeitlimit)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(prozess.pid, signal.SIGTERM)
        except OSError:
            pass
        print(f"Sammler: Abgleich abgebrochen nach {zeitlimit:g} s — lokaler Stand bleibt, nächster Abgleich holt nach",
              file=sys.stderr)


def _aktiv(datei: Path) -> bool:
    """Stand-Zeile eines Tagesstands: Sitzungen oder Commits > 0."""
    try:
        with open(datei, encoding="utf-8", errors="replace") as fh:
            for _ in range(3):
                treffer = STAND_MUSTER.search(fh.readline())
                if treffer:
                    return int(treffer.group(1)) > 0 or int(treffer.group(2)) > 0
    except OSError:
        pass
    return False


def hinweis(umg: Umgebung) -> str:
    """Jüngster Tag vor heute (bis 7 Tage zurück) mit einem aktiven Tagesstand, aber ohne Tagesbericht.md."""
    for zurueck in range(1, HINWEIS_TAGE + 1):
        tag = umg.heute - timedelta(days=zurueck)
        ordner = umg.berichte / tag.isoformat()
        if not ordner.is_dir() or (ordner / "Tagesbericht.md").is_file():
            continue
        if any(_aktiv(p) for p in ordner.glob("*.md") if p.name != "Tagesbericht.md"):
            return f"Tagesbericht für {tag.strftime('%d.%m.%Y')} fehlt — Trigger: „Tagesbericht: {tag.isoformat()}“."
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Tagesstand dieses Macs schreiben und berichte/ abgleichen.")
    parser.add_argument("--tag", help="JJJJ-MM-TT, „gestern“ oder „heute“ (Standard: heute und gestern)")
    parser.add_argument("--still", action="store_true")
    parser.add_argument("--ohne-abgleich", action="store_true")
    parser.add_argument("--hook", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:  # argparse hat Hilfe oder Fehler schon auf stdout/stderr ausgegeben — nie blockieren
        return 0
    still = args.still or args.hook
    try:
        umg = umgebung_laden()
        jetzt = datetime.now()
        tage = [tag_parsen(args.tag, umg.heute)] if args.tag else [umg.heute, umg.heute - timedelta(days=1)]
        for tag in tage:
            stand = tagesstand(umg, tag, jetzt)
            ziel = umg.berichte / tag.isoformat() / f"{umg.mac}.md"
            schreiben(ziel, rendern(stand))
            if tag == umg.heute:
                schreiben(ziel.parent / f"{umg.mac}.patch", sicherung(umg.repo, umg.mac, jetzt))
            if not still:
                print(f"Sammler: {ziel.relative_to(umg.repo).as_posix()} — Sitzungen {len(stand.sitzungen.sitzungen)},"
                      f" Commits {stand.git.commits_gesamt}")
        if not args.ohne_abgleich:
            standard = ABGLEICH_ZEITLIMIT_HOOK if args.hook else ABGLEICH_ZEITLIMIT
            abgleichen(umg, float(os.environ.get("NIRO_SAMMLER_ABGLEICH_TIMEOUT") or standard), still)
        if args.hook:
            zeile = hinweis(umg)
            if zeile:
                print(zeile)
    except Exception as e:  # noqa: BLE001 — der Sammler blockiert nie eine Sitzung
        print(f"Sammler: {type(e).__name__}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
