# Protokoll — Förch / Vertrieb Kaufbeuren / 2026-07 Kaufbeuren Dreh

## 2026-08-07 — Erstlauf: Footage-Analyse + Schnittplan (komplett)

**Gemacht:**
- Charge angelegt; Skript-PDFs (3 Google-Sheets-Exporte: 9 Werbeanzeigen AD-1–5 + VB-1–4, Strategie-Tabelle) nach `Material/Konzept/` verschoben, strukturiert in `_intern/script_structured.json`.
- Ton-Kamera verifiziert: **a7MK4** (~3 dB über FX3, Konvention Juni-Dreh); FX3 startet ~3–5 s früher.
- 4 Interviews transkribiert (ElevenLabs, 16.088 Wörter, 0 Fehler): Adriano (AD Kfz, 3,5 J.), Franzi (AD Bau, 1. Jahr), Friedrich Riesch (Regionalleiter seit 04/26), Thomas Mix (Shopverkäufer seit 2004). Utterances mit Timecodes gebaut (420).
- B-Roll-Bestand erfasst: 196 Clips / 21 benannte Ordner / ~72 min (4 Clips „Aussortiert" = gesperrt).
- Analyse `00-material-analyse.md`: Wer-ist-wer, Abdeckung (9 Videos ↔ 4 Personen), B-Roll-Mapping, Sperrliste.
- 9 Schnittpläne gebaut (Kompakt + Dossier-Langfassung je Video), Zitate + Timecodes maschinell gegen utterances.json verifiziert (`_intern/check_zitate.py`, 0 Probleme nach 7 Verbatim-Korrekturen).
- PDF gerendert: `Ergebnisse/O-Ton-Pläne/Foerch-Vertrieb-Kaufbeuren-Schnittanweisungen.pdf` (20 Seiten; Budget je Video ≤ 2 S. eingehalten).

**Geliefert:** PDF (20 S.) + 00-Analyse + 9× video-N-*.md + 99-Anhang + Dossier (9 Langfassungen).

**Entscheidungen (NIRO, im Plan markiert):**
- Franzi = AD-1-Hauptstimme (einzige Erst-Jahr-Person); Thomas trägt alle 4 VB-Videos allein.
- VB-3 wie gescriptet nicht baubar (kein Handwerks-Quereinsteiger interviewt) → Plan als Option B „Praxiswissen zählt" (Thomas als Zeuge); Option A = Nachdreh.
- Take-Exklusivität festgelegt (Kannibalisierungs-Sperren, s. Übersichtsseite).
- Alle Gehalts-/Provisions-O-Töne gesperrt bis Kundenfreigabe (Cap-frei-Schiene war kundenseitig gestrichen; Friedrich sagt wörtlich „ungedeckelt").

**Offen (für David/Kunde):**
- Bündel-Widerspruch Skript vs. Strategie: AD-1 + VB-1 ein Video oder zwei?
- AD-2: Förch-Go nach Sichtung des Grobkonzepts.
- VB-3: Option A (Nachdreh) vs. B (Umbau, empfohlen).
- Mini-Nachdrehs empfohlen: AD-5 Zuhause-Shots (~30 min), VB-2 Uhr-/Tür-Details (~15 min).
- Nachnamen Franzi/Adriano, Person „Leiter am PC" (vermutl. Jens), „IKKL"-App-Name, Endcard-URLs + Berufstitel (m/w/d), Format/Ziellängen (Annahme 9:16, 35–50 s).

## 2026-08-07 (Nachtrag) — Korrektur Ton-Kamera: FX3 statt a7MK4

**Davids Korrektur:** FX3 hat den Ton zu 100 % (Mikro); die a7IV hört den Interviewer besser (Raum) → ab jetzt IMMER beide Kameras transkribieren (Regel in WORKFLOW-Schnittplan.md + Memory verankert).

**Gemacht:**
- 4 FX3-Dateien zusätzlich transkribiert (a7MK4 blieb als Kontext-Transkript; Index-Feld `kamera_rolle`: ton|kontext; jetzt 8 Clips / 822 Utterances).
- Alle Quellen + Timecodes der 9 Kompaktpläne auf FX3 umgestellt — **wortgenau** über Wort-Zeitstempel aus dem Scribe-Cache (`_intern/remap_to_fx3.py`), nicht per Offset-Schätzung. Offset a7→FX3 real: Adriano ~+7 s, übrige ~+2–3 s.
- 22 Zitat-Stellen an den FX3-Wortlaut angepasst (FX3-ASR hört teils besser: „Umkreis von Memmingen", das „um" bei Friedrichs Fürsorge-Take; Widerspruchs-Stellen für Gehör-Check markiert: „Vertrieb haben/Vertriebler", „grundlegend/Grundnormen", „rund um Gebäude/Kaufbeuren").
- Sperrlisten (Gehalt, Störer, Verhörer) auf FX3-Zeiten umgeschrieben; Anhang remappt; Dossiers mit Umrechnungs-Hinweis versehen (bleiben a7-basiert).
- Checker verschärft (`check_zitate.py`): wortgenaue FX3-Verifikation von Zitat + Timecode (±4 s) — 0 Probleme. PDF neu gerendert (20 S., Budgets ok).

**Erkenntnis für künftige Drehs:** Ton-Kamera nie aus Pegel raten (a7 war lauter — das war der Raum, nicht das Mikro); pro Dreh bei David erfragen. Störer (Kunden-Zurufe, Killerfliege) sind auf der FX3-Lav-Spur deutlich leiser als auf der a7 — trotzdem prüfen.
