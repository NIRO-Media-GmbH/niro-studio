# NIRO Transcribe — Design

*Datum: 2026-07-01 · Status: freigegeben (Konzept), vor Umsetzungsplan*

## 1. Ziel

Ein chat-gesteuertes Werkzeug, das aus mehreren Interview-Audiodateien (WAV) und
einem Skript (PDF) automatisch pro Ziel-Video eine dramaturgisch und
marketingpsychologisch sinnvolle Auswahl von O-Tönen zusammenstellt und als
lesbares Dokument mit von–bis-Timestamps ausgibt — damit die passenden Stellen in
DaVinci Resolve schnell gefunden werden.

**Oberste Anforderung:** Ergebnis vor Skript-Treue. Die Qualität und Reihenfolge
der ausgewählten Aussagen muss stimmen, weil der Betrieb voll automatisch ist.

## 2. Betriebsmodell

- **Voll automatischer Batch-Ablauf**, gesteuert über die Claude-App (diese Session).
- **Claude Opus 4.8 ist Orchestrator UND „Gehirn"**: Transkript-Abgleich,
  Aussagen-Zerlegung und kreative Auswahl passieren direkt in der Session (kein
  separater LLM-API-Aufruf). Der Nutzer kann im Chat jederzeit nachjustieren.
- **Transkription** läuft über Hilfsskripte (ElevenLabs Scribe + Whisper lokal).
- **Datei-Weg:** Nutzer legt die WAVs per Finder in den Projektordner und sagt im
  Chat Bescheid; PDF und Briefs kommen über den Chat.

## 3. Projektstruktur (pro Dreh)

```
<projekt>/
├── audio/            # .wav Dateien (vom Nutzer per Finder abgelegt)
├── skript.pdf        # das Skript
├── briefs.yaml       # ein Brief pro Ziel-Video + globale Einstellungen
├── cache/            # gecachte Transkripte (Scribe + Whisper) je Datei-Hash
└── output/           # fertige Dokumente (pro Video + Gesamt-Übersicht)
```

## 4. Pipeline (6 Stufen)

### Stufe 1 — Einlesen & Zuordnen
- `audio/` scannen.
- **Dateiname-Interpretation per LLM**, tolerant gegen Varianten (Trenner,
  Schreibweisen, mehrteilige Namen/Bereiche). Ergebnis je Datei:
  `{ typ, bereich, name, quelldatei }`. Das Muster ist NICHT garantiert
  (`Typ_Bereich_Name` ist nur der Normalfall).
- Die **erkannte Interpretation wird sichtbar ins Dokument geschrieben**, damit
  Fehlinterpretationen sofort auffallen.
- **PDF → Rahmendaten**: Kernbotschaften, Zielgruppe, Tonalität, Themen, ggf.
  vorgegebene Struktur.
- **`briefs.yaml`** einlesen (siehe Abschnitt 5).

### Stufe 2 — Transkription (je WAV)
- **ElevenLabs Scribe** → Transkript A: wortgenaue Timestamps + Sprechererkennung.
- **Whisper (lokal, whisper.cpp)** → Transkript B: unabhängige Zweitmeinung.
- Ergebnisse werden **gecacht** (Schlüssel = Datei-Hash) → erneute Läufe kosten
  keine erneute Transkription.

### Stufe 3 — Abgleich (je WAV)
- Opus vergleicht A & B und erzeugt **eine** saubere, korrigierte Fassung.
- **Scribe-Timestamps sind der Anker** (präziser); Whisper dient zur Korrektur von
  Wortfehlern/Lücken.

### Stufe 4 — Aussagen-Zerlegung (je WAV)
- Opus zerlegt das Transkript in einzelne, zitierfähige **Aussagen**
  (in sich geschlossene Gedanken-/Sinneinheiten).
- Je Aussage: `von–bis`, Person, Bereich, Quelldatei, Themen-Label.
- Ergebnis: ein **Aussagen-Pool** über alle Interviews.

### Stufe 5 — Kreative Zuordnung & Reihenfolge
- Pro Ziel-Video: Opus wählt aus dem Pool die passendsten Aussagen, ordnet sie
  dramaturgisch, respektiert Brief-Vorgaben (Person/Moderation, Länge,
  Durchmischung) und Skript-Rahmen.
- **Dramaturgie:** Opus wählt das Framework passend zum Brief/Inhalt
  (z. B. AIDA, Problem-Agitate-Solve, Hero's Journey) und begründet die Wahl.
  Ein Brief kann eine Struktur fest vorgeben (überschreibt die Auto-Wahl).
- **Wiederverwendung:** Standard = **exklusiv** (jede Aussage global nur einem
  Video). Pro Durchlauf umschaltbar auf Mehrfachnutzung.
- **Bei „exklusiv": globaler Planungsschritt**, der die Aussagen über ALLE Videos
  gemeinsam verteilt (statt gierig nacheinander), damit nicht das erste Video alle
  starken O-Töne wegnimmt.

### Stufe 6 — Dokument-Ausgabe
- **Pro Video** ein lesbares Markdown-Dokument (optional PDF).
- Eine **Gesamt-Übersicht** über alle Videos.

## 5. Brief-Format (`briefs.yaml`)

Der Nutzer beschreibt Briefs formlos im Chat; Opus überführt sie in diese Struktur.

Pro Video:
- `titel` / Nummer
- `fokus` — Botschaft/Kernaussage
- `person` — feste Moderator:in **oder** „durchmischen"
- `ziel_laenge` — z. B. ~90 Sek
- `dramaturgie` *(optional)* — feste Struktur-Vorgabe
- `tonalitaet` *(optional)*

Global (einmal pro Dreh):
- `wiederverwendung` — `exklusiv` (Standard) | `mehrfach`
- `anzahl_videos`

## 6. Ergebnis-Dokument (Format)

Pro Video:
- **Kopf:** Video-Titel, gewähltes Framework + Begründung, geschätzte Länge.
- **Tabelle:** `# | Person | Bereich | Quelldatei | von–bis | Wortlaut | Warum hier`.
- **Roter Faden:** kurze Dramaturgie-Notiz.

Gesamt-Übersicht:
- Welche Person in welchem Video, Auslastung des Pools, ungenutzte starke Aussagen.

## 7. Qualitätssicherung (weil voll automatisch)

1. **Begründungspflicht** — jede Auswahl & Position wird begründet (Spalte „Warum hier").
2. **Kritischer Zweit-Durchgang** — nach dem ersten Entwurf Selbstprüfung gegen:
   Flow sinnvoll? Redundanzen? Emotionaler Bogen? Klarer Einstieg & Abschluss?
   Passt es zu Brief & Skript? → Überarbeitung.
3. **Timestamp-Verifikation** — jede von–bis-Zeit wird gegen das Transkript geprüft;
   keine erfundenen Zeiten (Vertrauens-Knackpunkt für DaVinci).

## 8. Technik-Stack

- **Sprache:** Python (Hilfsskripte für Transkription; Opus orchestriert & denkt).
- **Transkription:** ElevenLabs Scribe (API-Key nötig) + whisper.cpp (lokal, Mac).
- **PDF-Parsing:** pdfplumber / pypdf.
- **Gehirn:** Claude Opus 4.8 (diese Session — kein separater Key).
- **Ausgabe:** Markdown, optional PDF-Export.
- **Cache:** transkript-Ergebnisse je Datei-Hash.

## 9. Einmaliges Setup

- ElevenLabs-API-Key hinterlegen.
- whisper.cpp lokal installieren (inkl. deutschem Modell, z. B. large-v3).

## 10. Bewusst NICHT im Scope (YAGNI, erste Version)

- DaVinci-Import (EDL/XML/SRT) — später ergänzbar.
- Separates GUI/CLI zum Selbststarten — Steuerung läuft über den Chat.
- Video-Datei-Mapping — es wird nur mit Audio (WAV) gearbeitet; die Quelldatei im
  Dokument reicht zum Wiederfinden.

## 11. Offene Punkte für die Umsetzung

- Genaues Whisper-Modell/-Setup (Geschwindigkeit vs. Genauigkeit auf dem Mac).
- Format für sehr lange Interviews (Chunking beim Abgleich, um Kontext zu schonen).
- Umgang mit mehreren WAVs pro Person (Zusammenfassen im Pool).
