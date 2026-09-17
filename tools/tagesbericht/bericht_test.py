import unittest
from datetime import date, datetime

from bericht import Tagesstand, hinweise, rendern
from chargen_stand import ChargenStand, Lieferung
from gedaechtnis_stand import Notiz
from git_stand import Branch, Commit, GitStand, Gruppe, Worktree
from sitzungen_stand import Sitzung, SitzungenStand

HEUTE = date(2026, 9, 17)
STAND = datetime(2026, 9, 17, 16, 40)


def voller_stand() -> Tagesstand:
    git = GitStand(
        head_branch="main", head_hash="abc1234",
        auf_main=[Commit("10:00", "abc1234", "A heute")],
        branches=[Branch("claude/x", 1, 0, "2026-09-17", "/wt", [Commit("11:30", "b000000", "B ungepusht")]),
                  Branch("main", 0, 0, "2026-09-17", None, [])],
        worktrees=[Worktree("/repo", "main", True, [Gruppe("tools/motion/", 0, 2, 0, "2026-09-17 09:00",
                                                           ["tools/motion/neu.ts", "tools/motion/src/x.ts"], 0)]),
                   Worktree("/wt", "claude/x", False, [])],
        stashes=1)
    chargen = ChargenStand(
        je_charge_alle={"projects/Kunde/Projekt/2026-09 Charge": ["2026-09-17 11:07 — AutoCut: Kantenprüfung"],
                        "projects/K0/P/2026-01 C": ["2026-09-17 — Medien aufs NAS verschoben"]},
        je_charge={"projects/Kunde/Projekt/2026-09 Charge": ["2026-09-17 11:07 — AutoCut: Kantenprüfung"]},
        sammel=[("2026-09-17 — Medien aufs NAS verschoben", 6)],
        lieferungen=[Lieferung("projects/Kunde/Projekt/2026-09 Charge", 7, ["Export/a.mp4", "Export/b.mp4"])])
    s1 = Sitzung(kennung="s1", titel="Test-Sitzung", ordner=".", branch="main", von="09:00", bis="10:00",
                 auftraege=["Auftrag eins", "Auftrag zwei"], weitere_auftraege=14, schluss="Schlussbericht: alles erledigt.",
                 fehler_anzahl=1, fehler=["Fehler: Datei fehlt"], dateien=["projects/Ohne/Projekt/2026-09 Charge/_intern/x.py"],
                 werkzeuge=[("Edit", 1)], chargen=["projects/Ohne/Projekt/2026-09 Charge"])
    s2 = Sitzung(kennung="s2", titel="Offen", ordner="/wt", branch="claude/x", von="11:00", bis="11:06",
                 auftraege=["Offener Auftrag"], schluss="Ich prüfe.", schluss_offen=True, fehler_anzahl=5,
                 fehler=[f"Fehler {n}" for n in range(1, 6)], werkzeuge=[("Bash", 1)])
    return Tagesstand(mac="Test-Mac", tag=HEUTE, stand=STAND, repo="/repo", git=git, chargen=chargen,
                      sitzungen=SitzungenStand(sitzungen=[s1, s2]), notizen=[Notiz("notiz-a", "Eine Notiz")],
                      fehler=["Testfehler"])


def leerer_stand() -> Tagesstand:
    return Tagesstand(mac="Test-Mac", tag=HEUTE, stand=STAND, repo="/repo", git=GitStand(head_branch="main", head_hash="abc1234"),
                      chargen=ChargenStand(), sitzungen=SitzungenStand(), notizen=[])


class Hinweise(unittest.TestCase):
    def test_alle_hinweisarten(self):
        h = hinweise(voller_stand())
        self.assertEqual(h, [
            "Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge — Sitzung „Test-Sitzung“ (09:00–10:00)",
            "Ohne Schlussbericht: „Offen“ (11:00–11:06)",
            "Viele Tool-Fehler: „Offen“ (5)",
            "Ungepusht: claude/x (+1)",
        ])

    def test_worktree_mit_aenderungen(self):
        t = voller_stand()
        t.git.worktrees[1].gruppen.append(Gruppe("tools/b.txt", 1))
        self.assertIn("Worktree mit Änderungen: /wt (claude/x)", hinweise(t))

    def test_leer(self):
        self.assertEqual(hinweise(leerer_stand()), [])


class Rendern(unittest.TestCase):
    def setUp(self):
        self.md = rendern(voller_stand())

    def test_kopf(self):
        zeilen = self.md.splitlines()
        self.assertEqual(zeilen[0], "# Tagesstand Test-Mac — 2026-09-17")
        self.assertEqual(zeilen[1], "Stand: 2026-09-17 16:40 · Repo /repo · HEAD main abc1234 · Sitzungen 2 · Commits 2")

    def test_git(self):
        self.assertIn("## Git\n### Auf main\n- 10:00 abc1234 A heute\n", self.md)
        self.assertIn("### Ungepusht\n- claude/x (+1 / −0, letzter Commit 2026-09-17, Worktree /wt)\n  - 11:30 b000000 B ungepusht\n", self.md)
        self.assertIn("### Branches ohne Commits heute\n- main: +0 / −0, letzter Commit 2026-09-17\n", self.md)
        self.assertIn("### Unversioniert (Hauptordner, main)\n- tools/motion/: 0 geändert, 2 neu, 0 gelöscht, jüngste 2026-09-17 09:00 — tools/motion/neu.ts, tools/motion/src/x.ts\n", self.md)
        self.assertIn("### Unversioniert (/wt, claude/x)\n- keine\nStashes: 1\n", self.md)

    def test_chargen(self):
        self.assertIn("## Chargen\n### Protokoll-Einträge\n- „2026-09-17 — Medien aufs NAS verschoben“ — in 6 Chargen\n- projects/Kunde/Projekt/2026-09 Charge\n  - 2026-09-17 11:07 — AutoCut: Kantenprüfung\n", self.md)
        self.assertIn("### Neue Dateien unter Ergebnisse/\n- projects/Kunde/Projekt/2026-09 Charge: 7 Dateien — Export/a.mp4, Export/b.mp4 (+5)\n", self.md)
        self.assertIn("Änderungszeiten bleiben beim Abgleich erhalten", self.md)

    def test_sitzungen(self):
        self.assertIn("### 09:00–10:00 · Test-Sitzung · main · 16 Aufträge · 1 Tool-Fehler\n- Ordner: . · Sitzung s1\n- Aufträge: 1. „Auftrag eins“ 2. „Auftrag zwei“ (+14 weitere)\n- Schlussbericht: „Schlussbericht: alles erledigt.“\n- Tool-Fehler: „Fehler: Datei fehlt“\n- Dateien: projects/Ohne/Projekt/2026-09 Charge/_intern/x.py\n- Werkzeuge: Edit 1\n- Chargen: projects/Ohne/Projekt/2026-09 Charge\n", self.md)
        self.assertIn("### 11:00–11:06 · Offen · claude/x · 1 Aufträge · 5 Tool-Fehler\n", self.md)
        self.assertIn("- Schlussbericht: ohne Schlussbericht — letzte Antwort: „Ich prüfe.“\n", self.md)

    def test_gedaechtnis_und_hinweise(self):
        self.assertIn("## Gedächtnis\n- notiz-a: Eine Notiz\n", self.md)
        self.assertIn("## Hinweise\n- Protokoll fehlt: projects/Ohne/Projekt/2026-09 Charge", self.md)
        self.assertIn("- Fehler: Testfehler\n", self.md)

    def test_leer_ueberall_keine(self):
        md = rendern(leerer_stand())
        for abschnitt in ("### Auf main", "### Ungepusht", "### Branches ohne Commits heute", "### Protokoll-Einträge",
                          "### Neue Dateien unter Ergebnisse/", "## Sitzungen", "## Gedächtnis", "## Hinweise"):
            self.assertIn(abschnitt + "\n- keine\n", md)
        self.assertIn("Sitzungen 0 · Commits 0", md)
        self.assertIn("Stashes: 0\n", md)


if __name__ == "__main__":
    unittest.main()
