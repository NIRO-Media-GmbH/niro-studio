# Design: Foto-Funktion (ARW-RAW-Pipeline)

Datum: 2026-08-03 · Status: zur Review

## Ziel & Kontext

Fünfte Studio-Funktion neben Interview-Pipeline, Footage-Sortierer, Schnittplan
und Motion: RAW-Fotos (zunächst Sony ARW) Ende-zu-Ende bearbeiten —
Sichtung/Culling → Look-Aufbau → Batch-Entwicklung → Export. Anlass sind die
Autofotos des Aufbereiters BumbleClean; die Funktion ist aber kundenneutral
aufgebaut (Looks pro Kunde austauschbar).

Arbeitsmodell: Ende-zu-Ende durch Claude. David gibt Feedback in Runden wie
beim Videoschnitt (Übersichts-Grids statt Einzeldateien; Anweisungen im Chat
wie „alle etwas wärmer", „Bild 12 heller"). Look-Vorgabe über Referenzbilder,
die David bereitstellt.

## Entscheidungen (geklärt 2026-08-03)

| Frage | Entscheidung |
|---|---|
| Anwendungsfall | Jetzt Auto-/Detailingfotos (BumbleClean), perspektivisch alle Foto-Typen |
| Arbeitsteilung | Ende-zu-Ende durch Claude, Feedback-Runden mit David |
| Look-Quelle | Referenzbilder (Nachbau durch Claude, Freigabe durch David) |
| RAW-Engine | RawTherapee-CLI; Fallback ART (gleiches Profilformat); Notbetrieb sips |

Begründung RawTherapee: Profi-Demosaic und Highlight-Rekonstruktion, und die
Entwicklungsprofile (`.pp3`) sind Klartext — Claude kann jeden Parameter gezielt
setzen, das Ergebnis visuell prüfen und präzise nachjustieren. darktable wurde
verworfen (Modul-Parameter binär kodiert → nur grobe Style-Anwendung möglich),
reine Bordmittel ebenfalls (sips backt das RAW mit Apple-Standard, kaum
Lichter-/Schatten-Spielraum).

## Architektur

Trigger im Chat: `„Foto: <Kunde>/<Projekt>[/<Charge>]"` → Claude liest
`tools/photo/WORKFLOW-Foto.md` und folgt ihm (Muster der vier bestehenden
Funktionen; Eintrag in CLAUDE.md-Triggertabelle gehört zum Erstausbau).

    tools/photo/
    ├── WORKFLOW-Foto.md      Betriebsanleitung für Claude
    ├── looks/<kunde>/        Kunden-Looks: <name>.pp3 + NOTES.md (Herkunft/Referenz)
    └── scripts/              kleine, einzeln nutzbare Helfer (s. Komponenten)

    projects/<Kunde>/<Projekt>/<Charge>/
    ├── Material/Fotos/Referenz/   Referenzbilder für den Look
    ├── Ergebnisse/Fotos/          fertige Bilder + Auswahl-Übersichten
    └── _intern/photo/             Arbeitsprofile, Previews, Culling-Daten, Logs

Die ARW-Originale bleiben auf SSD/NAS (Konvention wie Drehmaterial) und werden
ausschließlich lesend verwendet — nie verändert, verschoben oder gelöscht. Der
Quellpfad wird beim Trigger genannt und im Chargen-Ordner als Manifest
(`_intern/photo/quelle.md`) festgehalten. Alle Entwicklung läuft über
Profil-Dateien und erzeugt neue Ausgabedateien.

## Ablauf pro Auftrag

1. **Sichtung/Culling** — Eingebettete JPEG-Previews aller ARWs extrahieren
   (exiftool, schnell, ohne RAW-Entwicklung), Schärfe-Metrik und
   Belichtungs-Clipping messen, Near-Duplicates gruppieren. Claude sichtet und
   legt David eine Auswahl als Kontaktabzug-Übersicht vor; David bestätigt oder
   ändert. Überspringbar, wenn die Auswahl schon feststeht.
2. **Look-Aufbau** (einmal pro Kunde, danach wiederverwendt) — Referenzbilder
   analysieren, Look auf 2–3 Testbildern nachbauen: entwickeln → Ergebnis
   ansehen → `.pp3` anpassen, bis es der Referenz entspricht. David bekommt
   Referenz-vs.-Ergebnis-Vergleichsbilder; nach Freigabe wird der Look unter
   `tools/photo/looks/<kunde>/` gespeichert und committet.
3. **Batch-Entwicklung** — Look-Profil auf die gesamte Auswahl anwenden. Das
   Profil setzt alle Look-Parameter fest; pro Bild variieren nur
   Belichtungskorrektur und Weißabgleich (zunächst RawTherapee-Automatik,
   Ausreißer zieht Claude nach Stichproben-Sichtung manuell nach).
4. **Export + Abgabe** — Volle Auflösung plus Web-/Social-Formate nach Bedarf,
   sRGB, zielgerechte Ausgabeschärfung, EXIF bereinigt (Copyright rein, GPS
   raus). Ablage in `Ergebnisse/Fotos/`, Eintrag ins `Protokoll.md` der Charge
   (Protokoll-Pflicht gilt wie bei allen Funktionen).

## Komponenten

- **WORKFLOW-Foto.md** — beschreibt die vier Schritte, Feedback-Schleifen,
  Ablagepfade, Namenskonventionen; Stil und Detailgrad wie die bestehenden
  Workflow-Dateien in `tools/transcribe/`.
- **looks/** — je Kunde beliebig viele benannte Looks; `NOTES.md` hält fest,
  aus welchen Referenzen der Look entstand und was ihn ausmacht.
- **scripts/** — Previews extrahieren, Schärfe-/Clipping-Report,
  Kontaktabzug/Vergleichs-Grid bauen, Batch-Entwicklung ausführen,
  Web-/Social-Export. Jeder Helfer einzeln aufrufbar und verständlich;
  Implementierungssprache (Python-venv analog transcribe vs. Shell+ImageMagick)
  entscheidet der Umsetzungsplan.
- **Abhängigkeiten** — RawTherapee (neu, `brew install rawtherapee`), exiftool,
  ImageMagick, sips (alle vorhanden).

## Fehlerbehandlung

- Originale sind tabu: Scripts öffnen ARWs nur lesend; Ausgaben landen immer in
  `_intern/photo/` oder `Ergebnisse/Fotos/`.
- Einzelbild-Fehler (defekte Datei, Konverter-Absturz) werden geloggt, der
  Batch läuft weiter; am Ende gibt es einen Fehlbild-Bericht statt stillem
  Verschlucken.
- Läuft die RawTherapee-CLI auf macOS nicht sauber (bekanntes Cask-Risiko),
  wird auf ART umgestellt — gleiches Klartext-Profilformat, Architektur
  unverändert. Für schnelle Previews unabhängig davon: sips.
- Farbverbindlichkeit: Ausgabe immer sRGB mit eingebettetem Profil; finale
  Farbabnahme macht David auf kalibriertem Schirm (Claude beurteilt Look und
  Konsistenz, nicht absolute Monitor-Farbtreue).

## Bewusst außerhalb des Scopes

- Beauty-/Pixel-Retusche, Objekte entfernen, Composings → bleibt
  Photoshop-Handarbeit.
- Text-/Grafik-Overlays auf Fotos → Motion-/Design-Terrain (dort gelten dann
  m/w/d- und Nur-Website-Infos-Regeln).
- Topaz Photo AI als Entrausch-/Upscale-Stufe: erst nach dem Piloten prüfen
  (Frage: skriptbare CLI vorhanden?), kein Bestandteil des Erstausbaus.
- Erstausbau wird nur mit Sony ARW getestet; die Engine liest weitere
  RAW-Formate, sodass nichts verbaut ist.

## Test & Abnahme

- **Setup-Verifikation:** ein echtes ARW von David durch die komplette Kette
  (Install → Preview → Entwicklung mit Testprofil → Export) mit Sichtprüfung,
  bevor irgendetwas weiteres gebaut wird. Dabei RT-CLI-Pfad/Version im
  Cask-Bundle verifizieren.
- **Pilot:** die BumbleClean-Autofotos komplett durch alle vier Schritte,
  inklusive Look-Aufbau aus Davids Referenzbildern.
- **Erfolgskriterium:** David würde die Ergebnisse ohne eigene
  Lightroom-Nacharbeit an den Kunden geben.
- **Beim Piloten festzulegen:** benötigte Social-/Web-Zielformate (4:5, 1:1,
  9:16, Website-Breiten) — wird als Export-Preset im Look-Ordner hinterlegt.
