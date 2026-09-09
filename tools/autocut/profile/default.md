# Schnitt-Profil „default" — Startregeln für B-Roll und Beat-Folge (NIRO Studio)

Gilt für alle Kunden, bis Stufe 4 aus den gelesenen Resolve-Timelines Profile je Videotyp
ableitet (`profile/<typ>.md` + `.yaml`). Die Zahlenwerte stehen in `profile/default.yaml`
und werden von `autocut_place_broll.py` hart geprüft; die Prosa hier ist die Entscheidungsgrundlage
für Claude beim Erstellen von `broll_plan.json` (siehe `prompts/place-broll.md`).

## 1. David-Regeln des Studios (gelten für jede Cutlist und jeden B-Roll-Plan)

1. **Höchstens 2 Takes derselben Person hintereinander.** Nie 3 oder mehr O-Töne derselben
   Interview-Person direkt aufeinander (Regel 02.08.2026, HBL). Zwei in Folge sind erlaubt
   (z. B. Christian #9/#10 als Scharnier). Verlangt der Plan dennoch drei, wird das im Bericht als
   Abweichung ausgewiesen — B-Roll dazwischen ersetzt keinen Sprecherwechsel, kann ihn aber
   dramaturgisch abfedern.
2. **Stärkste Aussage zuerst.** Erklär-/Bereichs-/Recruiting-Videos öffnen nie mit der
   Selbstvorstellung; Sekunde 0 ist der stärkste O-Ton (Zahl, Story, Klischee-Brecher), die
   Vorstellung folgt als Beat 2 (Regel 07.08.2026, Förch). Für B-Roll heißt das: der Hook-Beat
   bleibt ohne B-Roll — das Gesicht trägt den Einstieg.
3. **Keine Dopplung.** Was eine Ebene schon sagt, wiederholt keine andere: Keyword-Kasten,
   Bauchbinde, Caption, Untertitel und B-Roll-Bild dürfen dieselbe Information nicht doppeln
   (Regel 12.08.2026, LohiBW). Eine Caption „Zertifiziertes Weaning-Zentrum" braucht kein
   B-Roll-Bild, das eine Tafel mit demselben Text zeigt; ein O-Ton „wir gehen durch den Flur"
   braucht kein Flur-Bild um seiner selbst willen. B-Roll ergänzt (Beweis, Ort, Emotion), es
   illustriert nicht wörtlich.
4. **„(m/w/d)" bei jedem Berufstitel.** Auf jeder Job-/CTA-Endcard und überall, wo ein Berufstitel
   eingeblendet wird (Regel 15.07.2026, WLC). Betrifft Caption-/Endcard-Beats — im B-Roll-Plan
   als Hinweis im `grund` festhalten, wenn ein Endcard-Beat gefüllt wird.
5. **Nur Website-belegte Inhalte** in Kundendeliverables; Vergütungs-O-Töne und Kunden-Tabus aus
   dem Plankopf sind Sperren, keine Ermessenssache. B-Roll unterliegt denselben Sperren
   (Clip-Pfad + Zeitbereich in `cutlist.json` → `sperren`).

## 2. B-Roll-Regeln v2 (Feedback 04.09.2026, Zahlen in `default.yaml`)

- **Verteilung:** 80–85 % der Timeline liegt B-Roll auf V3, 15–20 % ist der Sprecher zu sehen. Der Sprecher ist in
  **Fenstern** sichtbar: am Anfang jedes O-Ton-Beats 2,5 s beim ersten Auftritt der Person, sonst 2,0 s (1,5–4,0 s
  wählbar); zusätzliche Fenster mitten im Beat nur für einen Peak (Pointe, Emotion). Ganz-Gesicht-Beats: der Hook
  (Beat 1), Beats mit „Gehaltenes Gesicht"/„Bookend" im Plan, Beats unter 3 s. „Frontal" in der Bild-Spalte beschreibt
  nur die Einstellung des Fensters, nicht „Gesicht halten".
- **Keine Schwarzframes:** Zwischen den Fenstern laufen **Strecken**, die V3 lückenlos füllt — über Pausen,
  Platzhalter, Beat-Grenzen und den Endcard-Platzhalter hinweg (die Grafik kommt später von Motion, der Beat-Marker
  sagt es). Jede Strecke ist mindestens so lang wie der kürzeste Shot (2,0 s): das Raster schiebt dafür
  Standardfenster automatisch per `offset_s` weiter nach hinten; bei eigenen Plan-Fenstern meldet `--raster` eine
  zu kurze Strecke stattdessen als Fehler.
- **Szenen statt Einzelshots:** Eine Szene sind mindestens 3 aufeinanderfolgende Shots aus **einem** sortierten
  Ordner (Standort + Motiv-Ordner), mit Einstellungswechsel von Shot zu Shot: Establishing (Totale/Halbtotale) →
  näher → Detail, oder als Enthüllung umgekehrt. Ausnahmen (mit `ausnahme`-Text): Plan-Kommentar „Wechselschnitt
  beider Häuser"/„Gesichter-Montage" (Shot-für-Shot-Wechsel S1/S2), Einzel-Einschub aus einem kleinen Ordner,
  Strecken unter 6 s.
- **Cut-Flow:** Zwei aufeinanderfolgende Shots haben nie dieselbe Einstellung **und** Perspektive **und**
  Brennweitenklasse; nahezu gleiche Kadragen (Setup-Abstand) vermeiden. Bewegungsrichtungen nicht gegeneinander
  schneiden (links→rechts auf rechts→links nur mit Absicht).
- **Längen:** über O-Ton 2,0–5,0 s je Shot (Zeitlupe bis 6,0 s); in Platzhaltern 1,5–3,0 s; „Schnelle Cuts"
  1,0–2,0 s; „Halbes Tempo" = Obergrenzen ausreizen. Der letzte Shot einer Strecke wird vom Code auf die Reststrecke
  gesetzt.
- **Zeitlupe (`tempo`):** 2× nur für 50p-Clips, 4× nur für 100p-Clips (echtes Konformieren). Ja bei Händen,
  Geräten, Gehen, ruhigen Fahrten, Details; nein bei sprechenden Menschen, schneller Aktion, sichtbarer Hektik. 4×
  nur für bewusst langsame Momente. Zeitlupen-Shots dürfen länger laufen und tragen ruhige Aussagen.
- **Bildlogik zur Aussage, Standort-Regeln, Sperren, Mängel, Bild-Spalte zuerst, Keine Wiederholung:**
  Standorte werden im Bild nicht benannt, wenn der Plan es nicht vorsieht; Handkamera-Wackler nur als
  bewusstes Stilmittel („Puls"); Beweis-Aussage → Beweis-Bild, Emotion → Mensch ohne Blick in Kamera,
  Team → Gruppe; „Nur S1!"/„Nur S2!" strikt; Sperren aus `cutlist.json` gelten auch für B-Roll; keine
  Abschnitte mit Mängeln „Blick in Kamera", „Crew im Bild", „Logo/Marke"; kein Clip zweimal im Video;
  Abweichung von der Bild-Spalte nur mit `abweichung_grund`.
- **Ton:** B-Roll ausschließlich auf V3 ohne Audio.

## 3. Was der Code prüft (Abbruch) und was Warnung bleibt

Fehler: Fenster außerhalb 1,5–4,0 s oder außerhalb des Beats oder an Nicht-O-Ton-Beats; Gesichtsanteil unter 12 %
oder über 23 %; Strecke fehlt/leer (Schwarz); Shot ragt über das Streckenende; letzter Shot nicht anpassbar;
Shot-Länge außerhalb der Grenzen; `tempo` ohne passende Clip-Bildrate; Bereich nicht verwendbar; gesperrter Mangel;
Sperre; „Nur S1/S2"; Clip doppelt; Szene mit < 3 Shots ohne Ausnahme; Szene aus mehreren Ordnern ohne Ausnahme;
Cut-Flow-Verstoß (Einstellung + Perspektive + Brennweite gleich); Abschnittsfelder fehlen (Nachlauf nicht gelaufen);
Abweichung ohne Grund. Warnung: Gesichtsanteil außerhalb 15–20 %; Setup-Abstand < 10; Szene ohne
Einstellungswechsel; mehr als 3 Ausnahmen; Qualität < 3; Shot ohne Grund; `tempo` 4.
