import json, sys, time
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/src")
from niro_transcribe.footage.discover import discover_clips
from niro_transcribe.footage.move_plan import Move
from niro_transcribe.footage.mover import execute_move

FOOTAGE = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
               "SW Projektentwicklung & Dienstleistung GmbH/02_Projekte/"
               "04_Projekt-21.07.26-Einfamilienhaus und Smartino/03_Medien/01_Footage")
SORT = FOOTAGE / "sortiert"
INTERN = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
              "Einfamilienhaus-und-Smartino/2026-07 Dreh/_intern")
LOG = INTERN / "_verschiebe_log.jsonl"

manifest = json.loads((INTERN / "move_manifest.json").read_text(encoding="utf-8"))
ziel_map = {m["src"]: m["dst"] for m in manifest["moves"]}

# Nur Clips außerhalb von sortiert/ (2 Avata sind schon drüben)
clips = [c for c in discover_clips(FOOTAGE) if SORT not in c.path.parents]
pending = [Move(src=str(c.path), dst=ziel_map[str(c.path)]) for c in clips]
print(f"{len(pending)} Moves offen")

done = []
with open(LOG, "a", encoding="utf-8") as fh:
    for runde in range(1, 7):
        failed = []
        for mv in pending:
            try:
                res = execute_move(mv)
                fh.write(json.dumps(asdict(res), ensure_ascii=False) + "\n")
                fh.flush()
                done.append(res)
            except OSError as e:
                failed.append((mv, str(e)))
        if not failed:
            break
        pending = [m for m, _ in failed]
        print(f"Runde {runde}: {len(done)} ok, {len(failed)} gelockt -> warte 60 s")
        time.sleep(60)

print(f"FERTIG: {len(done)} verschoben, {len(pending) if failed else 0} verbleibend")
for m, err in (failed if failed else []):
    print("  NOCH GELOCKT:", Path(m.src).name, "-", err[:80])
