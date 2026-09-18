"""Gemeinsame Pfade und Konstanten der SFX-Library."""
from pathlib import Path

NAS_ROOT = Path("/Volumes/NIRO NAS/NIRO Productions")
LIBRARY = NAS_ROOT / "01_Projekte/03_Vorlagen und Tools/08_SFX Library"
MUSIK_PLAN = Path(__file__).resolve().parent.parent / "musik/data/plan.json"  # Songs der Musik-Library ausschließen
DATA = Path(__file__).resolve().parent / "data"  # lokale Arbeitsdateien (gitignored)
EIGENE_LIBRARIES = ("07_Musik Library", "08_SFX Library")

AUDIO_EXT = {".mp3", ".wav", ".aif", ".aiff", ".m4a", ".flac", ".ogg", ".aac", ".wma"}

# Ordner der Library (User-Entscheid 16.09.2026: fein nach Sound-Typ)
KATEGORIEN = [
    "Whoosh & Transitions", "Impacts & Hits", "Riser & Build-ups", "Drones & Flächen", "Glitch & Digital",
    "UI, Clicks & Pops", "Film Burn, Vinyl & Analog", "Intros, Logos & Jingles", "Foley & Alltag",
    "Menschen & Crowd", "Natur, Wasser & Wetter", "Fahrzeuge & Maschinen", "Feuer, Explosionen & Waffen",
    "Ambience & Orte", "Horror & Spannung", "Cartoon & Game",
]
UNKLAR = "Unklare Quelle"

FORMAT_RANG = {".wav": 5, ".aif": 4, ".aiff": 4, ".flac": 4, ".m4a": 2, ".aac": 2, ".mp3": 1, ".ogg": 1, ".wma": 0}
