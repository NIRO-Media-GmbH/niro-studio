# NIRO Review

Lokales Review-Werkzeug im NIRO-CI: Claude legt Videostände ab, du kommentierst im Browser an der Stelle im Video,
Claude setzt um und legt die nächste Version daneben. Ordnung Kunde → Projekt → Video → V1, V2 … auf dem NAS
(`08_Claude Tools/NIRO Studio/review/`), beide Macs sehen denselben Stand. Kunden-Feedback läuft weiter über
Dropbox Replay.

## Einrichten (einmal je Mac)

```bash
python3 tools/review/review.py installieren
```

Legt den LaunchAgent `de.niro.review` an (startet bei Anmeldung, startet nach Absturz neu), Adresse
`http://localhost:4711`, Log `~/Library/Logs/NIRO Review/server.log`. Braucht Python ≥ 3.9 und ffmpeg (SETUP.md).
Nach einem Code-Update (`git pull`) den Server neu starten:

```bash
launchctl kickstart -k gui/$(id -u)/de.niro.review
```

Entfernen: `python3 tools/review/review.py deinstallieren`. Ohne LaunchAgent: `python3 tools/review/review.py server`.
Wer den Agent vor dem 18.09. 15 Uhr installiert hat: einmal `installieren` wiederholen — der alte Eintrag lief als
„Background"-Prozess, macOS drosselt dann die Netz-I/O (erster NAS-Index 36 s statt 0,2 s).

## Bedienen

- **Projekte** links, Videos als Karten mit Vorschaubild, Versions-Chip und Zustand (Review offen · bei Claude ·
  Freigegeben). Im geöffneten Projekt listet die Seitenleiste alle Videos (Punkt = Zustand, Version, offene Kommentare),
  das aktuelle ist markiert. Suchfeld filtert Projekte und Titel.
- **Player:** oben links ▲/▼ zum vorherigen/nächsten Video des Projekts mit Position „3 / 30" (Tasten ↑/↓); Timecode
  frame-genau, Scrubber mit Kommentar-Markern (Punkt = Stelle, Balken = Bereich), Versions-Pillen.
  Tippen im Kommentarfeld pausiert das Video; der Kommentar landet am aktuellen Frame. „Bereich bis hier" (oder `O`)
  macht einen Bereich, „Allgemein" einen Kommentar ohne Zeit.
- **Bausteine** über dem Kommentarfeld: Klick fügt den Text ein (mehrere Klicks hängen an), ⇧-Klick sendet sofort an der
  aktuellen Stelle. „＋ aus Text" speichert den Text im Feld als neuen Baustein, × am Chip entfernt ihn. Die Liste liegt
  auf dem NAS (`review/_bausteine.json`) und gilt auf beiden Macs; ohne Datei die Standardliste (nach Häufigkeit der
  Wurst-&-Liebe-Kommentare vom 18.09.: Andere Cam, Shot tauschen, Shot raus, Erst ab hier, Länger zeigen, O-Ton fehlt,
  Grafik runter, Stabilisieren, Ranzoomen, Heller, Zu dunkel, Musik wechseln, Pop-SFX raus, Satz raus, Wide Shot, Pause raus,
  Lauter, Totale, Slow-Mo, UT flackert, 90° gedreht, Retusche, Zu kurz, Bestätigt?).
- **Review abschließen** sperrt die Version für neue Kommentare und stellt sie auf „bei Claude" — dann im Chat
  „fertig" oder „Review: Kunde/Projekt" sagen. **Freigeben**, wenn das Video fertig ist.
- Ab V2 zeigt „Seit V1 geändert" jede Antwort von Claude mit Sprung zur neuen Stelle; dort abhaken („erledigt") oder auf
  Rückfragen antworten.
- Beim ersten Öffnen fragt die Seite nach dem Namen (David / Jan / Sergio / frei); er steht an jedem Kommentar.
- Die Review-Kopie hat höchstens 1920 px lange Kante (4K ruckelt im Browser); Frames und Timecodes entsprechen dem
  Original-Export 1:1.

## Tasten

| Taste | Wirkung |
|---|---|
| Leertaste | Play / Pause |
| ← / → | ein Frame zurück / vor (mit ⇧ eine Sekunde) |
| ↑ / ↓ | vorheriges / nächstes Video im Projekt |
| Home / End | Anfang / Ende |
| I / O | Bereich: In / Out auf den aktuellen Frame |
| C | Kommentarfeld fokussieren (pausiert) |
| ⌘↩ / Strg+↩ | Kommentar senden |
| Esc | Kommentarfeld verlassen |
| M / F | stumm / Vollbild |
| 1–9 | Version wechseln |

## Für Claude

Ablauf und Befehle: `WORKFLOW-Review.md`. Kurz: `hinzufuegen` (Version ablegen), `kommentare` (holen, Export in
`Material/Feedback/`), `umsetzung`/`antworten` (Status und Antworten), `status`, `entfernen` (Papierkorb).

## Tests

```bash
tools/autocut/venv/bin/python -m pytest tools/review/tests -q
```
