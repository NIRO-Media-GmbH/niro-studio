# Protokoll — SW Projektentwicklung / Einfamilienhaus und Smartino / 2026-07 Dreh

## 2026-08-11

- Auftrag (David): alle Dateien transkribieren, kein Konzept-Skript vorhanden.
  B-Roll (auch mit Hintergrund-Gerede) herausfiltern — nur gescriptete Szenen
  und Interviewszenen mit echtem Sprech-Content zählen. Danach sortieren.
- Material auf NAS: `NIRO Productions/01_Projekte/01_Kunden/SW Projektentwicklung
  & Dienstleistung GmbH/02_Projekte/04_Projekt-21.07.26-Einfamilienhaus und
  Smartino/03_Medien/01_Footage/`
  - Kamera-A FX3: 40 Clips (~22 min), alle mit Audio
  - Kamera-B A7iv: 46 Clips (~65 min), alle mit Audio — lange Takes hier
  - Mavic: 2 Clips, Avata: 1 Clip — **keine Audiospur** → automatisch B-Roll
- Onboarding-/Konzept-Ordner auf NAS sind leer (bestätigt: kein Skript).
- Transkription: ElevenLabs Scribe mit Diarisation über beide Kameras
  (86 Clips), Index in `_intern/transcripts_index.json`.
- Befund: 95 Videodateien insgesamt (auch .MOV bei den Drohnen). KEINE
  Interviews — ausschließlich gescriptete Erklär-/Ad-Takes: Projekt
  Gottwolfshausen, Bifazial (2 Multi-Cam-Paare FX3+A7iv), BauSolar-Modul,
  Flachdach (Multi-Cam), Hotel Smartino (= „Smartino": Hotel in Schwäbisch
  Hall, Gewerbe-Referenz), E-Auto/Wallbox-Ads, Recruiting Elektromeister.
- Sortiert auf NAS nach `01_Footage/sortiert/`: 25 Takes in 7 Themen-Ordner,
  4 Regie-Besprechungen (90_), 66 B-Roll (99_, inkl. Drohnen + LRF-Proxies).
  Alle 95 verschoben, 0 verloren; Undo: `_intern/_verschiebe_log.jsonl`.
- Geliefert: `Ergebnisse/Sortierung/zuordnungsplan.md` + `transkripte.md`.
- Sonderfall: `Kamera-A FX3/FX3_0253.MP4` war NAS-seitig SMB-gelockt →
  hash-verifizierte Kopie liegt in `sortiert/02_Bifaziale-Solarmodule/`,
  Original-Duplikat löschen, sobald Lock weg (ggf. NAS-Neustart).
- Offen: Sprecher-Name (Steffen/Fabrice/Flo fallen im Ton), Ton-Kamera für
  den Schnitt bestätigen, m/w/d bei Recruiting-Endcards beachten.

### Schnittplan (gleiche Session, 2026-08-11)

- Utterances gebaut (`_intern/utterances.json`, 52 Clips / 680 Utterances).
- Geliefert: `Ergebnisse/O-Ton-Pläne/SW-Projektentwicklung-Schnittanweisungen.pdf`
  (16 Seiten: 1 Übersicht + 7× 2 Seiten) plus die MDs; intern zusätzlich
  `00-material-analyse.md` (nicht im PDF).
- Struktur: V1 Gottwolfshausen · V2 Hotel Smartino (2-Teiler) · V3 Bifazial ·
  V4 BauSolar-Modul · V5 Flachdach · V6 Ad-Set E-Auto/Wallbox (7 Ads) ·
  V7 Ad-Set Recruiting Elektromeister (5 Ads). Ohne Kundenskript = Grobkonzept.
- Sprecher identifiziert: **Fabrice** (Anrede im Ton, a7_0127 00:58 / a7_0092
  03:58) — Nachname + Schreibweise noch bei SW bestätigen.
- Verifiziert per Skript (`_intern/verify_plans.py`, `verify_speaker.py`):
  52 Quellen-Zeilen, alle Zitate wortgenau im Timecode-Bereich belegt,
  alle Bereiche sprecher-rein (kein Regie-Ton von Jan).
- **Fund 1 — Rechenfehler gesperrt:** a7_0125 · 00:25–00:32 „fast 55.000 kWh
  eingespart"; korrekt sind 45.000 (70.000 − 25.000). Zeile nicht senden.
- **Fund 2 — Zahlen-Falle Bifazial:** FX3-ASR hört „25 %", A7iv „fünf und
  zwanzig". Gesprochen ist ein Bereich → **5–20 %** ist richtig, nie 25 % texten.
- **Fund 3:** Härtetest-Modul ≠ gezeigtes Modul (a7_0110 · 02:10–02:52) —
  Formulierung „unsere vorherigen Videos" bewusst offen lassen, Passage sperren.
- Ton-Empfehlung bei den 3 Multi-Cam-Paaren: **FX3** (A7iv-Spur windig,
  viele Verhörer) — von David freigeben lassen.
- Offen an SW: Stelle(n) im Recruiting eindeutig klären (Büro-Elektromeister
  vs. Teamleiter), CI/Endcard + Formular-URLs, Freigabe Hotel-Smartino-Nennung,
  Strompreis 35 ct als Rechengrundlage, 17 MA / 160 Projekte bestätigen.
