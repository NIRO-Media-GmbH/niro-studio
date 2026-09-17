"""Ende-zu-Ende-Tests des Sammlers und Runner für alle *_test.py in diesem Ordner.
Aufruf: python3 tools/tagesbericht/sammler_test.py   (Exit 0 = alle Tests bestanden)"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import date
from pathlib import Path

from testhilfe import chargen_anlegen, gedaechtnis_anlegen, repo_anlegen, sitzungen_anlegen

HIER = Path(__file__).resolve().parent
SAMMLER = HIER / "sammler.py"
ABGLEICH_ECHT = HIER.parent / "studio_abgleich.sh"
HEUTE = date(2026, 9, 17)


def ohne_stand(text: str) -> str:
    return "\n".join(z for z in text.splitlines() if not z.startswith("Stand: "))


class SammlerEndeZuEnde(unittest.TestCase):
    def setUp(self):
        self.basis = Path(tempfile.mkdtemp(prefix="sammler_test_"))
        daten = repo_anlegen(self.basis, HEUTE)
        self.repo, self.wt = daten["repo"], daten["wt"]
        chargen_anlegen(self.repo, HEUTE)
        self.projects_dir = self.basis / "claude" / "projects"
        sitzungen_anlegen(self.projects_dir, self.repo, self.wt, HEUTE)
        self.gedaechtnis = self.basis / "gedaechtnis"
        gedaechtnis_anlegen(self.gedaechtnis, HEUTE)
        self.nas = self.basis / "nas" / "NIRO Studio"
        (self.basis / "nas").mkdir()
        shutil.copy(ABGLEICH_ECHT, self.repo / "tools" / "studio_abgleich.sh")
        self.env = {**os.environ,
                    "NIRO_STUDIO_REPO": str(self.repo), "NIRO_STUDIO_NAS": str(self.nas), "NIRO_STUDIO_MAC": "Test-Mac",
                    "NIRO_STUDIO_HEUTE": HEUTE.isoformat(), "NIRO_CLAUDE_PROJECTS_DIR": str(self.projects_dir),
                    "NIRO_CLAUDE_MEMORY_DIR": str(self.gedaechtnis),
                    "NIRO_RESOLVE_LUT_DIR": str(self.basis / "lut_lokal"), "NIRO_NAS_LUT_DIR": str(self.basis / "lut_nas" / "NIRO Grading")}
        for k in ("NIRO_SAMMLER_CMD", "NIRO_SAMMLER_ABGLEICH_CMD", "NIRO_SAMMLER_ABGLEICH_TIMEOUT"):
            self.env.pop(k, None)
        self.berichte = self.repo / "berichte"

    def tearDown(self):
        shutil.rmtree(self.basis, ignore_errors=True)

    def lauf(self, *args, **env):
        return subprocess.run([sys.executable, str(SAMMLER), *args], env={**self.env, **env}, capture_output=True,
                              text=True, cwd=str(self.repo), timeout=120)

    def test_schreibt_heute_und_gestern_ohne_abgleich(self):
        aus = self.lauf("--ohne-abgleich")
        self.assertEqual(aus.returncode, 0, aus.stderr)
        heute = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        gestern = (self.berichte / "2026-09-16" / "Test-Mac.md").read_text()
        patch = (self.berichte / "2026-09-17" / "Test-Mac.patch").read_text()
        self.assertTrue(heute.startswith("# Tagesstand Test-Mac — 2026-09-17\n"))
        self.assertIn("Sitzungen 2 · Commits 2", heute)
        for erwartet in ("A heute", "B ungepusht", "Test-Sitzung", "Offener Auftrag", "AutoCut: Kantenprüfung",
                         "— in 6 Chargen", "Export/a.mp4", "notiz-a", "Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge",
                         "Ungepusht: claude/x (+1)", "Worktree mit Änderungen"):
            self.assertIn(erwartet, heute)
        self.assertIn("A0 gestern", gestern)
        self.assertIn("Gestern-Auftrag", gestern)
        self.assertIn("Sitzungen 1 · Commits 1", gestern)
        self.assertFalse((self.berichte / "2026-09-16" / "Test-Mac.patch").exists())
        self.assertTrue(patch.startswith("# Sicherung Test-Mac "))
        self.assertIn("+Inhalt der neuen Datei", patch)
        self.assertFalse((self.nas / "berichte").exists())
        self.assertIn("Sammler: berichte/2026-09-17/Test-Mac.md", aus.stdout)

    def test_zweiter_lauf_gleicher_inhalt(self):
        self.lauf("--ohne-abgleich")
        erster = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        time.sleep(1.1)
        self.lauf("--ohne-abgleich")
        zweiter = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        self.assertEqual(ohne_stand(erster), ohne_stand(zweiter))

    def test_nur_ein_tag(self):
        aus = self.lauf("--tag", "2026-09-16", "--ohne-abgleich", "--still")
        self.assertEqual((aus.returncode, aus.stdout), (0, ""))
        self.assertTrue((self.berichte / "2026-09-16" / "Test-Mac.md").exists())
        self.assertFalse((self.berichte / "2026-09-17").exists())

    def test_abgleich_mit_echtem_skript(self):
        fremd = self.nas / "berichte" / "2026-09-15" / "Anderer-Mac.md"
        fremd.parent.mkdir(parents=True)
        fremd.write_text("# Tagesstand Anderer-Mac — 2026-09-15\nStand: 2026-09-15 18:00 · Repo x · HEAD main a · Sitzungen 2 · Commits 0\n")
        aus = self.lauf()
        self.assertEqual(aus.returncode, 0, aus.stderr)
        self.assertTrue((self.nas / "berichte" / "2026-09-17" / "Test-Mac.md").exists())
        self.assertTrue((self.nas / "berichte" / "2026-09-17" / "Test-Mac.patch").exists())
        self.assertEqual((self.berichte / "2026-09-15" / "Anderer-Mac.md").read_text(), fremd.read_text())

    def test_hook_hinweis(self):
        fremd = self.nas / "berichte" / "2026-09-15" / "Anderer-Mac.md"
        fremd.parent.mkdir(parents=True)
        fremd.write_text("# Tagesstand Anderer-Mac — 2026-09-15\nStand: 2026-09-15 18:00 · Repo x · HEAD main a · Sitzungen 2 · Commits 0\n")
        leer = self.nas / "berichte" / "2026-09-14" / "Anderer-Mac.md"
        leer.parent.mkdir(parents=True)
        leer.write_text("# Tagesstand Anderer-Mac — 2026-09-14\nStand: 2026-09-14 18:00 · Repo x · HEAD main a · Sitzungen 0 · Commits 0\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.returncode, 0, aus.stderr)
        self.assertEqual(aus.stdout, "Tagesbericht für 16.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-16“.\n")
        (self.berichte / "2026-09-16" / "Tagesbericht.md").write_text("# Tagesbericht\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.stdout, "Tagesbericht für 15.09.2026 fehlt — Trigger: „Tagesbericht: 2026-09-15“.\n")
        (self.berichte / "2026-09-15" / "Tagesbericht.md").write_text("# Tagesbericht\n")
        aus = self.lauf("--hook")
        self.assertEqual(aus.stdout, "")

    def test_abgleich_zeitlimit(self):
        schlaefer = self.basis / "schlaefer.sh"
        schlaefer.write_text("#!/bin/sh\nsleep 5\n")
        schlaefer.chmod(schlaefer.stat().st_mode | stat.S_IXUSR)
        start = time.monotonic()
        aus = self.lauf("--hook", NIRO_SAMMLER_ABGLEICH_CMD=str(schlaefer), NIRO_SAMMLER_ABGLEICH_TIMEOUT="1")
        self.assertLess(time.monotonic() - start, 8)
        self.assertEqual(aus.returncode, 0)
        self.assertIn("Abgleich abgebrochen", aus.stderr)
        self.assertTrue((self.berichte / "2026-09-17" / "Test-Mac.md").exists())

    def test_robust_ohne_sitzungen_nas_und_gedaechtnis(self):
        aus = self.lauf(NIRO_CLAUDE_PROJECTS_DIR=str(self.basis / "fehlt"), NIRO_STUDIO_NAS=str(self.basis / "weg" / "NIRO Studio"),
                        NIRO_CLAUDE_MEMORY_DIR=str(self.basis / "fehlt2"))
        self.assertEqual(aus.returncode, 0, aus.stderr)
        heute = (self.berichte / "2026-09-17" / "Test-Mac.md").read_text()
        self.assertIn("## Sitzungen\n- keine\n", heute)
        self.assertIn("Sitzungen 0 · Commits 2", heute)
        self.assertIn("- Fehler: Gedächtnis", heute)

    def test_kaputtes_repo_endet_mit_null(self):
        aus = self.lauf("--ohne-abgleich", NIRO_STUDIO_REPO=str(self.basis / "kein-repo"))
        self.assertEqual(aus.returncode, 0)
        self.assertTrue((self.basis / "kein-repo" / "berichte" / "2026-09-17" / "Test-Mac.md").exists())

    def test_unbekannte_option_endet_mit_null(self):
        aus = self.lauf("--gibt-es-nicht")
        self.assertEqual(aus.returncode, 0)
        self.assertIn("usage", aus.stderr.lower())
        self.assertFalse((self.berichte / "2026-09-17").exists())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(HIER), pattern="*_test.py", top_level_dir=str(HIER))
    ergebnis = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if ergebnis.wasSuccessful() else 1)
