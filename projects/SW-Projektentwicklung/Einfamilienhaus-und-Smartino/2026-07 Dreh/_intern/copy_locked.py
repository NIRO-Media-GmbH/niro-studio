import json, shutil, sys
from pathlib import Path
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/src")
from niro_transcribe.cache import file_hash

FOOT = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
            "SW Projektentwicklung & Dienstleistung GmbH/02_Projekte/"
            "04_Projekt-21.07.26-Einfamilienhaus und Smartino/03_Medien/01_Footage")
SRC = FOOT / "Kamera-A FX3" / "FX3_0253.MP4"
DST = FOOT / "sortiert" / "02_Bifaziale-Solarmodule" / "FX3_0253.MP4"
SC_SRC = FOOT / "Kamera-A FX3" / "FX3_0253M01.XML"
SC_DST = DST.parent / "FX3_0253M01.XML"
LOG = Path("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
           "Einfamilienhaus-und-Smartino/2026-07 Dreh/_intern/_verschiebe_log.jsonl")

before = file_hash(SRC)
shutil.copy2(SRC, DST)
if file_hash(DST) != before:
    DST.unlink(missing_ok=True)
    sys.exit("Prüfsumme abweichend — Kopie verworfen, Quelle unangetastet")
print("Kopie verifiziert (Hash identisch).")
size = SRC.stat().st_size
try:
    SRC.unlink()
    unlinked = True
    print("Quelle gelöscht — vollständiger Move.")
except OSError as e:
    unlinked = False
    print(f"Quelle GELOCKT, bleibt als Duplikat liegen: {e}")

# Sidecar normal verschieben (war im Test frei)
import os
os.rename(SC_SRC, SC_DST)
print("Sidecar verschoben.")

if unlinked:
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"src": str(SRC), "dst": str(DST), "method": "copy",
                             "size": size, "sidecar_src": str(SC_SRC),
                             "sidecar_dst": str(SC_DST)}, ensure_ascii=False) + "\n")
