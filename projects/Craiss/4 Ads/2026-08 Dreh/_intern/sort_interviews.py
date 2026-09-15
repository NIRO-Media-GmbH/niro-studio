"""Interview-Clips auf dem NAS in Personen-Ordner „Name - Beruf" sortieren.

Aufruf:
  sort_interviews.py            -> nur Plan anzeigen (verschiebt nichts)
  sort_interviews.py --execute  -> verschieben + Undo-Log schreiben

Zuordnung aus den Transkripten (Selbstvorstellungen), Dual-Cam-Paare über
die XML-CreationDate verifiziert. Die FX3-Uhr läuft rund 8 Minuten vor der
a7MK4-Uhr — die Paare wurden über den Inhalt bestätigt, nicht über die Uhr.

SMB-Falle (NAS): os.rename kann mit EIO/EBUSY an frisch gelesenen Dateien
scheitern (stale Lock). Deshalb Retry-Runden, dann hash-verifizierte Kopie.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

FOOTAGE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Craiss Generation Logistik GmbH & Co. KG/02_Projekte/01_Projekt-4 Ads/"
    "03_Medien/01_Footage/Sortiert/Interviews"
)
LOG = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh/"
           "_intern/_verschiebe_log.jsonl")

# Ziel-Ordner -> Clip-Stems (MP4 + zugehöriges M01.XML wandern zusammen)
PLAN: dict[str, list[str]] = {
    "Opa Didi - Rentner-Fahrer": [
        "FX3_0781", "a7MK4_20260810_0067",
    ],
    "Victor Fodor - LKW-Fahrer Fernverkehr": [
        "FX3_0782", "a7MK4_20260810_0068",
    ],
    "Adrian Mules - LKW-Fahrer Nahverkehr": [
        "FX3_0783", "a7MK4_20260810_0069",
    ],
    "Jakub Platek - LKW-Fahrer Fernverkehr": [
        "FX3_0784", "FX3_0785", "a7MK4_20260810_0070",
    ],
    "Jan Machuta - LKW-Fahrer Fernverkehr": [
        "FX3_0786", "a7MK4_20260810_0071",
    ],
    "Thomas Baranski - Disponent": [
        "FX3_0856", "a7MK4_20260810_0088",
    ],
    "Michael Craiss - Geschäftsführender Gesellschafter": [
        "FX3_0898", "FX3_0899", "FX3_0900",
        "a7MK4_20260810_0113", "a7MK4_20260810_0114", "a7MK4_20260810_0725",
    ],
    "Eva - Recruiterin": [
        "FX3_0901", "FX3_0902",
        "a7MK4_20260810_0115", "a7MK4_20260810_0726", "a7MK4_20260810_0727",
    ],
}


def sha256_head(p: Path, n: int = 64 << 20) -> str:
    """Hash über die ersten n Bytes — reicht zur Kopie-Verifikation, ohne
    20-GB-Dateien zweimal komplett über SMB zu ziehen."""
    h = hashlib.sha256()
    with p.open("rb") as f:
        while n > 0:
            chunk = f.read(min(1 << 20, n))
            if not chunk:
                break
            h.update(chunk)
            n -= len(chunk)
    return h.hexdigest()


def find_files(stem: str) -> list[Path]:
    """MP4 + XML-Sidecar zu einem Stem, egal in welchem Unterordner."""
    hits = []
    for p in FOOTAGE.rglob("*"):
        if not p.is_file():
            continue
        if p.stem == stem or p.stem == f"{stem}M01":
            hits.append(p)
    return sorted(hits)


def move_one(src: Path, dst: Path, entries: list) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "existiert-schon"
    for versuch in range(4):
        try:
            os.rename(src, dst)
            entries.append({"von": str(src), "nach": str(dst), "art": "rename"})
            return "verschoben"
        except OSError as e:
            if versuch == 3:
                break
            time.sleep(2 + 3 * versuch)
    # Fallback: hash-verifizierte Kopie, Original bleibt liegen (Lock)
    before = sha256_head(src)
    shutil.copy2(src, dst)
    if sha256_head(dst) != before:
        dst.unlink(missing_ok=True)
        raise RuntimeError(f"Kopie stimmt nicht überein: {src}")
    entries.append({"von": str(src), "nach": str(dst), "art": "kopie",
                    "hinweis": "Original gelockt — nach Lock-Ende löschen"})
    return "kopiert (Original gelockt)"


def main() -> None:
    execute = "--execute" in sys.argv
    entries: list = []
    gesamt = fehlend = 0

    for ordner, stems in PLAN.items():
        print(f"\n{ordner}/")
        for stem in stems:
            files = find_files(stem)
            if not files:
                print(f"   ! FEHLT: {stem}")
                fehlend += 1
                continue
            for src in files:
                dst = FOOTAGE / ordner / src.name
                gesamt += 1
                if src == dst:
                    print(f"   = {src.name} (schon am Ziel)")
                    continue
                vor = src.parent.relative_to(FOOTAGE)
                vor = str(vor) if str(vor) != "." else "Interviews"
                if not execute:
                    print(f"   → {src.name:<30} (aus {vor}/)")
                else:
                    status = move_one(src, dst, entries)
                    print(f"   → {src.name:<30} {status}")

    if execute:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        # leere Alt-Ordner (GF/, HR/) aufräumen
        for d in sorted(FOOTAGE.iterdir(), reverse=True):
            if d.is_dir() and d.name not in PLAN:
                rest = [x for x in d.iterdir() if x.name != ".DS_Store"]
                if not rest:
                    for x in d.iterdir():
                        x.unlink()
                    d.rmdir()
                    print(f"\nLeeren Alt-Ordner entfernt: {d.name}/")
                else:
                    print(f"\nAlt-Ordner {d.name}/ NICHT leer: "
                          f"{[x.name for x in rest]}")
        print(f"\nUndo-Log: {LOG}")

    print(f"\n{gesamt} Dateien in {len(PLAN)} Personen-Ordnern, {fehlend} fehlend.")
    if not execute:
        print("PLAN-Modus — nichts verschoben. Mit --execute ausführen.")


if __name__ == "__main__":
    main()
