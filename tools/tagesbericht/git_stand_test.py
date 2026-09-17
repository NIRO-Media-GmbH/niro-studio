import os
import shutil
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from git_stand import git_stand, sicherung, worktrees_lesen
from testhilfe import lokal, repo_anlegen

HEUTE = date(2026, 9, 17)


class GitStandAusRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.basis = Path(tempfile.mkdtemp(prefix="git_stand_test_"))
        daten = repo_anlegen(cls.basis, HEUTE)
        cls.repo, cls.wt = daten["repo"], daten["wt"]
        cls.stand = git_stand(cls.repo, HEUTE)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.basis, ignore_errors=True)

    def branch(self, name):
        return next(b for b in self.stand.branches if b.name == name)

    def test_kopf(self):
        self.assertEqual(self.stand.head_branch, "main")
        self.assertEqual(len(self.stand.head_hash), 7)
        self.assertEqual(self.stand.fehler, [])

    def test_auf_main_nur_heute(self):
        self.assertEqual([c.betreff for c in self.stand.auf_main], ["A heute"])
        self.assertEqual(self.stand.auf_main[0].zeit, "10:00")
        self.assertEqual(len(self.stand.auf_main[0].hash), 7)

    def test_ungepushter_branch(self):
        x = self.branch("claude/x")
        self.assertEqual((x.vor, x.hinter), (1, 0))
        self.assertEqual(x.letzter, "2026-09-17")
        self.assertEqual(os.path.realpath(x.worktree), os.path.realpath(str(self.wt)))
        self.assertEqual([(c.zeit, c.betreff) for c in x.commits_heute], [("11:30", "B ungepusht")])

    def test_main_ohne_vorsprung(self):
        m = self.branch("main")
        self.assertEqual((m.vor, m.hinter), (0, 0))
        self.assertIsNone(m.worktree)
        self.assertEqual(m.commits_heute, [])

    def test_commits_gesamt(self):
        self.assertEqual(self.stand.commits_gesamt, 2)

    def test_unversioniert_hauptordner(self):
        haupt = next(w for w in self.stand.worktrees if w.ist_haupt)
        self.assertEqual(haupt.branch, "main")
        gruppen = {g.pfad: g for g in haupt.gruppen}
        self.assertEqual(sorted(gruppen), ["NOTIZ.md", "tools/a.txt", "tools/bin.dat", "tools/motion/"])
        self.assertEqual((gruppen["tools/a.txt"].geaendert, gruppen["tools/a.txt"].neu), (1, 0))
        self.assertEqual((gruppen["tools/motion/"].neu, gruppen["tools/motion/"].weitere), (2, 0))
        self.assertEqual(gruppen["tools/motion/"].beispiele, ["tools/motion/neu.ts", "tools/motion/src/x.ts"])
        self.assertRegex(gruppen["tools/motion/"].juengste, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
        self.assertEqual(gruppen["NOTIZ.md"].neu, 1)

    def test_unversioniert_worktree(self):
        wt = next(w for w in self.stand.worktrees if not w.ist_haupt)
        self.assertEqual(wt.branch, "claude/x")
        self.assertEqual([(g.pfad, g.geaendert) for g in wt.gruppen], [("tools/b.txt", 1)])

    def test_stashes(self):
        self.assertEqual(self.stand.stashes, 1)

    def test_gestern(self):
        gestern = git_stand(self.repo, HEUTE - timedelta(days=1))
        self.assertEqual([c.betreff for c in gestern.auf_main], ["A0 gestern"])
        self.assertEqual(next(b for b in gestern.branches if b.name == "claude/x").commits_heute, [])

    def test_worktrees_lesen(self):
        wts = worktrees_lesen(self.repo)
        self.assertEqual([b for _, b in wts], ["main", "claude/x"])

    def test_sicherung(self):
        patch = sicherung(self.repo, "Test-Mac", lokal(HEUTE, 16, 40))
        self.assertTrue(patch.startswith("# Sicherung Test-Mac 2026-09-17 16:40\n"))
        self.assertIn("# Worktree: ", patch)
        self.assertIn("(main)", patch)
        self.assertIn("(claude/x)", patch)
        self.assertIn("diff --git a/tools/a.txt b/tools/a.txt", patch)
        self.assertIn("+a3 lokal", patch)
        self.assertIn("+Inhalt der neuen Datei", patch)
        self.assertIn("+notiz", patch)
        self.assertIn("# nicht gesichert (groß oder binär): tools/bin.dat", patch)
        self.assertIn("+b geändert", patch)
        self.assertLess(patch.index("(main)"), patch.index("(claude/x)"))


class GitStandOhneRemote(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="git_stand_test_"))

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def test_repo_ohne_origin(self):
        from testhilfe import commit, git
        repo = self.basis / "solo"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@t")
        git(repo, "config", "user.name", "t")
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "x.txt").write_text("x\n")
        commit(repo, "einziger", lokal(HEUTE, 8))
        stand = git_stand(repo, HEUTE)
        self.assertEqual(stand.auf_main, [])
        m = next(b for b in stand.branches if b.name == "main")
        self.assertIsNone(m.vor)
        self.assertEqual([c.betreff for c in m.commits_heute], ["einziger"])
        self.assertEqual(stand.fehler, [])

    def test_kein_repo(self):
        stand = git_stand(self.basis / "leer", HEUTE)
        self.assertTrue(stand.fehler)
        self.assertEqual(stand.auf_main, [])
        patch = sicherung(self.basis / "leer", "M", lokal(HEUTE, 9))
        self.assertIn("# Fehler", patch)


if __name__ == "__main__":
    unittest.main()
