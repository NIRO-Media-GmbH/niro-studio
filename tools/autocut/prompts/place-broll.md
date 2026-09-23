# B-Roll einfügen v2 — Arbeitsanleitung für Claude (AutoCut Stufe 3)

Gilt für „AutoCut: <Kunde>/<Projekt>[/<Charge>] B-Roll" nach `autocut_build.py` (roh-Timeline steht),
`autocut_index_broll.py` und `autocut_index_sections.py` (Nachlauf, Pflicht). Ergebnis: `<Charge>/_intern/autocut/broll_plan.json`
(Version 2). Der Code prüft hart (`--verify-only`), baut V3 in die roh-Timeline und das Finalisieren macht daraus die End-Timeline.

    TOOL="/Users/jansantos/NIRO Studio/tools/autocut"
    PY="$TOOL/venv/bin/python"
    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"

| Skript | Zweck |
|---|---|
| `"$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --compact` | kompakten Index mit Abschnittsfeldern schreiben (Schritt 1) |
| `"$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --raster` | Fenster + Strecken berechnen → `raster.json`, `<video>-raster.md` (Schritt 2, nach Fenster-Änderungen wiederholen) |
| `"$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --verify-only` | harte Prüfung → `broll_verify.json` (Schritt 5) |
| `"$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE"` | prüfen und V3 bauen (Schritt 7, nach Freigabe) |

## Eingaben (nur lesen)

- `cutlist.json` (Beats, Bild-Spalte, Kommentare, Sperren), `timeline.json` (Beat-Positionen), `raster.json` (Fenster und
  Strecken mit den Beats darunter, O-Ton-Texten und Hinweisen), `broll_index_kompakt.json` (je Clip `ref`, `fps`, verwendbare
  `abschnitte[{von_s,bis_s,kurz,q,einstellung,perspektive,brennweite,richtung,motiv,brennweite_mm,zoom,bewegungsart,haltung,bewegung_spitzen}]`
  — die letzten fünf sind **gemessen**, nicht Claudes Einschätzung: `brennweite_mm` (KB-Median im Abschnitt), `zoom`
  (keiner/langsam/schnell), `bewegungsart`, `haltung` und `bewegung_spitzen` (`[t_s, bewegung]` der lokalen
  Bewegungs-Maxima, `t_s` = Fenster-Start); ohne Telemetrie `None`/leer, Claudes Klasse `brennweite` bleibt daneben
  bestehen), `profile/default.md` + `.yaml`, Plankopf.

## Aufbau von broll_plan.json (v2)

```json
{"version": 2, "video": "video-1-….md",
 "fenster": [{"beat_nr": "1", "voll": true, "grund": "Hook"},
             {"beat_nr": "18", "offset_s": 0.0, "dauer_s": 2.5, "grund": "erster Auftritt Marcel"},
             {"beat_nr": "18", "offset_s": 11.0, "dauer_s": 2.0, "grund": "Peak-Satz im Bild"}],
 "strecken": [
  {"nr": 1, "szenen": [
    {"ordner": "Standort 1/Notaufnahme", "grund": "Welt 1 akut als Szene", "ausnahme": "",
     "shots": [
      {"clip": "Standort 1/Notaufnahme/FX3_9503.MP4", "in_s": 2.0, "out_s": 5.0, "tempo": 1, "grund": "Totale Schockraum, Establishing"},
      {"clip": "Standort 1/Notaufnahme/FX3_9545.MP4", "in_s": 0.5, "out_s": 2.0, "tempo": 2, "grund": "Detail Monitor, 2× ruhig"},
      {"clip": "Standort 1/Notaufnahme/FX3_9506.MP4", "in_s": 8.5, "out_s": 11.0, "tempo": 1, "grund": "Halbnah Pflegekraft am Bett"}]}]}]}
```

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `version` | ja (Wert 2) | Schema-Version von `broll_plan.json`; der Code prüft hart auf `2` |
| `video` | ja | Dateiname des Plans (`cutlist.json`-Feld `video`, z. B. „video-1-….md") |
| `fenster[].beat_nr` | ja | O-Ton-Beat; Einträge ersetzen das Standardfenster dieses Beats (mehrere je Beat erlaubt) |
| `fenster[].offset_s`, `dauer_s`, `voll` | `dauer_s` oder `voll` | Beginn relativ zum Beat-Anfang, Länge 1,5–4,0 s, oder `voll: true` = ganzer Beat |
| `strecken[].nr` | ja | Nummer aus `raster.json`; jede Strecke des Rasters muss vorkommen |
| `szenen[].ordner` | ja | „Standort/Motiv-Ordner"; alle Shots der Szene aus diesem Ordner (sonst `ausnahme`) |
| `szenen[].ausnahme` | bei < 3 Shots / Ordnermix | Grund, z. B. „Plan: Wechselschnitt beider Häuser" |
| `shots[].clip`, `in_s`, `out_s` | ja | `ref` aus dem kompakten Index; Quellbereich in Echtzeit-Sekunden, in einem verwendbaren Abschnitt |
| `shots[].tempo` | nein | 1 (Standard), 2 (nur 50p-Clips), 4 (nur 100p-Clips); Timeline-Dauer = (out−in)·tempo |
| `shots[].grund`, `abweichung`, `abweichung_grund` | `grund` erwartet | wie bisher; Abweichung von der Bild-Spalte nur mit Grund (gelber Marker) |

Nur diese Felder — `strecken[].von_s`/`bis_s` (falls in `raster.json` vorhanden) sind reine Lese-Hinweise auf die
Streckengrenzen in Timeline-Sekunden; der Code ignoriert sie beim Prüfen und Bauen, sie müssen nicht geschrieben werden.
Beats ohne `fenster`-Eintrag bekommen das Standardfenster (Hook/„Gehaltenes Gesicht"/„Bookend"/< 3 s = voll;
erster Auftritt 2,5 s; sonst 2,0 s).

## Ablauf

1. **Index kompakt** (`--compact`) lesen: je Ordner die Clips mit `q ≥ 4`, ruhiger Bewegung, ohne Mängel merken — und je Ordner,
   welche **Einstellungen** vorhanden sind (eine Szene braucht ≥ 3 verschiedene: z. B. Totale + Halbnah + Detail).
2. **Raster** (`--raster`) lesen: Gesichtsanteil (Ziel 15–20 %), Fenster, Strecken mit Beats/Texten/Hinweisen. Fenster nur
   ändern, wenn nötig (Peak-Fenster, Anteil außerhalb des Ziels); danach `--raster` wiederholen. Eine Strecke unter
   2,0 s (kein Shot ist kürzer) und ein Gesichtsanteil außerhalb der harten Grenze 12–23 % meldet `--raster` selbst
   als Fehler in `raster.json` (`fehler`) — eigenes Fenster per `offset_s` weiter nach hinten schieben oder `voll`
   statt `dauer_s` setzen, dann erneut `--raster`.
3. **Je Strecke** Szenen bauen: Thema aus den Beats darunter (Bild-Spalte zuerst, Plan-Regeln „Nur S1!", Sperren, Tabus),
   Ordner wählen, 3+ Shots mit Einstellungswechsel und Cut-Flow (nie Einstellung + Perspektive + Brennweite gleich, keine
   fast gleichen Kadragen; mit Telemetrie zusätzlich: kein Schnitt auf dieselbe KB-Brennweite und keine schnelle Zoomfahrt
   im genutzten Bereich anschneiden), Längen nach Profil, `tempo` nach Kriterien. Die Shot-Summe soll die Strecke etwa
   füllen; der letzte Shot wird vom Code auf die Reststrecke gesetzt (bleibt in seinen Längen-Grenzen: lieber einen Shot
   mehr planen). Kein Clip zweimal im Video. Ausnahmen nur mit Text.
4. **Schreiben** (`ensure_ascii=False`, `indent=1`).
5. **Prüfen** (`--verify-only`), Fehler beheben (Tabelle unten), erneut prüfen.
6. **Dem User vorlegen:** Gesichtsanteil, Zahl der Strecken/Szenen/Shots/Zeitlupen, Ausnahmen und Abweichungen mit Grund,
   offene Motive. Erst nach Freigabe bauen.
7. **Bauen** (ohne Flag), dann `scripts/autocut_finalize.py` für Pegel/Zeitlupe/End-Timeline.

| Meldung | Abhilfe |
|---|---|
| `Strecke n … fehlt im Plan` / `ist leer` | jede Raster-Strecke mit Szenen füllen (Schwarz ist verboten) |
| `ragt über das Streckenende` / `bleibt keine Zeit` | Shots kürzen oder einen weglassen; Summe ≈ Streckenlänge |
| `Gesichtsanteil … außerhalb` | Fenster kürzen/verlängern oder Peak-Fenster streichen; `--raster` neu |
| `tempo 2 braucht 50 fps` | nur Clips mit passender `fps` verlangsamen |
| `dieselbe Einstellung …, Perspektive … und Brennweite` | Shot tauschen (andere Einstellung oder Perspektive) |
| `schneiden dieselbe KB-Brennweite` (nur mit Telemetrie) | anderen Shot oder Bereich wählen — direkt aneinanderstoßende Shots brauchen unterschiedliche KB |
| `schneller Zoom im genutzten Bereich` (nur mit Telemetrie) | anderen Bereich wählen oder `abweichung` mit Grund setzen |
| `nur k Shots — eine Szene braucht mindestens 3` | Shot ergänzen oder `ausnahme` mit Grund |
| `Shots aus verschiedenen Ordnern` | Szene teilen oder `ausnahme` (Wechselschnitt) |
| `Abschnittsfelder fehlen` | `autocut_index_sections.py` laufen lassen |
| `wird zweimal verwendet` / `verwendbar` / `Mangel` / `Sperre` / `Nur S1` | wie bisher: anderer Clip/Bereich |

## Eiserne Regeln

Nur `broll_plan.json` schreiben; NAS nur lesen; Plan und Cutlist nicht ändern; keine Bilder erfinden (Kontaktbogen/Abschnittsbogen
ansehen bei Zweifel); Sperren, Standort-Regeln, Mängel, Fenster-Grenzen und Szenen-Regel nicht verhandelbar; Ausnahmen und
Abweichungen im Abschluss nennen; Bauen erst nach Freigabe.
