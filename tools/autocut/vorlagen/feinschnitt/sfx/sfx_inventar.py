"""Vorlage (Stand 15.09.2026): SFX-Inventar aus den Bins des Users im offenen Resolve-Projekt lesen → inventar.json (nur lesen).

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_inventar.py --suchen   → Bins mit „sfx“, „sound“ oder „audio“ im Pfad auflisten
                                                                               (je bis 60 Clips: Name, Dauer, Dateipfad)
        tools/autocut/venv/bin/python _intern/sfx/sfx_inventar.py            → SFX_BIN rekursiv lesen, inventar.json schreiben
Inventar nur im Projekt feinschnitt_bauen.PROJEKT (sonst Abbruch); im Media Pool wird nichts verändert, SFX-Dateien bleiben unberührt.
Schreibt _intern/sfx/inventar.json — Liste je Clip (Beispiel: inventar.beispiel.json):
  bin       Bin-Pfad ab SFX_BIN mit Wurzel „SFX“, z. B. „SFX/Whoosh/Fast“ (→ BINS in sfx_analyse.py)
  name      Clipname im Media Pool (= Dateiname; Schlüssel für sfx_spektren.py und PLATZIERUNGEN in sfx_plan_bauen.py)
  dauer     Clip-Eigenschaft „Duration“ (Timecode-Text)
  pfad      Clip-Eigenschaft „File Path“, NFC-normalisiert (macOS liefert Umlaute teils als NFD)
  online    pfad existiert auf diesem Rechner (False = Bin des Users offline, z. B. nach Umbenennung eines NAS-Ordners)
  pfad_nas  lesbarer Pfad für Messung, Plan und Einsatz: pfad nach PFAD_ERSETZUNG (ohne passende Ersetzung = pfad)
15.09.: Die SFX-Bins des Users waren offline (NAS-Ordner umbenannt), pfad_nas wurde per Präfix-Ersetzung ergänzt; später hat der User
die Bins neu verknüpft, sodass sfx_einsetzen.py die Items per pfad_nas im Media Pool wiederfand. Danach: sfx_analyse.py.
Herkunft: Taxodia-Charge, Session-Scratchpad sfx_inventar.py + sfx_bins.py (pfad_nas in der Session nachträglich ergänzt)
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import unicodedata
from collections import Counter
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
SFX_BIN: list[str] = []  # Bin-Pfad des SFX-Ordners im Media Pool ab Master, z. B. ["<Audio-Bin>", "SFX"] (mit --suchen finden)
# Präfix-Ersetzungen Resolve-Pfad → lesbarer Pfad (nur nötig, wenn online = False, weil Ordner umbenannt/verschoben wurden):
PFAD_ERSETZUNG: list[tuple[str, str]] = [
    # ("<Mount>/<alter Ordnername>/", "<Mount>/<neuer Ordnername>/"),  # erster passender Präfix gewinnt
]
# ── Ende ANPASSEN ──────────────────────────────────

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def finde(f, teile):
    for t in teile:
        f = next((s for s in (f.GetSubFolderList() or []) if s.GetName() == t), None)
        if f is None:
            return None
    return f


def suchen(f, pfad: str) -> None:
    """Bins mit „sfx“, „sound“ oder „audio“ im Pfad samt ersten 60 Clips ausgeben (Suche nach dem SFX-Bin des Users)."""
    name = f.GetName()
    clips = f.GetClipList() or []
    if "sfx" in (pfad + "/" + name).lower() or "sound" in (pfad + "/" + name).lower() or "audio" in (pfad + "/" + name).lower():
        print(f"{pfad}/{name}: {len(clips)} Clips")
        for c in clips[:60]:
            print("   ", c.GetName(), "|", c.GetClipProperty("Duration"), "|", unicodedata.normalize("NFC", c.GetClipProperty("File Path") or ""))
    for s in f.GetSubFolderList() or []:
        suchen(s, pfad + "/" + name)


def nas_pfad(pfad: str) -> str:
    for alt, neu in PFAD_ERSETZUNG:
        if pfad.startswith(alt):
            return neu + pfad[len(alt):]
    return pfad


def main() -> None:
    r = RA.connect()
    p = r.GetProjectManager().GetCurrentProject()
    if p is None:
        raise SystemExit("In Resolve ist kein Projekt geöffnet.")
    print("Projekt:", p.GetName())
    mp = p.GetMediaPool()
    if "--suchen" in sys.argv:
        suchen(mp.GetRootFolder(), "")
        return
    if p.GetName() != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{p.GetName()}' ≠ Freigabe '{fb.PROJEKT}' — kein Inventar geschrieben.")
    if not SFX_BIN:
        raise SystemExit("ANPASSEN-Block ausfüllen: SFX_BIN ist leer (Bin-Pfad mit --suchen finden) — kein Inventar geschrieben.")
    sfx = finde(mp.GetRootFolder(), SFX_BIN)
    if sfx is None:
        raise SystemExit(f"Bin {'/'.join(SFX_BIN)} nicht gefunden — kein Inventar geschrieben.")
    out = []

    def walk(f, pfad):
        for c in f.GetClipList() or []:
            fp = unicodedata.normalize("NFC", c.GetClipProperty("File Path") or "")
            out.append({"bin": pfad, "name": c.GetName(), "dauer": c.GetClipProperty("Duration"), "pfad": fp, "online": os.path.exists(fp),
                        "pfad_nas": nas_pfad(fp)})
        for s in f.GetSubFolderList() or []:
            walk(s, pfad + "/" + s.GetName())

    walk(sfx, "SFX")
    (HIER / "inventar.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(Counter(o["bin"] for o in out))
    print("online:", sum(o["online"] for o in out), "von", len(out), "| pfad_nas lesbar:", sum(os.path.exists(o["pfad_nas"]) for o in out))


if __name__ == "__main__":
    main()
