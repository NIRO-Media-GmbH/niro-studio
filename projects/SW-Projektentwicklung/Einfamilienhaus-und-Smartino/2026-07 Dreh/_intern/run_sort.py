import json, sys
from pathlib import Path
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/src")
from niro_transcribe.footage.discover import discover_clips
from niro_transcribe.footage.move_plan import Move, MovePlan
from niro_transcribe.footage.mover import execute_plan

FOOTAGE = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
               "SW Projektentwicklung & Dienstleistung GmbH/02_Projekte/"
               "04_Projekt-21.07.26-Einfamilienhaus und Smartino/03_Medien/01_Footage")
SORT = FOOTAGE / "sortiert"
INTERN = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
              "Einfamilienhaus-und-Smartino/2026-07 Dreh/_intern")

# Themen-Zuordnung der Sprech-Clips (Stem -> Zielordner)
THEMEN = {
    "a7MK4_20260721_0091": "01_Projekt-Gottwolfshausen",
    "a7MK4_20260721_0092": "01_Projekt-Gottwolfshausen",
    "FX3_0253": "02_Bifaziale-Solarmodule",
    "FX3_0254": "02_Bifaziale-Solarmodule",
    "a7MK4_20260721_0093": "02_Bifaziale-Solarmodule",
    "a7MK4_20260721_0094": "02_Bifaziale-Solarmodule",
    "a7MK4_20260721_0110": "03_BauSolar-Modul",
    "FX3_0260": "04_Flachdach-Erklaerung",
    "a7MK4_20260721_0098": "04_Flachdach-Erklaerung",
    "a7MK4_20260721_0124": "05_Hotel-Smartino",
    "a7MK4_20260721_0125": "05_Hotel-Smartino",
    "a7MK4_20260721_0132": "05_Hotel-Smartino",
    "a7MK4_20260721_0133": "05_Hotel-Smartino",
    "a7MK4_20260721_0104": "06_E-Auto-Wallbox-Ads",
    "a7MK4_20260721_0105": "06_E-Auto-Wallbox-Ads",
    "a7MK4_20260721_0106": "06_E-Auto-Wallbox-Ads",
    "a7MK4_20260721_0108": "06_E-Auto-Wallbox-Ads",
    "a7MK4_20260721_0109": "06_E-Auto-Wallbox-Ads",
    "a7MK4_20260721_0127": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0128": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0129": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0130": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0131": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0135": "07_Recruiting-Elektromeister",
    "a7MK4_20260721_0136": "07_Recruiting-Elektromeister",
    # Regie-/Planungsgespräche (Kontext, kein Material)
    "FX3_0265": "90_Regie-Besprechungen",
    "a7MK4_20260721_0097": "90_Regie-Besprechungen",
    "a7MK4_20260721_0107": "90_Regie-Besprechungen",
    "a7MK4_20260721_0126": "90_Regie-Besprechungen",
}

clips = discover_clips(FOOTAGE)
moves, classifications = [], []
for c in clips:
    ziel = THEMEN.get(c.path.stem)
    if ziel is None:
        ziel = f"99_B-Roll/{c.camera}"
    moves.append(Move(src=str(c.path), dst=str(SORT / ziel / c.path.name)))
    classifications.append({"clip": c.path.name, "camera": c.camera, "ziel": ziel})

plan = MovePlan(moves=moves)
problems = plan.validate([str(c.path) for c in clips])
if problems:
    print("VALIDIERUNG FEHLGESCHLAGEN:")
    for p in problems: print(" -", p)
    sys.exit(1)

plan.save(INTERN / "move_manifest.json")
(INTERN / "classifications.json").write_text(
    json.dumps(classifications, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Plan valide: {len(moves)} Moves. Führe aus...")

results = execute_plan(plan, INTERN / "_verschiebe_log.jsonl",
                       discovered_srcs=[str(c.path) for c in clips])
sc = sum(1 for r in results if r.sidecar_src)
print(f"FERTIG: {len(results)} Dateien verschoben ({sc} mit XML-Sidecar), Methode: "
      f"{set(r.method for r in results)}")
