# Protokoll — MAN / Wartezimmervideo / 2026-07 Erste Fassung

## 2026-07-23 — Projekt-Setup & Design

**Gemacht:** Projekt aufgesetzt, Kundenanforderung (Mail) geklärt, Design mit David
entwickelt und freigegeben. Materialbestand auf NAS gesichtet: vier Drehs, zusammen
~1,4 TB (TikTok-Ads 2023: 215 GB, Ad Dreh 2025: 302 GB, Frauen in der Werkstatt:
706 GB, Lagerlogistik: 176 GB).

**Geliefert:** Design-Doc `docs/superpowers/specs/2026-07-23-man-wartezimmervideo-design.md`

**Entscheidungen:**
- Zwei Fassungen (stumm + Ton), 1–3 Min, Ziel ~90–120 s, reines Standort-Image (keine Job-CTAs)
- Gesprochenes = O-Töne aus Interviews; stumme Fassung nutzt dieselben Aussagen als animierte Untertitel
- Nur Interviews transkribieren (alle vier Drehs); Erkennung über größte Dateien pro Dreh; ältere Drehs sind unsortiert
- B-Roll ohne Transkription, Auswahl per Thumbnail-Kontaktbögen
- Deliverable = Cutter-Paket (O-Ton-Plan, Konzept, Sortierung, 2 Schnittplan-PDFs, Remotion-Renders); Musik + Finalschnitt beim Cutter
- Format: sämtliches Footage ist 9:16; Ausgabe 16:9 — Footage in Fenstern (Solo/versetzt/Duo-Split), Remotion-Grafik füllt die Leinwand (Frame-Renders mit Alphakanal für den Cutter)

**Offen:** ~~Phase 1 starten~~ → erledigt, siehe unten.

## 2026-07-23 — Phase 1: Scan + Interview-Freigabe

**Gemacht:** Umsetzungsplan geschrieben (`docs/superpowers/plans/2026-07-23-man-wartezimmervideo.md`,
9 Tasks, 2 Gates). ffprobe-Scan aller vier Drehs: 3.595 Videodateien, 222/334/699/189 GB —
plausibel. Kandidatenliste gebaut (Proxies ausgefiltert), Gate mit David durchlaufen.

**Geliefert:** `_intern/scan.csv` (3.595 Zeilen), `_intern/interview-kandidaten.md`
(markiert: 10× [OK], 9× [OK?], Rest [RAUS]).

**Entscheidungen (David):**
- Transkription = Kern (10 Interviews Dreh 02/03/04) + Jan-Hauptkamera-Takes Dreh 01 (9 Takes)
- Ton-Kamera: FX3 bei Dreh 02/03/04 (immer die FX3-/A-Seite der Paare)
- Dreh 01 Ton-Kamera unbekannt → 60s-Sample-Check Jan (A7iv) vs. Bennet (A7c) vor Vollauf
- Nicht transkribieren: Quiz 2025, Bennet-Takes (vorbehaltlich Sample), Actioncams, B-Roll, Hooks

**Offen:** ~~Task 3~~ → erledigt, siehe unten.

## 2026-07-23 — Transkription, O-Ton-Auswahl, Konzept

**Gemacht:** Sample-Check Dreh 01 (A7iv-Ton brauchbar; Befund: Jan/Bennet = verschiedene
Interviews, Bennet bleibt laut David draußen). 19 Clips transkribiert (19/19 ok,
~27.600 Wörter) → `_intern/utterances.json` (1.508 Utterances). O-Ton-Kandidaten per
4 Fan-out-Agenten, zentral gegen utterances.json verifiziert (Agent-Zitate teils
paraphrasiert → final nur Span-basierte Wort-für-Wort-Extraktion). Konzept entworfen.

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/00-oton-auswahl-standort-image.md` — 15 Kern-O-Töne + 11
  Alternativen in 5 Clustern, alle sprecherrein, Quellen dreiteilig
- `Ergebnisse/Konzept.md` — 5 Kapitel + Opener/Endcard, ~1:50, Loop-fähig, beide Fassungen
- `_intern/script_structured.json` — 2 Videos (Ton/stumm) nach Schnittplan-Schema

**Entscheidungen (David):** Ton-Kamera FX3 überall; Dreh 01 = Jan-Takes; Standorte
mischen ok, solange keine Standortnamen genannt werden (2023=Karlsruhe, 2025=Schweinfurt).

**Offen:** ~~Konzept-Freigabe~~ → erteilt, siehe unten.

## 2026-07-23 — Cutter-Paket komplett (Phase 3)

**Gemacht:** Konzept von David freigegeben (Standorte mischen ok, ohne Nennung).
142 B-Roll-Kontaktbögen gerendert (Keyframe-Decode nach Performance-Fix; 3 Zeitraffer-
Sonderfälle mit kaputten Timestamps über Frame-Select gelöst), per 4 Kapitel-Agenten
gesichtet, 33 Clips verifiziert. Remotion-Layout-System gebaut (7 Kompositionen,
`tools/motion/src/clients/man/projects/wartezimmervideo/`), Pre-Delivery-Review über
Kontrollframes, 17 Final-Renders. Schnittpläne beide Fassungen (Dossier-Langfassungen +
Kompakt), PDF gerendert, Seitenbudget geprüft (Deckblatt + Übersicht + 1 Seite/Fassung).
Alle Render-Referenzen im Plan gegen `Ergebnisse/Renders/` abgeglichen (16/16 + 1 Reserve).

**Geliefert (Cutter-Paket komplett):**
- `Ergebnisse/O-Ton-Pläne/MAN-Wartezimmervideo-Schnittanweisungen.pdf` (4 Seiten)
- `Ergebnisse/O-Ton-Pläne/` video-1-ton.md, video-2-stumm.md, 01-projekt-grundlagen.md,
  00-oton-auswahl-standort-image.md, Dossier/ (2 Langfassungen)
- `Ergebnisse/Sortierung/broll-auswahl.md` (33 Clips, 5 Kapitel, ★-Empfehlungen)
- `Ergebnisse/Renders/` 17 ProRes-4444-Alpha-Renders (3 Frames, Opener, Endcard,
  5 Trenner — kap5 als Reserve, 7 Zitat-Inserts), 1,9 GB
- `Ergebnisse/Konzept.md` (freigegeben)

**Abweichungen vom Plan:** Frame-Renders typbasiert (frame-solo/-versetzt/-duo) statt
je Kapitel — Frames sind kapitelunabhängige 30-s-Loops, spart 4 redundante Renders.
Kap-3-Prozess-Labels als Cutter-Texteinblendung spezifiziert statt gerendert.

**Offen (für David/MAN):**
1. MAN-Freigabe 2023er Gesichter — betrifft NUR optionale Bausteine (O-14/O-15/A-05);
   Kernschnitt kommt ohne 2023er Material aus.
2. Musikwahl/Lizenz (Ton-Fassung).
3. Karten vs. klassische Untertitel in der stummen Fassung (MAN-Geschmacksfrage).
4. Namen der 2023er Azubis (0837/0859) nur bei Nutzung nötig.
5. Bennet-Takes 2023 (~58 min, eigene Interviews) bewusst nicht transkribiert —
   Nachschub-Option, falls Service-Cluster breiter werden soll.

## 2026-07-23 — Verlängerung auf ~2:20 (Davids Wunsch)

**Gemacht:** Beide Fassungen um zwei O-Töne verlängert (~1:50 → ~2:20): O-02 Markus
(Betriebsleiter, Fehlerkultur) neu in Kapitel 1, O-11 Louis (LKW-Liebe) neu in
Kapitel 4 — bewusst zwei NEUE Stimmen (Chef-Perspektive fehlte). Stumme Fassung
timeline-identisch nachgezogen (Design-Prinzip: eine Struktur).

**Geliefert:** 2 neue Renders `insert-O-02.mov` + `insert-O-11.mov` (ProRes 4444
Alpha); Konzept.md, script_structured.json, beide Kompakt-Schnittpläne, beide
Dossier-Langfassungen, Übersichtsseite aktualisiert; PDF neu gerendert (6 Seiten:
Deckblatt + Übersicht + je 2 pro Fassung — im Budget). Konsistenz-Check: 19 Renders,
18 referenziert, keine fehlenden.

**Hinweis:** Kürzungs-Option zurück auf ~1:50 = O-02 + O-11 rausnehmen (im
Kompaktplan V1 unter „Alternativen" dokumentiert).

## 2026-07-23 — Format-Korrektur: eine Zeile pro Aussage

**Gemacht:** David-Feedback: mehrere Aussagen in einer Ablauf-Zeile sind fürs
Schneiden unübersichtlich. Beide Kompakt-Tabellen auf EINE Zeile pro O-Ton/Karte
umgebaut (2a/2b, 3a/3b, 5a/5b — je eigene Quelle, Bild-Zuordnung, Kommentar,
Zeitfenster). PDF neu gerendert (6 Seiten, im Budget).

**Regel dauerhaft verankert:** `tools/transcribe/WORKFLOW-Schnittplan.md`
(Format-Standard) + Studio-Gedächtnis (cutter-schnittplan-format) — gilt ab
sofort für alle Schnittpläne, nicht nur MAN.

## 2026-07-23 — Format-Korrektur 2: Personen-Namen überall

**Gemacht:** David-Feedback: Personen-Namen müssen IMMER dabeistehen, nie nackte
Dateinamen. Beide Kompakt-Pläne überarbeitet: Quellen in V2 wieder voll dreiteilig
(Person + Rolle + Ordner + Timecode), Bild-Spalte nennt jetzt Ordner + sichtbare
Personen (z. B. Jonathan Nnadi + Nico im Duo-Paar), nicht identifizierbares
Personal als „n. n." gekennzeichnet, unverifizierte Namens-Behauptungen entfernt
(Teamfoto C9297: „vor Nutzung verifizieren"). PDF neu (6 Seiten, im Budget).

**Regel verankert** (Workflow-Standard + Gedächtnis): Personen-Namen in JEDER
Spalte inkl. Bild/B-Roll; „n. n." statt weglassen; keine ungeprüften Namen.

## 2026-07-23 — Umbau: alle Personen rein, Kap 3 ohne Prozess-Erklärung

**Gemacht (Davids Feedback):** O-08 (Alexanders Ersatzteil-Prozess) wirkte deplatziert
→ Kapitel 3 heißt jetzt „die Menschen hinter den Kulissen": Prozess läuft rein visuell
(B-Roll + Labels), gesprochen wird Haltung. Alexanders Ersatz-Aussage aus seinen
Utterances gehoben (O-18 „ohne Teile keine reparierten Lkws", Regie-Vorsprecher vor
07:37 im Kommentar markiert). Alle 10 Personen der Drehs 2025/26 sprechen jetzt:
NEU Lara (O-17 Diagnosegeräte — sauberer Take gefunden, Transkript-Warnung obsolet),
Tobi (O-06), Jonathan (A-03), Nico (A-02). Länge ~2:56 (im 1–3-min-Rahmen).
Beide Pläne komplett neu: 13 Zeilen, eine pro Aussage, Personen überall benannt.

**Geliefert:** 5 neue Zitat-Karten (insert-O-06/O-17/O-18/A-02/A-03.mov, Alpha
geprüft; insert-O-08 + O-15 jetzt Reserve), O-Ton-Auswahl auf 17 Kern + 11
Alternativen erweitert (alle sprecherrein), Konzept/script_structured/Pläne/
Übersicht aktualisiert, PDF neu (7 Seiten — V1 braucht 3; von David gedeckt:
„Dokument halt länger falls nötig"). Konsistenz: 24 Renders, 23 referenziert.

**Erkenntnis (Betrieb):** Die zsh-Shell splittet unquotete Variablen nicht —
`$FLAGS` kam als EIN Argument bei Remotion an; Ursache aller „mysteriösen"
Render-Abbrüche. Merkregel: Render-Flags immer ausschreiben.

**Offen:** 2023er Block (Jan Volz O-14, Ilja A-01, O-15) NUR nach MAN-Freigabe —
damit wären auch 2023er vertreten, Laufzeit dann >3:00 → mit MAN klären.
Rest unverändert (Musik, Karten vs. UT).

## 2026-07-23 — Ciattei rein, Lager-Aussagen allgemeiner

**Gemacht (Davids Feedback):** (1) Mark Ciattei (Betriebsleiter Karlsruhe, Dreh 01)
gesichtet — Volltreffer: „Fahrzeuge nicht von der Stange … im Lkw-Bereich wird
wirklich noch repariert" → als O-19 Kap-4-Abschluss eingebaut (2023-Vorbehalt
deutlich markiert, Fallback dokumentiert). (2) Lager-Aussagen entschärft: O-18
(Alexander „ohne Teile") und A-03 (Jonathan „Kollegen im Lager") → Reserve;
stattdessen allgemeine Aussagen aus den Transkripten gehoben: O-21 Alexander
(privat unterwegs/Teambuilding), O-20 Jonathan („bei MAN fühle ich mich wohl").
Nico A-02 bleibt (nennt das Lager nicht). Auswahl jetzt 20 Kern + 11 Alternativen,
alle sprecherrein verifiziert (bei O-19 spricht die Regie den Satz vor — In-Punkt
im Plan markiert).

**Geliefert:** 3 neue Karten (insert-O-19/O-20/O-21.mov, Alpha geprüft; Reserve
jetzt insert-O-08/O-15/O-18/A-03), beide Pläne + Konzept + script_structured +
Übersicht auf ~3:05 (Fallback ohne Ciattei ~2:50), PDF neu (7 Seiten).
Konsistenz: 27 Renders, 24 referenziert, nichts fehlt.

**Offen:** MAN-Freigabe 2023 entscheidet über Ciattei-Klimax (sonst ~2:50) ·
Musik · Karten vs. UT · Namen 0837/0859 nur bei Nutzung.

## 2026-07-23 — Nico-Tausch: Wachstums-Aussage statt Kulturen

## 2026-07-23 — Musik-Shortlist geliefert (nur Artlist + Envato)

**Gemacht:** Klarstellung David: NIRO hat nur Artlist- und Envato-Abos (kein Epidemic
Sound — in Gedächtnis gesichert). Track-Recherche für die drei Akte über Websuche;
Shortlist mit 13 Kandidaten + Anhör-Checkliste nach
`Ergebnisse/Musik-Empfehlungen.md`. Hinweis: Auswahl tag-basiert, David muss im
Player gegenhören (Vocals/Energie/Loop). Schnittplan-Sound-Spalte bleibt bis zur
finalen Reihenfolge unangetastet.

## 2026-07-23 — Davids Timeline analysiert; Lara-Tausch O-17 → O-23

**Stand:** David hat SRT seiner Premiere-Timeline geschickt (~1:28 O-Ton-Block,
11 Blöcke A–K, weicht von PDF ab: Markus auf 1 Satz, Tobi nutzt A-06 statt O-06,
Hannes stark gekürzt, Lara + Jonathan fehlen). Sortier-Empfehlung geliefert:
nur Nico-Block hinter Alexander ziehen → Qualität / Menschen / Fahrzeuge / Herz;
Entscheidung Davids steht aus. SRT-Warnung: Premiere-Auto-Transkript hat Hörfehler
(„Chirarchie", „Babaschau") — für UT die O-Ton-Auswahl nutzen.
**Lara:** O-17 (Diagnosegeräte) laut David unpassend → Reserve; NEU O-23
„mein Vater war schon immer Lkw-Fahrer … mit Lkws groß geworden" (FX3_0491 ·
00:13–00:31, In/Out-Empfehlung ~10 s), Platz: Fahrzeug-Block vor Louis.
Verifiziert (22 Kern + 11 Alternativen), `insert-O-23.mov` gerendert.
PDF-Pläne bewusst NOCH NICHT umgebaut — warten auf Davids finale Reihenfolge,
dann eine Konsolidierung statt drei.

## 2026-07-23 — Musik-Konzept freigegeben, Timeline-Abgleich angekündigt

**Stand:** Drei-Akte-Musikkonzept von David freigegeben (Akt 1 Organic/Folk 0:00–1:26,
Akt 2 Funk-Groove 1:26–2:00, Akt 3 Cinematic 2:00–Ende; Wechsel auf den Trennern,
alles instrumental, loop-tauglich, Lizenz via Artlist/Epidemic). **Suche wartet:**
David schickt das Transkript seiner tatsächlichen Timeline (weicht von der PDF ab);
Aufgabe dann: seine Szenen in eine passende thematische Reihenfolge bringen, danach
Musik-Suche auf die echte Reihenfolge mappen.

## 2026-07-23 — Nico-Tausch: Wachstums-Aussage statt Kulturen (davor)

**Gemacht (Davids Wunsch):** Nicos Kap-3-Aussage getauscht: A-02 (viele Kulturen)
→ Reserve; neu **O-22** „…wie man sich dann wirklich weiterentwickelt, wenn man
arbeitet … man wird reifer, erwachsener … so viel selbstständiger" (FX3_1810 ·
10:03–10:24, Out-Empfehlung nach „erwachsener" ~12 s — Timing bleibt 1:47–2:00).
Sprecherrein verifiziert (jetzt 21 Kern + 11 Alternativen), `insert-O-22.mov`
gerendert, alle Dokumente + PDF nachgezogen. Konsistenz: 28 Renders, 24
referenziert, nichts fehlt.

## 2026-07-24 — Verbindliche Timeline des finalen Schnitts (Ton-Fassung)

**Gemacht:** Davids finalen 9:16-Schnitt (Audio 134,0 s) mit Scribe + Whisper
(large-v3) transkribiert und beide Engines abgeglichen → verbindliche Timeline
`_intern/final-16x9/timeline.json` (12 O-Ton-Blöcke, 9 Lücken). Alle Blöcke der
O-Ton-Auswahl zugeordnet, unklare Spleiße per utterances.json verifiziert
(Markus „ständiger Verbesserungsweg“, Laras Bewerbungs-Satz).
**Reihenfolge final:** O-01 · [12,8 s Trenner] · O-04, O-02, O-21, A-06, O-05,
O-22 · [25,3 s Trenner] · O-11, O-23, O-12, O-10, O-19. Abweichungen vom Plan:
A-06 statt O-06 (Tobi), O-20/Jonathan fehlt, O-19 (Ciattei) jetzt Schluss NACH
der Sohn-Story, Lara O-23 nach Louis statt davor, kein Service-Kapitel.
**Offen:** Whisper-Halluzinationen in den Musik-Lücken ignoriert (67 s, 118 s);
zwei Hör-Checks empfohlen (O-04 „wir sind eine kleine Familie“?, O-01 „legen
wir“); Laras „muss ich mich hier bewerben“ = leichtes Bewerbungs-Framing trotz
Standort-Image-Vorgabe — David entscheiden lassen. Ciattei-Block: MAN-Freigabe
2023er Material weiter offen.

**Weiter (gleiche Session) — Animations-Konzept 16:9-Bühne:** Neuer Ansatz
(Davids fertiger 9:16-Schnitt statt Einzelclips): Remotion bettet das Video per
OffthreadVideo ein und rendert das komplette 16:9-Master — kein Alpha-Roundtrip
mehr. Konzept aus 4 Design-Agenten synthetisiert: Passepartout-Fenster 576×1024
mit roter Offset-Kontur; Seitenwechsel nur in den zwei großen Lücken
(links→rechts→links, loop-geschlossen); Geisterrahmen als Duo-Ersatz in der
25-s-Bridge; persistente Sprecher-Plaketten aus timeline.json; 3 wortsynchrone
Zitat-Momente (0:06 Julia, 0:44 Tobi, 2:12 Ciattei); Sohn-Story bewusst
grafikfrei; Kapitel-Fortschrittsleiste; Musik-Akte auf 2:14 (~0:15 / ~1:16);
stumme Fassung als Render-Flag über gemeinsame sync-plan.json. Mockups an David.
**Entscheidungen (David):** Passepartout-System freigegeben · Endcard anhängen ·
Lara-Audio bleibt (Text-Sperre gilt) · Jonathan bewusst draußen · Timeline-
Wortlaute „passt so".

**Detail-Konzept geschrieben + adversariell verifiziert** (3 Prüf-Agenten:
Timing-Mathe, Vorgaben, Remotion-Baubarkeit — 4 kritische + 12 Warnungs-Findings
eingearbeitet, u. a.: Karten der stummen Fassung brauchen gekürzte Kernsätze mit
Zeichen-Budget statt Volltext; Leisten-/Logo-Choreografie bei Travels + Bridge;
Video-Freeze-Layer nach Frame 3350; Ambient-Drift auf Root-Ebene wegen
Sequence-relativer Frames; Ciattei-Rollentext „Betriebsleiter Servicebetrieb"
ohne „Karlsruhe" als expliziter Sonderfall; Face-Zone pro Fensterseite mappen).
**Geliefert:** `Ergebnisse/Animations-Konzept-16x9.md` (verbindlich),
Spec-Update im Studio-Repo. **Nächste Schritte:** David liefert 9:16-Videodatei
(CFR, 48 kHz, bevorzugt ProRes 422) · Bild-Check Hero-Shot bei 76,0 s ·
Umsetzungsplan + Implementierung · Musik-Suche auf Akt-Zeiten 17,2/76,0 ·
stumme Karten-Kurztexte zur Abnahme.

## 2026-07-24 — Konzept v2: MAN-Web-Look (Davids Design-Feedback)

**Davids Feedback:** v1 nicht hochwertig genug; sehr nah an man.eu; nie länger
als 5 s statisch; ALLE Aussagen kurz einblenden, aber nie 1:1 — Zusammenfassung.
Assets in `Material/` geliefert: MAN Global komplett (inkl. Thin/Light),
Logos weiß/schwarz, `löwe-halb.jpg`.

**Gemacht:** man.eu per Browser gesichtet (Homepage, Cards, Hero, 404) →
Design-Tokens extrahiert: Anthrazit #2E3A46/#222C36 statt Bordeaux, ALLES
scharfkantig (Radius 0), Rot #E30045 nur als Akzent (Vertikal-Balken vor
Listen, Tab-Unterstrich, Slider-Striche), Bold-Condensed-VERSALIEN, Panel-
Versatz-Layouts, Löwe als angeschnittenes Artwork. Konzept auf v2 umgebaut:
Takeaway-System für alle 12 Blöcke (Zusammenfassungen, Vorschlagsliste in §5),
5-s-Garantie als System (Echtzeit-Tabs/Striche + Ambient + Beat-Füller im
sync-plan-Generator), Geisterrahmen → Panel-Versatz-Moment, wortsynchrone
Zitat-Momente entfallen (setzten Wörtlichkeit voraus). Neue Mockups an David.

**Offen:** Look-Freigabe v2 + Takeaway-Liste (§5) durch David · Videodatei ·
Rest unverändert.

**Nachtrag v2.1 (Davids Feedback):** (1) Logo IMMER als Bilddatei
(MANlogoWeiss.png), nie Schriftzug. (2) Höchstens EIN vertikaler Screen —
Bridge ohne zweites Panel, Kapiteltitel + Löwe direkt auf der Fläche.
(3) Permanente Kapitel-Tabs + Fortschritts-/Aussagen-Striche komplett
gestrichen (5-s-Garantie jetzt über Ambient + Beat-Füller im Generator).
Konzept-Doc + Guardrails (9–11) aktualisiert, Mockup v3 mit echtem Logo an
David. Kapiteltitel bleiben als kurze Marken-Momente in den zwei großen
Lücken — falls David sie ganz streichen will, melden.

**Nachtrag v2.2 (Davids Feedback: „Löwe nicht gut erkennbar"):**
Löwen-Silhouette aus löwe-halb.jpg per PIL freigestellt (rechte Hälfte,
Rot + Weiß als Alpha-PNG, /tmp — bei Implementierung nach
tools/motion/public übernehmen). Neue Regel (Guardrail 12): Löwe nur in
Branding-/Kapitel-/Endcard-Momenten, dann groß, volle Deckkraft,
angeschnitten; Ton-in-Ton-Wasserzeichen in Sprech-Blöcken gestrichen.
Ambient-Ebene = rote Linie + Panel-Modulation. Mockup mit echtem Löwen an
David.

---

## 2026-07-24 · Umsetzung 16:9-Master (sync-plan + Komposition)

**Gemacht:** (1) sync-plan-Generator `_intern/final-16x9/build_sync_plan.py`
validiert und gelaufen (Stdlib, transcribe-venv): 81 Einträge, Takeaways
wörtlich aus Konzept §5, Guardrails 1/2/3/5 im Code, 5-s-Beat-Prüfung
BESTANDEN (max Fenster vorher 10,83 s → 8 Zwischen-Beats → max nachher
4,70 s). JSON nach `tools/motion/src/clients/man/projects/wartezimmervideo/
sync-plan.json` + Kopie neben timeline.json. (2) Komposition `ManWz169Master`
(ID `man-wz-169-master`, 1920×1080, 25 fps, 3550 F/142 s, Props
fassung ton|stumm + ohneCiattei) in die bestehende Composition.tsx gebaut
und in Root.tsx registriert: Anthrazit-Bühne #2E3A46, Versatz-Panel #222C36,
576×1024-Fenster mit OffthreadVideo (wz-master-1080.mov, per ffprobe
bestätigt: ProRes 1080×1920, 25p, 3349 F) + Freeze bis 136,0 s, roter
8-px-Innenkanten-Balken, Plaketten/Morphs, Takeaway-Zeilen (Cond Bold 76
VERSALIEN, Schlüsselwort rot), Branding-Moment, 2 Kapitel-Wipes, Löwe
rot/weiss nur in Marken-Momenten, Ambient (Wanderlinie + Panel-Modulation,
ganze Loop-Perioden auf Root-Ebene), Dichte-Hüllkurven, Endcard mit
Loop-Rückbau, Ciattei in abtrennbaren Sequences, ReviewOverlay mit
Face-Zone pro Fensterseite (§8).

**Geliefert:** sync-plan.json (2×), Composition.tsx (Sektion 6), Root.tsx.
Typecheck (tsc --noEmit) sauber, `remotion compositions` listet die Comp,
2 Testframes (F60 Kaltstart, F1950 Kapitel 2 + Löwe) korrekt gerendert.

**Entscheidungen/Offenes:** Plakette-Rolle 34 px nach Konzept §3 (Task-Text
nannte 36 — Spec ist verbindlich). Bei Kapitel 2 läuft das rote
„NUTZFAHRZEUG" teils über den weißen Löwen — im Face-Zone-/Look-Review mit
David prüfen. Takeaway-Liste §5 weiter zur Abnahme offen; Testframes
Face-Zone-Review + Musik (17,2/76,0) wie gehabt.

## 2026-07-24 — Testframes 16:9-Master (Session 2)

**Gemacht:** wz-master-1080.mov auf Stabilität geprüft (2× Größenmessung
im 20-s-Abstand, 2 053 492 102 Bytes stabil; ffprobe: ProRes 1080×1920,
25 fps, 3349 Frames — deckt sich mit sync-plan.meta). 8 Testframes plus
1 QA-Frame aus `man-wz-169-master` gerendert (remotion still, Flags
ausgeschrieben), alle 1920×1080.

**Geliefert:** Ergebnisse/Testframes-16x9/: 01-kaltstart (F12),
02-branding (F360), 03-marke1 (F480), 04-team-takeaway (F1132),
05-bridge-hit (F1900), 06-sohnstory (F2800), 07-ciattei (F3320),
08-endcard (F3480), qa-facezone (F1132 mit showGuides+showFaceZone).

**Entscheidungen/Offenes:** Keine Code-Fixes nötig. F1900 = exakter
Hit-Frame → Kapitel-2-Titel/Löwe stehen dort bei Animationsstart (noch
unsichtbar); Kontrollframe F1960 bestätigt korrektes Rendern
(„FASZINATION NUTZFAHRZEUG" + weißer Löwe). Weiter offen: rotes
„NUTZFAHRZEUG" läuft teils über den weißen Löwen; Endcard-Claim
„SERVICE-TEAM" berührt rechts den roten Löwen — beides im Look-Review
mit David klären.

## 2026-07-24 — Review-Fixes 16:9-Master (3 kritische Befunde)

**Gemacht:** Drei kritische Befunde aus dem Testframe-Review behoben:
(1) **Bridge-Hit 76,0 s:** Kapitel-2-Wipe deckt jetzt im Riser-Auslauf zu
(wipeStart 75,4, Dauer 0,6), Titel-Reveal beginnt exakt am Musik-Hit —
am Hit-Frame steht die volle Rot-Fläche statt leerer Bühne
(build_sync_plan.py, Kontrollframe F1900 geprüft: Rot-Fläche + Hero-Shot
LKW im Fenster — Hero-Shot-Annahme aus Konzept §6 bestätigt).
(2) **Endcard-Kollision:** Löwe an der Endcard von Rot auf WEISS
(Guardrail 12: Rot ODER Weiß zulässig) — roter Claim „SERVICE-TEAM"
läuft zwar weiter in die Silhouette, ist aber rot auf weiß klar lesbar.
(3) **Face-Zone-Mapping:** Zone von Frame- auf Fensterraum umgestellt
(Composition.tsx: winX + rel×576 / M_WIN_Y + rel×1024, folgt dem Fenster
durch die Travels); Pixel-Messung im neuen qa-facezone bestätigt
x 1575–1748, y 130–540 (Soll laut Spec §8). Plakette (y 824–944)
überlappt die Zone weiterhin nicht.

**Geliefert:** build_sync_plan.py + sync-plan.json (2× regeneriert,
Beat-Prüfung weiter BESTANDEN, 81 Einträge), Composition.tsx
(faceZone169), Testframes neu (gleiche Pfade): 05-bridge-hit.png
(jetzt F1915 = 76,6 s — Titel voll, Löwe zieht herein; F1900 wäre die
volle Wipe-Fläche), 08-endcard.png (F3480), qa-facezone.png (F1132).
Typecheck sauber; wz-master-1080.mov vor Rendern auf stabile Größe
geprüft (2 053 492 102 Bytes, 2×20 s).

**Entscheidungen/Offenes:** Endcard-Löwe weiß = gewählte Variante aus dem
Review-Vorschlag (Alternative Textblock-Verschiebung nicht nötig).
Look-Review der neuen Frames mit David; Rest unverändert (Musik,
Takeaway-Abnahme §5, MAN-Freigabe 2023).

**Nachtrag (Review-Fixes 2):** Löwen-Anschnitt rechts repariert (Artwork hat
den Kopf oben rechts — bei `right:-240` war genau der Kopf draußen): Kapitel 2
+ Endcard jetzt kleiner/tiefer (H 940, top 640), Kopf mit offenem Maul frei,
Titel/Claim berühren die Silhouette nicht mehr; Kapitel-2-Löwe bekommt Exit
89,3–89,9 (Opacity+TranslateX, in der Lücke), Branding-Moment Opacity-Exit
über die letzten 10 Frames (kein Pop bei F445). build_sync_plan.py: 5-s-Beat-
Prüfung jetzt für BEIDE Varianten (ohne Ciattei: Lücke 117,7→126,38 = 8,68 s
→ variantenunabhängiger Beat bei 122,04 s; beide max 4,70 s, BESTANDEN) +
Standort-Filter generisch (STANDORTNAMEN-Liste statt hart „Karlsruhe“).
sync-plan.json 2× regeneriert, tsc sauber, Testframes 02/05/05b(F2000)/08 neu
gerendert und Bild-verifiziert.

## 2026-07-24 — Generator-Umbau sync-plan (Davids Umbau-Entscheidungen)

**Was gemacht:** `_intern/final-16x9/build_sync_plan.py` komplett auf Davids
Entscheidungen vom 2026-07-24 abends umgebaut: (1) Plaketten nur Vorname
(erstes Wort von person, Rolle bleibt; Ciattei → „Mark / Betriebsleiter
Servicebetrieb“), Lage komplett auf der Grafikfläche. (2) Neues Wording
wörtlich: 4 dauerhafte Kapitel-Headlines als neuer Typ `headline`
(0,4–9,8 / 21,8–64,8 / 89,9–107,0 / 107,3–133,8; Cond Bold ~92 px,
Slide+Fade) + alle 12 Takeaways ersetzt (~64 px). (3) Typen `wisch` und
`balken-puls` komplett raus (Erzeugung UND Beat-Füller) — Kantenbalken
konstant rot. (4) Travels/Wipes/Bridge/KapitelMarken raus, Fenster fest
rechts x=1164/y=28/576×1024 (Rand rechts 180 px); neuer Typ `spotlight`
mit 9,5–22,3 (inkl. Branding-Beat 13,0–17,0) und 64,6–89,9 (Flare am
Musik-Hit 76,0); Löwe dauerhaft subtil hinter dem Fenster, Blick zur
Bildmitte. (5) Lara-Sperre 101,0 s und Ciattei-Sonderfälle unverändert.
5-s-Prüfung bleibt, Füller nur noch subtile Typo-/Licht-Events
(`typo-akzent`/`licht-akzent`/`zeilen-shift`), unfüllbare Fenster → WARNUNG
statt weißer Pulse. Alt-Keys `travels`/`wische`/`kapitelMarken`/`bridge`
bleiben als LEERE Arrays im JSON (Absturz-Schutz für die laufende
Composition bis zu deren Umbau).

**Geliefert:** sync-plan.json 2× regeneriert (final-16x9 + tools/motion/
src/clients/man/projects/wartezimmervideo). Beat-Check beide Varianten
BESTANDEN: vorher max 13,90 s (mit) / 16,10 s (ohne Ciattei), 10 subtile
Zwischen-Beats (6× typo-akzent, 4× licht-akzent), nachher max 4,80 s /
4,80 s, 0 Warnungen.

**Entscheidungen/Offenes:** Composition.tsx (Sektion 6) muss noch auf die
neuen Keys `fenster`/`headlines`/`spotlights`/`loewe` umgebaut werden —
bis dahin zeigt das Studio das Fenster übergangsweise links (kein Crash).
Löwen-Vektorisierung (Phase 1) offen.

## 2026-07-24 (abends) — Komposition-Umbau ManWz169Master

**Was gemacht:** Sektion 6 in `tools/motion/src/clients/man/projects/
wartezimmervideo/Composition.tsx` komplett auf den neuen sync-plan
(fenster/headlines/spotlights/loewe) und Davids Umbau-Entscheidungen
umgebaut: Fenster fest rechts x=1164 (Travel-Code entfernt), Spotlight-
Momente in beiden sprechfreien Lücken (Fenster-Glide zur Mitte ×1,04,
Abdunkelung #171E26 + Vignette, roter Glow, 4 Lichtstreifen mit Flare
bei 76,0 s, roter Vektor-Löwe), dauerhafte Kapitel-Headlines (Slide+
Fade statt Wipes), Plaketten nur Vorname komplett auf der Grafikfläche,
weißer balken-puls raus (Kantenbalken konstant rot), Löwen auf die
neuen Vektor-PNGs (dunkel dauerhaft hinter dem Fenster, rot in den
Spotlights, weiß auf der Endcard), Endcard-Hero links + Loop-Rückbau
(Frame 3549 ≙ Frame 0), Face-Zone auf feste Fensterposition rechts.

**Geliefert:** Composition.tsx (Sektion 6 neu, alte Wipe-/Travel-/
Bridge-Komponenten entfernt); `npx tsc --noEmit` sauber, Bundle
kompiliert (3550 Frames), 7 Kontroll-Stills geprüft (Frame 0, 60, 150,
375, 1900, 3450, 3549).

**Entscheidungen/Offenes:** Endcard-Löwe lt. Plan WEISS (Guardrail 12,
Plan-Hinweis) statt „roter Löwe" aus Task-Punkt 6 — Komposition ist
datengetrieben (nimmt Variante aus dem Plan). Logo Zone A blendet
während der Spotlights mit ab (Spotlights „textfrei"). Sichtprüfung im
Studio (Hot-Reload läuft) durch David offen.

## 2026-07-24 (abends) — Testframes nach Umbau (9 Stills)

**Gemacht:** 9 Kontroll-Stills des umgebauten 16:9-Masters
(`man-wz-169-master`) gerendert, alte Testframes ersetzt (auch
qa-facezone.png entfernt). Sichtprüfung an 04/02/09: Headline dauerhaft,
Takeaway darunter, Plakette nur Vorname („TOBI") komplett auf der
Grafikfläche, Kantenbalken konstant rot, Spotlight-1 mit rotem
Vektor-Löwen (Blick zur Bildmitte), Endcard weißer Löwe links.

**Geliefert:** `Ergebnisse/Testframes-16x9/` — 01-kaltstart (F60),
02-spotlight1-branding (F350), 03-team-headline (F560),
04-tobi-takeaway (F1132), 05-hit-flare (F1900), 06-spotlight2-mitte
(F2000), 07-sohnstory (F2800), 08-ciattei (F3320), 09-endcard (F3480);
alle 1920×1080.

**Entscheidungen/Offenes:** Keine Render-Fehler. Sichtprüfung aller 9
Frames durch David offen.

## 2026-07-24 (nachts) — Umbau v3: Review-Fixes Endcard-Freeze + Testframe 03

**Gemacht:** Zwei kritische Testframe-Befunde behoben: (1) Endcard-Fenster war ab
136,0 s komplett schwarz — Freeze-Layer endete bei meta.freezeBis=136,0; jetzt
FREEZE_BIS=142,0 (Freeze läuft unter dem Dimmer bis Loop-Ende, Fenster nie leer),
Dimm-Rampe entkoppelt (endet beim Hero-Start 136,0), Dimm-Level 0,92→0,85 — Hero-Shot
bleibt gedimmt sichtbar, weißer Löwe frei vom Fenster (Pixel-Check: kein Weiß > x 1150).
(2) 03-team-headline war mitten in der Reveal-Animation gegriffen (F560 = 0,1 s nach
Blockstart) — Timing korrekt, Testframe auf Steady-State F600 (24,0 s) gelegt: Headline +
Takeaway + MARCEL-Plakette voll deckend. sync-plan 2× regeneriert (Beat-Check BESTANDEN),
tsc sauber, 09/03 neu gerendert + Bild- und Pixel-verifiziert, Loop-Grenze F3549 geprüft.

## 2026-07-24 (nachts) — Umbau v4: Design-Fixes Weiß-Pulsen, Endcard-Löwe, Flare

**Gemacht:** Drei verifizierte Warnungen behoben (Davids Linie: nichts pulsiert
weiß, edel/smooth): (1) Weißes sinus-pulsierendes Overlay auf dem Versatz-Panel
auf DUNKLE Modulation umgestellt (schwarzes Overlay, gleiche Hüllkurve, max 5 %)
— kein weißes Aufhellen mehr im Master. (2) Endcard-Löwe verkleinert visH
760→640 (visX 660 bleibt): rechte Kante jetzt x≈1072, Pixel-Check 95 px Luft
zur Fensterkante 1164 (≥88 px inkl. Drift ±7). (3) Flare am Musik-Hit 76,0 war
im Render unsichtbar — Ursache: Hüllkurve startete ERST am Hit (Wert 0 auf dem
Hit-Frame 1900). Hüllkurve jetzt auf den Hit zentriert (±0,25 s, weich
rein/raus), Streifen-Boost 2,1×→3×, Opazitäts-Kappe im Flare 0,35→0,55, plus
kurzer zusätzlicher roter Glow-Boost hinterm Fenster (kein Weiß).

**Geliefert:** `Ergebnisse/Testframes-16x9/` — 05-hit-flare (F1900),
06-spotlight2-mitte (F2000), 09-endcard (F3480) neu gerendert und als Bild
verifiziert. tsc sauber.

**Entscheidungen/Offenes:** Davids Beispielwerte (visX≈760/visH≈680) hätten
die rechte Kante auf ~1198 geschoben (80-px-Regel verletzt) — stattdessen
visX 660 belassen und nur visH reduziert. Sichtprüfung Flare-Intensität
(sichtbar, nicht trashig?) durch David offen.

## 2026-07-24 (nachts) — Umbau v5: Löwen-Präsenz an beiden Enden kalibriert

**Gemacht:** Davids Bild-Befund („Löwe in Sprech-Blöcken gar nicht sichtbar,
im Spotlight viel zu dominant") an beiden Enden zur Mitte gezogen —
Vorgabe „edel", „dauerhaft subtil dahinter".
(1) **Dunkler Löwe (Sprech-Blöcke):** stand mit visX=1142 fast komplett unter
Fenster+Panel (nur 22 px Rest) → unsichtbar. Jetzt visX 1142→620, visY
−110→330, visH 1300→1250, opacity 1→0,68. Damit liegt der komplette Kopf
mit Maul (0–55 % der Silhouetten-Breite) frei auf der Grafikfläche, Rumpf und
Läufe laufen ab x 1164 hinter Fenster+Panel durch (≈260 px Überlappung) und
unten aus dem Bild. Ton-in-Ton gemessen: PNG #252F3A auf #2E3A46 ergibt
#28323E ⇒ ~13 % Kontrast zur Fläche (Zielband 8–14 %). visY 330 hält ihn
unter der Headline und rechts der Takeaways/Plakette — kein Textkontakt.
(2) **Roter Löwe (Spotlights):** war volles #E30045 bei 90 % → Sticker-Optik
neben dem Fenster. Jetzt opacity 0,9 → 0,24 Grund (Flare-Peak 0,38, unter
Davids 45-%-Deckel), filter brightness(0,82) + blur(3px), visX 1290→1195
(≈85 px hinter der Panel-Kante 1280, Drift −30…+30 beibehalten → Überlappung
55–115 px), visH 1150→1180, visY 10→20. Ergebnis: tiefes Dunkelrot (gemessen
#46162D ruhig / #6A1937 im Flare) statt Vollton, weiche Kante, kommt hinter
dem zentrierten Fenster hervor. Kein Weiß, keine harten Kanten-Pops.
Zwischenschritt visH 1330/visY −30 wurde verworfen: Kopf oben angeschnitten,
Silhouette kippte in eine amorphe Masse.
`Loewe169` hat dafür eine optionale `filter`-Prop bekommen.

**Geliefert:** `Ergebnisse/Testframes-16x9/` — 03-team-headline,
04-tobi-takeaway (F1132), 05-hit-flare (F1900), 06-spotlight2-mitte (F2000)
neu gerendert, alle vier als Bild und per Pixel-Messung verifiziert.
tsc sauber.

**Entscheidungen/Offenes:** 03-team-headline wurde auf F600 gerendert, nicht
auf das im Auftrag genannte F560 — F560 liegt mitten in der Takeaway-Reveal
(Text bricht optisch), F600 ist der in v3 festgelegte Steady-State.
Composition-ID im CLI ist `man-wz-169-master` (nicht der Komponentenname
`ManWz169Master`). Sichtprüfung der neuen Löwen-Kalibrierung durch David offen.

## 2026-07-25 (nachts) — Umbau v6 (Review-2-Fixrunde v4): Jitter, Takeaway-Deckung, Endcard-Linie

**Gemacht:** Drei kritische Review-Befunde behoben. (1) **Nr. 2 endgültig:** Die
letzte X-Animation an Text — `translateX` im Headline-Wechsel (Composition.tsx
1052) — ist raus, Eintritt jetzt Fade + 12 px von unten, Austritt reiner Fade.
Zusätzlich werden Headline-Wechsel im Generator wie Plaketten sequenziert
(HEAD_PAUSE_ZIEL 0,5 s / MIN 0,4 s): K3 endet 107,0 → 106,2 s, ist 106,8 s
unsichtbar, K4 startet 107,3 s — die 0,30-s-Doppel-Headline auf offener Bühne
(F2685) existiert nicht mehr. (2) **Nr. 3 strukturell:** `takte_pausen()` hat
einen Modus `verzoegern` bekommen; Takeaways werden nie mehr gekürzt, die Pause
entsteht durch Verzögern des NEUEN Elements (Takeaway 6: Ein 51,15 → 51,60 s,
Takeaway 5 steht jetzt bis 50,20 = Blockende). Plaketten bleiben auf `kuerzen`
(Nr. 6). Neuer Guardrail prüft je Takeaway die Blockende-Deckung und warnt bei
Rückfall; `taktCheck.takeawayDeckungBlockende` zeigt Δ = 0,00 für alle Blöcke
außer 9 (Lara-Sperre, gewollt). (3) **Nr. 7:** Die rote Ambient-Wanderlinie
(2 px, volle Bildhöhe, wanderte durch jeden Frame) ist ersatzlos entfernt — sie
war der Kantenbalken bei x=1677 auf dem Fullscreen-Endscreen und widersprach
auch Nr. 12 („sehr clean").

**Geliefert:** `_intern/final-16x9/build_sync_plan.py` + beide `sync-plan.json`
neu (Status BESTANDEN, 0 Warnungen), `Composition.tsx` (ManWz169Master), tsc
sauber. `Ergebnisse/Testframes-16x9/` alle 10 Stills neu gerendert (F60/160/350/
600/1132/1900/2000/2450/2800/3400 — die Linie steckte in jedem Frame), dazu
9 Prüfframes in `/tmp/wzcheck-v4/`. Verifiziert: keine durchgehende 2-px-Spalte
mehr in irgendeinem Frame (Endcard x=1677 jetzt gleichmäßig #2E3A46), F2685
zeigt nur noch „MIT HERZ DABEI", F1250 (50,0 s) Takeaway 5 voll deckend,
F1290 Takeaway 6 im Reveal, Loop-Naht F0 ≙ F3549 (0 abweichende Pixel).

**Entscheidungen/Offenes:** Die Wanderlinie wurde komplett gestrichen statt nur
auf der Endcard ausgeblendet — sie war nirgends beauftragt und lief als harte
Kante über die Grafikfläche. Zwischen den Kapiteln 3 und 4 steht die
Grafikfläche jetzt 0,5 s ohne Headline (F2676) — bewusst, analog zum
Plaketten-Takt. Sichtprüfung durch David offen.

## 2026-07-25 — Umbau v7 (Review 3: vier Restbefunde)

**Gemacht:** (1) **Takeaway-Grad vereinheitlicht:** statt 56/52/48 px jetzt EIN
fester Grad 54 px für alle 12 Takeaways; die einzige Ausnahmestufe (46 px)
vergibt der Generator und nur bei echtem Spaltenüberlauf — gemessen mit
fontTools gegen 964 px nutzbare Breite, breiteste Zeile ist Block 7 mit 656 px,
also braucht KEIN Takeaway die Ausnahme. (2) **Plaketten-Hierarchie:** Name
44→58 px Cond Bold, Rolle 34→30 px bei 80 % statt 92 % Weiß, Kasten 120→131 px;
Verhältnis der Tintenhöhen 44:28 statt 34:26. (3) **Flare 76,0 s** — Ursache
sauber diagnostiziert: die Hüllkurve war korrekt (Frame 1900 = Peak 1,0) und
der Boost landete auch im Layer, aber der Glow saß zentriert bei (960|540) und
damit vollständig HINTER dem Fenster, und reines #E30045 hebt zwar Rot an,
senkt aber Grün/Blau — Luminanz nur +4 %. Jetzt breiter Wash in hellem MAN-Rot
(#FF3D6E) mit sichtbaren Flanken neben dem Fenster, kräftigerer roter Glow
dahinter und ein zweiter, 1,8× breiterer Streifensatz (#FF5C82). (4) **Fenster**
576×1024 bei y=28 → **540×960 bei y=60** (9:16 exakt, x=1200, Rand rechts 180),
vertikal zentriert; Schatten auf die 60-px-Ränder umgerechnet (Stufe 1 Blur 70/
y 6/0,34, Stufe 2 Blur 120/y 0/0,20) — läuft rundum aus statt abzubrechen.
Mitgezogen: Kantenbalken (1192–1199), Versatz-Panel, Spotlight-Mitte 672→690,
Face-Zone, Löwen-Überlappung (jetzt ≈233 px), Plaketten-Grenze.

**Geliefert:** `Composition.tsx` (ManWz169Master), `build_sync_plan.py` + beide
`sync-plan.json` (Status BESTANDEN, 0 Warnungen), tsc sauber. Alle 10 Stills in
`Ergebnisse/Testframes-16x9/` neu gerendert. Verifiziert per Pixelmessung:
Versalhöhe jetzt 39–41 px in allen Frames (Rest ist optischer Rundungsüberhang
von O/G/C, Zeilenabstand 65–67 px = 54·1,12+6) statt vorher 38–42 px durch drei
Schriftgrade; Flare F1900 gegen F1870 **+63,7 % Luminanz links / +41,6 %
gesamt** (vorher +4 %), Farbe (149|48|79) also klar rot, kein Weißblitz, Rampe
F1894 noch auf Grundwert; Fensterkanten x 1200–1740 / y 60–1020 in allen
Frames; Schattenabfall oben 43,7→53,2, unten 40,9→50,5 (Bühne 56,3) = weicher
Auslauf ohne Abriss; 10-endcard bei x=1677 keine Senkrechte (nur 26 % der
Zeilen abweichend = rechte Silhouettenkante des weißen Löwen, monotone Kante,
keine 1–3-px-Spitze im ganzen Bild).

**Entscheidungen/Offenes:** Fenster auf 540×960 statt der vorgeschlagenen
984er-Höhe — 984 ist nicht ganzzahlig 9:16, 540×960 ist exakt und deckt sich mit
den 9:16-Frame-Kompositionen weiter oben in der Datei; 60 px Rand geben dem
Schatten mehr Raum als 48. Die Breitenprüfung im Generator nutzt fontTools als
OPTIONALE Abhängigkeit — fehlt sie, läuft er stdlib-only durch und protokolliert
die übersprungene Prüfung. Sichtprüfung durch David offen.

## 2026-07-25 — Rollen final: nur Mechatroniker

**David:** Bei MAN gibt es keine „Mechaniker", nur Mechatroniker — gilt auch,
wenn Mitarbeiter sich im Interview selbst so nennen (Tobi: „bin normaler
Nutzfahrzeugmechaniker"). Marcel + Tobi → „Nutzfahrzeugmechatroniker";
Marcels Fachrichtung und Alexanders Stelle (Teilelager & Teileverkauf) von
David bestätigt. `build_sync_plan.py` (ROLLEN) angepasst, sync-plan neu
generiert (0 Treffer „Nutzfahrzeugmechaniker"), Frames 04/05/06 neu gerendert.
**In Gedächtnis gesichert** (man-wartezimmervideo): gilt für alle MAN-Projekte.

## 2026-07-26 — Finaler Export Ton-Fassung 16:9

**Davids Review 4:** (1) Musik-Hit-Flare bei 76,0 s („blitzt kurz auf") komplett
entfernt — Spotlights laufen jetzt gleichmäßig durch, Löwe pulst nicht mehr mit.
(2) Nach dem Videoende sprang das Bild auf den ERSTEN Frame (Julia) zurück:
Ursache war der `<Freeze>`-Layer hinter dem Videoende — die Freeze-Frame-Nummer
lag gegenüber der verschobenen Sequence-Zeitachse außerhalb des gültigen
Bereichs, Remotion fiel auf Frame 0 zurück. Layer ersatzlos entfernt; das
Fenster blendet stattdessen über 1,0 s (133,0–134,0 s) zu transparent ab und ist
exakt zum Materialende weg. (3) Endcard: Löwe bündig an der rechten Bildkante
(gemessen 1 px, Drift dort deaktiviert — sonst Spalt), Logo + Claim + Balken
mittig in der Fläche links davon.

**Geliefert (`Ergebnisse/Renders/`):**
- `MAN-Wartezimmervideo-16x9-Master.mov` — ProRes 422 HQ, 1920×1080/25p,
  PCM-Ton 48 kHz, 142,0 s (3550 Frames), 1,5 GB
- `MAN-Wartezimmervideo-16x9-Preview.mp4` — H.264 CRF 18, AAC, 76 MB

**Verifiziert:** Helligkeitsverlauf 133,5–135,5 s monoton (kein Sprung, kein
Blitz), Fenster ab 134,0 s vollständig weg, Endcard-Löwe bündig, Video in allen
Fenster-Positionen (fest rechts, mitten im Glide, mittig) bündig im Rahmen.

**Offen:** Musik (Artlist/Envato, Akt-Wechsel 0:17 und 1:16) legt David in
Premiere drunter · stumme Fassung als Render-Flag (`fassung: "stumm"`) ·
MAN-Freigabe 2023er Material (Ciattei) — Fallback-Flag `ohneCiattei` vorhanden.

## 2026-07-26 — 4K-Fassung (Davids Wunsch)

**Gemacht:** Dieselbe Komposition mit `--scale=2` gerendert — identisches
Layout, nur doppelte Pixeldichte. Glücksfall der Geometrie: Das Video-Fenster
misst im Design 540×960, bei 2× also exakt 1080×1920 = Auflösung der
ProRes-Arbeitskopie → Footage pixelgenau 1:1, kein Hochskalieren; Logo, Löwe,
Typo und Werkzeuge (alles Vektor) werden echt in 4K neu gezeichnet.

**Geliefert (`Ergebnisse/Renders/`):**
- `MAN-Wartezimmervideo-4K-Master.mov` — ProRes 422 HQ, 3840×2160/25p, PCM, 4,1 GB
- `MAN-Wartezimmervideo-4K-Preview.mp4` — H.264 CRF 18, AAC, 207 MB
(die beiden 1080er Fassungen bleiben daneben liegen)

**Verifiziert:** Layout maßstabsgetreu — roter Kantenbalken bei HD x=1192 und
4K x=2384, relative Position identisch 0,6208; Endcard-Löwe weiterhin bündig
(2 px bei 3840). Dauer/Framezahl/Ton in beiden Fassungen gleich (142,0 s,
3550 Frames, 48 kHz).

## 2026-07-26 — Drop-Shadow entfernt, alle vier Fassungen neu

**David:** Schlagschatten ums Video-Fenster raus. Zweistufiger boxShadow in
Composition.tsx gelöscht; die dunkle Grundfläche bleibt (verhindert Durchschein
beim Ein-/Ausblenden), Tiefe trägt jetzt allein das weiche Versatz-Panel.

**Geliefert — alle vier Renders neu (`Ergebnisse/Renders/`):**
- `MAN-Wartezimmervideo-4K-Master.mov` 3840×2160 ProRes 422 HQ · 4,1 GB
- `MAN-Wartezimmervideo-4K-Preview.mp4` 3840×2160 H.264 · 208 MB
- `MAN-Wartezimmervideo-16x9-Master.mov` 1920×1080 ProRes 422 HQ · 1,4 GB
- `MAN-Wartezimmervideo-16x9-Preview.mp4` 1920×1080 H.264 · 80 MB
Alle 3550 Frames / 142,0 s / 48 kHz.

**Verifiziert:** Am löwenfreien oberen Bildrand beträgt der Helligkeits-
unterschied zwischen freier Fläche und Fensterkante nur noch 3/255 (vorher
Schattensaum) — kein Schlagschatten mehr. HD- und 4K-Fassung inhaltlich
identisch.

## 2026-07-29 — Kundenfeedback Runde 1: Design

**Gemacht:** MANs 13 Änderungswünsche gegen timeline.json und sync-plan.json
gemappt — jeder Timecode trifft eindeutig ein Element. Aufteilung: 5 Wünsche
sind Bildschnitt (David/Premiere), 7 sind Grafikebene, 1 ist eine zusätzliche
Fassung. QR-Ziel recherchiert, Endcard-Varianten als Mockup vorgelegt.

**Geliefert:** `docs/superpowers/specs/2026-07-29-man-wartezimmervideo-kundenfeedback-design.md`

**Entscheidungen (David):**
- Schnitt tauscht nur Bilder, Längen bleiben → Tonspur und alle Animations-
  Timings bleiben gültig, keine Neu-Transkription. Gate vor der Umsetzung:
  ffprobe-Abgleich der neuen 9:16-Datei gegen die alte.
- Endcard Variante A (QR rechts auf dem Platz des Löwen, Text links),
  Standzeit 5 → 8 s, Master 142 → 145 s.
- Löwe ersatzlos raus; Spotlights tragen allein der verstärkte Werkzeug-Regen.
  Gegen meine Empfehlung (MAN-Halbbogen als Ersatzmotiv) — bleibt als Reserve
  dokumentiert, falls die 25-s-Lücke am Testframe leer wirkt.
- Untertitel klassisch unten im Videofenster, nicht auf der Grafikfläche.
  Gegen meine Empfehlung (540 px Fensterbreite ⇒ ~30 px Schrift, aus
  Wartezimmer-Distanz grenzwertig).
- „Azubi" fällt nur bei Nico, nicht bei Louis/Lara/Hannes.

**Befunde:**
- MANs Logo ist reiner Schriftzug im Halbbogen, kein Löwe darin — bleibt nutzbar.
- Die MAN-Karriereseite liegt unter dem Pfad `…/grosses-bewegen-mit-man.html`:
  „Großes bewegen mit MAN" ist MANs eigener Employer-Claim, der Kundenwunsch
  sitzt also im Corporate Wording.
- Mit dem CTA ist das Video ein Recruiting-Film. Folge: Laras Textsperre
  („muss ich mich hier bewerben", 101,0 s) entfällt — sie war nur wegen der
  Vorgabe „keine Recruiting-Botschaften" gesetzt.
- Ciattei-Block gilt als freigegeben: MAN hat ihn kommentiert und dabei nur
  Szenen beanstandet, nicht die Person.

**Offen:** Davids Schnitt · Spec-Freigabe · Umsetzungsplan · QR-URL
(`jobs.man.eu`) durch David/MAN bestätigen · HD-only für die stumme Fassung?

## 2026-07-29 — Mail 2 (Querformat + Löwen-Erlaubnis) & V2-Sichtung

**MAN-Mail 2:** (1) Produktszenen im vollen Querformat zeigen, gern aus den
Brandportal-Produktfilmen bzw. dem verlinkten Film („Großes bewegen mit MAN",
YouTube krzTgbNEVQc — gesichtet: nur ~8 s textfreie Produktstrecke bei 31–39 s,
1080p; Referenzkopie in `_intern/produktfilm-referenz/`). (2) Löwe DOCH
erlaubt, Auflage: **blickt immer nach rechts** — hebt das Verbot aus Mail 1
auf; Gedächtnis entsprechend korrigiert (Platzierung folglich immer links).

**Davids V2-Schnitt geliefert** (`Material/V2 Videodateien/`): Haupt 9:16
2160×3840 mit Ton (Quer-Parts schwarz) + Quer 16:9 3840×2160 stumm (nur
Quer-Parts). Beide HEVC 10-bit, 25 fps, 164,92/164,96 s.

**Verifiziert:** Quer-Strecken exakt 64,56–76,56 (12,0 s, dunkle
Studio-Produktshots) und 133,52–164,92 (31,4 s Fahraufnahmen-Finale,
Schwarzblende ab 163,92, Ton blendet mit). Timeline STEHT: Strecke 1 in der
alten 25,3-s-Lücke getauscht, Strecke 2 hinter Ciattei angehängt — Nico bei
64,4 im Bild, Louis bei 91, Dauer-Mathe passt. Keine Neuableitung nötig.
Musik ist eingearbeitet (Lücken −17 dB). 5 Szenentausche drin (Stichproben).
Haupt blendet 133,52–133,92 ab — liegt unter der Quer-Ebene, egal.

**Übergangs-Konzept (Antwort auf Davids Frage):** Blende statt Schnitt — das
Fenster wird zur Maske und wächst in 15 Frames auf Vollbild, Quer-Video läuft
bildschirmfest darunter. Harte Cuts an den fixen Frames sind Voraussetzung,
nicht Problem; an den V2-Dateien ist NICHTS zu ändern. Schließen 1 landet auf
der zentrierten Spotlight-Position; Öffnung 2 bleibt offen, Endcard kommt aus
der Schwarzblende. Master neu 175,0 s / 4375 Frames (Endcard 165–173, Ausklang
bis 175, Loop-Naht bleibt).

**Spec v2 geschrieben** (ersetzt v1: Löwe zurück statt raus, Quer-Ebene,
Master 175 s, Musik-Punkt erledigt). **Offen:** Herkunft/Auflösung
Quer-Material (Brandportal? nativ 4K?) · QR-Bestätigung · stumme Fassung
HD-only? · optional Musik-Outro unter Endcard · Spec-Review David →
Umsetzungsplan.

## 2026-07-29 — Review-Fix-Pass: 1-Frame-Dropout + Near-Black-Pop + Kopfkommentar

**Gemacht:** Drei Review-Befunde in Composition.tsx (Sektion 6 / ManWz169Master)
behoben, Commit `1331fde` im motion-Subrepo.

**(1) CRITICAL — 1-Frame-Dropout F1914 (Quer-1-Schließ-Naht):**
Die zeitbasierte Aktiv-Boundary `t > q.ende + 1e-6` ließ Frame 1914 (t=76,56=
q.ende) als aktiven quer-aktiv-State gelten, obwohl die Quer-1-Sequence bereits
bei F1913 endet — Ergebnis: leerer #0B1117-Kasten mit rotem Balken für 1 Frame.
Fix: framebasierte Boundary `fNow >= q.frameBis` (frameBis=1914 ist exklusiv).
Für bleibtOffen nur Untergrenze geprüft. Still-Befund: F1913 = Quer-Inhalt im
fast geschlossenen Fenster (roter TGX-Streifen) ✓; F1914 = Haupt-Video im
zentrierten Fenster mit Inhalt ✓.

**(2) MINOR 1 — Near-Black-Pop F4123 (Quer-2-Video-Ende):**
Quer-2-Video endet bei F4122 (Material-Schwarz); danach zeigte die offene
Fullscreen-Box ihren #0B1117-Grund. Fix auf BEIDEN Divs nötig (äußerer
Grund-Div + innerer Video-Container-Div mit overflow:hidden):
`querAktiv?.bleibtOffen && frame >= querAktiv.frameBis ? "#000000" : "#0B1117"`.
Pixel-Messung F4122: min=max=0 (Schwarz aus Material) ✓; F4123: min=max=0
(reines #000000, kein Aufhellen) ✓.

**(3) MINOR 2 — Stale Kopfkommentar:**
Altes Endcard-Timing (134/135/140/142 s, Frame 3549) auf v9-Stand umgeschrieben:
Quer-Blenden 64,56–76,56 + 133,52–Ende, CTA-Endcard 165,0–173,0, Ausklang
173,0–175,0, Loop-Naht F4374 ≙ F0.

**Naht-Diff:** PIL ImageChops.difference F4374 vs F0 → bbox=None, max diff=0,
identisch bestätigt. F4374 center pixel [46,58,70] = reines Anthrazit ✓.

**tsc:** Kein Output (sauber).

**Geliefert:** `tools/motion/src/clients/man/projects/wartezimmervideo/
Composition.tsx` (Commit 1331fde); Fix-Report angehängt an
`.superpowers/sdd/task-4-report.md`.

**Offen:** Vollrender ausstehend; Review-Pass war rein Still-basiert.

## 2026-07-29 — Umsetzung V2 (Quer-Blenden, CTA-Endcard, Untertitel): Testframes

**Gemacht:** Testframe-Satz für Kunden-Review produziert (Task 5).
Alle alten PNGs (v8-Stand, Löwe rechts) aus `Ergebnisse/Testframes-16x9/` gelöscht.
13 Ton-Stills und 3 Stumm-Stills der neuen `man-wz-169-master`-Komposition
(4375 Frames / 175,0 s) gerendert, alle als Bild verifiziert.
Loop-Naht per PIL geprüft: F0 ≙ F4374, bbox=None, max diff=0 — pixelidentisch.

Sichtprüfung aller 16 Frames:
- Quer-Blenden (05 F1620, 06 F1750, 07 F1907, 10 F3345, 11 F3700): öffnen/schließen korrekt,
  Vollbild randlos ohne Grafik-Elemente.
- Löwe links (02 F350, 08 F2050): Kopf frei ab y=21 (voll im Frame), dunkelrot/edel,
  Blick nach rechts — PASS.
- Endcard (12 F4250): QR-Kontrast sehr gut (Weiß 255 auf Anthrazit 46 = 209 Graustufen),
  CTA + Logo + Claim klar.
- Loop-Ende (13 F4374): reine Anthrazit-Fläche, kein Element.
- Stumm Julia (14 F150): UT auf dunklem Footage, Kontrast gut.
- Stumm Markus (16 F800): alle vier Elemente (Headline + Takeaway + Plakette + UT) sichtbar.

Abweichung: Brief nennt F2520 für Lara-UT; UT-Block „Muss ich mich hier bewerben" läuft
F2561–2604 — F2520 liegt vor dem Block. F2570 (Mitte des Blocks) genommen; im Report vermerkt.

**Geliefert:** `Ergebnisse/Testframes-16x9/` — 16 PNGs (01–13 Ton-Fassung, 14–16 stumm);
`.superpowers/sdd/task-5-report.md` (vollständiger Befund-Report).

**Offen (David — Review-Gate a–e):**
a) Look Blende auf/zu am Bewegtbild (05/07) — Standbild-Check nicht ausreichend.
b) Löwen-Position und -Intensität links (02/08) am Monitor.
c) Endcard-QR per Handy scannen (JOBS.MAN.EU bestätigen); URL-Label unterhalb
   QR im Standbild nicht gemessen — visuell prüfen.
d) UT-Dichte stumm (15-stumm-lara-bewerben-ut.png, F2570): Lara-Footage sehr hell,
   UT-Kontrast ~35–45 Graustufen — am Wartezimmer-TV (3–5 m Abstand) testen.
e) Stumme Fassung HD-only oder 4K? (offen seit 2026-07-26)

**Nachtrag (Kalibrierung + Final-Review, gleiche Session):**
(1) Endcard-Claim brach hässlich um („…MIT" / „MAN") → expliziter Zweizeiler
„GROSSES BEWEGEN" / „MIT MAN" (rot), Commit e84ea3f. (2) UT-Kontrast-Befund d)
direkt adressiert: Verlaufsband 150→200 px / 0,55→0,8 plus stärkerer
Text-Schatten — Lara-Frame deutlich lesbarer, TV-Check bleibt. (3) c) erledigt:
JOBS.MAN.EU-Label steht (Messfehler des Prüf-Skripts), QR aus dem GERENDERTEN
Frame real dekodiert → https://jobs.man.eu/. (4) Finaler Whole-Branch-Review
fand 1 Medium: Headlines K2/K4 fadeten 0,6 s in die öffnende Quer-Blende
hinein — Fade endet jetzt AN der Deadline (K2 63,8 s / K4 132,76 s), Commit
1dc21c2, Stills F1618/F3342 sauber. Testframes 05/10/12/14/15 ersetzt.
Commits gesamt (Sub-Repo tools/motion): 6e8ce08 · a7a3b70 · 2dfcb69 · 1331fde
· e84ea3f · 1dc21c2. Studio-Repo-Befund: tools/+projects/ gitignored, Motion-
Code lebt im Sub-Repo (MAN-Ordner dort erstmals eingecheckt, Plan korrigiert).
Gate a–e unverändert offen — Renders erst nach Davids Freigabe.

## 2026-07-29 — Render V2: 4K-Master (Ton-Fassung)

**David:** „Erstmal als Video rendern, nur eine 4K-Version, sonst nichts" —
Gate damit auf Sichtung am fertigen Video verlagert, Lieferumfang reduziert.

**Geliefert:** `Ergebnisse/Renders/MAN-Wartezimmervideo-V2-4K-Master.mov` —
ProRes 422 HQ, 3840×2160/25p, PCM 48 kHz Stereo, 175,0 s (4375 Frames), 6,65 GB.
Renderzeit ~6 min (ProRes-Arbeitskopien statt HEVC im Renderpfad).

**Verifiziert am gerenderten File:** ffprobe 4375 F/175,0 s exakt · Loop-Naht
F0 ≙ F4374 pixelgenau (Diff-Maximum 0) · Stichproben-Frames 64,8/76,4/140/168 s
zeigen Blende auf, Blende zu, Finale-Vollbild, CTA-Endcard mit QR korrekt.

**Offen:** Davids Sichtung des 4K-Masters (ersetzt Gate a–d) · stumme Fassung
+ weitere Formate NUR auf Zuruf (e bleibt offen) · QR-Bestätigung durch MAN.

## 2026-07-29 — Werkzeug-Fix + finale 4K-MP4

**Davids Befund am 4K-Master:** „Werkzeuge rechts fehlen, sonst passt alles."
Diagnose per Kontrast-Boost (8×): Silhouetten fehlten KOMPLETT — der
Werkzeug-Wrapper aus dem Seitentausch hatte keine Maße, Werkzeuge.tsx füllt
den Elternbereich (inset 0, overflow hidden) → 0×0-Kollaps, alles geclippt.
Zweite Ursache dahinter: Korridor 4–9 % wäre auch gefixt unsichtbar geblieben
→ auf 0,12–0,18 angehoben. Commit f58985c (Sub-Repo), Testframes 02/08 neu.
Lehre: „Subtile" Elemente in Stills nie per Augenschein abnehmen — Pixel-Diff
zweier Frames oder Kontrast-Boost messen (Review-Durchrutscher in Task 5).

**Geliefert:** `Ergebnisse/Renders/MAN-Wartezimmervideo-V2-4K.mp4` —
H.264 CRF 18, 3840×2160/25p, AAC 48 kHz, 175,0 s / 4375 Frames, 408 MB
(~18,6 Mbit/s). Verifiziert: beide Spotlights zeigen Werkzeuge rechts +
Löwe links, ffprobe-Werte exakt.

**Hinweis:** `MAN-Wartezimmervideo-V2-4K-Master.mov` (ProRes, 18:52 Uhr) ist
VERALTET (ohne Werkzeuge) — bei Bedarf neu rendern, sonst löschen.
**Offen:** stumme Fassung (HD/4K?) auf Zuruf · QR-Bestätigung MAN.

## 2026-07-31 — Finale Lieferung: UT-Fassung 4K-MP4, alte Renders gelöscht

**David liefert `Material/V2 Videodateien/MAN Wartezimmervideo_V2 Haupt_UT_V1.mp4`**
— identische Timeline (4124 F/25p), 1080×1920, Ton + EINGEBRANNTE Untertitel.
Ersetzt die geplante Remotion-UT-Ebene (die 42 Segmente bleiben als ungenutzter
Fallback hinter `fassung:"stumm"`). ProRes-Arbeitskopie wz-v2-haupt-ut-1080.mov,
videoSrc umgestellt (Sub-Repo 4518f7a), Kontroll-Frame: Davids UT im Fenster,
keine Doppel-UT, Grafikbühne unverändert.

**Geliefert:** `Ergebnisse/Renders/MAN-Wartezimmervideo-V2-UT-4K.mp4` —
H.264 CRF 18, 3840×2160/25p, AAC, 175,0 s/4375 F, **393 MB** (< 500-MB-Vorgabe).
Verifiziert an 4 Frames: UT sichtbar (Markus/Lara/Tobi), Endcard mit QR intakt.

**Gelöscht (Davids „lösche die alten"):** die 4 Erstlieferungs-Master/Previews
vom 26.07. + V2-ProRes (veraltet, ohne Werkzeuge) + V2-MP4 ohne UT — ~13 GB.
Alpha-Renders für den Cutter (insert/trenner/frames/opener/endcard) bewusst
behalten.

**Stand: MAN-Feedback beider Mails vollständig umgesetzt und ausgeliefert.**
Offen nur noch: QR-Ziel `jobs.man.eu` von MAN bestätigen lassen (Tracking?).

## 2026-08-07 — Finale MAN-Rückmeldung: Quer V3 + Standard-Abbinder (v10)

**MAN-Mail 3 (an Jan):** „Passt jetzt super", drei Punkte: (1) Produktszenen —
weniger Winter, weniger E-Truck, mehr TGE; (2) Schwertransporter-Szene am Ende
ganz raus (Kunde hat die Quer-Datei selbst neu geschnitten: V3); (3) Standard-
Abbinder ganz am Ende einbinden (MAN-Logo, Brand-Portal-Screenshot).

**Gate (ffprobe V3 vs V2):** identisch — HEVC 4K 10-bit, 25p, 4123 Frames,
164,92 s. Szenen 1:1 längengleich getauscht, Timeline/Ton unberührt. Punkte
1+2 stecken komplett in der Kundendatei; verifiziert per Vergleichsstreifen
(Winterszenen raus, TGE drin — bei 140,0 s fährt ein TGE 3.180; Strecke 1
bildidentisch zu V2, PSNR ~48 dB) und Luminanzmessung.

**Befund, der die Abbinder-Platzierung entschied:** V3 schneidet bei 160,2 s
HART auf Schwarz (YAVG 511→64, keine Materialblende) — der Kunde hat mit dem
Schwertransporter-Rauswurf exakt die Lücke für den Abbinder geschaffen
(4,7 s Schwarz vor der Endcard, Musik lief weiter). Abbinder daher IM Finale
vor der CTA-Endcard statt hinter ihr — Master bleibt 175,0 s/4375 F,
Endcard (165,0–173,0) und Loop-Naht unangetastet.

**Umsetzung (Generator v10 + Composition):** Logo-Ein 157,52–158,72 über der
letzten Fahrszene (Autobahn), Dimmer 158,92–160,2 übernimmt die CI-„Über-
blendung zum schwarzen Hintergrund" UND verdeckt den harten Material-Cut,
weißes Logo (700 px, zentriert, Position/Größe konstant — nur Opacity
animiert) steht 3,7 s auf Schwarz, Logo-Aus 163,92–164,92 synchron zur
Musik-Ausblende, ab 165,0 Endcard wie gehabt. Quer-Quellen auf
wz-v3-quer-a/b-2160.mov (ProRes Standard, Schnitt-Alignment per PSNR ~60 dB
bestätigt). Beat-Prüfung BESTANDEN (größtes Standfenster 3,72 s).

**Geliefert:** `Ergebnisse/Renders/MAN-Wartezimmervideo-V3-UT-4K.mp4` —
H.264 CRF 18, 3840×2160/25p, AAC 48 kHz, 175,0 s/4375 F, 369 MB (<500-MB-
Vorgabe). Verifiziert am File: ffprobe exakt, Abbinder-Phasen als Stills
(Logo über Fahrszene/auf Schwarz/Ausblende), Endcard+QR intakt, Ton −18,9 dB
mean, Loop-Naht F0 ≙ F4374 (verlustfrei Diff 0; im MP4 max 1/255).

**Betrieb:** Platte war <1 % frei — Chrome lehnte beim ersten 4K-Render
Fetches ab („disk space low", Render scheiterte). Gelöst: Render aus
schlankem Bundle (public-man-Spiegel, Videos als APFS-Clones) + verwaiste
Arbeitskopien gelöscht (wz-master-1080 = V1-Relikt, wz-v2-quer-a/b =
ersetzt; alle aus `Material/` regenerierbar). wz-v2-haupt-1080.mov (Fassung
ohne UT) bewusst behalten. Lehre: Render-Kommandos nie durch `| tail`
kürzen — maskiert Exit-Code und Fehlertext.

**Offen:** Davids/MANs Sichtung des V3-Masters · QR-Bestätigung (unverändert) ·
V2-UT-Render liegt daneben, Löschung auf Zuruf.
