# Workflow — Schnittplan für Cutter (Voll-Durchlauf, Claude in der Session)

Auslöser: **„Schnittplan: <Kunde>/<Projekt>[/<Charge>]"** — Roh-Videomaterial
(MP4-Footage nach Dreh) wird transkribiert und zu Cutter-tauglichen
Schnittanweisungen (PDF) nach Konzept-Script verarbeitet.
(Abgrenzung: „Video-Auswahl" = Interview-WAV-Pipeline in `WORKFLOW.md`;
„Footage sortieren" = Clips verschieben in `WORKFLOW-Footage.md`.)

Voraussetzung: `.env` (ELEVENLABS_API_KEY) geladen, ffmpeg im PATH,
Material-Quelle (NAS/SSD) gemountet. **Originale werden NIE verändert —
nur lesen.** Erst-Referenz: WLC Recruiting (`projects/WLC/Recruiting/2026-07
Erster Dreh/`, Session-Protokoll 2026-07-08/09).

## Ablauf

1. **Konzept lesen & strukturieren.** Script/Konzept (Sheet/PDF) in
   `_intern/script_structured.json` bringen: `{"videos":[{"nr","titel",
   "standort/…","rows":[{"id","typ","text"}]}]}`, typ ∈ scripted|interview|visual.
   Projekt-Regeln (z. B. Standort-Trennung, Wording-Tabus, Kunden-Vetos) als
   `hinweise`-Block mit aufnehmen.
2. **Selektiv transkribieren.** NUR gesprochene Ordner (Interviews/Hooks/
   Reporter…), keine B-Roll/Drohne/Proxies/„Nicht verwenden". Welche Kamera
   die Ton-Kamera ist, IMMER bei David erfragen — nie aus Pegel/Vor-Charge
   raten, das wechselt pro Dreh (WTN: a7MK4 · MAN: FX3 · Förch 06/26: a7MK4 ·
   Förch Kaufbeuren 07/26: FX3). Bei Dual-Cam-Interviews **beide Kameras
   transkribieren** (David-Regel 2026-08-07): Ton-Kamera liefert Zitate +
   Timecodes für den Cutter; die Zweit-Kamera hört den Interviewer besser
   (Raum-Mikro) → Kontext/Wer-ist-wer, nie Tonquelle. Runner nach Vorlage
   `projects/Förch/Vertrieb Kaufbeuren/…/_intern/transcribe_vertrieb.py`
   (Feld `kamera_rolle`: ton|kontext; nutzt `transcribe_clip`, Cache in
   `_intern/cache/`, Index `_intern/transcripts_index.json` mit Feldern
   standort/kategorie/person).
3. **Utterances bauen.** `venv/bin/python scripts/build_utterances.py
   "<Chargen-Ordner>"` → `_intern/utterances.json` (Timecodes pro Utterance,
   Sprecher-getrennt). Das ist die einzige Quelle für Zitate + Timecodes.
4. **Analyse & Abstimmung.** Wer-ist-wer klären (Selbstvorstellungen!),
   Material↔Script-Abdeckung, Konflikte (z. B. Person an mehreren Standorten,
   nie gedrehte Szenen) → als Übersicht nach `Ergebnisse/O-Ton-Pläne/00-…md`
   und mit David abstimmen, bevor Pläne gebaut werden.
5. **Pläne bauen (Langfassung).** Pro Video ein detaillierter Plan; danach
   IMMER verifizieren: (a) Zitat-Echtheit + Timecodes + Sprecher-Reinheit
   gegen utterances.json, (b) Projekt-Regeln/Compliance, (c) Cutter-Tauglichkeit
   & verpasste bessere Takes. Langfassungen nach
   `Ergebnisse/O-Ton-Pläne/Dossier/video-N-…-lang.md` (internes Arbeitsdokument).
6. **Cutter-Kompaktfassung.** Aus jeder Langfassung `video-N-<slug>.md` im
   Format unten — **das ist der Kunden-/Cutter-Standard (David, 2026-07-09)**.
7. **Übersichtsseite** `01-projekt-grundlagen.md` (EINE PDF-Seite): NAS-Pfad,
   Projekt-Hauptregel, Video-Tabelle (Nr/Titel/Zuordnung/Protagonisten/Länge),
   Personen-Tabelle (Person/Rolle/Ordner), Kamera-/Ton-Regeln, Tabus, zentrale
   offene Punkte. Optional `99-anhang-…md` für starkes ungenutztes Material.
8. **PDF rendern.** `_intern/pdf_meta.json` anlegen (titel, untertitel, stand,
   warnbox = Projekt-Hauptregel, kapitel_farben, dateiname), dann
   `venv/bin/python scripts/render_schnittplan_pdf.py "<Chargen-Ordner>"`.
   **Seitenzahl je Kapitel prüfen** (pypdf) — Budget unten einhalten, sonst
   Datei kürzen (nicht das Layout quetschen).
9. **Protokoll.** `Protokoll.md` im Chargen-Ordner fortschreiben.

## Format-Standard Cutter-Plan (verbindlich, Quelle: David-Feedback WLC)

- **Umfang-Budget: max. 2 PDF-Seiten pro Video** (A4 quer; Richtwert
  < 6.000 Zeichen je MD, Video mit vielen Beats < 6.500 nur wenn nötig)
  **+ genau 1 Übersichtsseite** vorne. Keine Transkript-Wände — Detail
  gehört in die Dossier-Langfassung, nicht in die Cutter-PDF.
- **Quellenangabe IMMER dreiteilig:** `<Person> (<Rolle/Position>) ·
  <Ordner>/<Datei> · <von–bis>` — nie nur der Dateiname. Gerade wenn
  Ordnername ≠ echte Rolle (WLC: Ordner „Lagerleiter", Person Gruppenleiter).
  Hooks: `Hooks/<Ordner>/<Datei> · <von–bis> (<wer/was>)`.
- **Personen-Namen in JEDER Spalte, nie nackte Dateinamen** (David, 2026-07-23,
  MAN): Auch die Bild-/B-Roll-Spalte nennt Ordner + sichtbare Personen mit Name
  (Rolle), wo identifiziert; nicht identifizierbare Personen als „n. n."
  kennzeichnen, nie stillschweigend weglassen. Nur ohne Personen im Bild reicht
  Ordnername + Bildbeschreibung. Keine ungeprüften Namens-Behauptungen —
  im Zweifel „vor Nutzung im Clip verifizieren" vermerken.
- **Sektionen je Video:** Titel [Zuordnung] · Ziel & Story (max 3 Sätze inkl.
  Ziellänge) · Material (erlaubt/verboten, 3–4 Zeilen) · Ablauf/Szenen-Tabelle
  (# | Szene | O-Ton wörtlich | Quelle | Bild | Sound | Caption | **Kommentar**)
  · Alternativen & Abweichungen (Bullets) · Offen (Bullets).
- **Kommentar-Spalte (NIRO)** ist Pflicht: Take-Wahl, Warnungen (Regie im Take,
  Artefakte), Schnitt-Hinweise — Telegrammstil, max ~15 Wörter.
- **EINE Ablauf-Zeile pro Aussage/O-Ton — NIE mehrere Aussagen in einer Zeile
  bündeln** (David, 2026-07-23, MAN Wartezimmervideo). Kapitel/Szenen mit mehreren
  O-Tönen bekommen Unterzeilen (2a/2b …), jede mit eigener Quelle, eigenem Bild
  und eigenem Kommentar. Lieber wird das Dokument länger; das Seiten-Budget darf
  dafür eher ausgereizt werden als Zeilen zusammenzulegen.
- **Zitate wörtlich** (inkl. Versprecher), lange Zitate mit `[…]` mittig
  kürzen — Anfang/Ende wörtlich, damit der Cutter In/Out findet. Keine Szene
  der Langfassung streichen, nur komprimieren.
- Alle Beats müssen abgedeckt sein; kritische Warnungen (Tabus, gesperrte
  Clips, Kannibalisierungs-Sperren zwischen Videos) müssen die Kürzung überleben.
