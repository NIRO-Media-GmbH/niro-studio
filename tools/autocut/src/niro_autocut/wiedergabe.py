"""Wiedergabe-Prüfung vor schreibenden Resolve-Läufen (Regel 6 in tools/resolve/WORKFLOW-Resolve.md): die Fenster
von DaVinci Resolve per ``werkzeuge/fenster.swift`` auflisten. Ein unbenanntes, sichtbares Resolve-Fenster in
Bildschirmgröße ist der Vollbild-Viewer — der User spielt ab. Ohne Bildschirmaufnahme-Recht sind alle Fensternamen
leer; dann ist das Ergebnis „unklar".
"""
from __future__ import annotations

import shutil
import subprocess

from .charge import TOOL_ROOT

FENSTER_SWIFT = TOOL_ROOT / "werkzeuge" / "fenster.swift"


def fenster_ausgabe(timeout_s: int = 90) -> str | None:
    """Ausgabe von fenster.swift (interpretiert, ohne Übersetzen); None, wenn swift fehlt oder scheitert."""
    swift = shutil.which("swift")
    if swift is None or not FENSTER_SWIFT.is_file():
        return None
    try:
        r = subprocess.run([swift, str(FENSTER_SWIFT)], capture_output=True, text=True, timeout=timeout_s)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return r.stdout if r.returncode == 0 else None


def status(ausgabe: str | None, vollbild_min=(1900, 1000)) -> str:
    """„spielt_ab" | „ruhig" | „unklar" aus Zeilen „id⇥Besitzer⇥layer=…⇥onscreen=…⇥BxH⇥Name"."""
    if not ausgabe:
        return "unklar"
    fenster = []
    for zeile in ausgabe.splitlines():
        teile = zeile.split("\t")
        if len(teile) < 6 or "Resolve" not in teile[1]:
            continue
        try:
            breite, hoehe = (int(float(x)) for x in teile[4].split("x", 1))
        except ValueError:
            continue
        fenster.append({"sichtbar": teile[3] == "onscreen=true", "breite": breite, "hoehe": hoehe,
                        "name": "\t".join(teile[5:]).strip()})
    if not fenster or not any(f["name"] for f in fenster):
        return "unklar"
    vollbild = any(not f["name"] and f["sichtbar"] and f["breite"] >= vollbild_min[0] and f["hoehe"] >= vollbild_min[1]
                   for f in fenster)
    return "spielt_ab" if vollbild else "ruhig"
