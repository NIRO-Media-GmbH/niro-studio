# Protokoll — Setzer / Social-Reels / 2026-08 Dreh 18.08

## 2026-08-24 — Schnittplan Video 1 (Fleischkäse vs. Leberkäse)

**Auftrag:** Schnittplan für das Setzer-Material auf `NIRO-SSD-03`, Ordner
`03_Dreh 2026.08.18`. Zunächst **nur Video 1**. Kein Konzept vorhanden — der
Plan ist komplett aus dem Material rekonstruiert.

**Gemacht**
- Neues Projekt angelegt: `projects/Setzer/Social-Reels/2026-08 Dreh 18.08/`.
- Material gesichtet: `Rohmaterial iPhone` mit sieben Themen-Ordnern (01–07),
  `00 Discarded`, Proxys, zwei BTS-Fotos.
- **38 Clips transkribiert** (ElevenLabs Scribe): alle 20 aus Ordner 01, die
  12 thematisch passenden aus `00 Discarded` (Nummernkreis 4874–4899) sowie
  die freistehenden Hook-/B-Roll-Clips. Runner: `_intern/transcribe_setzer.py`,
  Index `_intern/transcripts_index.json`, Utterances `_intern/utterances.json`.
- Bildinhalt jedes Clips über extrahierte Frames geprüft (`_intern/frames/`) —
  ohne Konzept ist das die einzige Quelle für Ort, Requisite und Bildwirkung.
- Technik aus den Metadaten geklärt: **zwei iPhones** (14 Pro = 23,976 fps,
  15 Pro = 25 fps), 9:16, Ton durchgehend leise, ein 4K-Clip.
- Sprecher identifiziert: **Nico Setzer** (Kittel-Stick + Website-Abgleich).
- Website `landmetzgerei.de` vollständig gegengeprüft (355 Seiten) für
  belegtes Wording.
- Faktencheck der zentralen Aussage gegen die Leitsätze für Fleisch und
  Fleischerzeugnisse (Nr. 2.4.2.2.2) + § 15 LFGB.
- Pläne gebaut, verifiziert (`_intern/verify_plan.py` — Zitate, Timecodes,
  Clip-Grenzen, Sprecher-Reinheit, keine Discarded-Quellen) und als PDF
  gerendert: **4 Seiten** (Deckblatt + 1 Übersicht + 2 Video).

**Geliefert**
- `Ergebnisse/O-Ton-Pläne/Setzer-Schnittanweisungen-Video-1.pdf`
- `Ergebnisse/O-Ton-Pläne/01-projekt-grundlagen.md`
- `Ergebnisse/O-Ton-Pläne/video-1-fleischkaese-vs-leberkaese.md`
- `Ergebnisse/O-Ton-Pläne/00-materialanalyse-video-1.md` (intern)
- `Ergebnisse/O-Ton-Pläne/Dossier/video-1-fleischkaese-vs-leberkaese-lang.md`

**Entscheidungen**
- Schnittfassung ≈ 32 s: 6929 (Hook, Cam B) → 4883 → 4884 → 4888 → 4900 → 4903.
- Bewusst der kurze Twist-Take 4888 statt 4889–4892: die langen sagen „Sobald
  man Bayern verlässt", das doppelt den Einstieg von 4900.
- 4900 statt 4898 als Erklär-Take: 4898 hängt bei 4,78–5,48 durch.
- `00 Discarded` bleibt gesperrt — Sortierung wurde gegengeprüft und stimmt
  (u. a. 4895 sachlich falsch, 4899 beruft sich auf ein nicht existierendes
  „deutsches Fleischergesetz").

**Offen**
1. **Ton-Kamera bestätigen** — welches iPhone trägt den DJI-Empfänger?
2. **Faktenlage Beat 5a**: „muss außerhalb von Bayern Leber drin sein" ist
   verkürzt (Leitsätze sind nicht bindend; leberfreier Leberkäs darf außerhalb
   Bayerns als „Bayerischer Leberkäs(e)" verkauft werden). So lassen oder
   nachdrehen? Nachdreh-Satz liegt im Plan.
3. Wording: Nico sagt „24/7 Märkte", die Website sagt „24/7 Shops" — O-Ton
   bleibt, NIRO-Text folgt der Website.
4. Preis 2,05 € auf der SB-Schale lesbar — kaschieren?
5. ~~Setzer-CI fehlt~~ — am 24.08. von der Website gezogen, siehe unten.
6. Drehdatum: Metadaten sagen 19.08.2026, der Ordner sagt 18.08.
7. Videos 2–7 warten auf Freigabe von Video 1.

## 2026-08-24 (2) — Untertitel + Animationen Video 1

**Auftrag:** Animation + Untertitel in Setzer-CI, viele abwechslungsreiche
Animationen, dazu eine SVG-Zeichnung des Fleischkäs. 9:16, 24 fps.
Grundlage: der von David gelieferte SRT-Export des fertigen Schnitts.

**CI ermittelt** (Elementor-Kit `post-6.css` auf landmetzgerei.de, echte Werte,
nicht geschätzt): Primary/Logo-Rot **#E30613**, Accent **#B9000B**, Secondary
**#0D0802**, hell **#FFFAFA**, Fließtext **#7A7A7A**. Headlines **Arial 900,
Versalien**, Button-Radius **3 px**. Die Website lädt **keinen Webfont** —
gerendert wird mit dem System-Arial-Black.
Angelegt als `tools/motion/src/clients/setzer/brand.json`.

**Logo rekonstruiert:** `~/Downloads/Setzer.png` (2701×1038) enthält nur die
weiße Kontur, die Buchstabenflächen sind transparent. Über Rot gelegt und den
Außenbereich per Floodfill freigestellt → vollfarbiges Logo mit Alpha unter
`tools/motion/public/clients/setzer/setzer-logo.png`. Die Website-Dateien sind
mit 290×135 px für Video zu klein; ein echter Vektor fehlt weiterhin.

**Zehn Beats, bewusst je eine andere Bewegungsart:** VS-Chips · Metzger-Stempel
· Grenzwisch · Linienzug · Type-Reveal · 100→0-Zähler · Herkunfts-Badge ·
24/7-Kasten mit laufendem Zeiger · gezeichneter Laib mit Anschnitt · Poll mit
Sprechblase.

**SRT korrigiert** (Whisper hatte viel verhört): Lebercase/Levo Case →
Leberkäs, Fleischcase → Fleischkäs, „einen Bahnverlässt" → „Bayern verlässt",
„sieht Sarah" → „sieht die Sache", Fleischerleitsetzen → Fleischerleitsätzen.

**Zwei Projektregeln im Code umgesetzt:**
- „24 Sieben Märkten" steht **nicht** im Untertitel — der Kasten trägt
  „24/7 SHOPS" (Website-Schreibweise).
- Keine Dopplung Animation/Untertitel: Produktnamen im Hook, das Prädikat
  „keine Leber drin", der Satz über dem Zähler, das Schlusswort „Fleischkäse"
  und die CTA-Antworten stehen nur in der Grafik, jeweils als ganze
  Sinneinheit. Beim Herkunfts-Badge deshalb nur „HOHENLOHE" statt „REGION
  HOHENLOHE" — „Region" steht schon im Untertitel.

**Review-Durchlauf** brachte echte Fehler, alle behoben: Poll-Chips waren
seitlich abgeschnitten (jetzt gestapelt), eine Untertitelzeile lief über die
volle Breite (Seiten auf max. 2 Zeilen aufgeteilt), halb aufgebaute Zeilen
standen grau und linksversetzt im Bild (Zeilen erscheinen jetzt als Ganzes),
Chips und 24/7-Kasten ragten in die Gesichtszone, Hero-Fläche und
Kommentar-Blase über die Safe Zone. Der Laib war in Fassung 1 als Brot
lesbar — neu gezeichnet: kastenförmig statt rund, parallele Einschnitte statt
Zickzack, dunkle Fläche dahinter gegen die Tarnfarbe im braunen Footage.
Ränder aller Beats nachgemessen: alles unter 45 % (Gesicht), über 86 %
(IG-UI) und innerhalb der seitlichen 5 %.

**Geliefert**
`Ergebnisse/Renders/Setzer-V1-Fleischkaese-vs-Leberkaese_Overlay_1080x1920_24p_Alpha.mov`
— ProRes 4444 mit Alpha, 1080×1920, 24 fps, 32,21 s, 214 MB.
Komposition: `tools/motion/src/clients/setzer/projects/fleischkaese-vs-leberkaese/`.

**Offen aus dieser Runde**
1. **Exakte Laufzeit des Schnitts** — die Timeline endet 32,21 s nach dem
   letzten Wort. Weicht der Schnitt ab, `durationInSeconds` und ggf.
   `timeOffsetSec` in Remotion nachziehen.
2. **Kein Abgleich gegen das echte Bild möglich** — der fertige Schnitt liegt
   nicht als Datei vor. Positionen sind gegen Roh-Frames geprüft, nicht gegen
   den Cut. Bitte einmal drüberlegen und Gesichtsfreiheit bestätigen.
3. **Vektor-Logo vom Kunden anfordern** (Website-Raster ist zu klein).
4. Render braucht das System-Arial-Black (macOS). Auf einem anderen Rechner
   vorher prüfen oder eine Font-Datei mitliefern.

## 2026-08-25 — Feedback-Runde V1 → Overlay V2

**Grundlage:** Dropbox-Replay-Kommentare von Michael Manheim (25.08., 6 Punkte)
zur V1 des Overlays.

**Umgesetzt**
1. **Farbkonzept „rot–schwarz" statt „rot–weiß"** (Kommentar 1): alle hellen
   Flächen auf schwarzen Grund gedreht — VS-Chips (schwarz mit roter Kante /
   rot), Stempel (schwarz, rote Doppelrahmen, weiße Type), Hohenlohe-Badge,
   Poll-Chips, Kommentar-Blase; VS-Plakette mit rotem statt weißem Ring.
2. **Zähler-Überlappung** (Kommentar 2): bei zweistelligen %-Werten kollidierte
   die Zahl mit dem Ring. Kreis von 20 % auf 21,5 % Höhe vergrößert, Ziffern
   von 0,082 auf 0,058 verkleinert, tabular-nums. Nachgemessen bei „51 %":
   26 px Mindestabstand Ziffern↔Rot. Restyle: schwarzer Kreis, roter Ring.
3. **Hohenlohe-Klärung** (Kommentar 3): Badge bleibt drin, ist aber per Prop
   `showHohenlohe` abschaltbar, bis Volker „Hohenlohe" freigibt.
4. **24/7-Shop-Logo** (Kommentar 4): offizielles SVG vom Dropbox-Link geladen
   (`public/clients/setzer/shop-logo.svg`, weiß/rot auf 214×100-ViewBox),
   ersetzt Text + Uhr-Icon; sitzt auf schwarzem Kasten mit roter Unterkante.
5. **Fleischkäs-Grafik im Iconset-Stil** (Kommentar 5): AI-Etikett
   („Backofen Fleischkäse") als Referenz gerendert — Stil ist schwarzer
   Grund, weiße Line-Icons, rote Highlights. Zeichnung umgebaut: weiße
   Konturen auf sattem schwarzem Panel, Schnittflächen der Scheibe jetzt
   **rot** als Highlight (statt rosa), Messer als weiße Line-Art mit roten
   Nieten. Geometrie (Kastenform, parallele Einschnitte) beibehalten.
6. **Setzer-Logo nur einfarbig** (Kommentar 6): aus dem Konturen-PNG zwei
   strikt einfarbige Fassungen gebaut (`setzer-logo-rot.png` #E30613,
   `setzer-logo-weiss.png`); im Hero läuft Rot auf Schwarz (Favicon-Look).
   Die rot-weiße Kontur-Fassung ist **gelöscht**, damit sie nie wieder
   versehentlich verwendet wird.

**Geliefert**
`Ergebnisse/Renders/Setzer-V1-Fleischkaese-vs-Leberkaese_Overlay_V2_1080x1920_24p_Alpha.mov`
(ProRes 4444 Alpha, 1080×1920, 24 fps, 32,21 s). Safe Zones nach dem Umbau
erneut vermessen — alle Beats innerhalb (Gesicht < 45 %, IG-UI > 86 %,
seitlich 5 %).

**Offen**
- Volker: darf „Hohenlohe" stehen? Sonst `showHohenlohe: false` rendern.
- Die AI-Datei enthält weitere Icons (Ofen, Dampf-Teller, Timer) — bei den
  nächsten Videos direkt in diesem Stil bauen.

## 2026-08-25 (2) — Kundenmaterial eingebaut → Overlay V3

David hat `projects/Setzer/Kundenmaterial/` bereitgestellt
(`01_Stammdaten` Logos + `Niro` Vorlagen/Fonts).

**Gesichtet**
- `01_Stammdaten`: `Logo ohne hg.png` (2702×1039, einfarbig rot #DC0C17),
  `logo schwarz.png` (einfarbig schwarz), `Setzer_Logo.png` (1080×430,
  **schwarze Buchstaben mit roter Kontur** — per Randabstands-Messung
  bestimmt; auf dunklem Grund unbrauchbar, da die Buchstaben verschwinden),
  `cropped…SCHWARZ_ROT (2).png` (klein), `setzer Kopie.png` (Mini),
  `vip-logo.png` (weiß, eigenes Zeichen).
- `Niro`: 6× „Have Heart Font.TTF" — **alle byte-identisch** (intern
  „DobiType", 62 Glyphen). **Keine Umlaute, keine Ziffern, kein „/"** —
  das ist die Marker-Script vom Etikett/Claim.

**Umgesetzt (V3)**
- Meine rekonstruierten Logo-PNGs durch die **Kunden-Originale** ersetzt:
  `setzer-logo-rot.png` = „Logo ohne hg.png", dazu `-schwarz`,
  `-rot-schwarz` und abgeleitetes `-weiss` in
  `tools/motion/public/clients/setzer/`.
- **Have Heart** als `fonts/HaveHeart.ttf` registriert. „Fleischkäse" im
  Auflösungs-Beat jetzt im **Etikett-Look**: schwarzes Panel, weiße
  Marker-Script, rote Kante — das „ä" kann die Font nicht, die Punkte sind
  als `FakeAe`-Komponente handgesetzt.
- Im Hero unter dem Logo der Claim **„damits RICHTIG schmeckt!"** in der
  Script (RICHTIG rot), wie auf dem Etikett. Panel dafür verdichtet und
  neu vermessen (46,0–85,7 % — innerhalb aller Zonen).

**Geliefert**
`Ergebnisse/Renders/Setzer-V1-Fleischkaese-vs-Leberkaese_Overlay_V3_1080x1920_24p_Alpha.mov`

**Notiz für alle weiteren Setzer-Videos:** Have Heart nur für Wörter ohne
Umlaute/Ziffern direkt nutzen; Umlaute via FakeAe, Zahlen (z. B. „24/7")
gehören in Arial Black oder ins Shop-Logo-SVG.

## 2026-08-25 (3) — Bayern-Flagge → Overlay V4

Davids Wunsch: Bayern-Flagge beim Twist („sobald man Bayern verlässt…").
Umgesetzt im Grenz-Beat (7,2–9,5 s): weiß-blaue Rautenflagge am Mast mit
rotem Knopf, steht am **linken Ende der Grenzlinie** — der rote Pfeil zieht
von ihr weg über die Grenze (= Bayern verlassen). Entrollt sich exakt auf
dem gesprochenen „Bayern" (7,32 s), leichtes Wehen, dünne schwarze Kontur
für hellen Hintergrund. Das Weiß-Blau ist eine bewusste Ausnahme vom
rot–schwarz-Konzept: die Landesfarben sind hier die Aussage.
Zonen nachgemessen (46,2 % top) — alles im Rahmen.

**Geliefert:** `…_Overlay_V4_1080x1920_24p_Alpha.mov`

## 2026-08-25 (4) — Fleischkäs-Zeichnung raus → Overlay V5

Davids Entscheidung: die gezeichnete Fleischkäs-Grafik fliegt komplett raus,
im Hero-Beat (25,1–28,95 s) bleibt **nur das Setzer-Panel**: schwarzes Panel
mit roter Oberkante, Setzer-Logo (einfarbig rot, Kunden-Original, jetzt
größer auf 46 % Bildbreite) und der Claim „damits RICHTIG schmeckt!" in der
Have-Heart-Script. Panel neu choreografiert (aufklappen → Logo landet →
Claim blendet nach) und auf 62 % Bildhöhe zentriert; Zonen gemessen
(52,2–74,1 %). `Fleischkaes.tsx` bleibt im Repo (unbenutzt), falls die
Zeichnung mal wieder gebraucht wird — der Etikett-Look des
„Fleischkäse"-Schriftzugs in Beat 5 ist NICHT betroffen und bleibt drin.

**Geliefert:** `…_Overlay_V5_1080x1920_24p_Alpha.mov`

## 2026-08-28 — Feedback V2 (Font + Claim-Vektor) → Overlay V6

Dropbox-Replay-Kommentare von Michael (26.08., 2 Punkte):

1. **Richtige Font ist „Have Heart One"** (Set Sail Studios, per Dropbox
   geliefert): Die „Have Heart Font.TTF" aus dem Kundenmaterial war ein
   Fake — intern „DobiType", nur 62 Glyphen. Die echte Font hat den vollen
   Zeichensatz **inklusive Umlauten und Ziffern** → der FakeAe-Punkte-Hack
   ist raus, „Fleischkäse" steht jetzt echt im Auflösungs-Beat.
   Installiert als `fonts/HaveHeartOne.ttf`; die DobiType-Datei ist aus dem
   Motion-Client gelöscht, das Original liegt weiter im Kundenmaterial.
2. **Claim als offizieller Vektor**: `Setzer_CLAIM_WEISS.ai` (Dropbox) →
   mit pdftocairo transparent gerastert (2481×717, komplett weiß),
   getrimmt als `claim-weiss.png` ins Motion-Public. Ersetzt den selbst
   gesetzten Claim im Hero (meine Fassung hatte laut Michael die falsche
   Font und „RICHTIG" fälschlich in Rot).

Beide Dateien zusätzlich ins Kundenmaterial gesichert
(`01_Stammdaten/Setzer_CLAIM_WEISS.ai`, `Niro/Have-Heart-One.ttf`).
Zonen nach dem Umbau gemessen — beide Panels im Rahmen.

**Geliefert:** `…_Overlay_V6_1080x1920_24p_Alpha.mov` — aktueller Stand.

## 2026-08-28 (2) — Video 6 „Pfefferbeisser": Untertitel + Animationen

David hat den Wort-SRT des fertigen Schnitts geliefert
(`Subtitle 1 Video 6 Pfefferbeiser.srt` im Chargen-Ordner, 66,4 s).
Neue Komposition `Setzer-Pfefferbeisser`
(`tools/motion/src/clients/setzer/projects/pfefferbeisser/`) im
Design-System aus Video 1 (rot–schwarz, Iconset-Stil, Kunden-Assets).

**Sieben Beats:** Intro-Kaskade SCHULTER/SCHLEGEL/PFEFFERBEISSER (Chips,
wie gesprochen) · Waagen-Icon mit einpendelndem roten Zeiger (Gewürze) ·
rotierender Vermengen-Rotor · Räucher-Icon (Scheite + flackernde Flamme +
Rauch-Loop) · **TROCKNEN ⇄ RAUCHEN**-Wechsel, aktiver Chip springt auf den
gesprochenen Wortzeiten (56,57/57,33/57,90/58,63 s) · 24/7-Shop-Logo-Kasten
· Marken-Outro (Logo + Claim). Icons alle im Kundenstil: schwarzer Grund,
Icon weiß, Highlight rot. Keine Dopplung: Schulter/Schlegel-Passage,
Trocknen/Rauchen-Passage und „24/7 Stores" laufen nur als Grafik.

**ASR-Korrekturen** (auf Originalzeiten): Pfefferbeiser→Pfefferbeißer,
„Seitendarm 2022"→**„Saitendarm 20/22"** (Schafsaitling-Kaliber),
„Mischautomatenwolf"→„Mischautomaten-Wolf". **Beide gegen den Ton prüfen**
— sind fachlich plausibel, aber aus dem SRT nicht beweisbar.
„24-7 Stores" steht nicht im Untertitel (Shop-Logo trägt die Aussage,
Website-Wording). Neue Untertitel-Option `sizeScale` pro Seite für
unteilbar lange Wörter („FLEISCHEREI-FACHGESCHÄFTEN").

**QA:** 20-Frame-Sweep. Drei Fehler gefunden und behoben (Icon-Chip-Padding
Faktor 10 daneben → ragte in die Gesichtszone; Intro-Kaskade zu hoch;
Toggle lief seitlich über). Nach dem Fix alle Beats in den Zonen.

**Geliefert:**
`Ergebnisse/Renders/Setzer-V6-Pfefferbeisser_Overlay_V1_1080x1920_30p_Alpha.mov`
(ProRes 4444 Alpha, 1080×1920, **30 fps** — Davids Wunsch vom 28.08.,
die 24p-Fassung ist gelöscht; 68,9 s). Video 6 läuft damit anders als
Video 1 (24 fps) — die Komposition rechnet in Sekunden, fps ist Prop.

**Offen:** Saitendarm-Kaliber + „Mischautomaten-Wolf" gegen den Ton
prüfen; Laufzeit endet 68,9 s (letztes Wort 66,37 + Shop-Kasten + Outro) —
an den echten Schnitt anpassen (`durationInSeconds`/`timeOffsetSec`).

## 2026-08-28 (3) — Renders nach Video geclustert

`Ergebnisse/Renders/` hat jetzt einen Unterordner pro Video, benannt wie
die Quellordner auf der SSD:
- `01 - Unterschied Fleischkäse vs. Leberkäse/` — Overlay V1–V6
  (V6 = aktueller Stand, 24 fps). Die erste, unversionierte Datei heißt
  jetzt `…_Overlay_V1_…`, damit die Versionsreihe eindeutig ist.
- `06 - Pfefferbeisser/` — Overlay V1 (30 fps, aktueller Stand).

Kommende Videos (02–05, 07) bekommen je einen eigenen Ordner nach
demselben Muster. Framerates bleiben pro Video unterschiedlich —
wurde unterschiedlich gefilmt (Davids Bestätigung 28.08.).

## 2026-09-01 — Video 4 „Fleischsalat Zutaten": Schnitt transkribiert

**Auftrag:** Im Chargen-Ordner liegt `Video 4 zum Transkribieren/` mit dem
Export des fertigen Schnitts (`04 - Fleischsalat Zutaten.mp4` — reiner
AAC-Ton ohne Videospur, 131,8 s) und einer Premiere-Auto-UT. Video 4
transkribieren.

**Gemacht**
- Befund zur mitgelieferten `…UT.srt`: unbrauchbar — massive Verhörer
  („Essensbogen", „Fotionspräger", „Schmickiale") und ab ~35 s japanische
  Halluzinationen (マヨネーズ); in der Musik-/B-Roll-Lücke hat die
  Premiere-ASR die Sprache verloren. Datei bleibt als Referenz liegen.
- Schnitt mit **ElevenLabs Scribe** transkribiert (gleiche Pipeline wie der
  Rohmaterial-Lauf; Runner `_intern/transcribe_video4.py`, Cache
  `_intern/cache`, Wort-JSON `_intern/video4_scribe_words.json`):
  313 Wörter, eine Stimme, letztes Wort bei 131,3 s.
- Wort-SRT im Format der Video-6-Lieferung gebaut
  (`_intern/make_video4_srt.py`): ein Wort pro Cue, `<b>`-Tags, Timecodes
  **+1 h** (Premiere-Sequenz), Mindest-Cue-Dauer 30 ms (Scribe lieferte
  drei 0-ms-Wörter).
- **7 ASR-Korrekturen auf Originalzeiten**, alle im Transkript-MD
  dokumentiert. Kernkorrektur: 3× „Leola" → **„Lyoner"** (Grundzutat,
  Theken-Produkt; die Premiere-ASR hörte an denselben Stellen
  „Leonor"/„Leononkabel" — gleiche Lautfolge). Dazu „will"→„füllen",
  „vertan"→„verteilt", „Unumgänglich"→„Unhygienisch",
  „haftbleiben"→„haften bleiben".

**Geliefert**
- `Video 4 zum Transkribieren/04 - Fleischsalat Zutaten UT Scribe.srt`
- `Video 4 zum Transkribieren/04 - Fleischsalat Zutaten Transkript.md`
  (Volltext in Absätzen, Korrekturtabelle, Prüfliste)

**Offen**
1. **Gegen den Ton prüfen:** „Lyoner" (12,9/36,7/60,3 s), „füllen"
   (24,6 s — alternativ „wiegen"?), „verteilt" (69,8 s), „Unhygienisch"
   (74,2 s) sowie „Die Rindfleisch- und Fleischwurst" (15,5 s —
   ungewöhnlich neben der Lyoner, unkorrigiert gelassen).
2. UT-Design später: „äh" (5×) raus, Zahlwörter ggf. als „250 g"/„125 g".
3. Inhalts-Flag fürs fertige Video: „wissenschaftlich bewiesen" (85,6 s)
   zur Handschuh-Bakterien-Aussage vor Auslieferung prüfen (Präzedenz:
   Leitsätze-Faktencheck Video 1).

## 2026-09-01 (2) — Video 4: Untertitel + Animationen (Overlay V1)

**Auftrag:** Passende Animationen + Untertitel zum frisch transkribierten
Video 4. Grundlage: das Scribe-Worttranskript aus der Vormittagssession
(t = 0 ist der erste Frame des Schnitts — die Zeiten stammen aus dem
Audio-Export des Schnitts selbst, kein Offset nötig).

**Neue Komposition** `Setzer-Fleischsalat-Zutaten`
(`tools/motion/src/clients/setzer/projects/fleischsalat-zutaten/`) im
Design-System aus Video 1/6 (rot–schwarz, Iconset-Stil, Arial Black,
Kunden-Logo + Claim-Vektor). 131,78 s, **30 fps als Standard übernommen
(wie Video 6) — Framerate gegen die echte Sequenz prüfen**, die
Komposition rechnet in Sekunden, fps ist Prop.

**Leitmotiv Zutaten-Checkliste** (zwei Auftritte desselben Elements):
- Aufbau 5,4–19,9 s: fünf Chips stapeln sich auf den Wortzeiten —
  ESSIGGURKEN · MAYONNAISE (Sub „ÖL · WASSER · GEWÜRZE") · LYONER
  (Sub „AUCH IN DER THEKE") · FLEISCHWURST · GEWÜRZE (Sub „Z. B. SENF").
  Fünf eigene Line-Icons im Etikett-Stil (Gurke, Mayo-Glas, Ring-Lyoner
  mit Clip, Wurst, Streuer).
- Abhaken 34,9–47,6 s: dieselben Chips kehren zurück, rote Haken
  zeichnen sich auf den gesprochenen Zeiten (Lyoner 36,9 · Mayo 37,7 ·
  Gurken 39,8 · Fleischwurst 43,4 auf „alle Zutaten drin" · Gewürze
  45,2), Stack-Puls auf „vermengt" (46,55).

**Weitere Beats:** Waagen-Icon (49,95–55,85) · HAND ✓ vs. MASCHINE ✗ —
Zahnrad dreht und wird auf „kaputt" (60,75) rot durchgestrichen, roter
Ring pulst auf „von Hand" (61,55) · 5-MIN-Timer mit konstant laufendem
rotem Zeiger (63,9–73,9, trägt „fünf Minuten lang") · Waschen-/
Desinfizieren-Icons nacheinander (76,45/80,55) · zwei Becher-Chips
**250 g / 125 g** auf den Zahlzeiten (104,75/106,3) · 250-g-Chip kehrt
bei der Becher-Demo zurück und pulst auf „250 Gramm raus" (119,3) ·
Marken-Outro Logo + Claim (127,7–131,7, trägt den Schlusssatz).

**Dopplungs-Fenster ohne Untertitel** (Grafik trägt die Sinneinheit):
Zutaten-Aufzählung 5,26–19,60 · Live-Zugabe 35,12–47,22 · „fünf Minuten"
63,86–65,64 · Grammaturen 104,60–108,94 · „250 g raus" 113,44–120,66 ·
Outro ab 127,56. Rest verbatim als Versalien-UT (30 Seiten, max. 2
Zeilen, „äh" raus, 1 Akzentwort/Seite), inkl. der unsicheren Wörter
(„Lyoner", „Unhygienisch" …) wie im Transkript korrigiert.

**QA:** 22 Still-Frames an allen Beat-Momenten gerendert und die soliden
Alpha-Grenzen (60 %-Schwelle) programmatisch gegen die Zonen gemessen —
nach zwei Korrekturen (leeres Checklisten-Panel durch Chip-Stack ersetzt;
sizeScale-Pass über 16 lange UT-Seiten, weil Arial-Black-Zeilen mit
W-lastigen Wörtern die 5-%-Ränder rissen) **alle Frames innerhalb**
(oben ≥ 46 %, unten ≤ 86 %, seitlich 5 %). Kein Abgleich gegen das
echte Bild möglich — der Schnitt liegt nur als Audio vor; Gesichtszone
ist die Setzer-Standardannahme (bis 46 % Höhe).

**Geliefert**
`Ergebnisse/Renders/04 - Fleischsalat Zutaten/Setzer-V4-Fleischsalat-Zutaten_Overlay_V1_1080x1920_30p_Alpha.mov`
(ProRes 4444 Alpha, 1080×1920, 30 fps, 131,78 s).

**Offen**
1. **Framerate bestätigen** (30 fps angenommen; Umstellen = fps-Prop +
   Neu-Render).
2. **Gesichtsfreiheit am echten Schnitt prüfen** — Overlay einmal
   drüberlegen (Positionen gegen Audio-only gebaut).
3. Transkript-Prüfliste aus der Vormittagssession gilt weiter
   („Lyoner" 3×, „füllen/wiegen", „Rindfleisch- und Fleischwurst",
   „wissenschaftlich bewiesen"-Claim). Ändert der Ton-Check Wörter,
   sind UT-Seiten und ggf. die LYONER-Chip-Zeile betroffen.
4. „FLEISCHWURST"-Chip trägt bewusst nur den sicheren Kern des
   unklaren O-Tons (15,5 s).

## 2026-09-01 (3) — Feedback David → Overlay V2

Sechs Punkte (Chat, 01.09.), alle umgesetzt:

1. **0:16 Fleischwurst komplett raus** — Chip aus der Checkliste
   entfernt (Stack hat jetzt 4 Zeilen); die Passage 15,5–17,4 s läuft
   ohne Grafik und ohne UT. Der O-Ton-Befund „Rindfleisch- und
   Fleischwurst" bleibt im Transkript dokumentiert.
2. **0:28 „Frisch in den Verkauf"** — Ton-Korrektur: Scribe hatte
   „frisch in der Theke" verhört. UT-Seite + SRT (Wörter 75/76)
   angepasst; das nachhängende „auch" bleibt unbestätigt.
3. **0:04 „was da drin ist"** — Ton-Korrektur, UT + SRT (Wort 13).
4. **0:40 Animation komplett raus** — die Abhak-Reprise der Checkliste
   (34,9–47,6 s) ist komplett entfernt (inkl. Haken-Mechanik und
   Wurst-Icon im Code). Da die Grafik die Sinneinheiten getragen hatte,
   läuft das Fenster 35,1–47,3 s jetzt als **fünf normale UT-Seiten**
   (Dopplungs-Regel symmetrisch angewandt).
5. **1:13 „Und dass hier dann jeder"** — Ton-Korrektur „wir"→„hier",
   UT + SRT (Wort 175).
6. **1:39 „Frisch in die Filiale"** — Ton-Korrektur, erneut ein
   „Theke"-Verhörer. UT + SRT (Wort 252).

**Erkenntnis daraus:** Scribe verhört im Dialekt systematisch Wörter
als „Theke" — die zwei verbliebenen „Theke"-Stellen (14,4 s, steht als
Chip-Subzeile „AUCH IN DER THEKE" im Overlay, und 130,7 s Outro) sind
damit prüfpflichtig; Liste im Transkript-MD aktualisiert.

**QA:** 10 Stills der geänderten Stellen gemessen — alle in den Zonen.

**Geliefert**
`Ergebnisse/Renders/04 - Fleischsalat Zutaten/Setzer-V4-Fleischsalat-Zutaten_Overlay_V2_1080x1920_30p_Alpha.mov`
(ProRes 4444 Alpha, 1080×1920, 30 fps, 131,78 s). V1 bleibt als
Versionsstand liegen. SRT + Transkript-MD im Video-4-Ordner auf dem
neuen Stand (12 Korrekturen, davon 4 ton-bestätigt).

**Offen:** Framerate-Bestätigung (30 fps angenommen) ·
Gesichtsfreiheit am echten Bild · Rest-Prüfliste („Lyoner" 3×,
füllen/wiegen, verteilt, Unhygienisch, Rindfleisch-Frage, 2× „Theke",
„auch" 28 s, „wissenschaftlich bewiesen"-Claim).
