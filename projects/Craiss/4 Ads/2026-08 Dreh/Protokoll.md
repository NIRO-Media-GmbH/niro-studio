# Protokoll — Craiss Generation Logistik / 4 Ads / Charge 2026-08 Dreh

## 12./13.08.2026 — Material-Analyse, Interview-Sortierung, Schnittplan

**Gemacht**

- Material auf dem NAS gesichtet: 24 Interview-Clips (3 h 14 min, Dual-Cam
  FX3 + a7MK4) und 189 B-Roll-Clips in 15 Ordnern (~2 h) + 7 Drohnen-Files.
- Ton-Kamera bei David erfragt → **FX3** (bestätigt 12.08.).
- Alle 24 Interview-Clips mit ElevenLabs Scribe transkribiert (beide Kameras,
  David-Regel 2026-08-07). Drei parallele Worker gegen denselben Cache, sonst
  hätte der Lauf über zwei Stunden gedauert.
- **Dual-Cam-Paare verifiziert:** Die FX3-Uhr läuft rund 8 Minuten vor der
  a7MK4-Uhr. Die Paare wurden über den Inhalt zugeordnet, nicht über die
  Uhrzeit — Timecodes sind zwischen den Kameras nicht übertragbar.
- **Interviews sortiert:** 48 Dateien (24 MP4 + 24 XML) in 8 Personen-Ordner
  „Name - Beruf" verschoben, alle per `os.rename` sauber durch, kein SMB-Lock.
  Die Grob-Ordner `GF/` und `HR/` sind aufgelöst. Undo-Log in
  `_intern/_verschiebe_log.jsonl`.
- Konzept (4 Google-Sheet-Tabs) nach `Material/Konzept/` gelegt und nach
  `_intern/script_structured.json` strukturiert.
- Alle 8 Interviews per Fan-out-Agenten ausgewertet → Zitat-Inventare mit
  Timecodes, Sperren, Fakten-Checks.
- **Schnittplan gebaut:** 16-seitiges PDF `Craiss-Schnittanweisungen.pdf`
  (1 Übersichtsseite + 5 Videos + Anhang B-Roll/Nachdreh).
- **59 Quellenangaben verifiziert** — jedes Zitat sitzt wortgenau im
  angegebenen Timecode-Bereich (`_intern/verify_plans.py`).

**Geliefert**

- `Ergebnisse/O-Ton-Pläne/Craiss-Schnittanweisungen.pdf` (16 S.)
- `Ergebnisse/O-Ton-Pläne/00-material-und-abweichungen.md` (intern)
- `Ergebnisse/O-Ton-Pläne/Dossier/o-ton-index-personen-lang.md` (intern)
- Sortierte Interview-Ordner auf dem NAS

**Entscheidungen (David, 13.08.)**

- **K4 Block 1 = Michael Craiss**, Block 2 = Eva. K5 bleibt strikt ohne
  Geschäftsführung.
- **K1 und K2 werden als B-Roll-Filme neu gedacht** — Bildebene trägt, Ton
  kommt aus VO, Captions und Fahrer-O-Tönen.

**Vier Konzept-Abweichungen**

1. **Klaus-Martin Andreas hat nicht gedreht** — kein einziger Clip. Er sollte
   K4 Block 1 tragen.
2. **Michael Craiss wurde doch interviewt** (28 min) — das Konzept schloss ihn
   aus, weil er am geplanten Drehtag 29.06. in Berlin war. Gedreht wurde am 10.08.
3. **K1 und K2 wurden nicht als Sprech-Szenen gedreht** — kein Carsten Alt,
   kein Liviu, kein Fahrer-Hook. Die komplette Dialogebene fehlt.
4. **Zwei Konzept-Kernsätze existieren nicht:** Opa Didis 95-/30-Jahre-Satz
   (er sagt „über fünfzig Jahr", auf beiden Kameras) und Thomas Baranskis
   Multi-Voice-Abbinder (er sagt im ganzen Interview kein Grußwort).

**Offen / beim Kunden**

- Klarname „Opa Didi" und Nachname Eva für die Bauchbinden.
- „seit 95 Jahren auf der Straße" freigeben — Michael Craiss unterscheidet:
  Gründung 1931, Spedition „seit über fünfzig Jahren".
- Beweis-Card-Zahlen freigeben; ~1000 Mitarbeiter gilt für die **Gruppe**.
- Rückmeldefrist: Konzept 24 h, Set-Ansage 48 h, gesprochen „zeitnah" —
  ohne Freigabe kommt keine Zahl ins Bild.
- „Herr Rauschberger" — Schreibweise und wer tatsächlich zurückruft.
- Endcard: URL, CTA-Wortlaut, Craiss-CI.
- Ob Kundenlogos (DHL/Deutsche Post) im Bild sein dürfen.
- Freigaben Dritter: Albert Craiss, Jakubs Bruder, Jan Machutas Familie.

**Anmerkungen**

- Videos 3 und 4 haben je 16 Beats und laufen deshalb auf 3 PDF-Seiten statt 2.
  Das ist bewusst so: eine Zeile pro Aussage geht vor dem Seiten-Budget
  (Format-Standard). Übersichtsseite und die übrigen Videos halten das Budget.
- **Die B-Roll wurde nicht transkribiert** (Absprache: nur Ordnernamen
  auswerten). Ob in `Neuer LKW Fahrer einlernen` und `Servicewerkstatt`
  verwertbarer Ton liegt, ist damit offen — 30 Minuten Sichtung würden
  K1 deutlich belastbarer machen.
- Ein Nachdreh unter 15 Minuten (Thomas 2 Sätze, Opa Didi 1 Satz, ein
  Fernverkehrsfahrer) würde K3 vollständig machen — Details im PDF-Anhang.
