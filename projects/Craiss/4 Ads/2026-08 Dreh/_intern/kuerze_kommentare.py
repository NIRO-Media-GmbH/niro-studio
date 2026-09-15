"""Kommentar-Spalte der Ablauf-Tabellen auf Telegrammstil kürzen.

NIRO-Standard: max ~15 Wörter je Kommentar. Video 3 und 4 haben je 16 Beats —
die Zeilen bleiben (eine Zeile pro Aussage ist Pflicht), gekürzt wird nur der
Kommentar, damit das 2-Seiten-Budget hält.
"""
from pathlib import Path

PLANS = Path("/Users/jansantos/NIRO Studio/projects/Craiss/4 Ads/2026-08 Dreh/"
             "Ergebnisse/O-Ton-Pläne")

KURZ = {
    "video-3-viele-jahre.md": {
        "1a": 'Wort bei 06:32,2–06:32,8, danach 2,2 s Luft. Alt: 06:28–06:29',
        "1b": '**Anderer Clip!** 0785 = 10-s-Fehlstart. Einziger sauberer Solo-Take',
        "1c": '**Nicht im Transkript** — Take in der Tonlücke 08:36,1–08:37,8. '
              'Am Original prüfen. Alt-Lücken: ≈08:27 / ≈08:31,5 / ≈08:33,5',
        "2": 'Ersatz für den nicht gedrehten Abbinder. Blick nicht in die Kamera — Achse beachten',
        "3": 'In nach der Rückfrage. **Nie „30 Jahre" einblenden**',
        "4": '18 s — Mitte per […] kürzen. **Freigabe für „Albert Craiss" einholen**',
        "5": 'In **zwingend ab 07:18** (davor polnische Rückfrage), Out vor „Und äh Wochenende"',
        "6": 'Emotionaler Anker. Direkt an #7 anschließbar — 17 s ohne Schnitt',
        "7": 'Sprachliste vor Veröffentlichung mit Craiss gegenprüfen',
        "8": 'Ehrlichster Moment des Drehs — Sprachbarriere als Sympathie',
        "9": '1,5 s, spontan, 3 s Luft davor. Zwei Jakub-Takes = Maximum',
        "10": 'Auf 8 s kürzen — der Vollsatz läuft 14 s aus',
        "11": 'Regie-Ansage läuft bis 05:33 — Schnitt frühestens 05:34,5',
        "12": 'Untertitel: „Ich fahr **auf den** Hof"',
        "13": 'Bester Beweis gegen „nur eine Nummer" — und er darf Nein sagen',
        "14": 'Nur den Schlusssatz — Vorlauf ab 10:57 ist sprachlich kaputt',
        "15": '**Alle Zahlen freigeben lassen.** ~1000 Mitarbeiter gilt für die **Gruppe**',
        "16": 'm/w/d ist Pflicht',
    },
    "video-4-funnel.md": {
        "2": 'Schluss-Floskel „stehe gerne zur Verfügung" **immer** weg. UT: „geschäftsführende**r**"',
        "3": 'Mitte („Vorteile und Nachteile") per […] raus. **Out hart 02:42**',
        "4": 'Stärkster rationaler Beweis. Boardinghäuser freigeben — impliziert eine Zusage',
        "6": 'Bestes Schlagwort des Drehs. **Erst ab 03:35** — davor gesperrter Vorlauf',
        "8": 'Ab 14:38 wiederholt er sich dreifach — per […] weg',
        "9": '**Out spätestens 15:01** — danach absolute Sperrzone. Schlusssatz trägt auch solo',
        "10": '**Bester Take.** Alles vor 05:02 ist Notmaterial — davor war sie angespannt',
        "13": '**Keine Frist einblenden** — „24 Stunden" existiert in keinem Take',
        "14": '**Out hart 08:00,6** — danach folgt ein unfertiger Nachsatz. Alt: 07:42–07:47',
        "16": 'Bester CTA-Take. **Bild am Satzende prüfen** — kein weiterer Take. Alt: 08:35–08:38',
    },
}


def main() -> None:
    for fname, mapping in KURZ.items():
        p = PLANS / fname
        vorher = len(p.read_text(encoding="utf-8"))
        out, getroffen = [], 0
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and line.count("|") >= 8:
                cells = line.strip("|").split("|")
                key = cells[0].strip()
                if key in mapping:
                    cells[-1] = " " + mapping[key] + " "
                    line = "|" + "|".join(cells) + "|"
                    getroffen += 1
            out.append(line)
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        nachher = len(p.read_text(encoding="utf-8"))
        fehlt = set(mapping) - set()
        print(f"{fname}: {getroffen}/{len(mapping)} Zeilen gekürzt, "
              f"{vorher} -> {nachher} Zeichen")


if __name__ == "__main__":
    main()
