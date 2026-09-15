# Protokoll — WTN / Imagefilm / 2026-06 Erster Dreh

Projekt-Kontext: B2B-Imagefilm (separate Spur, kein Recruiting) aus dem
Dreh vom 09.06.2026 — gleiche Dreh-Quelle wie „5x Ads", eigenes Projekt
(Entscheidung David, 2026-08-03). Rohmaterial:
`NIRO-SSD-02/WTN/01_Projekt-Dreh_09.06.26/03_Medien/01_Footage/`.

## 2026-08-03 — Projektanlage + Schnittplan-Start

**Gemacht:**
- Projektstruktur angelegt; Imagefilm-B2B-Konzepte (3 Google-Sheets-PDFs)
  aus `5x Ads/…/Material/Konzept/` hierher verschoben (lagen dort, weil das
  Projekt noch nicht existierte); Onboarding-PDF kopiert (bleibt auch im
  Ads-Projekt, projektübergreifend).
- Schnittplan-Workflow gestartet (WORKFLOW-Schnittplan.md).

**Entscheidungen:**
- Chargen-Name „2026-06 Erster Dreh" nach Drehdatum 09.06.2026 (die
  Ads-Charge desselben Drehs heißt „2026-07 Erster Dreh", benannt nach
  Bearbeitungsbeginn — bewusst nicht übernommen).
- Ton-Kamera laut David „meistens FX3, nicht sicher ob immer" → pro
  Ordner per Audio-Level-Check verifizieren, bevor transkribiert wird.

**Gemacht (Fortsetzung, gleiche Session):**
- Konzept strukturiert → `_intern/script_structured.json` (IF-Beats, Hinweise,
  Tabus, Pflicht-Personen/-Bereiche aus Onboarding S. 5+7-8).
- Ton-Kamera je Ordner per Audio-Level verifiziert: 81xx-Setups (Sprechpart02,
  Beck, Hüttner, Weber) → **a7MK4**; Produktionsleiter → C0686; Sprechpart01 →
  C8092 (einzige Kamera). „Meistens FX3" traf hier nicht zu.
- 6 Ton-Kamera-Clips transkribiert (ElevenLabs, ~36 min) →
  `_intern/transcripts_index.json`; Azubi-/Ausbilder-Interviews bewusst
  ausgelassen (Recruiting-Content). Utterances gebaut → `_intern/utterances.json`
  (259 Utterances, einzige Quelle für Zitate + Timecodes).
- B-Roll inventarisiert (Quer 664/Hoch 115 Dateien) und auf IF.3-Kette gemappt.
- Analyse-Übersicht → `Ergebnisse/O-Ton-Pläne/00-analyse-uebersicht.md`.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/00-analyse-uebersicht.md` (Abstimmungsdokument)

**Erkenntnisse:**
- Sprechpart01/02 = gescriptete B2B-Kernsätze (Fertigungstiefe / Full-Service),
  mehrere Takes, Julia Schilpp gibt Regie; Sprecher-Identität unklar (tbd).
- Roland Hüttner (Techn. Vertrieb Umformwerkzeuge) = B2B-Kernstimme, in den
  5 Ads unverbraucht; inkl. „alles aus einer Hand"-Satz (07:03–07:13) und
  freigegebenem CTA-Take (09:11–09:21). Markus heißt Markus Beck.
- Ads-WAV-Transkript Roland hatte den falschen Sprecher exportiert (nur
  Interviewer) — MP4-Transkription dieser Charge ersetzt das.
- Scribe-Verhörer: WTN→„BTN", PECM→„PCM"/„PDDCM", Wetzel→„Wessel".

**Entscheidung (Nachtrag 2026-08-03):** Kannibalisierung Ads↔Imagefilm
freigegeben — alles Vorhandene darf doppelt genutzt werden (David). Damit ist
Wetzels Maschinenpark-Satz (C0686 · 02:34–02:58) wieder Top-Kandidat.

## 2026-08-03 (Fortsetzung) — Planbau nach Davids Antworten

**Entscheidungen (David):** Sprechpart-Sprecher = die im Skript vorgesehenen
Vertriebsleute (Zuordnung Beck/Hüttner per Clip-Folge + Inhalt, Verifikation
am Bild durch Cutter) · Rückgrat = Sprechparts als Gerüst + Interview-Akzente
(NIRO-Empfehlung) · CTA = kombiniert (Hüttner-O-Ton 09:11–09:21 + Text-
Endcard) · Hook = A (value-led).

**Claim-Check wtn.de:** „Kaum ein Unternehmen der Branche kann so viel für
seine Kunden tun wie wir" (wörtlich) + „Full-Service-Supplier" + „30 Jahre
WTN" belegt → Overlays darauf umgestellt. „Technologien, die der Wettbewerb
nicht hat" und „Geprüft bis in den Mikrometer" unbelegt → gestrichen.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/Dossier/video-1-imagefilm-b2b-lang.md` (Langfassung,
  Zitate/Timecodes/Sprecher gegen utterances.json verifiziert; dabei
  SP01-Take-Bewertung korrigiert: kein Take dokumentiert freigegeben,
  T3 empfohlen, T5/T4 Alternativen)
- `Ergebnisse/O-Ton-Pläne/video-1-imagefilm-b2b.md` (Cutter-Kompaktplan)
- `Ergebnisse/O-Ton-Pläne/01-projekt-grundlagen.md` (Übersichtsseite, 1 PDF-Seite)
- `Ergebnisse/O-Ton-Pläne/WTN-Imagefilm-Schnittanweisungen.pdf` (5 Seiten)

**Format-Abweichung (dokumentiert):** Video-Kapitel = 3 PDF-Seiten statt 2.
Grund: 11 Ablauf-Beats mit 7 wörtlichen O-Tönen; Eine-Zeile-pro-O-Ton-Regel
hat laut WORKFLOW-Schnittplan Vorrang vor dem Seitenbudget („lieber länger
als Zeilen zusammenlegen"); Datei ~6,3k Zeichen < 6.500er-Ausnahmegrenze.
Alle weiteren Kürzungen gingen an Zitat-Substanz oder kritische Warnungen.

**Offen (an Kunde/Cutter):** Schleifen-Freigabe [CHECK] · PECM-B-Roll sichten
[CHECK] · Sprechpart-Sprecher am Bild verifizieren · Uwe Traub fehlt im
Material · QS-Caption- + Endcard-Wortlaut · Ziellänge (~100–120 s) bestätigen.

**Offen (Gate — vor Planbau mit David klären, s. 00-analyse ➊–➏; ➋ entschärft
sich durch die Freigabe nicht):**
- ➊ Wer spricht Sprechpart01/02 (Uwe Traub?)
- ➋ Storyline-Rückgrat: Sprechparts als Gerüst (NIRO-Empfehlung) vs. rein Interview
- ➌ CTA: Text-Endcard vs. gesprochener Roland-CTA
- ➍ Hook-Variante A/B/C
- ➎ Schleifen-Tabu (Onboarding „Schleifen 1+2") vs. IF.3-Kette — Kunde
- ➏ Claim „Technologien, die der Wettbewerb nicht hat" gegen wtn.de belegen
  oder abschwächen — Kunde/Websitecheck
- B-Roll-Lücken: PECM (Pflicht!), HSC, CNC-Fräsen quer, Dreh-/Fräszentrum (1 Clip),
  CAD/Konstruktion nur hochformat
