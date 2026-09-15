"""Vorlage (Stand 15.09.2026): Vorprüfung vor sfx_einsetzen.py --ausfuehren — SFX-Dateien im Media Pool, Clip-FPS, genutzte Länge.

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_vorpruefung.py
Liest sfx_plan.json und den Media Pool des offenen Projekts (nur lesen; Abbruch, wenn es nicht feinschnitt_bauen.PROJEKT ist).
Je genutzter Datei (pfad_nas):
  - Media-Pool-Item mit diesem Dateipfad vorhanden? („NICHT im Media Pool“ ist kein Fehler: sfx_einsetzen.py importiert die Datei dann
    in den eigenen Bin; bevorzugt aber den Bin des Users neu verknüpfen lassen.)
  - Clip-Eigenschaft FPS = 25 (sfx_einsetzen.py rechnet Quell-In/-Out in 25er-Frames)
  - Dateilänge (ffprobe) ≥ größtes src_in_s + dauer_frames/25 aller Platzierungen dieser Datei
Ausgabe nur im Terminal: je Datei eine Zeile, am Ende „Probleme: [...]“ (leer = ok).
Herkunft: Taxodia-Charge, Session-Scratchpad sfx_vorpruefung.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
# (keine eigenen Werte: Projekt aus feinschnitt_bauen.PROJEKT, Platzierungen aus sfx_plan.json)
# ── Ende ANPASSEN ──────────────────────────────────

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def main() -> None:
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    s = RA.ResolveSession(RA.connect())
    if s.project_name != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{fb.PROJEKT}' — nichts geprüft.")
    index = s._path_index()
    probleme = []
    for pf in sorted({e["pfad_nas"] for e in plan}):
        mpi = index.get(RA._norm(pf))
        roh = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pf],
                             capture_output=True, text=True).stdout.strip()
        if not roh:
            probleme.append(f"nicht lesbar: {pf}")
            print("NICHT LESBAR", pf.split("/")[-1])
            continue
        dauer_s = float(roh)
        fps = mpi.GetClipProperty("FPS") if mpi else None
        nutz = max(e["src_in_s"] + e["dauer_frames"] / 25 for e in plan if e["pfad_nas"] == pf)
        print(("Media Pool ✓" if mpi else "NICHT im Media Pool"), f"FPS {fps}", f"Datei {dauer_s:.2f} s, genutzt bis {nutz:.2f} s", pf.split("/")[-1])
        if nutz > dauer_s + 1e-3:
            probleme.append(pf)
        if mpi and str(fps) not in ("25", "25.0", "25.000"):
            probleme.append(f"FPS {fps}: {pf}")
    print("Probleme:", probleme)


if __name__ == "__main__":
    main()
