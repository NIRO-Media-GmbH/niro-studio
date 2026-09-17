import unittest

from text import erste_zeile, kuerzen


class Kuerzen(unittest.TestCase):
    def test_normalisiert_whitespace(self):
        self.assertEqual(kuerzen("  a \n b\t c ", 100), "a b c")

    def test_kuerzt_mit_auslassung(self):
        self.assertEqual(kuerzen("abcdefghij", 5), "abcd…")
        self.assertEqual(len(kuerzen("x" * 500, 200)), 200)

    def test_laesst_kurzes_stehen(self):
        self.assertEqual(kuerzen("kurz", 4), "kurz")


class ErsteZeile(unittest.TestCase):
    def test_erste_nicht_leere_zeile(self):
        self.assertEqual(erste_zeile(["\n\nFehler: x\nDetails", "mehr"]), "Fehler: x")

    def test_leer(self):
        self.assertEqual(erste_zeile([]), "")
        self.assertEqual(erste_zeile(["", " \n "]), "")


if __name__ == "__main__":
    unittest.main()
