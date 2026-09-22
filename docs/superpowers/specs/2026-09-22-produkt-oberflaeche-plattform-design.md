# Produkt-Design: Oberfläche, Plattformen, Preisrechner, Integrationen (Design-Spec)

Datum: 2026-09-22 · Status: **Entwurf zur Entscheidung, nichts umgesetzt** · Ergänzt den Plan
`2026-09-22-autocut-standalone-produkt-design.md` (Geschäftsmodell, Architektur-Grundsatz, Kosten). Diese Spec
beantwortet die Produktfragen vom 22.09.: Bedienung, mehrere Schnittprogramme, Review-Schleife im Produkt, Installer für
Mac und Windows, Login, Projektanlage, angebundene Dienste, Preisrechner mit Vorkalkulation, Guthaben und Abo, Sprachen,
Stabilität. Die Rechercheberichte vom 22.09. zu NLE-Schnittstellen, Wettbewerb und Bausteinen sind eingearbeitet (Abschnitte 2.4,
10 und 11), ebenso die Entscheidungen des Users vom Abend des 22.09. (Abschnitt 13).

## 0. Entscheidungen in Kürze

| Frage | Entscheidung | Warum |
|---|---|---|
| Nur Resolve oder alle Schnittprogramme? | **NLE-neutraler Kern** mit eigenem Schnittmodell und eigenem Vorschau-Render (ffmpeg); Resolve als Stufe 1 „live", Premiere und Final Cut als Stufe 2 „per Datei" (eigene Writer für FCP7-XML und FCPXML 1.13/1.14, OTIO als Zweitdatei), Avid Stufe 3 (OTIO ab Media Composer 2025.6), CapCut Stufe 4 (gerenderte Lieferung MP4 + SRT + Alpha-Grafiken; es gibt keinen offiziellen Importweg) | Die Urteile (Schnittplan, Cutlist, B-Roll, Ton) sind programmunabhängig; nur das Konformieren ist je NLE anders. Der eigene Vorschau-Render macht Review-Schleife und Kantenprüfung für alle NLEs gleich |
| Bedienung: Chat, Häkchen oder Erkennung? | **Erkennung schlägt vor, Häkchen bestätigen, ein Freitextfeld je Schritt für Regieanweisungen.** Kein Chat als Hauptsteuerung | Häkchen sind zugleich die Preisgrundlage; Chat macht Kosten und Ergebnis unvorhersehbar |
| Fremddienste (ElevenLabs, Higgsfield, …) | **NIRO stellt sie bereit und rechnet sie in Credits ab.** Eigene Keys nur als Enterprise-Option. Ausnahme: Musikbibliotheken (Artlist, Envato) — Lizenz gehört dem Kunden, also eigenes Konto verbinden oder eigene Dateien | Kein Onboarding-Hindernis, keine Keys im Client, Marge bleibt, Qualität steuerbar. Entschieden 22.09. |
| Preis je Video | **Verbindlicher Kostenvoranschlag vor jedem Lauf** in Credits, aus messbaren Größen (Interview-Minuten, Footage-Stunden, Ziel-Länge, Module, Review-Runden) | Marge schwankt nicht, Kunde weiß vorher, was es kostet |
| Guthaben oder Abo? | **Beides:** Prepaid-Credits (verfallen nicht) und Abo mit monatlichen Credits zum günstigeren Kurs plus Übertrag | Niedrige Einstiegshürde und Bindung zugleich |
| Review | **Review bleibt lokal** (Entscheidung 22.09.): Die App führt den Review-Server wie heute NIRO Review, legt Versionen sauber unter `<Projekt>/Review/<Video>/V<n>/` ab, Kommentare liegen daneben; Knopf „Änderungen umsetzen" erzeugt V+1 mit Antworten je Kommentar; Endkunden-Runden über den Link im Netz der Agentur oder Export nach Dropbox Replay / Frame.io | Kein Medium verlässt den Rechner; das ist heute schon der Kern eurer Arbeitsweise |
| Installer | **Ein Installer je OS** (.dmg signiert/notarisiert, .msi/.exe signiert), alles gebündelt (Python, ffmpeg, Modelle bei Bedarf), Auto-Update, Server erzwingt Mindestversion | „Runterladen, einloggen, loslegen" |
| Plattformen | **macOS (Apple Silicon) zuerst, Windows im zweiten Schritt** mit denselben Kernen; Apple-Vision-Teile werden durch ONNX-Modelle ersetzt, damit beide OS gleich rechnen | Windows-Anteil bei Resolve- und Premiere-Nutzern ist groß |
| Sprachen | **Videos in jeder Sprache** (Transkription mit Spracherkennung, Ausgabe-Sprache wählbar), **UI Englisch als Standard**, Deutsch ab Tag 1, weitere per i18n | Weltweiter Markt |
| B-Roll | **Automatisch als Standard** aus dem gesamten indexierten Material mit Telemetrie- und Setup-Regeln (Stufe 3 reaktiviert); Eingrenzung optional per Häkchen an Ordnern/Clips oder per Auswahl-Timeline (heutige 3a bleibt als Rückfall) | Die Zutaten (Brennweite, Haltung, Bewegung, Wackeln, Schärfe, Setup-Hash) sind seit 21.09. da; Stufe 3 ist damit aber noch nicht neu belegt → im Durchstich am Eval-Korpus prüfen |
| Grafiken | **Direkt im MVP, ohne Vorlagenbibliothek für Kunden:** eigene Dateien immer; generierte Bauchbinden, Titel, Endcards, Untertitel-Stil aus dem Brand-Kit, wie heute in der Animation-Funktion | Intern eine Komponentenbasis für Konsistenz und Kosten, nach außen nur Brand-Kit plus Freitext |
| Concierge-Pilot | **Noch nicht** | Entscheidung 22.09.; bleibt Option |
| Struktur | Produktlinie der **NIRO Productions**, eigenes CI für das Produkt | Entscheidung 22.09. |

## 1. Ziele und Randbedingungen (aus dem Gespräch vom 22.09.)

- Sehr flexibel: Kunden schneiden in Resolve, Premiere, Final Cut oder CapCut.
- Review-Schleife wie bei NIRO: Kommentare → Bestätigen → KI setzt um → neue Version.
- Installer mit allen Paketen, Login beim Start, Projekt über Dateipfad, Projektart wählbar oder erkannt.
- Fremddienste bereitstellen oder verbinden lassen; Animationen wählbar.
- Preis je Video vorberechnet und variabel nach Aufwand, Guthaben aufladen, Abo mit Rabatt.
- Stabil bei vielen Nutzern, Mac und Windows, weltweit, sprachunabhängig, UI Englisch mit Umschaltung.
- Weiterhin gültig aus dem Plan: Rohmaterial bleibt beim Kunden, Prompts und Regeln bleiben im Server, kein Claude Code
  beim Kunden, KI über NIROs API-Konto.

## 2. Architektur: ein Kern, viele Schnittprogramme

### 2.1 Das Schnittmodell (Edit Decision Model)

Alles, was die Pipeline entscheidet, landet in **einem** programmunabhängigen Schnittmodell (JSON, verlustfrei nach
OpenTimelineIO abbildbar): Spuren, Clips mit Quelle und In/Out, Pegel je Clip, Geschwindigkeit, Marker, deaktivierte
Clips, Spurnamen, Grafik- und Musik-Ebenen, Untertitel, Bildrate und Timecode-Format. Die heutigen Dateien
`cutlist.json`, `timeline.json`, `broll_plan.json`, `ton.json` sind Vorstufen davon.

### 2.2 Eigener Vorschau-Render

Die App rendert aus dem Schnittmodell und den **Originalmedien lokal** mit ffmpeg eine Vorschau (≤ 1080p, H.264):
Sprecher-Spuren, B-Roll, Pegel, Musik, Grafik-Dateien mit Alpha, Untertitel eingebrannt oder als Spur. Darauf laufen
Kantenprüfung und Review — **unabhängig davon, welches Schnittprogramm der Kunde benutzt** und ohne dass es geöffnet
sein muss. Grading, Stabilisierung und der finale Master bleiben Sache des NLE.

### 2.3 Adapter je Schnittprogramm

| Stufe | Programm | Weg | Was ankommt | Was fehlt / Ersatz |
|---|---|---|---|---|
| 1 „live" | DaVinci Resolve Studio 21.1+ (Mac/Win) | Scripting-API wie heute: Bins, Timelines, Spuren, Pegel, Speed, Marker, Render-Queue; Auswahl-Timeline direkt lesen | Alles inkl. Feinschnitt, Grading-Baum, Stabilisierung, Master-Render | — (Studio nötig; Free hat seit 21.1 kein Scripting) |
| 2 „Datei" | Adobe Premiere Pro 26.x | **Eigener FCP7-XML-Writer** (xmeml v5; heute schon als „Premiere-Probecutter" im Einsatz) plus OTIO als Zweitdatei (Import/Export seit Premiere 26.0, nur Grundinformationen: Cut, Spuren, Spurnamen, lineare Speed, Marker, TC); Auswahl-Timeline per OTIO- oder XML-Export zurücklesen | Cutlist, zwei Kameraspuren, B-Roll-Spur, Pegel je Clip (Filter `audiolevels`), konstante Speed (`timeremap`), Marker (ohne Farben), deaktivierte Clips (`enabled`), Spurnamen, Multiclip | Variable Speed, Grading, Stabilisierung → Vorschau-Render, Master im NLE. Später UXP-Plugin (offiziell seit 25.6, Verteilung als `.ccx` oder Marketplace): Clips einfügen, Pegel, Marker, deaktivieren, Export über Media Encoder — **Speed setzen geht per UXP nicht**, Timeline-Import per API ist angekündigt |
| 2 „Datei" | Final Cut Pro 12.x | **Eigener FCPXML-1.13/1.14-Writer** (`adjust-volume` in dB, `timeMap`, `conform-rate`, `enabled`, `marker`, Rollen, Lanes, `mc-clip`); Übergabe per Datei oder AppleScript `open` (Bibliotheks-Dialog bleibt); Rücklesen aus FCPXML mit eigenem Parser (Lanes und Rollen → Spuren) | wie Premiere, plus variable Speed | Keine Spuren, nur Lanes und Rollen; keine Automations-API, später Workflow Extension (Drag-and-drop von FCPXML) |
| 3 | Avid Media Composer ≥ 2025.6 | OTIO-Datei (Import seit 2025.6; 2026.8 bringt API/SDK mit Sequenz-Erzeugung), AAF nur als Rückfall | Cutlist, Spuren, Marker | Pegel/Speed als Nacharbeitsliste; Enterprise-Fall auf Nachfrage |
| 4 | CapCut Desktop | **Kein offizieller Importweg** (Hersteller-Hilfe 01/2026: keine Projektdateien von Drittsoftware). Lieferung als gerendertes MP4 + SRT + Alpha-Grafiken zum Weiterbauen | Fertiges Video in Vorschauqualität, Untertitel, Grafiken | Draft-Dateien schreiben ist Grauzone (ToS verbieten Automatisierung) und bricht mit jedem Release → höchstens experimentell, nie versprechen |
| alle | Ohne NLE | MP4 + SRT + Kapitelmarken aus dem Vorschau-Render | Fertiges Video in Vorschauqualität | Master nur über NLE oder Zusatz-Render (ProRes) |

Rücklesen der B-Roll-Auswahl: Der Cutter legt in seinem NLE eine Auswahl-Timeline an und exportiert sie (Resolve: direkt
per API; Premiere: OTIO oder FCP7-XML; FCP: FCPXML mit eigenem Parser, weil Lanes und Rollen erst zu Spuren werden
müssen; Avid: OTIO); die Stufe 3a arbeitet dann wie heute.

**OpenTimelineIO als Hausformat, aber eigene Writer.** OTIO 0.18.1 (11/2025, Python 3.9–3.13) taugt als internes
Austauschformat für Archiv, Tests und den Import in Resolve, Premiere und Avid. Die XML-Adapter (`otio-fcp-adapter`,
`otio-fcpx-xml-adapter`, `otio-cmx3600-adapter`) haben aber seit Juli 2023 kein Release und transportieren weder
Clip-Pegel noch Speed noch deaktivierte Clips; der FCPXML-Adapter schreibt Version 1.8 von 2018. Deshalb schreibt der
Kern FCP7-XML und FCPXML 1.13/1.14 selbst; nur `otio-aaf-adapter` 2.0.0 (11/2025) wird genutzt.

**Bildraten und Timecode weltweit:** 23,976 / 24 / 25 / 29,97 / 30 / 50 / 59,94 / 60 fps, Drop-Frame-Timecode (NTSC),
variable Bildraten von Smartphones werden vor der Analyse auf konstante Bildrate konformiert. FCP7-XML kodiert 29,97 als
`timebase 30 + ntsc TRUE`, FCPXML als `1001/30000s`, OTIO als exakte Rationalzahl — der Kern rechnet nur in
Rationalzahlen, nie in Fließkomma-fps. Die heutige Festlegung auf 25 fps entfällt.

**Probe-Roundtrips vor dem Bau** (Unbekannte aus der Recherche): Premiere-Import von `audiolevels`, konstantem
`timeremap`, `enabled`, Spurnamen (`MZ.TrackName`), Stereo/Mono-Kanalzuordnung und 23,976 über das `ntsc`-Flag aus
FCP7-XML; Premiere-OTIO-Import (kommen `enabled` und Pegel an, ab welcher Version genau); FCPXML-Writer gegen DTD 1.13/1.14
mit `adjust-volume`, `timeMap`, Lanes, Rollen und dem Bibliotheks-Dialog beim `open`; Resolve ignoriert fremde
OTIO-Speed-Effekte (Speed nur per API oder XML); Avid-OTIO-Import (Marker, Speed, Pegel undokumentiert); Medienpfade
und Relink bei unterschiedlichen NAS-Mounts.

Was nur in Resolve geht, und der Ersatz anderswo: Grading und LUTs → ffmpeg `lut3d` im Vorschau-Render; Stabilisierung
und Optical-Flow-Retime → ffmpeg `vidstab` und `minterpolate` als gebackene Zwischenclips oder Hinweis im Schnittplan;
Render-Queue → Premiere über Media Encoder per UXP, FCP und Avid manuell; Gesichts- und Kantenprüfung → eigener
Frame-Export per ffmpeg.

### 2.4 Befunde der NLE-Recherche (22.09.2026)

Kurzmatrix aus dem Recherchebericht. N = nativ per API steuerbar · D = per Datei-Import abbildbar · T = teilweise oder
unsicher · X = nicht möglich.

| Merkmal | Resolve | Premiere (UXP / Datei) | Final Cut (FCPXML) | Avid (OTIO/AAF) | CapCut |
|---|---|---|---|---|---|
| Clips, Quell-In/Out, mehrere Spuren | N | N / D | D | D, ab 2026.8 auch N | X |
| Zwei Kameraspuren synchron | N | N / D | D | D | X |
| B-Roll-Spur mit Lücken | N | N / D | D (Lanes) | D | X |
| Spurnamen | N | N (26.3) / D | X (Rollen als Ersatz) | T | X |
| Pegel je Clip | N | N (Volume › Level) / D (`audiolevels`) | D (`adjust-volume`) | T | X |
| Speed konstant | N | **X per UXP** / D (`timeremap`, OTIO) | D (`timeMap`) | T | X |
| Speed variabel | D | X | D | X | X |
| Marker | N | N / D | D (ohne Farben) | D | X |
| Deaktivierte Clips | N | N / D | D (`enabled="0"`) | T | X |
| Render starten | N | N (Media Encoder) | X (Share manuell) | T | X |
| Timeline zurücklesen | N | D (OTIO/XML) | D (FCPXML, eigener Parser) | D | X |

Stand der Programme: Resolve 21.1 (Scripting-README 21.0.4 vom 24.07.2026: Import AAF/EDL/XML/FCPXML/DRT/ADL/OTIO,
Export OTIO/FCP7-XML/FCPXML 1.8–1.10/AAF/EDL); Premiere 26.5.1 (FCP7-XML-Import ja, `.fcpxml` nein, OTIO seit 26.0,
UXP offiziell seit 25.6); Final Cut 12.3 (FCPXML 1.14 seit 12.0); Avid 2026.8 (OTIO-Import seit 2025.6); CapCut ohne
Importweg laut Hersteller-Hilfe vom 21.01.2026. Bildraten: FCP7-XML kodiert 23,976 als `timebase 24` + `ntsc TRUE`,
FCPXML als `1001/24000s`; die OTIO-Kernbibliothek hat offene Rundungsfehler bei 23,976/29,97 (Issues #476, #830, #876),
darum rechnet der Kern selbst in Rationalzahlen. Quellen: OTIO-Releases und Adapter auf GitHub/PyPI, Resolve-README
(extremraym.com), Adobe-Developer-Doku zu UXP (SequenceEditor, AudioClipTrackItem, ProjectConverter, EncoderManager),
Adobe-Community-Ankündigung zu OTIO, Apple-Release-Notes und FCPXML-DTDs (CommandPost), CapCut-Hilfe und ToS,
Avid-Pressemeldungen zu 2025.6 und 2026.8.

## 3. Oberfläche

### 3.1 Start und Login

Erster Start: Einladungscode + E-Mail + Passwort (Argon2), optional Passkey/TOTP; Gerät wird registriert (Schlüsselpaar in
Keychain bzw. Windows Credential Store), max. Geräte je Sitz laut Tarif. Danach: Login-Screen mit „angemeldet bleiben"
(Refresh-Token rotierend), Organisation wählen, falls mehrere. Ohne Server: nur Einstellungen sichtbar.

### 3.2 Startseite

Projektkarten (Status, letzter Schritt, nächste Aktion), Guthaben und Verbrauch des Monats, Hinweise (Resolve läuft /
nicht erkannt, Update verfügbar), Schnellstart „Neues Projekt".

### 3.3 Neues Projekt (Assistent, vier Schritte)

1. **Ordner wählen** — Dateipfad-Dialog (NAS/SSD/lokal), Projektname, Kunde (für Brand-Kit und Review-Ablage). Die App
   schreibt nur in einen eigenen Unterordner `_studio/` und nie in das Material.
2. **Erkennung** — läuft lokal: Kameras und Rollen (Dateinamen-Präfixe, Metadaten, Sony-rtmd falls vorhanden),
   Interview-Clips mit Dauer und **erkannter Sprache**, B-Roll-Anzahl und -Dauer, Bildraten, vorhandene Proxies,
   Musik- und Grafikdateien, installierte Schnittprogramme (Resolve läuft? Premiere/FCP vorhanden?). Ergebnis als
   **bestätigbare Karten**: „2 Interviews, 2 Kameras, 58 min · Deutsch 98 %", „412 B-Roll-Clips, 3 h 12 min · 25/50 fps",
   „Ziel: DaVinci Resolve Studio 21.1 erkannt". Der Nutzer korrigiert per Klick (Ordner als B-Roll markieren, Kamerarolle
   tauschen, NLE wechseln).
3. **Auftrag** — kurzes strukturiertes Formular, vorbelegt aus der Erkennung: Videoart (Imagefilm, Recruiting,
   Erklärvideo, Reel/Short, Aftermovie, Testimonial, Talk/Podcast), Zielformate (16:9, 9:16, 1:1), Ziel-Länge, Anzahl
   Videos, Konzept/Skript hochladen (PDF, DOCX, Text) oder „ohne Konzept" (Aussagen-Pool-Modus), Ausgabesprache,
   **Module als Häkchen**: B-Roll (automatisch / eingegrenzt auf markierte Ordner oder Auswahl-Timeline / keine), Musik
   (eigene Dateien / Bibliothek verbinden), Grafik und Animationen (generiert aus dem Brand-Kit oder eigene Dateien),
   Untertitel, Grading (nur Resolve), Review lokal. Dazu
   **ein Freitextfeld „Regieanweisungen"** (z. B. „Hook mit der Geschäftsführerin, ruhiger Ton, keine Musik unter
   O-Tönen").
4. **Kostenvoranschlag** — aufgeschlüsselt in Credits und Währung (Abschnitt 4), Guthaben danach, Hinweis „verbindlich,
   wird nicht überschritten", Knopf **Start**. Reicht das Guthaben nicht: Aufladen oder Abo direkt hier.

### 3.4 Projektansicht

Linke Leiste = Pipeline: Material → Transkript & Aussagen → Schnittplan → Rohschnitt → B-Roll → Ton & Musik → Grafik →
Prüfung → Review → Export. Je Schritt: Status, Ergebnis, Kosten des Schritts, Aktionen („Neu berechnen", „Anweisung
geben", „Überspringen"). Fortschritt live über WebSocket mit Teilschritten („Kontaktbögen 240/412").

- **Transkript & Aussagen:** Transkripte je Sprecher, Aussagen-Pool mit Suche und Filter (Thema, Sprecher, Länge),
  Anhören per Klick (lokales Audio).
- **Schnittplan-Editor:** eine Zeile je Aussage (Beat, Sprecher, Zitat, Quelle, Bild-Hinweis, Sperre), Reihenfolge per
  Ziehen, „Alternative vorschlagen", Ziel-Länge live, PDF-Export im heutigen Cutter-Format; **Freigabe** → Rohschnitt.
- **Vorschau-Player:** App-Render mit Zeitleiste (Beats, B-Roll, Musik, Grafik), Frame-genaues Scrubbing, Wellenform.
- **B-Roll:** Standard automatisch aus dem gesamten indexierten Material mit den Telemetrie- und Setup-Regeln;
  Eingrenzung optional per Häkchen an Ordnern und Clips oder per Auswahl-Timeline; Kontaktbögen je Beat mit Zuordnung
  und Begründung, Warnungen (lesbare Bildschirme → Blur-Marker).
- **Ton & Musik:** Pegel je Clip, Musik-Plan (eigene WAV), Ducking-Vorschau.
- **Grafik:** Bauchbinden, Titel, Endcards und Untertitel-Stil werden aus dem Brand-Kit generiert, ohne
  Vorlagenauswahl, Wünsche per Freitext; eigene ProRes-4444-Dateien einsetzen; Grafik-Review am echten Bild.
- **Prüfung:** Kantenprüfung mit Befund-Bild und Ton-Ausschnitt, Ein-Klick-Korrektur, erneuter Lauf.
- **Review:** Abschnitt 5.
- **Export:** „In Resolve bauen" (live), „XML für Premiere", „FCPXML für Final Cut", „XML für CapCut", „MP4 + SRT";
  „Master rendern" (Resolve-Render-Queue oder App-Render ProRes/H.264).

### 3.5 Konto und Verwaltung

Konto: Guthaben, Abo, Rechnungen (Stripe-Portal), Team und Sitze, Geräte, Brand-Kits (Logo, Farben, Schriften je
Endkunde), Integrationen (Musikbibliothek verbinden; Enterprise: eigene Keys), Sprache, Updates, Datenschutz
(Löschfristen, was in die Cloud geht).

Admin (NIRO): Organisationen anlegen und freischalten, Kontingente, Kosten je Kunde je Schritt (Soll/Ist), Job-Logs,
Versionen sperren, Feature-Flags, Preisliste und Credit-Formeln pflegen.

### 3.6 Gestaltung

Dunkles Studio-Thema und helles Thema, eine Schrift, ruhige Typografie, klare Statusfarben, keine Spielereien; die
Zeitleiste ist das zentrale Element. Barrierefreiheit: Tastaturbedienung, Kontraste, Screenreader-Labels. Sprache im
UI: Englisch Standard, Deutsch, danach Spanisch, Französisch, Portugiesisch, Italienisch, Niederländisch, Japanisch,
Koreanisch, Chinesisch nach Nachfrage; Datums-, Zahl- und Timecode-Formate je Region.

## 4. Preisrechner: Credits, Vorkalkulation, Guthaben, Abo

### 4.1 Grundeinheit

**1 Credit = 0,10 € nominal.** Kunden sehen Credits und den Gegenwert in ihrer Währung, nie Token oder Modelle. Jeder
Pipeline-Schritt hat eine Formel aus messbaren Eingaben; die Summe ist der Kostenvoranschlag und **verbindlich**. NIRO
trägt die Schwankung — die Pipeline-Schritte laufen mit Budgets und Zug-Grenzen, daher ist die Schwankung klein. Der
Server protokolliert Soll gegen Ist je Schritt; die Formeln werden monatlich nachkalibriert.

### 4.2 Formel (Startwerte, Marge ≥ 65 % nach den Kostenhebeln aus dem Plan-Nachtrag)

| Position | Bemessung | Credits | Beispiel |
|---|---|---|---|
| Transkription mit Sprechertrennung | je Minute Interview | 0,3 | 58 min = 17 |
| Material-Indexierung (B-Roll) | je Footage-Stunde, einmal je Dreh, gecacht | 60 | 3,2 h = 192 |
| Aussagen-Pool und Schnittplan | je Video, Staffel nach Interview-Minuten (≤ 60 / ≤ 120 / mehr) | 120 / 180 / 250 | 120 |
| Rohschnitt (Cut) | je Video, Staffel nach Ziel-Länge (≤ 90 s / ≤ 3 min / ≤ 8 min / ≤ 15 min) | 120 / 200 / 320 / 480 | 320 |
| B-Roll-Zuordnung und Einsetzen | je Video, Staffel nach B-Roll-Anzahl (≤ 150 / ≤ 500 / mehr) | 80 / 140 / 220 | 140 |
| Ton (Pegel) und Musik-Plan | je Video | 60 | 60 |
| Grafiken (generiert) | je gerenderter Grafik | 15 | 6 × 15 = 90 |
| Kantenprüfung | inklusive im Cut | 0 | 0 |
| Review-Runden | 2 inklusive, danach je Runde | 50 | 0 |
| Zweites Format (z. B. 9:16 aus 16:9) | je Video | 40 % des Cuts | 128 |
| Generative Dienste (Bild/Video, Sprachsynthese) | Durchreichung der Anbieterkosten × 1,5, einzeln ausgewiesen | variabel | — |
| **Summe Beispiel** (3,2 h Footage, 58 min Interviews, ein 4-Minuten-Film 16:9 + 9:16, 6 Grafiken) | | | **1.067 Credits ≈ 107 €** |

Zweites Video aus demselben Dreh: ohne Transkription und Indexierung ≈ 640 Credits. Ein Reel ohne B-Roll: ≈ 300 Credits.
Die Formel bildet genau die Aufwandstreiber ab, die im Gespräch genannt wurden: 1.000 B-Roll-Shots und 20 Interviews
kosten sichtbar mehr als 20 Interviews ohne B-Roll; Animationen kommen je Stück dazu.

### 4.3 Kaufen

| Weg | Angebot | Kurs |
|---|---|---|
| Prepaid-Pakete (verfallen nicht) | 500 Credits 49 € · 2.000 Credits 179 € · 5.000 Credits 399 € · 15.000 Credits 1.049 € | 0,098 → 0,070 €/Credit |
| Abo Starter | 290 €/Monat, 3.500 Credits, 1 Sitz, 2 Geräte | 0,083 €/Credit |
| Abo Studio | 590 €/Monat, 8.000 Credits, 3 Sitze, Brand-Kits, Übertrag bis 2 Monate | 0,074 €/Credit |
| Abo Agency | 1.190 €/Monat, 18.000 Credits, 8 Sitze, Grading-Profile, Priorität in der Warteschlange | 0,066 €/Credit |
| Jahreszahlung | −15 % | |
| Enterprise | Rechnung, Volumen, EU-Inferenz, SSO, AVV nach Kundenvorlage | Verhandlung |

Abo-Credits werden zuerst verbraucht, dann Prepaid. Übertrag begrenzt, damit kein Guthaben-Berg entsteht. Alles über
Stripe Billing (Abos, Einmalzahlungen, Steuer, Rechnungen mit USt-ID, SEPA, Kartenzahlung, Kundenportal). Preise in
EUR und USD, später weitere Währungen über Stripe.

### 4.4 Schutz der Marge

Kostenobergrenzen je Schritt (Token-Budget, Zug-Grenze), Batch-Index, Cache je Dreh, Vorfilter, Modellwahl je Schritt
(Plan-Nachtrag). Meldet ein Schritt Budgetüberschreitung, wird er mit knapperem Kontext wiederholt, nicht teurer.
Wöchentlicher Bericht: Ist-Kosten je Credit, Marge je Kunde, Ausreißer.

## 5. Review-Modul (lokal, Entscheidung 22.09.)

Aus NIRO Review (3.751 Zeilen, lokal, ohne Login) wird das Review-Modul der App — **lokal, wie heute**:

- **Ablage:** Die App legt je Video einen Review-Ordner an, `<Projekt>/Review/<Video>/V<n>/`, mit Vorschau-Render
  (≤ 1080p, H.264), Kommentaren als JSON und Bericht. Versionen werden nie überschrieben. Nichts davon geht in die
  Cloud; der Server kennt nur die Kommentartexte, wenn „Änderungen umsetzen" gedrückt wird.
- **Server:** Der Review-Server läuft in der App (heute LaunchAgent auf Port 4711) und ist im Netz der Agentur
  erreichbar; Team-Kollegen öffnen den Link im Browser. Zweitrechner sehen dieselbe Ablage über NAS oder Freigabe.
- **Kommentare** frame-genau mit In/Out-Bereich, Antworten, Status (offen, umgesetzt, Rückfrage, erledigt),
  Schnellbausteine, Sterne-Bewertung mit Steuerwirkung (1–2 Sterne → gegen Konzept und Regeln neu prüfen; sinkende
  Bewertung → anhalten und nachfragen).
- **Endkunden der Agentur:** Runden über den lokalen Link im Agenturnetz oder Export der Version nach Dropbox Replay /
  Frame.io (heutige Replay-Anbindung übernehmen); Kommentare von dort werden importiert. Ein optionaler Relay-Dienst
  für externe Links kommt nur, wenn Kunden ihn ausdrücklich wollen.
- **„Änderungen umsetzen":** Server klassifiziert Kommentare (Haiku), plant Änderungen (Opus) und zeigt den Plan mit
  Kosten („7 Änderungen, 180 Credits"); nach Bestätigung konformiert der Client, rendert die Vorschau neu und legt V+1
  mit Antwort je Kommentar ab („gekürzt bei 01:12", „nicht umgesetzt, weil …").
- **Marker-Export:** Kommentare als Marker in Resolve (live) oder in die XML/FCPXML (Stufe 2).
- Später: Versionsvergleich nebeneinander, Zeichnen im Bild, Freigabe-Unterschrift.

## 6. Fremddienste und Zusatzmodule

| Dienst | Modell | Abrechnung |
|---|---|---|
| Transkription (ElevenLabs Scribe, Fallback Whisper lokal) | NIRO-Konto, serverseitig | in Credits enthalten |
| KI-Urteile (Anthropic; Wahrnehmung ggf. Gemini Flash oder lokal) | NIRO-Konten, serverseitig | in Credits enthalten |
| Generative Bild/Video (Higgsfield u. a.), Sprachsynthese | NIRO-Konto, serverseitig, nur auf ausdrückliche Wahl | Durchreichung × 1,5, einzeln ausgewiesen |
| Grafiken und Animationen | Eigene Dateien des Kunden (ProRes 4444) immer; dazu **generierte Grafiken aus dem Brand-Kit** (Bauchbinden, Titel, Endcards, Untertitel-Stil), die die KI wie heute in der Animation-Funktion als Remotion-Komposition schreibt und der Server rendert; keine Vorlagenbibliothek für Kunden, intern eine Komponentenbasis für Konsistenz und Kosten | je gerenderter Grafik in Credits; Remotion-Lizenz: frei bei höchstens 3 Mitarbeitern, sonst „Automators" mit 100 $/Monat Minimum (Abschnitt 11) |
| Musikbibliotheken (Artlist, Envato u. a.) | Lizenz gehört dem Kunden → eigenes Konto verbinden oder eigene Dateien hochladen | keine |
| Grading-LUTs, SFX | NIRO-Basis-Baum plus Kunden-LUTs; SFX-Bibliothek des Kunden | Grading-Profile im Agency-Tarif |
| Eigene API-Keys (Anthropic, ElevenLabs) | nur Enterprise, Aufrufe laufen weiter über den Server | Software-Entgelt statt Credits für diese Schritte |

Bundles ergeben sich aus den Tarifen (Abschnitt 4.3): Starter ohne Grafik-Bibliothek, Studio mit Brand-Kits und
Vorlagen, Agency mit Grading-Profilen und Priorität. Generative Dienste bleiben in allen Tarifen einzeln ausgewiesen.

## 7. Installer, Plattformen, Updates

- **macOS:** .dmg, Apple Silicon (arm64), signiert und notarisiert; Intel-Macs nicht unterstützt (lokale Modelle,
  Alter der Geräte).
- **Windows:** .msi/.exe (NSIS), signiert (Azure Trusted Signing oder EV-Zertifikat, damit SmartScreen nicht warnt),
  Windows 11 x64; NVIDIA-GPU optional für lokale Modelle, sonst Cloud-Index.
- **Gebündelt:** Python-Laufzeit (eigenständig, kein System-Python), ffmpeg/ffprobe statisch, kleine ONNX-Modelle
  (Gesichter, Personenmaske), Resolve-Bridge; große Modelle (Qwen3-VL ≈ 5–6 GB, Whisper large ≈ 1,5 GB) nur auf Wunsch
  beim ersten Einsatz mit Fortschritt und Prüfsumme. Installergröße ohne Modelle realistisch 300–500 MB (Abschnitt 11).
- **Voraussetzungen-Check** beim Start: Resolve Studio installiert und „External scripting = Local" (Anleitung mit
  Bildern), Premiere/FCP vorhanden für Exportpfade, Schreibrechte auf den Projektordner, NAS erreichbar.
- **Auto-Update** mit signierten Manifesten; Hülle, UI und Python-Sidecar getrennt versioniert, damit nicht jedes Update 150 MB lädt; der Server lehnt veraltete Versionen ab; Änderungsprotokoll in der App.
- **Download-Seite:** erkennt das Betriebssystem und bietet den passenden Installer; Direktlinks für IT-Abteilungen,
  Prüfsummen, Silent-Install für Windows-Rollouts.
- **Sicherheit:** keine Geheimnisse im Client, kurzlebige Job-Tickets, Geräte-Bindung, Wasserzeichen je Kunde im Build
  (siehe Plan, Abschnitt 6).

## 8. Weltweit: Sprachen, Formate, Regionen

- **Footage-Sprache** wird erkannt (Scribe, 90+ Sprachen, Sprechertrennung); Prompts sind sprachneutral, die
  Ausgabesprache (Schnittplan, Berichte, Untertitel) ist wählbar. Mischsprachige Interviews werden je Abschnitt
  gekennzeichnet.
- **UI** Englisch Standard, i18n mit ICU-Formaten (Zahlen, Datum, Plural), Umschaltung ohne Neustart; Rechts-nach-links
  später.
- **Bildraten, Timecode, Kameras**: Abschnitt 2.3; Kamerarollen werden erkannt statt vorausgesetzt, Sony-Telemetrie ist
  ein Bonus, kein Muss.
- **Regionen:** EU-Hosting des Servers; Datenresidenz-Option für KI-Aufrufe (Bedrock Frankfurt / Vertex EU) als
  Enterprise-Merkmal; Zeitzonen und Währungen über Stripe.

## 9. Stabilität und Skalierung

- Schwere Arbeit (Medien, Rendern, lokale Modelle) bleibt beim Kunden — die Cloud verarbeitet nur Text, JSON und kleine
  Bilder und skaliert deshalb leicht.
- **Server:** zustandslose API hinter Load-Balancer, verwaltetes Postgres mit Point-in-time-Recovery, Redis,
  **Workflow-Engine für langlaufende Jobs** (dauerhaft, Wiederholungen, „warten auf Client-Ergebnis", Zeitlimits),
  Objektspeicher mit Ablaufregeln, WebSocket-Gateway, Warteschlangen mit Priorität je Tarif, Idempotenz-Schlüssel,
  Rate-Limits je Organisation.
- **KI-Anbieter:** dünne Modellschicht mit Wiederholung, Backoff, Schutzschalter und Ausweichanbieter (Anthropic ↔
  Bedrock/Vertex), Batch für den Index, Caching; der eigentliche Engpass sind Rate-Limits der Anbieter → Stufen
  erhöhen, Last verteilen.
- **Betrieb:** OpenTelemetry, Fehlerberichte, Dashboards, Statusseite, Blue/Green-Deploys, Lasttests vor der Beta,
  Backups, Wiederherstellungsübung, EU-Rechenzentrum, später zweite Region.
- **Client:** Absturzberichte (opt-in), Wiederaufnahme unterbrochener Jobs (Cache je Clip), Diagnosepaket für den
  Support.

## 10. Wettbewerb im Detail (Recherche 22.09.2026, 20 Anbieter)

Legende: ✔ ja · ~ teilweise · ✘ nein · ? nicht belegt. „nativ" = Timeline entsteht direkt im NLE-Projekt.

| Anbieter | Schnittplan aus Konzept | 2-Kam-Sync | Rough Cut im NLE | B-Roll mit Regeln | Pegel · Musik · Grafik · Grading | QC | Review-Link | KI setzt Kommentare um | Rohmaterial lokal | NLEs | Preis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Eddie AI v4** | ~ Brief/Paper-Edit/Skript, kein Cutter-Plan | ✔ | ✔ nativ .prproj/.drp + XML/FCPXML/OTIO/EDL | ~ Beta, „works best with static b-rolls", regellos | ~ · ✔ generativ · ~ Captions · ✘ | ✘ | ✔ Cloud, gratis „Eddie Review", Frame.io-Roundtrip | ~ „Spark": Kommentar → Prompt → Änderung im Eddie-Edit, nicht in der Cutter-Timeline, keine Versionierung | ✘ Proxys in Cloud; Enterprise on-prem | Premiere, Resolve, FCP, Avid | Credits 10 $/1.000; Import 250/h, Export 100; ≈ 12–16 $ je 3-h-Projekt |
| **Quickture** | ✔ Ziellänge, Story-Beats, Notizen | ✔ | ✔ Panel Premiere/Avid | ~ Vision-Matching | ✘ | ✘ | ✘ | ~ Revisionen aus Notizen | ✘ Proxys in Cloud | Premiere, Avid | 499 $/Seat/Monat |
| **Adobe Premiere 26.5 + AI Assistant (Beta 06/2026)** | ~ Paper Edit manuell; Assistant „rough assembly", Skript/Notizen „not yet" | ✔ Sync-Map | ✔ nativ | ✘ nur generative B-Roll | ~ Match Source Audio · ✘ · ✘ · ✘ | ✘ | ✔ Frame.io | ~ Frame.io-Assistant fasst Feedback nur zusammen | ~ Cloud | Premiere | im CC-Abo; Firefly-Credits; Frame.io 15–25 $/Mitglied |
| **Resolve 20/21 nativ + MCP 21.1** | ~ IntelliScript braucht Skript | ✔ + SmartSwitch | ✔ nativ | ✘ | ✔ Audio Assistant · ~ · ✘ · ✔ Werkzeuge | ✘ | ✔ Cloud Presentations, 20 gratis | ✘ | ✔ | Resolve | Studio 295 $ einmalig |
| **Threadline Studio** | ✔ Brief → Assembly, Intonationsanalyse | ✔ nur Studio-Tier | ~ XML | ✘ | ✘ | ✘ | ✔ Share-Links | ✘ | ~ | Premiere, Resolve, FCP | 6 / 24 / 95 $ je Monat |
| **Filmit RoughCut** | ✔ Story-Text → Hero/Cut-down/Shorts | ~ | ✔ nativ (Resolve Workflow Integration, Premiere-Panel) | ✘ | ✘ | ✘ | ✘ | ✘ | ✔ Whisper lokal, eigener LLM-Key | Resolve, Premiere | 20 $/Monat + API |
| **Selects (Cutback)** | ~ | ✔ Auto-Switch | ~ Handoff | ✘ | ~ | ✘ | ✘ | ✘ | ✘ | Premiere, FCP, Resolve | 20 / 100 / 1.000 $ je Monat |
| **Descript / Underlord** | ~ | ✘ kein Multicam-Export | ~ XML/FCPXML/AAF | ~ Stock | ✔ Studio Sound · ~ · ~ · ✘ | ✘ | ~ | ~ eigener Loop | ✘ | Export | 16–65 $/Monat |
| **Jumper** | ✘ Suche | ✘ | ~ Selects | ~ Suche | ✘ | ✘ | ✘ | ✘ | ✔ offline | Premiere, Resolve, FCP, Avid | 169 $ einmalig; Pro 49 $/Monat |
| **Firecut · AutoCut · Autopod** | ✘ | ~ Sprecherwechsel | ✔ nativ | ~ Stock | ~ Captions/Zooms | ✘ | ✘ | ✘ | ? | Premiere, Resolve | 7–44 $/Monat |
| **Spingle** (Beta) | ✘ | ✘ | ~ Selects auf Spur 2 | ~ | ✘ | ~ Ausschuss | ✘ | ✘ | ✘ | Premiere | kein Preis |
| **Digital Nirvana RoughCut** | ✔ „explains every decision" | ? | ~ AAF/XML | ? | ✘ | ✘ | ? | ? | ? | Avid, Premiere, FCP, Resolve | Enterprise |
| **Deutschsprachig:** Sisyphos · A-Roll Studio · AMBOSS | ~ signalbasiert · ✘ · ✘ | ✘ | ~ FCPXML · ~ XML · ✔ Premiere | ✘ | ✘ · ~ Auphonic · ~ | ~ | ✘ | ✘ | ✔ · ✘ · ✔ | FCP · XML · Premiere | 189 € einmalig · 0,25 €/min · 49–99 €/Monat |
| **Frame.io · Dropbox Replay · BMD Presentations** | reine Review-Werkzeuge | | | | | | ✔ | ✘ | | Panels | 15–25 $ · 10–12 $ je Nutzer · 20 gratis |
| **FrameSense** | reines Datei-QC (Black/Freeze/Loudness) | | | | | ✔ | | | ✘ | | 29 / 79 $ je Monat |
| **NIRO (geplant)** | ✔ | ✔ | ✔ nativ Resolve, Datei für Premiere/FCP | ✔ regelbasiert aus eigener Auswahl + Telemetrie | ✔ · ✔ · ✔ · ✔ | ✔ Kantenprüfung | ✔ | ✔ V+1 mit Antworten im Cutter-Projekt | ✔ | Resolve live, Premiere/FCP Datei, Avid OTIO | Credits, Abo 290–1.190 €/Monat |

**Gibt es unseren Umfang schon?** Nein, nicht als Kette. Jeder Baustein existiert irgendwo: Aussagen-Auswahl aus Brief
(Eddie, Quickture, Threadline, Filmit), Zwei-Kamera-Sync (Eddie, Resolve, Selects), native Timeline (Eddie .drp, Filmit
direkt in Resolve, Quickture-Panel), Mix (Resolve Audio Assistant), Review mit Frame-Kommentaren (Eddie, Frame.io,
Replay, BMD Presentations), Kommentar → Änderung (Eddie „Spark", Quickture-Notizen). Niemand verbindet
konzeptgetriebenen Schnittplan und Feinschnitt mit regelbasierter B-Roll-Verteilung aus der eigenen Auswahl, Musik,
Grafik, Grading, Kanten-QC und einem Review-Loop, dessen Ergebnis als neue Version in der Timeline des Cutters landet.

**Wer kommt am nächsten?** Eddie AI: hohes Tempo (v3 04/2026, v4 09/2026), native .drp/.prproj, Multicam inkl.
„schmutziger" Multicam-Import, Night Shift, Kommentar-Spark, MCP-Server mit ~100 Werkzeugen, Agenten in Blackmagic
Cloud, ~100 Sprachen, Enterprise on-prem. Grenzen: Der Übergabepunkt ist der Rough Cut, alles danach passiert außerhalb;
die B-Roll-Automatik ist Beta und regellos („the B-roll placement wasn't amazing"); Proxys gehen in die Cloud; Relink
auf Originale schlägt bei Web-Uploads oft fehl; Kommentar-Umsetzung wirkt nur auf Eddies Edit. Quickture ist im
Revisions-Loop stark, aber Broadcast-Enterprise ohne Resolve bei 499 $ je Seat.

**Unsere Lücke im Markt:** (1) Feinschnitt-Stufe im NLE mit Regeln aus der eigenen Auswahl-Timeline — bietet niemand.
(2) QC am Export mit Kantenprüfung — es gibt nur generisches Datei-QC. (3) Review → KI setzt um → V+1 mit Antworten im
Projekt des Cutters — Eddie hat den Halbautomaten in der eigenen Cloud, im NLE hat es niemand. (4) Rohmaterial bleibt
lokal — Eddie, Quickture, Selects, Threadline, Spingle laden Proxys hoch; lokal arbeiten nur Jumper, Filmit, Sisyphos
und Resolve nativ, und die machen keinen Feinschnitt. (5) Deutsch als Erstsprache — Adobe „optimized for English",
Resolve-Transkription mit Schwächen bei Deutsch.

**Angreifbar durch Adobe:** AI Assistant, Paper Edit und Frame.io-Zusammenfassung sitzen im CC-Abo; „versioning,
cut-downs, script/production note integration" stehen ausdrücklich als „not yet", also Roadmap. Setzt der Assistant
Frame.io-Kommentare um, ist unser Review-Loop für Premiere-Agenturen im Abo enthalten. Kurzfristiger Schutz:
Englisch-Fokus, Cloud-Zwang, kein Resolve. **Angreifbar durch Blackmagic:** Der MCP-Server gibt jedem Studio-Nutzer mit
Claude denselben Hebel, den wir nutzen; IntelliScript, SmartSwitch, Audio Assistant und Cloud Presentations decken Sync,
Skript-Assembly, Mix und Review-Kommentare nativ ab. Unser Vorsprung ist das Domänenwissen (Konzept → Aussagen →
Regelwerk → QC → Antworten an den Kunden), nicht der technische Zugriff — deshalb bleibt es serverseitig.

**Preiseinordnung (09/2026):** Plugins 10–35 $ je Seat und Monat; Rough-Cut-SaaS 24–100 $ je Monat; Eddie ≈ 12–16 $
je 3-h-Projekt, Vielnutzer 120–350 $ je Monat; Enterprise 399–999 $ je Seat (Quickture); Review 10–25 $ je Nutzer;
QC 29–79 $. Für unseren Umfang ist eine Agentur-Lizenz von 100–300 $ je Seat und Monat oder ein Projektpreis von
50–150 € je Video marktkonform — oberhalb der Plugins, deutlich unter Quickture. Unsere Tarife (290 / 590 / 1.190 €
mit 1 / 3 / 8 Sitzen) liegen genau dort; das Beispielprojekt aus Abschnitt 4.2 (≈ 107 €) ebenso.

Quellen (Auswahl): [Eddie v4 (CineD)](https://www.cined.com/eddie-ai-v4-unveiled-native-premiere-and-resolve-projects-avid-extension-and-c2pa-signing/) ·
[Eddie Pay-as-you-go (CineD 28.08.2026)](https://www.cined.com/eddie-ai-overhauled-pay-as-you-go-pricing-editing-from-claude-and-chatgpt-and-an-iphone-app/) ·
[Eddie B-Roll-Hilfe](https://help.heyeddie.ai/en/articles/13254231-b-roll-placement) · [Eddie Kosten](https://help.heyeddie.ai/en/articles/10076713-cost-price-subscribe-credit-unsubscribe) ·
[Eddie Frame.io-Roundtrip](https://www.heyeddie.ai/help/frameio-review-round-trip) · [Eddie Export](https://www.heyeddie.ai/help/export-to-your-nle) ·
[Quickture (PVC NAB 2026)](https://www.provideocoalition.com/nab-2026-eddie-ai-quickture-selects-the-ai-editing-assistants/) · [quickture.com](https://www.quickture.com/) ·
[Adobe AI Assistant Beta](https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317) ·
[Premiere 26.5](https://community.adobe.com/announcements-727/what-s-new-in-adobe-premiere-26-5-september-2026-1641187) · [Frame.io Blog 08.09.2026](https://blog.frame.io/2026/09/08/new-in-frame-io-indesign-previews-spacebar-quicklook-and-ibc-2026/) ·
[Resolve 21 New Features Guide](https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_21_New_Features_Guide.pdf) · [Resolve 21.1 MCP (CineD)](https://www.cined.com/davinci-resolve-21-1-released-ai-assistant-integration-via-mcp-individual-hdr-trims-and-python-scripting-moves-to-studio/) ·
[BMD Cloud Presentations](https://help.cloud.blackmagicdesign.com/presentations/) · [Threadline (CineD)](https://www.cined.com/threadline-launches-ai-editing-workspace-with-intonation-analysis-and-native-xml-export-to-premiere-resolve-and-final-cut-pro/) · [Threadline Pricing](https://threadlinestudio.io/pricing) ·
[Filmit RoughCut](https://filmit.io/roughcut/) · [Selects Pricing](https://tryselects.com/pricing/) · [Descript Timeline exports](https://help.descript.com/hc/en-us/articles/10255813481613-Timeline-exports) ·
[Jumper](https://getjumper.io/) · [Firecut](https://firecut.ai/pricing/all/) · [AutoCut](https://www.autocut.com/en/pricing/) · [Autopod](https://www.autopod.fm/pricing) ·
[Spingle (MASV)](https://masv.io/blog/best-ai-video-editor) · [Digital Nirvana](https://digital-nirvana.com/news/digital-nirvana-launches-roughcut-ai-video-editing-platform/) ·
[Sisyphos](https://startupvalley.news/de/sisyphos-mac-app-ki-rohschnitt/) · [A-Roll Studio](https://aroll-studio.de/) · [AMBOSS](https://www.amboss-app.de/) ·
[Frame.io Pricing](https://frame.io/pricing) · [Dropbox Replay (Shade)](https://shade.inc/blog/dropbox-review-video-production) · [FrameSense](https://www.framesense.io/)

## 11. Fertige Bausteine (Recherche 22.09.2026, Lizenzen und Preise geprüft)

Empfohlener Stack. Alles Open Source mit MIT/BSD/Apache, sofern nicht anders vermerkt; „n. v." = nicht verifiziert.

| Bereich | Baustein | Alternativen / Ausschlüsse | Warum |
|---|---|---|---|
| Desktop-Hülle | **Tauri 2** (2.11.6, 09/2026; Apache/MIT) mit Sidecar, signiertem Updater, Bundler für dmg/msi/nsis; Remote-UI möglich | Electron (MIT) als Rückfall | Kleinste Hülle (5–10 MB statt 80–120 MB), Updater und Installer eingebaut; Rust-Kern ist schwerer zu lesen als Electron |
| Python-Paketierung | **python-build-standalone + uv** (Release 09/2026, Python 3.10–3.15) als eingebetteter Interpreter mit venv | PyInstaller 6.22 nur onedir als Rückfall; Nuitka für Obfuskation einzelner Module | fusionscript, onnxruntime, numpy laufen ohne Freeze-Sonderfälle; Resolve-Scripting läuft nachweislich mit aktuellem Python |
| Frontend | **React 19 + Vite 8 + Tailwind 4 + shadcn/ui** (auf Base UI, seit 07/2026 Standard), TanStack Router/Query, Zustand; i18n mit **ICU MessageFormat als Quellformat**, umgesetzt mit **Lingui** (MIT, Makros, Build-Prüfung fehlender Übersetzungen) oder i18next + i18next-cli | react-intl als Alternative; Fluent Nische | Größte Bibliotheksdichte; i18next deckt Plural, Datum, Zahl und Übersetzer-Werkzeuge ab |
| Player und Zeitleiste | **Eigene `<video>`-Steuerung mit `requestVideoFrameCallback`** (Frame-Schritte über `mediaTime`, nicht `currentTime`) und **mediabunny** (MPL-2.0, WebCodecs-Decode für exakte Frames); Player-Oberfläche ist Nebensache: Video.js v10 vereint Vidstack, media-chrome und Plyr (Release Candidate 09/2026, GA offen), bis dahin media-chrome oder Omakase Player (Apache-2.0); **wavesurfer.js v7** (BSD-3) mit serverseitig berechneten Peaks; Zeitleiste und Zeichen-Overlay als Eigenbau auf **react-konva** oder **fabric.js** plus **perfect-freehand** (alle MIT) | tldraw und „OpenVideo Editor" nur mit Kauflizenz → meiden; Kitsu ist AGPL/Vue/Pipeline-Werkzeug | Kein brauchbares Open-Source-Review-Frontend mit Frame-Kommentaren vorhanden → Review-UI aus NIRO Review selbst bauen; Safari-`currentTime` ist nicht frame-genau, WebView2 und WKWebView unterscheiden sich bei Codecs → Review-Kopien als H.264 |
| Backend | **FastAPI + Postgres + Hatchet** (MIT; braucht nur Postgres; Durable Events für „warten auf Bridge-Ergebnis", Retries je Schritt, Concurrency je Mandant) | Temporal (MIT) als Reserve; Celery/Dramatiq passen nicht (kein Warten/Signale); Inngest-Server ist SSPL | Passt zum Python-Kern; Hatchet Cloud springt vom Free-Tier auf 500 $/Monat → selbst hosten |
| Credits und Zahlung | **Eigener Credit-Ledger** (Reservierung → Verbrauch → Freigabe) + **Stripe** Checkout/Subscriptions/Tax/Kundenportal | Stripe Credit Grants nur für metered Abo-Positionen, keine Reservierung, max. 100 offene Grants je Kunde → reichen nicht; Lago (AGPL)/OpenMeter messen nur; Polar.sh als Merchant of Record denkbar | Vorkalkulation und verbindlicher Voranschlag brauchen Reservierung im eigenen Ledger |
| Auth, Orgs, Einladungen | **Clerk oder WorkOS AuthKit** zum Start (Orgs, Einladungen, Passkeys fertig; FastAPI prüft JWTs) | Zitadel (AGPL, Postgres, Orgs nativ) als Self-Host-Option für EU; Keycloak (JVM) möglich | Schnellster Start; Einladungspflicht ist Konfiguration, kein Eigenbau |
| Lizenzen und Geräte | **Ed25519-Eigenbau** (Lizenzdatei, Gerätetabelle, Heartbeat) oder **Keygen CE** (Fair Core License; Cloud frei bis 100 Lizenzen) | Cryptlex/LicenseSpring binden an Anbieter | Bei 1–3 Entwicklern ist der Eigenbau oft günstiger als Keygen-Betrieb |
| Admin, Betrieb | **Refine** (MIT) für das Admin-Panel; **Sentry** (EU-Region) + **OpenTelemetry**; **Cloudflare R2** (EU-Jurisdiktion, kein Egress, 0,015 $/GB-Monat, Lifecycle-Regeln); slowapi + Cloudflare Rate Limiting | MinIO ist tot (Repo archiviert 25.04.2026) → nicht einsetzen | Standard, wenig Betrieb |
| Medien | **ffmpeg 9.0.2 als LGPL-Build** (BtbN für Windows; eigener LGPL-Build für macOS arm64) mit Hardware-Encodern; **ONNX Runtime 1.30 + YuNet** (Modell MIT) für Gesichter; **MediaPipe Image Segmenter** (Apache-2.0) oder BiRefNet (MIT) für Personenmasken (rembg nur mit ausdrücklich gewähltem Modell: der Standard bria-rmbg ist CC BY-NC); **PySceneDetect 0.7.1**; scipy-Kreuzkorrelation für Sync; ffmpeg ebur128 / pyloudnorm | Ausgeschlossen: InsightFace (Modelle nur nicht-kommerziell), Ultralytics YOLO (AGPL), Robust Video Matting (GPL), GPL-ffmpeg mit x264/x265 im Installer; MediaPipe kennt kein Python 3.13 | Alles MIT/BSD/Apache inklusive Modellgewichten; ersetzt Apple Vision auf beiden OS mit gleichen Ergebnissen |
| Lokale KI | **Qwen3-VL-8B** (Apache-2.0; Q4 ≈ 5–6 GB, ≈ 6–7 GB VRAM), 4B als Fallback; **mlx-vlm-Server** (0.7.2, 09/2026) auf Mac, **llama-server** (llama.cpp b11105, Qwen3-VL seit 10/2025, CUDA/Vulkan/ROCm) auf Windows; **whisper.cpp 1.9.4** (Metal/CUDA/Vulkan) oder faster-whisper 1.2.1 (Windows nur NVIDIA); Sprechertrennung pyannote community-1 (CC-BY-4.0, auf Hugging Face gated; Spiegeln mit Namensnennung erlaubt) → Standard bleibt Scribe in der Cloud | Ollama (MIT, v0.34.3) liefert ein Standalone-Zip „for embedding in applications" als Alternative zu llama-server; LM Studio darf laut Terms nicht gebündelt werden; llama-cpp-python hinkt hinterher; Nachfolger Qwen3.5/3.6/3.8 sind nativ multimodal (Apache-2.0) und im Eval mitzutesten | Beide Server sprechen OpenAI-kompatibles HTTP → ein Client in der Bridge; Modelle aus eigenem R2-Spiegel mit SHA-256 beim ersten Start (Hugging Face drosselt anonyme Downloads; tauri-plugin-upload hat weder Resume noch Prüfsumme → selbst ergänzen) |
| Animationen | **Remotion 4.0.527** mit @remotion/renderer in eigenen Docker-Workern; **Company License „Automators": 0,01 $ je erfolgreichem Render, mindestens 100 $/Monat** (Creators 25 $/Seat für kleine Volumen; Enterprise ab 500 $). Endkunden brauchen keine Lizenz, wenn sie Videos aus unseren Vorlagen rendern; verboten ist, dass Nutzer eigene Remotion-Projekte hochladen. Lizenz ändert sich mit Remotion 5.0 (Wortlaut offen) | Remotion Lambda (AWS-Bindung) für Lastspitzen; Cloud Run ist Alpha und eingestellt; Motion Canvas ohne Release seit 12/2024; Revideo (MIT) ohne React-Vorlagenmodell | Planbar, Vorlagen bleiben React-Code im eigenen Repo |
| Austauschformat | **OpenTimelineIO 0.18.1** (Wheels cp39–cp313 für Windows x64 und macOS arm64), otio-aaf-adapter 2.0.0; **eigene Writer für FCP7-XML und FCPXML 1.13/1.14** | Die XML-Adapter sind Kleinstprojekte (7–23 Sterne) ohne Pegel/Speed/Transitions (Abschnitt 2.3) | OTIO für Resolve, Premiere, Avid und Tests; XML selbst schreiben |

**Größen:** Installer ohne Modelle realistisch 300–500 MB (Python-Sidecar mit numpy/scipy/pillow/opencv 150–250 MB,
onnxruntime 14–22 MB, ffmpeg 80–120 MB, Tauri 5–10 MB); Modelle 5–9 GB nur auf Wunsch (Qwen3-VL-8B Q4 ≈ 5–6 GB,
Whisper large-v3 2,9 GB, turbo 1,5 GB).

**Feinheiten aus der Medien-Recherche:** Für macOS arm64 gibt es keinen etablierten LGPL-ffmpeg-Anbieter (Riedl und
Homebrew sind GPL mit x264/x265, evermeet nur Intel) → eigener LGPL-Build nach den Vorlagen luckyneko/ffmpeg-prebuilt
bzw. Nothing-Software/FFmpeg-Builds mit VideoToolbox, h264_mf und NVENC; H.264-Software-Encoding nur über OpenH264,
dessen Cisco-Binary zur Laufzeit geladen werden muss und nicht gebündelt werden darf. Für kleine Gesichter ergänzt
UniFace-RetinaFace (MIT, ONNX) den schnellen YuNet; SCRFD aus InsightFace bleibt tabu. MediaPipe 1.0.1 ist für Python
3.13 nicht verifiziert; DirectML unter Windows ist in Wartung, neue Entwicklung läuft über Windows ML → CPU- und
CoreML-Pfade zuerst, GPU als Bonus. Audio-Sync bleibt Eigenbau mit `scipy.signal.correlate`, wie heute.

**Feinheiten aus der Desktop-Recherche:** Der Tauri-Updater kennt kein Delta, jedes Update lädt Hülle plus
Python-Sidecar (130–200 MB komprimiert) → Sidecar und Hülle getrennt versionieren und den Sidecar nur laden, wenn er
sich geändert hat. Die Notarisierung von Sidecars ist ein offener Tauri-Fehler (#11992), Python-Bibliotheken unter
Resources stehen nicht in Tauris Signierliste → eigener Signierschritt im Build. Remote-UI ist über eine URL als
`frontendDist` möglich, die Doku warnt aber vor entfernten Inhalten (IPC-Freigabe je Origin, CSP nur für gebündelte
Assets) → **UI wird gebündelt und häufig aktualisiert**, Remote-Inhalte nur für Hilfe und Neuigkeiten. Große
Vorschau-Videos nicht über Tauris `asset:`-Protokoll, sondern über einen lokalen HTTP-Server mit Range-Unterstützung aus
dem Python-Kern (wie heute `review.py`). Nuitka steht inzwischen unter AGPL mit Runtime-Ausnahme (Kompilate frei
verteilbar, Commercial 250 €/Jahr für Einbettung und Obfuskation). Windows-Signierung über Azure Artifact Signing (ex
Trusted Signing, ≈ 10 $/Monat, Identitätsprüfung der Firma 1–20 Werktage, EU-Organisationen zugelassen) statt
EV-Zertifikat. Resolve-Scripting läuft mit Python 3.10–3.12 am sichersten, 3.13/3.14 sind auf Studio 20.3 belegt; der
eingebettete Interpreter muss `RESOLVE_SCRIPT_API`, `RESOLVE_SCRIPT_LIB` und `PYTHONPATH` selbst setzen — im
Durchstich als erstes prüfen. Tauri ab 2.11.6 einsetzen (Sicherheitsfix für IPC-Kanäle vom 19.09.2026).

**Feinheiten aus der Frontend-Recherche:** WebKit springt beim Seek über `currentTime` bei hohen Bildraten 3–6 Frames
statt einem (hls.js-Issue #7583) → Frame-Stepping über `requestVideoFrameCallback().mediaTime` oder WebCodecs-Decode;
WKWebView auf älterem macOS hat keinen `AudioDecoder` → Wellenformen serverseitig oder per ffmpeg berechnen. Vidstack
läuft aus (Maintainer 03/2026: nur noch PR-Merges), deshalb keine Player-Bibliothek als Fundament. Kein
Open-Source-Review-Frontend ist direkt übernehmbar; **FreeFrame** (MIT; React + FastAPI/Celery/Postgres, frame-genaue
Timecode-Kommentare, Zeichnen, Versionsvergleich, Export als EDL/FCPXML/Premiere) taugt als Code-Steinbruch,
Kitsu, Clapshot und Kollaborate als Vorbilder. Lizenzfallen im Frontend: tldraw (≈ 6.000 $/Jahr), OpenVideo Editor,
Twick (kein Hosting ohne Vertrag), AYON und OpenFrame (FSL), Kitsu (AGPL), peaks.js (LGPL), audiowaveform (GPL, nur als
separater Prozess). Review-Preisanker: Frame.io 15–25 $, Replay 9–11 €, Filestage 199–329 € flat, Kollaborate Server
159–1.899 $ einmalig.

**Risiken aus der Recherche:** Remotion-Lizenzänderung mit 5.0 und 100 $ Mindestgebühr; pyannote-Gewichte gated;
Hatchet-Cloud-Preissprung → Self-Host; Stripe Credit Grants ungeeignet → Ledger Pflicht; Hugging-Face-Rate-Limits
ohne Token → eigener Spiegel; Vidstack- und Revideo-Wartung unklar; MediaPipe ohne Python 3.13; Windows: GPU-Vielfalt
erzwingt Modellwahl beim Start und CPU-Fallback, Signing (EV oder Azure Trusted Signing) kommt zur Apple-Notarisierung
hinzu; WebView-Unterschiede bei Codecs und Seek-Genauigkeit testen.

Quellen (Auswahl): [Tauri](https://crates.io/api/v1/crates/tauri) · [python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases) ·
[PyInstaller](https://pypi.org/project/pyinstaller/) · [Omakase Player](https://github.com/byomakase/omakase-player) · [tldraw-Lizenz](https://github.com/tldraw/tldraw/blob/main/LICENSE.md) ·
[Hatchet](https://github.com/hatchet-dev/hatchet) · [Hatchet-Preise](https://hatchet.run/pricing) · [Temporal-Preise](https://temporal.io/pricing) ·
[Stripe Billing Credits](https://docs.stripe.com/billing/subscriptions/usage-based/billing-credits) · [Keygen](https://github.com/keygen-sh/keygen-api) · [Zitadel](https://github.com/zitadel/zitadel) ·
[MinIO archiviert](https://github.com/minio/minio) · [BtbN ffmpeg](https://github.com/BtbN/FFmpeg-Builds) · [ONNX Runtime](https://pypi.org/project/onnxruntime/) ·
[YuNet](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/README.md) · [InsightFace-Lizenz](https://github.com/deepinsight/insightface) · [PySceneDetect](https://pypi.org/project/scenedetect/) ·
[Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) · [Qwen3-VL GGUF](https://ollama.com/library/qwen3-vl/tags) · [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) ·
[llama.cpp Qwen3-VL PR](https://github.com/ggml-org/llama.cpp/pull/16780) · [Ollama Windows Standalone](https://docs.ollama.com/windows) · [LM Studio Terms](https://lmstudio.ai/terms) ·
[faster-whisper](https://pypi.org/project/faster-whisper/) · [whisper.cpp Modelle](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md) · [pyannote](https://pypi.org/project/pyannote.audio/) ·
[HF Rate Limits](https://github.com/huggingface/hub-docs/blob/main/docs/hub/rate-limits.md) · [R2-Preise](https://developers.cloudflare.com/r2/pricing/) ·
[Remotion-Lizenz](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) · [Remotion-Preise](https://www.remotion.pro/license) · [Remotion-FAQ](https://www.remotion.dev/docs/license/faq) ·
[Motion Canvas](https://github.com/motion-canvas/motion-canvas/releases) · [OTIO PyPI](https://pypi.org/project/OpenTimelineIO/) · [Tauri Sidecar-Notarisierung #11992](https://github.com/tauri-apps/tauri/issues/11992) · [Tauri Remote-URLs](https://v2.tauri.app/security/capabilities) · [Nuitka Runtime-Lizenz](https://raw.githubusercontent.com/Nuitka/Nuitka/develop/LICENSE-RUNTIME.txt) · [Azure Artifact Signing](https://learn.microsoft.com/azure/artifact-signing/quickstart) · [Video.js v10](https://videojs.org/blog) · [Vidstack-Zusammenschluss](https://github.com/vidstack/player/discussions/1747) · [mediabunny](https://github.com/Vanilagy/mediabunny) · [hls.js #7583](https://github.com/video-dev/hls.js/issues/7583) · [Lingui](https://github.com/lingui/js-lingui) · [FreeFrame](https://github.com/Techiebutler/freeframe) · [fabric.js](https://github.com/fabricjs/fabric.js) · [FFmpeg Legal](https://ffmpeg.org/legal.html) · [OpenH264 Binary License](https://www.openh264.org/BINARY_LICENSE.txt) · [rembg](https://github.com/danielgatis/rembg) · [MediaPipe Image Segmenter](https://developers.google.com/edge/mediapipe/solutions/vision/image_segmenter) · [UniFace](https://github.com/yakhyo/retinaface-pytorch)

## 12. Offene Punkte und Probe-Läufe vor dem Bau

1. Probe-Roundtrips Premiere 26.x (FCP7-XML: Pegel, Speed, `enabled`, Spurnamen, Kanäle, 23,976; OTIO-Umfang) und
   Final Cut 12.x (FCPXML 1.14: `adjust-volume`, `timeMap`, Lanes/Rollen, `open`-Dialog) — je ein Tag; CapCut nur als
   gerenderte Lieferung testen.
2. Eigener Vorschau-Render mit ffmpeg aus dem Schnittmodell (zwei Kameraspuren, B-Roll, Pegel, Musik, Alpha-Grafik) —
   Prototyp an einer bestehenden Charge.
3. Credit-Formel gegen die gemessenen Kosten der fünf Referenzprojekte kalibrieren, sobald der Modellvergleich gelaufen
   ist.
4. Aus der Recherche entschieden: Remotion Automators-Lizenz (100 $/Monat Minimum) einplanen, Hatchet selbst gehostet
   als Workflow-Engine, Credit-Ledger selbst bauen; offen bleibt Ed25519-Eigenbau gegen Keygen CE für Lizenzen und
   Clerk/WorkOS gegen Zitadel für Auth — Entscheidung im Durchstich.
5. Windows: Ersatz für Apple-Vision-Teile (ONNX) und lokale Modelle mit/ohne GPU — Prototyp nach dem Mac-Durchstich.
6. Namensfindung (siehe Plan): „AutoCut" ist besetzt.

## 13. Entscheidungen vom 22.09. (abends) und Zeitplan

| Punkt | Entscheidung |
|---|---|
| Name | Vorschläge mit Domain- und Kollisionsprüfung liefert Claude (Chat 22.09.); Entscheidung offen |
| MVP | Schnittplan, Rohschnitt, **automatische B-Roll** (Eingrenzung optional), Ton, Finalisieren, Kantenprüfung, **Review lokal**, **Grafiken** (eigene Dateien + generierte aus Brand-Kit). Später: Musik-Analyse, SFX, Grading, Premiere/FCP-Writer |
| Plattform | Mac (Apple Silicon) zuerst, Windows danach |
| Programme | Resolve im Fokus; übrige Programme so, wie es heute per Datei geht; Ausbau, wenn dort MCP oder API kommen |
| Preis | 1 Credit = 0,10 €, Tarife 290 / 590 / 1.190 €, Prepaid verfällt nicht, Pilot 249 €; später anpassbar |
| Review | lokal, versionierte Ordner, kein Cloud-Hosting |
| Concierge | noch nicht |
| Fremddienste | über NIRO-Konten in Credits (Empfehlung übernommen) |
| UI-Sprachen | Englisch und Deutsch |
| Struktur | Produktlinie der NIRO Productions, eigenes CI |
| Budget | so wenig wie nötig: eine kleine Hetzner-Maschine, eigenes Auth mit Einladung statt Clerk, Stripe erst zur Beta, Remotion nur so lange frei, wie die Firma höchstens 3 Mitarbeiter hat, sonst 100 $/Monat |
| Zeit | intern unbegrenzt; Zielvorgabe „geschlossene Beta in 7 Tagen" → realistisch: **interner Durchstich in 7 Tagen**, geschlossene Beta mit fremden Agenturen frühestens 6–8 Wochen danach (Installer, Signierung, Abrechnung, Recht) |

### 7-Tage-Plan: interner Durchstich (Mac, Resolve, Mitarbeiter als erster Nutzer)

| Tag | Inhalt |
|---|---|
| 1 | Repo anlegen; `niro_autocut` und `niro_transcribe` mit Tests als `core/` übernehmen; Schnittmodell-Schema; lokaler Server (FastAPI) mit Job-Modell; Login-Stub mit Einladungsliste |
| 2 | Pipeline-Schritte Transkription (Scribe über Server), Aussagen-Pool, Schnittplan als API-Schritte: Prompts aus WORKFLOW und `prompts/` übersetzt, Structured Output, Verify |
| 3 | Cutlist-Schritt mit Verify-Schleife (Tool Runner, Budget, Zug-Grenze); Bridge-Runner wickelt prepare, sync, build in Resolve als Jobs ab; Readback zurück an den Server |
| 4 | Web-UI (React/Vite) im Fenster: Projekt anlegen, Erkennung, Auftrag, Kostenvoranschlag mit Formel und Stub-Ledger, Fortschritt; Rohschnitt bauen |
| 5 | B-Roll automatisch: Stufe 3 mit den Telemetrie-Feldern reaktivieren und am Eval-Projekt prüfen; Eingrenzung per Ordner-Häkchen; 3a bleibt Rückfall |
| 6 | Ton (Pegel), Finalisieren, Kantenprüfung als Jobs; Review lokal (NIRO Review integriert, Versionsordner); „Änderungen umsetzen" als Schritt |
| 7 | Durchlauf mit dem Mitarbeiter an einem echten Projekt; Kosten und Zeit je Schritt messen; Bericht; Lückenliste |

Nicht im Durchstich: Tauri-Installer und Notarisierung (Start im Entwicklermodus), Windows, Stripe, Premiere- und
FCP-Writer, Grafik-Generator, Musik, Grading, Mandanten-Härtung. Voraussetzungen: GitHub-Repo an Tag 1,
Anthropic-Workspace spätestens Tag 2, Freigabe der Eval-Projekte, Resolve Studio offen auf dem Studio-Mac.

### Danach (Wochen 2–8 bis zur geschlossenen Beta)

Tauri-Hülle mit Installer und Signierung, Auth mit Geräten, Credit-Ledger mit Stripe, Grafik-Generator, Premiere-XML,
AGB/AVV/EULA, Windows-Vorbereitung; dann 2–3 Agenturen als geschlossene Beta.

## 14. Reihenfolge

Durchstich auf Mac mit Resolve als Stufe 1, **aber von Anfang an über das Schnittmodell und den eigenen
Vorschau-Render**, damit Stufe 2 später nur Adapter sind. Danach: Review-Modul, Preisrechner mit Stripe, Premiere- und
FCP-Adapter, Windows, Grafik-Generator, CapCut als Render.
