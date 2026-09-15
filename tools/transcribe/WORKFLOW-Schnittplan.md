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
   Datei kürzen (nicht das Layout quetschen); fast leere Schlussseiten
   vermeiden (letzte Bullets zusammenziehen).
   **Zitat-Prüfung darf nicht leerlaufen:** `verify_plans.py` muss die Zitate
   auch erkennen (Zähler „Zitat-Fragmente" > 0). Die Pläne schließen Zitate mit
   ASCII-`"` — Regex `„([^“”"]+)["“”]`, Vorlage `projects/Steuerkanzlei Ludwig x
   Taxodia/…/_intern/verify_plans.py` (mit Leerlauf-Schutz und Gegentest).
9. **Protokoll.** `Protokoll.md` im Chargen-Ordner fortschreiben.

## Format-Standard Cutter-Plan (verbindlich, Quelle: David-Feedback WLC)

- **Umfang: Lesbarkeit vor Seitenbudget** (User 14.09.2026, ersetzt die alte
  2-Seiten-Grenze): Rappold (60-s-Ads) „3–4 Seiten pro Video" ok, Taxodia
  (5-min-Erklärvideo) „so viele Seiten wie nötig, nicht über 20" — das ganze
  PDF bleibt bei max. 20 Seiten, **+ genau 1 Übersichtsseite** vorne. Keine
  Transkript-Wände — Langfassung und Clip-Funde gehören ins Dossier.
- **Quellenangabe IMMER dreiteilig:** `<Person> (<Rolle/Position>) ·
  <Ordner>/<Datei> · <von–bis>` — nie nur der Dateiname. Gerade wenn
  Ordnername ≠ echte Rolle (WLC: Ordner „Lagerleiter", Person Gruppenleiter).
  Hooks: `Hooks/<Ordner>/<Datei> · <von–bis> (<wer/was>)`.
- **Personen-Namen in JEDER Spalte, nie nackte Dateinamen** (David, 2026-07-23,
  MAN): sichtbare Personen mit Name (Rolle), wo identifiziert; nicht
  identifizierbare Personen als „n. n." kennzeichnen, nie stillschweigend
  weglassen. Keine ungeprüften Namens-Behauptungen — im Zweifel „vor Nutzung
  im Clip verifizieren" vermerken.
- **Bild-Spalte = „Bild-Vorschlag" nur mit Motiven** (User 14.09.2026, generell):
  keine B-Roll-Clip- oder Ordner-Verweise, der Cutter wählt den B-Roll selbst.
  Interview-Bild (Kamera-A/B) und Ton-Quellen bleiben konkret; Sperr- und
  Datenschutzhinweise zu einzelnen Clips bleiben als Warnung; die Clip-Funde
  der Sichtung stehen im internen Dossier.
- **Captions/Einblendungen** bringen neue, website-belegte Fakten und
  wiederholen nie das Gesagte (User 14.09.2026); Beleg im Kommentar nennen.
- **Sektionen je Video:** Titel [Zuordnung] · Ziel & Story (max 3 Sätze inkl.
  Ziellänge) · Material (erlaubt/verboten, 3–4 Zeilen) · Ablauf/Szenen-Tabelle
  (# | Szene | O-Ton wörtlich | Quelle | Bild-Vorschlag | Sound | Caption | **Kommentar**)
  · Alternativen & Abweichungen (Bullets) · Offen (Bullets).
- **Kommentar-Spalte (NIRO)** ist Pflicht: Take-Wahl, Warnungen (Regie im Take,
  Artefakte), Schnitt-Hinweise — Telegrammstil, max ~15 Wörter.
- **EINE Ablauf-Zeile pro Aussage/O-Ton — NIE mehrere Aussagen in einer Zeile
  bündeln** (David, 2026-07-23, MAN Wartezimmervideo). Kapitel/Szenen mit mehreren
  O-Tönen bekommen Unterzeilen (2a/2b …), jede mit eigener Quelle, eigenem Bild
  und eigenem Kommentar. Lieber wird das Dokument länger; das Seiten-Budget darf
  dafür eher ausgereizt werden als Zeilen zusammenzulegen.
- **Zitate wörtlich und vollständig** (inkl. Versprecher; User 14.09.2026:
  volle Zitate schlagen Kürzung). `[…]` nur für echte Innenschnitte — die
  Quelle nennt dann mehrere Bereiche mit „+". Keine Szene der Langfassung
  streichen.
- Alle Beats müssen abgedeckt sein; kritische Warnungen (Tabus, gesperrte
  Clips, Kannibalisierungs-Sperren zwischen Videos) müssen die Kürzung überleben.
