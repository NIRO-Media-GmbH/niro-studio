import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import umgebung
from umgebung import Umgebung, schluessel_fuer, tag_parsen, tagesgrenzen, umgebung_laden


class SchluesselUndTag(unittest.TestCase):
    def test_schluessel(self):
        self.assertEqual(schluessel_fuer(Path("/Users/jansantos/NIRO Studio")), "-Users-jansantos-NIRO-Studio")

    def test_tag_parsen(self):
        heute = date(2026, 9, 17)
        self.assertEqual(tag_parsen(None, heute), heute)
        self.assertEqual(tag_parsen("heute", heute), heute)
        self.assertEqual(tag_parsen("gestern", heute), date(2026, 9, 16))
        self.assertEqual(tag_parsen("2026-09-01", heute), date(2026, 9, 1))

    def test_tagesgrenzen(self):
        anfang, ende = tagesgrenzen(date(2026, 9, 17))
        self.assertIsNotNone(anfang.tzinfo)
        self.assertEqual(anfang.date(), date(2026, 9, 17))
        self.assertEqual((anfang.hour, anfang.minute), (0, 0))
        self.assertEqual(ende - anfang, timedelta(days=1))


class UmgebungAusVariablen(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="umgebung_test_"))
        self.repo = self.basis / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.projects = self.basis / "projects"
        self.schluessel = schluessel_fuer(self.repo)
        for name in (self.schluessel, self.schluessel + "--claude-worktrees-x", "-anderes-repo"):
            (self.projects / name).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_laden_aus_variablen(self):
        env = {
            "NIRO_STUDIO_REPO": str(self.repo),
            "NIRO_STUDIO_NAS": str(self.basis / "nas" / "NIRO Studio"),
            "NIRO_STUDIO_MAC": "Test/Mac:1",
            "NIRO_STUDIO_HEUTE": "2026-09-17",
            "NIRO_CLAUDE_PROJECTS_DIR": str(self.projects),
        }
        with mock.patch.dict(os.environ, env):
            os.environ.pop("NIRO_CLAUDE_MEMORY_DIR", None)
            u = umgebung_laden()
        self.assertEqual(u.repo, self.repo)
        self.assertEqual(u.mac, "Test-Mac-1")
        self.assertEqual(u.heute, date(2026, 9, 17))
        self.assertEqual(u.gedaechtnis, self.projects / self.schluessel / "memory")
        self.assertEqual(u.berichte, self.repo / "berichte")
        self.assertFalse(u.nas_da())
        self.assertEqual([p.name for p in u.sitzungsordner()],
                         sorted([self.schluessel, self.schluessel + "--claude-worktrees-x"]))

    def test_mac_aus_git_config(self):
        subprocess.run(["git", "-C", str(self.repo), "config", "niro.mac", "Studio-Mac"], check=True)
        with mock.patch.dict(os.environ, {"NIRO_STUDIO_REPO": str(self.repo)}):
            os.environ.pop("NIRO_STUDIO_MAC", None)
            self.assertEqual(umgebung.mac_name(self.repo), "Studio-Mac")

    def test_nas_da_wenn_elternordner_existiert(self):
        (self.basis / "nas").mkdir()
        u = Umgebung(repo=self.repo, nas=self.basis / "nas" / "NIRO Studio", mac="M", heute=date(2026, 9, 17),
                     projects_dir=self.projects, gedaechtnis=self.basis / "g")
        self.assertTrue(u.nas_da())

    def test_sitzungsordner_ohne_projects_dir(self):
        u = Umgebung(repo=self.repo, nas=self.basis / "nas", mac="M", heute=date(2026, 9, 17),
                     projects_dir=self.basis / "fehlt", gedaechtnis=self.basis / "g")
        self.assertEqual(u.sitzungsordner(), [])


if __name__ == "__main__":
    unittest.main()
