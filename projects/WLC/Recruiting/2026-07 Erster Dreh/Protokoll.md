# Protokoll — WLC / Recruiting / 2026-07 Erster Dreh

## 2026-07-08 — Projekt angelegt, Script gecheckt

**Gemacht:**
- Projektstruktur angelegt: `projects/WLC/Recruiting/2026-07 Erster Dreh/`.
- Konzept-Sheet „WLC Wuerth Logistik - Recruiting-Videos" (Google Sheet)
  lokal gesichert: XLSX-Komplettkopie + alle 4 Tabs als CSV
  (Übersicht, Grobkonzepte, Feinkonzepte, Drehplan) in `Material/Konzept/`.
- Script geprüft: 6 Videos (3 Azubi, 2 Fachkraft, 1 Employer-Brand),
  Feinkonzepte mit Szenen, Captions, Sound und CTA-Endcards vollständig.

**Geliefert:**
- `Material/Konzept/WLC-Recruiting-Videos-Script.xlsx`
- `Material/Konzept/{Übersicht,Grobkonzepte,Feinkonzepte,Drehplan}.csv`
- `Material/Konzept/WLC Wuerth Logistik - Recruiting-Videos.gsheet` (Link zum Original)

**Auffälligkeiten im Script (beim Check gefunden):**
- Video 6 Hook C: Caption-Spalte enthält noch das verworfene Wording
  „…die Würth nach Deutschland trägt" — laut Anmerkung ist der
  Deutschland-Frame tabu (Cornelia, Meeting 12.5.). Sprechtext ist schon
  korrigiert („Gemeinsam gestalten wir die Logistik bei WLC").
- Video 2 Hook B: Personen-Spalte sagt noch „Azubi mit Kaffeebecher",
  das Kaffee-Klischee wurde aber durch den Besen-Frame ersetzt.

**Schnitt-relevante offene Punkte (aus dem Script):**
- Video 1 Hook B: Wording „langweilig" vs. „lame" vs. „uninteressant" —
  am Drehtag mehrfach aufgenommen, Entscheidung fällt im Schnitt.
- Video 1 Hook C / Video 2 Hook C: Trend-Sound-Auswahl kurz vor
  Live-Gang fixieren (Niro-Schnitt).
- Video 2, Szene 2.7: Zahlen für Beweis-Card offen (Übernahmequote via
  Yannik, Azubi-Zahl via Ausbildungsleitung) — mind. 2 konkret, sonst Card weglassen.
- Video 4/5: Hochregal-Höhe 30 m vs. 36 m ungeklärt → Typo-Hooks betroffen.
- Video 5 Hook B: News-Schlagzeilen rechtefrei oder mit Quellen-Vermerk —
  vor Schnitt klären.
- Video 5, Szene 5.4: Konzern-Freigabe öffentliche Zahlen offen
  (u. a. 850 vs. 750+ Mitarbeiter).
- Video 6: zwei Cut-Optionen liefern (mit + ohne VO-Schluss).

**Offen:**
- ~~Rohmaterial-Speicherort noch nicht verortet~~ → NAS gefunden (s. unten).
- Schnitt-Start: Reihenfolge der Videos mit David festlegen.

## 2026-07-08 (2) — Transkription + Standort-Analyse

**Gemacht:**
- Rohmaterial verortet: NAS `NIRO Productions/01_Projekte/01_Kunden/WLC …/
  02_Projekte/01_Projekt-Dreh18.05 & 20.05/03_Medien/01_Footage/`
  (Adelsheim = Dreh 18.05., Kupferzell = 20.05.). Originale nur gelesen —
  nichts verschoben/umbenannt (Vorgabe David).
- 41 FX3-Clips transkribiert (ElevenLabs Scribe + Diarisation, ~122 min;
  nur Interviews/Hooks/Reporter, ohne B-Roll/Drohne/A7MK4/„Nicht verwenden").
  Cache in `_intern/cache/`, Index `_intern/transcripts_index.json`.
- Feinkonzept strukturiert: `_intern/script_structured.json`.
- Standort-Matrix + Szenen-Abdeckung erstellt.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/00-material-und-standort-uebersicht.md`
- `_intern/transcripts_index.json`, `_intern/script_structured.json`,
  `_intern/transcribe_wlc.py`

**Entscheidungen (David):**
- Standort-Trennung strikt pro Video; **Video 6 = bestätigte Ausnahme** (darf mischen).
- Nur FX3 transkribieren (A7MK4 ohne Mikro; iPhone-Clips im Besen-Ordner ausgelassen).

**Kern-Erkenntnisse:**
- Personen: Hamid (Azubi 1, A'heim), Torben Kempf (Azubi 2, A'heim; spricht
  vermutlich auch Kupferzell-Stapler-Hooks), Sebastian Franke (Teamleiter
  Halbautomaten, A'heim, Quereinsteiger), Jana + Reporterin (A'heim),
  Marvin (Gruppenleiter, K'zell, Hero V4), Sina Osterhag (Ausbildungsleitung, K'zell).
- Kundenseite bestätigt im Material selbst: „kleines Lager"-Hook nur für
  Kupferzell ausspielen (Adelsheim-Lager alt+groß).
- Script-Lücken: V1 Hook A/B + 1.1 + 1.4 nicht gedreht; V5 Insolvenz-Story
  existiert nicht; V2: Sina (2.6) liegt in Kupferzell → Ersatz Sebastian.
- Bonus-Material (Kupferzell): Sina-Gehalts-Hook („1.300 € im Monat als
  Azubi") + Torben-Stapler-Hooks → Kandidat für eigenes Azubi-Video Kupferzell.

**Offen:**
- Torben-Frage: darf dieselbe Person in Videos beider Standorte auftauchen
  (Material ist getrennt, Person nicht)?
- V2-Beweis-Card: Übernahmequote fehlt konkret (nur „sehr viele").
- Hochregal-Höhe 30 vs. 36 m; Zahlen-Freigaben Konzern (V5).
- Schnitt-Reihenfolge + Start-Video mit David.

## 2026-07-08 (3) — Schnittanweisungen für alle 6 Videos (PDF für externe Cutter)

**Gemacht:**
- Utterance-Index mit Timecodes gebaut (`_intern/utterances.json`, 1.077
  Utterances über 40 Clips, aus Scribe-Wort-Timestamps).
- Multi-Agent-Durchlauf (30 Agenten): je Video Schnittplan → 3 unabhängige
  Prüfer (Zitat-Echtheit gegen Timecodes, Standort-Reinheit + Wording-Tabus,
  Cutter-Tauglichkeit/verpasste Upgrades) → Finalisierung. 122 Findings
  eingearbeitet. Eigene Stichproben (Standort-Greps, 2 Timecode-Proben) sauber.
- PDF-Renderer gebaut (fpdf2, A4 quer, Szenen-Tabellen mit NIRO-Kommentarspalte,
  Standort-Farbcodierung, Warnbox-Deckblatt).

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/WLC-Schnittanweisungen.pdf` (75 Seiten:
  Deckblatt + Grundlagen + 6 Video-Kapitel + Anhang)
- `Ergebnisse/O-Ton-Pläne/video-{1..6}-*.md` (Quell-Markdown der Kapitel)
- `01-projekt-grundlagen.md` (Cutter-Onboarding), `99-anhang-ungenutztes-material.md`
- `_intern/{build_utterances,render_pdf}.py`

**Entscheidungen (David):**
- 6 Videos (kein Bonus-Video); Script-nah, Abweichung erlaubt wenn erheblich
  besser; Standort-Trennung fix; Kommentarspalte erwünscht.
- Bonus-Material (Sina-Gehalts-Hook, Torben-Stapler-Serie) in Anhang
  dokumentiert statt verworfen.

**Erkenntnisse aus dem Durchlauf:**
- Drohnen-Clips sind standortneutral benannt (`DJI_*.MOV`) — Trennung nur über
  Ordner/Nummern: Adelsheim DJI_0332–0344, Kupferzell ab DJI_0367 (in PDF dokumentiert).
- Zahlen-Konflikt im Sina-Interview (25 vs. 22 Azubis, FX3_8773 bei 720,9/748,8 s)
  → Beweis-Card V2 mit abgesichertem Wording, Klärung vor Animation nötig.
- V1/V2 teilen sich Hamid+Torben → Kannibalisierungs-Sperren in beiden Plänen.

**Offen (in PDF als „Offene Punkte" je Video geführt):**
- Sina/Yannik: Azubi-Zahlen + Übernahmequote; Hochregal-Höhe 30/36 m;
  Konzern-Zahlen-Freigaben; Trend-Sounds kurz vor Live-Gang; Uhrzeit-Caption V3.

## 2026-07-13 — Skript-Abgleich Video 4 (Schnitt läuft)

**Gemacht:** Auf Davids Frage den Schnittplan Video 4 gegen das Feinkonzept
(script_structured.json) abgeglichen — Szene für Szene. Keine Dateien geändert.

**Ergebnis:** Struktur skriptnah; 3 echte Abweichungen (Hook-VO nie
eingesprochen → Caption-only; 4.6-Zitat nie gesagt → „Augenhöhe"-Ersatz;
Abbinder #10 neu), 2 Korrekturen (Splash „CREW-MODDER"→Gruppenleiter,
4.5-Caption wegen Fördermittel/AKL gestrichen). Hook B/C ungenutzt
(Hook C blockiert: Hochregal-Höhe offen). Details s. Antwort im Chat /
`video-4-fachkraft-aufstieg.md` Abschnitt „Alternativen & Abweichungen".

**Entscheidung (David):** Hook A wird KI-generiert (Kling 3.0 Multishot auto),
damit kein WLC-Lager zu sehen ist — Hook zeigt bewusst ein generisches,
leicht angestaubtes Fremd-Lager (Kontrast zu WLC ab Cold-Open). 3 Prompt-
Varianten geliefert (Multishot 3-Shot, POV ohne Gesicht, Single-Mood-Shot);
9:16, 10 s, Captions weiterhin aus dem Schnitt. Szene #7 (Equipment-Salve)
bleibt echtes B-Roll — Tech-Claims nicht per KI faken.
Zusätzlich: Hook-VO wird per ElevenLabs generiert (Script-Text „Wenn du seit
Jahren denselben Gang läufst … und dich fragst, ob's das war."), ruhiger
männlicher Sprecher; Caption bleibt trotzdem (Sound-off-Viewing). Damit ist
die Abweichung „Hook-VO nie eingesprochen" behoben.

**Video 5 (Schnitt gestartet):** Hero-Landing wird KI-generiert (Kling,
Rückwärts-Trick: echter Frame aus FX3_8756 als Start-Frame, Sprung nach oben
durchs Deckenfenster, im Schnitt reversed) — Prompts geliefert.

**Entscheidung (David): Adelsheim-Ausnahme für Video 5** — Standort-Trennung
für V5 aufgehoben (wie V6). Grund: Script-Hero (Insolvenz-Quereinsteiger) nie
gedreht, Kupferzell hat nur Marvin als Fachkraft-Stimme. Plan
`video-5-wachstum.md` aktualisiert: Sebastian Franke fest als neue Szene 5b
eingeplant (FX3_8585 ca. 01:29–01:38 Quereinstieg, +9 s → Zielfassung ≈ 88 s,
Einsparhebel Sz 6/Sz 10; 2 Alternativ-Takes; V2-Take 156,5–176,3 s gesperrt),
AKL-Cross-Cut + Adelsheim-Drohne (DJI_0332–0344) freigegeben, Auflagen:
Hook-Targeting bleibt NUR Kupferzell (Kunden-Vorgabe), Adelsheim-Bilder nicht
unter Marvins „hier"-Aussagen, Hochregal-Card weiter ohne Zahl (30/36 offen).
Offen: job_details_263 auf beide Standorte prüfen (Endcard „+ Adelsheim").

## 2026-07-09 — PDF auf Cutter-Format umgestellt + Workflow verankert

**Gemacht (David-Feedback):**
- Alle 6 Pläne auf Kompaktformat gekürzt: **max 2 PDF-Seiten pro Video +
  1 Übersichtsseite** (vorher 75 Seiten, jetzt 15). Langfassungen bleiben
  intern erhalten in `Ergebnisse/O-Ton-Pläne/Dossier/` (…-lang.md).
- Quellenangaben durchgehend dreiteilig: `Person (Rolle) · Ordner/Datei ·
  von–bis` (u. a. wegen Ordner „Lagerleiter" ≠ Rolle Gruppenleiter).
- Übersichtsseite neu: Video-Tabelle, Personen-Tabelle, Standort-Regel,
  Kamera/Tabus/offene Punkte — eine Seite.
- Workflow dauerhaft verankert: neuer Trigger **„Schnittplan: <Kunde>/<Projekt>"**
  in CLAUDE.md → `tools/transcribe/WORKFLOW-Schnittplan.md` (Format-Standard
  dokumentiert); generische Skripte `tools/transcribe/scripts/
  {build_utterances,render_schnittplan_pdf}.py` (Meta via `_intern/pdf_meta.json`);
  Feedback-Memory `cutter-schnittplan-format` angelegt.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/WLC-Schnittanweisungen.pdf` (15 Seiten: Deckblatt,
  Übersicht, 6×2 Video-Seiten, Anhang) — gebaut über den generischen
  Workflow-Weg (verifiziert identisch).
- `_intern/pdf_meta.json` (PDF-Konfiguration für Re-Renders).

**Hinweis:** Zwischenzeitlicher API-Ausfall beim ersten Kürzungs-Lauf —
4/6 Dateien waren geschrieben, V3+V4 im zweiten Lauf nachgezogen; alle
6 final geprüft (Seitenzahlen per pypdf).

## 2026-07-15 — Schnitt-Start Video 6

**Gemacht:** David startet den Schnitt von Video 6 (Employer-Brand).
Schnitt-Start-Briefing aus Plan + Dossier-Langfassung erstellt: zwei
Cut-Optionen (A mit VO ~45 s / B ohne VO ~35 s), VO-Entscheidung als
zentrale offene Frage, Abhängigkeit Beweis-Card-Animation (NIRO Motion),
harte Warnungen (Deutschland-Tabu, FX3_8740 gesperrt, Regenfenster ab
11:16, Bauchbinde „Gruppenleiter"). Keine Plan-Dateien geändert.

**Offen (Schnitt-relevant):** VO-Weg (Nachvertonung Marvin empfohlen —
falls ja, Session früh organisieren, deckt auch Hook B + sauberen CTA ab);
Liste der 12 Standorte + Würth-Logo-Freigabe für Map-Animation;
Drohnen-Freigabe (Plan B: Container); CTA-Wortlaute Meta/LinkedIn.

**Motion-Graphics-Paket V6 gebaut (NIRO Motion, neuer Kunde `wlc`):**
- WLC-Client im Motion-Tool angelegt: `tools/motion/src/clients/wlc/`
  (brand.json aus offiziellen CD-Richtlinien 2025: Würth Rot #CC0000,
  Schwarz/Weiß, Grau-Stufen als Layoutfarben; Fonts Wuerth Global
  Extra Bold Cond/Bold/Book als lokale TTFs; Logo weiß + Team-Wappen
  nach `public/clients/wlc/`). Quelle CI: `Material/02_CI_Richtlinien/
  WLC_Corporate Design Richtlinien 2025.pdf` + `01_Logo & Schriftarten/`.
- 4 Kompositionen (`recruiting-v6`, 9:16 4K, 25fps, Studio-Ordner „WLC"):
  1. `WlcV6-WortBattle` — Antonym-Overlay mit Alpha, 6 Paare à 6s-Block
     (3s/Wort, Davids Vorgabe statt 4→3→2-Kadenz aus dem Plan),
     Red-Sweep-Transition (Rot + Grau-Blade, weiße Kante, −12°) in 1s-Slots
     zwischen den Blöcken → 41s gesamt („bis ~42s Vergleiche").
  2. `WlcV6-Trio` — „ALLES LAGER. ALLES WIR. ALLES HIER." Overlay (8s),
     Punkte in Würth-Rot.
  3. `WlcV6-BeweisCard` — Map + Pin-Drops + „SEIT 1996." (4s).
     **Standort-Recherche (Web, 2026-07-15): wlc-online.com nennt 6
     Standorte (Adelsheim HQ, Kupferzell, Neuenstadt a. K., Kemmeten/
     Künzelsau, Öhringen, Crailsheim — alle Hohenlohe/Heilbronn-Franken);
     Intralogistik-BW-Profil: „3 Hauptstandorte + 7 Außenlager" (=10);
     Konzept sagt „12" → Zahl online NICHT belegbar, VOR Live-Gang mit
     Cornelia klären (Endcard-Sub „12 STANDORTE" betroffen!).**
     Design angepasst: 6 echte Pins (Geo-Positionen) + Lupen-Inset, das
     die Regional-Cluster-Region vergrößert (bundesweite Streuung wäre
     faktisch falsch gewesen). Render ersetzt durch
     `V6-beweis-card-6-standorte-belegt.mov`.
  4. `WlcV6-CtaEndcard` — schwarz, Logo, Headline, Sub, roter CTA-Balken
     „BEWIRB DICH JETZT.", Hashtags (5s).
- Technik: Font-Gate (delayRender bis Würth-TTFs geladen, sonst
  Fallback-Font im Render), echte Font-Gewichte statt Faux-Bold.
- Renders (ProRes 4444 mit Alpha) nach `Ergebnisse/Renders/`:
  V6-wort-battle-alpha.mov, V6-trio-alpha.mov,
  V6-beweis-card-ENTWURF-platzhalter-pins.mov, V6-cta-endcard.mov.

**CTA-Endcard v2 (David-Feedback: Firmenname stand doppelt, Optik zu
statisch):** Neu im Look des MAN-Lager-CTAs — animierter Grafik-
Hintergrund (Iris-Reveal, atmender Würth-Rot-Glow, Grid, Streaks,
Partikel), Eyebrow-Badge „SEIT 1996 TEIL DER WÜRTH-GRUPPE", Headline
jetzt der Claim „ALLES LAGER. ALLES WIR. ALLES HIER." (Rot-Block hinter
letzter Zeile) statt Firmenname — Name nur noch im Logo. Weißer
CTA-Button „BEWIRB DICH JETZT." mit Glow-Puls, Hashtags. 6s, Alpha
(Iris-Reveal über Footage). Render: `V6-cta-endcard-v2-MAN-style.mov`.
Hinweis: David hat die v1-Renders um 15:26 aus `Ergebnisse/Renders/`
in sein Schnittprojekt verschoben — alte `V6-cta-endcard.mov` (v1) dort
ersetzen. „SEIT 1996"-Freigabe weiter offen.

**Outro v3 = Map + CTA kombiniert (David: v2 zu überladen, fließender
Übergang gewünscht):** Neue Komposition `WlcV6-Outro` (8s) ersetzt die
separate CTA-Endcard: „SEIT 1996." + Silhouette → Pins droppen als
Cluster → Kamera-Zoom auf die Hohenlohe-Region (Pins fächern auf,
konstante Bildschirmgröße via Radius/Zoom) → Zoom-Through-Übergang
(Zoom läuft weiter, Map löst sich auf) → Logo + roter CTA-Balken
„BEWIRB DICH JETZT." + Hashtags. Streng CI: nur Schwarz/Weiß/Würth-Rot
+ Grau 85 als Kartenfläche, keine Effekt-Deko, Firmenname nur im Logo.
Pin-Geo-Positionen gegen Koordinaten verifiziert (Adelsheim nördlichst,
Crailsheim östlichst — alles Hohenlohe, Zoom gerechtfertigt).
Render: `V6-outro-map-cta.mov`. Die alte `WlcV6-CtaEndcard` ist aus
dem Studio entfernt (v2-Render `V6-cta-endcard-v2-MAN-style.mov`
verworfen); `WlcV6-BeweisCard` (Lupe) bleibt für Cut-Option A.

**Outro v3.1 (David: CTA-Phase zu minimalistisch, Hashtags raus):**
Hashtags entfernt (gehören in Post-Copy). CTA-Phase aufgewertet:
Team-Wappen (punch), Logo, Claim-Zeile „ALLES LAGER. ALLES WIR.
ALLES HIER." in Wuerth Bold mit roten Punkten (Anbindung ans Trio),
CTA-Balken größer. Props: claim, showWappen. Render überschrieben
(`V6-outro-map-cta.mov`, 8s).

**Overlays Video 4 + 5 (Final-Cuts, Timing aus Wort-SRTs in
`Material/Transkript Fertige Videos/1.4.srt + 1.5.srt`):**
Davids Nummerierung 1.4/1.5 = Video 4 (~48s) / Video 5 (~68s).
Entscheidungen (David): Motion-Elemente + Plan-Captions (keine
Wort-Untertitel); Endcards im V6-Stil NACH dem Video (kein Overlay);
V5-Cards nur belegte Fakten; Format 1080×1920/25p.
- `V4-overlay-captions.mov` (48s, Alpha): Hook zweistufig (0,1–5,6s),
  Splash MARVIN/Gruppenleiter (7,6–11,8s), Stationen-Ticker
  Kommissionierer→Staplerfahrer→Fachwirt→Gruppenleiter (wortgenau
  8,96/10,04/18,36/20,48s, Ende 21,5s), Caption „Weiterentwicklung —
  auch ohne Führungsrolle." (21,8–27,8s). Schicht-Szene + Abbinder
  sind im Cut entfallen → deren Captions nicht gebaut.
- `V5-overlay-captions.mov` (68s, Alpha): Hook zweizeilig (3,3–7,8s),
  Splash in der Sprechpause (8,6–13s), Captions „FTS" (22–25,2s,
  OHNE „15" — Zahl ist aus dem Cut geflogen), „Teil der Würth-Gruppe"
  (39,6–42,8s), „Improve — Ergonomie am Arbeitsplatz" (54,9–60s).
  Benefits-Szene + Sebastian im Cut entfallen → keine Benefit-Cards.
- `V4V5-job-endcard.mov` (4s, Vollbild): Wappen/Logo/„Fachkraft
  Lagerlogistik · Lagermitarbeiter"/„WLC Kupferzell"/CTA-Balken —
  laut Plan für beide Videos identisch (job_details_263).
  Offen: Endcard „+ Adelsheim" nur nach Freigabe.

**Overlays v2 (David: mehr Punch/Variation, Face-Zone-Verstoß V5-Hook):**
Beide Overlays neu gebaut und überschrieben: Hooks mit Punch +
Micro-Shake + rotem Highlight-Sweep auf Schlüsselwörtern („KLEINEN
LAGER"/„GROSSEM", „DAS WAR."); V5-Hook von 38 % auf 62 % verlegt
(Sprecher on camera — Face-Zone 8–45 % bleibt jetzt frei; V4-Hook
bleibt zentriert, Gang-Shot ohne Gesicht, per `hookTop` schiebbar).
Splash mit geschrägten Bars (−8°). V4-Werdegang jetzt als ZEITSTRAHL
(rote Fortschrittslinie, Pin-Nodes im Map-Look, Labels alternierend,
„VOR 9 JAHREN"→„HEUTE", Gruppenleiter rot). Captions in zwei Stilen:
Keyword-Cards (FTS./IMPROVE./WEITERENTWICKLUNG. + Subline) und
Skew-Bar („Teil der Würth-Gruppe").

**Sina-Befund + Ad C1 (David, 2026-07-16):** David stellt fest, dass
die Ausbildungsleitung (Sina Osterhag) in keinem der 6 Videos vorkommt
— Folge der Standort-Trennung (V1–V3 Adelsheim, Sina Kupferzell; ihr
V2-Beat 2.6 war durch Sebastian/Torben ersetzt) + Fachkraft-Sperrlisten
V4/V5 + Entscheidung „6 Videos ohne Bonus". Optionen A (Video 7
Kupferzell), B (V2-Re-Cut mit Ausnahme), C (eigene Kurz-Ads) vorgelegt
→ **Entscheidung David: Option C.** Umsetzung: FX3_8774 nachtranskribiert
(Cache), finaler Gehalts-Hook-Take verifiziert **05:20,7–05:26,3**
(Anhang-Schätzung 04:30 korrigiert; In-Punkt hart, Regie endet 05:20,3).
Ad-Plan `Ergebnisse/O-Ton-Pläne/ad-c1-sina-gehalt.md` erstellt (Hook →
Vergütungs-Staffel-Grafik 1.324,84/1.397,01/1.448,56 € → Endcard);
Endcard gerendert (`AD-azubi-endcard.mov`, „DEINE AUSBILDUNG BEI WLC
(M/W/D)"). Motion-Overlay folgt nach Picture-Lock via Wort-SRT.
Offen: Freigabe Gehaltszahlen öffentlich (Cornelia/Yannik); Targeting
Kupferzell vs. bundesweit; optional Ad C2 („Halt, stopp", FX3_8773 —
bräuchte Nachtranskription).

**Video 7 — Schnittplan als PDF (David, 2026-07-16):** Zusätzlich zu
Ad C1 doch eigenes Kupferzell-Azubi-Video mit Sina. Nachtranskribiert
für Timecodes: FX3_8773 (24:43), FX3_8734, FX3_8743 (Cache erweitert).
Plan gebaut + verifiziert: Hook „Was würdest du im Monat mit 1.300 €
machen?" (8774 · 01:57,6–02:04,6, sauberster Take — kannibalisiert
NICHT mit Ad C1), 6-Berufe-Take (8773 · 18:21,8–18:38,1, einziger mit
allen 6), Betreuung („immer jemand da", 07:54–08:31 gekürzt), Benefits
(10:24,3–10:47,3 — Sina sagt selbst „Zeugnisprämien"!), Torben-
Staplerschein (8734 · 9,4–14,7), CTA-Option 8743 (Blick prüfen;
wortgleich V1-CTA → Kannibalisierungs-Entscheidung offen).
Geliefert: `video-7-azubi-kupferzell.md` + Dossier-Langfassung +
**`WLC-Schnittplan-Video-7.pdf`** (4 Seiten: Deckblatt, Übersicht mit
Sperren, 2 Video-Seiten).

**V7-Umbau auf Sina-only (David):** Kein Sina-CTA-Take vorhanden
(Regie am Set: CTA kommt auf die Endcard — Beleg FX3_8774 · 00:36);
Torben-Beats komplett raus (löst zugleich CTA-Kannibalisierung mit V1
und die Torben-in-beiden-Standorten-Frage). Neuer Closer gefunden +
verifiziert: „Aus meiner Sicht macht es Sinn … weil wir ein geiles
Unternehmen sind … wohlfühlen und willkommen fühlen bei uns."
(FX3_8773 · 03:55,9–04:15,2, Jumpcut-Kürzung). Plan + PDF neu
(Sina-only verifiziert). Offen: Gehaltszahlen-Freigabe, „geiles
Unternehmen"-Wording mit Kunde.

**V7-Overlay (Final-Cut ~85s, SRT aus Downloads/WLC Transkripte/
Video 7.srt):** Sina-only-Schnitt, 0 B-Roll → Animationen tragen das
Video (David). Gebaut: Hook-Headlines mit rotem „1.300 €"-Block
(0,3–8,2s), 3 Fullscreen-Momente — nummeriertes Berufe-Board
(8,4–21,9s, 6 Badges wortgenau; ACHTUNG: Berufe 4–6 im SRT kollabiert
→ Chips 16,6/18,4/20,2s interpoliert), Flash-Card „IMMER JEMAND DA."
(49,9–52,2s auf ihrem Kernsatz), Benefits-Board mit 6 Checks
(52,6–70,8s inkl. ZEUGNISPRÄMIE) — dazu Sina-Splash (22,9s),
Betreuungs-Chips (Ausbildungsteam/Ausbilder/Beauftragte/immer
ansprechbar), Closer „EIN GEILES UNTERNEHMEN." (73,9s) + „WILLKOMMEN
IM TEAM." (82,6s). Neue Bausteine: BenefitBoard-numbered, FlashCard.
Render: `V7-overlay-captions.mov` (86s, Alpha). Endcard =
`AD-azubi-endcard.mov` anhängen. Boards v2 (David: Fullscreen-
Animationen zu langweilig): Red-Sweep-Entry, Dunkelrot-Radial,
mitzählende Ghost-Nummer, Items mit Slide+Badge-Bounce+Glow,
roter Fortschrittsbalken, Ken-Burns-Drift; Flash-Card mit Weißblitz
+ roter Schräg-Bande. V7 + V3 (teilt Benefits-Board) neu gerendert.

**V4-Feintuning (David, 2026-07-16):** Hook-Zeile 2 endet mit „…"
statt Punkt. Zeitstrahl mit Kamera-Logik: konstanter 1,5×-Zoom, Fokus
fährt smooth (Easing-Fenster −12/+3 Frames um jedes Wort) zum aktiven
Posten — aktuelle Station immer zentriert und groß. V4 neu gerendert.

**Job-Endcard finalisiert (David):** Standort-Zeile raus, Job-Zeile
jetzt „Fachkraft Lagerlogistik · Lagermitarbeiter · Ausbildung"
(universell für Fachkraft- UND Azubi-Zielgruppe); Hintergrund statt
Vollschwarz ein CI-konformer Radial-Verlauf (tiefes Würth-Rot #3A0000
Richtung Schwarz + dezenter Rot-Glow + Vignette). Render überschrieben
(`V4V5-job-endcard.mov`).

**Overlays Video 1–3 (Final-Cuts, SRTs in `Material/Transkript
Fertige Videos/`; Konzept-Abgleich gegen video-1/2/3-Pläne):**
- `V1-overlay-captions.mov` (61s, Alpha): Klischee-Caption-Sequenz
  0–8,3s (Plan-Beats 1–4: „Ausbildung im Lager? Eher so." → POV →
  „Machst du Abi?"/„Lager? Echt?"/„Klingt langweilig?" → „SPOILER:"),
  Splashes Hamid (8,5s) + Torben (CTA 54,4s — ACHTUNG: falls CTA-
  Sprecher doch Hamid ist, Splash tauschen), Keyword-Cards „NIE
  LANGWEILIG."/„STAPLERFAHREN."/„GEKNECHTET." mit Rot-Durchstreicher
  bei 42,6s + „LAGER. ABER BEI WLC.". Feedback-Runde (David): Sub der
  Geknechtet-Card „IST ES NICHT."→„NICHT BEI WLC.", Durchstreicher-
  Geometrie gefixt (mittig durch Versalhöhe, symmetrische −3°-Neigung,
  endet vor dem Punkt); V1 neu gerendert. Hook-Captions von
  Untertitel- auf Headline-Look umgestellt (David): Größe pro Caption
  statt global auf längste Zeile, \n-Umbrüche für gestapelte Blöcke,
  POV-Zeile zweizeilig — V1+V2+V3 neu gerendert. Zweite Runde (David,
  V2-Hook weiter zu untertitelig): Größen-Cap der Hook-Headlines
  0,036→0,05 Bildhöhe, alle längeren Hooks in V1–V3 zweizeilig
  gestapelt; V1+V2+V3 erneut gerendert. Veraltete
  V6-cta-endcard-v2-MAN-style.mov aus Renders/ gelöscht (David).
- `V2-overlay-captions.mov` (55s, Alpha): Besen-Hook-Captions (Zeile
  wurde im Cut nicht gesprochen → Caption trägt), Titel „Mein erster
  Tag bei WLC.", Splashes Hamid/Sebastian/Torben, „TAG 1: ERSTMAL
  ANKOMMEN.", Key-Line „KEINE NUMMER." (44,8s, Plan-Pflicht).
  Beweis-Card (22/25 Azubis) weiter weggelassen — Zahl offen.
- `V3-overlay-captions.mov` (118s, Alpha) — Eye-Candy-Paket, da Video
  ohne B-Roll (David): 4 FULLSCREEN-Stations-Cards (x/4 + rote
  Schräg-Bande: Materialwirtschaft/Controlling/M&S/Empfang, auf den
  „Jetzt sind wir…"-Übergängen), Vollbild-Benefits-Board 51,6–62,1s
  (Checks wortgenau; „ZEUGNISPRÄMIE" — Jana sagt „Notenprämie",
  Caption MUSS lt. Kundenklärung Zeugnisprämie!), Tätigkeiten-Chips
  (Controlling/M&S/Sales/Empfang, wortgenau), Hook „KAUFMANN BEI WLC?
  NUR EXCEL?" + Pflicht-Payoff „Was Kaufmann bei WLC wirklich heißt."
  (108,6s), Jana-Splash. Weggelassen (Freigaben offen): „Start 2027",
  „22 Azubis"-Zahl, job-Links.
- `V3-job-endcard-kaufmann.mov` (4s): Endcard-Variante „AUSBILDUNG
  KAUFMANN/-FRAU GROSS- & AUSSENHANDELSMANAGEMENT" (V1/V2 nutzen die
  universelle `V4V5-job-endcard.mov`).
- **(m/w/d)-Regel (David, dauerhaft):** Jede CTA-/Job-Endcard muss
  „(m/w/d)" am Berufstitel tragen — gilt ab sofort für ALLE
  Recruiting-Videos (als Feedback-Memory gespeichert). Beide Endcards
  aktualisiert + neu gerendert: `V4V5-job-endcard.mov` („… AUSBILDUNG
  (M/W/D)"), `V3-job-endcard-kaufmann.mov` („AUSBILDUNG KAUFMANN/-FRAU
  GROSS- & AUSSENHANDELSMANAGEMENT (M/W/D)").
- Stations-Cards v2 (David: zu leer/nicht ansprechend): Ghost-Nummer
  (riesige „03" in Dunkelgrau mit Ken-Burns-Drift), dunkelroter
  Radial-Hintergrund statt Voll-Schwarz, Doppel-Bande (Grau-Blade +
  Rot mit weißer Kante), Stations-Fortschritt als Punkte-Reihe.
  V3-Render überschrieben. Stations-Cards danach um je ~0,5s
  verlängert (Lesezeit, David): 12,7–14,7 / 32,2–34,4 / 62,0–64,2 /
  86,4–88,6s; erneut überschrieben. Tätigkeiten-Chips überarbeitet
  (David: zu klein, nicht bündig/gleich groß — Ursache: Skew pro Chip
  + Center-Scale): jetzt gerade Kanten, linksbündig an roter
  Führungslinie, Schrift ~30 % größer, Scale-Origin links; V3 erneut
  gerendert.

**Weitere Entscheidungen (David, Schnittphase):** Nie gedrehte VOs
werden KI-generiert (ElevenLabs, neutraler Sprecher — Texte geliefert:
6.8-Schluss, 6.9-CTA, optional Hook B; Hook C nur mit Cornelia-Freigabe).
Dynamik-Beratung gegeben (Musik-Mute auf LEISE, Kadenz-Optionen).

**Musik-Recherche V6 (Artlist, nach Tags/Waveform — Ohr-Check durch David):**
Kandidaten dunkel-cinematisch (Bundeswehr-Machart): „Apex Predator"
(Jeremy Chontow, Instrumental, 120 BPM), „The Brotherhood" (Emmanuel
Jacob, 140 BPM). Heller/Recruiting-freundlich: „Stampede" (Risian,
145 BPM, Claps & Snaps, Sport/Trailer). Zwei-Schichten-Alternative:
Percussion-Bett aus Album „Big Energy Drums" (Rhythm Scott) + warmer
Cinematic-Build für die Auflösung (z. B. „Empire"/Timothy Shortell,
„The Honored Moment"/lumine wave). Track-Entscheidung offen.

## 2026-07-29 — Kundenfeedback Runde 1 (Replay) triagiert

**Gemacht:** 7 Replay-Kommentar-Exporte (Cornelia, 21.07., alle Videos V1–V7)
gesichert und triagiert: 46 Kommentare → **27 Animation (NIRO Motion) /
15 Schnitt (David) / 4 Klärfälle.** Zuordnung gegen Protokoll-Stand +
Final-Cut-SRTs verifiziert (u. a.: „geknechtet" wird im V1-O-Ton wirklich
gesprochen → Card-Änderung allein reicht nicht; V4-Hook-Caption steht als
„DENSELBEN" im Comp).

**Kern-Themen Animation:** (1) Abbinder-Redesign in 6 von 7 Videos gefordert
(weniger Wappen+Logo — „Logo im weißen Kasten" ODER „nur Wappen groß";
Stellen untereinander, je mit (m/w/d)) → betrifft alle 4 Endcard-Varianten
+ V6-Outro-CTA-Phase. (2) Rote Satz-Punkte → weiß, als „allgemeines Thema"
(alle Overlays neu rendern). (3) **Splash-Name „Samed" statt „Hamid"**
(V1 + V2 — Namens-Korrektur, hohe Prio). (4) Diverse Card-/Caption-Texte
(Details s. Feedback-Dateien + Chat-Triage 29.07.).

**Geliefert:** `Material/Feedback/2026-07-21 Replay-Runde-1/` (7 TXT-Exporte
+ `00-Triage-Übersicht.md` — alle 46 Kommentare mit Zuordnung, Klärfragen,
Reihenfolge); Triage-Aufteilung im Chat.

**Offen/Klärfälle (vor Umsetzung):** V1 „geknechtet"→„ausgenutzt" (O-Ton-
Konflikt); V2 „an die Hand genommen" (O-Ton raus vs. Slogan-Card „Man wird
immer unterstützt."); V4 Antwort an Cornelia (Hook = bewusst KI-Fremd-Lager);
V4 „den gleichen" vs. korrektes „denselben" (falls ja: auch ElevenLabs-VO
+ Titel neu); V4 Splash nur „Gruppenleiter" ohne Name?; V6 Claim-Wechsel
„Mein Weg. Meine Entwicklung. Meine Zukunft bei WLC." (trifft Wort-Battle-
Auflösung + Outro + Videotitel); V3 Payoff-Slogan (Kunde liefert Vorschlag);
Endcard-Variante Kasten vs. Wappen; V7 Berufe-Titel wie Stellenanzeigen
(Wortlaute anfordern). Reihenfolge: längenändernde Cuts (V2/V3/V7) zuerst,
danach Overlay-Retiming.

## 2026-07-29 (2) — Neue Final-Cuts transkribiert + Timing-Analyse

**Gemacht:** David liefert 4 neue Schnittfassungen in `Material/Fertige Video
nach änderungen/` (1.4, 1.5, 1.6, Video 7 — V1–V3 macht ein Externer, Dateien
fehlen noch). Alle 4 mit Scribe wort-transkribiert (Skript
`_intern/transcribe_final_cuts_v2.py`, Cache erweitert) und automatisch gegen
die alten Wort-SRTs gedifft (Wort-Alignment → Versatz-Segmente + Element-
Mapping in `_intern/retiming_v2.json`).

**Befunde pro Video:**
- **1.4 (48→51,7s):** Sprache komplett unverändert (Versätze ≤0,2s =
  Engine-Jitter). +3,7s = alte Job-Endcard jetzt im Export eingebrannt
  (Frame-Check). → KEIN Retiming nötig; nur inhaltliche Feedback-Änderungen.
- **1.5 (68→66,2s):** Bis ~52s unverändert. Improve-Passage umgeschnitten
  (u. a. „…Ergonomie am Arbeitsplatz voranzutreiben" GESPROCHEN entfernt —
  deckt sich mit Cornelias Improve≠Ergonomie-Feedback). Improve-Card sitzt
  neu ca. 55,2–57,7s und wird eh inhaltlich neu gebaut. Endcard eingebrannt.
  Alle anderen Elemente unverändert.
- **1.6 (49,0s):** Musik-only-Fassung (0 Wörter, Tonspur ok, −10,5 dB mean) —
  kein VO. Elemente modular → kein SRT-Retiming, nur Content-Redesign offen.
- **Video 7 (~85,8→83,3s):** Berufe-Passage umgeschnitten: „Anwendungs-
  entwicklung"-Zusatz + Denkpause raus, aber Sina nennt weiter 6 Berufe →
  Board bleibt 6 Badges, Badge 6 nur noch „FACHINFORMATIKER". Chips jetzt
  wortgenau: 10,4/12,4/14,7/16,5/18,0/20,1s (vorher 4–6 interpoliert!),
  Board-Ende ~21,5s. Ab dort alles ≈ −1,3s, driftet bis −1,9s am Ende
  (Mikro-Trims, passt zu Schnaufer-Cuts): Splash 21,5 · Flash-Card 48,1 ·
  Benefits 50,7–69,0 · Closer 71,9 · Willkommen 80,8s. → Komplett-Retiming
  V7-Overlay nötig. Endcard NICHT im Export (wird weiter angehängt).
- **V1–V3 Baselines (alte Exporte in Downloads):** V1 61,93s · V2 54,57s ·
  V3 117,89s. Erwartung: V2 (Coppenrath-Cut) + V3 (Jahresabschluss-Cut)
  ändern Länge sicher, V1 (Szenentausch) evtl. längenneutral. Neue Dateien
  vom Externen in denselben Ordner → Pipeline erneut laufen lassen.

**Geliefert:** Wort-SRTs (0-basiert, ohne 01:00-Timeline-Offset!) in
`Material/Transkript Fertige Videos/Nach Änderungen 2026-07-29/`;
`_intern/final_cuts_v2_words.json`, `_intern/retiming_v2.json`,
`_intern/transcribe_final_cuts_v2.py`; alte `Video 7.srt` aus Downloads ins
Projekt kopiert.

**Hinweis:** 1.4/1.5-Exporte enthalten die ALTE Endcard eingebrannt — nach
Endcard-Redesign muss David dort eh neu exportieren; fürs Sprach-Timing sind
die Fassungen aber belastbar.

**Nächster Schritt:** Ein Rebuild-Pass für alle Overlay-Änderungen (V7-Retiming
+ Feedback-Texte + rote Punkte + Endcard-Varianten) — idealerweise nachdem
die Klärfälle (s. oben) beantwortet sind, sonst doppelte Renders.

## 2026-07-30 — Feedback-Umsetzung komplett: alle Overlays + Karten neu (17 Renders)

**Gemacht (Davids Go „mit Annahmen bauen", V1–V3-Timing lt. David unverändert):**
Alle 27 Animations-Punkte aus dem Kundenfeedback umgesetzt, alle 46 Kommentare
final gegengecheckt (46/46 abgedeckt: 27 Animation ✓, 15 Schnitt-seitig, 4 mit
offenem Kunden-Anteil). Änderungen:
- **Global:** Satz-Punkte weiß statt rot (Cards, Boards, Trio, Outro-Claim,
  BeweisCard) — Cornelias „allgemeines Thema".
- **V1/V2:** Splash „SAMED." statt „HAMID." (+ voller Rollen-Wortlaut, auch
  Torben); „NIEMALS LANGWEILIG."; „STAPLERFÜHRERSCHEIN./BEREITS IN DER
  AUSBILDUNG"; „AUSGENUTZT." statt „GEKNECHTET." (O-Ton sagt weiter
  „geknechtet" — geflaggt); neue CTA-Einblendung 45,2–50,9 s (Cornelias
  Wortlaut, 2 PunchLines); „TAG 1: WILLKOMMENSVERANSTALTUNG."; neue Card
  „MAN WIRD IMMER UNTERSTÜTZT." (25,8 s — O-Ton bleibt, Lösung per Slogan).
- **V3:** Jana-Bauchbinde im Cornelia-Wortlaut (SkewBar-Rollen jetzt mit
  fitText-Auto-Fit); Benefits-Item „AZUBI-EVENTS"; neuer Chip „KREATIVES
  ARBEITEN" (71,6 s, Gruppe bis 76 s). Payoff bleibt (Kundin liefert Slogan).
- **V4:** Hook „DEN GLEICHEN GANG" (VO sagt noch „denselben" — Voice-ID der
  Original-VO nirgends dokumentiert → VO-Neugenerierung bei David oder neu
  mit anderem Sprecher); Splash nur „GRUPPENLEITER." ohne Namen; Subline
  „DIE GEFÖRDERT WIRD"; **Zeitstrahl-Edge-Fade**: Labels blenden aus, bevor
  sie den Bildrand schneiden (Fix für „Kommisionierer abgeschnitten";
  Still-verifiziert). Dauer 51,7 s.
  **Präzisierung David 30.07. zu Kommentar 6: Zeitstrahl KOMPLETT raus**
  (stations leer), nur die Gruppenleiter-Einblendung bleibt (7,6–11,8 s,
  rote Bar „GRUPPENLEITER." + graue Bar „WLC KUPFERZELL"); Spacing per
  Still geprüft, V4 neu gerendert. Damit ist der Edge-Fade-Fix in V4
  ohne Anwendung (Code bleibt für künftige Zeitstrahl-Nutzung).
- **V5:** Card „ERGONOMIE./DEN MITARBEITERN ETWAS GUTES TUN" ersetzt
  „IMPROVE." — David hat „Improve" komplett aus dem O-Ton geschnitten;
  wortgenau 52,1–57,6 s. Dauer 66,2 s.
- **V6:** Trio + Outro-Claim = „MEIN WEG. MEINE ENTWICKLUNG. MEINE ZUKUNFT
  BEI WLC."; Trio-Zeilen enger (gap 0,35→0,2·size); Outro-CTA-Phase
  entschlackt mit `brandStyle`-Prop (wappen/logobox) + optionalem
  `jobs`-Prop (Stellen unter dem Claim — Cornelias Abbinder-Vorgabe).
- **V7:** Komplett auf Final-Cut v2 retimed (83,3 s): Berufe-Board 8,5–21,4 s,
  6 Chips wortgenau (10,4/12,5/14,7/16,5/18,1/20,1), männliche Form,
  „(M/W/D)" im Board-Titel (Design-Entscheidung statt 6× je Zeile),
  „FACHINFORMATIKER" ohne Zusatz; Board-Items einheitliche Auto-Fit-Größe;
  Chips 30,4–46,5; Flash 48,3–50,1; Benefits 50,2–68,9 (wortgenau);
  Kunden-Slogan als Closer-Zweizeiler 73,8–81,2 (ersetzt „EIN GEILES
  UNTERNEHMEN." — Wording war eh offen); „WILLKOMMEN IM TEAM." 81,4 s.
- **Endcards neu** (Stellen untereinander, je (M/W/D), Kundenliste; ihr
  „(w/w/d)" als Tippfehler korrigiert): 2 Marken-Varianten „nur Wappen groß"
  / „farbiges Logo im weißen Kasten" (`logo-pos.jpg` aus CI-Ordner
  „Logo RGB.jpg", 1181 px — HKS14-Datei war mit 439 px zu klein).

**Geliefert (Ergebnisse/Renders/, ProRes 4444 Alpha):** V1/V2/V3/V4/V5/V7-
overlay-captions.mov (61/55/118/51,7/66,2/83,3 s), V6-trio-alpha.mov,
V6-outro-map-cta-{WAPPEN,LOGOBOX,WAPPEN-STELLEN}.mov, V6-beweis-card-6-
standorte-belegt.mov (Punkt weiß), Endcards mit Ziel-Videos im Namen
(David 30.07.): endcard-V1-V2-V4-V5-lager-*, endcard-V3-kaufmann-*,
endcard-V7-azubi-* (je WAPPEN/LOGOBOX; V7-Karte gilt auch für Ad C1).
Alte Karten-Renders → `_alt-vor-feedback-2026-07-29/`.

**Wichtige Hinweise Montage:** Davids neue 1.4/1.5-Exporte haben ALTES
Overlay + alte Endcard EINGEBRANNT → finale Montage braucht Clean-Exporte
(die alten V1–V3-Exporte in Downloads sind offenbar clean). V7-Export ist
clean, Endcard separat anhängen.

**Offen (Kunde/David):** Endcard-Variante wählen (Wappen vs. Logobox; V6 auch
mit/ohne Stellen); V3-Payoff-Slogan (Vorschläge im Chat geliefert); V4-VO
„den gleichen"; V5-Automatisierungs-Text (Vorschlag im Chat); V7-Berufe wie
Stellenanzeigen (Wortlaute anfordern); V3-Endcard Kaufmann- vs. Lager-Stellen;
Antwort an Cornelia zu V4-Hook (bewusst KI-Fremd-Lager); (M/W/D) im
V7-Board-Titel statt je Zeile ggf. auf Kundenwunsch umstellen.

## 2026-07-31 — Nachschärfung V4 + V7 (Davids Klärungen), Renders neu

**V4 — Kommentar 6 geklärt (David):** Cornelia meinte: **Zeitstrahl komplett
raus**, nur die Gruppenleiter-Einblendung bleibt. Umgesetzt: `stations: []`,
Splash „GRUPPENLEITER." / „WLC KUPFERZELL" (7,6–11,8 s) — Spacing per
Composite geprüft, Standard-Splash-Position passt. Werdegang läuft jetzt nur
im O-Ton. (Edge-Fade-Code bleibt im Timeline-Baustein für künftige Nutzung.)

**V7 — Berufe-Titel nach Stellenanzeigen:** David liefert
`Material/Info zur Stellenanzeigen/` (PNG-Screens: Lagermitarbeiter
Adelsheim+Kupferzell, Ausbildung Fachkraft für Lagerlogistik Adelsheim).
Muster der Anzeigen: volle Präpositionen („Fachkraft **für** Lagerlogistik")
+ **(m/w/d) direkt hinter jedem Titel, kleiner gesetzt**. Board umgebaut:
Titel wieder „6 AUSBILDUNGSBERUFE.", alle 6 Zeilen mit „FÜR" + (M/W/D) als
kleinerem Suffix (BenefitBoard rendert `(M/W/D)` automatisch bei 55 % Größe,
Auto-Fit einheitlich). Damit ist Klärfall „V7-Berufe wie Stellenanzeigen"
erledigt.

**Hinweis Diskrepanz:** Endcard-Stellenzeilen folgen weiter Cornelias
diktierter Liste („FACHKRAFT LAGERLOGISTIK" ohne „für") — die Stellenanzeige
schreibt „Fachkraft für Lagerlogistik". Falls einheitlich gewünscht: kurzer
Umbau + Re-Render der 2 Lager-Endcards.

**Geliefert:** `V4-overlay-captions.mov` + `V7-overlay-captions.mov`
überschrieben (ProRes 4444 Alpha).

## 2026-08-31 — Kundenfeedback Runde 2: V3-Chip + V4-Splash (2 Replay-Kommentare)

**Gemacht (2 Screenshots von David, Cornelia via Replay):**
- **V3 (Kundin „1.3") bei 1:23,6** — Kommentar „Vor- & Nachbereitung von
  Kundenbesuche": liegt wortgenau auf Janas Sales-Passage („…Kundenbesuche
  vorbereite oder auch nachbereite", 83,7–86,7 s). Chip „KUNDENBESUCHE"
  (81,5 s) → **„VOR- & NACHBEREITUNG VON KUNDENBESUCHEN"** (Grammatik
  korrigiert: Kundin schrieb „von Kundenbesuche" — analog zur
  „(w/w/d)"-Korrektur; falls sie wortwörtlich besteht, kurzer Re-Render).
  Dabei Safe-Zone-Verstoß gefixt: ChipStack hat jetzt Auto-Fit-Größe pro
  Gruppe (fitText, einheitlich wie Benefits-Board) — der lange Wortlaut lief
  vorher rechts aus dem Bild. Gilt auch für V7-Chips beim nächsten Render.
- **V4 (Kundin „1.4") bei 0:21** — Kommentar „Können wir hier WLC
  Würth-Logistik | Standort Kupferzell schreiben?": Timestamp liegt exakt auf
  Marvins „…und jetzt Gruppenleiter." (20,6–21,2 s) — die bisherige
  Splash-Einblendung „GRUPPENLEITER./WLC KUPFERZELL" (7,6–11,8 s) nahm die
  Pointe vorweg. **Lesart: Splash-Wortlaut ersetzen** (Pipe-Format = Cornelias
  Bauchbinden-Konvention aus Runde 1). Haupt-Render: rote Bar
  „WLC WÜRTH-LOGISTIK" + graue Bar „STANDORT KUPFERZELL", Timing unverändert.
  Zusätzlich Absicherungs-Variante gerendert (GRUPPENLEITER. bleibt rote Bar,
  graue Bar = voller Kunden-Wortlaut mit Pipe).
  **Entscheidung David 31.08.: GRUPPENLEITER. bleibt drin** — die Variante
  ist die finale Fassung und wurde zu `V4-overlay-captions.mov` umbenannt
  (Splash-ersetzte Fassung verworfen, Defaults im Code nachgezogen).

**Geliefert (Ergebnisse/Renders/, ProRes 4444 Alpha):**
- `V3-overlay-captions.mov` (118 s, überschrieben)
- `V4-overlay-captions.mov` (51,7 s, überschrieben — GRUPPENLEITER. +
  „WLC WÜRTH-LOGISTIK | STANDORT KUPFERZELL")

**Review:** Stills mit Guides in `_intern/work/review-*.png` geprüft —
Face-Zone frei, V3-Chip nach Fix innerhalb Safe Zone, V4-Splash mittig sauber.

**Offen:** Grammatik-Hinweis „Kundenbesuchen" ggf. im Freigabetext an Kundin
erwähnen; V7-Re-Render mit Chip-Auto-Fit (gelieferte Fassung hat mit
„AUSBILDUNGSBEAUFTRAGTE IN JEDER ABTEILUNG" vermutlich denselben
Safe-Zone-Überlauf) — nur auf Davids Zuruf.

## 2026-09-09 — Kundenrückfrage „Samed" + Schriftart: Animationsstand verifiziert

**Anlass:** Mail von WLC (Cornelia): Name des Auszubildenden in 1.1 und 1.2
falsch („er heißt Samed", war bereits in Korrekturschleife angemerkt) +
Frage, ob in allen Videos „die neue Schriftart" umgesetzt ist.

**Gemacht (reine Verifikation, keine Änderung an Comps oder Renders):**
- Feedback-Herkunft geprüft: Der Punkt steht als **Kommentar 1** in beiden
  Runde-1-Exporten vom 21.07. (1.1 bei 01:00:09:15, 1.2 bei 01:00:12:20),
  triagiert am 29.07. als „hohe Prio".
- Umsetzung belegt: `recruiting-v1-v3/Composition.tsx` trägt `"SAMED."` in
  beiden Overlay-Defaults (Z. 136 + 166, Kommentar „Kundenkorrektur 21.07.")
  — committed, nicht Teil der offenen Arbeitskopie.
- **Render gegengeprüft (harter Beweis):** Kontaktbögen + Einzel-Stills aus
  den gelieferten Alpha-Renders `V1-overlay-captions.mov` (30.07. 14:45) und
  `V2-overlay-captions.mov` (30.07. 14:46) zeigen beide „SAMED." mit dem
  vollen Rollen-Wortlaut. Ebenfalls im Render sichtbar: „NIEMALS LANGWEILIG.",
  „STAPLERFÜHRERSCHEIN.", „AUSGENUTZT.", CTA-Zweizeiler, „TORBEN." →
  **alle Runde-1-Punkte aus 1.1/1.2 sind in den Overlays drin.**
- Schriftart geprüft: Fonts sind zentral in `clients/wlc/components/index.tsx`
  definiert (FONT_XBDCN/BOLD/BOOK = Wuerth Global) und werden von **allen**
  drei WLC-Kompositionen importiert — technisch kann kein Video eine andere
  Schrift haben. Font-Gate (`useWlcFonts`, delayRender bis alle drei TTFs
  geladen) schließt einen Fallback-Font im Render aus. Kunden-Fontordner
  enthält unverändert die Würth-TTFs (Dateistand 2021).

**Befund:** Die Animation ist korrekt und war es schon am 30.07. Wenn die
Kundin in 1.1/1.2 weiter „Hamid" sieht, betrifft das die **Montage/den
ausgelieferten Stand**, nicht das Overlay: Die Overlays werden als separate
ProRes-4444-Alpha-Dateien geliefert und müssen in den Schnitt gelegt werden.
Vermerk vom 30.07. passt genau dazu — Exporte hatten teils ALTES Overlay
eingebrannt, V1–V3 wurden extern geschnitten.

**Offen / zu klären mit Kundin:**
- Welche Fassung von 1.1/1.2 lag ihr vor (Replay-Version/Datum)? Vermutlich
  ein Stand vor der 30.07.-Montage.
- **„Neue Schriftart" ist im Projekt nirgends beauftragt** — weder in den 46
  Kommentaren aus Runde 1 noch in Runde 2 (31.08.) noch im Protokoll. Rückfrage
  nötig, was gemeint ist (evtl. der Headline-Look der Hook-Captions oder eine
  CI-Umstellung, zu der uns keine Font-Dateien vorliegen).

**Nachtrag gleicher Tag — „neue Schriftart" ist geklärt:** Jan liefert die
Dateiliste des Kunden: `WuerthSans-{BlackCond,Black,Demi,Book}_V1_000.ttf`.
Das ist eine **andere Familie** als die eingebundene. Font-Metadaten der
aktuell genutzten TTFs ausgelesen (name-Tabelle): Familie `Wuerth`, Schnitte
`Extra Bold Cond` / `Bold` / `Book` (Dateistand 2021) — neu ist `WuerthSans`
in Version V1_000. **Die Kundin hat recht: Die neue Schrift ist nirgends
umgesetzt, in keinem der 7 Videos.** WuerthSans liegt auf dem Studio-Rechner
noch gar nicht vor (Suche in Repo, Downloads, Desktop: kein Treffer).

**Umstellungs-Umfang erhoben:**
- **Code: 1 Datei.** `clients/wlc/components/index.tsx` definiert Familien-
  namen + `loadFont`-URLs zentral; die 55 Verwendungen in den drei
  Kompositionen laufen über die Konstanten FONT_XBDCN/BOLD/BOOK und bleiben
  unangetastet.
- **Assets: 9 public-Ordner** (`public`, `public-wlc`, `public-hbl`,
  `public-lohi`, `public-man`, `public-niro`, `public-setzer`, `public-sw`,
  `public-bumble-clean`) + `build-sw/public` — alle enthalten echte Kopien
  derselben TTFs (md5 identisch), keine Symlinks.
- **Renders: 17 Dateien / ~8,5 min** Alpha-Material müssen komplett neu.
- **Eigentlicher Aufwand = Layout, nicht Dateitausch:** Andere Schnitt-
  metriken ⇒ `fitText` misst neu ⇒ alle Auto-Fit-Elemente (Bauchbinden,
  Benefits-Board, Chips, Stations-Cards) verschieben sich. Die dokumentierten
  Safe-Zone- und Face-Zone-Prüfungen sind danach erneut fällig.

**Offen:** (1) TTF-Dateien werden gebraucht. (2) Schnitt-Mapping: 3 alte →
4 neue Schnitte; `Extra Bold Cond → BlackCond` und `Book → Book` sind klar,
für `Bold` stehen **Demi** (näher am bisherigen Gewicht) oder **Black** zur
Wahl — betrifft Rollen-Bauchbinden, Chips, Benefits-Items. (3) Beim Kunden
erfragen, ob mit der Schrift auch neue CI-Richtlinien (Farben/Logo) kommen.

## 2026-09-09 (2) — Schrift-Umstellung auf Wuerth Sans, alle 17 Renders neu

**Gemacht:** Kunde liefert die neue Hausschrift (`Neue Fonts/WuerthSans-*_V1_000.ttf`).
Abgleich bestätigt den Wechsel: alte Familie `Wuerth` V1.30 (upem 2048) →
`Wuerth Sans` V1_000 (upem 1000). Umgestellt.

- **Mapping (optisch entschieden, NICHT nach OS/2-Zahlen):**
  Extra Bold Cond → **BlackCond**, Bold → **Black**, Book → **Book**.
  Demi bleibt ungenutzt. Grund: Die alte Familie trägt untypische Gewichte
  (Bold = 500, Book = 300); Demi (600) rendert sichtbar dünner als das alte
  Bold und schwächt die Rollen-Bauchbinden, Black trifft das gewohnte
  Gewicht (Breite +1 % statt −4 %).
- **Zeichenabdeckung** aller vier Schnitte gegen die im Projekt genutzten
  Sonderzeichen geprüft (Umlaute, `&`, `|`, `–`, Klammern): vollständig.
- **Positions-Ausgleich (User-Regel):** Die Overlays liegen über freigegebenen
  Schnitten und müssen pixelgleich sitzen. Wuerth Sans hat aber eine andere
  Zeilenbox (hhea 1.15 em vs. 1.3496 em alt) — ohne Ausgleich schrumpfte jede
  textabhängige Box: im V1-Splash roter Kasten 12 px flacher, Schrift 13 px
  höher. Fix: der neuen Schrift beim Laden die hhea-Metriken des jeweils
  abgelösten Schnitts aufprägen (`ascentOverride`/`descentOverride`/
  `lineGapOverride`, Werte im Code dokumentiert). Dafür `loadFont` durch die
  FontFace-API ersetzt (Remotions loadFont kann keine Overrides), mit
  Node-Guard für `getCompositions`.
- **Verifiziert durch Nachmessen** (nicht nur Sichtprüfung): Bounding-Boxen
  alt vs. neu bei gleicher Framenummer über 9 Testpunkte in 7 Kompositionen —
  8× y-Position exakt identisch, 1× (V3-Chipstack) 1 px Versatz durch die
  anders hohen Glyphen selbst. Splash-Referenz V1@240: Gesamt 241 px, roter
  Kasten 109 px, Schrift-Oberkante y=1188 — alle drei wie in der Altfassung.
- **Safe-/Face-Zonen** an den kritischen Stellen mit Guides geprüft (V3-Chips,
  Benefits-Board, V7-Berufe-Board, Endcards): unauffällig. Der lange V3-Chip
  hat exakt dieselbe Bounding-Box wie vorher (976×176 @ +65+195).

**Geliefert:** `Ergebnisse/Renders/2026-09-09 Neue Schrift (Wuerth Sans)/` —
alle 17 Renders (ProRes 4444 Alpha), Dateien mit Suffix `-WuerthSans`, damit
die Fassung auch einzeln verschickt eindeutig bleibt. Laufzeiten unverändert
(61/55/118/51,7/66,2/83,3 s + V6-Bausteine + 6 Endcards).
**Der Hauptordner `Renders/` behält bewusst den bisherigen Auslieferungsstand
(alte Schrift)** — nichts überschrieben.

**Nebenbefunde:**
- Die Props der 10 Varianten-Renders (Endcards, V6-Outro) waren nirgends
  gespeichert und mussten aus den fertigen .mov zurückgelesen werden. Liegen
  jetzt als JSONs in `_intern/render-props/`, gefahren von
  `_intern/render-all.sh` (baut alle 17 reproduzierbar).
- Der graue Kasten des langen V3-Chips ragt 15 px über die 5 %-Safe-Zone —
  **Altbestand aus dem 31.08.-Stand, kein Regress** (in beiden Fassungen
  identisch gemessen). Text selbst liegt drin. Nicht angefasst.

**Offen:** Freigabe der neuen Fassung durch David/Kundin; danach entscheiden,
ob der Hauptordner auf die Wuerth-Sans-Fassung umgestellt wird. Frage an
Cornelia, ob mit der Schrift auch neue CI-Richtlinien (Farben/Logo) kommen —
sonst laufen wir Gefahr, ein zweites Mal alle 17 Renders zu fahren.

**Nachtrag — Gegenprobe „steckt noch alte Schrift drin?" (09.09.):** Statisch:
keine alten TTF-Dateinamen und keine alten Family-Aliase mehr im Code, kein
anderer Client lädt `clients/wlc/fonts`, alle `fontFamily`-Werte im
WLC-Client laufen über FONT_XBDCN/FONT_BOLD/FONT_BOOK. Dynamisch: die drei
alten TTFs in allen 10 public-Ordnern temporär umbenannt und neu gerendert —
V1@240 ergibt **0 abweichende Pixel** gegenüber dem Render mit vorhandenen
Altdateien (Gegenprobe alt↔neu: 68.694 Pixel, der Test schlägt also an).
Stills aus V3/V7/Endcard zeigen durchgehend Wuerth Sans, nirgends eine
System-Fallbackschrift. Altdateien danach wiederhergestellt (Rollback).
Hinweis: In den Logo-Assets (`logo-white.png`, `logo-pos.jpg`, Wappen) steckt
weiterhin die alte Würth-Wortmarke — das sind unveränderte Kunden-Assets,
kein Satz von uns; neue Logo-Dateien lagen nicht bei.

## 2026-09-10 — Fehlender 18. Render: V6-Wort-Battle mit Wuerth Sans nachgezogen

**Anlass:** Jan vermisst `V6-wort-battle-alpha.mov` in der neuen Schrift.

**Ursache (belegt, kein Fehler an der Komposition):** Die Datei lag nie im
Studio-Ordner `Ergebnisse/Renders/`. Sie stammt aus dem allerersten V6-Paket
vom **15.07. 14:16** und wurde direkt auf `NIRO-SSD-03/… /03_Medien/
SSD Downloads/` gelegt (833 MB) — anders als ihre Schwester
`V6-trio-alpha.mov`, die in der Feedback-Runde am 30.07. neu gerendert wurde
und dadurch in `Renders/` landete. Die Wort-Battle war von Runde 1 inhaltlich
nicht betroffen (nur Einzelwörter über `WlcWord`, keine Satzpunkte, kein
Claim) und wurde deshalb nie neu gebaut. Am 09.09. wurde die Render-Liste
`_intern/render-all.sh` aus dem **Inventar von `Renders/` = 17 Dateien**
rekonstruiert → die 11. WLC-Komposition `WlcV6-WortBattle` fiel durchs Raster.
10 von 11 Kompositionen wurden umgestellt.

**Gemacht:**
- `_intern/render-all.sh` um die fehlende Zeile ergänzt (jetzt 18 Renders,
  Wort-Battle als erster V6-Baustein) — damit ist die Lücke geschlossen.
- `WlcV6-WortBattle` neu gerendert: `2026-09-09 Neue Schrift (Wuerth Sans)/
  V6-wort-battle-alpha-WuerthSans.mov` (ProRes 4444, 2160×3840, 25 fps,
  1025 Frames = 41,000 s, yuva444p12le, 847 MB — Format identisch zu den
  17 Schwester-Renders).

**Verifiziert (User-Regel „Position erhalten"):** Bounding-Boxen alt (SSD)
gegen neu bei identischer Framenummer, 7 Testpunkte über alle 6 Wortpaare
(LAUT/LEISE/GENAU/MASCHINE/DRAUSSEN/GRAMM/TEAM). Vertikale Mitte weicht
maximal **2 px** ab, horizontal bleibt alles auf der Canvas-Mitte (1080).
Die vier breiten Wörter sitzen wie vorher exakt am `fitText`-Breitenlimit
(x0≈156, x1≈1990). Sichtprüfung an 3 Frames: Schnitt sichtbar Wuerth Sans
BlackCond, Größe und Sitz unverändert. Transition geprüft (Frame 160):
RedSweep deckt voll ab (Alpha 100 %) wie dokumentiert.

**Offen:** Der Hauptordner `Renders/` enthält die Wort-Battle in der ALTEN
Schrift weiterhin nicht — die Altfassung liegt nur auf NIRO-SSD-03. Wenn der
Ordner den vollständigen Auslieferungsstand abbilden soll, müsste sie von
dort kopiert werden (833 MB). Nicht ohne Ansage gemacht.

## 2026-09-10 (2) — NAS-Ordner `04_Exportiert` geprüft: alle 7 V3-Fassungen

**Auftrag (Jan):** Prüfen, ob die V3-Exporte auf dem NAS stimmen und zur
jeweiligen Vorfassung passen (Änderung soll nur die Schrift sein).
Pfad: `NIRO NAS/…/01_Kunden/WLC …/02_Projekte/01_Projekt-Dreh18.05 & 20.05/
04_Exportiert/` — 19 Dateien, 7 × V3 (09.09. 19:52–20:19 und 10.09. 18:01–18:28).

**Methode (rein lesend):** ffprobe-Eckdaten aller Fassungen; Tonspuren auf
8 kHz Mono dekodiert und sekundenweise korreliert (findet jede Schnitt-
änderung); Bildvergleich mit 2 fps gegen die jeweilige Vorfassung, Heatmap
der Änderungszonen; hochauflösende Textausschnitte für die Schriftprüfung.

**Ergebnis — 4 Videos mit sauberem Vorgänger (V2 vom 31.08.):**
| Video | Dauer/Frames | Ton-Korrelation | Bildänderung |
|---|---|---|---|
| 1.3 | identisch (2992 / 119,680 s) | 0,999989 | nur Textband y 217–786, max 3,0 % |
| 1.4 | identisch (1291 / 51,712 s) | 0,999966 | nur Textband y 384–673, max 2,9 % |
| 1.5 | identisch (1653 / 66,197 s) | 0,999998 | nur Textband y 417–667, max 2,9 % |
| 1.7 | identisch (2080 / 83,264 s) | 0,999997 | nur Textband y 209–794, max 3,7 % |
→ **reiner Schriftwechsel, kein Eingriff in Schnitt oder Ton.**

**Die drei ohne V2 im Ordner (1.1, 1.2, 1.6):** Vergleichsstand dort ist die
Fassung vom 16.07. — also **zwei Feedback-Runden alt**. Abweichungen sind
deshalb erwartbar und wurden einzeln zugeordnet:
- **1.1** — Dauer identisch (1553 / 62,123 s), Ton identisch (0,9996).
  Bildunterschiede = die belegten Runde-1-Korrekturen: „GEKNECHTET." →
  „AUSGENUTZT.", „STAPLERFAHREN./SCHON IN DER AUSBILDUNG" →
  „STAPLERFÜHRERSCHEIN./BEREITS IN DER AUSBILDUNG", neue Endcard mit Wappen
  und drei (m/w/d)-Zeilen. Schnitt unverändert.
- **1.2** — **37 Frames (1,48 s) kürzer.** Zuordnung per Versatz-Suche:
  0–20 s deckungsgleich (Versatz 0), **21–28 s echt überarbeitet**, ab 29 s
  wieder dasselbe Material mit −1,48 s Versatz. Das ist genau der Runde-1-
  Punkt „MAN WIRD IMMER UNTERSTÜTZT." bei 25,8 s (O-Ton per Slogan gelöst).
- **1.6** — gegen die 29.07-Fassung aus `Material/Fertige Video nach
  änderungen/` geprüft (der richtige Vorgänger): Dauer identisch, Ton 0,997,
  Bildabweichung nur in den **6 Wort-Battle-Blöcken** (0–5,5 / 7–12,5 /
  14–19,5 / 21–26,5 / 28–33,5 / 35–40,5 s — exakt das 7-s-Raster, die
  RedSweep-Transitions dazwischen unverändert) sowie 42–48,5 s
  (Claim „MEIN WEG. MEINE ENTWICKLUNG." + neue Outro-Endcard vom 30.07.).

**Schrift verifiziert:** In allen sieben V3 ist Wuerth Sans drin — an
hochaufgelösten Textausschnitten gegengeprüft (1.1 „POV: LETZTES SCHULJAHR.",
1.2 „MEIN ERSTER TAG BEI WLC.", 1.3/1.7 „AZUBI-BENEFITS.", 1.4/1.5
Endcard-Stellenzeilen, 1.6 „LAUT"). **Das 1.6-V3 von 18:28 enthält bereits
die heute nachgerenderte Wort-Battle** in neuer Schrift.

**Gegenprobe auf vergessene Overlays:** Für jedes Sample-Frame mit Text
geprüft, ob es sich gegenüber der Vorfassung geändert hat. Alle zunächst
auffälligen Stellen waren Fehlalarme (helle Fenster, reine Logo-Phasen der
Endcard, ein Transition-Frame). Die Bauchbinde „SINA." in 1.7 bei 21,5 s lag
mit 599 geänderten Pixeln knapp unter der Schwelle — Differenzbild zeigt
sauber die Glyphen, also ebenfalls neu. **Kein Overlay ist in alter Schrift
stehengeblieben.**

**Anmerkungen (kein Fehler, aber auffällig):**
1. Für **1.1, 1.2 und 1.6 fehlt die V2-Stufe im Ordner.** Die Datei ohne
   Suffix ist dort der Stand vom 16.07. und damit **zwei Runden veraltet** —
   Verwechslungsgefahr beim Rausschicken. 1.4/1.5/1.7 haben ihre V2 vom
   31.08., obwohl Runde 2 nur V3-Chip und V4-Splash betraf.
2. **1.6-Dateiname:** die Altfassung heißt „… Alles hier..mp4" (Satzpunkt +
   Endung), die neue „… Alles hier_V3.mp4" — der Satzpunkt ist weg. Für die
   Sortierung egal, beim Ausliefern aber uneinheitlich.
