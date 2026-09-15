# Protokoll — Förch / Messevideos / 2026-07 Messestand Schwarz Gruppe

## 2026-07-17 — Projektanlage & Transkription (Schnittplan-Workflow)

**Gemacht:**
- Neues Projekt angelegt (Charge „2026-07 Messestand Schwarz Gruppe").
- Footage-Analyse SSD `NIRO-SSD-02/05_Förch Messestand Schwarz Gruppe`:
  - `Gesprochene Takes/`: 6 FX3-Clips (FX3_0207–0211, 0224), ~24 Min gesamt
  - `Kamera-A B-Roll/`: 67 Clips (FX3_0171 ff.)
  - `Kamera-B Timelapse/`: 1 Clip (a7MK4)
  - `02_Video-Konzept/` und `01_Video-Onboarding/`: leer — kein Konzept vorhanden
  - Assets-Ordner: leer
- Transkription der 6 gesprochenen Takes gestartet (nur lesen, Cache in `_intern/`).

**Ziel-Deliverables (David, 2026-07-17):** 1 Messevideo quer + 3 Social-Media-Reels.

- Transkription abgeschlossen: 6/6 Clips OK, 182 Utterances
  (`_intern/transcripts_index.json`, `_intern/utterances.json`).
- Material-Analyse geschrieben: `Ergebnisse/O-Ton-Pläne/00-material-analyse.md`
  (Clip-Inventar, Personen-Hypothese, gesperrte Passagen, O-Ton-Kandidaten).

**Erkenntnisse:**
- Event: Karrieretag Familienunternehmen, Schwarz Gruppe Neckarsulm, Dreh 2026-07-10.
- Personen: Philipp (HR BP), Linda, Dennis Wortmann (Recruiter Vertrieb).
- Gesperrt: FX3_0224 02:06 (off-camera-Aussage) und 06:50 („Lidl"-Version;
  07:36 „Schwarz Gruppe"-Version verwenden).

**Entscheidungen (David, 2026-07-17):**
- Personen bestätigt: 0209/0210 = Linda, 0211 = Philipp, 0224 = Dennis Wortmann.
- Kein Kundenkonzept — Struktur frei konzipiert (Aftermovie ~90 s + 3 Reels).
- KEIN CTA auf den Endcards; Musik wählt der Cutter frei.

**Geliefert:**
- `_intern/script_structured.json` (Konzept, Sperren, Kannibalisierungs-Regeln)
- Dossier-Langfassungen: `Ergebnisse/O-Ton-Pläne/Dossier/video-1…4-*-lang.md`
- Cutter-Pläne: `video-1-aftermovie.md`, `video-2-reel-standrundgang.md`,
  `video-3-reel-karrieretag-facts.md`, `video-4-reel-team-insights.md`
- `01-projekt-grundlagen.md` + **`Foerch-Schnittanweisungen.pdf`**
  (10 Seiten: Deckblatt, 1 Übersicht, je Video 2 Seiten — Budget eingehalten)
- Zitat-/Timecode-/Sprecher-Verifikation gegen `utterances.json`: 24 Stellen
  geprüft, alle sauber (Fund dabei: Nieser+„Gesundheit."/Regie-„Danke." direkt
  am In-Punkt der 900-Kandidaten-Stelle 0211 03:50 — Warnung in Plänen ergänzt).

**Nachtrag (gleiche Session):** Linda-Interview wird im Schnitt als eine
Sequenz gelegt (0209+0210 direkt aneinander, David) — alle 0210-Stellen in
den Plänen auf Sequenz-TC umgestellt (0210 startet bei 03:54, exakt
+233,76 s = Dateilänge 0209); Regel auf Übersichtsseite dokumentiert,
PDF neu gerendert (weiterhin 10 Seiten, Budget ok).

**Nachtrag 2 — Motion (gleiche Session):** REC-Overlay für Video-2-Hook
gebaut (Remotion, neuer Client `tools/motion/src/clients/foerch/`,
Komposition `Foerch-RecOverlay`): Handy-Sucher-Look mit blinkendem
REC-Punkt (1 Hz), Batterie, Eck-Klammern, laufendem Timecode unten mittig.
Geliefert: `Ergebnisse/Renders/rec-overlay-hook.mov` (ProRes 4444 Alpha,
1080×1920, 25 fps, 5 s). Pre-Delivery Review ok: Face Zone frei, REC/Batterie
in Reels-Safe-Zone; Eck-Klammern + Timecode bewusst außerhalb (dekorativer
Sucher-Look). Props flexibel: blinkHz, showTimecode, uiScale.
Förch-`brand.json` nur als Platzhalter angelegt — **CI unbestätigt**, vor
erster CI-Komposition Styleguide einholen.

**Nachtrag 3 — Musik Video 2 (gleiche Session):** Song-Auswahl auf Artlist
(Browser): **„Now That We're Here" — Danny Shields** (Artlist Original,
Funk/Hip-Hop/Lofi, Moods Playful/Groovy/Carefree/Uplifting, 02:31) für das
Standrundgang-Reel; auf Davids Förch-Artboard gelegt. Alternativen notiert:
„1991" (Ido Maimon), „BKN" (Monako), „Happy Toes" (MooveKa), Album
„Delicious Ambitious" (Jürgen Brischar). Auswahl nach Tags/Metadaten —
finales Reinhören durch David.

**Nachtrag 4 — Video 3 Neuausrichtung (gleiche Session):** David fand v1
(„So läuft ein Karrieretag": Tagesablauf/Nachgang) inhaltlich schwach →
umgebaut zum Value-Reel **„Jobmesse richtig nutzen"** aus Zuschauersicht:
Hook „900 Bewerber. So stichst du raus." + 3 Recruiter-Tipps (Linda:
Lebenslauf einpacken · Philipp: vorher Plan machen — bislang ungenutztes
Kernzitat 0211 05:37 · Dennis: Trau dich, Kennenlernen kann Anfang von
vielem sein). Tagesablauf/Nachgang-O-Töne raus (bleiben Aftermovie).
Dateien ersetzt (`video-3-reel-messe-tipps.md` + Dossier-Langfassung),
Zitate verifiziert, PDF neu gerendert (10 Seiten, Budget ok).

**Nachtrag 5 — Video 4 Neuausrichtung (gleiche Session):** David: v1 wirkte
random (nur Dennis stellte sich vor, ohne Themen-Beitrag; Philipp doppelt).
v2-Regeln: keine Selbstvorstellungen (Linda hat außerhalb 0208 keine — „alle
oder keiner" → keiner, Bauchbinden tragen Namen), jede:r genau ein
Themen-Beat, Dennis als Klammer: Hook „unter Strom" → Closer „mal gucken,
was daraus noch wird" (0224 ca. 01:03, neu erschlossen). Dennis-Intro
„Königsdisziplin" gestrichen → aufgehoben für separate Recruiter-
Vorstellungs-Videos (Philipp schlägt die in 0209 03:27 selbst vor —
Folgeprojekt-Idee für Förch). PDF neu gerendert (10 Seiten, Budget ok).

**Nachtrag 6 — Video 4 v3 (gleiche Session):** David-Veto gegen den
„unter Strom"-Hook → FX3_0224 05:36–05:58 als Sperre aufgenommen (Pläne,
Grundlagen, Warnbox). Neuer Einstieg: Cold Open mit Lindas „jedes Gespräch
ist ein Highlight für sich"; Struktur jetzt 3 Beats (Linda → Philipp →
Dennis-Closer „mal gucken, was daraus noch wird", Langvariante ab 00:50).
PDF neu gerendert — Video 4 passt jetzt auf 1 Seite (gesamt 9 Seiten).

**Nachtrag 7 — Video 4 v4 + neue Doppel-Regel (gleiche Session):** David:
v3 zu kurz/dünn. NEUE REGEL: Zwischen den drei Reels doppelt sich nichts;
der Aftermovie steht für sich (Überschneidung Reel↔Aftermovie erlaubt) —
zentral in Grundlagen + script_structured dokumentiert, alte
Kannibalisierungs-Regel ersetzt. Video 4 dadurch als Tagesbogen mit
6 Beats (~50 s): Linda Wo-sind-wir → Philipp Aufbau/8–18 Uhr (Timelapse!)
→ Dennis Laufkundschaft → Linda Highlight/Spirit → Philipp 4. Karrieretag
→ Dennis „mal gucken, was daraus noch wird". Jede:r 2 Beats, Zeitmarker-
Captions (Tag 0 / 8:00 / 18:00). Übersichtsseite gestrafft (war auf 2 Seiten
gerutscht), PDF neu: 10 Seiten, Budget ok.

**Nachtrag 8 — Musik Video 4 (gleiche Session):** Artlist-Pick für das
Team-Insights-Reel: **„Itchy Feet" — Vens Adams** (Artlist Original,
Folk/Acoustic/Corporate, Moods Carefree/Playful/Hopeful, 98 BPM, 01:57,
Instrumente u. a. Ukulele/Claps/Whistle/Akustikgitarre — passt zum
„warm/organisch"-Briefing und zum Tagesbogen). Auf Förch-Artboard gelegt.
Alternativen (gleiche Filter Hopeful+Carefree): „Homebound" (Elijah Aaron),
„Northland" (Roie Shpigler/Ziv Moran), „Wild Grace" (Ziv Moran/Steven
Beddall). Auswahl nach Tags — finales Reinhören durch David.

**Nachtrag 9 — Aftermovie-Optimierung vor Schnittstart (gleiche Session):**
David beginnt den Schnitt → V1-Plan überarbeitet: (a) O-Ton-Budget von ~75 s
auf ~60 s gedrückt, zwei Musik-Breather fest eingeplant (Film soll atmen);
(b) Orts-Doppelung Beat 2/3 entschieden — Philipp-In erst bei „vertreten
heute Förch[e]" (ca. 00:11); (c) NEU Stand-Moment mit Lindas Öl-/„wo unser
Herz schlägt"-Zitat (FX3_0208 ca. 00:40, seit Doppel-Regel erlaubt; erster
Streichkandidat); (d) Streichreihenfolge definiert, Breather nie streichen.
Neue Zitate verifiziert, PDF neu gerendert (V1 weiterhin 2 Seiten).

**Nachtrag 10 — Musik Aftermovie (gleiche Session):** Zwei-Song-Konzept
(Davids Vorgabe: klassisch/cinematisch → freundlich): **Song 1 „Ascension"**
— Ian Post feat. Budapest Art Orchestra (Classical/Cinematic, echtes
Orchester, Theme Time-Lapse — passt zum Cold Open) für Beats 1–4;
**Song 2 „Shooting for the Stars"** — The North (Pop/Corporate,
Uplifting/Carefree/Hopeful, Claps/Bells) ab Breather 1 bis Ende.
Umschnittpunkt = Breather 1 (im Plan vermerkt, PDF neu gerendert). Beide
auf Förch-Artboard. Alternativen cinematisch: „The Time is Now" (Roberto
Prado), „Departure" (Steven Beddall). Auswahl nach Tags — David hört rein.

**Nachtrag 10b:** David findet die Picks noch nicht perfekt → je 3 weitere
Kandidaten geliefert. Cinematisch: „The Time is Now" (Roberto Prado),
„Departure" (Steven Beddall), „Graceful Trip" (Monument Music). Freundlich:
„Away Again – Creative Cut" (Campagna), „Northland" (Roie Shpigler/Ziv
Moran), „Hey – Instrumental" (Ziv Moran/Flint — Folk/Acoustic/Cinematic,
könnte als Brücke sogar beide Parts tragen). Links im Chat.

**Nachtrag 11 — Kunden-Feedback Video 4 (ca. 2026-07-20 via Frame.io):**
Linda Pfäfflin (Förch — bestätigt nebenbei Lindas Nachnamen, in Grundlagen
übernommen): „Ende wirkt etwas abrupt, kann das etwas verlängert werden?"
(0:48). Gestufte Lösung in V4-Plan dokumentiert: (1) Dennis-Closer auf
Langvariante ab 00:50 (+~10 s), (2) 4–6 s Musik-Outro mit warmer B-Roll +
weicher Blende statt Hard Cut in die Endcard, „Feierabend"-Caption dorthin,
(3) optional Philipp „nur positiv" (0211 00:48) als vorletzter Beat.
PDF neu gerendert.

**Offen:**
- FX3_0208 00:12 reinhören: sagt Philipp wirklich „Minijobben/Schwarzkopf"?
  (Entscheidet Intro-Nutzung in Video 2.)
- Förch-CI (Farben/Fonts/Logo) für künftige Motion-Arbeiten bestätigen.
- Duz-Wording der V3-Captions mit Förch-Tonalität abgleichen.
- Folgeprojekt-Idee an Förch: Recruiter-Vorstellungs-Videos für Karriereseite
  (Dennis' „Königsdisziplin"-Intro + Philipps eigener Vorschlag 0209 03:27).
- Lindas Positionsbezeichnung für Bauchbinde; Philipps Titel bestätigen.
- Zahl „900" bei Caption-Nutzung von Förch absichern.
- Hook-Freigabe Video 4 („von der Messe noch gar nichts mitgekriegt").
