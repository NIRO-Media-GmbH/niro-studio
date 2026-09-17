import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from gedaechtnis_stand import Notiz, gedaechtnis_stand
from testhilfe import gedaechtnis_anlegen

HEUTE = date(2026, 9, 17)


class GedaechtnisNotizen(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="gedaechtnis_test_"))
        self.ordner = self.basis / "memory"
        gedaechtnis_anlegen(self.ordner, HEUTE)

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_heute_geaenderte_notizen(self):
        notizen, fehler = gedaechtnis_stand(self.ordner, HEUTE)
        self.assertEqual(notizen, [Notiz(name="notiz-a", beschreibung='Eine "Notiz" von heute')])
        self.assertEqual(fehler, [])

    def test_gestern(self):
        notizen, _ = gedaechtnis_stand(self.ordner, HEUTE - timedelta(days=1))
        self.assertEqual(notizen, [Notiz(name="notiz-b", beschreibung="gestern")])

    def test_ordner_fehlt(self):
        notizen, fehler = gedaechtnis_stand(self.basis / "fehlt", HEUTE)
        self.assertEqual(notizen, [])
        self.assertEqual(len(fehler), 1)


if __name__ == "__main__":
    unittest.main()
