import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from chargen_stand import Lieferung, chargen_stand
from testhilfe import chargen_anlegen

HEUTE = date(2026, 9, 17)
C1 = "projects/Kunde/Projekt/2026-09 Charge"
C2 = "projects/Kunde/2026-08 Kurz"


class ChargenStandAusProtokollen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="chargen_test_"))
        cls.repo = cls.basis / "repo"
        cls.repo.mkdir()
        chargen_anlegen(cls.repo, HEUTE)
        cls.stand = chargen_stand(cls.repo, HEUTE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def test_eintraege_aller_formen_nur_heute(self):
        self.assertEqual(self.stand.je_charge[C1], ["2026-09-17 11:07 — AutoCut: Kantenprüfung", "Session 17.09.2026 — Feinschnitt"])
        self.assertEqual(self.stand.je_charge[C2], ["Overlay-Export Video 1 (2026-09-17)"])

    def test_sammelzeile(self):
        self.assertEqual(self.stand.sammel, [("2026-09-17 — Medien aufs NAS verschoben", 6)])
        self.assertNotIn("projects/K0/P/2026-01 C", self.stand.je_charge)
        self.assertIn("projects/K0/P/2026-01 C", self.stand.je_charge_alle)
        self.assertEqual(len(self.stand.je_charge_alle), 7)

    def test_lieferungen(self):
        self.assertEqual(self.stand.lieferungen, [Lieferung(charge=C1, anzahl=1, beispiele=["Export/a.mp4"])])

    def test_gestern(self):
        gestern = chargen_stand(self.repo, HEUTE - timedelta(days=1))
        self.assertEqual(gestern.je_charge_alle, {C1: ["2026-09-16 — Gestern"]})
        self.assertEqual(gestern.sammel, [])
        self.assertEqual(gestern.lieferungen, [Lieferung(charge=C1, anzahl=1, beispiele=["Export/b.mp4"])])

    def test_ohne_projects(self):
        leer = chargen_stand(self.basis / "nix", HEUTE)
        self.assertEqual((leer.je_charge_alle, leer.lieferungen, leer.fehler), ({}, [], []))


class ChargenStandBeiGesperrtemOrdner(unittest.TestCase):
    """Bis Python 3.12 werfen is_file/is_dir bei EACCES PermissionError, ab 3.13 geben sie False zurück —
    der Test erzwingt den Fehler unabhängig von der Version."""

    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="chargen_test_"))
        self.repo = self.basis / "repo"
        self.repo.mkdir()
        chargen_anlegen(self.repo, HEUTE)
        gesperrt = self.repo / "projects" / "Gesperrt" / "P" / "2026-01 C"
        gesperrt.mkdir(parents=True)
        (gesperrt / "Protokoll.md").write_text("## 2026-09-17 - x\n")

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_permission_error_wird_gemeldet_nicht_geworfen(self):
        echt = Path.is_file

        def gesperrt(pfad):
            if "Gesperrt" in str(pfad):
                raise PermissionError(13, "Permission denied", str(pfad))
            return echt(pfad)

        with mock.patch.object(Path, "is_file", gesperrt):
            stand = chargen_stand(self.repo, HEUTE)
        self.assertTrue(any("Gesperrt" in f for f in stand.fehler), stand.fehler)
        self.assertIn(C1, stand.je_charge)
        self.assertNotIn("projects/Gesperrt/P/2026-01 C", stand.je_charge_alle)


if __name__ == "__main__":
    unittest.main()
