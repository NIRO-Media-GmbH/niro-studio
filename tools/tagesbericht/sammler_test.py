"""Ende-zu-Ende-Tests des Sammlers und Runner für alle *_test.py in diesem Ordner.
Aufruf: python3 tools/tagesbericht/sammler_test.py   (Exit 0 = alle Tests bestanden)"""
import sys
import unittest
from pathlib import Path

HIER = Path(__file__).resolve().parent


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(HIER), pattern="*_test.py", top_level_dir=str(HIER))
    ergebnis = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if ergebnis.wasSuccessful() else 1)
