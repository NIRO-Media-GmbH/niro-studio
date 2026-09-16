# AutoCut — Kantenprüfung und Schnittbild (Spec)

Datum: 2026-09-16 · Status: Entwurf vom User freigegeben („Mach es so auf GitHub für meinen 2. Mac"), Umsetzung mit
Push auf `main`.

## Anlass

Am 16.09. wurde `browser-use/video-use` (MIT, Claude-Skill: Scribe → EDL → ffmpeg-Render → Selbstprüfung) für AutoCut
geprüft. Als Werkzeug passt es nicht (MP4 statt Resolve-Timeline, Regelkonflikte), zwei Ideen daraus schließen aber
eine Lücke:

- **Claude hört und sieht den gebauten Schnitt nicht.** Die Readbacks prüfen Positionen, nicht das Ergebnis. Die
  Fehler der letzten Wochen waren Render-Fehler: stumme Tonspuren (−180 dB trotz Pegel im Meter), Frame-Versatz
  (`GetSourceStartFrame` 1 Frame daneben), Schwarzframes an Wipes (bei Taxodia nur aus dem Plan gerechnet).
- **In Stufe 1 entscheidet Claude In/Outs nur aus Text und Zahlen.** Atmer, Blinzeln oder Kamerawackler an der Kante
  sind so nicht sichtbar.

Vorbild: `helpers/timeline_view.py` (Filmstreifen + Wellenform + Wörter als ein PNG) und der Vorschlag aus Issue
#162/#64 (Knackser- und Blitz-Prüfung je Schnittkante nach dem Render; dort nur vorgeschlagen, nicht gebaut).

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Gemessen wird woran? | Am **fertigen Export** der Timeline (Quick Export „H.265 Master" oder Export des Users), nicht an einer Nachbildung aus Proxys — nur so fallen Resolve-seitige Fehler auf. |
| Woher kommen die Schnitte? | Aus der Timeline in Resolve, **nur lesend** (`read_timeline` + `GetLeftOffset`), gespeichert als Schnappschuss `_intern/autocut/kanten_readback.json`. Mit `--readback <json>` läuft die Prüfung ohne Resolve. |
| Welche Timeline? | `--timeline`, sonst Schlüssel `timeline` der zuletzt geschriebenen (mtime) der Dateien `feinschnitt.json`, `finalize.json` (nur mit `status: ok`) und `build.json` in `_intern/autocut/`. |
| Welcher Export? | `--render`, sonst die neueste Datei in `<Charge>/Ergebnisse/Export/`, deren Name mit dem Timeline-Namen beginnt (Quick-Export-Standardname). |
| Export anstoßen? | **Nein.** Der Export bleibt der dokumentierte Review-Render (`tools/resolve/WORKFLOW-Resolve.md`, schreibend, nach Freigabe) oder ein Export des Users. |
| Passt der Export? | Bildrate und Frame-Zahl müssen exakt der Timeline entsprechen, sonst Abbruch (Exit 2) — ein veralteter Export würde falsche Befunde liefern. |
| Was ist ein Befund? | Ein **Verdachtsfall** mit Timecode und Schnittbild. Claude sieht sich jedes Bild an, bevor etwas geändert oder gemeldet wird. |
| Code-Herkunft | Eigene Umsetzung; Grundlayout und Idee nach video-use (MIT, „Copyright (c) 2026 Browser Use"), vermerkt im Dateikopf von `schnittbild.py`. |
| Nicht im Umfang | Export per Skript; stumme Einzelspur unter Musik (im Mix nicht messbar, nur Totalausfall als Tonloch); 30-ms-Tonblenden auf A1 (erst, wenn Knackser gemessen werden); Cutter-Schnitte ohne Timeline (Frame.io); HDR-Tonemapping. |

## Design

### 1. Schnappschuss (`kanten.py`)

`read_timeline` (`resolve_api.py`) liest je Item zusätzlich `left_offset` (`GetLeftOffset`) und `speed`
(`GetSpeed()["Percentage"]`); beides über `_safe`, fehlt es, steht `None`. `snapshot_from_readback(tl_dict, projekt)`
macht daraus:

```json
{"quelle": "resolve", "gelesen_am": "2026-09-16T15:02:11", "projekt": "Taxodia 09.26",
 "timeline": "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt", "fps": 25.0,
 "start_frame": 90000, "start_timecode": "01:00:00:00", "laenge": 6845,
 "spuren": {"V1": [{"name": "FX3_0222.MP4", "datei": "/Volumes/…/FX3_0222.MP4", "start": 0, "dauer": 60,
                    "quell_in": 3076, "aktiv": true, "tempo": 100.0}],
            "A1": […]}}
```

`start` ist relativ zum Timeline-Start, `quell_in` = Left-Offset in Timeline-Frames (Quellsekunde = `quell_in / fps`
bei 100 %). `laenge` = `end_frame − start_frame`. `quelle` ist `"resolve"` oder `"plan"` (von Hand erzeugt, z. B. aus
einem Bauplan — nur für Kalibrierung, im Bericht genannt).

Abgeleitet:
- **Bild-Schnitte:** alle Start- und End-Frames aktiver Items auf V-Spuren, ohne 0 und `laenge`, sortiert, eindeutig.
- **Ton-Schnitte:** dasselbe für A-Spuren.
- **Ton-aktiv-Maske:** je Frame, ob ein aktives A-Item liegt; erstes und letztes Frame jedes Items zählen nicht
  (Blenden).

### 2. Messen am Export (`kanten_medien.py`)

- **Bild:** ein ffmpeg-Durchlauf (`-hwaccel videotoolbox`, Rückfall Software) → Graustufen 96×54 je Frame
  (`scale=96:54:flags=area,format=gray`, rawvideo-Pipe). Daraus je Frame `mittel`, `streuung` und
  `diff` = mittlere absolute Differenz zum Vorframe. Cache: `_intern/autocut/work/kanten/<fingerprint>.npz`
  (Fingerprint wie im Transkript-Cache: Name, Größe, mtime).
- **Ton:** PCM float32 48 kHz stereo über ffmpeg-Pipe (nicht gecacht, schnell).

### 3. Befunde

Alle Schwellen stehen im Block `kanten:` in `defaults.yaml` und werden am Taxodia-Export kalibriert (Startwerte in
Klammern).

| Art | Regel | Nur an Schnitten? |
|---|---|---|
| **Schwarzbild** | Frames mit `mittel < schwarz_mittel_max` (24) **und** `streuung < schwarz_streuung_max` (4); zusammenhängende Läufe | nein, ganzer Export |
| **Schnipsel** | zwei harte Bildwechsel (`diff ≥ wechsel_diff_min`, 18) höchstens `schnipsel_max_frames` (2) Frames auseinander → dazwischen stehen 1–2 Frames; sind diese Frames alle schwarz, zählt nur das Schwarzbild (kein Doppelbefund) | nein; Kontext „an Schnitt"/„ohne Schnitt" (±1 Frame) |
| **Knackser** | je Ton-Schnitt: `spitze` = max \|Δ²x\| (zweite Differenz, je Kanal) im Fenster ±`knack_kante_ms` (10) um das Schnitt-Sample (`frame × 48000 / fps`); `umgebung` = 99. Perzentil von \|Δ²x\| in ±`knack_fenster_ms` (250) ohne ±`knack_kante_ms`; Befund, wenn `spitze ≥ knack_min` (0,02) **und** `spitze / max(umgebung, 1e-6) ≥ knack_faktor` (6) | ja |
| **Tonloch** | RMS über beide Kanäle je Frame-Fenster (`48000/fps` Samples) < `tonloch_dbfs` (−90 dBFS) in der Ton-aktiv-Maske; Läufe ab `tonloch_min_frames` (2) | nein; nur wo ein Tonclip liegt |
| **Wort angeschnitten** | je aktivem A-Item mit Transkript und Tempo 100 % oder unbekannt: Kante in Quellsekunden (`quell_in/fps` bzw. `(quell_in+dauer)/fps`); ein Wort mit `start < kante < end`, von dem mindestens `wort_min_ms` (80) abgeschnitten werden (Out-Kante: `end − kante`, In-Kante: `kante − start`) | ja (braucht keinen Export) |

**Transkript je Item:** `transcripts_index.json` der Charge; Treffer über den NFC-normalisierten Pfad (mit `path_map`),
sonst eindeutiger Dateiname. Kein Treffer → Item ohne Wortprüfung, im Bericht als Hinweis gezählt. Wörter aus
`_intern/cache/<fingerprint>.scribe.json` (Felder `text`, `start`, `end`, `speaker`; Wörter mit Länge 0 zählen nicht).

**Kontext je Befund:** Timecode (`start_timecode` + Frame, Format `HH:MM:SS:FF`), nächster Bild- und Ton-Schnitt mit
Abstand in Frames, Spur und Clipname der dort liegenden Items.

### 4. Schnittbild (`schnittbild.py`)

`zeichne(video, von_s, bis_s, ausgabe, *, woerter=(), bild_schnitte=(), ton_schnitte=(), marken=(), frames=10,
beschriftung=None, tc_start=None, fps=None)` → PNG 1920 px breit:

1. Kopfzeile: Datei, Bereich (Sekunden, bei `tc_start` zusätzlich Timecode), Beschriftung.
2. Filmstreifen: `frames` Bilder gleichmäßig im Bereich (ffmpeg `-ss` je Bild, `scale=320:-2`).
3. Pegelband in dBFS (−60 … 0, RMS je 10 ms) statt normierter Wellenform — Löcher und Pegelsprünge bleiben sichtbar.
4. Wörter über dem Pegelband in zwei Zeilen (weniger Überdeckung); Pausen ab 400 ms zwischen Wörtern schraffiert.
5. Senkrechte Linien: Bild-Schnitte (cyan), Ton-Schnitte (orange); Marken (rot, mit Kurztext) für Befunde.
6. Zeitleiste in Sekunden bzw. Timecode.

Wörter im Export-Modus: aus den A-Items des Schnappschusses auf die Export-Zeit umgerechnet
(`t_export = (wort − quell_in/fps) + start/fps`), nur innerhalb des Items.

### 5. Skripte

```
"$PY" "$TOOL/scripts/autocut_kanten.py" "$CHARGE" [--timeline "<Name>"] [--render "<Datei>"] [--readback "<json>"] [--ohne-bilder]
"$PY" "$TOOL/scripts/autocut_schnittbild.py" "$CHARGE" --clip <Dateiname> --von <s|mm:ss.s> --bis <s|mm:ss.s> [--frames N] [--ausgabe <png>]
"$PY" "$TOOL/scripts/autocut_schnittbild.py" "$CHARGE" --render "<Datei>" (--tc HH:MM:SS:FF | --frame <Frame ab Timeline-Start>) [--fenster 1.5] [--readback "<json>"] [--frames N] [--ausgabe <png>]
```

`autocut_kanten.py`:
1. Charge öffnen, Timeline und Export bestimmen (s. Entscheidungen).
2. Schnappschuss: `--readback` laden, sonst Resolve lesend verbinden, Timeline im offenen Projekt suchen
   (nicht gefunden → Exit 2 mit Projektname), lesen, `kanten_readback.json` schreiben.
3. Export prüfen (ffprobe: fps, Frame-Zahl) → Abweichung Exit 2.
4. Messen, Befunde bilden; ohne `--ohne-bilder` je Befund ein Schnittbild (±1,5 s) nach
   `_intern/autocut/work/schnittbild/kante_<nr>_<art>_<HH-MM-SS-FF>.png` (Bindestriche statt Doppelpunkte).
5. `_intern/autocut/kanten.json` (Parameter, Prüfumfang, Befunde, Messwert-Verteilungen), Bericht
   `Ergebnisse/Rohschnitt/<video>-kanten.md`, Protokoll-Eintrag.
6. Exit 0 = keine Befunde, 1 = Befunde, 2 = Voraussetzung fehlt.

`autocut_schnittbild.py` schreibt nur das PNG (Standard unter `_intern/autocut/work/schnittbild/`) und druckt den Pfad.
Alle Schreibziele liegen in den AutoCut-Schreibbereichen (`Charge.assert_writable`); Resolve wird nur gelesen.

### 6. Bericht `<video>-kanten.md` (`kanten_bericht.py`)

Kopf (Timeline, Schnappschuss-Quelle und Zeit, Export mit Frames/fps/Codec), Prüfumfang (Bild-/Ton-Schnitte, Items mit
Transkript, Items ohne Transkript), Befunde je Art, Tabelle `Nr | Art | Timecode | Frames | Wert | Kontext | Bild`,
Messwert-Verteilungen für die Kalibrierung (`diff` an Bild-Schnitten vs. übrige Frames; Knack-Verhältnis an
Ton-Schnitten: Median, 95. Perzentil, Maximum).

## Fehlerbehandlung

| Lage | Verhalten |
|---|---|
| Kein Export gefunden | Exit 2: „Kein Export für '<Timeline>' in Ergebnisse/Export — Review-Render (WORKFLOW-Resolve) oder --render" |
| Export ≠ Timeline (fps/Frames) | Exit 2 mit beiden Zahlen: „Export ist nicht aktuell" |
| Resolve nicht erreichbar / Timeline nicht im offenen Projekt | Exit 2 mit offenem Projektnamen; Hinweis `--readback` |
| ffmpeg-Fehler beim Dekodieren | Exit 2 mit ffmpeg-Meldung (letzte Zeilen) |
| Clip ohne Transkript | kein Abbruch; Hinweis im Bericht |
| Befund-Bild scheitert | kein Abbruch; Befund ohne Bild, Warnung |

## Tests (pytest, ohne Resolve)

- `test_kanten.py` mit synthetischen Daten: Schwarzlauf; Schnipsel (Wechsel 1 Frame auseinander → Befund, 5 Frames →
  keiner); Knackser (Sprung genau am Schnitt-Sample → Befund; ohne Sprung → keiner; Sprung 200 ms neben dem Schnitt →
  keiner an diesem Schnitt); Tonloch (3 stille Frames in der Maske → Befund; außerhalb der Maske oder am Item-Rand →
  keiner); Wortkanten (Kante 120 ms im Wort → Befund; in der Pause → keiner; Wort mit Länge 0 → keiner); Schnappschuss
  aus einem `read_timeline`-Dict (absolute → relative Frames, Left-Offset); Timecode-Format; Schnitt-Listen und Maske.
- `test_schnittbild.py`: PNG aus einem mit ffmpeg erzeugten 2-s-Testclip (lavfi `testsrc2` + `sine`), mit Wörtern
  (auch Länge 0), Schnittlinien außerhalb des Bereichs werden ignoriert.
- `test_kanten_script.py`: Ende-zu-Ende mit synthetischem Export (ffmpeg: 3 s, 25 fps, 160×90, ein schwarzes Frame,
  Ton mit Sprung an einem Schnitt) und `--readback`-Schnappschuss → Exit 1, erwartete Befunde, Bericht und JSON
  geschrieben; falsche Frame-Zahl → Exit 2.
- `test_resolve_api.py`: `read_timeline` liefert `left_offset` und `speed` (Fake um `GetLeftOffset` erweitert).

## Doku

- `WORKFLOW-AutoCut.md`: Unterbefehl „Kanten" in der Tabelle; eigener Abschnitt „Kantenprüfung"; Abnahme Stufe 6 mit
  Pflicht-Kantenprüfung und der Regel „Prüfen → beheben → neu exportieren, höchstens 3 Runden, dann offen melden";
  Stufe 1 Schritt 3: bei unklaren In/Outs Schnittbild ansehen; Fehlerbilder; Ausgabe-Konvention.
- `README.md`: Stufen-Tabelle, Schnellstart, Aufbau, Arbeitsdateien.
- `defaults.yaml`: Block `kanten:` mit kalibrierten Werten und Kommentar zur Herkunft.
- `CLAUDE.md`: AutoCut-Zeile um „Kantenprüfung" ergänzen.

## Reihenfolge

Code + Tests → Kalibrierung am Taxodia-Export (Schnappschuss aus Resolve, falls „Taxodia 09.26" geöffnet ist, sonst
Soll-Stand aus `feinschnitt_bauen.py`) → Schwellen in `defaults.yaml` → Doku → Commit nur eigener Pfade → Push `main`.
