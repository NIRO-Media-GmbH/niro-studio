import sys
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/transcribe/src")
from niro_transcribe.footage.pipeline import transcribe_all

FOOTAGE = ("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
           "SW Projektentwicklung & Dienstleistung GmbH/02_Projekte/"
           "04_Projekt-21.07.26-Einfamilienhaus und Smartino/03_Medien/01_Footage")
PROJECT = ("/Users/jansantos/NIRO Studio/projects/SW-Projektentwicklung/"
           "Einfamilienhaus-und-Smartino/2026-07 Dreh")

index = transcribe_all(FOOTAGE, PROJECT)
ok = sum(1 for r in index if r.get("ok"))
print(f"FERTIG: {ok}/{len(index)} Clips transkribiert")
