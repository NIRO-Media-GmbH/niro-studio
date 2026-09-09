# NIRO AutoCut — Design (Spec)

Datum: 2026-09-03 · Status: Abschnitte 1–3 vom User freigegeben, 4–7 zur
Durchsicht (User hat autonome Umsetzung freigegeben, Review am 04.09. früh)

## Zweck

Sechste Funktion von NIRO Studio: Aus einem fertigen Cutter-Schnittplan
entsteht automatisch eine **Rohschnitt-Timeline in DaVinci Resolve** — alle
O-Töne in Planreihenfolge, beide Kameraperspektiven synchron, danach passende
B-Roll auf einer eigenen Spur. Die Interview-Pipeline, der Footage-Sortierer,
der Schnittplan-Workflow, Motion und Foto bleiben **unverändert**; AutoCut
liest nur deren Ergebnisse.

Referenzfall: `projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und
Imagefilm Dreh/` (Plan `video-1-imagefilm-zwei-haeuser.md`, 25 Zeilen, davon
16 O-Töne; Resolve-Projekt „Marien Elisabeth Klinikum Kassel - Imagefilm").

## Recherche-Erkenntnisse (03.09., abends, mit Gegenprüfung)

- **Resolve-API:** `recordFrame` ist absolut (Timeline-Startframe + Offset, 01:00:00:00 @ 25 fps = 90000);
  `AddMarker(frameId)` ist dagegen relativ zum Timeline-Start. `endFrame` ist inklusiv. Alle Clips in einem
  `AppendToTimeline`-Aufruf, danach Readback (`GetStart/GetDuration`). `useCustomSettings='1'` ist für eigene
  Auflösungen Pflicht, setzt aber Color-Management-Keys zurück (BMD-Bug, Forum t=212784) → Keys sichern und
  zurückschreiben. `LinkProxyMedia` nur, wenn `GetClipProperty('Proxy')` nicht schon eine Auflösung nennt.
  Cloud-Projekte speichern sofort (Live Save) → nur eigene, neue Timelines anfassen. Keine Wrapper-Bibliothek
  (pydavinci verwaist), rohe API.
- **Rotation:** Sony schreibt das Rotations-Flag nur bei hochkant gedrehten Clips (Craiss: 90°); die MEK-Interviews
  sind quer (kein Flag) → 16:9, passend zum Plan.
- **Alignment:** eigenes, gegen 61 Craiss-Planzeilen validiertes Modul `quote_align.py` (Token-Alignment mit
  Levenshtein + Kölner Phonetik, Zahlwörter, „[…]"-Segmente, Take-Wahl per mm:ss-Hinweis). MEK: alle 16 O-Ton-
  Zeilen mit Score ≥ 0,93 und exakten Ankern aufgelöst.
- **Vision:** Bildtoken = ⌈w/28⌉·⌈h/28⌉, lange Kante ≤ 2576 px; Kacheln 640×360 im 4×3-Gitter (~3.700 Token pro
  Bogen); Kachelnummer + Zeit einbrennen und zusätzlich als Text mitgeben; Structured Outputs via
  `output_config.format` (Schema ohne min/max, Scores als Enum); System-Prompt ≥ 1024 Token für Prompt-Caching;
  `effort` als Kostenhebel. Kosten 464 Clips: grob 25–50 € online mit Opus 5 (Batch-API halbiert).
- **Sync:** Prototyp bestätigt: Johanna-Paar 48,8 Frames bei Konfidenz 19,7 (Resolve-Referenz 48), kein Drift
  über 10 Minuten.

## Entscheidungen (mit User abgestimmt)

| Frage | Entscheidung |
|---|---|
| Altes AutoCut (März 2026) | Kein Code wird übernommen. Nur Ideen: Szenenwechsel-Erkennung, Einstellungsgröße/Bewegung als Merkmale, Timeline als Ziel. |
| Bedienung | Chat-gesteuert wie die anderen Funktionen, keine GUI. Dateien werden nicht importiert, nur NAS-Pfade aus dem Transkript-Index genutzt. |
| Zielformat | Direkt in Resolve per Scripting-API (Studio 21.0.4 läuft, externes Scripting verifiziert). Zusätzlich XML-Export über Resolve für Premiere-Probecutter. |
| Spurlayout | V1 = FX3 (Ton-Kamera), V2 = a7IV synchron, V3 = B-Roll **ohne Audio**, A1 = FX3-Ton, A2 = a7IV-Ton **in der Timeline, aber stumm** (Clips deaktiviert, wie in den bestehenden Sync-Timelines des Users). |
| Sync | Waveform-Kreuzkorrelation in Python auf Audio der **Originale**; Resolve-Auto-Sync nur Rückfallebene. Kameras haben getrennte Uhren, Timecode-Sync unmöglich. |
| Proxies | Für alles Visuelle die vorhandenen Resolve-Proxies (`<Clip-Ordner>/Proxy/<stem>.mov`, 1920×1080); für alles mit Audio die Originale. |
| Bildformat | Aus dem Rotations-Flag der FX3-Datei: 90° → Hochformat 2160×3840, sonst 3840×2160. Bildrate aus der Datei. |
| Nicht-O-Ton-Zeilen (VO, reine Bild-Szenen, Grafik, Drohne) | Platzhalter-Lücke mit der Plan-Schätzung „~x s" plus Marker (Option A). |
| B-Roll-Auswahl | Bild-Spalte des Plans ist Hinweis mit Gewicht; AutoCut darf abweichen, wenn es Passenderes findet, und begründet die Abweichung (Option C). |
| Rollenverteilung | Claude entscheidet (Cutlist, B-Roll-Zuordnung), Code baut und prüft hart (Studio-Muster). |
| B-Roll-Index | Batch über die Anthropic-API mit eigenem Key (alter Key aus dem Schlüsselbund „niro_autocut" ist aktiv). |
| Stil | Schnitt-Profil aus der Blackmagic-Cloud-Bibliothek des Users (Stufe 4, ab 04.09.), Korrektur-Schleife danach. Kein Modell-Fine-Tuning (nicht verfügbar, nicht sinnvoll). |
| Bestandsschutz | Einziger Eingriff außerhalb von `tools/autocut/`: eine Trigger-Zeile in `CLAUDE.md`. NAS wird nur gelesen. |

## 1. Umfang und Bedienung

Trigger im Chat: **„AutoCut: <Kunde>/<Projekt>[/<Charge>]"** mit Unterbefehl:

| Unterbefehl | Stufe | Ergebnis |
|---|---|---|
| „Rohschnitt" | 1 | Timeline mit O-Tönen (V1/V2/A1/A2), Pausen, Platzhaltern, Markern |
| „B-Roll-Index" | 2 | Beschreibung aller B-Roll-Clips des Drehs (`broll_index.json`) |
| „B-Roll" | 3 | V3 gefüllt nach Plan, Index und Profil |
| „Profil" | 4 | Schnitt-Profil aus Cloud-Timelines (ab 04.09.) |

Anleitung: `tools/autocut/WORKFLOW-AutoCut.md`. Eingaben aus der Charge:
Cutter-Plan `Ergebnisse/O-Ton-Pläne/video-N-*.md`, `_intern/utterances.json`,
`_intern/transcripts_index.json`, `_intern/cache/<fingerprint>.scribe.json`.
Ausgaben: `_intern/autocut/` (Arbeitsdateien), `Ergebnisse/Rohschnitt/`
(Berichte, XML-Export), `Protokoll.md` (Eintrag pro Session), neue Bin +
Timeline im offenen Resolve-Projekt.

Nicht in Stufe 1–3: Musik, Erzähler-Stimme (VO), Multicam-Objekte, Grading,
Untertitel. Musik/VO können später als eigene Spuren ergänzt werden.

## 2. Ablage und Bestandsschutz

```
tools/autocut/
├── WORKFLOW-AutoCut.md      Chat-Ablauf für Claude (wie WORKFLOW-*.md der anderen Tools)
├── README.md · SETUP.md     Kurzdoku, Einrichtung
├── defaults.yaml            Standardwerte (Pause, Handles, B-Roll-Längen, Modell …)
├── .env                     ANTHROPIC_API_KEY (nicht versioniert)
├── .gitignore               venv, .env, work, caches
├── venv/                    Python 3.12; numpy, scipy, pillow, anthropic, rapidfuzz, pytest, pyyaml, python-dotenv
│                            + .pth auf tools/transcribe/src (niro_transcribe nur importiert, nichts installiert)
├── src/niro_autocut/
│   ├── charge.py            Charge öffnen, Pfade, Config, Schreib-Sperren
│   ├── media.py             ffprobe, Proxy-Suche, Format/Rotation, Fingerprint, Audio-Extraktion (Originale)
│   ├── plan.py              Cutter-Plan-Tabelle lesen (Zeilen, Sperren, Ziellänge)
│   ├── align.py             Zitat → Wortspanne (Normalisierung, lokales Alignment, Score)
│   ├── cutlist.py           Datenmodell + harte Prüfung der Cutlist
│   ├── sync.py              Waveform-Kreuzkorrelation, Kamerapaare, Konfidenz
│   ├── timeline_model.py    Beats → Record-Positionen (Pausen, Platzhalter, Handles)
│   ├── resolve_api.py       Verbindung, Media Pool (Dedupe per Pfad), Proxy-Link, Timeline-Bau, Marker, Export
│   ├── broll_index.py       Szenenwechsel, Frames, Kontaktbögen, Claude-Vision, Cache
│   ├── broll_plan.py        Modell + Prüfung der B-Roll-Zuordnung, Bau von V3
│   ├── report.py            report.md, broll-index.md, broll-plan.md, Protokoll-Eintrag
│   └── profile.py           (Stufe 4) Timelines lesen, Kennzahlen, Archiv
├── scripts/                 CLI-Einstiege je Schritt (siehe Abschnitt 6)
├── prompts/                 index-clip.md, place-broll.md, cutlist.md, profile-rules.md
├── profile/                 default.md + default.yaml (Startprofil), später je Videotyp
└── tests/                   pytest (Einheiten + Fake-Resolve), Fixtures aus MEK-Auszügen
```

Schreib-Bereiche (hart im Code erzwungen): nur `_intern/autocut/**`,
`Ergebnisse/Rohschnitt/**`, `Protokoll.md` (anhängen) und in Resolve nur
**neue** Bin/Timeline/Media-Pool-Einträge. Nie: bestehende Timelines ändern,
Dateien auf dem NAS schreiben, andere Tools anfassen.

## 3. Stufe 1 — Rohschnitt

### 3.1 Vorbereiten (`autocut_prepare.py <Charge> --video <plan.md>`)

1. Charge prüfen: Plan vorhanden, `utterances.json`, Index, Cache; NAS
   gemountet; Resolve läuft, Projekt offen, externes Scripting erreichbar.
2. Interview-Clips aus dem Index (Kategorie Interviews) auflösen: Original,
   Proxy (`<dir>/Proxy/<stem>.mov`), ffprobe: Bildrate, Rotation, Dauer,
   Frame-Zahl, Timecode. Proxy und Original müssen in Bildrate und Frame-Zahl
   übereinstimmen (Toleranz 1 Frame) — sonst Abbruch mit Meldung.
3. Format der Timeline: Bildrate + Auflösung aus der ersten FX3-Datei
   (Rotation 90/270 → Hochformat). Mischformate → Abbruch mit Meldung.
4. Kamerapaare je Interview-Ordner: FX3-Dateien (kamera_rolle „ton") und
   a7-Dateien (kamera_rolle „kontext"). → `_intern/autocut/media.json`.

### 3.2 Sync (`autocut_sync.py <Charge>`)

- Audio der **Originale** als 16-kHz-Mono-WAV nach `_intern/autocut/work/audio/`
  (ffmpeg, gecacht per Fingerprint).
- Für jedes FX3×a7-Paar im selben Interview-Ordner: Versatz per FFT-
  Kreuzkorrelation auf einer robusten Repräsentation (Onset-/Hüllkurve statt
  Rohsignal, damit Lavalier vs. Kameramikro vergleichbar sind). Konfidenz =
  Hauptpeak gegen zweitgrößten Peak. Ein Versatz gilt nur, wenn ein zweites,
  disjunktes Prüffenster denselben Wert (±1 Frame) liefert; sonst „unsicher".
- Ergebnis `sync.json`: pro Paar `offset_frames` (a7-Position = FX3-Position +
  offset), Konfidenz, überlappender Bereich in FX3-Sekunden. Paare ohne
  Überlappung werden verworfen. Drift wird gemessen (Versatz an Anfang vs. Ende
  des Überlappungsbereichs) und im Bericht ausgewiesen.
- Erste Prüfung: Johanna_Notaufnahme muss die 48 Frames aus der bestehenden
  Sync-Timeline des Users reproduzieren (±1 Frame).
- Rückfallebene: `MediaPool.AutoSyncAudio` (Waveform) — nur auf Anweisung.

### 3.3 Cutlist (Claude in der Session, Hilfsskript `autocut_find_quote.py`)

Claude liest Plan + Utterances und schreibt `_intern/autocut/cutlist.json`:

```json
{
  "video": "video-1-imagefilm-zwei-haeuser.md", "ziel_laenge_s": 185,
  "fps": 25, "format": "16:9", "pause_s": 1.0,
  "beats": [
    {"nr": "1", "szene": "Kaltstart-Teaser", "typ": "oton",
     "person": "Sandra", "rolle": "Fachkrankenschwester Notfallpflege",
     "clip": "<NAS-Pfad FX3_9557.MP4>",
     "cuts": [{"in_s": 217.32, "out_s": 219.61, "text": "Weil das mein Job ist. Das ist meins.", "hart_in": false, "hart_out": true}],
     "pause_after_s": 1.0, "bild_hinweis": "Gehaltenes Gesicht, roh, kein Logo",
     "kommentar": "OHNE Kontext, KEINE Bauchbinde …", "caption": null, "plan_dauer_s": 3},
    {"nr": "2", "szene": "VO: Vorurteil", "typ": "vo", "text": "Viele denken: …",
     "platzhalter_s": 6, "bild_hinweis": "Gesichter-Montage beider Häuser"}
  ],
  "sperren": [{"clip": "<Pfad FX3_9994.MP4>", "von_s": 16, "bis_s": 52, "grund": "Volkmarsen"}]
}
```

- Typen: `oton`, `vo`, `bild`, `grafik`. Ein Beat kann mehrere `cuts` haben
  (Auslassungen „[…]" → Teilschnitte, die direkt aneinander liegen).
- `autocut_find_quote.py <Charge> --clip <Datei> --text "…" [--near mm:ss]`
  liefert Kandidaten mit wortgenauen Zeiten (Anfang = erstes Wort, Ende =
  letztes Wort) und Score; bei Mehrfachtreffern entscheidet die Nähe zum
  mm:ss-Hinweis. Claude wählt und trägt ein.
- Handles: Standard 6 Frames vor dem ersten Wort, 8 Frames nach dem letzten;
  `hart_in`/`hart_out` = 0 Frames (Plan: „In hart", „Out HART"). Handles
  werden beim Bau begrenzt, damit kein Wort eines anderen Sprechers hineinragt.
- `pause_after_s` Standard aus Config (1,0 s); Plan-Hinweise wie „1–2 s STILLE"
  überschreiben.

### 3.4 Prüfen (`autocut_verify.py <Charge>`)

Harte Prüfungen, jede Verletzung stoppt vor dem Bau:
- Clip existiert (Original + Proxy), gehört zur Charge, hat ein Transkript.
- Jeder Cut enthält Transkript-Wörter des Clips (`verify_statement`-Logik),
  der Text stimmt mit den Wörtern im Intervall überein (Score ≥ Schwelle).
- Keine Überschneidung mit einer Sperre (auch nicht durch Handles).
- Dauer plausibel: Summe der Cuts eines Beats innerhalb 50–200 % der
  Plan-Schätzung „~x s" (Warnung, kein Abbruch, wenn kein Wert im Plan).
- Gesamtlänge (Cuts + Pausen + Platzhalter) gegen Ziellänge: Abweichung
  > 25 % → Warnung.
- Sync-Abdeckung: für jeden Cut ein a7-Paar mit Überlappung? Sonst Warnung
  (V2 bleibt leer).

### 3.5 Bauen (`autocut_build.py <Charge>`)

Per Resolve-API im offenen Projekt:
1. Bin `AutoCut/<Video-Kurzname>` anlegen (nur, wenn nicht vorhanden).
2. Media Pool: für jeden Clip zuerst vorhandenes Item per Dateipfad suchen
   (alle Bins); nur fehlende importieren; Proxy per `LinkProxyMedia`
   verknüpfen, falls noch nicht verknüpft.
3. Timeline `AutoCut <Video> <JJJJ-MM-TT HHMM>` mit Bildrate/Auflösung aus
   3.1; Spuren V1..V3, A1..A2 benannt („FX3", „a7IV", „B-Roll", „FX3 Ton",
   „a7IV Ton stumm").
4. Beats in Planreihenfolge: Cut → FX3 auf V1+A1 (startFrame/endFrame aus
   Cut inkl. Handles, recordFrame = laufende Position); a7 auf V2+A2 mit
   Offset aus `sync.json` (nur bei voller Abdeckung des Cuts), A2-Clips
   `SetClipEnabled(False)`. Teilschnitte eines Beats ohne Lücke, danach
   `pause_after_s` Lücke. Platzhalter = Lücke `platzhalter_s`.
5. Marker pro Beat am Beat-Anfang: Name „#nr Szene", Notiz = O-Ton/VO-Text,
   Bild-Hinweis, Kommentar, Caption; Farbe nach Typ (oton Blau, vo Gelb, bild
   Grün, grafik Lila, Warnung Rot). Zusätzlich Marker „V2 fehlt" wo nötig.
6. `_intern/autocut/timeline.json`: alle gesetzten Items mit Record-Positionen
   (Grundlage für Stufe 3 und für die Korrektur-Schleife).
7. Bericht `Ergebnisse/Rohschnitt/<video>-rohschnitt.md`: Beat-Tabelle
   (Nr, Szene, Quelle, In/Out, Dauer, V2 ja/nein), Sync-Tabelle, Warnungen,
   Gesamtlänge; Protokoll-Eintrag.

Optional: `autocut_export_xml.py` → `Timeline.Export(…, EXPORT_FCP_7_XML)`
nach `Ergebnisse/Rohschnitt/`.

## 4. Stufe 2 — B-Roll-Index (`autocut_index_broll.py <Charge>`)

- Umfang: alle Clips unter `…/Sortiert/B-Roll/**` beider Standorte (aus dem
  Footage-Root des Index abgeleitet); optional `--extra` für Mavic/Actioncam.
  Interviews sind ausgeschlossen. Fehlt ein Proxy: Original mit Warnung.
- Pro Clip:
  1. ffprobe (Proxy + Original): Dauer, fps, Rotation, Frames; Fingerprint
     des Originals als Cache-Schlüssel.
  2. Szenenwechsel im Proxy per ffmpeg `select='gt(scene,T)'` (T aus Config,
     Start 0,30) → Abschnitte.
  3. Frames: je Abschnitt Anfang+0,5 s, Mitte, Ende−0,5 s, dazu alle 2 s bei
     längeren Abschnitten; mindestens 4, höchstens 24 Frames pro Clip
     (bei längeren Clips Raster gestreckt). Skaliert auf 480 px Breite
     (Hochkant: 480 px Höhe), Zeitstempel als Text-Overlay (Pillow, weil
     drawtext in dieser ffmpeg-Installation fehlt).
  4. Kontaktbögen 4×3 Kacheln als JPEG (≤ 1600 px lange Kante), alle Bögen
     eines Clips in einer Anfrage.
  5. Claude (Modell aus Config, Standard `claude-opus-5`) mit festem
     Prompt-Teil (Prompt-Caching) und JSON-Schema als Structured Output.
  6. Cache `_intern/autocut/broll_index/<fingerprint>.json`; Lauf ist
     unterbrechbar und wieder aufnehmbar; 4–6 parallele Anfragen, Retry mit
     Backoff.
- Schema pro Clip: `datei`, `ordner` (Motiv-Ordner), `standort`, `dauer_s`,
  `orientierung`, `beschreibung_kurz` (≤ 12 Wörter), `beschreibung`,
  `motive[]`, `personen {anzahl, beschreibung, gesicht_erkennbar,
  blick_in_kamera}`, `einstellung` (Totale/Halbtotale/Halbnah/Nah/Detail),
  `kamerabewegung` (statisch/Schwenk/Fahrt/Handkamera/Gimbal/Drohne/Zoom),
  `tempo`, `stimmung`, `licht`, `abschnitte[] {von_s, bis_s, beschreibung,
  qualitaet 1–5, verwendbar}`, `maengel[]` (Unschärfe, Wackler, Blick in
  Kamera, Mikro/Crew im Bild, Logo/Marke, Über-/Unterbelichtung, zu kurz),
  `tags[]`, `eignung[]` (Opener, Detail, Übergang, Emotion, Beweis, Team,
  Ort), `qualitaet_gesamt 1–5`.
- Ausgaben: `_intern/autocut/broll_index.json` (aggregiert) und
  `Ergebnisse/Rohschnitt/broll-index.md` (je Ordner eine Zeile pro Clip).
- Kosten (Schätzung): ~2 Bögen × ~2.500 Token + Prompt je Clip; 464 Clips
  ≈ 10–20 € mit Opus 5. Laufzeit: Frames aus Proxies Minuten, API parallel
  ~30 min.

## 5. Stufe 3 — B-Roll-Einfügung (Claude + `autocut_place_broll.py <Charge>`)

- Eingaben: `cutlist.json`, `timeline.json` (Record-Positionen),
  `broll_index.json` (kompakt: kurz + Abschnitte + Tags + Mängel), Bild-Spalte
  je Beat, Plan-Regeln (z. B. „Nur S1!", Sperren, Tabus), Schnitt-Profil
  (`tools/autocut/profile/default.*`, ab Stufe 4 je Videotyp).
- Claude (Prompt `prompts/place-broll.md`) entscheidet pro Beat: abdecken
  ja/nein, welche Clip-Abschnitte, Reihenfolge, Dauern, Startpunkt relativ zum
  Beat; Abweichung von der Bild-Spalte nur mit Begründung. Ergebnis
  `_intern/autocut/broll_plan.json`:
  `[{beat_nr, items: [{clip, in_s, out_s, start_offset_s, grund,
  abweichung: bool, abweichung_grund}]}]`.
- Startprofil (bis Stufe 4 vorliegt), alle Werte in `defaults.yaml`:
  Sprecher beim ersten Auftritt ≥ 2,5 s sichtbar, bevor B-Roll kommt;
  B-Roll-Länge 2,0–5,0 s (Montage-Platzhalter 1,5–3,0 s, „Schnelle Cuts"
  → 1,0–2,0 s); kein Clip zweimal im Video; nicht zwei Clips aus demselben
  Motiv-Ordner direkt hintereinander; Standort-Regeln des Plans; keine
  Abschnitte mit Mängeln „Blick in Kamera", „Crew im Bild", „Logo/Marke";
  Beats > 8 s enden mit Sprecher im Bild (letzte 1,5 s frei); Platzhalter
  werden vollständig gefüllt; O-Ton-Beats höchstens zu 80 % abgedeckt.
- Prüfung im Code: Clip + Proxy existieren, In/Out innerhalb eines
  „verwendbar"-Abschnitts, Dauern in den Grenzen, keine Überschneidung auf
  V3, keine Wiederholung, Items innerhalb der Beat-Grenzen, keine Sperren.
- Bau: V3 per API, `mediaType = 1` (nur Video), Marker Gelb „B-Roll
  abweichend" bei Abweichungen. Bericht `Ergebnisse/Rohschnitt/<video>-broll.md`
  (pro Beat: gewählte Clips, Grund, Abweichung).

## 6. Fehlerfälle, Sicherheit, Betrieb

- Vorbedingungen mit klaren deutschen Meldungen: NAS nicht gemountet,
  Resolve nicht erreichbar / kein Projekt offen, Proxy fehlt, Transkript
  fehlt, mehrere `video-*.md` ohne `--video`, API-Key fehlt.
- Reihenfolge erzwungen: Prüfen vor Bauen; `build` verweigert bei
  ungeprüfter oder veränderter Cutlist (Hash in `verify.json`).
- Bau ist pro Timeline „alles oder nichts": bricht ein API-Schritt ab, wird
  die angefangene Timeline in „… FEHLER" umbenannt und im Bericht genannt;
  nichts wird automatisch gelöscht.
- Wiederholbarkeit: jeder Lauf erzeugt eine neue Timeline mit Zeitstempel;
  Caches (Audio, Index, Frames) werden wiederverwendet; `cutlist.json` und
  `broll_plan.json` dürfen von Hand geändert und neu geprüft/gebaut werden.
- Kosten-Schutz: Index meldet vor dem Lauf Clipzahl und Schätzung; `--limit`
  für Testläufe.
- Protokoll-Pflicht der Charge gilt: jeder Lauf schreibt einen Eintrag.

CLI (alle mit `tools/autocut/venv/bin/python`, Argument = Chargen-Ordner):
`autocut_prepare.py`, `autocut_sync.py`, `autocut_find_quote.py`,
`autocut_verify.py`, `autocut_build.py`, `autocut_export_xml.py`,
`autocut_index_broll.py`, `autocut_place_broll.py`,
`autocut_read_timelines.py` (Stufe 4).

## 7. Tests

- Einheiten (pytest, ohne Resolve/NAS): `align` (Auslassungen, Umlaute,
  Zahlwörter, Mehrfachtreffer mit Timecode-Nähe), `plan` (MEK-Tabelle →
  25 Zeilen / 15 O-Töne / Sperren), `cutlist` (Sperren-Überschneidung,
  fehlender Clip, Dauer-Plausibilität), `sync` (synthetische Signale mit
  bekanntem Versatz, Rauschen, Teilüberlappung, Drift → Versatz ±1 Frame,
  Konfidenz), `media` (Format aus Rotation), `timeline_model` (Pausen,
  Platzhalter, Handles-Begrenzung), `broll_index` (Frame-Raster,
  Kontaktbogen-Kacheln, Schema-Validierung), `broll_plan` (Überschneidung,
  Wiederholung, Grenzen), `resolve_api` gegen ein Fake-Resolve-Objekt
  (Aufrufreihenfolge, recordFrame-Berechnung, Dedupe).
- Integration (manuell, MEK): Johanna-Offset 48 Frames ±1; alle 15 O-Töne
  geprüft; Timeline-Länge ≈ 3:05 ± 15 s; V2-Abdeckung im Bericht; Index für
  10 Clips mit `--limit`, dann voll; V3 ohne Audio, keine Wiederholungen.

## 8. Stufe 4 — Schnitt-Profil (ab 04.09., eigener Plan)

- Cloud-Projekte per `LoadCloudProject` (Namensliste vom User), pro Projekt
  alle Timelines lesen (`GetItemListInTrack`, Source-Frames, Marker) und als
  OTIO/XML in `tools/autocut/profile/archiv/` sichern (dauerhaft, unabhängig
  von der Cloud). MP4s dienen dem Abgleich, welche Timeline final war.
- Kennzahlen je Videotyp (Format, Länge): Sprecher-Vorlauf vor erster
  B-Roll, B-Roll-Längenverteilung, Abdeckungsgrad, Pausen zwischen Aussagen,
  Rückkehr zum Sprecher, Schnitte auf Sprechpausen, Hook-/Endcard-Längen.
- Claude formuliert Regeln in Prosa + Beispiele (Aussage → Bildfolge) →
  `profile/<typ>.md` + `profile/<typ>.yaml` (überschreibt `defaults.yaml`).
- Korrektur-Schleife: `autocut_diff_timeline.py` vergleicht die vom User
  korrigierte Timeline mit `timeline.json`/`broll_plan.json` und schlägt
  Regeländerungen vor; Übernahme nur nach Freigabe.

## Risiken

- Wortgenaue Schnitte bleiben Rohschnitt; Atmer/Satzanfänge braucht ein
  Mensch.
- Proxy ≠ Original in Frames → Abbruch statt falscher Platzierung.
- a7-Abdeckung lückenhaft → V2 leer, sichtbar im Bericht.
- B-Roll-Passung ist Geschmack → Regeln + Review + Profil ab Stufe 4.
- Resolve-API-Eigenheiten (Record-Positionen, Spurindizes, Cloud-Projekte)
  → Fake-Resolve-Tests plus ein früher Live-Test mit zwei Clips.
