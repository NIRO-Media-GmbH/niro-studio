"""Gemeinsame Pfade und Konstanten der Musik-Library."""
from pathlib import Path

NAS_ROOT = Path("/Volumes/NIRO NAS/NIRO Productions")
LIBRARY = NAS_ROOT / "01_Projekte/03_Vorlagen und Tools/07_Musik Library"
DATA = Path(__file__).resolve().parent / "data"  # lokale Arbeitsdateien (gitignored)

AUDIO_EXT = {".mp3", ".wav", ".aif", ".aiff", ".m4a", ".flac", ".ogg", ".aac", ".wma"}

# Ordner der Library (Einsatzzweck, User-Entscheid 16.09.2026)
KATEGORIEN = [
    "Recruiting & Ads",
    "Imagefilm & Corporate",
    "Social Reels & Trends",
    "Event & Aftermovie",
    "Emotional & Testimonial",
]
UNKLAR = "Unklare Quelle"

# Bessere Fassung zuerst (gleicher Song in mehreren Formaten)
FORMAT_RANG = {".wav": 5, ".aif": 4, ".aiff": 4, ".flac": 4, ".m4a": 2, ".aac": 2, ".mp3": 1, ".ogg": 1, ".wma": 0}
