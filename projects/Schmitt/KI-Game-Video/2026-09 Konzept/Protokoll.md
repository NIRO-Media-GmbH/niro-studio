# Protokoll — Schmitt / KI-Game-Video / 2026-09 Konzept

## 2026-09-11 — Projekt angelegt, Recherche

**Auftrag (Briefing)**
- Neues Video für die Schmitt Gruppe, vollständig KI-generiert, soll trotzdem aussehen wie vor Ort bei Schmitt.
- Kundenwunsch: „aus den vorhandenen Szenen an der Spedition mit den LKWs ein komplett neues Video mit KI“ — Richtung Videospiel „wie GTA“, Referenz Bausparkasse Schwäbisch Hall #MakeItReal (Minecraft-Stil).
- Referenzmaterial NAS: `01_Kunden/Schmitt Gruppe/02_Projekte/02_Projekt-05.26` (Video) und `03_Projekt-05.26 Fotoshooting` (Fotos).

**Gemacht**
- Ordner angelegt: `Ergebnisse/Recherche`, `_intern/kontaktboegen`.
- Material gesichtet, Kontaktbögen in `_intern/kontaktboegen/` (Fotos V3, B-Roll-/Drohnen-Proxys, vier Reel-Exporte):
  - Fotos V3: 159 JPG 6000×4000 — Zentrale 1–5, Poolauto/Jobrad 6–23, Technik 24–44, Büro/Dispo 45–88 + 117–130, Lager 89–109 + 149–159, LKW 110–116 + 131–138 + 147–148, Werkstatt 139–146; personenfrei u. a. 2–5, 69–72, 131–133, 136, 147, 148. Daneben `Fotos Bearbeitet` (150), `V2 (Auswahl ohne Logo)` (20), Fuji-Altbestand (129 JPG, 32 RAF).
  - Video 02: 307 GB, sortiert mit Proxys — Mavic 5,1K ProRes (12 Überflüge), Avata FPV 4K (~4 min Lagerflug), FX3 4K/100 fps LKW-B-Roll, a7IV, Actioncam; 5 Interviews (Berufskraftfahrer, Ausbildungsleiterin, Auszubildende, Lagermitarbeiter, Lagerleiter ehem. Azubi). Log-Profil, überwiegend hochkant.
  - Exporte: 4 Recruiting-Reels 9:16 (31–62 s). CI-Ordner auf NAS leer.
- Recherche: #MakeItReal, Schmitt-Websites, Higgsfield-CLI nur lesend (Modelle, Schemas, Credit-Preise — nichts generiert, nichts hochgeladen), GTA-VI-Termin, Recht (Marke, KUG/DSGVO, AI Act Art. 50, Higgsfield-AGB).
- Dossier: `Ergebnisse/Recherche/Schmitt KI-Game-Video Recherche.html` (auch als privates Artifact).

**Website-belegte Inhalte (schmitt.jobs, schmitt-vellberg.de, Stand 11.09.)**
- Gegründet 1935 in Mannheim mit einem Lastzug; 4. Generation seit 2023 (Julia Schmitt Jonas)
- Standorte: Crailsheim, Gaildorf, Obersontheim, Schwäbisch Hall, Schwäbisch Hall-Sulzdorf, Vellberg
- Claim: „Ein Ziel – eine Leidenschaft“
- Stellen: Berufskraftfahrer Nah-/Fernverkehr, Staplerfahrer, Schichtführung Lager, Stv. Dispositionsleitung, IT-Anwendungsadministrator Lagerverwaltungssystem, Facility Management Elektrik, Logistikmitarbeiter kaufmännisch, Aushilfe Haustechnik; Ausbildung & Studium — alle mit „(m/w/x)“
- Benefits: 30 Tage Urlaub, Job Rad, Werkswohnung, bAV, bKV, Edenred-City-Karte, Weiterbildungen/Coaching, Mitarbeiterrabatte, Gesundheitsmanagement, Mitarbeiterunterstützung, Fitnesskooperationen
- **Widersprüche:** Fläche „rund 270.000 m²“ (schmitt.jobs) vs. „über 300.000 m²“ (Firmenseite); Reel 2 nannte „29 Tage Urlaub“, Website 30

**Befunde Werkzeuge (Higgsfield Creator, 4.799 Credits)**
- Credits: Flux Kontext 1,5 · Nano Banana Pro 2 · Seedream 5 Pro 3 · GPT Image 2 6,5 · Kling 3.0 10 s 17,5 · Wan 3.0 10 s 17,5 · Veo 3.1 8 s 22 · Seedance 2.0 5 s/720p 22,5, 10 s/1080p 90, 10 s/4K 220 · Seedance 2.5 10 s/1080p 90
- Video-Edit: `kling_video_edit` (Kling 3.0 Omni Edit, std/pro/4k), `seedance_2_5 --mode video_edit` (genau 1 Video, bis 1080p), `flux_3_video_edit`; Workflow `kling3_0_motion_control`
- Seedance 2.0: bis 3 Video- und 9 Bildreferenzen; lehnt echte Gesichter als Referenz meist ab
- Higgsfield darf Uploads zum Training nutzen (außer Enterprise); Ergebnisse kommerziell nutzbar und übertragbar

**Empfehlung (vorgelegt, nicht entschieden)**
- Hybrid: Fotos → Game-Keyframes → Clips; Drohne/FPV → Video-to-Video; HUD in Remotion; Schluss kippt in echten Drohnenflug („Make it real“)
- Kein „GTA“ in Video und Posts, eigenes HUD, Mitarbeitende nur mit KI-Einwilligung, durchgehend als KI-generiert kennzeichnen
- Look-Test ≈ 300 Credits: Schmitt-132/-136/-3 × 2 Looks × 2 Modelle, ein Seedance-Clip, V2V-Test Mavic DJI_0373

**Offen**
- Freigabe Look-Test (Upload zu Higgsfield + Credits)
- Format/Länge (Reel 9:16 vs. 16:9), Fokus Spedition vs. ganze Gruppe, erkennbare Mitarbeitende ja/nein, Release um GTA-VI-Start 19.11.2026, Budget/Aufstockung
- Endcard-Schreibweise: Schmitt (m/w/x) vs. Studio-Regel (m/w/d)

## 2026-09-11 — Look-Test GTA

**Freigabe (User):** Look-Test ja — Upload von Schmitt-132/-136/-3 und Mavic DJI_0373 zu Higgsfield, ~300 Credits. Vorgabe: „genau dieser GTA-Look“. Wenn der Look passt → finales Script.

**Gemacht**
- Eingänge in `_intern/looktest/input/`: Fotos auf 2400 px ohne EXIF; DJI_0373 von 5,7 bis 15,5 s, D-Log → DJI-LUT „Mavic 3 D-Log to Rec.709“ (liegt im Resolve-LUT-Ordner), 1080p.
- 18 Standbilder in `Ergebnisse/Look-Test/keyframes/`: je Foto Artwork (B), Ingame Runde 1 (A) und Ingame Runde 2 (A2), jeweils Nano Banana Pro und GPT Image 2; Prompts nennen „Grand Theft Auto V“ — kein Modell hat abgelehnt.
- Clips in `Ergebnisse/Look-Test/clips/`: Seedance 2.0 aus dem Schmitt-136-Artwork (5 s, 720p); Drohnenflug nur per Text-Prompt mit Seedance 2.5 Video-Edit (1080p) und Kling 3.0 Omni Edit (pro).
- Zusatztest im Budget: erstes Drohnenbild im GTA-Ingame-Look als Stilvorlage für Kling Omni Edit.
- Vergleichsseite `Ergebnisse/Look-Test/Seite/schmitt-look-test.html` (Vorher/Nachher-Regler, synchrone Clips).

**Befunde**
- Artwork mit Nano Banana Pro trifft den GTA-Ladebildschirm am klarsten; Logos, Claim und Website bleiben lesbar. Der Seedance-2.0-Clip daraus ist stabil (Logo 5 s scharf).
- Ingame Runde 1 zu fotonah; Runde 2 mit ausdrücklichen Spielgrafik-Merkmalen liest sich als Game-Screenshot.
- GPT Image 2 macht Los Santos daraus (Palmen, Villa, Hochhäuser bei 136 und 3) → finaler Prompt muss die echte Umgebung festschreiben. Beide Modelle erfinden Autos vor der Zentrale.
- Video-to-Video nur per Prompt: Kamera und Logo exakt, aber nur warme Abendstimmung statt Spielgrafik; Kling bleicht Solardächer aus.
- Creator-Tarif: höchstens 8 gleichzeitige Aufträge (`rate_limit_reached`), abgeprallte Aufträge werden nicht berechnet. Preise: Kling Omni Edit 10 s pro = 18 Credits, Seedance 2.5 Video-Edit 10 s 1080p = 88,56 Credits.
- Zusatztest Stilvorlage: erstes Drohnenbild im Ingame-Look (Nano Banana Pro 2 Cr., GPT Image 2 6,5 Cr.) als Bildreferenz für Kling 3.0 Omni Edit (je 18 Cr.) → **funktioniert**: der echte Flug wird zur Spielgrafik, Kamera, Gebäude und Logo bleiben exakt; die GPT-Vorlage wirkt am stärksten. Fremdmarken auf Trailern (DHL, Yang Ming) bleiben sichtbar.
- Verbrauch gesamt: 250,06 Credits in 25 Aufträgen (Stand 4.548,94).
- Vergleichsseite fertig: `Ergebnisse/Look-Test/Seite/schmitt-look-test.html`, privat veröffentlicht: https://claude.ai/code/artifact/c1295436-77cb-4cd5-96d1-967d9c375754 (Recherche-Dossier: https://claude.ai/code/artifact/bcf32181-263e-4c78-9713-eee79a31fab7).

**Offen**
- ~~Look-Entscheidung~~ → entschieden, siehe nächster Eintrag

## 2026-09-11 — Look-Entscheidung und Script-Vorgaben (User)

**Entscheidungen**
- **Look:** wie `clips/DJI_0373_seedance25_edit.mp4` (Seedance 2.5 Video-Edit nur mit Text-Prompt: warme Goldene-Stunde-Stimmung, nah am Realbild) — nicht Artwork, nicht Kling mit Stilvorlage. Referenzbilder in `_intern/lookref/`.
- **Musik:** https://www.youtube.com/watch?v=MfWggaf6D60 („das Lied nehmen wir“) — Titel und Lizenz prüfen (NIRO hat nur Artlist + Envato).
- **Format:** Hochformat 9:16, höchstens 45 s.
- **Fremdmarken** (DHL, Yang Ming, OPTIMA …) retuschieren; zusätzliche Autos im Bild sind in Ordnung.
- **Script:** unterhaltsames Employer-Branding-Video, das man gern anschaut; ein Hauptprotagonist, der mit NPCs interagiert; Fahrszenen Pflicht; alles in 3rd Person; nicht gewalttätig. Zuerst Vorschläge.

**Befund Musik**
- Der Link ist ein Fan-Upload von „Inner Light“ — Elderbrook & Bob Moses (Parlophone UK / Warner, 2021; 121 BPM, fis-Moll, 4:18). Der Song ist der Abschluss des GTA-VI-Trailers „An Extended Look“ (Ende August 2026), Streams danach +1.070 %.
- Nicht über Artlist/Envato abgedeckt → für kommerzielle Nutzung Sync-Lizenz (Master + Verlag) nötig; in Business-Accounts auf Instagram/TikTok nicht aus der Musikbibliothek nutzbar. Zusammen mit dem GTA-VI-Look sehr nah an der Rockstar-Kampagne.
- Vorschlag: Script-Timing auf 121 BPM bauen (4 Takte ≈ 7,9 s), parallel Lizenz anfragen oder Artlist/Envato-Alternative mit gleichem Tempo suchen.

**Script-Vorschläge vorgelegt:** A „Neuer Spielstand“ (erster Tag als Tutorial), B „Nebenmissionen“ (NPC-Comedy, Empfehlung), C „Level-Up“ (Azubi → Profi). Bewusst verworfen: Speedrun und Verfolgungsjagd (Tempo-Assoziation passt nicht zu einer Spedition).

**Offen**
- Konzeptwahl → danach Shot-für-Shot-Script
- Musiklizenz oder Alternative
- Stellen- und Ausbildungstitel vor Script-Freigabe gegen schmitt.jobs prüfen (Ausbildungsliste stammt von Seiten aus 2023)

## 2026-09-11 — Story A festgelegt, Produktionsweg

**Vorgaben (User)**
- Alles direkt in 9:16 generieren, nichts nachträglich croppen.
- Musik („Inner Light“) für die Preview okay, später ggf. tauschen; kein Schnitt auf den Takt nötig.
- Story A mit Änderungen:
  - 0–4 s Figurenauswahl als Startscreen: Animation mit generierten Figurenbildern in Fenstern, Hintergrund ein generiertes Hallen-Video, Übergänge ineinander, läuft automatisch ab.
  - Nach der Auswahl winkt die Ausbilderin ihn heran („Erster Tag? Dann komm mal mit.“), erste Quest „Hol dir deinen Schlüssel“.
  - Dialoge mit Higgsfield-Stimmen vertont und lippensynchron direkt in der Videogenerierung.
  - Kein Schlüsselwurf: Er holt den Schlüssel selbst in einem Gebäude, geht wieder raus und steigt ein; alle Szenen mit NPCs belebt.
  - Beim Einsteigen fährt die Kamera in einer flüssigen Bewegung auf die Fahrzeugkamera (weiter weg), kein harter Schnitt.
  - Freischaltungen und HUD kommen nachträglich per Animation; sehr nah an GTA, mit eigenen Ergänzungen.
  - Fahrt zu einem anderen Schmitt-Standort (Material aus älteren Projekten prüfen); rückwärts an die Entladerampe, Entladen passiert im Gebäude (außen wenig zu sehen) → gut darstellen.
  - „Auftrag erledigt“, Abklatschen mit einem Kollegen, Kamera fährt raus.
- Alle Shots einheitlich, flüssige Übergänge, Figur immer gleich mit gleicher Kleidung → zuerst Avatar und Stilreferenz. Weg zum besten Ergebnis entscheidet Claude.

**Entscheidungen (Claude)**
- Feste erfundene Figuren (Hauptfigur, Ausbilderin): Kandidaten → Auswahl → Referenzblatt (Ansichten, Gesicht); keine echten Mitarbeitenden.
- Übergänge: letztes Bild eines Shots wird Startbild des nächsten; lange Takes per Verlängerung.
- Stimmen: deutsche TTS-Stimme je Figur, als Audio-Referenz in Seedance 2.0 für Lipsync.
- Figuren-Kandidaten gestartet (4 × Hauptfigur, 2 × Ausbilderin, Nano Banana Pro / GPT Image 2, 9:16) → `Ergebnisse/Figuren/Kandidaten/`.

**Projekt 01 „6x Ads“ (Dreh 14.11.2023, Nachdreh 03.04.2025):** A7iv 186 Clips (180 GB), A7sIII 83 (141 GB), Avata 2, FX3-Nachdreh 35; alles 4K 25p bzw. Avata 50p, keine Proxys; Export nur „1.1 Vorstellung Schmitt – Julia“ V1–V5. Kontaktbögen in Arbeit.

## 2026-09-11 — Script V1, Casting, Stimmproben

**Gemacht**
- Figuren-Kandidaten in 9:16 (`Ergebnisse/Figuren/Kandidaten/`): Luca K1–K4 (Nano Banana Pro, K1 zusätzlich GPT Image 2) und Ausbilderin K1/K2; Vorlagen Schmitt-132 bzw. Schmitt-3 plus Look-Bild; 18,5 Credits.
- Stimmproben (`Ergebnisse/Stimmen/Proben/`): Ausbilderin „Erster Tag? Dann komm mal mit.“ mit ElevenLabs Helena, Nora, Vera und Inworld Johanna (de); Luca „Alles klar, bin dabei!“ mit ElevenLabs Julian, Marcus, Jasper und Inworld Josef (de). Kosten je Satz: ElevenLabs/Minimax 0,15, Seed Speech 0,1, Qwen 0,02, Inworld 2 Credits.
- Script V1 „Neuer Spielstand“ (9 Shots, 45 s) mit Casting und Konsistenz-Plan: `Ergebnisse/Script-Casting/Seite/schmitt-neuer-spielstand.html`, privat veröffentlicht: https://claude.ai/code/artifact/64ba8881-fbf2-43b3-ae77-22519da765d1
- Projekt-01-Sichtung A7iv: Entladen durchs Rampentor von innen (Clips 7202–7211), Halle mit Holzdach und Seitenentladung eines Planenaufliegers (7289–7304), Hof mit Schmitt-LKW und Fahrerkabine (7227–7262), Büros (7317–7341).
- Stimmen bei Higgsfield: `text2speech_v2` (elevenlabs, minimax, seed_speech, vibe_voice, cozy_voice; 113 Preset-Stimmen ohne Sprachangabe), `inworld_text_to_speech` mit deutschen Stimmen Johanna/Josef, `qwen_audio_tts` mit `language de`. Seedance 2.0 nimmt `audio_references` für Lipsync.

**Offen**
- Casting-Auswahl (Figur, Ausbilderin, Stimmen), Script-Freigabe, Endcard-Schreibweise (m/w/x oder m/w/d), Pilot (≈ 100 Credits)
- ~~Zweiter Standort sichten~~ → erledigt und in Shot 6 eingetragen: Avata DJI_0168/0169 (FPV um Schmitt-Sattelzug, weiße Halle mit gelbem Sockelstreifen, überdachte Rampe mit angedocktem LKW), A7sIII BNA6693–6703 (Hof vor Tor-Reihe), BNA6705–6716 (Fahrerkabine), BNA6752–6754 (Empfang „schmitt LOGISTIK“), FX3-Nachdreh 1955–1960 (LKW im Sonnenlicht, fährt vorbei). Welcher Standort das ist, soll der User bestätigen.

## 2026-09-11 — Casting entschieden, Produktion Shot 0 + 1 gestartet

**Entscheidungen (User)**
- Alle Figuren noch zu fotorealistisch, sie sollen nach Game aussehen. Beste Hauptfigur: `luca_k3_nano_banana_pro` (kurze schwarze Haare, kurzer Bart).
- Ausbilderin: K2 (rotbrauner Bob).
- Stimmen: Ausbilderin = ElevenLabs „Helena“, Luca = ElevenLabs „Jasper“.
- Schreibweise auf Karten und Endcard: „(m/w/d)“.
- „Lets go, mach erstmal die ersten 2 Shots ready“ → umgesetzt als Shot 0 (Startscreen) + Shot 1 (Erster Tag).

**Plan**
- Game-Look der Figuren in zwei Stufen testen (L1 GTA-VI-Cutscene, L2 stärker stilisiert) → Referenzblätter, NPC-Porträts für die Auswahlkarten, Zentrale-Vorlage, Hallenflug, Keyframe und Video Shot 1 mit Lipsync (Helena-Satz), Startscreen in Remotion, Preview Shot 0 → 1 mit Song. Rahmen ≈ 300 Credits.

**Game-Look-Test (14,5 Credits, `Ergebnisse/Figuren/Game-Look/`)**
- Stufe L1 (GTA-VI-Cutscene) bleibt bei beiden Modellen zu fotorealistisch; L2 mit GPT Image 2 nur halb stilisiert.
- **Entscheidung (Claude): L2 mit Nano Banana Pro** (`luca_k3_L2_nano_banana_pro.png`) ist die Stilvorlage für alle Figuren — eindeutig Spielfigur, Gesicht, Bart und Outfit bleiben.
- Ausbilderin in L2 noch zu fotorealistisch → neu mit Luca-L2 als Stilvorlage.
- Remotion: Kunde `schmitt` angelegt (brand.json: Blau #2554A5, Dunkelblau #233359, Gelb #F2B233 aus der Lackierung abgeleitet, Barlow Condensed), Komposition `neuer-spielstand` (Startscreen mit 6 Karten inkl. „Initiativ“, Auswahlrahmen, Zoom-through in Shot 1), Symlink `public/projects/schmitt-ki-game-video` → `Material/Video`.

## 2026-09-11 — Shot 0 + Shot 1 als Preview fertig

**Gemacht**
- Figuren-Referenzen im Game-Look L2 (`Ergebnisse/Figuren/Referenz/`): Luca von hinten, von der Seite, Gesicht; Ausbilderin mit Luca als Stilvorlage, Variante 2 gewählt.
- Karten-Porträts (5, gezeichneter Game-Stil): `Ergebnisse/Startscreen/Karten/` → als JPG in `Material/Video/startscreen/`.
- Ortsvorlagen `Ergebnisse/Orte/ort_zentrale.png` und `ort_halle.png`; Hallenflug mit Seedance 2.0 (5 s, 1080×1920) → `Material/Video/startscreen/halle.mp4`.
- Startbild Shot 1: `Ergebnisse/Keyframes/shot1_start_v2.png` (Ausbilderin größer im Bild, Luca steht noch).
- Shot 1: zwei Takes Seedance 2.0 (5 s, 1080×1920, 24 fps) mit Helenas Satz als `--audio-references` → `Ergebnisse/Shots/`. Scribe-Prüfung: Beide sprechen „Erster Tag? Dann komm mal mit.“ — Take 1 bei 3,06–5,00 s in der Nahaufnahme, Lippen passen plausibel; Take 2 bei 0,36–2,62 s, Gesicht dabei klein. **Take 1 gewählt.**
- Remotion `Schmitt-NeuerSpielstand` (25 fps): Startscreen 3,3 s (Karten fliegen ein, Rahmen springt fünfmal, rastet auf „Berufskraftfahrer (m/w/d)“ ein, „A Spiel starten“, Zoom-through) → Shot 1. Alle Texte in der Reels-Safe-Zone (y 134–1104, x 54–1026). Menü-Sounds von remotion.media.
- Previews: `Ergebnisse/Renders/Preview_Shot0-1_take1.mp4` (Favorit) und `Preview_Shot0-1_take2.mp4`, je 8,4 s, H.264.
- Verbrauch seit der Casting-Entscheidung: 184 Credits (Stand 4.341,54).

**Offen**
- Song „Inner Light“ fehlt in der Preview: keine Audiodatei vorhanden, YouTube-Download geht nicht → Datei vom User.
- HUD für Shot 1 (Minimap) kommt in der Post.
- In Take 1 geht die Ausbilderin Luca entgegen, statt am Eingang zu bleiben — passt als Übergang in Shot 2 (Quest).

## 2026-09-11 — Preview abgelehnt: Cartoon statt GTA V

**Feedback (User):** „Nein nein nein, es sieht alles nur nach Cartoon aus und nicht nach GTA 5.“
- Ursache: „zu fotorealistisch“ wurde als Stilisierung gelesen; die Stufe L2 (Nano Banana Pro) war cartoonhaft, und als Stilvorlage für Karten, Orte und Shot 1 hat sie alles in gezeichneten Cartoon-Stil gezogen.
- **Zielbild:** GTA-V-Ingame-Grafik — halbrealistische 3D-Spielfiguren und -Welt (Spiel-Hautshader, Haar-Cards, Spieltexturen, harte Echtzeit-Schatten, warmes GTA-Grading), weder Foto noch Cartoon (keine Konturen, kein Cel-Shading).
- Verworfen: L2-Figuren, Karten-Porträts, Orte, Hallenflug und Shot-1-Takes im Cartoon-Stil (Dateien bleiben als Referenz liegen). Die Startscreen-Animation in Remotion bleibt, nur die Bilder werden getauscht.
- Neuer Stiltest (≈ 25 Credits): Luca und Ausbilderin aus den ursprünglichen Kandidaten plus ein Shot-1-Testbild, jeweils GPT Image 2 und Nano Banana Pro; Stilanker sind die GTA-V-Ingame-Bilder aus dem Look-Test (Runde 2) → `Ergebnisse/Figuren/GTA5-Test/`. Freigabe durch den User vor der Neuproduktion.
- Ergebnis Stiltest (25,5 Credits, Stand 4.316,04; Vergleichsbogen `Ergebnisse/Figuren/GTA5-Test/Vergleich_GTA5-Test.jpg`): **GPT Image 2 kommt GTA V am nächsten** — harte Sonne, kräftiges Grading, Asphalt und Gebäude wie gerendert; Gesichter noch recht realistisch. **Nano Banana Pro bleibt fast so fotorealistisch wie die Kandidatenbilder** — mit fotorealistischer Vorlage für diesen Look ungeeignet. Shot-1-Testbild von GPT: Schulterkamera, Ausbilderin am Eingang, Kollegen und Auto — Personen noch klein. Warte auf User-Entscheidung zur Richtung.
- **Entscheidung (User):** „Ja GPT, suche dir online selbst GTA-Ingame-Screenshots heraus.“ → Richtung GPT Image 2; echte GTA-V-Ingame-Screenshots dienen nur intern als Stilvorlage (Quelle: offizielle Steam-Shopseiten von GTA V / GTA V Enhanced), nichts aus GTA im Ergebnis. Danach Neuproduktion von Figuren-Referenzen, Karten, Orten, Hallenflug und Shot 1 im GTA-V-Look.
- Stilvorlagen geladen (nur intern, nicht veröffentlichen) → `_intern/stilreferenz-gta5/`: aus 87 offiziellen Steam-Screenshots (GTA V Enhanced 11, Legacy 76; Liste per Steam-API `appdetails`) fünf Tageslicht-Szenen ohne eingebrannte Logos gewählt, je 1920×1080 von `shared.akamai.steamstatic.com`:
  - `gta5_3240220_07.jpg` (919 KB) — drei Figuren zu Fuß in der Wiese, von hinten
  - `gta5_271590_74.jpg` (714 KB) — Straße mit Passanten
  - `gta5_271590_38.jpg` (928 KB) — Sattelzug auf der Straße
  - `gta5_271590_41.jpg` (608 KB) — Figur in der Einfahrt
  - `gta5_271590_53.jpg` (410 KB) — Büro innen (für die Dispo)
- Beim Sichten ausgeschlossen als Ganzbild-Vorlage: #41 (Figur mit Pistole) und #38 (bewaffnete Fahrzeuge) — sonst wandern Waffen in die Bilder. Genutzt: #07 zugeschnitten auf Figuren und Umgebung, #74 zugeschnitten auf Passanten; für die Figurendarstellung nur Kopfausschnitte aus #41 und #53 (ohne Waffe, ohne Geld).
- GPT Image 2 mit Screenshot-Vorlagen (Luca vorne/hinten, Ausbilderin, 2 Startbilder Shot 1; 32,5 Credits, Stand 4.283,54 → `Ergebnisse/Figuren/GTA5/`, `Ergebnisse/Keyframes/GTA5/`): Bildaufbau gut, aber in der 1:1-Detailansicht **Gesichter wie Fotos echter Menschen** — nicht GTA V, dem User nicht vorgelegt.
- Nächster Ansatz: Lucas 3D-Spielfigur (L2) als Ausgang, Richtung GTA-V-Figurendarstellung rendern; kleiner Modellvergleich (GPT Image 2, Nano Banana Pro, Flux Kontext, Seedream 5 Pro).
- Modellvergleich (19,5 Credits, Stand 4.264,04 → `Ergebnisse/Figuren/GTA5-Matrix/`, Gesichter 1:1 gegen GTA-V-Kopfausschnitte): GPT mit Fotovorlage bleibt fotorealistisch; GPT ohne Foto realistisch mit leichtem CG-Glanz; **Nano Banana Pro und Seedream 5 Pro landen als saubere 3D-Spielfigur am nächsten an GTA V**; Flux Kontext wird deutlich stilisierter (AAA-Held, eher zu stilisiert). Weil der Look zweimal danebenlag, gehen die vier Stufen A–D als Auswahl an den User (`Luca_GTA5_Optionen.jpg`).
- **Entscheidung (User): Stufe A** = GPT Image 2 ohne Fotovorlage, aus der 3D-Figur L2 mit GTA-V-Kopfausschnitten als Stilvorlage (`m5_gpt_ohnefoto.png` → `Ergebnisse/Figuren/A/luca_A_vorne.png`). Dieses Bild ist ab jetzt die Render-Vorlage für alle Figuren, Karten und Orte.
- Neuproduktion Welle 1 gestartet (≈ 85 Credits): Luca hinten/Seite/Gesicht, Ausbilderin v1 (aus K2-Foto) und v2 (aus L2-Figur), vier NPC-Karten, Zentrale und Halle → `Ergebnisse/Figuren/A/`, `Ergebnisse/Startscreen/Karten-A/`, `Ergebnisse/Orte/A/`; danach automatisch zwei Startbilder Shot 1 → `Ergebnisse/Keyframes/A/`. Hallenflug und Shot-1-Takes erst nach Sichtprüfung.

## 2026-09-11 — Look A: Sichtprüfung, Hallenflug, Startbilder, Shot-1-Takes

**Sichtprüfung Welle 1** (Gesichter 1:1 nebeneinander)
- Luca vorne, hinten, Seite und Gesicht sind konsistent. Die Nahaufnahme ist etwas detailreicher, bleibt aber Spielfigur.
- **Ausbilderin v2 gewählt (Claude):** glatte Spielfigur-Haut wie Luca A. v1 (aus dem K2-Foto) wirkt wie das Foto einer echten Frau.
- NPC-Karten (Staplerfahrerin, Schichtführer, Disponentin, Azubi) passen zu Look A, keine Fremdmarken. Zentrale mit „schmitt“-Schriftzug und Halle ohne Palmen.
- Startbilder v1/v2 aus Welle 1 verworfen: mit Ausbilderin v1 gebaut, Ausbilderin zu klein für Lipsync.

**Gemacht**
- Hallenflug Look A: Seedance 2.0 aus `ort_A_halle.png` (5 s, 1080×1920, 24 fps, ohne Ton) → `Ergebnisse/Startscreen/halle_A_seedance20_5s.mp4` → `Material/Video/startscreen/halle.mp4`. Die Cartoon-Kopie ist ersetzt, das Cartoon-Original liegt weiter in `Ergebnisse/Startscreen/`.
- Karten Look A als JPG (900 px) → `Material/Video/startscreen/karte_*.jpg`. Berufskraftfahrer = `luca_A_vorne.png`.
- Startbilder Shot 1 neu mit Ausbilderin v2 (GPT Image 2):
  - `shot1_A_start_v3.png`: Prompt wie Welle 1.
  - **`shot1_A_start_v4.png` (gewählt):** Ausbilderin ca. 4 m vor Luca, Gesicht lesbar, „schmitt“-Schriftzug über dem Eingang im Bild, Kollegen mit Kaffee im Hintergrund.
- **Fehler in der Remotion-Komposition behoben:** Keine `scale`-Animation hat gegriffen, auch nicht in der abgelehnten Preview. Ursache: React 18.3 hängt an Zahlen „px“ an, der CSS-Wert wird ungültig.
  - Betroffen waren Karten-Zoom, Einrasten (1 → 1,07), Zoom-through (1 → 1,6) und die Landung von Shot 1 (1,22 → 1).
  - Die Werte stehen jetzt als String.
  - Karten-Ausschnitte an die neuen Bilder angepasst: Luca mit Zoom 1,6 auf Kopf und Oberkörper, NPCs ohne Zoom und mit Kopffreiheit.
  - Stills von Karten, Einrasten und Zoom-through geprüft.
- Shot 1: drei Takes mit Seedance 2.0 aus Startbild v4 (5 s, 1080×1920, 24 fps). Referenzen: Luca hinten, Ausbilderin v2, Zentrale; Helenas Satz als Audio-Referenz. Ergebnis → `Ergebnisse/Shots/shot1_A_take1–3.mp4`, Kopien mit dichten Keyframes in `Material/Video/shots/`.
  - Scribe-Prüfung: Take 1 spricht „Erster Tag? Dann komm mal mit.“ bei 0,14–1,92 s, Take 2 bei 0,08–1,82 s.
  - Take 3: Der erste Scribe-Lauf erkannte nur „[outro jingle]“ → zunächst verworfen. **Später korrigiert:** Zwei weitere Läufe finden den Satz vollständig (0,12–1,86 s). Der erste Lauf war ein Scribe-Fehler (siehe Eintrag „Shot 1 getauscht“).
  - Lippen-Check mit Standbildern je Wort: In Take 1 passt es — Mund offen bei „Erster“ und „Tag“, geschlossen in der Pause, Armgeste zum Eingang bei „komm mal mit“. In Take 2 bleibt der Mund bei „Erster Tag“ fast geschlossen.
  - Ablauf beider Takes: Die Ausbilderin winkt, spricht, dreht sich zum Eingang und geht vor. Luca folgt, die Kamera bleibt hinter ihm.
  - **Take 1 gewählt.**
- Remotion: Whoosh am Übergang ab dem Schnitt auf 0,15 abgesenkt, weil der Satz direkt am Anfang von Shot 1 liegt.
- Verbrauch dieser Runde: 193 Credits (Hallenflug 45, Startbilder 13, Takes 135), Stand 3.986,54.
- Preview neu: `Ergebnisse/Renders/Preview_Shot0-1_A_take1.mp4` (Favorit, an den User geschickt) und `Preview_Shot0-1_A_take2.mp4` als Alternative. Beide 8,4 s, 1080×1920, H.264, ohne Musik.
  - Kontaktbogen geprüft: Karten fliegen ein, der Rahmen springt und rastet ein, Zoom-through, Shot 1 landet mit Lichtblitz.
  - Pegel Take 1: Mittel −25,5 dB, Spitze −4,8 dB.

**Offen**
- Feedback des Users zur Preview im Look A, danach Shot 2 (Schlüssel holen).
- Song „Inner Light“ als Audiodatei, dazu Sync-Lizenz oder Alternative.
- HUD/Minimap in der Post.
- Welcher Standort der zweite Schmitt-Standort ist (Shot 6).

## 2026-09-11 — Shot 1 getauscht: Take 3

**Wunsch (User):** „tausche den aktuellen shot mit dem aus: https://higgsfield.ai/asset/all/9240485a-f699-4ba7-b494-f318b15da519“
- Der Link führt zum Seedance-Job `9240485a…`. Er ist identisch mit `Ergebnisse/Shots/shot1_A_take3.mp4` (Job-Log und md5 stimmen überein).
- Nachprüfung Ton: Scribe erkennt mit und ohne Audio-Event-Tags „Erster Tag? Dann komm mal mit.“ bei 0,12–1,86 s. Die Einstufung „ohne Satz“ aus der ersten Prüfung war falsch.
- Lippen (Standbilder je Wort): Der Mund bewegt sich dezenter als in Take 1, in der Pause ist er geschlossen — plausibel.
- Ablauf: Die Ausbilderin winkt während „Erster Tag“, dreht sich dann und geht vor Luca zum Eingang. Sie bleibt bis zum Ende im Bild.
- Preview neu gerendert: `Ergebnisse/Renders/Preview_Shot0-1_A_take3.mp4` (8,4 s, 1080×1920, H.264, ohne Musik; Mittel −26,5 dB, Spitze −3,4 dB), an den User geschickt.
- Standardwerte der Komposition `Schmitt-NeuerSpielstand` auf Take 3 und 8,38 s gesetzt.
- Keine neuen Credits.

## 2026-09-11 — Shot 2 „Die erste Quest“

**Freigabe (User):** „Finde ich mega, weiter mit Shot 2“ → Look A und Shot 0 + 1 (Take 3) abgenommen.

**Script V1, Shot 2 (0:09–0:13)**
- Die Kamera schwenkt halbseitlich, beide sind im Bild. Die Ausbilderin tippt aufs Tablet und deutet zur Dispo.
- Dialog: Ausbilderin „Dein Schlüssel hängt in der Dispo. Hol ihn dir!“ – Luca „Bin dabei.“
- Einblendungen (Quest, Zielmarker Dispo) kommen später per Animation.

**Gemacht**
- Stimmen (ElevenLabs über Higgsfield, je 2 Takes, 0,6 Credits) → `Ergebnisse/Stimmen/Shot2/`:
  - Helena v1 und v2 korrekt, **v2 gewählt** (deutlichere Pause vor „Hol ihn dir“).
  - Jasper v1 hört Scribe als „In dabei“ → verworfen. **v2 „Bin dabei“ gewählt.**
  - Dialogdatei `Material/Video/audio/shot2_dialog.mp3` (3,6 s): Helena 0,10–2,34 s, Pause, Luca 2,84–3,34 s. Scribe erkennt zwei Sprecher. Die Einzelzeilen liegen daneben als `shot2_ausbilderin_helena.mp3` und `shot2_luca_jasper.mp3`.
- Startbild = letztes Bild von Shot 1 Take 3 → `Ergebnisse/Keyframes/A/shot1_A_take3_letztes_bild.png` (1080×1920; Luca von hinten, Ausbilderin an der Glastür).
- Drei Takes Seedance 2.0 gestartet (5 s, 1080p, 9:16). Referenzen: Luca Seite und Gesicht, Ausbilderin v2, Zentrale; Dialogdatei als Audio-Referenz.
- Remotion `Schmitt-NeuerSpielstand` umgebaut:
  - Prop `shots` (Liste aus Clip und Videolänge) statt `shot1Src`.
  - Shot 1 landet weiter aus dem Zoom-through, alle weiteren Shots hängen per Schnitt an. Jeder Clip läuft bis zu seinem letzten Bild.
  - Die Gesamtlänge rechnet `schmittNeuerSpielstandMetadata` aus den Shots. `durationInSeconds` in den Render-Props ist nicht mehr nötig.
- Dispo-Fotos für Shot 3 gesichtet (Schmitt-121 bis 130):
  - Büro mit Headsets und Monitoren (122–124; 125 von hinten mit „Schmitt Gruppe“-Polo).
  - Anmeldung „Schmitt Spedition“ mit Glasscheibe (126–130).
  - Echte Mitarbeitende werden durch erfundene NPCs ersetzt.
- Takes Shot 2 (135 Credits, Stand 3.850,94) → `Ergebnisse/Shots/shot2_A_take1–3.mp4`, Kopien in `Material/Video/shots/`:
  - Ablauf in allen drei: Luca geht auf die Ausbilderin zu. Sie dreht sich mit dem Tablet um, tippt und zeigt zur Tür. Die Kamera fährt seitlich herum, bis beide im Profil stehen.
  - Scribe mit Sprechertrennung: Alle drei enthalten beide Sätze und zwei Sprecher.
    - Take 1: Ausbilderin 0,90–3,42 s („Hol i dir“, etwas verschluckt), Luca 4,24–4,76 s.
    - Take 2: 1,52–3,80 s und 4,26–4,80 s.
    - Take 3: 1,28–3,44 s und 4,04–4,58 s.
  - Take 3 verworfen: Die Kamera kreist über die Achse, am Ende ist Luca nicht mehr im Bild.
  - Lippen-Check Take 1: Beide Figuren sind groß im Profil. Mund offen bei „Dispo“, „Bin“ und „dabei“, geschlossen vor Lucas Antwort.
  - Lippen-Check Take 2: passt ebenfalls, aber bei „Hol ihn dir“ dreht sie sich weg, und am Anfang wird länger gelaufen.
  - **Take 1 gewählt (Claude):** schnelleres Tempo, die Lippen beider Figuren sind gut sichtbar.
- Preview Shot 0–2: `Ergebnisse/Renders/Preview_Shot0-2_A_s2take1.mp4` (13,4 s, 1080×1920, H.264, ohne Musik), an den User geschickt. Die Alternative mit Take 2 liegt daneben (`…_s2take2.mp4`).
  - Pegel: Mittel −21,4 dB, Spitze −1,1 dB.
  - Schnitt Shot 1 → 2 geprüft: letztes und erstes Bild praktisch gleich, kein Sprung.
  - Standardwerte der Komposition: Shot 1 Take 3 + Shot 2 Take 1.
- Render-Befehl ab jetzt: `--props='{"shots":[{"src":"shots/shot1_A_take3.mp4","seconds":5.04},{"src":"shots/shot2_A_take1.mp4","seconds":5.04}]}'`

**Offen**
- Feedback des Users zu Shot 2, danach Shot 3 (Dispo: Innenraum-Vorlage aus Schmitt-122 bis 130, NPCs statt echter Mitarbeitender, Disponent „Gute Fahrt!“).
- Einblendungen (Quest „Hol dir deinen Schlüssel“, Zielmarker Dispo) in der Animationsphase.
- Song „Inner Light“ als Audiodatei.
- Spitzenpegel −1,1 dB in der Preview → beim Mischen in Resolve normalisieren.

## 2026-09-11 — Shot 2 neu: reinlaufen, Ladescreen, Schlüsselszene

**Feedback (User):** „Ne die sollen nicht mehr stehenbleiben draußen, sie sollen reinlaufen und währenddessen sprechen dann kommt ein ladescreen und dann die schlüsselszene“

- **Shot 2 neu:** Die Version, in der beide draußen im Profil stehen (Take 1), ist verworfen.
  - Neuer Ablauf: Die Ausbilderin öffnet die Glastür und geht hinein, Luca folgt. Der Dialog läuft im Gehen, sie spricht über die Schulter.
  - Drei Takes Seedance 2.0 mit 6 s, Startbild und Dialogdatei wie zuvor → `Ergebnisse/Shots/shot2_B_take1–3.mp4`.
- **Ladescreen neu** zwischen Shot 2 und 3 (Remotion):
  - Artwork im Look A mit langsamem Zoom, Text „Neue Quest · Hol dir deinen Schlüssel · Ziel: Dispo“, Fortschrittsbalken und Lade-Kreis in Schmitt-Gelb.
  - Zwei Artwork-Varianten (Schlüsselbrett, Luca auf dem Hof) → `Ergebnisse/Ladescreen/`.
- **Shot 3 vorbereitet:**
  - Dispo-Vorlage im Look A aus Schmitt-122 und Schmitt-121, ohne Personen, mit Schlüsselbrett → `Ergebnisse/Orte/A/ort_A_dispo_v1/v2`.
  - Die Disponentin ist die NPC-Karte aus dem Startscreen. Stimme „Gute Fahrt!“: Nora und Vera je 2 Takes, alle korrekt. **Vera v1 gewählt** (1,04 s, Sprache 0,10–0,84 s) → `Material/Video/audio/shot3_disponentin.mp3`.
- **Takes Shot 2 neu** (6 s; laut Kontostand je ≈ 74 Credits):
  - Take 1: Die Ausbilderin steht lange in der Tür, der Dialog beginnt erst bei 2,7 s.
  - Take 2: Scribe hört „Hau ihn dir“ statt „Hol ihn dir“ → verworfen.
  - **Take 3 gewählt:** Sie öffnet die Tür, schaut beim Hineingehen über die Schulter und spricht (2,46–4,54 s). Luca antwortet im Foyer (4,84–5,38 s). Die Lippen passen bei „Dispo“, „Hol“ und „dir“. Clip: 145 Bilder = 6,04 s.
- **Ladescreen gebaut** (Remotion, Segment `kind: "ladescreen"`, 2,4 s):
  - Motiv `ladescreen_A_luca` → `Material/Video/ladescreen/ladescreen_luca.jpg`. Das Schlüsselbrett-Motiv fiel raus, weil der Schlüssel unter dem Quest-Text läge.
  - Der Textblock wächst von der Safe-Zone-Unterkante (y 1090) nach oben: „Neue Quest“, „Hol dir deinen Schlüssel“, Ziel-Pin „Ziel: Dispo“. Fortschrittsbalken und „Lädt“-Kreis stehen in einer Zeile.
  - Hinter dem Text liegt eine weiche Abdunklung, weil der gelbe Kicker über dem hellen Himmel unlesbar war.
  - Übergänge: Der Clip davor blendet in 0,25 s auf Schwarz (Bild und Ton), der Ladescreen blendet 0,3 s ein und aus, der Clip danach blendet von Schwarz ein.
- **Shot 3 Startbilder** (GPT Image 2 aus Luca hinten, Disponentin-Karte, Dispo v1):
  - v1 mit ganzem Schlüsselbrett und Kollege am Drucker.
  - v2 mit größerer Disponentin.
  - Drei Takes gestartet: Take 1 und 2 aus v2, Take 3 aus v1; Audio-Referenz „Gute Fahrt!“.
- **Takes Shot 3** (135 Credits, Stand 3.452,76) → `Ergebnisse/Shots/shot3_A_take1–3.mp4`, Kopien in `Material/Video/shots/`:
  - Take 1 und 2 (aus v2) schneiden trotz „no cuts“ auf eine Nahaufnahme der Disponentin. Im Fenster hinter ihr sind Sonnenuntergang und Hochhaus-Skyline zu sehen, das passt nicht zur Dispo. In Take 2 hält außerdem die Disponentin den Schlüssel. → verworfen.
  - **Take 3 gewählt** (aus v1): durchgehende Verfolgerkamera. Luca nimmt den Schlüssel vom Brett, hebt ihn kurz und geht weiter. Die Disponentin sitzt am Platz, schaut zu ihm und sagt „Gute Fahrt“ (Scribe 3,76–4,44 s). Ihr Mund ist bei „Gute“ und „Fahrt“ geöffnet.
- Standardwerte der Komposition: Shot 1 Take 3, Shot 2 B Take 3, Ladescreen, Shot 3 Take 3 (546 Bilder = 21,84 s).
- Preview `Ergebnisse/Renders/Preview_Shot0-3_Ladescreen.mp4` (21,9 s, 1080×1920, H.264, ohne Musik), an den User geschickt.
  - Pegel: Mittel −22,8 dB, Spitze −1,4 dB.
  - Übergänge geprüft: Shot 1 → 2 ohne Sprung. Shot 2 blendet im Foyer auf Schwarz, der Ladescreen blendet ein und aus, Shot 3 blendet von Schwarz ein.
- Rendern ab jetzt ohne Props (Standardwerte) oder mit `shots` samt `kind` je Segment.
- Verbrauch dieser Runde (seit 3.850,94): 398,18 Credits, Stand 3.452,76. Die 6-s-Takes von Shot 2 haben laut Kontostand je ≈ 74 Credits gekostet, nicht 54 wie im Kostenrechner (dort ohne Referenzen gerechnet).

**Offen**
- Feedback des Users zu Shot 2 neu, Ladescreen und Shot 3.
- Danach Shot 4: raus auf den Hof und Einsteigen mit Kamerazug in die Fahrzeugkamera.
- Song „Inner Light“ als Audiodatei; Pegel beim Mischen in Resolve normalisieren.

## 2026-09-11 — Feedback Shot 0–3, weiter mit Shot 4

**Feedback (User):** „okay nice so passt es schon sehr gut, nur beim letzen shot ganz am ende müssen wir paar wenige frames rauslöschen da hier ein komischer cut zu sehen ist und die menschen im hintergrund verschwinden. Mach weiter dann“

- **Shot 3 gekürzt:**
  - Die Szenenwechsel-Analyse (ffmpeg `scene`) findet den Sprung bei Bild 108 (4,50 s, Wert 0,34; alle anderen Bilder unter 0,2). Ab dort steht die Kamera anders, und die Disponenten sind weg.
  - Shot 3 endet jetzt nach Bild 107 (`seconds: 4.53` = 113 Bilder bei 25 fps).
  - „Gute Fahrt“ endet bei 4,44 s und bleibt ganz drin.
- **Shot 4 „Einsteigen“ gestartet**, zwei Startbilder mit GPT Image 2:
  - Vorlage Schmitt-132: Actros mit Schmitt-Spedition-Logo, Hof mit Rampentoren.
  - Luca von hinten mit dem Schlüssel in der Hand. Die Staplerfahrerin (NPC-Karte) winkt vom Stapler, hinten rangiert ein LKW.
  - Kennzeichen neutral.
  - Geprüft: Das letzte Bild der Komposition entspricht Clip-Bild 107, der Sprung ist raus. Shot 0–3 dauern jetzt 21,32 s (533 Bilder).
  - **Startbild v2 gewählt** (`Ergebnisse/Keyframes/A/shot4_A_start_v2.png`): Der Actros steht näher, sodass Laufen und Einsteigen in 5 s passen. Fahrerseite sichtbar, Schmitt-Auflieger an Rampe 33 im Hintergrund, Staplerfahrerin winkt. v1 zeigt den LKW zu weit weg.
- Shot 4 in zwei verketteten Clips:
  - 4a: Luca geht zum LKW und steigt ein. Drei Takes Seedance 2.0 (5 s) aus Startbild v2; Referenzen Luca hinten und Seite, Staplerfahrerin-Karte, Schmitt-132.
  - 4b: Kamerazug hinter den LKW, der LKW fährt an. Startbild wird das letzte Bild von 4a. Zwei Zielbilder in Fahrzeugkamera-Perspektive (GPT Image 2) zur Auswahl → `Ergebnisse/Keyframes/A/shot4b_A_ende_v1/v2`.
  - Zeitbudget im Blick behalten: Shot 0–3 haben 21,3 s. Shot 4 sollte zusammen höchstens etwa 7 s lang sein, sonst reißt das 45-s-Ziel.
  - Zielbilder 4b v1/v2 unbrauchbar: Palmen, Sonnenuntergang über Los Santos und Hochhaus-Skyline im Hintergrund. Ursache: GTA-Straßenszene als Stilvorlage und keine Ortsangabe für die Ansicht, die das Startbild nicht zeigt.
  - Neu als v3/v4: ausdrücklich deutsches Gewerbegebiet in Hohenlohe, keine Palmen, keine Skyline; Zentrale im Look A als zweite Ortsreferenz, ohne GTA-Straßenvorlage.
- **Takes Shot 4a** (135 Credits; Stand 3.278,76 inkl. Zielbilder v1/v2) → `Ergebnisse/Shots/shot4a_A_take1–3.mp4`, Kopien in `Material/Video/shots/`:
  - Take 1: harter Schnitt bei Bild 85 (Szenenwert 0,27), vom Weg über den Hof direkt an die offene Tür → verworfen.
  - Take 2: durchgehend (höchster Wert 0,13). Luca öffnet die Tür, steigt ein und sitzt am Steuer.
  - **Take 3 gewählt:** am ruhigsten (höchster Wert 0,07). Luca läuft über den Hof, am Anfang ist die Staplerfahrerin zu sehen. Er öffnet die Fahrertür und steigt ein. Im letzten Bild sitzt er im Profil am Lenkrad hinter der geschlossenen Tür mit Schmitt-Logo.
  - Kleiner Makel in Take 2 und 3: Die Kleinschrift auf der Tür unter dem Logo ist Fantasietext, nur aus der Nähe lesbar.
  - Letztes Bild von Take 3 → `Ergebnisse/Keyframes/A/shot4a_A_take3_letztes_bild.png`, Startbild für 4b.
- **Zielbilder 4b v3/v4 brauchbar:**
  - Beide: Verfolgerkamera schräg von oben hinter dem Schmitt-LKW, Rampen 32/33 links, Hoftor, grüne Hügel und Laubbäume, keine Palmen.
  - v4 zeigt den LKW mittig; im Hintergrund weht eine rot-weiße Fahne (kleiner Makel). v3 zeigt den LKW schräg links.
  - Unterschied zum Startbild: Dort steht ein Motorwagen mit Kofferaufbau, die Zielbilder zeigen eher einen Sattelzug. Risiko: Der LKW verformt sich im Kamerazug.
- **Shot 4b, drei Takes mit verschiedenen Ansätzen:** Startbild ist immer das letzte Bild von 4a.
  - Take 1: Zielbild v4.
  - Take 2: Zielbild v3.
  - Take 3: ohne Zielbild, nur Prompt.
  - Referenzen: Startbild Shot 4, Schmitt-132, Zentrale.
- **Takes Shot 4b** (135 Credits, Stand 3.143,76) → `Ergebnisse/Shots/shot4b_A_take1–3.mp4`, Kopien in `Material/Video/shots/`:
  - Take 1 (Zielbild v4): Die Kamera schwenkt schnell von der Tür vor den LKW, dann zur Seite und nach hinten (höchster Szenenwert 0,11). Wirkt hektisch.
  - **Take 2 gewählt** (Zielbild v3): ruhigste Fahrt (höchster Wert 0,05). Die Kamera zieht von der Tür zurück, gleitet tief an der Seite entlang, hinter den LKW und steigt in die Verfolgerkamera. Der LKW fährt Richtung Tor, Rampen 32/33 links, grüne Hügel.
  - Take 3 (ohne Zielbild): wieder Palmen und kahle Hügel im Hintergrund → verworfen. Ohne deutsches Zielbild driftet also auch Seedance nach Los Santos.
- Standardwerte der Komposition um Shot 4a Take 3 und 4b Take 2 ergänzt (785 Bilder = 31,4 s).
- Preview `Ergebnisse/Renders/Preview_Shot0-4.mp4` (31,4 s, 61 MB) und Review-Kopie `Preview_Shot0-4_klein.mp4` (24 MB, an den User geschickt).
  - Pegel: Mittel −22,4 dB, Spitze −1,0 dB.
  - Schnitte geprüft: Shot 3 → 4a ist ein gewollter Ortswechsel (Dispo → Hof). Shot 4a → 4b: letztes und erstes Bild gleich, kein Sprung.
- Verbrauch dieser Runde (seit 3.452,76): 309 Credits (4a 135, 4b 135, Startbilder 13, Zielbilder 26), Stand 3.143,76.

**Offen**
- Feedback des Users zu Shot 4.
- **Zeitbudget:** Shot 0–4 haben 31,4 s. Laut Script kämen noch ~20 s dazu (Tour 8, Rampe 5, Lager 3, Erledigt 4) → ~51 s statt höchstens 45 s. Vorschlag an den User:
  - Ladescreen 1,6 s statt 2,4 s.
  - Shot 4a erst ab ~1,5 s zeigen (Anfang des Laufwegs; Shot 3 → 4a ist ohnehin ein Schnitt; braucht einen Startversatz in der Komposition).
  - Shot 4b bei ~4,2 s enden lassen.
  - Shot 5 „Auf Tour“ 5 s statt 8 s.
- Danach Shot 5 „Auf Tour“.
- Song „Inner Light“ als Audiodatei.

## 2026-09-11 — Neuer Schluss statt Shot 5–8

**Entscheidung (User):** „Ne ich glaube wir machen jetzt einfach einen passenden abschlussshot statt wie geplant den rest zu machen. Jetzt soll er einfach auf ne straße fahren und dann geht die kamera hoch und man sieht das gebäude dann kommt ein animierter CTA für Berufskraftfahrer“

- Shots 5–8 aus Script V1 (Tour, Rampe, Lager, Erledigt) entfallen. Damit ist das Zeitbudget kein Problem mehr, der Kürzungsvorschlag ist hinfällig.
- **Shot 5 (Schluss):**
  - Start = letztes Bild von 4b (`Ergebnisse/Keyframes/A/shot4b_A_take2_letztes_bild.png`). Der LKW fährt vom Hof auf die Straße, die Kamera steigt hoch und zeigt das Gebäude.
  - Zielbild im Look A nach dem Drohnenflug DJI_0373 (Standbild und Seedance-2.5-Look-Frames aus dem Look-Test) mit dem Logo „schmitt Logistik“ an der Fassade. Zwei Varianten → `Ergebnisse/Keyframes/A/shot5_A_ende_v1/v2`.
- **CTA in Remotion** (neues Segment `kind: "cta"`):
  - Kicker „Dein Spielstand wartet“ (aus Script V1), Titel „Berufskraftfahrer“ mit „(m/w/d)“.
  - Drei Benefits wörtlich laut schmitt.jobs (Stand 11.09., siehe Website-Liste oben): „30 Tage Urlaub“, „Job Rad“, „Werkswohnung“.
  - Button „A · Jetzt bewerben“ wie „A Spiel starten“ im Startscreen, darunter „schmitt.jobs“.
  - Hintergrund ist das eingefrorene letzte Bild des Schluss-Shots, abgedunkelt.
- **CTA gebaut** (`Cta` in `tools/motion/src/clients/schmitt/projects/neuer-spielstand/Composition.tsx`, Schema-Felder `perks`, `button`, `url`):
  - Ablauf 4,5 s: Abdunklung 0,6 s, Kicker ab 0,15 s, Titel ab 0,3 s, Benefits nacheinander ab 0,9 s mit gelbem Haken, Button ab 1,7 s, „Drücken“ bei 2,6 s mit Bestätigungs-Klick.
  - Layout-Test mit Platzhalter-Hintergrund (`Material/Video/cta/cta_test_bg.jpg`, aus Zielbild 4b v3): Alle Texte liegen in der Safe Zone (Titel ab y 170, Button 930–1026, Adresse bis 1092), „Berufskraftfahrer“ passt in eine Zeile. Die Abdunklung ist noch recht kräftig; sie wird am echten Schlussbild nachgestellt, damit das Gebäude mit Logo sichtbar bleibt.
  - Typprüfung ohne Fehler.
- **Zielbilder Schluss-Shot** (13 Credits, Stand 3.130,76):
  - Beide zeigen das Schmitt-Logistik-Gelände schräg von oben mit Logo an der Fassade, Hof mit Aufliegern, Städtchen und Hügeln. Der blaue Schmitt-LKW fährt auf der Straße im Vordergrund. Keine Palmen.
  - **v2 gewählt** (`Ergebnisse/Keyframes/A/shot5_A_ende_v2.png`): Logo größer und gut lesbar (etwa auf 38 % der Bildhöhe), LKW deutlicher.
- **Schluss-Shot:** drei Takes Seedance 2.0 (5 s) gestartet.
  - Start = letztes Bild 4b, Ziel = Luftbild v2.
  - Referenzen: Look-Frame DJI_0373 (t6.0), Startbild Shot 4, Schmitt-132.
  - Die letzten Bilder der Takes werden als CTA-Hintergrund gesichert.
- **Takes Schluss-Shot** (135 Credits, Stand 2.995,76) → `Ergebnisse/Shots/shot5_A_take1–3.mp4`, Kopien in `Material/Video/shots/`:
  - Take 2 beginnt nicht mit dem Startbild, sondern mit der Frontansicht aus dem Startbild von Shot 4 (einem Referenzbild). Dazu kommt ein harter Schnitt bei Bild 48 (Wert 0,29) → verworfen.
  - Take 3: harter Schnitt bei Bild 43 (0,22), vom Hof direkt auf die Straße vor dem Gebäude → verworfen.
  - **Take 1 gewählt:** durchgehend (höchster Wert 0,07). Der LKW fährt vom Hof, die Kamera steigt, folgt ihm auf die Straße ins Abendlicht und schwenkt auf das Schmitt-Logistik-Gebäude mit Logo. Das Ende liegt nah am Luftbild v2.
  - Letztes Bild → `Material/Video/cta/cta_bg.jpg` als CTA-Hintergrund. Die Test-Hintergründe sind gelöscht.
- CTA-Abdunklung am Luftbild nachgestellt: oben dunkel für Titel und Benefits, in der Mitte (32–49 % der Höhe) fast frei für Gebäude und Logo, unten dunkel für Button und Adresse.
- Komposition komplett: Startscreen, Shot 1, Shot 2, Ladescreen, Shot 3, Shot 4a, Shot 4b, Schluss-Shot, CTA = 1023 Bilder = 40,9 s.
- **Komplett-Preview V1:** `Ergebnisse/Renders/Preview_Komplett_V1.mp4` (41,0 s, 82 MB) und Review-Kopie `Preview_Komplett_V1_klein.mp4` (24 MB, an den User geschickt).
  - Pegel: Mittel −21,4 dB, Spitze −1,0 dB.
  - Schnitte geprüft: 4b → Schluss-Shot und Schluss-Shot → CTA laufen jeweils ohne Sprung (letztes und erstes Bild gleich).
- Verbrauch für den neuen Schluss: 148 Credits (Zielbilder 13, Takes 135), Stand 2.995,76.

**Offen**
- Feedback des Users zur Komplett-Preview.
- Song „Inner Light“ als Audiodatei (Sync-Lizenz klären) oder Alternative aus Artlist/Envato. Sounddesign und Pegel in Resolve (Spitze aktuell −1,0 dB).
- Schreibweise „Job Rad“ ist von schmitt.jobs übernommen; ggf. mit Schmitt klären, die Marke heißt „JobRad“.
- Beim Posten KI-Kennzeichnung (AI Act Art. 50); kein „GTA“ in Video und Post.

## 2026-09-11 — Fertigstellung V2: Musik, Schlussszene, Motion Design, Sound, Logo

**Wünsche (User):**
- Musik am Ende entfernen.
- Den „GTA-Song“ selbst von YouTube laden und so anlegen, dass der Drop kommt, sobald der LKW losfährt.
- Neue finale Szene: Fahrer im Innenraum während der Fahrt, schaut auf die Straße und dreht sich dann in die Kamera: „Worauf wartest du, bewirb dich jetzt“.
- Alle Motion-Design-Elemente einbauen und das Video fertigstellen; noch nichts in DaVinci.
- SFX über Remotion (ElevenLabs), nicht abgehackt und passend.
- Am Ende das Schmitt-Logo.

**Umsetzung und Entscheidungen**
- **Song:** Nicht von YouTube geladen. „Inner Light“ ist ein geschützter Warner-Titel; YouTube-Rippen verstößt gegen Nutzungsbedingungen und Urheberrecht.
  - Keine legale Kopie gefunden (Spotlight, ~/Music, NAS).
  - Musikspur in Remotion vorbereitet: `MUSIC` in `timeline.ts` legt den Drop automatisch auf das Anfahren (Shot 4b + 1,25 s) und senkt die Musik unter Dialog ab. Es fehlen nur die Datei und die Drop-Sekunde im Song.
- **Musik in den Clips entfernt:** Der Seedance-Clip-Ton ist komplett stumm (`clipAudio: false`).
  - Der Dialog kommt aus den sauberen TTS-Dateien, gelegt auf die Scribe-Wortzeiten der Clips (Abweichung ≤ 80 ms).
  - Versätze: Shot 1 +0,04 s, Shot 2 Helena +2,33 s und Jasper +4,72 s, Shot 3 +3,66 s, Shot 6 +2,44 s.
- **ElevenLabs-API:** Der Schlüssel hat keine Rechte für Soundeffekte (`sound_generation`) und Stimm-Isolierung (`audio_isolation`).
  - Geräusche stattdessen mit Mirelo Text-to-Audio über Higgsfield (1 Credit je Geräusch): 20 Geräusche, dazu 2 neu (ui_confirm und ui_whoosh_in waren fast stumm) → `Material/Video/sfx/`.
  - Normalisiert in `sfx/norm/`: Einmal-Geräusche auf −1 dB Spitze, Atmos auf −23 LUFS, jeweils mit 6–20-ms-Rampen.
  - Dialog auf −3 dB Spitze → `Material/Video/audio/dialog/`.
- **Schlussszene (Shot 6):**
  - Startbild mit GPT Image 2 (v1: Fahrerkabine, Luca im Profil am Lenkrad, draußen Hohenlohe).
  - Stimme Jasper „Worauf wartest du? Bewirb dich jetzt!“ (v1 von 3).
  - Drei Takes Seedance 2.0: Take 1 und 2 zeigen gegen Ende eine Palme vor dem Fenster. **Take 3 gewählt** (Satz 2,50–4,76 s, Lippen passen, keine Palme).
- **Motion Design** (neu, `hud.tsx`):
  - Minimap oben rechts in Shot 1–2, 3 und 4a–4b; beim Anfahren zeichnet sich die Route.
  - Hinweis-Karten oben links: „Standort · Schmitt Gruppe · Vellberg“, „Neues Item · LKW-Schlüssel erhalten“, „Ziel · Steig in deinen LKW“, „Neue Route · Route zum Ziel“.
  - Untertitel im Game-Stil für alle Dialoge (Plan `_intern/cinematic-caption-plan.json`).
  - Logo-Karte am Ende.
- **Logo:** Offizielle SVGs auf schmitt-vellberg.de gefunden (`logo_gruppe_weiss.svg`, `logo_gruppe.svg`). Der Download braucht die Freigabe des Users → vorerst Wortmarken-Platzhalter „Schmitt Gruppe“.
- **Timing (`timeline.ts`):** Ladescreen 2,0 s, Shot 4a ab 1,0 s (Anlauf gekürzt), Shot 5 4,2 s, Shot 6 4,96 s, CTA 3,8 s, Logo 2,0 s → 1124 Bilder = 44,96 s.
- **Komposition umgebaut:** Segmente mit `id`; Ton, Untertitel, HUD und Musik als Daten; `trimStart`; Logo-Segment; gemeinsame Bausteine in `shared.ts`.
- **Verbrauch dieser Runde:** 166,25 Credits (Startbilder Shot 6 13, Takes 135, Geräusche 22 u. a.), Stand 2.829,51.
- **Prüfung V2:**
  - Kontaktbogen über alle Szenen: HUD, Untertitel, Ladescreen, CTA und Logo-Karte sitzen in der Safe Zone.
  - Die „Standort“-Karte hat in Shot 1 den Schmitt-Schriftzug an der Fassade angeschnitten → alle Hinweis-Karten 106 px tiefer gesetzt, geprüft.
- **Lautheit:** Remotion-Mischung −22,9 LUFS (Spitze −4,4 dBFS) → ffmpeg-loudnorm (zwei Durchläufe, dynamisch) auf −15,3 LUFS, True Peak −1,5 dBFS, LRA 7,8 LU.
- **Geliefert:**
  - `Ergebnisse/Renders/Preview_Komplett_V2.mp4` (Remotion, unnormalisiert).
  - `Preview_Komplett_V2_normalisiert.mp4` (Master, 82 MB).
  - `Preview_Komplett_V2_klein.mp4` (21 MB, an den User geschickt).

**Offen**
- Freigabe des Users, das offizielle Logo `logo_gruppe_weiss.svg` von schmitt-vellberg.de zu laden (danach `src` im Logo-Segment setzen, neu rendern).
- Legal beschaffte Datei von „Inner Light“ (oder Alternative aus Artlist/Envato) → `MUSIC.src` und `dropInSong` setzen; der Drop landet dann automatisch auf dem Anfahren.
- Feedback des Users zu V2 (Sounddesign, HUD, Schlussszene).
- Rechte im ElevenLabs-Konto, falls SFX künftig direkt über ElevenLabs laufen sollen.
