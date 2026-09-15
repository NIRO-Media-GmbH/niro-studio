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
| `broll_einsetzen.py` | Auswahl-Shots auf V3 der roh-Timeline, Marker, Readback (3a) |
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
  Color, Begradigen, Werkzeuge. Namen nicht ändern.
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
