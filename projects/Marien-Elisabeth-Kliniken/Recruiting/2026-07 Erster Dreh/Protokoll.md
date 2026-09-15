# Protokoll — Marien-Elisabeth-Kliniken / Recruiting / 2026-07 Erster Dreh

## 2026-09-14 — Prüfung Video 3 NEU gegen Schnitt 07.08. und Kunden-Feedback

**Gemacht:**
- Beide Fassungen aus `Prüfen/` geprüft: `…_720p.mp4` (= Export 07.08., 64,1 s) und `…_NEU.mov` (57,2 s,
  2160×3840, 25 fps). Scribe-Wort-Transkripte, framegenauer Bildabgleich neu ↔ alt, Wortzuordnung zu den
  Quellclips, Lippensync gegen die NAS-Originale (mit Gegenprobe), B-Roll-Herkunft über den B-Roll-Index des
  Imagefilm-Projekts, R128/Musik/Knackser. Kunden-Feedback im Wortlaut aus der Session vom 11.09. geholt.

**Ergebnis:** CAC in Ton und Bild komplett raus; [NEU] Zoran und [FIX] Augenhöhe drin; alle neuen
Interview-Bilder lippensynchron; nur Standort 1. Mängel:
- MUSS: Schwarzbild 00:14:12–00:15:14 in Zorans Satz; Zoran erst 5,1 s nach dem Hook statt direkt (Plan #2).
- SOLLTE: Christian #3 jetzt 8,7 s am Stück im Bild statt B-Roll-gedeckt (Bildanteil 39 → 42 %, Sprechzeit
  32,6 → 20,8 s); Loch 0:17,5–0:19,9 mit abgesenkter Musik; Zorans „am, am"/„äh" noch drin.
- KANN: Musiksprung ca. 0:32,3–0:32,9; Herzkatheter-B-Roll gegen CT/Impella/Ultraschall getauscht;
  True Peak −0,2 dBTP.

**Geliefert:** `Ergebnisse/Review/Video3-Intensiv-Elisabeth-NEU-Pruefung-2026-09-14.md`; Arbeitsdateien in
`_intern/review-v3-neu/`.

**Offen:** Endcard fehlt weiterhin; Kunde zum Hook informieren; Korrekturrunde beim Cutter.

## 2026-09-11 — Kunden-Änderung Video 3 (Intensiv Elisabeth): Analyse & Optionen

**Kunden-Feedback:** „Cardiac Arrest Center" komplett raus (Christians Teil im
Schnitt 0:19–0:31); Einstieg lieber durch jemanden aus der Pflege, damit der
Chefarzt/ärztliche Direktor das Video nicht dominiert.

**Gemacht:**
- Cutter-Schnitt `~/Downloads/vids 2/3 - Intensiv ist nicht gleich Intensiv.mp4`
  (07.08., 64,0 s, 9:16, 25 fps) per Scribe transkribiert
  (`_intern/transcribe_schnitt_v3.py` → `_intern/schnitt_v3_scribe_words.json`)
  + 1-fps-Standbilder. Christian spricht darin ~33 von 64 s (Hook, Ausstattung,
  CAC 0:20–0:32 inkl. Urkunden-B-Roll, CTA).
- **Korrektur Juli-Plan:** Den V3-Hook in FX3_9652 spricht **Christian selbst**
  (Standbilder 00:12/00:30/00:56/01:15 vom NAS-Original) — nicht eine
  Sprecherin (Diarisations-Fehlschluss). Es gibt keinen Pflege-Take des
  gescripteten Hooks; `Scriptet/` enthält nur V1-ZNA-Hooks.
- Pflege-Alternativen für Einstieg und Ausstattungs-Beleg aus 9649/9650
  zusammengestellt, dem User zur Freigabe vorgelegt.

**Entscheidung (User):** Hook bleibt bei Christian (FX3_9652, Take 2),
sonst alle empfohlenen Änderungen: Pflege (Zoran „Beruf am Limit …
hochtechnisierten Gerätschaften", 9650 · 02:29–02:41) direkt nach dem Hook,
Christian behält Ausstattung + CTA, Zorans Satz bei 0:36 auf „… mit den Ärzten
auf Augenhöhe" gekürzt. Nicht gewählte Varianten stehen als A1–A7 im Plan.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/MEK-Video3-Intensiv-Elisabeth-Schnittplan-V2.pdf`
  (4 S. = Deckblatt + Übersicht + 2 S. Video 3), Änderungsplan gegen den
  Schnitt vom 07.08. mit [NEU]/[FIX]/[CHECK]-Zeilen, Schnitt- und
  Quell-Timecodes aus Wort-Abgleich Schnitt ↔ Scribe-Cache.
- Quellen in `_intern/work/schnittplan-v3-v2/` (Übersicht, Video-MD,
  pdf_meta); Zitate/Timecodes gegen utterances.json geprüft (13 Referenzen OK).

**Offen:** Kunde informieren, dass der Hook bei Christian bleibt (sonst A2 =
Text-Headline); Herzkatheter-B-Roll bleibt (Kardiologie-Bezug ok?); Länge
jetzt ca. 48 s + Endcard statt 64 s; Export 07.08. hat keine Endcard (CHECK).

## 2026-09-01 — a7MK4-Nachtranskription; Imagefilm in eigenes Projekt ausgegliedert

**Gemacht:**
- Die 13 a7MK4-Interview-Clips (Kontext-Kamera, ~127 min) nachtranskribiert —
  Beide-Kameras-Regel vom 2026-08-07 kam nach der Juli-Session. Runner
  `_intern/transcribe_mek_a7.py`: erweitert `transcripts_index.json` additiv
  (Bestand unangetastet, Backfill `kamera_rolle: ton` auf die FX3-Einträge,
  a7-Einträge mit `kamera_rolle: kontext`). FX3 bleibt Ton-/Timecode-Referenz
  (David-Bestätigung 22.07.); Timecodes der Kameras sind nicht übertragbar.

**Entscheidungen (David):**
- Imagefilm wird ab jetzt in einem **eigenen Projekt** geführt:
  `../../Imagefilm/2026-06 Ads und Imagefilm Dreh/` (neues Konzept folgt dort,
  neuer Schnittplan dort). Der Juli-V5 in `MEK-Schnittanweisungen.pdf` bleibt
  hier als gelieferter Stand; ob das neue Konzept ihn ersetzt oder
  weiterentwickelt, entscheidet sich beim Konzept-Lesen.
- Transkript-Index, Cache und Utterances werden in die neue Charge kopiert
  (Duplikat gewollt, damit beide Chargen eigenständig sind).

## 2026-07-22 (3) — Schnittanweisungen für alle 5 Videos (PDF für Cutter)

**Entscheidungen (David, zu den 7 Abstimmungsfragen):** FX3 = Ton-Referenz ✓;
Bauchbinden meine Wahl (Martina „Pflegerische Leitung Notaufnahme" — trägt
CTA; Sandra „Fachkrankenschwester Notfallpflege"; Kunden-Verifikation offen);
Vita-Konkurrenznennungen erstmal ok; V3-Hook-Takes (FX3_9652) nutzen;
V2/V4-Hooks per KI-VO oder O-Ton; Imagefilm bleibt „Zwei Häuser" (Volkmarsen
ignorieren); Fakten-Cards frei: 39/40 Urlaubstage + 100 % Weiterbildungskosten.

**Gemacht:**
- 5 Schnittpläne gebaut (Kompaktfassung + Dossier-Langfassung mit vollem
  Take-Archiv je Video). Zitate/Timecodes programmatisch gegen utterances.json
  verifiziert (`_intern/verify_quotes.py`, 3 Läufe grün).
- 3-Agenten-Prüfpass (Standort/Compliance, Zitat-Echtheit/Sprecher,
  Cutter-Sicht): ~25 Findings eingearbeitet — u. a. Zoran-Timecode-Korrektur
  (9650 · 02:28 statt 02:34), V5-Cold-Open-Subfenster mit Zwischenruf-Warnung,
  „Notfallsanitäter" für Marien als unbelegt markiert, Ramonas „Man ist Teil
  davon"-Satz in V4 #5 gezogen, Volkmarsen-Sperrfenster in V4, Karten-Freigaben
  auf Davids Liste eingedampft (Einspringprämie + „2 Freistellungen" → offen).
- PDF gerendert und aufs Format-Budget gebracht (mehrere Kürzungsrunden):
  **13 Seiten** = Deckblatt + 1 Übersichtsseite + 5×2 + Anhang; Detail bleibt
  in den Dossier-Langfassungen.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/MEK-Schnittanweisungen.pdf` (13 Seiten)
- `video-{1..5}-*.md`, `01-projekt-grundlagen.md`,
  `99-anhang-ungenutztes-material.md` (u. a. Bonus-Ad-Idee „Vom Marketing in
  die Pflege"/Zoran), `Dossier/video-{1..5}-*-lang.md`
- `_intern/{pdf_meta.json, verify_quotes.py}`

**Offen (im PDF je Video als OFFEN geführt):** Kundenfreigaben (Vita-Nennung,
Notfallsanitäter Marien, „Dr."-Titel, Card-Zahlen Elisabeth, Einspringprämie,
„Liebe sei Tat", Drohnen, Endcard-Linkziel); Hook-Sprecherin FX3_9652
identifizieren; KI-VO-Stimme V4; Ziellängen/Formate sind Annahmen (Ads 9:16
60–80 s, Imagefilm 16:9 90–120 s); Musik.

## 2026-07-22 (2) — Schnittplan-Workflow: Transkription + Analyse

**Gemacht:**
- Footage auf NAS verortet (`…/01_Projekt-2xAds1xImagefilm_24.06.26/03_Medien/
  01_Footage/`), bereits team-vorsortiert (B-Roll/Interviews/Scriptet pro
  Standort) → Schnittplan-Workflow statt Footage-Sortierer. Originale nur gelesen.
- Standort-Regel von David: strikte Trennung der zwei Häuser, NUR Imagefilm (V5)
  darf mischen. In `_intern/script_structured.json` als Hauptregel verankert
  (+ m/w/d-Pflicht, Keine-MFA-Veto V3/V4, Platzhalter-Zahlen-Warnung).
- Tonkamera-Check: beide Kameras haben Ton (anders als WLC); FX3 = Ton-/
  Timecode-Referenz (deckt überall mehr ab), A7MK4 = parallele B-Cam. 25
  FX3-Clips transkribiert (Scribe + Diarisation, 133 min, 21.444 Wörter; 1
  Timeout-Retry Sodan-Clip). Utterances gebaut (1.022 mit Timecodes).
- Alle Transkripte durchgearbeitet: Wer-ist-wer, Abdeckung pro Video, Tabus.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/00-material-und-standort-uebersicht.md` (Analyse +
  offene Fragen), `_intern/{script_structured.json, transcribe_mek.py,
  transcripts_index.json, utterances.json, work/transcripts_md/}`

**Kern-Erkenntnisse:**
- Standort 1 = Elisabeth (Dreh 24.06.), Standort 2 = Marien (Dreh 02.07.) —
  per O-Ton bestätigt. 12 Personen identifiziert; Ordner „Sodan" = **Zoran**.
- Hooks: V1 gescriptet ✓ (Scriptet-Ordner), V3 gescriptet ✓ (in FX3_9652,
  Sprecherin unklar), V2/V4 ✗ nicht gedreht.
- V3 stärkstes Material (Cardiac Arrest Center, Impella, Chefarzt Ex-Uniklinik);
  V4-Emotions-Peak „wieder selbst atmen" fehlt als wörtlicher O-Ton.
- Kundenvertreterin war beim Dreh dabei — Vorgaben im Material: keine
  Konkurrenz-Nennung, Station nicht schlechtreden, Naming „Elisabeth
  Krankenhaus Kassel"/„Marienkrankenhaus" für Einzelhaus-Videos, 2 gesperrte
  Passagen (Martina „gibt nichts, was es nicht gibt"; Zoran Präsentkorb).

**Offen (warten auf David, dann Pläne bauen):** FX3-Bestätigung; Rollen
Martina/Sandra (beide „pflegerische Leitung ZNA"); Konkurrenz-Nennung in
Vita-Kontext; V3-Hook-Sprecherin; V2/V4-Hook-Lösung; Volkmarsen vs. „Zwei
Häuser"; Freigabe Fakten-Cards (39/40 Urlaubstage, 100 % Weiterbildungskosten).

## 2026-07-22 — Projekt angelegt

**Gemacht:** Kundenordner, Projekt und Charge angelegt; Konzept-PDFs (Google-Sheets-Exporte) gelesen, umbenannt und einsortiert.

**Geliefert:** `Material/Konzept/` mit drei PDFs:
- `Konzept Übersicht (5 Videos).pdf` — Titel, Zielgruppe, Pain pro Video
- `Konzept Detail (Hooks, Inhalt, Shotlisten).pdf` — Hooks A/B/C, Inhaltsbögen, Shotlisten für den Dreh
- `Testimonial-Fragen.pdf` — Interviewfragen pro Rolle (V1–V5)

**Entscheidungen:**
- Projektname „Recruiting" — das Paket umfasst 5 Videos: V1 ZNA Elisabeth, V2 ZNA Marien, V3 Intensiv Elisabeth (Hightech-Kardiologie), V4 Intensiv Marien (Weaning), V5 Imagefilm „Zwei Häuser, ein Versprechen". Der Imagefilm bleibt in diesem Projekt, da primär Employer Branding und Teil desselben Konzepts/Drehs.
- Charge „2026-07 Erster Dreh" nach Studio-Konvention.

**Offenes:**
- Dreh steht noch aus — Interview-WAVs und Footage folgen nach Drehtag.
- Benefit-Zahlen im Konzept sind laut Dokument Platzhalter — vor Schnitt/Animation final klären.
- CTA-Endcards: „(m/w/d)" am Berufstitel nicht vergessen (gilt für alle Recruiting-Kunden).
