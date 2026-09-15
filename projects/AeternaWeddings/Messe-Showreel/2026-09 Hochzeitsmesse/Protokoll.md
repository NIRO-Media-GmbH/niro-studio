# Protokoll — AeternaWeddings / Messe-Showreel / 2026-09 Hochzeitsmesse

## 2026-09-11 — Projekt angelegt

**Gemacht**
- Ordner angelegt: `Material/CI`, `Material/Video`, `Ergebnisse/Renders`, `_intern`.
- Website https://aeterna-weddings.de/ gesichtet (Marke von NIRO Media GmbH, Hochzeitsfilm + Reels + optional Foto, EU-weit).

**Auftrag**
- Hochzeits-Showreel für eine Hochzeitsmesse, großer 16:9-Bildschirm, Dauerschleife.
- Geschnittenes Video (~5 min) links groß eingebettet, rechte Fläche mit animierten Infografiken.

**Website-belegte Inhalte (nur diese dürfen ohne Freigabe rein)**
- Claims: „Liebe, die man sieht. Momente, die man fühlt.“ · „Euer Tag. Eure Erinnerungen. Für immer spürbar.“ · „Aeterna Experience“ (klar, planbar, entspannt)
- Versprechen: 100 % pünktliche Lieferquote · redundante Datensicherung 12 Monate · Sneak Peek in 48–72 h · ein fester Ansprechpartner
- Leistungen: Story-driven Cinematic Film · Social-Media-Reels · optional Fotografie · Destination-Hochzeiten auf Anfrage
- Keine Preise, kein Instagram/E-Mail/Telefon auf der Seite; Buchung über HubSpot-Terminlink (David Niemann)

**Offen**
- Bildschirm-Specs, Abspielweg, Ton, Messe-Termin
- Geschnittenes Showreel (Master) → `Material/Video/`
- Info-Inhalte rechts + QR-Ziel festlegen

## 2026-09-11 — CI gesichtet, Layout-Richtung

**CI** (Kundenebene `projects/AeternaWeddings/CI/Aeterna/`)
- Logo „Aeterna“ als Schreibschrift (SVG/AI/PDF), Wortmarke + Monogramm „A“, jeweils in Gold/Anthrazit/Elfenbein
- Farben (Logo-SVG + Website-CSS): Gold `#C1A67A` · Schwarz `#000000` · Dunkelbraun `#3B352F` · Elfenbein `#FCFBF8` · Weiß
- Schriften der Website: Playfair Display (Headlines) · Red Hat Text 400/600 (Fließtext) · Great Vibes (Script-Akzente, liegt als TTF in der CI)

**Zusatzinhalte der Website** (voller Text gelesen): „Was euch nicht passiert“ (4 Punkte), 6 USPs, 6-Schritte-Ablauf (Kennenlernen 15–20 Min., Sneak Peek 48–72 h, erste Reels in 24 h, Hauptstück in 4K), Collections „Aeterna + Atelier“ (Foto) und „Aeterna Legacy“ (Interviews), Anfrage ideal 6–12 Monate vorher
- **Widerspruch auf der Website:** Stat-Leiste sagt „Weltweite Verfügbarkeit“, FAQ sagt „EU-weit. Destination-Feiern auf Anfrage.“ → vor Verwendung klären

**Entscheidungen**
- Video noch nicht geschnitten → Aufbau mit Platzhalter, Länge aus der Datei gelesen, sobald der Schnitt da ist
- Layout-Entwurf: Video 1280×720 links (2/3 Breite), rechts Info-Kapitel, QR + CTA dauerhaft sichtbar; zwei Looks (Nacht/Elfenbein) zur Wahl gestellt
- **User wählt Look B „Elfenbein“** (Grund Elfenbein `#FCFBF8`, Text Dunkelbraun `#3B352F`, Akzent Gold)
- Aeterna ist neu gegründet, Inhalte stehen noch nicht final → Recherche beauftragt: was andere Hochzeitsdienstleister auf Messe-Screens zeigen + Messe-Display-Regeln
- Recherche fertig → `_intern/recherche-messe-screen.md` (Quellen). Folgen fürs Konzept: Kapitel 8–12 s statt 25 s (Zyklus 75 s × 4 = 5:00), Text ≤ 15 Wörter/Kapitel, Fließtext ≥ 48 px → Video-Fenster eher ~1120×630 statt 1280×720, QR dauerhaft ~240 px dunkelbraun, LCD statt OLED, Reue-Statistiken nicht verwenden
- **User-Entscheidungen Zusatz-Inhalte:**
  - Verfügbarkeit: **deutschlandweit** (Website sagt noch EU-weit/weltweit)
  - „Warum Film“: ja
  - Messe-Bonus: ja, **Extra-Reel** bei Buchung innerhalb von 14 Tagen nach der Messe
  - Verlosung: nein · Preise: **generell nicht zeigen** · Instagram: nein · Kundenstimmen: keine vorhanden
  - Team: erwähnen, aber nicht zeigen (keine Porträts)
  - Terminlage: allgemein halten („2027 noch Termine frei“)
- Kapitelplan-Entwurf (8 Kapitel à 12,5 s = 100-s-Zyklus × 3 = 5:00) vorgelegt
- **Technik (User):** 75" LG LCD, Abspielen per USB-Stick in 4K; Showreel gedreht in 25p, Animationen in 50p gewünscht
  - LG webOS-Spezifikation (webostv.developer.lge.com, webOS TV 25): H.264 in 4K nur bis 30p/50 Mbps → **4K50 muss HEVC sein** (Main/Main10 @ L5.1, max. 60 Mbps, MP4)
  - 25p-Video in 50p-Timeline = jedes Bild exakt verdoppelt, kein Ruckeln
- Offen: Betrachtungsabstand, Messe-Name/-Datum, QR-Ziel
- **Render-Weg (User): alles in Remotion.** Kapitelplan abgenommen. **Design abgenommen** → `_intern/design-spec.md`

## 2026-09-11 — Resolve: Szenen-Erkennung Showreel-Quelle

**Gemacht**
- Resolve-Projekt „Messe Showreel“ (21.1.0.14, lokal geöffnet): Timeline 1 = 1920×1080 @ 25 fps, ein Clip „Lea & Sebastian Hochzeit_V3.mp4“ (3840×2160, HEVC Main 10, 25p, 21:23:05, ~80 Mbps, 12,8 GB, NAS `/Volumes/personal_folder/Jan/JS/Lea Hochzeit/`), Audiospur leer
- **Freigabe User:** Schreiben erlaubt in „Messe Showreel“, ausdrücklich **direkt in Timeline 1** (Ausnahme von „nur anhängen“)
- `Timeline.DetectSceneCuts()` per externem Skript (AutoCut-venv, kein 60-s-Limit): Analyse 76 s, Readback nach 107 s
- **Ergebnis:** 1 → **323 Shots** (322 Schnitte), keine Lücken, Abdeckung unverändert 01:00:00:00–01:21:23:03; Shot-Dauer min. 3 / Median 68 / max. 2644 Frames
- Schnittliste: `_intern/cut-detection/timeline1-scene-cuts.json` (Skript `detect_scene_cuts.py` lag im Session-Scratchpad)
- Prüfstellen T1: Häufung kurzer Shots 01:09:21–01:09:41 (10 Shots < 1 s, darunter 3-Frame-Shots); lange Shots 166 ab 01:09:41:21 (105,8 s) und 268 ab 01:17:00:17 (38,2 s) → evtl. unerkannte Überblendungen
- **Timeline 2** (User: „dasselbe für Timeline 2“, direkt): Clip „Video_V4.mp4“ (3840×2160, H.264 High, 25p, 23:38:19, ~80 Mbps, 14,2 GB, AAC stereo, `/Volumes/personal_folder/Jan/JS/`)
  - Analyse 123 s → **468 Shots**, keine Lücken, Abdeckung unverändert 01:00:00:00–01:23:38:18; Shot-Dauer min. 1 / Median 55,5 / max. 1500 Frames
  - **Auffällig:** 154 Shots < 1 s, davon 107 ≤ 10 Frames, gehäuft im letzten Drittel: 01:19:46–01:20:22 (63), 01:20:54–01:21:28 (27), 01:21:45–01:22:04 (16), 01:22:48–01:23:08 (17), 01:23:34–01:23:38 (11) → vermutlich Fehlschnitte durch Lichtwechsel/Blitze (Party?) oder schnelle Montage — sichten
  - Schnittliste: `_intern/cut-detection/timeline2-scene-cuts.json`
- Aktive Timeline des Users (Timeline 2) blieb aktiv; nichts außer den beiden Timelines verändert

## 2026-09-11 — Showreel 5:00: Analyse

**Entscheidungen (User):** erster Wurf + Tauschen per rote Marker · Tagesbogen 8 × 37,5 s · ohne Musik (Messe stumm) ·
Shots dürfen gekürzt werden → `_intern/showreel-schnitt-spec.md`

**Gemacht**
- Decode-Analyse beider Filme (5 fps, 960×540; Schärfe, Helligkeit, Clipping, Sättigung, Bewegung):
  T1 3:33 min, T2 ~6:50 min Rechenzeit → `_intern/showreel-analyse/t1|t2-samples.npy`, `-small.npy`
- **Befund Szenen-Erkennung:** Am Schnittpunkt verglichene Bilder täuschen (Überblendungen) → Vergleich ±1 s:
  T1 nur 5, T2 62 Fehlschnitte (Blitze/Club-Licht); zugleich übersieht Resolve Überblendungen (Segmente mit
  mehreren Einstellungen, z. B. Getting-Ready-Montage T1) → Fenster-Wächter: Randabstand 4 Frames bei harten,
  15 bei weichen Schnitten; keine Blende und kein Inhalts-Kippen im Fenster
- Segmente: T1 318, T2 406; technisch aussortiert (zu kurz/schwarz/weiß) 66 + 140 → **518 Kandidaten** auf
  87 Kontaktbögen → Bildanalyse (Kategorie, Einstellung, Wert 1–5, Flags, bester Frame) mit 4 Agenten gestartet
- **Test-Timeline (User-Wunsch, zufällige Clips):** Bin + „Claude Test Random 5min 2026-09-11 1545“ in „Messe Showreel“
  — 120 Clips aus dem Probeplan (Zufallsbewertung, aber echte Fenster-Wächter), 7500 Frames = 5:00, 3840×2160/25p,
  nur Video, Clipfarben, 8 blaue Block-Marker
  - Befunde: externes Skript scheiterte an frisch angelegter Timeline (SetSetting/AppendToTimeline → None) → Bau per
    MCP; `endFrame` exklusiv; Readback über `GetLeftOffset` (GetSourceStartFrame rundet teils −1)

## 2026-09-11 — Showreel 5:00: erster Wurf in Resolve

**Bildanalyse:** 518 Segmente (4 Agenten, Rubrik `_intern/showreel-analyse/vision/RUBRIC.md`) → Katalog ohne Wert ≤ 2,
Text/Grafik/Übergang/SW-Effekt/Unschärfe → Sequenz nach Tagesbogen-Vorlage (`showreel-schnitt-spec.md`)

**Nachgeschärft nach Sichtung der Prüfbögen (Anfangs-/Endbild je Shot):**
- Farbblitz-Wächter (Light-Leak t1-161; Grenze 25, Party 60), dunkle Szenen strengere Kontinuität
- Szenen-Deckel ±12 s (max. 2 im Loop, 1 pro Block, nie direkt hintereinander) + Motiv-Deckel Eröffnungstanz ≤ 4, Torte ≤ 2
  + Bildvergleichs-Sperre gegen Doppel-Motive (t2-035/t2-067 derselbe Kirchenkuss)
- Gesperrt: t2-155/t2-078/t2-082/t2-081 (Autokennzeichen), t1-250/t1-003 (Überblendung), t1-313 (Schnitt im Fenster)

**Geliefert (Resolve „Messe Showreel“, Freigabe dieser Session, nur angehängt):**
- Bin „Claude Showreel 2026-09-11 1559“
- **„Claude Showreel 5min 2026-09-11 1559“:** 120 Shots, 7500 Frames = 5:00, 3840×2160/25p, nur Video, harte Schnitte,
  Clipfarben je Kategorie, 8 blaue Block-Marker (Notiz = Slot-Kategorien); Readback 0 Abweichungen, 0 Lücken
  - Paare 58 (Lea & Sebastian) / 62 (Jessica & Dominik); Wert 5: 30 · 4: 54 · 3: 36
- **„Claude Showreel Reserve 2026-09-11 1559“:** 61 Ersatz-Shots nach Kategorie (11 blaue Marker), 3085 Frames
- Aktive Timeline des Users danach wieder aktiv; Plan `_intern/showreel-analyse/plan.json`, Katalog `katalog.json`,
  Skripte `scripts/`, Prüfbögen `pruefboegen/`

**Clipfarben:** Teal Location · Beige Details · Apricot Getting Ready · Yellow Trauung · Orange Trauung-Moment ·
Pink Emotion · Violet Paar · Lime Gratulation · Olive Reden/Dinner · Navy Abend · Purple Party

**Offen / bekannt schwach**
- Abend-Material knapp (4 Shots) → Slot 12 teils Tageslicht (Block 3/4) bzw. Party
- Block 5: LOVE-Buchstaben zweimal (Slot 3 + 8, letzte Lockerungsstufe)
- Tauschrunde: User setzt rote Marker in der 5min-Timeline → Claude tauscht aus Reserve/Katalog
- Einverständnis der Paare für öffentliche Messe-Nutzung prüfen

## 2026-09-11 — Showreel v2: 80 % Lea & Sebastian

**User:** „80 % nur die Hochzeit von Lea, diese Shots sind viel schöner geworden“

**Umbau der Sequenz** (`scripts/sequence_plan.py`, Plan `plan_v2_80-20.json`, Prüfbögen `pruefboegen/v2-80-20/`)
- Lea-Material reicht nicht für 96 Shots in 120 Slots (146 Lea-Shots ab Wert 3 im Katalog) → Vorlage auf **13 Slots je
  Block** (~2,9 s/Shot, ruhiger), 104 Slots gesamt
- Jessica & Dominik nur in kurzen Slots: ungerade Blöcke Details · 2. Paar-Slot · Party, gerade Blöcke Location · Party;
  harte Obergrenze 20, nie zwei hintereinander (auch nicht über die Loop-Naht)
- Slot-weise Verteilung über alle Blöcke (statt Block für Block) → kein Block verhungert; Auffüllen je Block, Lea zuerst
- Ersatz-Kategorien nur innerhalb der Tagesphase (Morgen/Trauung/Paar & Feier/Abend); Paarbilder nur in Paar-Slots;
  Szenen-Deckel Lea 3 / Jessica 2 je ±12 s; Eröffnungstanz max. 1 pro Block; Party-Schluss 1,5 s

**Geliefert (Resolve „Messe Showreel“, nur angehängt; v1 bleibt bestehen):**
- Bin „Claude Showreel v2 2026-09-11 1656“
- **„Claude Showreel 5min v2 80-20 2026-09-11 1656“:** 103 Shots, 7500 Frames = 5:00, 4K/25p, nur Video;
  **Lea 83 Shots / 79,9 % der Zeit**, Jessica 20; Readback 0 Abweichungen, 0 Lücken; 8 blaue Block-Marker
  (Notiz nennt Slots, Jessica-Shots markiert)
- **„Claude Showreel Reserve v2 2026-09-11 1656“:** 57 Shots nach Kategorie
- Aktive Timeline des Users danach wieder aktiv

**Bekannte Schwachstellen v2 (Kandidaten für rote Marker)**
- Block 5: Abend-Slot leer, Blockende mit Tagesbild (t1-041)
- Block 2: zwei Gäste-Emotionen direkt hintereinander (Slot 5+6)
- Block 7 Slot 12: Gast filmt mit Handy (t1-293); Kuss an der Treppe zweimal im Loop (Block 2 und 7)

## 2026-09-11 — Showreel v3: Schwachstellen getauscht

**User:** „ja passt, mach alle so“ → alle vier Schwachstellen aus v2 getauscht

**Vorgehen:** `sequence_plan.py --swap scripts/swap_v3.json` auf Basis von `plan_v2_80-20.json`, alle übrigen Shots
unverändert. Regelbasierter Tausch fand für 2 Slots nichts (Zeremonie im Film dicht, Doppel-Motiv-Sperre) → gezielte
Cutter-Wahl per Rangliste, nur mit Fenster-Wächtern; Blocklängen danach wieder exakt

| Block/Slot | raus | rein |
|---|---|---|
| B5 S11 (Abend, war leer) | – | t1-195 Paar im Gegenlicht an der Weide (W5) |
| B5 S13 | t1-041 Tagesbild | t1-292 Tanzfläche mit Ballons |
| B2 S6 | t1-061 zweite Gäste-Emotion | t1-058 Einzug Braut mit Vater ins Zelt |
| B7 S7 | t1-049 Treppenkuss (doppelt mit B2) | t1-050 Paarporträt an der Holztreppe |
| B7 S12 | t1-293 Gast filmt mit Handy | t1-272 Braut lacht mit Freundinnen |

**Geliefert (Resolve „Messe Showreel“, nur angehängt; v1/v2 bleiben bestehen):**
- Bin „Claude Showreel v3 2026-09-11 1706“
- **„Claude Showreel 5min v3 2026-09-11 1706“:** 104 Shots, 7500 Frames = 5:00, 4K/25p, nur Video; Lea 84 Shots /
  **80,0 % der Zeit**, Jessica 20; alle Blöcke 13 Shots; Readback 0 Abweichungen, 0 Lücken
- **„Claude Showreel Reserve v3 2026-09-11 1706“:** 57 Shots
- Plan `plan_v3.json`, Prüfbögen `pruefboegen/v3/`

**Offen:** Sichtung v3 durch User; aufräumen (Test-Timeline, v1, v2) nur auf Zuruf; danach Export des Showreels
(4K/25p Master) als Input für die Remotion-Komposition (Material/Video)

## 2026-09-11 — Showreel v4: User-Löschungen + Garten-Shooting

**User:** Shots versehentlich in v2 statt v3 gelöscht → prüfen, in v3 ersetzen; großer ungenutzter Teil (Garten-Shooting
Lea, weiche Blenden, keine Schnitte erkannt) nutzen

**Befund**
- v2: 49 von 103 Shots gelöscht (37 Lea, 12 Jessica; darunter 13× Wert 5), **46 davon in v3**; t1-048 gekürzt 100 → 85 Frames
  → `_intern/showreel-analyse/v2_user_loeschungen.json`, Bogen `pruefboegen/v4/geloescht_v2.png`
- Muster (Tendenz): Gäste im Fokus, warme dunkle Glashaus-Szenen (4× Eröffnungstanz, Reden), Essen/Deko, Drohnen, Club-Shots Jessica
- Garten-Shooting steckt in Segment t1-163 (01:09:41–01:11:27, 106 s, von Resolve nicht geschnitten, Bildanalyse als ein
  Segment „Szenenwechsel“ → nie verwendet)

**Gemacht**
- Montage-Segmente mit weichen Blenden zerlegt (Stabilitätsprüfung ±0,4 s; Garten toleranter 0,55): t1-163 → 25 Einstellungen
  (17 nutzbar), dazu t1-053/002/003/079/029/250 → `segments_sub.json`; 29 Einstellungen selbst bewertet
  (`vision/zerlegt/`) — 5× Wert 5 aus dem Garten (Terrasse/Rosen, Pergola-Porträt, Brunnen-Gang, Jubel am Brunnen) + Brautvater im Wald
- Sequenz-Skript: zerlegte Einstellungen im Katalog, User-Löschungen gesperrt + Abzug für gleichen Moment/ähnliches Bild,
  User-Kürzung fixiert, kurze Paar-/Abend-Einstellungen erlaubt, gleichmäßiger Längenausgleich (Lea zuerst)
- `--swap scripts/swap_v4.json` auf Basis v3: 45 von 46 Slots neu besetzt (B1 S10 bleibt leer), keine gelöschten Shots wieder drin

**Geliefert (Resolve „Messe Showreel“, nur angehängt; v1–v3 bleiben):**
- Bin „Claude Showreel v4 2026-09-11 1753“
- **„Claude Showreel 5min v4 2026-09-11 1753“:** 103 Shots, 7500 Frames = 5:00, 4K/25p; Lea 83 Shots / 79,0 % der Zeit;
  14 zerlegte Einstellungen (6 aus dem Garten); Shotlängen 1,2–4,4 s; Readback 0 Abweichungen, 0 Lücken
- „Claude Showreel Reserve v4 …“: 56 Shots · Plan `plan_v4.json`, Prüfbögen `pruefboegen/v4/`

**Offen / Entscheidung User**
- Abendteil: nach den Löschungen kaum noch Lea-Abend-/Party-Material → Blockenden in B2–B8 teils mit Gratulation/Gästen am Tag.
  Optionen: so lassen · mehr Jessica-Party im Abendteil (Anteil sinkt) · Abendteil verkürzen (neue Vorlage)
- Kleinigkeiten: Glashaus-Totale ähnlich in B4 und B7; Fotobox-Perücken B8 S5

## 2026-09-11 — Showreel v5: mehr Party

**User:** „Mach noch mehr Partymaterial rein. Es ging nur um die spezifischen Shots und nicht darum, dass die Szene
unpassend ist“ (nächster Durchgang; Löschungen diesmal direkt in v4)

**Befund v4:** 10 Shots gelöscht (t2-010 Kerze, t2-075 Drohne, t2-151, t1-277, t1-076, t2-140, t2-013 Kirchenschiff,
t1-272, t1-218 Fotobox-Perücken, t1-264 Braut tanzt im Glashaus); t1-029s01 vom User gekürzt (2838/70 → 2822/41)
→ `v4_user_aenderungen.json`

**Gemacht**
- Abzug für „gleicher Moment/ähnliches Bild wie gelöscht“ entfernt – nur die konkreten Shots bleiben gesperrt (v2 + v4)
- Abendteil: Party zuerst, nie Tagesbilder; Jessica-Obergrenze tagsüber 22, im Abendteil +10, Party-Folgen erlaubt
- 8 kurze Lea-Party-Shots zurückgeholt (Strobo-Schnitte fälschlich als weiche Blende gewertet, Rand 4 statt 15) →
  `segments_override.json`, selbst bewertet (`vision/party/`)
- `--swap scripts/swap_v5.json` auf Basis v4: 20 von 21 Slots neu (10 Löschungen + 10 Tagesbilder im Abendteil), Kürzungen fixiert

**Geliefert (Resolve „Messe Showreel“, nur angehängt; v1–v4 bleiben):**
- Bin „Claude Showreel v5 2026-09-11 1804“
- **„Claude Showreel 5min v5 2026-09-11 1804“:** 103 Shots, 7500 Frames = 5:00, 4K/25p; **21 Party-Shots** (v4: 8, 49 s),
  2–3 pro Block, kein Tagesbild im Abendteil; Lea 71 Shots / **71,4 % der Zeit** (Jessica 32); Readback 0 Abweichungen, 0 Lücken
- „Claude Showreel Reserve v5 …“: 55 Shots · Plan `plan_v5.json`, Prüfbögen `pruefboegen/v5/`

**Offen:** Sichtung v5; B1 S10 bleibt leer (kein passender Kandidat); Lea-Anteil bewusst auf ~71 % gesunken (Lea-Party-Material erschöpft)

## 2026-09-11 — Showreel v6: Durchgang nach Sichtung v5

**User:** „nächster Durchgang, wir nähern uns dem Ende“ (Änderungen direkt in v5)

**Befund v5:** 12 Shots gelöscht (t2-093 Festzelt, t2-035 Kirchenkuss, t1-036 First Look, t2-247, t1-263, t2-164 FPV-Drohne,
t1-082, t1-053s04 Vater mit Schirm, t2-090 Fachwerkhaus, t2-303, t1-297 Fotobox, t2-297 Straußwurf); t1-053s03 gekürzt
(5543/100 → 5567/76) → `v5_user_aenderungen.json`

**Gemacht**
- Sperrliste liest jetzt alle Lösch-Runden automatisch (`v*_user_*.json`)
- `--swap scripts/swap_v6.json` auf Basis v5: erster Lauf ließ 8 Tages-Slots leer (Lea-Material für Location/Trauung nur
  noch ~1,6 s lang, Jessica tagsüber am Deckel) → späte Ausweichstufe: kurze Einstellungen ab 1,6 s in jedem Slot,
  Längenausgleich bis +2 s je Shot → alle 13 Slots besetzt (auch der seit v4 leere B1 S10)

**Geliefert (Resolve „Messe Showreel“, nur angehängt; v1–v5 bleiben):**
- Bin „Claude Showreel v6 2026-09-11 1858“
- **„Claude Showreel 5min v6 2026-09-11 1858“:** 104 Shots, 7500 Frames = 5:00, 4K/25p; 21 Party-Shots, kein Tagesbild im
  Abendteil; Lea 74 Shots / 73,6 % der Zeit; Kürzungen t1-029s01, t1-048, t1-053s03 fixiert; Readback 0 Abweichungen, 0 Lücken
- „Claude Showreel Reserve v6 …“: 54 Shots · Plan `plan_v6.json`, Prüfbögen `pruefboegen/v6/`
- Neu u. a.: Ringtausch von hinten, Manschettenknöpfe, Gästebuch, Freundin nimmt Brautkleid, Freunde heben Bräutigam hoch,
  Brauttanz im Laserlicht

**Hinweise:** Blöcke 3, 4, 6 starten nicht mehr mit Location, sondern mit Detail/Getting Ready (Location-Material nach den
Löschungen erschöpft); einzelne ruhige Shots bis 5 s (t1-087 Trauung 125 Frames)

- User-Wunsch: 13 grüne Range-Marker „NEU v6“ auf die neuen Shots in v6 gesetzt (Notiz: Block · Slot · Motiv · Paar),
  Readback 13 grün + 8 blau

**Offen:** Sichtung v6 → Final; danach Export Master 4K/25p nach `Material/Video/` (Remotion-Input), Aufräumen der
Zwischenversionen (Test-Timeline, v1–v5) nur auf Zuruf

## 2026-09-11 — Grafik-Ebene (Remotion) + Messe-Screen-Composite in Resolve

**User:** „Okay passt, jetzt baue alle Grafiksachen ein, alles direkt in Resolve. Dafür importierst du deine zuvor gerenderten
Animationen“ → v6 ist der Schnitt-Stand. Die Animationen waren noch nicht gerendert und wurden jetzt gebaut; zusammengesetzt
wird **in Resolve** statt wie in der Design-Spec geplant in Remotion (kein Showreel-Master-Export als Remotion-Input nötig)

**Gemacht — Remotion (Client `aeterna-weddings`)**
- `tools/motion/src/clients/aeterna-weddings/`: `brand.json`, Komposition `Aeterna-MesseScreen`
  (`projects/messe-screen/Composition.tsx`); Logo + QR-SVG (Ziel `https://aeterna-weddings.de`, Dunkelbraun auf Elfenbein)
  in `tools/motion/public/clients/aeterna-weddings/`; Motion-Kern um 50 fps ergänzt (`core/types.ts`, `core/schemas.ts`), Paket `qrcode`
- Aufbau laut Design-Spec: Elfenbein-Grund mit ausgestanztem Video-Fenster (1152×648 an 64/216 im 1080er-Raster, Radius 14,
  Gold-Passepartout), Kicker „Hochzeitsfilm · Social-Reels · Fotografie“, Claim in Great Vibes unter dem Video, Logo,
  8 Kapitel à 12,5 s (Masken-Reveal, Goldlinie), Fortschrittsbalken, QR + „Jetzt scannen · Kostenfreies Kennenlernen“
- Standbilder geprüft; Zeilenumbrüche in Kapitel 1, 4, 7, 8 korrigiert

**Geliefert**
- `Ergebnisse/Renders/aeterna-messe-grafik-4k50-loop100s.mov`: ProRes 4444 mit Alpha, 3840×2160, 50p, 5000 Frames = 100 s, 6,0 GB
  - Nachmessung: Fenster x 128–2431 / y 432–1727 voll transparent, harte Kanten, runde Ecken; an der Loop-Naht springt
    nur der Fortschrittsbalken (voll → leer)
- Resolve „Messe Showreel“ (Freigabe dieser Session, nur angehängt; v1–v6 unverändert):
  - Bin „Claude Messe-Screen 2026-09-11 1920“ mit dem Grafik-Render (Alpha mode automatisch „Straight“)
  - **„Claude Messe-Screen v1 2026-09-11 1920“:** eigene Timeline-Einstellungen 3840×2160 @ 50p
    - V1: verschachtelte Timeline „Claude Showreel 5min v6 2026-09-11 1858“, Zoom 0,604 · Pan −640 · Tilt 0
      (Fenster plus 4–8 px Überstand gegen Haarlinien), Retime „Nearest“ (25p → 50p = reine Bildverdopplung)
    - V2: Grafik-Render 3× hintereinander (je 5000 Frames), nur Video
    - Readback: 15000 Frames = 5:00; V1 15000 Frames ab Offset 0 (25p-Timeline wird in Echtzeit übernommen); V2 3 × 5000; keine Lücken
  - Standbild aus Resolve: Elfenbein exakt #FCFBF8, Fensterkanten ohne dunkle Haarlinie, Kapitel 3 und Fortschrittsbalken passen zu Sekunde 30
- API-Befund: `ExportCurrentFrameAsStill` direkt nach `SetCurrentTimecode` im selben Skript liefert beim zweiten Aufruf wieder das alte Bild

**Offen**
- Sichtung des Composites durch den User; danach Export H.265 4K50 (MP4, ≤ 60 Mbps, LG webOS) nach `Ergebnisse/Export/` für den USB-Stick
- QR-Ziel vorerst `aeterna-weddings.de` (HubSpot-Terminlink möglich) · Aufräumen der Zwischenversionen nur auf Zuruf

## 2026-09-11 — Grafik v2: Frame.io-Feedback

**User (Frame.io-Kommentare + Screenshots):** 0:18 „beides Singular oder beides Plural“ → Plural („mach hier Filme“) ·
0:35 „Foto"s"“ · 0:52 „Doppelpunkt hinter der Überschrift“. **Noch nichts in Resolve** – dort läuft gerade ein anderes Projekt

**Gemacht (Remotion `Aeterna-MesseScreen`)**
- Kapitel 2: „Fotos zeigen, / wie es aussah. / Filme zeigen, / wie es sich / angefühlt hat.“ – im Plural passt „Filme zeigen,
  wie es“ bei 58 px nicht mehr in eine Zeile → fünf Zeilen, Schriftgröße unverändert
- Kapitel 3: „Fotos auf Wunsch“
- Kapitel 5: „Was euch nicht passiert:“ – die Überschrift bricht wie schon in v1 (so auf Frame.io gesichtet) nach „nicht“ um, Liste unverändert
- 4K-Standbilder der Kapitel 2, 3, 5 geprüft: Zeilen gezählt, alles innerhalb der Panelbreite

**Geliefert**
- `Ergebnisse/Renders/aeterna-messe-grafik-4k50-loop100s-v2.mov`: ProRes 4444 mit Alpha, 3840×2160, 50p, 5000 Frames = 100 s,
  6,0 GB (v1 bleibt liegen)
  - Nachmessung: Fenster unverändert (x 128–2431 / y 432–1727); Render deckt sich mit den Standbildern (max. 4 Stufen);
    v1 ↔ v2 unterscheiden sich nur an den drei Textstellen (Kapitel 2 Zeilen 3–5, Kapitel 3 dritter Punkt, Kapitel 5
    Doppelpunkt), Kapitel 4 identisch; Loop-Naht wie v1 (nur Fortschrittsbalken)
- Resolve „Messe Showreel“ (User: „DaVinci ist wieder frei“; Freigabe dieser Session, nur angehängt; Composite v1 bleibt):
  - Bin „Claude Messe-Screen v2 2026-09-11 2025“ mit dem v2-Render (Alpha mode „Straight“, 5000 Frames @ 50p)
  - **„Claude Messe-Screen v2 2026-09-11 2025“:** 3840×2160 @ 50p; V1 verschachtelte v6-Timeline mit den Werten aus v1
    (Zoom 0,604 · Pan −640 · Tilt 0 · Retime Nearest); V2 Grafik v2 3×
  - Readback: 15000 Frames = 5:00, Aufbau identisch mit v1 (Positionen, Offsets, Transform); danach war die aktive
    Timeline des Users (Composite v1) wieder aktiv

**Offen**
- Sichtung Composite v2; danach Export H.265 4K50 (MP4, ≤ 60 Mbps) nach `Ergebnisse/Export/` für den USB-Stick
- Aufräumen (Composite v1, Grafik v1, Zwischenversionen) nur auf Zuruf

## 2026-09-11 — Export für den LG-Messebildschirm (USB-Stick)

**User:** „Export so, dass es für den LG-Fernseher passt, Datei nicht über 4 GB, am besten mehrere Renders zum Testen“

**Gemacht**
- Resolve „Messe Showreel“: Render-Job aus „Claude Messe-Screen v2 2026-09-11 2025“ → Master
  `_intern/export-master/Aeterna-Messe-Screen-v2_Master_4K50_ProRes422LT.mov` (ProRes 422 LT, 3840×2160, 50p, 15000 Frames
  = 5:00, Rec.709 Limited, ohne Ton, 21,4 GB; Renderzeit 68 s)
  - `AddRenderJob` lieferte zuerst keinen Job (Timeline im selben Skript umgeschaltet) → Timeline in eigenem Aufruf
    aktiviert, dann ok; Deliver-Format/Codec danach zurück auf MP4/APV, aktive Timeline des Users (Composite v1) wieder
    aktiv; „Job 1“ bleibt in der Render-Queue
  - Prüfung: 30 Stichproben (alle 10 s) ohne Offline-Medien, Kapitel-Reihenfolge in allen drei Durchläufen korrekt,
    Elfenbein 252/251/247
- Testdateien per ffmpeg aus dem Master (`_intern/export-master/lg_exports.sh`, Prüfung `lg_verify.py`): alle MP4 mit
  faststart, Rec.709-Tags und stummer AAC-Stereospur (falls der Player eine Tonspur erwartet), weit unter 4 GB

**Geliefert** (`Ergebnisse/Export/`)

| Datei | Codec | Bild | Größe | Ø / Spitze 1 s |
|---|---|---|---|---|
| `01_Aeterna-Messe_4K50_H265_max40Mbps.mp4` | H.265 Main L5.1 (x265 medium, CRF 18, VBV 40 Mbit/s) | 3840×2160 / 50p | 0,53 GB | 14,1 / 50,3 Mbit/s |
| `02_Aeterna-Messe_4K50_H265-Apple_30Mbps.mp4` | H.265 Main L5.1 (Apple VideoToolbox) | 3840×2160 / 50p | 1,12 GB | 30,0 / 46,0 Mbit/s |
| `03_Aeterna-Messe_4K25_H265_max25Mbps.mp4` | H.265 Main L5.0 (x265 fast, CRF 19, VBV 25 Mbit/s) | 3840×2160 / 25p | 0,39 GB | 10,4 / 30,3 Mbit/s |
| `04_Aeterna-Messe_4K25_H264_max40Mbps.mp4` | H.264 High L5.1 (x264 medium, CRF 18, VBV 40 Mbit/s) | 3840×2160 / 25p | 0,58 GB | 15,5 / 27,5 Mbit/s |
| `05_Aeterna-Messe_1080p50_H264_max16Mbps.mp4` | H.264 High L4.2 (x264 medium, CRF 18, VBV 16 Mbit/s) | 1920×1080 / 50p | 0,19 GB | 4,9 / 11,1 Mbit/s |

**Testreihenfolge am LG:** 01 → 02 (gleiches Format, anderer Encoder) → 03 (falls 4K50 nicht läuft) → 04 (falls kein H.265)
→ 05 (Full HD, läuft praktisch überall)

**Offen**
- User testet am LG, welche Datei läuft (alle fünf fertig und geprüft)
- Master (21 GB) bleibt in `_intern/export-master/`, bis feststeht, welche Variante läuft
