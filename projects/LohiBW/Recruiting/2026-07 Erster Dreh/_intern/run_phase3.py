"""Phase 3: Manifest ausfuehren — geprueftes Verschieben mit Undo-Log.
execute_plan validiert die Vollstaendigkeit selbst und bewegt sonst nichts."""
from __future__ import annotations

from pathlib import Path

from niro_transcribe.footage.discover import discover_clips
from niro_transcribe.footage.move_plan import MovePlan
from niro_transcribe.footage.mover import execute_plan

FOOTAGE = Path("/Volumes/NIRO-SSD-02/Lohi Backup/01_Footage")
MANIFEST = Path("projects/LohiBW Recruiting/manifest.json")
LOG = Path("/Volumes/NIRO-SSD-02/Lohi Backup/sortiert/_verschiebe_log.jsonl")

plan = MovePlan.load(MANIFEST)
discovered = [str(c.path) for c in discover_clips(FOOTAGE)]
print(f"Manifest: {len(plan.moves)} Moves | discovered: {len(discovered)} Clips")

results = execute_plan(plan, LOG, discovered_srcs=discovered)

renamed = sum(1 for r in results if r.method == "rename")
copied = sum(1 for r in results if r.method == "copy")
with_sc = sum(1 for r in results if r.sidecar_src)
print(f"FERTIG: {len(results)} verschoben ({renamed} rename, {copied} copy), {with_sc} inkl. Sidecar")
print(f"Log: {LOG}")
