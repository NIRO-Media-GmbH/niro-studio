# AutoCut-Vorlagen: Feinschnitt (Stand 15.09.2026)

Chargen-Skripte für **Stufe 3a „B-Roll aus Auswahl"** und **Stufe 6 „Feinschnitt"**, entstanden im
Taxodia-Erklärvideo (`projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/`, Originale mit
echten Werten in `_intern/`, Ablauf und Zahlen im `Protokoll.md`). Die Vorlagen sind neutralisiert, aber
**nicht getestet**: Es sind Kopiervorlagen, keine AutoCut-Stufen mit Tests. Ablauf, Regeln und Reihenfolge stehen in
`../WORKFLOW-AutoCut.md` (Abschnitte „Stufe 3a" und „Stufe 6").

## Benutzen

    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"
    cp -Rn "/Users/jansantos/NIRO Studio/tools/autocut/vorlagen/feinschnitt/." "$CHARGE/_intern/"

1. **Kopieren** mit `-n`, damit vorhandene Chargen-Skripte nie überschrieben werden. Die Ordnerstruktur spiegelt
   `_intern/`: Die Skripte laden sich gegenseitig über relative Pfade.
2. **ANPASSEN-Block** oben in jeder Datei füllen. Er enthält Projektname = Schreibfreigabe, Timeline-Namen und die
   Tabellen, die Claude in der Session entscheidet. Werte mit „Standard (15.09.)" sind erprobte Regelwerte.
   Bleiben Pflicht-Tabellen leer, bricht das Skript ab, bevor es schreibt.
3. **Starten** aus dem Chargen-Ordner: `tools/autocut/venv/bin/python _intern/<skript>.py`.
   - Ohne Flag läuft nur ein Probelauf. Geschrieben wird erst mit `--bauen` bzw. `--ausfuehren`;
     `grading_anwenden.py` braucht `--test`/`--alle`, `kalibrierung_resolve.py`/`pruefung_resolve.py` einen Schritt.
   - Ohne Flag schreiben nur `werkzeuge/schreibtest*.py` und `begradigen/karte_nachsetzen.py`.
   - Die vier OpenCV-Skripte (siehe unten) laufen mit `tools/transcribe/venv/bin/python`.
4. **Swift-Helfer** einmal je Charge bauen (Befehl im Kopfkommentar), z. B.
   `swiftc -O _intern/gesichtscheck/faces.swift -o _intern/gesichtscheck/faces`.

Vorlagen, die in Resolve schreiben, gehen so vor:
- Projektname gegen `PROJEKT` prüfen und nur eigene Objekte anfassen.
- Timeline und Bin des Users wiederherstellen, wo sie sie wechseln.
- Das Ergebnis zurücklesen.

Reine Mess- und Analyseskripte (Musik, SFX-Messung, Color-Fit, Linien, Kalibrier-Auswertung) arbeiten ohne
Resolve. Resolve-Regeln: `tools/resolve/WORKFLOW-Resolve.md`.

## Inhalt

| Datei | Zweck |
|---|---|
| `find_tc.py`, `plan_rows.py` | Wortgenaue In/Out je Phrase aus dem Scribe-Cache; Plan-Zeilen mit Dauer und Sprecherfolge → `plan_rows.json` |
| `cutlist_aus_plan.py` | Cutlist mit einem Cut je „+"-Bereich, `hart_in`/`hart_out`, Sperren (ersetzt den Draft bei Innenschnitten) |
| `broll_auswahl.py` | Auswahl-Timeline des Users nur lesen, Kontaktbögen aus dem echten In/Out (3a) |
| `broll_einsetzen.py` | Auswahl-Shots auf V3 der roh-Timeline, Marker, Brennweitenregel mit digitalem Zoom (7. Spalte `zoom`), Readback (3a) |
| `audio_normalisieren.py` | A1 True Peak −3 dBTP je Clip + Voice Isolation, ebur128-Gegenmessung (6a) |
| `grafik_review.py`, `grafik_einsetzen.py` | Remotion-Standbilder über dem echten Bild; Alpha-Render als ein Clip auf V4 (6b) |
| `musik_analyse.py`, `musik/sprung_berechnen.py`, `musik/mischung_pruefen.py` | Tempo/Abschnitte, beat-genaue Sprünge, Offline-Mischung nach BS.1770 (6c) |
| `feinschnitt_bauen.py` | Feinschnitt-Timeline V1–V4/A1–A5 mit Schwarzframe-Rechnung (6d); wird von vielen Vorlagen als Modul `fb` geladen |
| `gesichtscheck/gesichtscheck.py`, `gesichtscheck/faces.swift` | Grafik gegen Gesichter (Apple Vision) (6e) |
| `feinschnitt_umbau.py` | ältere Timelines für Handarbeit umbauen (6f) |
| `sfx/sfx_inventar.py` … `sfx/sfx_ton_render.py` | Inventar, Messung, Spektren, Plan, Prüfmischung, Vorprüfung, Einsatz, Readback, Ton-Render (6g); `inventar.beispiel.json` |
| `color/grading_anwenden.py`, `color/broll_trims.py`, `color/skripte/*` | Grading-Analyse bis `grading_vorschlag.json`, CDL + LUT je Item, B-Roll-Trims (6h); `grading_vorschlag.beispiel.json` |
| `begradigen/*` | Kameralage aus Sony-rtmd, Kalibrierung des Resolve-Transforms, Begradigung, Kopfposition A/B, Nachbesserung (6i) |
| `werkzeuge/fenster.swift` | Wiedergabe in Resolve erkennen (Vollbild-Viewer), ohne Fokuswechsel — braucht Bildschirmaufnahme-Recht |
| `werkzeuge/ping*.py`, `zustand.py`, `stand_lesen.py`, `voll_readback.py` | Erreichbarkeit, Spurzustand, Stand sichern, Readback gegen den Feinschnitt-Plan |
| `werkzeuge/schreibtest*.py`, `renderstatus.py`, `render_formate.py` | Schreibsperre erkennen, Render-Jobs und -Formate lesen |

**OpenCV-Skripte** (transcribe-venv): `begradigen/raster_erzeugen.py`, `linien_messen.py`,
`kalibrierung_auswerten.py`, `pruefung_auswerten.py`.

## Abhängigkeiten zwischen den Vorlagen

- **`feinschnitt_bauen.py` (`fb`)** liefert `lade`, `plan`, `bericht`, `grafik_elemente`, `tc`, `AC`, `PROJEKT`,
  `ENDE`, `GRAFIK`, `MUSIK_PLAN`, `PUNCH_IN`, `ALPHA_JSON`, `DECKEND_AB`. Nutzer: Musik, SFX, Gesichts-Check,
  Color, Begradigen, Werkzeuge. Namen nicht ändern. `BROLL` hat eine optionale 7. Spalte `stabil` (True/False);
  ohne sie kommt der Vorschlag aus `_intern/autocut/telemetrie.json` (`autocut_telemetrie.py` vorher laufen
  lassen): Stativ/Gimbal bleiben unstabilisiert, Handkamera mit `wackeln` > `telemetrie.ruhig_max_px` wird
  stabilisiert. Der Probelauf druckt je Shot Vorschlag und Grund; `roll_grad` > 2° erscheint als „schief".
  Die optionale 8. Spalte `zoom` legt den digitalen Zoom fest (1.0 = keiner); ohne sie setzt die Brennweitenregel aus
  `telemetrie.json` einen Zoom, wenn zwei direkt anschließende Shots dieselbe KB-Brennweite hätten (Spec 2026-09-21).
- **`color/grading_anwenden.py`**: `cdl_fuer`, `resolve_cdl`, `LUT_REL` und die Tabelle `GRUPPEN` braucht auch
  `begradigen/pruefung_resolve.py`.
- **`color/skripte/colorlib.py`** wird genutzt von `begradigen/linien_messen.py` und den Color-Skripten.
- **`begradigen/parameter_berechnen.py` (`pb`)**: `resolve_h` (Transform-Modell) braucht auch der Gesichts-Check.

## Abweichungen von den Taxodia-Originalen

- Personen, Clips, Orte, Musiktitel, Projekt- und Timeline-Namen sind Platzhalter; Plan-Tabellen sind leer.
- Der Pfad zu `tools/autocut/src` wird relativ zur Datei gesucht, nicht fest verdrahtet (unabhängig vom Rechner).
- Probelauf als Standard auch bei `audio_normalisieren.py`, `grafik_einsetzen.py` und
  `begradigen/aufraeumen_begradigen.py`. Pflicht-Modus bzw. -Schritt bei `grading_anwenden.py`,
  `pruefung_resolve.py` und `kalibrierung_resolve.py`.
- `alpha_v2.json` heißt jetzt `alpha_<Render>.json` (eine Messung je Render). Musik-Konstanten heißen `MUSIK_1..3`.
- Neu zusammengesetzt aus Befehlen der Session: `musik/sprung_berechnen.py`, `sfx/sfx_inventar.py`,
  `sfx/sfx_vorpruefung.py`, `sfx/sfx_readback.py`, `sfx/sfx_ton_render.py`, `begradigen/proben_waehlen.py`,
  `raster_erzeugen.py`, `pruefung_auswerten.py`, `kopf_oben_messen.py`.
- **SFX-Pegel:** Die Vorlage rechnet noch mit dem ersten, zu leisen Standard (Spitze ≤ −26 dBFS unter Sprache).
  Richtwert seit der Taxodia-Korrektur ist momentan nicht unter −30 LUFS — siehe Workflow 6g.

## Offene Befunde

**A1-Pegel nach True Peak je Clip (Klebl Recruiting, 25.09.2026).** Nur notiert, die Vorlagen sind nicht geändert.

- **Befund:** `NormalizeAudioLevel` mit True Peak −3 dBTP je A1-Clip (6a, 6d) richtet jeden Satz an seiner lautesten
  Spitze aus, nicht an seiner Lautheit.
  - Ein Satz mit einer Einzelspitze bekommt dadurch zu wenig Gain. Beispiel: Jonas „für einen Freund“, Spitze
    −10,9 dBFS, lag nach dem Bau 7,7 LU unter den anderen Beats.
  - Die Spitze begrenzt dann auch den Gesamtpegel: Der Export von Video 03 kam auf −20,2 LUFS, die anderen auf
    −17,1 bis −18,9 LUFS.
  - Dieselbe Regel gilt in Stufe 5 (`ton.py`/`finalize.py`).
- **Umgangen** in der Charge-Kopie `projects/Klebl/Recruiting-Videos/2026-09 Dreh Edeka Baustelle 22.09/_intern/feinschnitt_bauen.py`
  (Abschnitt nach `NormalizeAudioLevel`):
  - Plan-Schlüssel `a1_pegel` (dB je Beat, zusätzlich zur Normalisierung): Beat 3 +4 dB, Beat 5 +3 dB.
  - `ton_gesamt_db` (−2,6 dB auf A1; die Musik-/SFX-Pegel im Plan enthalten den Versatz schon) hält den True Peak
    der Mischung unter −1,5 dBTP (gemessen −1,6 dBTP).
  - Readback je Item in `feinschnitt.json` → `a1_pegel_korrektur`.
- **Vorschlag für `feinschnitt/feinschnitt_bauen.py`** (6d, sinngemäß auch `audio_normalisieren.py`, 6a):
  1. Im ANPASSEN-Block `A1_PEGEL: dict[str, float] = {}` (Beat → dB) und `TON_GESAMT_DB = 0.0` ergänzen.
  2. Nach `NormalizeAudioLevel` je A1-Item `AudioVolume` um `A1_PEGEL[beat] + TON_GESAMT_DB` erhöhen. Den
     Readback wie in der Klebl-Kopie in `feinschnitt.json` schreiben.
  3. `musik/mischung_pruefen.py` um die Sprachlautheit je Beat erweitern (Stem wie bisher, BS.1770 je A1-Item).
     Beats, die deutlich unter dem Median liegen (etwa mehr als 3 LU), als Vorschlag für `A1_PEGEL` melden:
     Anhebung bis zum Median, begrenzt durch die Beat-Spitze.
  4. Den nötigen Gesamtversatz, damit die Mischung höchstens −1,5 dBTP erreicht, als Vorschlag für `TON_GESAMT_DB`
     melden. Die Musik-/SFX-Pegel im Plan um denselben Wert verschieben.
  5. Weiter gedacht, ohne Spec-Entscheidung: je Clip auf Lautheit normalisieren (Modus „ITU-R BS.1770-4“ statt
     „True Peak“) und True Peak nur als Obergrenze prüfen. Das betrifft auch Stufe 5 und den User-Standard vom
     04./15.09. („True Peak −3 je FX3-Clip“), also nur mit dem User entscheiden.
