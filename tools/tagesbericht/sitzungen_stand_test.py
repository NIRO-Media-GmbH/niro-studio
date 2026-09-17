import json
import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from sitzungen_stand import charge_aus_pfad, relativ, sitzungen_stand
from testhilfe import sitzungen_anlegen

HEUTE = date(2026, 9, 17)


class SitzungenAusVerlaeufen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="sitzungen_test_"))
        cls.repo = cls.basis / "repo"
        cls.wt = cls.basis / "wt"
        cls.repo.mkdir()
        cls.wt.mkdir()
        ordner = sitzungen_anlegen(cls.basis / "claude" / "projects", cls.repo, cls.wt, HEUTE)
        cls.ordner = [ordner["haupt"], ordner["wt"]]
        cls.stand = sitzungen_stand(cls.ordner, HEUTE, cls.repo)
        cls.s1, cls.s2 = cls.stand.sitzungen

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def test_zwei_sitzungen_chronologisch(self):
        self.assertEqual(len(self.stand.sitzungen), 2)
        self.assertEqual((self.s1.von, self.s2.von), ("09:00", "11:00"))
        self.assertEqual(self.stand.fehler, [])

    def test_titel_zeitraum_branch_ordner(self):
        self.assertEqual(self.s1.titel, "Test-Sitzung")
        self.assertEqual((self.s1.von, self.s1.bis), ("09:00", "10:00"))
        self.assertEqual(self.s1.branch, "main")
        self.assertEqual(self.s1.ordner, ".")
        self.assertEqual(self.s1.kennung, "s1")

    def test_auftraege_gefiltert_und_gekuerzt(self):
        self.assertEqual(len(self.s1.auftraege), 12)
        self.assertEqual(self.s1.auftraege[0], "Auftrag eins")
        self.assertEqual(self.s1.auftraege[1], "Auftrag zwei")
        self.assertEqual(self.s1.weitere_auftraege, 4)
        alle = " ".join(self.s1.auftraege)
        for verboten in ("meta text", "system-reminder", "Request interrupted", "task-notification", "Gestern-Auftrag", "Subagent", "Alt"):
            self.assertNotIn(verboten, alle)

    def test_schlussbericht(self):
        self.assertEqual(self.s1.schluss, "Schlussbericht: alles erledigt.")
        self.assertFalse(self.s1.schluss_offen)

    def test_fehler_dateien_werkzeuge_chargen(self):
        self.assertEqual(self.s1.fehler_anzahl, 2)
        self.assertEqual(self.s1.fehler, ["Fehler: Datei fehlt", "ls: x: No such file or directory"])
        self.assertEqual(self.s1.dateien, ["projects/Ohne/Projekt/2026-09 Charge/_intern/x.py", "tools/neu.py"])
        self.assertEqual(self.s1.werkzeuge, [("Edit", 1), ("Write", 1)])
        self.assertEqual(self.s1.chargen, ["projects/Ohne/Projekt/2026-09 Charge"])

    def test_worktree_sitzung_offen_mit_vielen_fehlern(self):
        self.assertEqual(self.s2.titel, "Offener Auftrag")
        self.assertEqual(self.s2.branch, "claude/x")
        self.assertTrue(self.s2.schluss_offen)
        self.assertEqual(self.s2.schluss, "Ich prüfe.")
        self.assertEqual(self.s2.fehler_anzahl, 5)
        self.assertEqual(self.s2.fehler, [f"Fehler {n}" for n in range(1, 6)])
        self.assertEqual(self.s2.werkzeuge, [("Bash", 1)])
        self.assertTrue(self.s2.ordner.startswith("/"))

    def test_gestern(self):
        gestern = sitzungen_stand(self.ordner, HEUTE - timedelta(days=1), self.repo)
        self.assertEqual(len(gestern.sitzungen), 1)
        s = gestern.sitzungen[0]
        self.assertEqual(s.auftraege, ["Gestern-Auftrag"])
        self.assertEqual((s.von, s.bis), ("22:00", "22:00"))
        self.assertTrue(s.schluss_offen)

    def test_fehlender_ordner(self):
        stand = sitzungen_stand([self.basis / "fehlt"], HEUTE, self.repo)
        self.assertEqual(stand.sitzungen, [])
        self.assertEqual(len(stand.fehler), 1)


class Pfade(unittest.TestCase):
    def test_relativ(self):
        repo = Path("/tmp/x/repo")
        self.assertEqual(relativ("/tmp/x/repo/tools/a.py", repo), "tools/a.py")
        self.assertEqual(relativ("/tmp/x/repo", repo), ".")
        self.assertEqual(relativ("/tmp/x/anders/a.py", repo), "/tmp/x/anders/a.py")

    def test_charge_aus_pfad(self):
        self.assertEqual(charge_aus_pfad("projects/K/P/2026-09 C/_intern/x.py"), "projects/K/P/2026-09 C")
        self.assertEqual(charge_aus_pfad("projects/K/2026-08 C/Protokoll.md"), "projects/K/2026-08 C")
        self.assertIsNone(charge_aus_pfad("projects/K/P/Protokoll.md"))
        self.assertIsNone(charge_aus_pfad("tools/a.py"))


class SitzungenStandWirftNie(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="sitzungen_test_"))
        self.repo = self.basis / "repo"
        self.repo.mkdir()
        self.ordner = self.basis / "sitzungen"
        self.ordner.mkdir()
        from testhilfe import _rec, lokal
        kaputt = _rec("assistant", lokal(HEUTE, 9, 0), [{"type": "tool_use", "name": ["Edit"], "input": {}}], self.repo, "main")
        (self.ordner / "kaputt.jsonl").write_text(json.dumps(kaputt) + "\n")
        gut = _rec("user", lokal(HEUTE, 10, 0), "Guter Auftrag", self.repo, "main")
        (self.ordner / "gut.jsonl").write_text(json.dumps(gut) + "\n")

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_unhashbarer_werkzeugname_wird_toleriert(self):
        stand = sitzungen_stand([self.ordner], HEUTE, self.repo)
        self.assertEqual(stand.fehler, [])
        kaputt = next(s for s in stand.sitzungen if s.kennung == "kaputt")
        self.assertEqual(kaputt.werkzeuge, [("?", 1)])

    def test_ausnahme_in_einer_datei_bricht_die_anderen_nicht_ab(self):
        import sitzungen_stand as modul
        echt = modul.sitzung_lesen

        def explodiert(datei, tag, repo):
            if datei.name == "kaputt.jsonl":
                raise RuntimeError("Testexplosion")
            return echt(datei, tag, repo)

        with mock.patch.object(modul, "sitzung_lesen", explodiert):
            stand = sitzungen_stand([self.ordner], HEUTE, self.repo)
        self.assertEqual([s.kennung for s in stand.sitzungen], ["gut"])
        self.assertTrue(any("Testexplosion" in f for f in stand.fehler), stand.fehler)


if __name__ == "__main__":
    unittest.main()
