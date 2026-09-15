# Protokoll — HBL / Imagefilm / 2026-07 Szenen

## 2026-07-23 — Projekt angelegt, alle Szenen transkribiert

**Gemacht:**
- Neues Projekt angelegt (Kunde HBL, Projekt Imagefilm, Charge „2026-07 Szenen").
- Kundenfeedback zu den Szenen (Juli 2026) als Konzept-Dokument abgelegt:
  `Material/Konzept/Kundenfeedback-Szenen.md`.
- Alle 51 Szenen vom NAS transkribiert (ElevenLabs Scribe, Diarisation, gecacht):
  Quelle `NAS: …/HBL Management GmbH/02_Projekte/01_Projekt-1xImagefilm_4xAds/03_Medien/HBL Szenen/`
  — Gruppen A (5), M (8), S (3), TA (26, André/HiServ), TP (9, Philipp Eric
  Breitenfeld, Humanus). 51/51 ok, keine Fehler.

**Geliefert:**
- `Ergebnisse/Transkripte/uebersicht.md` — alle Szenen mit Dauer, Kundenfeedback, Textbeginn.
- `Ergebnisse/Transkripte/{A,M,S,TA,TP}.md` — Volltranskripte mit Zeitmarke pro Satz,
  Sprecherwechsel markiert (Regie-Kommentare sichtbar), Kundenfeedback je Szene im Titel.
- Renderer: `_intern/render_transkripte.py` (aus `_intern/transcripts_index.json` + Cache).
- `Ergebnisse/Transkripte/TA-aehm-liste.md` — Ähm-Schnittliste für André (Kundenwunsch):
  133 Ähms in 26 TA-Szenen, je mit von/bis-Timecode und Wortkontext (`_intern/aehm_liste.py`).

**Entscheidungen:**
- Scribe-Verhörer „HRE"/„HWL" → „HBL" korrigiert (im Renderer dokumentiert;
  Roh-Transkripte im Cache bleiben unverändert).
- Timecodes der Transkripte passen zu den Kundenangaben (S3 „ab 0:10", M2 „ab ~0:12").

**Offenes:**
- Kunde wünscht: Ähms bei André (HiServ) rausschneiden; bei Humanus bessere
  Kameraperspektive wählen. Die zweite Humanus-Perspektive liegt NICHT in
  `HBL Szenen/TP/` (dort nur eine Datei pro Szene), sondern als Rohmaterial in
  `03_Medien/01_Footage/Testimonial2/` (FX3 + a7MK4).
- S1/S2: Kunde will Ergänzungen einfügen (siehe Feedback-Dokument); A1 braucht
  andere Einleitung.
- TA-Szenen ohne Kundenbewertung (TA1–3, 5, 7, 8, 10, 11, 13, 15–20, 25, 26)
  stehen als Reserve zur Verfügung — Transkripte liegen vor.

## 2026-07-23 (2) — Schnittplan-Entwurf Imagefilm

**Gemacht:**
- Imagefilm-Dramaturgie aus den 25 vom Kunden bewerteten Szenen entworfen
  (Struktur: Problem-Hook aus Kundenmund → Grafik „zwei Säulen" → Block
  Säule 1 Lohnbüro → Block Säule 2 Software/Prozesse → Zahlen → Vertrauen →
  Empfehlung TA23 → CTA A5). Alle Kundenmarken eingearbeitet (S3 ab 0:08/0:10,
  M2 ab 0:09, A1 ohne Original-Einleitung, Ähm-Pflicht, TP-Perspektiv-Check).

**Geliefert:**
- `Ergebnisse/O-Ton-Pläne/HBL-Imagefilm-Schnittplan.pdf` (4 Seiten: Titel +
  Übersicht + 2 Seiten Video — Davids Format, Budget eingehalten).
- `Ergebnisse/O-Ton-Pläne/01-projekt-grundlagen.md`, `video-1-imagefilm.md`
  (Kompakt) + `Dossier/video-1-imagefilm-lang.md` (Langfassung mit allen
  Alternativen), `_intern/pdf_meta.json`.

**Entscheidungen (NIRO-Vorschläge, nicht Kunde):**
- Ziellänge ~3:00 mit dokumentiertem Kürzungspfad auf 2:45.
- 40 %-Claim als O-Ton M1 (0:19–0:26) im Säule-2-Block; TP6 nur mit
  Pflicht-Caption „Ohne HBL:"; TA18 („20 %") gesperrt bis Freigabe.
- A1-Einleitung + S1-„mit uns" als Caption-Lösung vorgeschlagen (statt
  Neuaufnahme) — Entscheidung offen.
- Unbewertete Szenen nur als Reserve/Alternativen geführt, klar markiert.

**Offenes (an David/Kunde):** Ziellänge/Format 16:9, Sprechernamen für Inserts
(HBL-Sprecherinnen + André-Nachname, Schreibweise HiServ), Factorial-Nennung
(TA4), S2-Kontext, Humanus-Perspektive je TP-Szene, Endcard-Text/URL.

## 2026-07-23 (3) — Revision: Ziellänge 2:00

**Anlass:** David: geplant waren 2:00 („bisschen Abweichung okay") — Erstentwurf
war auf ~3:00 ausgelegt.

**Gemacht:** Kern auf 15 Beats / ca. 2:17 gestrafft. Rausgefallen aus dem Kern
(alle als Erweiterungspfad/Alternativen dokumentiert, keine Kunden-Szene
verworfen): TA6 (Doppel-Hook), TA12 (Erweiterung Prio 1), M3 (Erweiterung
Prio 2, inkl. Säulen-Brücke), TA14 (durch TA24-Kurzfassung abgedeckt), M6.
M2 auf 0:09–0:21 gekürzt (Schlusssatz im Erweiterungspfad), TP5 auf 0:00–0:11,
TA24 auf 0:13–0:18, A1 gerafft (0:02–0:08 + 0:18–0:29).
Neu: Kürzungspfad auf ~2:00 und Erweiterungspfad auf ~2:45 im Plan.
PDF neu gerendert (4 Seiten, Budget ok, keine Glyph-Artefakte).

## 2026-07-23 (4) — Revision: Timecodes auf DaVinci-Gesamttimeline

**Anlass:** David schneidet alle Szenen als EINE Timeline in DaVinci (ohne
Einzeldatei-Nummerierung — die war nur für den Kunden).

**Gemacht:**
- Echte Cliplängen per ffprobe (NICHT Transkript-Enden — die sind kürzer,
  hätten über 51 Clips gedriftet) → `_intern/clip_durations.json`.
- Timeline-Offsets `_intern/timeline_offsets.py` → `timeline_offsets.json`;
  Annahme: Reihenfolge A→M→S→TA→TP, Gruppe aufsteigend, Stoß an Stoß,
  Gesamt 17:08. **Verifikations-Anker: TP9 startet TL 16:45.**
- Alle Ausgaben auf TL umgestellt: Transkripte (Sätze + Übersicht),
  Ähm-Liste (von/bis in TL), Schnittplan kompakt + Dossier + Grundlagen,
  PDF neu. Neue Zuordnungstabelle `Ergebnisse/Transkripte/00-timeline-referenz.md`.
- Rundung vereinheitlicht auf Abschneiden (TC zeigt nie hinter den Moment);
  20 Plan-Werte um 1 s korrigiert.

**Offen:** Timeline-Annahme von David bestätigen lassen (TP9 = TL 16:45?);
bei anderer Reihenfolge: `timeline_offsets.py` anpassen, alles neu generieren.

## 2026-08-31 — Kundenfeedback Runde 2: Digitalisierungs-Wording (Opener + Endcard neu)

**Anlass:** Review-Kommentare von Susan + Anne Christine (ca. 11.08., via
Screenshots von David; bei Kommentar 4 lt. David nur der Teil nach „//"):
(1) 0:02,6 Klartextzeile: „Nur Digitalisierung, nicht HR-Digitalisierung
(identisch mit Website)" · (2) 0:03,0 „Hier bitte unser Banner eingeben >
sieht es gut aus? wenn nicht, draußen lassen" · (3) 0:04,6 Säule 2: groß
„Die Digitalisierung deiner Personalabteilung", klein darunter „HR-Software
& Prozesse", auf Stimmigkeit achten · (4) 2:47,5 Endcard: „Grafik anpassen
wie am Start".

**Backup vorab (Davids Auftrag):** kompletter Ist-Stand als APFS-Clone nach
`_intern/backup/2026-08-31 Stand vor Feedbackrunde-2/` (alle 22 Renders +
Motion-Quellcode + Logo-PNGs, 2,4 GB).

**Umgesetzt (Wording-Beleg Website-Startseite: Hero „Wir digitalisieren
deine Personalabteilung", Leistungs-Kachel „Digitalisierung"):**
- Klartextzeile überall: „Dein Partner für Lohnabrechnung & Digitalisierung".
- Säule 2 in den Säulen-Bausteinen: Titel „Die Digitalisierung\ndeiner
  Personalabteilung" (2-zeilig per festem Umbruch, 72 statt 86 pt, damit
  es die 1240er-Säule hält) + neue optionale Sub-Zeile „HR-Software &
  Prozesse" (Futura Medium 46, wie Badge-Subline). Säulen-Reihe auf
  flex-start: die Nummern 01/02 fluchten exakt (im 4K-Still gemessen,
  y 897 = 897), der Sub steht frei darunter — Susans „rechts steht mehr"-
  Sorge damit ausbalanciert.
- Endcard „wie am Start": Titel neben der 02 jetzt als 2-Zeilen-Stack +
  Sub-Zeile; Nummern bleiben auf einer Flucht.
- Safe-Zone-Review (Stills f75/f145/f220 + Endcard f150) bestanden.

**Geliefert:** `21-opener-deine-hr-agentur.mov` (9,5 s) + `10-endcard.mov`
(8 s) NEU — beide 4K ProRes 4444 Alpha, Formate per ffprobe geprüft.

**Entscheidungen:**
- **Banner draußen gelassen** (von der Kundin explizit erlaubt): Es liegt
  kein Banner-Asset vor — nicht in `Material/CI/`, nicht in der Guideline,
  kein Banner-/Marquee-Element auf der Website. Der Website-Hero-Claim als
  „Banner" würde sich mit der neuen Säule 2 (1,4 s später) fast wörtlich
  doppeln. **Bei HBL klären, ob eine Banner-Datei existiert** — dann gern
  nachrüsten und beurteilen.
- Titel-02-Badge (`03`, „HR-Software & Prozesse" + Subline) und
  Säulen-Fokus-02 (`16`) bewusst NICHT neu gerendert: kein Kundenkommentar
  an diesen Stellen. Der CODE trägt das neue Säule-2-Wording aber bereits
  in Säulen-Grafik/Fokus 01+02/Master — Neu-Render von 01/15/16/00 genügt
  auf Zuruf (Muster wie Eintrag 2026-08-03 (5)). Achtung: 16 im Cut hieße
  dann groß „Die Digitalisierung deiner Personalabteilung" beim
  Säule-2-Blockwechsel — Konsistenz-Entscheidung liegt bei David.
- Kommentar 4, Teil vor „//" (Bild „wir 3 durch die Tür" bei 2:47) =
  Schnitt-Ebene (David/DaVinci), keine Grafik-Aufgabe. Falls die Endcard
  ÜBER dem Foto liegen soll: aktuelle Endcard ist Vollfläche Eierschale —
  BG-freie Variante wäre ein kurzer Folgeauftrag.

**Nachtrag (gleiche Session):** Davids Rückfrage per Screenshot (Karte bei
~1:01, Blockwechsel Säule 2): auch dort anpassen, „von der Logik her", trotz
fehlendem Kundenkommentar → `16-saeulen-fokus-02-hr-software.mov` NEU
(Fokus-Endzustand geprüft: Säule 2 groß mittig inkl. Sub, Safe Zone ok) +
Konsistenz-Nachzug `15-saeulen-fokus-01-lohnbuero.mov` und
`01-wer-ist-hbl-saeulen.mov` NEU (Alternativ-Karten, lagen sonst mit altem
Wording im Ordner). Formate geprüft (4444/Alpha). Jetzt trägt nur noch der
eingefrorene Master (00) das alte Säulen-Wording als Datei; Titel-02-Badge
(03) weiterhin bewusst unverändert.

**Nachtrag 2 — Banner eingebaut:** Das Kunden-„Banner" ist der Claim
„PERSONAL. LOHN. DIGITAL!" (Kirschrot auf Eierschale, N27; David hat das
Bild nachgereicht). Empfehlung „einbauen" von David bestätigt → im Opener
nativ als N27-Text gesetzt (nicht als PNG — randscharf in 4K): unten mittig
in der Position/Größe der roten Säulen-Klartextzeile (bottom 210, 58 pt,
Versalien, Spacing 12), Einblendung bei 0:02,9 (Kundin-Marke), bleibt über
die Säulen-Phase stehen (Phase 1 allein wäre nur 0,8 s Lesezeit), weicht
mit dem Fokus-Switch (6,4 s). Als Props steuerbar (banner/bannerAtSec).
Safe Zone geprüft (Stills f85/f145). `21-opener-deine-hr-agentur.mov`
erneut ersetzt (Format geprüft). Banner-Frage damit erledigt.

**Anlass:** Davids Frage, ob Säule 1 zu kurz kommt. Analyse: zeitlich
ausgeglichen (~51 s vs. ~48 s O-Ton), aber KEINE bewertende Kundenstimme
für Säule 1 im gesamten Material (beide Testimonial-Geber sind
Digitalisierungs-Kunden). TA9 als Kandidat mit Schnittmarken aufbereitet
(Kurzfassung ~13 s, Wort-TCs geliefert) — dann auf Davids Einwand
verworfen: TA9 beschreibt nur HiSERVs ANFORDERUNGEN (Compliance, korrekte
Abrechnung), bewertet HBL aber nicht → kein Mehrwert.

**Entscheidung:** Säule 1 bleibt mit der A1-Story als Beweis (trägt);
bei Kundenfreigabe aktiv Nachdreh-Empfehlung „Lohnbüro-Testimonial"
aussprechen (auch für die 4 Ads relevant). Optional für den
Vertrauens-Block: TA22 (TL 12:54–12:59, „konstruktiv, zuverlässig und
zielführend", 1 Ähm) — einzige ungenutzte echte Kurz-Bewertung,
übergreifend, kein Muss.

## 2026-08-03 (11) — Struktur-Beratung Einstieg + Brand-Opener

**Anlass:** David: TP2-Hook (Breitenfeld) wirkt „lost" (Säule-2-Inhalt vor
Säule-1-Block, Person verschwindet danach lange); Wunsch nach alternativem
Einstieg mit „etwas Allgemeinem zu HBL".

**Beratung (an David):** Kein O-Ton mit allgemeiner HBL-Vorstellung
vorhanden (bekannte Lücke) → Allgemeines muss von der Grafik-Ebene kommen.
Empfohlene Struktur: Brand-Opener am Anfang · TP2 an den Säule-2-Start
verschieben (Fokus-02 → TP2 „Durcheinander" → M2) — Take bleibt genutzt
(Kunde: „gut"), Breitenfeld im richtigen Kontext.

**Gemacht:** Neue Comp `HBL-Opener` (9,5 s): Punkt → Logo →
„DEINE HR-AGENTUR" (Website-wörtlich!) + Klartextzeile → Texte weichen,
Säulen 01|02 erscheinen → Fokus gleitet auf 01 → Outro. Phasen-Zeiten
(saeulenAtSec 3,6 / fokusAtSec 6,4) und alle Texte als Props.

**Geliefert:** `21-opener-deine-hr-agentur.mov` (9,5 s, 4K ProRes 4444
Alpha) — ersetzt am Filmanfang die Fokus-01-Karte (15 bleibt als
Alternative liegen); 16-Fokus-02 für den Blockwechsel. Master unverändert.
Nachtrag: Auftakt-Punkt vor dem Logo auf Davids Wunsch entfernt
(Opener beginnt jetzt direkt mit dem Logo-Aufbau); Datei ersetzt.

## 2026-08-03 (10) — Textlose Split-Blende als Datei

**Anlass:** David: noch eine Transition ohne Schrift. Die Comp
`HBL-SplitBlende` existierte bereits (Eintrag 4, Datei war durch die
Kunde-begeistert-Version ersetzt worden) → als eigene Datei gerendert.

**Geliefert:** `20-split-blende-ohne-text.mov` (1,8 s: Türen zu →
Punkt-Beat → Türen auf; universell für jeden Schnitt, Mitte ~0,7 s
auf die Schnittstelle legen).

## 2026-08-03 (9) — M1-Karte: „Weniger Fehler" + „Schnellere Durchlaufzeiten" + −40 %

**Anlass:** David: kleine Animation zu „Weniger Fehler / Schnellere
Durchlaufzeiten", kombiniert mit der 40-%-Einsparung; Countdown-Style
beibehalten.

**Gemacht:** Neue Comp `HBL-ErgebnisseM1` (eigene Komponente, Master-Code
unangetastet): Eierschale-Karte unten rechts, wortsynchron zum M1-Satz —
Punkt „Weniger Fehler" (1,1 s) · Punkt „Schnellere Durchlaufzeiten"
(2,3 s) · dann „bis zu −40 % Zeit & Kosten" mit Zähl-Animation ab 4,1 s.
Timings aus Cut02-SRT (Clip ab TC 01:01:44,8), alles als Props.
Face-/Safe-Zone geprüft (y 1156–1939).

**Geliefert:** `04-ergebnisse-m1-mit-40prozent.mov` (7 s, 4K ProRes 4444
Alpha) — ERSETZT `04-zahl-minus-40-prozent.mov` (gelöscht; die pure
Zahl-Karte bleibt als Comp `HBL-Zahl40` im Studio verfügbar).

**Nachtrag (Feinschliff):** Countdown mit führender Null („−07 %",
padStart — Zahl springt nicht mehr in der Breite), Punkte linksbündig,
Trennlinie + mehr Abstand zwischen Punkten und Zahl-Block. Datei ersetzt.

**Nachtrag 2 (Zitter-Fix):** Karte atmete beim Zählen weiter (Breite folgte
dem Inhalt, N27-Ziffern sind proportional). Fix: feste Kartenbreite
(1020 px content) + jede Ziffer in fixem 0,66-em-Fach (Anzeigetafel-
Prinzip). Verifiziert: Kartenkanten über Countdown-Frames pixelidentisch
(x 2620–3639). Datei erneut ersetzt.

## 2026-08-03 (8) — Ergebnis-Checkliste für den S3-Part

**Anlass:** David: „Animation für den gesamten S4 part" — gedeutet als
vierter Sprech-Part = S3-Passage („Umsetzung und laufende Betreuung …
Kerngeschäft", TC 01:00:47–01:01:01; einziger Part ohne Grafik).

**Gemacht:** `HBL-ChecklisteS3` — Eierschale-Karte unten rechts, 5
Ergebnis-Punkte mit Punkt-Bullets erscheinen WORTSYNCHRON zum O-Ton
(Timings aus dem Wort-SRT; als Props editierbar): Umsetzung & laufende
Betreuung (0,4) · Mit Lohnabrechnung nichts mehr zu tun (3,7) ·
Fehlerfreie, pünktliche Auszahlung (7,0) · Ohne Nachläufe &
Korrekturschleifen (9,2) · Zeit für dein Kerngeschäft (11,7). Alle
Texte aus dem S3-O-Ton. Face-/Safe-Zone geprüft.

**Geliefert:** `19-checkliste-s3-ergebnisse.mov` (14,4 s, 4K ProRes 4444
Alpha) — bei TC 01:00:47,0 auflegen, dann sitzen die Punkte auf den
gesprochenen Worten. Master unverändert.

**Nachtrag (gleiche Session):** David hat den S3-Take jetzt KOMPLETT im
Schnitt (inkl. „Wir starten mit einer klaren Analyse…") → Checkliste auf
7 Punkte erweitert (+ „Klare Analyse: Was lief bisher schief?" bei 0,6 ·
„Individuelle, einfache Prozesse" bei 3,4; Folge-Punkte auf
Take-relative Zeiten 8,3/11,3/14,4/16,2/19,3 verschoben — Quelle S.md,
da noch kein neues Cut-SRT). Datei ersetzt (22 s), Schrift minimal
kleiner (7 Zeilen), Karte y 1215–1939 = Face-/Safe-Zone ok. Clip am
Take-ANFANG anlegen. **ACHTUNG Kundenmail:** Kunde hatte S3 explizit erst
„ab 0:10" markiert — der Analyse-Anfang war ausgeklammert. Jetzt volle
Szene im Cut → bei Kundenfreigabe aktiv erwähnen.

**Nachtrag 2:** Nach dem Kundenmail-Hinweis nimmt David den S3-Anfang
wieder RAUS → Checkliste auf die 5-Punkte-Version zurückgebaut
(14,4 s, Timings 0,4/3,7/7,0/9,2/11,7, Schriftgröße wieder 54).
Datei erneut ersetzt; Auflage-Punkt bei TC 01:00:47,0 gilt wieder.
Kundenmarke S3 „ab 0:10" damit eingehalten (In bei 0:08 = Satzanfang,
wie gehabt bei Freigabe nennen).

## 2026-08-03 (7) — Blende „Das sagen unsere Kunden"

**Anlass:** David: Transition wie „Der Kunde war begeistert" für den
Testimonial-Block; Wording gegen Website prüfen.

**Wording-Check:** Website hat KEINEN Kundenstimmen-/Referenzen-Abschnitt
(Überschriften geprüft) — kein Wortlaut-Zwang; „Praxisbeispiele" (Nav)
passt zu Cases, nicht zu O-Tönen. Gewählt: „Das sagen unsere Kunden"
(neutral, kein Claim, beschreibt exakt die folgenden O-Töne).

**Geliefert:** `18-blende-das-sagen-unsere-kunden.mov` (3,5 s, Türen-Split
mit Punkt + Text, aus HBL-PraxisfallTransition via Props). Platzierungs-
Optionen: vor TA21 (Lücke 01:01:51,6–52,7, Start ~01:01:51,3 — Beginn des
großen Kunden-Blocks) oder vor TA14 (~01:01:21,8, direkt nach dem
Screen-Fenster). Master unverändert.

## 2026-08-03 (6) — Screen-Fenster: Chips unter den Rahmen

**Anlass:** David: Chips sollen nicht IM Bild stehen — unter das Fenster,
etwas größer; nur die Einzelanimation ändern.

**Gemacht:** Chips-Reihe aus dem Fensterbereich unter den Rahmen gesetzt
(top = Rahmenhöhe + 44 px, Breite 2760) und vergrößert (58 px, mehr
Padding). Safe-Zone geprüft: Unterkante y 2036 (Grenze 2052) ✓.
`14-screen-fenster-chips.mov` neu. Master-Datei weiterhin unangetastet
(Code trägt die Änderung — Hinweis aus Eintrag (5) gilt fort).

## 2026-08-03 (5) — Screen-Fenster auf Davids Recording-Format

**Anlass:** David: Fenster-Seitenverhältnis passt nicht zur
Bildschirmaufnahme (Factorial-Demo) — Referenzbild 1118×570 ≈ 1,96:1
(Loch war 16:9).

**Gemacht:** `ScreenFrameVisual` berechnet die Fensterhöhe jetzt aus
einer `fensterRatio`-Prop (Default 1,96; im Studio einstellbar für
künftige Formatwechsel). Loch per Alpha-Messung verifiziert:
2657×1353 = 1,964 ✓ (weicher Innen-Schatten täuschte bei der ersten
Messung kleineres Loch vor). `14-screen-fenster-chips.mov` neu gerendert.

**Hinweis:** Master-Datei auf Davids Wunsch NICHT neu gerendert — falls
er das Screen-Fenster aus dem Master (TC 01:01:07) nutzt statt der
Einzeldatei, hat der Master noch das alte 16:9-Loch; Code trägt bereits
das neue Ratio → ein Neu-Render genügt auf Zuruf.

## 2026-08-03 (4) — Split-Blende für A1→S3

**Anlass:** David: noch eine Fullscreen-Transition nach „Der Kunde war
begeistert." / vor „Umsetzung und laufende…" — Timing platziert er selbst
(nicht auf die 0,6-s-Lücke optimieren).

**Gemacht:** `HBL-SplitBlende` — schnelle Vollbild-Blende in der
Türen-Optik der Praxisfall-Transition, ohne Text: Türen zu (~0,5 s),
roter Punkt-Beat mittig, Türen auf (Punkt verschwindet vor halber
Öffnung). Default 1,8 s, Dauer über durationInSeconds skalierbar
(Öffnung hängt am Ende). Wiederverwendbar für jeden Schnitt.

**Geliefert:** `17-split-blende.mov` (1,8 s, 4K ProRes 4444 Alpha).
Empfohlene Lage: Mitte der Blende (~0,7 s) auf den Schnitt legen —
für A1→S3: Start ca. TC 01:00:46,0. Master unverändert.

**Nachtrag (gleiche Session):** David wollte den Satz „Der Kunde war
begeistert" IN der Blende + länger, um sie über den gesprochenen Satz zu
legen → ersetzt durch `17-blende-kunde-begeistert.mov` (3,5 s, gerendert
aus HBL-PraxisfallTransition via Props; Karte über dem Satz ab ca.
TC 01:00:44,3, Öffnung in S3). Die textlose Blende bleibt als Comp
`HBL-SplitBlende` im Studio verfügbar (Datei gelöscht).

## 2026-08-03 (3) — Säulen-Fokus-Varianten (Davids Idee)

**Anlass:** David: Säulen-Grafik soll in 2 Varianten enden — gleicher Anfang
(beide Säulen sichtbar), dann gleitet die jeweilige Säule (01 bzw. 02) in
die Mitte und wird größer, Rest blendet aus. Master-Datei NICHT ändern,
nur Einzelanimationen.

**Gemacht:** Neue Komponente `SaeulenFokusVisual` (eigenständig — Master
bleibt eingefroren): Phase 1 identisch zur Säulen-Grafik (~3 s, beide
sichtbar), dann Switch (0,8 s): Logo/Klartextzeile/Trenner/andere Säule
weichen aus, Fokus-Säule gleitet zentriert und skaliert ×1,5; Fokus-Hold,
Outro-Fade. Comps `HBL-Saeulen-Fokus01/02` (switchAtSec/Texte als Props).

**Geliefert:** `15-saeulen-fokus-01-lohnbuero.mov` +
`16-saeulen-fokus-02-hr-software.mov` (je 6,5 s, 4K ProRes 4444 Alpha) —
gedacht als große Blockwechsel-Karten für Säule 1 (vor S1) bzw. Säule 2
(Lücke S3→M2, ersetzt dort optional das kleine Titel-Badge). Master
unverändert (dort weiter Säulen-Grafik + Badges).

## 2026-08-03 (2) — Transition als Türen-Split, Rahmen-Haarlinie endgültig weg

**Anlass:** David: Kreis-Blende der Praxisfall-Transition gefällt nicht
(Öffnungs-Loch wirkte wie zweiter „Punkt" im Text) — „soll kein Kreis sein";
außerdem war die Haarlinie im Screen-Fenster trotz Overlap noch da.

**Gemacht:**
- Praxisfall-Transition umgebaut auf **Türen-Split**: Hälften schließen sich
  beim Einstieg aus links/rechts, Text+Punkt blenden aus, dann fahren beide
  Hälften auseinander und geben den A1-Take mittig frei (Timing unverändert,
  A1-Wort 1 bei halb geöffneten Türen). Kein Kreis mehr.
- Haarlinien-Ursache gefunden: CSS border+overflow/borderRadius erzeugt im
  Alpha eine Subpixel-Lücke an der Border-INNENKANTE (Overlap half nicht).
  Screen-Fenster-Rahmen neu aus 4 satt überlappenden Eierschale-Flächen
  ohne Beschnitt; 100-%-Crops (Ecke, Ober-/Unterkante) auf dunklem BG sauber.
- Render-Infrastruktur: ~29 GB verwaiste Remotion-Temp-Bundles gelöscht
  (Folge gestoppter Renders; Platte war voll → ENOSPC); Renders laufen jetzt
  über schlanken Spiegel `tools/motion/public-hbl/` (169 MB statt 6,5 GB
  public-Kopie pro Render — MAN-Videos liegen in public/). Beides in
  `WORKFLOW-Motion.md` dokumentiert.

**Geliefert (Formate geprüft):** `00-imagefilm-overlay-komplett.mov` NEU
(Türen-Split + dichter Rahmen) · `05-praxisfall-transition.mov` NEU ·
`14-screen-fenster-chips.mov` NEU.

## 2026-08-03 — Feinschliff: Logo scharf, Naht-Fix, Praxisfall-Transition

**Anlass:** David meldete (a) Haarlinie in der Screen-Fenster-Leiste,
(b) Logo überall „matschig", (c) Wunsch: „Ein Fall aus der Praxis" als
Fullscreen-Transition, die in den A1-Take übergeht.

**Fixes/Umbauten:**
- **Naht-Fix Screen-Fenster:** Browser-Leiste überlappt den Rahmen jetzt
  um 3 px — die Haarlinie (Video blitzte zwischen zwei Eierschale-Flächen
  durch) ist weg; auf dunklem BG-Composite verifiziert.
- **Logo-Fix:** Ursache Matsch = sips rastert PDFs erst in Punktgröße
  (214 px!) und skaliert dann hoch. Neu: PyMuPDF (ins transcribe-venv
  installiert) rastert das Vektor-PDF direkt bei 3400 px mit Alpha →
  `public/clients/hbl/logo-rot.png` + `logo-eierschale.png` ersetzt;
  100-%-Crop an der Endcard geprüft: scharf. (Alle CI-PNGs sind nur
  214 px — für Print/Video immer die Logo-PDFs rastern!)
- **Praxisfall-Transition** statt Caption: Vollbild-Eierschale-Karte mit
  Punkt-Motiv + „EIN FALL AUS DER PRAXIS" (N27), Kreis-IN in der
  S1→A1-Lücke (Master 21,3), Hold ~2,3 s, ab 23,9 Kreis-Blende von innen
  auf → A1-Take wird frei, Wort 1 „Freitagabend" bei 24,2. Technik:
  clip-path circle (In) + radial-gradient-Maske (Out) im Alpha-Kanal —
  Übergang passiert automatisch aufs Bild darunter. Neue Comp
  `HBL-PraxisfallTransition` ersetzt `HBL-CaptionPraxisfall` (Einzeldatei
  `05-praxisfall-transition.mov` ersetzt `05-caption-praxisfall.mov`).

**Geliefert (alle Formate geprüft):** `00-imagefilm-overlay-komplett.mov`
NEU (170 s, ~1,1 GB — Naht + Logo + Transition) · `01-wer-ist-hbl-saeulen.mov`
NEU · `05-praxisfall-transition.mov` NEU (3,4 s) · `10-endcard.mov` NEU ·
`14-screen-fenster-chips.mov` NEU. Stand: 15 Dateien (00–14) in
`Ergebnisse/Renders/`.

## 2026-08-02 (5) — Säule 2 konkreter: Chips + Subline + Screen-Fenster

**Anlass:** David: „HR-Software" wird nicht klar genug; Ideen A (Themen-Chips)
+ B (Titel-02-Subline) gewählt; er hat eine Bildschirmaufnahme der Software,
wusste aber nicht, wie/wo einbauen.

**Gemacht (alles O-Ton-belegt, kein Neuschnitt):**
- Titel-02-Badge mit Subline „Die passende Software finden, einführen &
  Prozesse digitalisieren" (aus M2 + Website-Claim; Dauer 3,6 s).
- Screen-Fenster-Overlay über M2 (Master 67,5–81,5 = TC 01:01:07–01:01:21):
  Eierschale-Rahmen mit Browser-Punkten und TRANSPARENTEM Fenster —
  Davids Bildschirmaufnahme kommt in DaVinci in die Spur DARUNTER
  (Vollbild reicht, Rahmen maskiert). Darauf 6 Themen-Chips, kumulativ:
  Bewerbermanagement · Onboarding · Zeiterfassung · Urlaub & Abwesenheiten ·
  Digitale Personalakte · Lohn-Schnittstelle (Belege: M1, M3, M8, TA20).
- Neue Comp `HBL-ScreenFenster` (auch einzeln nutzbar, 14 s).

**Geliefert:** `00-imagefilm-overlay-komplett.mov` NEU (170 s, ~1,1 GB) ·
`03-titel-02-hr-software.mov` NEU (3,6 s, mit Subline) ·
`14-screen-fenster-chips.mov` NEU (14 s). Formate geprüft (4444/Alpha).

**Offen:** David legt die Bildschirmaufnahme unter TC 01:01:07–01:01:21;
prüfen, dass dort UI-Inhalt gut sichtbar ist (Chips decken unteres Drittel).

## 2026-08-02 (4) — Master-Overlay (eine Datei), N27, Schwalm, Website-Check

**Anlass:** David: alles als EINE Datei mit Timings aus dem Cut02-SRT;
Website auf weitere Animations-Inhalte checken; N27 liegt jetzt in
`Material/CI/N27-Regular-&-Italic/`; André-Nachname selbst recherchieren.

**Gemacht:**
- **N27 eingebaut:** `N27-Regular.otf` → `tools/motion/public/fonts/hbl/`,
  @font-face „HBL N27"; alle großen Headlines (Säulen-Nummern/-Titel,
  Titel-Badges, −40 %-Zahl, Klartextzeile, Ohne-HBL-Pill, Endcard-Säulen)
  auf N27 Regular umgestellt (CI-Regel); Futura bleibt für Fließtext/
  Namen/Subs.
- **André = Andre Schwalm** (Head of Recruitment & Training, HiSERV GmbH,
  Schönefeld/Berlin) — via LinkedIn + RocketReach verifiziert, passt zu
  O-Ton („Personalgewinnung", Luftfahrt-GSE, seit 10/2022). Bauchbinde:
  „André Schwalm · HR & Digitalisierung · HiSERV". Bei Freigabe final
  bestätigen. Transkript enthält den Nachnamen NICHT (nur „Ich bin der
  Andre", TA1).
- **Website-Deep-Check:** /wir nennt die drei Geschäftsführenden
  Gesellschafterinnen **Melanie Lang, Susan Hanselmann, Anne Christine
  Berner** → drei HBL-Bauchbinden gerendert (Zuordnung Gesicht↔Name via
  David; „Susan Binder" aus der CI-Guideline existiert auf der Website
  nicht mehr). /leistungen: 3 Kacheln (Digitalisierung · Outsourcing ·
  Lohn und Gehalt), keine Zahlen → 2-Säulen-Logik der Kundenmail bleibt.
  Praxisbeispiel-Seite = exakt die A1-Story (Beleg!), keine neuen Zahlen.
  Keine weiteren Overlay-Inhalte nötig.
- **Master-Komposition `HBL-Imagefilm-Komplett`** (170 s = 2:50, Video-Zeit
  0:00 = TC 01:00:00): alle Elemente per Sequence auf Cut02-Timings —
  Säulen-Grafik 3,9–8,4 (überlappt S1-Anfang bewusst, Lücke nur 2,6 s) ·
  Titel 01 8,6 · mit-uns-Sub 17,5 · Praxisfall 24,2 · Titel 02 61,3 ·
  Binde Schwalm 84,0 (TA14) · Binde Breitenfeld 89,8 (TP5) · −40 % 104,8
  (M1) · Endcard ab 162 (ohne Out). „Ohne HBL:"-Pill bewusst NICHT im
  Master (TA21 liefert Kontext; liegt als Einzeldatei bei). Alle Timings/
  Texte als Props im Studio verschiebbar. Visuals refactored (Einzel-Comps
  + Master teilen dieselben Bausteine, outAtSec für Sequence-Outs).

**Geliefert (`Ergebnisse/Renders/`, 4K ProRes 4444 Alpha, 25 fps):**
`00-imagefilm-overlay-komplett.mov` (170 s, ~840 MB — bei TC 01:00:00
auflegen, fertig) + Einzeldateien 01–10 neu (N27/Schwalm; 08 heißt jetzt
`08-bauchbinde-andre-schwalm.mov`) + NEU 11/12/13 HBL-Team-Bauchbinden
(Lang/Hanselmann/Berner, je 5 s).

**Offen:** Schwalm-Schreibweise bei Freigabe bestätigen · HBL-Binden:
Zuordnung + Platzierung durch David (im Master nicht enthalten) ·
Ohr-Checks aus Eintrag (3) unverändert · Musik.

## 2026-08-02 (3) — Cut02-Gegencheck + Motion-Grafikpaket geliefert

**Anlass:** David: Cut02 fertig (Balance-Ergänzungen S2/M7+M8 bewusst NICHT
umgesetzt — „so wie's ist passt es"), Transkript liegt vor
(`Material/Cut02-HBL trans.srt`, Wort-Ebene, ~2:41); CI in `Material/CI/`
(guidline.pdf + Logos), Website https://www.hbl-management.com/.
Auftrag: Gegencheck + Animationen liefern.

**Gegencheck Cut02 (gegen Kundenmail + Umbau-Plan):**
- Umgesetzt: M2-Schlusssatz drin · TA14 nach M2-Schluss/vor TP5 · TA21 vor
  TP6 · „hättest?"-Fragment raus · A1-Halbsatz „vollständig digitalisiert"
  raus. Alle „sehr gut"-Takes + beide Kunden-Wortzitate vollständig; kein
  unerwünschtes Material. Reihenfolge = Plan.
- Bewusst nicht drin (kundenkonform, nur „gut"-Optionen): S2, M7/M8;
  TP5 komplett inkl. Guidance (statt Kürzung) — ok.
- Sprechpausen 2,7 s (nach Hook) / 3,1 s (nach S1) / 3,2 s (S3→M2) =
  Platz für Grafiken.
- Offene Kleinigkeiten (Ohr): TP2-„was" klingt weiter an (0:04) ·
  TA21-Einstieg „Also wenn wir" im SRT nicht erfasst — prüfen, ob hörbar ·
  TA21 „gegeben" nach „Speed" (0,8-s-Lücke) · M2 „Personal-Softwareanbieter"
  · TA23 „dazu".

**Motion (tools/motion, eigenes Git — nicht committet):**
- Neuer Client `src/clients/hbl/` mit brand.json aus guidline.pdf:
  Kirschrot #FF1438 · Eierschalenweiß #FCF8EC · Dunkelgrau #908385;
  Radius 28. Logo aus Vektor-PDF hochauflösend freigestellt (PIL, echter
  Alpha-Kanal) → `public/clients/hbl/logo-rot.png` + `logo-eierschale.png`.
- Fonts: CI nennt N27 (Headlines) + Futura — N27 liegt nicht vor; Futura
  Medium/Bold aus macOS-TTC nach `public/fonts/hbl/` extrahiert und per
  @font-face eingebunden (System-Futura-Bold lieferte defektes „é" →
  „Andrй"-Bug, behoben).
- 10 Kompositionen `src/clients/hbl/projects/imagefilm/Composition.tsx`
  (+ Root-Registrierung, Ordner „HBL"), alle 3840×2160/25fps, Texte als
  Props editierbar. Review nach Motion-CLAUDE.md: Safe-/Face-Zone-Stills
  geprüft, Guides in Defaults aus.

**Geliefert (`Ergebnisse/Renders/`, ProRes 4444 Alpha):** 01 Säulen-Grafik
„Wer ist HBL" (6 s) · 02/03 Titel 01/02 (je 3 s) · 04 „−40 %"-Karte (7 s) ·
05 „Ein Fall aus der Praxis:" (3 s) · 06 „mit uns"-Sub (3,5 s) ·
07 „Ohne HBL:"-Pill (6 s, optional) · 08/09 Bauchbinden André/Breitenfeld
(je 5 s) · 10 Endcard Logo+Säulen+URL (8 s, kein Job-CTA).

**Wording-Belege (David-Regel „nur Website-Infos"):** 40 %-Claim wörtlich
auf Website („40 % Zeit und Kosten zu sparen"); Duzen = Website-Ton;
Säulen-Titel aus Kundenmail („externes Lohnbüro" / Software+HR-Prozesse);
Klartextzeile „Dein Partner für Lohnabrechnung & HR-Digitalisierung" =
Kombination Mail+Website-Claim → bei Freigabe absegnen. Endcard nur URL
(www.hbl-management.com), keine unbelegten Kontaktdaten.

**Offen:** André-Nachname für Bauchbinde (Props editierbar) · N27
nachrüsten, falls Kunde Font liefert · TP2-„was" + Ohr-Checks (oben) ·
Humanus-Perspektive · Musik/Sound.

## 2026-08-02 (2) — Umbau-Plan Cut02 → Cut03: HBL-Balance

**Anlass:** David: Cut wirkt zu testimonial-lastig; Auftrag: wichtige
A/M/S-Takes prüfen (nur Meinung), dann Freigabe für meine Empfehlung;
Marker resetten — Basis ist jetzt Cut02, nur Neues markieren.

**Analyse (an David berichtet):** Redezeit war HBL-dominiert (~90 s vs.
~62 s Kunden), aber Struktur kundenlastig: Kunde eröffnet, nach dem
40-%-Satz bis zum CTA ~35 s nur Kundenstimmen, Säule 2 nur ~26 s HBL-Stimme.
Take-Bewertung: M7+M8 wichtig (Paar, „dafür"-Bezug), S2 wichtig
(Problem-Setup Säule 2, löst Kundenauflage via Titel + Caption), M3 nur
B-Prio („halbiert" vs. 40 %, E-Mail-Zeile), M5 = Ad-CTA (kannibalisiert A5),
M6 = Grafik-Ersatz, M4/A2–A4 unbewertet = Reserve.

**Gemacht (Plan rev. 6, PDF neu):** Basis = Cut02, alle alten Marker
entfernt. Nur noch 4 markierte Zeilen: [NEU] S2 (Zeile 8, nach Titel 02,
TL 4:55–5:12) · [NEU] M7+M8 (Zeile 16, nach TP6, TL 4:19–4:36) ·
[FIX] TP5 auf Satz 1 (−8 s, Guidance TL 15:56–16:04 raus) · [FIX]
A1-Halbsatz raus (−4 s, falls nicht schon in Cut02 geschehen).
TC-Spalte entfernt (Positionen relativ zu Nachbar-Takes — kein Cut02-SRT
vorhanden). Ziel ca. 2:55 + Endcard; HBL ~2/3 Redezeit, nie mehr als
2 Kunden-Takes in Folge. PDF 4 Seiten, Markierungen visuell geprüft;
Grundlagen + Dossier (Rev.-6-Block) nachgezogen.

**Offen:** S2-Kontext-Caption texten und bei Kundenfreigabe aktiv zeigen;
nach Umbau „Cut03-HBL trans"-SRT für Gegencheck.

## 2026-08-02 — Revision Umbau-Plan: TA14 in den Säule-2-Block

**Anlass:** David: TA24 → TA14 → TA23 wären 3 André-Takes in Folge — „finde
ich nicht gut". Außerdem Missverständnis geklärt: TA21 kommt komplett NEU
REIN (raus nur das „hättest?"-Fragment); „[…]" in Zitaten = nur PDF-Kürzung.

**Gemacht:**
- TA14 (Satz 1) von Position „vor TA23" in den Säule-2-Block verschoben:
  neu Zeile 10, nach M2-Schlusssatz / vor TP5 („+ vor 01:01:15"). Sprecher
  wechseln jetzt durch (…M2 HBL → TA14 André → TP5 Breitenfeld → M1 HBL →
  TA21 André → TP6 Breitenfeld → TA24+TA23 André wie in Cut01 → A5).
  Bauchbinden-Erstnennung André damit bei Zeile 10.
- Zeilen renummeriert (Fragment=13, TA21=14, TP6=15, TA24=16, TA23=17),
  alle Querverweise angepasst; Legende ergänzt: „[…] im Zitat = nur
  PDF-Kürzung, KEIN Schnitt". Dossier-Delta + pdf_meta (Stand 02.08.)
  nachgezogen. PDF neu: 4 Seiten, Markierungen visuell geprüft.

**Entscheidung (David-Regel, notiert):** Nie 3 Takes derselben
Interview-Person direkt hintereinander; 2 in Folge ok.

## 2026-07-31 (2) — Umbau-Plan Cut01 → Cut02 (PDF mit Farb-Markierungen)

**Anlass:** David baut Cut01 nach dem Review um; Wunsch: Schnittplan-PDF
aktualisieren, neue Clips und Änderungen farblich + textlich markieren.

**Gemacht:**
- `video-1-imagefilm.md` komplett neu als UMBAU-PLAN: 19 Zeilen in
  Cut01-Reihenfolge mit neuer Spalte „Cut01 von" (DaVinci-TC in Davids
  Schnitt, Start 01:00:00, Stand vor Einfügungen). Markierungssystem:
  [NEU] grün = neu einbauen (Zeile 2 Säulen-Grafik, 9 M2-Schlusssatz,
  13 TA21, 16 TA14) · [FIX] orange = ändern (1 TP2-Out „was", 5 A1-Halbsatz
  empfohlen raus + Praxis-Caption, 12 „hättest?"-Fragment raus) · [CHECK]
  blau = nur prüfen (Titel 01/02, Captions, Bauchbinde, 40-%-Grafik,
  Endcard, Ohr-Checks) · unmarkiert = bleibt exakt wie Cut01.
- Renderer `tools/transcribe/scripts/render_schnittplan_pdf.py` generisch
  erweitert: Tabellenzeilen mit „[NEU]/[FIX]/[CHECK]" in einer Zelle werden
  grün/orange/blau hinterlegt (FontFace fill, Priorität NEU>FIX>CHECK);
  clean() um −, ≈, ≤, ≥ ergänzt (waren „?" im PDF). Abwärtskompatibel.
- `pdf_meta.json` (Untertitel/Stand/Warnbox inkl. Marker-Legende),
  `01-projekt-grundlagen.md` (Video-Zeile, Kundenmarken inkl. A1-Lösung
  und M2-Schlusssatz, offene Punkte) und Dossier (rev. 5 Delta-Block,
  Kompaktfassung führt) nachgezogen.

**Geliefert:** `Ergebnisse/O-Ton-Pläne/HBL-Imagefilm-Schnittplan.pdf` —
4 Seiten (Deckblatt + Übersicht + 2 Seiten Video, Budget ok, keine
Encoding-Artefakte), Farb-Markierungen visuell verifiziert.

**Entscheidungen:**
- A1-„andere Einleitung" interpretiert als Caption „Ein Fall aus der
  Praxis:" + Position nach S1; „Freitagabend"-Satz bleibt (wie Cut01) —
  bei Kundenfreigabe explizit benennen.
- TA21 vor TP6 gesetzt: ersetzt „hättest?"-Fragment und liefert den
  „Ohne HBL"-Kontext, dadurch „Ohne HBL:"-Caption nur noch optional.
- Ziel-Länge ca. 2:36–2:45 + Endcard (Davids Länger-ok vom 31.07.).

**Offenes:** David baut um; danach Bild-Ebene-Checks (Zeilen 2/3/7/11/19,
Captions 4/5/14, Bauchbinden) + Ohr-Checks (8/15/17) abhaken;
Humanus-Perspektive; ggf. Cut02-SRT erneut gegenprüfen.

## 2026-07-31 — Review Cut01 gegen Kundenmail

**Anlass:** David hat Cut01 geschnitten (~2:14 O-Ton, DaVinci-TC ab 01:00:00);
Transkript `Material/Cut01-HBL trans.srt`. Auftrag: ausführlicher Abgleich mit
dem Kundenfeedback (Mail Juli 2026). Video darf länger werden.

**Ergebnis:**
- Cut enthält AUSSCHLIESSLICH kundengelistete Takes (Reihenfolge): TP2 (Hook),
  S1 komplett inkl. Wunsch-Satz „Deine Abrechnung läuft fehlerfrei und
  pünktlich" (ohne „mit uns" — O-Ton gibt es nicht her), A1 (ohne „mitten im
  Digitalisierungsprojekt", MIT „…vollständig digitalisiert"), S3 ab
  „Umsetzung…" (In 0:08 statt Kundenmarke 0:10 = Satzanfang), M2-Kernsatz
  „Als zertifizierter Implementierungspartner…", TP5 (intern gekürzt, „äh"
  raus), M1-Schlusssatz (40 %-Claim ✓ als O-Ton), TP6, TA24-Kernsätze (ohne
  „Mädels", Ähms raus), TA23 bis „Automatisierung" (Kunden-Zitat voll drin,
  Ähms raus), A5 als CTA. Kein unbewertetes/gesperrtes Material (kein TA18,
  kein Factorial), keine Regie-Töne.
- **FEHLT (Muss-Empfehlung):** M2-Schlusssatz „Unabhängig liefern wir…"
  (TL 2:52–2:59 — vom Kunden wörtlich mitzitiert!); TA14 und TA21 (beide
  „sehr gut" — einzige zwei Sehr-gut-Takes, die nicht im Cut sind).
- Schnittfehler-Verdacht: nacktes „hättest?" (Interviewer-Rest, 0,6 s) bei
  Video 1:37 vor TP6; TP2-Out „…Durcheinander, was" („was" klingt noch an);
  SRT-Start 00:59:59,84 (erster Ton vor der 01:00:00-Marke — Anschnitt?).
- Nicht aus SRT prüfbar (Bild-Ebene, KRITISCH): Säulen-Grafik/Klartextzeile
  „Wer ist HBL" — im Ton-Timing existiert KEINE stumme Grafikfläche
  (TP2→S1 nur 0,4 s Lücke; größte Lücke 2,4 s M2→TP5); Titel 01/02,
  Caption „Ohne HBL:" (TP6), Einleitungs-Caption A1, „mit uns"-Caption (S1),
  Bauchbinden, Humanus-Kameraperspektive (TP2/TP5/TP6).
- Hinweise: „Das Ergebnis … fehlerfrei/pünktlich" fällt 2× (S1-Ende + S3 —
  beides kundenkonform); A1-Digitalisierungs-Klausel mischt Säule 2 in den
  Säule-1-Block (Kunde verbietet es nicht, Plan rev. 4 hatte sie raus).

**Empfehlung (Ziel ~2:40):** M2-Schlusssatz ergänzen (+8 s); TA21
(TL 12:37–12:52, Ähm-Schnitte lt. Liste) direkt VOR TP6 — ersetzt das
„hättest?"-Fragment und liefert den „Ohne HBL"-Kontext natürlich; TA14
Satz 1 (TL 9:38–9:44) vor TA23. Optional: S2 nur mit Kontext-Caption,
TA9 (einzige Kundenstimme Säule 1), TA4 erst nach Factorial-Freigabe.

**Offen:** Grafik-Ebene bestätigen/nachrüsten; Ohr-Checks (Ähm-Reste, TA23
„dazu"/„eine", TA24-Satzanschlüsse, M2 „Als …Personal-Softwareanbieter"
vollständig?); Humanus-Perspektive; S3-In 0:08 bei Kundenfreigabe erwähnen.

## 2026-07-23 (5) — Review vor Schnittstart (3-fach geprüft)

**Anlass:** David startet den Schnitt; Auftrag: prüfen, ob alles passt, Story
rund, Kundenwünsche getroffen.

**Prüfung:** (a) Mechanik-Skript: alle Kern-Zitate wörtlich in den richtigen
Szenen, TL-Arithmetik, Ähm-Zählungen, Kern-Länge, 25/25 Kundenszenen
abgedeckt — ALLES BESTANDEN. (b) Unabhängiger Compliance-Review (Agent):
kein Blocker, 1 wichtiger + 4 kleine Befunde. (c) Unabhängiger
Dramaturgie-Review (Agent): Story trägt, kein Blocker, 5 wichtige + 5 kleine
Befunde.

**Eingearbeitete Fixes (Plan rev. 4):**
- Beat 5 (A1) NEU: Wendepunkt „Wir haben direkt in der Folgewoche übernommen"
  bleibt hörbar (0:02–0:12 + 0:18–0:24 + 0:27–0:29); Säule-2-Klausel
  „…vollständig digitalisiert" fällt raus. Kern jetzt ~2:19.
- Kürzungspfad ERSETZT: statt Beat 9 (kippte Säulen-Balance) jetzt Kürzung
  aus Redundanz (S3-Ergebnis-Satz −5, Beat 12 −6, Hook −3, Wendepunkt-Caption
  −3 = 2:02). S3-Satz-Streichung weicht vom Kundenzitat ab → bei Freigabe nennen.
- Beat 2: Klartextzeile unterm Logo ist PFLICHT (einzige „Wer ist
  HBL"-Antwort); Hook ohne Humanus-Insert, Bauchbinde erst Beat 9.
- TP6-Caption „Ohne HBL:" ~0,5 s vor Toneinsatz; TA24-Out ~13:42, S1-Out
  ~4:53 (Wortenden); TA24-„Mädels" 13:29–13:32 vereinheitlicht; TP5-Guidance
  15:56–16:04 korrigiert; TP3 als Kunden-Textmarke (TC abgeleitet) relabelt;
  M3-Brücken-Caveat (E-Mail-Zeile nicht als Lohnbüro-Kritik).
- Neu in Offen: S3-In 5:21 vs. Kundenmarke 5:23 absegnen; bewusste
  Evidenz-Asymmetrie (Säule 1 ohne Kunden-Testimonial — A1-Story ist der
  Beweis; ggf. Nachdreh-Empfehlung Lohnbüro-Testimonial).
- PDF neu: 4 Seiten (Budget ok), keine Artefakte.
