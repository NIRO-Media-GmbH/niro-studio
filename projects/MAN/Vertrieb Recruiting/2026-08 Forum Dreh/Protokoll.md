# Protokoll — MAN Vertrieb Recruiting / 2026-08 Forum Dreh

## 2026-08-15 — Schnittplan-Session (Start)

**Auftrag:** „Schnittplan für MAN Forum" (David). Material auf NIRO-SSD-03
(`/Volumes/NIRO-SSD-03/MAN Forum`), Dreh 04.08.2026 im MAN Truck/Bus Forum.

**Klärungen David:**
- Ton-Kamera = **FX3** (a7MK4 = Kontext-Kamera) — erfragt, nicht geraten.
- Ablage: `projects/MAN/Vertrieb Recruiting/2026-08 Forum Dreh/`.

**Material:**
- 4 Interviews (Dual-Cam FX3 + a7MK4): Viktoria — Verkäuferin (2 Takes/Kamera,
  ~47 min), Esta — Verkaufsleitung (~27 min), Roman — Verkäufer (~24 min),
  Trainee Programm (~11 min + 50-s-Nachschuss nur a7MK4).
- B-Roll: 15 thematische Ordner, 71 Clips (alle FX3, einsortiert).
- Dazu 66 unsortierte a7MK4-Clips in `A7iv/` (0623–0688) — vermutlich
  Zweitkamera-B-Roll, noch niemandem zugeordnet.

**Konzept:** 2 Google-Sheets-PDFs (in `Material/Konzept/`), 4 Videos:
1. Frauen im Truck-Verkauf — Role Models (Multi-Voice, 2 Frauen + ggf. Trainee)
2. Produktpalette — What We Really Sell (niedrigste Prio, Fahraufnahmen aus Bestand)
3. VBA — A Day in the Life (POV-Hook-Option, Probefahrt aus Bestand)
4. Trainee Sales — Dein Einstieg (Premium-Testimonial)
Strukturiert nach `_intern/script_structured.json` (inkl. Tabus: keine
Vertragsbestandteile in V1, Master-Voraussetzung in V4 nicht explizit).

**Gemacht:** Chargen-Struktur angelegt, Konzept-PDFs einsortiert,
`_intern/transcribe_forum.py` (nach Förch-Kaufbeuren-Vorlage), Transkription
aller 11 Interview-Dateien (beide Kameras, David-Regel 2026-08-07): 11/11 ok,
1.355 Utterances. Wer-ist-wer: „Esta" = **Esther Ludewig** (Verkaufsleitung
Transporter, 12 J.), Victoria **Wader** (Truckverkäuferin), **Roman Retsch**
(TGE-Kommunal, 26) — Roman gab ZWEI Interviews (Verkäufer + Trainee-Programm,
retrospektiv als Absolvent).

**Abstimmung David:** V3 (VBA) hat keinen eigenen Protagonisten → Victoria
führt, Roman stützt · Vergütungs-O-Töne + Mallorca-Spruch MIT ⚠️-Warnung in
die Pläne (Einbau erst nach MAN-Freigabe) · Romans Ausbildungs-Aufstiegs-Takes
nutzen, MAN klärt Master-Voraussetzung.

**Geliefert (`Ergebnisse/O-Ton-Pläne/`):**
- `MAN-Vertrieb-Recruiting-Schnittplan.pdf` — 10 Seiten (Deckblatt + 1
  Übersicht + 4 Videos à exakt 2 Seiten, pypdf-verifiziert)
- 4 Kompakt-Pläne + 4 Dossier-Langfassungen + `00-material-analyse.md` +
  `01-projekt-grundlagen.md`; B-Roll-Inventar `_intern/broll_inventar.csv`
- Alle Zitate + Timecodes gegen `_intern/utterances.json` verifiziert
  (Nachprüf-Lauf korrigierte 5 Timecodes vor Render)

**Entscheidungen/Sperren:** Milchsammler-Story exklusiv V4 („der erste
Roman") · Victorias Tagesablauf exklusiv V3 · Palette-Aufzählung exklusiv V2 ·
Protagonisten-Vetos respektiert (Kranwagen, „8–17 Uhr", Übergabe, Einarbeitung,
Esther-Scherze, „Weiterbildung lange nix") · Ford-Bashing + „Statistik-
Abischnitte" raus · ASR-Verhörer dokumentiert („blidd", „Mensch Oma",
„Bisse"-CTA).

**Offen:** MAN-Freigabe Vergütung/Mallorca · Master-Frage V4 · Endcard-Titel
(m/w/d) je Video · MAN-Bestand (Fahraufnahmen V2, Probefahrt V3, Werkstatt V4)
· IAA-Passage nur bei Launch vor der Messe · 66 unsortierte A7iv-Clips sichten
(POV-Hook V3, eTruck-Details, „zwei Verkäuferinnen") · PDF-Versand an Cutter.

## 2026-09-01 — 5. Video (Gesamtvideo) für Probecutter — Konzept + Guide-PDF

**Auftrag (Jan, 01.09.):** 5. Video aus dem Forum-Material als eigenständiges
Gesamtvideo (kein Themen-Fokus); Dopplung zu V1–V4 ausdrücklich erlaubt, V5
steht für sich. Zweck: Probecutter-Bewertung (1 Tag, Premiere), Ergebnis soll
trotzdem kundenverwendbar sein. Schnittplan diesmal als ausführliche
Erklär-PDF (Lese-Anleitung, Premiere-Setup, S-Log3-Conversion, Untertitel,
Musikvorschläge, Export, FAQ) — bewusste Einmal-Abweichung vom
2-Seiten-Standard, ausdrücklich KEIN neuer Workflow.

**Geliefert:** 3 Konzeptvorschläge (A „Das ist der MAN Vertrieb" —
Team-Gesamtvideo in Kapiteln · B „5 Gründe für den Vertrieb bei MAN" —
Zähler + Keyword-Captions · C „Ein Tag im MAN Vertrieb" — chronologisch),
Empfehlung A. Konzept-Entscheid + Endcard-/Musik-Logistik bei David angefragt.

**Festgelegt:** Compliance-Sperren gelten auch für V5 (Vergütungs-O-Töne +
Mallorca erst nach MAN-Freigabe — kommen gar nicht erst in den
Probecutter-Plan; Protagonisten-Vetos, Ford-Passage, 40-Stunden-Teil bleiben
draußen; IAA-Passage raus wegen Verfallsdatum). Exklusiv-Sperren zwischen
V1–V4 binden V5 nicht (Ansage Jan, 01.09.).

**Entscheidungen (Jan):** Konzept A („Das ist der MAN Vertrieb",
Team-Gesamtvideo in Kapiteln) · KEIN Voice-Over (Empfehlung angenommen;
steht so im FAQ des Guides) · Grafiken/Inserts/Endcard nicht
Cutter-Aufgabe — Probecutter kommt dafür auf Jan zu (zeigt den
Animations-Workflow persönlich) · Musik sucht der Probecutter selbst auf
Artlist (Zugang via Jan).

**Geliefert (`Ergebnisse/O-Ton-Pläne/Probecutter/`):**
- `MAN-Gesamtvideo-Probecutter-Guide.pdf` — 20 Seiten A4 quer: Deckblatt +
  Inhaltsverzeichnis (Teil-Farben, Seitenzahlen, PDF-Lesezeichen) + 12
  Kapitel in 3 Teilen (A Vorbereitung: Auftrag/Plan-Lesen/Material/Premiere ·
  B Schnitt: 22-Zeilen-Plan + Sperren-Liste · C Finishing:
  S-Log3-Color/Untertitel/Grafiken→Jan/Musik/Export) + FAQ; Erklärkästen
  (Gut zu wissen / Achtung / Tipp / An Jan wenden), Du-Form.
- V5-Plan: Hook + 5 Kapitel + Schluss/CTA, ~2:00–2:30, alle 22
  Zitate/Timecodes gegen `_intern/utterances.json` verifiziert
  (`_intern/probecutter/verify_v5.py`, 22/22 OK), Sprecherfolge
  max-2-Regel geprüft; Langfassung `Dossier/video-5-gesamtvideo-lang.md`.
- Einmal-Renderer `_intern/probecutter/render_probecutter_pdf.py`
  (Zwei-Pass fürs Inhaltsverzeichnis; Standard-Tool unangetastet,
  bewusst KEIN neuer Workflow).

**Nebenbefund NAS:** Forum-Material liegt komplett auf
`NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/
02_Projekte/06_Vertrieb Frauen München/03_Medien/01_Footage/` (301 GB) —
die 66 a7MK4-Clips sind dort bereits in die B-Roll-Motiv-Ordner einsortiert
(erledigt offenen Punkt vom 15.08.; NAS-Namen `a7MK4_20260804_XXXX`).
Technik verifiziert (ffprobe + Sony-XML): beide Cams UHD 2160×3840 vertikal
(rotation=90), 25p, H.264 10-Bit 4:2:2 ~140 Mbit/s, PCM 48 kHz,
s-log3-cine / s-gamut3-cine.

**Offen:** Übergabe-Kopie für den Probecutter ziehen (301 GB) + PDF
mitgeben · Artlist-Zugang bereitstellen (Jan) · Endcard-Berufstitel
„(m/w/d)" weiter bei MAN offen · optional Bewertungsraster für den
Probetag.

## 2026-09-07 — Review der V1-Schnitte (Leon Deissmann, Frame.io)

**Auftrag (Jan):** Frame.io-Share prüfen, dann die vier V1-Schnitte gegen
Konzept + Schnittplan reviewen. Frame.io-Share lädt im Browser ohne Login
(Abspielen, Screenshots, Kommentare lesen); für Ton/Transkript wurden die
Originale nach `Material/Videos V1/` geholt.

**Methode:** Scribe-Wort-Transkript je Schnitt (`_intern/review-v1/transcribe_v1.py`),
Frames 1 fps + Kontaktbögen + Einzelframes (`_intern/review-v1/frames/`),
EBU-R128-Messung, alle Zitate in `_intern/utterances.json` verortet.

**Geliefert:** `Ergebnisse/Review/MAN-Vertrieb-V1-Review-2026-09-07.md`
(Gesamtbild, MUSS/SOLLTE/KANN, Ist-Ablauf je Video mit Timecodes + Quellen,
Technik-Tabelle, Klärungen).

**Kern-Befunde:** V3 öffnet mit dem Mallorca-Spruch (⚠️ nur nach MAN-Freigabe) ·
V4-Endcard falsch („Verkäufer:in" statt Trainee) · V3-Insert Victoria über
Roman-Shot (0:12) · Pegel 11 LU auseinander (V2 −25,7 LUFS, V3 −14,4 LUFS bei
0,0 dBTP) · V2 erzählt die Milchsammler-Auslieferung (Sperre, exklusiv V4) ·
Schnitte 47–61 s statt 60–120 s → V1 Victoria-Mono (Esther 3,5 s), V3 ohne
Tagesablauf und mit Kaltakquise-Bild statt Beziehungs-Sales, V2 ohne
„Pull statt Push", V4 ohne Programm-Struktur/Praxis-Beat · Untertitel als
2–3-Wort-Fragmente, keine Takeaway-Captions, Endcard nicht im MAN-Web-Stil.
Compliance sonst sauber (kein Gehalt, kein Ford, V4-Aufstieg ohne
Ausbildungs-Bezug, m/w/d überall).

**Offen:** Schreibweisen Bader/Wader, Resch/Retsch, „seit 2023"-Insert
(nicht im Interview belegt) · Mallorca-Freigabe · Endcard-Wortlaut V4 ·
Längen-/Format-Entscheidung · Musik-Mix per Ohr · Feedback an Leon
(Wortlaut/Form noch nicht abgestimmt).
