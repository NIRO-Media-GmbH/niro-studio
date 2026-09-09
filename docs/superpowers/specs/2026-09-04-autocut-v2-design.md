# NIRO AutoCut v2 — Feedback-Runde 1 (Spec)

Datum: 2026-09-04 · Status: Entscheidungen vom User an Claude delegiert („Ich höre auf deine
Empfehlung"), Umsetzung autonom, Review durch den User an der neuen MEK-Timeline.
Grundlage: `2026-09-03-autocut-design.md` (Stufen 1–4). Diese Spec ändert nur, was hier steht;
alles andere gilt weiter.

## Anlass

Feedback zum ersten Rohschnitt (Timeline „AutoCut video-1-imagefilm-zwei-haeuser 2026-09-04 0032",
MEK Imagefilm): Sync perfekt. Wünsche: FX3-Ton je Clip auf True Peak −3 dBTP normalisieren; a7IV-Ton
ganz raus; B-Roll zu wenig und zusammengewürfelt — Ziel 80–85 % B-Roll, 15–20 % Sprecher sichtbar;
keine Schwarzframes; High-fps-B-Roll darf auf die Timeline-Bildrate verlangsamt werden; mindestens
3 aufeinanderfolgende Shots aus demselben sortierten B-Roll-Ordner (Szenen), Ausnahmen erlaubt; nie
zwei Shots hintereinander mit gleicher Einstellung/Perspektive/Brennweite.

Ist-Messung der Timeline 0032 (212,7 s): Sprecher 96,8 s = 45 %, B-Roll 85,8 s = 40 %, Schwarz
30,2 s = 14 % (21 Pausen à 1 s, Endcard-Platzhalter 6 s, 2 s Restlücken). O-Ton-Beats nur zu 26 %
abgedeckt. Ursachen im Startprofil: B-Roll nur innerhalb eines Beats, Pausen leer; „nicht zwei Clips
aus demselben Ordner nacheinander"; Abdeckung ≤ 80 % je Beat; lange Beats enden mit Gesicht.

## Befunde (04.09., geprüft)

- **Resolve-API 21.0.4** kennt weder „Normalize Audio Levels" noch eine Lautstärke-Eigenschaft für
  Timeline-Items und keine Clip-Geschwindigkeit (README geprüft). `Timeline.Export` (FCP7-XML) und
  `MediaPool.ImportTimelineFromFile` (XML, Optionen `timelineName`, `importSourceClips`,
  `sourceClipsFolders`) existieren; `DeleteTimelines`, `DeleteFolders`, `DeleteClips`, `SetTrackName`.
- **Resolve schreibt Clip-Pegel im FCP7-XML** als Filter „Audio Levels" (`effectid audiolevels`,
  Parameter `level`, linearer Faktor, `valuemin 1e-05`, `valuemax 31.6228` = +30 dB). Belegt an der
  Timeline des Users (Werte 0,92 … 9,23). Marker exportiert Resolve **nicht** ins XML.
- **FX3-Ton** ist Mono auf beiden Kanälen (Peaks identisch, PCM 16 bit 48 kHz) — Normalisierung je
  Clip ist eindeutig.
- **Sony-Metadaten** liefern keine Brennweite: Sidecar-XML nur Objektiv („24-70mm F2.8 DG DN II"),
  rtmd nur ISO/Blende. Brennweitenklasse muss die Vision schätzen.
- **B-Roll-Index** (463 Clips): Bildraten 296×25, 157×50, 10×100 fps; Einstellung nur je Clip, davon
  165 „gemischt"; Perspektive/Brennweite fehlen. Frames (464 Ordner, 66 MB) und Kontaktbögen
  (559, 83 MB) liegen im Cache `_intern/autocut/work/`. Frame-Dateiname = `<stem>_<Hundertstel>.jpg`.
- **XML-Roundtrip-Semantik** (Pegel- und Speed-Import, Medien-Zuordnung, Spurnamen) ist ungeprüft →
  eigene Probe (Abschnitt 6) vor dem ersten Finalisieren.

## Entscheidungen (Rückfragen, von Claude entschieden)

| Frage | Entscheidung |
|---|---|
| Endcard-Platzhalter (#25) | B-Roll darunter, durchgehend bis zum Timeline-Ende; der Beat-Marker (Lila „Grafik") bleibt und sagt „Grafik kommt von Motion". Kein Farbfeld-Generator. |
| „Wechselschnitt"/„Gesichter-Montage beider Häuser" im Plan | Ausnahme von der Szenen-Regel: Shot-für-Shot-Wechsel S1/S2 erlaubt, aber nur mit `ausnahme`-Text, der den Plan-Kommentar nennt; Einstellungs-Regel gilt trotzdem. Im Bericht ausgewiesen. |
| „Frontal" in der Bild-Spalte | Bezeichnet nur die Einstellung des Sprecher-Fensters, nicht „Gesicht halten". Ganz-Gesicht-Beats sind: Beat 1 (Hook), Beats mit „Gehaltenes Gesicht" oder „Bookend" in Szene/Bild/Kommentar, Beats kürzer als 3 s. |
| Slow-Mo | Claude entscheidet je Shot (`tempo` 1/2/4). 2× für Hände, Geräte, Gehen, ruhige Fahrten; nicht für sprechende Menschen, schnelle Aktion oder sichtbar hektisches Geschehen. 4× nur für bewusst langsame Momente (100p). Echtes Konformieren: jeder Quellframe genau einmal. |
| Normalisierung | Independent je Timeline-Clip, gemessen auf dem Schnittbereich inklusive Handles, nicht auf dem ganzen Take. Ziel −3,0 dBTP. |

## 1. Stufe 1 — Ton und Spuren

- **Spuren:** V1 „FX3", V2 „a7IV" (nur Bild, `mediaType 1`), V3 „B-Roll", A1 „FX3 Ton". Keine A2.
  `timeline_model` erzeugt keine A2-Items mehr; `disable_items`/Verknüpfung V2+A2 entfallen.
- **Zwischen- und End-Timeline:** Stufe 1 baut per API wie bisher, aber unter dem Namen
  `AutoCut <video> <JJJJ-MM-TT HHMM> (roh)`. Die End-Timeline `AutoCut <video> <JJJJ-MM-TT HHMM>`
  entsteht in Stufe 5 (Finalisieren, Abschnitt 4) aus dem XML-Roundtrip. Stufe 3 legt V3 in die
  roh-Timeline. Ohne Stufe 3 kann direkt finalisiert werden (nur O-Töne, normalisiert).
- **Pegelmessung** (`ton.py`, Skript-Teil von `autocut_finalize.py`): je A1-Item ffmpeg
  `-ss <in> -t <dauer> -i <Original> -map 0:a:0 -af ebur128=peak=true -f null -`; True Peak aus der
  Zusammenfassung (dBFS, Maximum beider Kanäle). `gain_db = −3,0 − tpk`, `gain_lin = 10^(gain_db/20)`,
  begrenzt auf +30 dB (Resolve-Maximum) mit Warnung; Warnung auch bei `tpk > −0,5` (Clipping-Verdacht)
  und bei Stille (`tpk < −60`, Gain wird dann 0 dB). Ergebnis `_intern/autocut/ton.json`:
  `{"ziel_dbtp": -3.0, "items": [{clip, src_in_f, src_out_f, rec_in_f, tpk_dbfs, gain_db, gain_lin,
  warnung}]}`. Messung gecacht je (Fingerprint, in, out).

## 2. Stufe 2b — Index-Nachlauf je Abschnitt (`autocut_index_sections.py`)

Ziel: die Felder, die die Schnittregeln brauchen, je **Abschnitt** eines Clips — ohne neue
Frame-Extraktion.

- **Eingabe:** `broll_index.json` (Clips mit `abschnitte[]`, `kacheln[]`, Fingerprint) und der
  Frame-Cache `work/frames/<stem>.<fp12>/`. Clips ohne Frames im Cache werden gemeldet und übersprungen.
- **Abschnittsbogen je Clip:** je Abschnitt zwei Kacheln (Frame nächst `von_s + 0,5` und Mitte;
  bei Abschnitten unter 1,5 s nur eine) à 480×270 (Hochkant 270×480), Beschriftung „A<n>·<a|b>",
  Raster 2 Spalten × Abschnitte (max. 5 Zeilen) → höchstens 960×1350 px, ≈ 0,7–1,7 k Bildtoken.
  Datei `work/sheets/<stem>.<fp12>_A.jpg`.
- **Claude-Anfrage** (Modell/Effort aus `index.model`/`index.effort`, System-Prompt
  `prompts/index-sections.md` mit Cache-Marke, Structured Output): je Abschnitt
  `einstellung` (Totale/Halbtotale/Halbnah/Nah/Detail), `perspektive_hoehe` (Augenhöhe/Aufsicht/
  Untersicht/Vogelperspektive), `perspektive_ansicht` (frontal/seitlich/schräg/Rückansicht/ohne Person),
  `brennweite` (weit/normal/tele — geschätzt aus Bildwinkel, Verzeichnung, Hintergrundkompression),
  `bewegungsrichtung` (keine/nach links/nach rechts/auf Kamera zu/von Kamera weg/gemischt),
  `hauptmotiv` (≤ 6 Wörter). Der Textteil nennt die Abschnittsgrenzen und die vorhandene
  Abschnittsbeschreibung, damit Kachel und Abschnitt eindeutig zugeordnet sind.
- **Lokal, ohne API:** `setup_hash` je Abschnitt (dHash 8×8 des mittleren Frames, 16 Hex-Zeichen)
  für die Erkennung nahezu gleicher Kadragen (Hamming-Distanz).
- **Ablage:** in den Clip-Cache `broll_index/<fingerprint>.json` gemerged (`abschnitte[i]` erhält die
  neuen Felder, Clip erhält `nachlauf: {modell, effort, indiziert_am, usage}`); `broll_index.json`
  und der kompakte Index werden neu geschrieben. `--dry-run` nennt Clipzahl, Cache-Stand und
  Kostenschätzung (Formel: Bildtoken aus Bogenmaßen + 600 Text + Ausgabe 250 je Clip); `--limit`,
  `--force`, `--parallel` wie beim Index. Nachlauf ist wieder aufnehmbar (Cache je Clip).

## 3. Stufe 3 — B-Roll-Layout über die ganze Timeline

### 3.1 Modell

Die Timeline zerfällt in **Sprecher-Fenster** (V1 sichtbar) und **Strecken** (V3 durchgehend):

- **Fenster** liegen an O-Ton-Beats: Standard am Beat-Anfang, 2,5 s beim ersten Auftritt einer
  Person, sonst 2,0 s; Ganz-Gesicht-Beats (Entscheidung oben) komplett. Claude darf je Fenster
  1,5–4,0 s setzen, weitere Fenster innerhalb eines Beats hinzufügen (`offset_s`) oder ein Beat als
  „voll" markieren. Fenster enden nie außerhalb ihres Beats.
- **Strecken** sind die Lücken zwischen den Fenstern — von Timeline-Anfang bis -Ende, über Pausen,
  Platzhalter und Beat-Grenzen hinweg. Der Code berechnet sie aus den Fenstern (`--raster`).
- **Szenen** füllen Strecken: eine Szene = mindestens 3 Shots aus **einem** sortierten Ordner
  (Standort + Motiv-Ordner), Einstellungswechsel von Shot zu Shot (Establishing zuerst, dann näher,
  oder umgekehrt als Enthüllung). Weniger als 3 Shots nur mit `ausnahme` (Plan-Kommentar
  „Wechselschnitt"/„Gesichter-Montage", Einzel-Einschub aus kleinem Ordner, Strecke kürzer als 6 s).
- **Shots:** `clip`, `in_s`, `out_s` (Quell-Echtzeit), `tempo` ∈ {1, 2, 4}, Timeline-Dauer
  `(out_s − in_s) × tempo`. Längen über O-Ton 2,0–5,0 s (bei `tempo` > 1 bis 6,0 s), in Platzhalter-
  Beats 1,5–3,0 s, „Schnelle Cuts" 1,0–2,0 s; maßgeblich ist der Beat unter dem Shot-Anfang (Pausen
  zählen zum vorigen Beat). Der letzte Shot einer Strecke darf auf die Reststrecke gekürzt sein, aber
  nicht unter die Mindestlänge; die Shot-Summe muss die Strecke auf ±1 Frame füllen.

### 3.2 Plan-Format `broll_plan.json` (v2)

```json
{"version": 2, "video": "video-1-….md",
 "fenster": [{"beat_nr": "1", "voll": true, "grund": "Hook"},
             {"beat_nr": "6", "offset_s": 0.0, "dauer_s": 2.5, "grund": "erster Auftritt Zoran"}],
 "strecken": [
   {"nr": 1, "szenen": [
      {"ordner": "Standort 1/Notaufnahme", "ausnahme": "", "grund": "Welt 1 akut: Schockraum als Szene",
       "shots": [
         {"clip": "Standort 1/Notaufnahme/FX3_9503.MP4", "in_s": 2.0, "out_s": 5.0, "tempo": 1,
          "grund": "Totale Schockraum, Establishing", "abweichung": false, "abweichung_grund": ""},
         {"clip": "Standort 1/Notaufnahme/FX3_9545.MP4", "in_s": 0.5, "out_s": 2.0, "tempo": 2,
          "grund": "Detail Monitor, 2× ruhig"}]}]}]}
```

Nur diese Felder. `fenster`-Einträge ohne `voll` brauchen `dauer_s`; `offset_s` Standard 0. Beats
ohne Eintrag bekommen das Standardfenster. Strecken-Nummern kommen aus `--raster`; der Code rechnet
`von_s/bis_s` selbst. Version-1-Pläne (`beats[]`) werden abgelehnt mit Hinweis auf `--raster`.

### 3.3 Prüfung (`verify_broll_plan`, Fehler = Abbruch, Warnung = Bericht)

Fehler: Fenster außerhalb 1,5–4,0 s (außer `voll`) oder außerhalb des Beats; Fenster in
Nicht-O-Ton-Beats; Strecken-Nummer unbekannt oder Strecke fehlt (→ Schwarz); Shot-Summe ≠
Streckenlänge (±1 Frame); Shot-Länge außerhalb der Grenzen; `tempo` ohne passende Clip-Bildrate
(2 nur ab 50p, 4 nur ab 100p, exakte Vielfache); Bereich außerhalb eines verwendbaren Abschnitts;
gesperrter Mangel; Sperre der Cutlist; „Nur S1/S2"; Clip doppelt (auch anderer Abschnitt); Szene mit
< 3 Shots ohne `ausnahme`; Shots einer Szene aus verschiedenen Ordnern ohne `ausnahme`; zwei
aufeinanderfolgende Shots (auch über Szenen- und Streckengrenzen, nicht über ein Fenster) mit
gleicher `einstellung` **und** gleicher Perspektive (Höhe + Ansicht) **und** gleicher `brennweite`;
Gesichtsanteil (Fenster-Summe / Gesamtlänge) unter 12 % oder über 23 %; Abschnittsfelder fehlen
(Nachlauf nicht gelaufen). Warnungen: Gesichtsanteil außerhalb 15–20 %; aufeinanderfolgende Shots
mit `setup_hash`-Distanz < 10; Szene ohne Einstellungswechsel-Muster; mehr als 3 Ausnahmen;
Abschnitt mit Qualität < 3; Shot ohne `grund`; `tempo` 4.

### 3.4 Bau

V3-Items in die roh-Timeline wie bisher (`mediaType 1`), `tempo`-Items mit ihrem Quellbereich;
ihre Timeline-Länge stimmt erst nach dem Finalisieren (Abschnitt 4). Marker: je Szene ein
cyanfarbener Marker „Szene n · <Ordner> · k Shots" am Szenenanfang; gelbe Marker „B-Roll
abweichend" bleiben. `broll_build.json` hält je Item `tempo`, Ziel-Länge in Timeline-Frames und
den Item-Schlüssel für das Finalisieren.

## 4. Stufe 5 — Finalisieren (`autocut_finalize.py`)

1. Voraussetzung: `build.json` (roh-Timeline), optional `broll_build.json`; `probe_xml.json` mit
   `level_import_ok: true` (Abschnitt 6), sonst Abbruch mit Hinweis auf die Probe.
2. Pegel messen (Abschnitt 1) → `ton.json`.
3. roh-Timeline als FCP7-XML exportieren nach `_intern/autocut/work/xml/<name>.roh.xml`.
4. **Patchen** (`xml_patch.py`, reines XML, keine Resolve-Aufrufe): A1-Clipitems bekommen den Filter
   „Audio Levels" mit `level = gain_lin` (vorhandenen Level-Parameter ersetzen, sonst Filter
   einfügen, Struktur exakt wie Resolves Export); V3-Clipitems mit `tempo > 1` bekommen den Filter
   „Time Remap" (`speed = 100/tempo`, `variablespeed 0`, `reverse FALSE`, `frameblending FALSE`) und
   `end = start + Ziel-Länge`; Zuordnung über Spur, `start` und Dateiname. Nichts anderes wird
   verändert. Ergebnis `<name>.final.xml`.
5. **Importieren:** `ImportTimelineFromFile(final.xml, {"timelineName": "<Endname>",
   "importSourceClips": False, "sourceClipsFolders": [AutoCut-Bin, B-Roll-Bin]})`.
6. **Prüfen** per Readback: je Spur Item-Zahl, Start und Dauer gegen `timeline.json` +
   `broll_build.json` (für `tempo`-Items die Ziel-Länge); alle Items referenzieren Media-Pool-
   Einträge mit Proxy; Re-Export der End-Timeline → jeder A1-Clip trägt `level` = Soll (±1 %),
   jeder `tempo`-Clip `speed` = Soll. Weicht etwas ab: End-Timeline in „… FEHLER" umbenennen,
   roh-Timeline behalten, Abbruch mit Meldung.
7. Nacharbeit per API: Spurnamen setzen; alle Marker aus `timeline.json` + `broll_build.json` neu
   setzen (XML trägt keine Marker); `tempo`-Items Clip-Farbe „Teal"; aktuelle Timeline des Users
   wiederherstellen (siehe Abschnitt 7).
8. roh-Timeline löschen (`DeleteTimelines`) — **einzige** erlaubte Löschung neben der Probe: nur die
   im selben Lauf gebaute Timeline mit Suffix „(roh)", deren Name in `build.json` steht. `--keep-roh`
   verhindert das Löschen.
9. `finalize.json`, Bericht `Ergebnisse/Rohschnitt/<video>-rohschnitt.md` erweitert um die Pegel-
   Tabelle (Clip, Bereich, True Peak, Gain), Protokoll-Eintrag. XML-Export für den Probecutter
   nutzt fortan die End-Timeline.

## 5. Profil, Prompts, Doku

- `profile/default.yaml` (v2): `face_share: [0.15, 0.20]`, `face_share_hard: [0.12, 0.23]`,
  `window_first_s: 2.5`, `window_s: 2.0`, `window_min_s: 1.5`, `window_max_s: 4.0`,
  `full_face_beat_max_s: 3.0`, `full_face_keywords: ["Gehaltenes Gesicht", "Bookend"]`,
  `shot_len_s: [2.0, 5.0]`, `shot_len_slow_max_s: 6.0`, `montage_len_s: [1.5, 3.0]`,
  `fast_cuts_len_s: [1.0, 2.0]`, `scene_min_shots: 3`, `scene_short_stretch_s: 6.0`,
  `setup_hash_min_distance: 10`, `max_exceptions_warn: 3`, `forbidden_maengel` wie bisher.
  Alte Schlüssel `max_coverage`, `tail_free_*`, `first_appearance_visible_s` entfallen.
- `profile/default.md` (v2): Regeln in Prosa — Szenen statt Einzelshots, Cut-Flow, Fenster-Logik,
  Slow-Mo-Kriterien, Ausnahmen, Bildlogik zur Aussage (unverändert), David-Regeln (unverändert).
- `prompts/place-broll.md` (v2): Ablauf Raster → Fenster → Strecken füllen → prüfen; Feldreferenz v2.
- `prompts/index-sections.md`: System-Prompt des Nachlaufs (Definitionen der Enums mit Beispielen).
- `WORKFLOW-AutoCut.md`: Stufen 1, 2b, 3, 5 und Probe; Ausgabe-Konvention (`ton.json`,
  `probe_xml.json`, `finalize.json`, `work/xml/`); Fehlerbilder (Level-Import fehlgeschlagen,
  Strecke nicht gefüllt, Nachlauf fehlt, tempo ohne Bildrate).
- Eiserne Regeln ergänzt: Löschen nur eigene roh-Timeline desselben Laufs und eigene Probe-Objekte;
  nach jedem Resolve-Lauf die zuvor aktive Timeline des Users wieder aktivieren.

## 6. Probe `resolve_probe_xml.py`

Einmal je Resolve-Umgebung, vor dem ersten Finalisieren. Legt Bin `AutoCut PROBE XML <HHMM>` und
Timeline `AutoCut PROBE XML <HHMM> (roh)` an: ein FX3-Interview-Clip 2 s auf V1+A1, ein 50p-B-Roll-
Clip 2 s Quelle auf V3 (Ziel 4 s bei 2×). Exportiert, patcht (`level 0.5`, `speed 50`, `end`),
importiert als „… PROBE IMPORT", liest zurück, re-exportiert. Schreibt `_intern/autocut/probe_xml.json`:
`level_import_ok`, `speed_import_ok`, `speed_source` (welche Angabe Resolve nutzt: `end`, `filter`,
beides), `markers_survive` (erwartet false), `tracknames_survive`, `media_relinked` (Proxy-Link
erhalten). Zusätzlich Rückfall-Datenpunkt: `AddItemListToMediaPool` desselben Pfads in den Probe-Bin
→ `duplicate_item_created`, danach `SetClipProperty('FPS','25')` auf dem Duplikat → `fps_settable`.
Löscht am Ende beide Probe-Timelines, die Duplikate und den Probe-Bin; stellt die Timeline des Users
wieder her. Fällt `speed_import_ok` aus, gilt Rückfall: `tempo` nur, wenn `fps_settable` und der Clip
in keiner bestehenden Timeline liegt (aus `timelines_readback.json`), konformiert am Duplikat im
AutoCut-Bin. Fällt `level_import_ok` aus, gilt Rückfall: normalisierte WAVs je A1-Item
(`work/audio_norm/`, PCM 24 bit) statt Kamera-Ton auf A1, verknüpft mit V1 — eigener Plan-Task,
erst bei Bedarf.

## 7. Betrieb und Sicherheit

- Alle Resolve-Läufe merken sich `GetCurrentTimeline()` beim Start und aktivieren sie am Ende wieder
  (der User arbeitet parallel in Resolve). Läufe sind kurz und laufen ohne Rückfragen durch.
- Schreibbereiche unverändert (`_intern/autocut/**`, `Ergebnisse/Rohschnitt/**`, `Protokoll.md`).
  Neue Ausnahme für Löschungen wie in Abschnitt 4/6. Bestehende Timelines des Users werden nur
  gelesen (Export ist lesend).
- `save_project`-Warnung („'NoneType' object is not callable") wird behoben (Aufruf am
  ProjectManager, Rückgabe nur protokolliert).
- Index-Clip a7MK4_20260702_9970 (HTTP 400): Nachlauf überspringt Clips ohne Erst-Index; erneuter
  Versuch mit kleinerem Bogen im Erst-Index bleibt offen.

## 8. Tests

Einheiten (ohne Resolve/NAS): ffmpeg-Ausgabe-Parser (True Peak), Gain-Formel und Grenzen,
`xml_patch` (Level einfügen/ersetzen, Time Remap + `end`, unveränderte Reste byteweise gleich),
Raster (Fenster-Standards, Ganz-Gesicht-Erkennung, Streckenbildung inkl. Pausen/Platzhalter/Endcard),
Strecken-Füllung (Summe, letzter Shot gekürzt), Szenen-Regel + Ausnahmen, Cut-Flow-Regel,
Gesichtsanteil, `tempo`-Gültigkeit und Timeline-Länge, Abschnittsbogen-Komposition aus dem Frame-Cache,
Schema des Nachlaufs, dHash-Distanz, Plan-v1-Ablehnung. Fake-Resolve: Finalize-Ablauf (Export →
Patch → Import → Prüfen → Marker/Spurnamen → roh löschen; Abbruchpfad ohne Löschung).
Live (MEK): Probe; Nachlauf `--limit 5` dann voll; Neubau (roh) → Plan v2 → V3 → Finalisieren;
Abnahme: Gesicht 15–20 %, Schwarz 0 s, Pegel im Re-Export, Slow-Mo-Längen, Szenen-Marker.

## 9. Reihenfolge der Umsetzung

1. Spurlayout ohne A2, Pegelmessung, `xml_patch`, Probe-Skript, Finalisieren (Code + Tests).
2. Nachlauf-Skript + Prompt + Schema + `setup_hash` (Code + Tests), Dry-Run auf MEK, `--limit 5`, Volllauf.
3. Layout v2 (Raster, Plan v2, Prüfung, Bau, Bericht), Profil/Prompt/Workflow-Doku.
4. Live: Probe → Stufe 1 (roh) → Plan v2 durch Claude → V3 → Finalisieren → Abnahme → Protokoll.
5. Stufe 4 (Profil aus Timeline-Referenzen) bleibt der eigene Plan; die Referenzen kalibrieren die
   Zahlen in `profile/default.yaml`.

## Risiken

- XML-Importer verhält sich anders als erwartet (Speed, Medien-Zuordnung) → Probe vor dem ersten
  Finalisieren, Rückfälle in Abschnitt 6.
- 15–20 % Gesicht sind bei vielen kurzen O-Tönen eng (MEK: 16 O-Töne, rechnerisch ≈ 19 %); der Code
  meldet den Anteil, Claude justiert Fenster.
- Kleine Ordner (< 3 verwendbare Clips mit verschiedenen Einstellungen) tragen keine Szene → nur
  Einzel-Einschübe mit Ausnahme; der Bericht listet Ordner ohne Szene.
- Brennweitenklasse ist Schätzung; Fehlurteile führen höchstens zu einem falschen Cut-Flow-Fehler,
  den Claude mit anderem Shot auflöst.
