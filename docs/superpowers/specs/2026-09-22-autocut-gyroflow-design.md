# AutoCut — Gyroflow-Stabilisierung für B-Roll (Spec)

Datum: 2026-09-22 · Status: entworfen, nicht umgesetzt. Baut auf der Kamera-Telemetrie
(`docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`) und der Brennweitenregel
(`docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md`) auf, beide umgesetzt und auf main.

## Anlass

Baustein 6d stabilisiert B-Roll heute mit `TimelineItem.Stabilize()` — einem rein optischen Verfahren. Gleichzeitig liest
die Telemetrie seit 21.09. die Sony-rtmd-Spur mit 2000 Hz aus, also genau die Gyrodaten, aus denen Gyroflow eine deutlich
bessere Stabilisierung rechnet (Rolling-Shutter-Korrektur, echte virtuelle Kamera statt Bildabgleich).

Zwei Bedingungen des Users (Chat 22.09.): **nicht alle Rawfiles durch Gyroflow**, und **keine doppelte Datenhaltung**.
Der naheliegende Gyroflow-Weg — jeden Clip rendern und als `_stabilized.mov` ablegen — verletzt beide.

## Machbarkeit (gemessen 22.09.)

| Prüfung | Ergebnis |
|---|---|
| Gyroflow-CLI | `/Applications/Gyroflow.app/Contents/MacOS/gyroflow` v1.6.1, läuft headless (Exitcode 0), GUI startet nicht mit |
| OFX-Plugin | v1.3.0 in `/Library/OFX/Plugins/Gyroflow.ofx.bundle`, installiert 01.11.2023 — **veraltet**, trägt `com.apple.quarantine` |
| Projekt-Export a7 IV | `--export-project` schreibt die `.gyroflow`-Datei und **rendert nicht**; 0,74 s für einen 0,48-s-Clip |
| Objektivprofil | **automatisch** aus den Clip-Metadaten: `camera_model: ILCE-7M4`, `lens_model: E 70-180mm F2.8 A065 (70.00 mm)`, `calibrated_by: Sony`, `official: true`, `distortion_model: "sony"` — Sony legt eigene Verzeichnungsdaten in die Datei, kein manuelles Profilsuchen |
| Synchronisation | entfällt: `has_accurate_timestamps: true` |
| Zoom-Konvention | Prozent, 100 = kein Beschnitt; `stabilization.max_zoom` (Standard 130) deckelt ihn, `gyro_source.adaptive_zoom_fovs` hält den gerechneten Verlauf |
| Resolve nativ | kein Ersatz — Gyro-Stabilisierung gibt es in Resolve nur für BRAW (Changelog 19.1.2), nicht für Sony-rtmd |

**Größe der Sidecar-Datei**, gemessen an `a7MK4_20260601_1935.MP4` (21,12 s, 402 MB):

| Export-Typ | Größe | Anteil am Video | Selbstgenügsam |
|---|---|---|---|
| 1 — ohne Gyrodaten | 8,0 KB | 0,002 % | nein (absoluter Pfad zurück aufs Video) |
| **2 — mit Gyrodaten** | **1,1 MB** | **0,27 %** | **ja** |
| 3 — verarbeitete Gyrodaten | 4,6 MB | 1,1 % | ja, aber 4× teurer ohne Gegenwert |

## Entscheidungen (Chat 22.09.)

| Frage | Entscheidung |
|---|---|
| Umfang | **Alle genutzten B-Roll-Shots**, nicht nur die mit `stabil`-Flag. Nur die, die im Feinschnitt-Plan vorkommen — nie das ganze Rohmaterial. |
| Rand-Haushalt | **Gyroflow zuerst**, aber über einen Deckel statt über eine Rückkopplung (Abschnitt 4): Gyroflows `max_zoom` wird so gesetzt, dass der Brennweitenregel ihre 1,25× garantiert bleiben. `digitalzoom_max` (1,5) bleibt unverändert. |
| Ablage | **Neben der Mediendatei** (`<clip>.gyroflow` im selben Ordner wie die MP4). Reist mit dem Footage auf SSD und NAS; das Plugin findet sie per „Load for current file" auch bei Handarbeit. Läuft nicht über `studio_abgleich.sh`. |
| Export-Typ | **2 (mit Gyrodaten).** Typ 1 wäre 130× kleiner, müsste aber bei jedem Projektöffnen und Render die Gyrospur aus dem Original nachlesen — bei 8-GB-FX3-Dateien übers NAS der teure Weg. 0,27 % ist keine Doppelhaltung, die zählt. |
| Anwendung in Resolve | **Fusion-Comp je Clip**, nicht DRT-Roundtrip (Begründung unten, Abschnitt 3). |
| Clips ohne Gyrospur | Bleiben beim heutigen Weg (`Stabilize()` + DRT-Modus). Gyroflow ersetzt ihn nicht, es tritt daneben. |
| Interviews | **Nicht betroffen.** 6i Begradigen und Kopfposition bleiben wie sie sind. Gyroflows Horizon Lock als Ablösung von 6i wurde erwogen und verworfen — zu großer Umbau, betrifft Gesichts-Check und Kopfposition. |

## 1 — `gyroflow_sidecars.py` (neuer Baustein)

Ein Werkzeug mit einer Aufgabe. Es liest Video und schreibt Sidecars. Es rendert nie und schreibt nichts nach Resolve —
dadurch ist es ohne laufendes Resolve testbar.

**Eingabe:** `_intern/autocut/gyroflow_clips.json`, geschrieben vom **Probelauf** von `feinschnitt_bauen.py`. Dort — und
nur dort — liegen beide Hälften zusammen: die `BROLL`-Tabelle mit den tatsächlich genutzten Shots und
`broll_auswahl.json`, das je Shot `datei` auflöst. Der Probelauf schreibt je genutztem Shot `{datei, tempo50}`; das
Werkzeug fasst auf **Quelldatei** zusammen, ein Sidecar je Datei, auch bei Mehrfachnutzung. Dazu `telemetrie.json`
derselben Charge für `haltung` und `wackeln`.

Damit ist die Reihenfolge aus Abschnitt 3 erzwungen statt nur empfohlen: ohne ausgefüllte `BROLL`-Tabelle gibt es keine
Clipliste, und ohne Clipliste läuft kein Export.

(`broll_einsatz.json` führt nur Zählwerte je Spur und taugt nicht als Quelle; `broll_plan.json` trägt die Zuordnung aus
Stufe 3, nicht die Auswahl des Feinschnitts. `tempo50` wird nur für den Bericht gebraucht, nicht für den Export.)

**Je Clip:**

1. Überspringen, wenn `quelle` nicht `rtmd` ist (keine Gyrospur → nichts zu rechnen), oder wenn der Dateiname
   `_stabilized` enthält (Avata-Exporte, wie in 6d).
2. Glättungs-Preset aus der Telemetrie ableiten (Abschnitt 2), als `--preset` mit JSON-Inhalt direkt übergeben.
3. `gyroflow "<clip>" --export-project 2 --preset "<json>" -f` — schreibt `<clip>.gyroflow` neben die Mediendatei.
4. `zoom_ist` = `max_zoom` aus dem Preset, `zoom_gedeckelt` = wahr. **Kein zweiter Export.** Ursprünglich war hier ein
   `--export-project 3` vorgesehen, aus dem der tatsächlich gerechnete Zoom je Frame kommen sollte; Befund 1, Punkt 6
   zeigt, dass dessen Normierung ungeklärt ist und ein geratener Umrechnungsfaktor schlechter wäre als der Rückfall.
   Der Deckel aus Abschnitt 4 hält den Haushalt ohnehin per Konstruktion; der Bericht weist den Wert als Obergrenze
   statt als Messwert aus.

**Ausgabe:** `_intern/autocut/gyroflow.json` — je Clip Pfad der Sidecar-Datei, verwendetes Preset, erkannte Kamera und
Objektiv, `zoom_ist` und `zoom_gedeckelt` (ob der Deckel gegriffen hat). Dazu ein Bericht: welche Clips ein Sidecar
bekamen, welche warum nicht, und bei welchen der Deckel griff (dort glättet Gyroflow schwächer als es könnte).

**Cache:** wie die Telemetrie je Clip über den Fingerprint plus Preset-Hash, unter `_intern/autocut/gyroflow/`. Ein
unveränderter Clip mit unverändertem Preset wird nicht neu exportiert.

**Schreibschutz.** `Charge.assert_writable` erlaubt nur `_intern/autocut/`, `Ergebnisse/Rohschnitt/` und das Protokoll —
ein Sidecar neben der Mediendatei fällt nicht darunter. Der Schreibschutz wird dafür nicht aufgeweicht; stattdessen
bekommt dieser eine Fall eine eigene, enge Regel (`sidecar_pfad()`): geschrieben wird ausschließlich eine Datei mit
der Endung `.gyroflow`, deren Stamm dem einer **existierenden** Mediendatei entspricht, die in `telemetrie.json` mit
genau diesem Pfad geführt ist. Alles andere wirft `AutoCutError`. Cache und `gyroflow.json` laufen weiter über
`assert_writable`.

## 2 — Glättung aus der Telemetrie

Das Preset ist kein Festwert, sondern kommt aus `haltung` und `wackeln`, die je Clip schon vorliegen und kalibriert sind
(21.09., 301 FX3- und 54 a7-IV-Clips). Startwerte, am ersten echten Durchlauf zu prüfen:

| `haltung` | `smoothness` | `max_zoom` | Begründung |
|---|---|---|---|
| `stativ` | 0,2 | 105 | Kaum Bewegung; starke Glättung würde nur Rand kosten und das Bild schwimmen lassen |
| `gimbal` | 0,4 | 110 | Schon vorgeglättet; zu viel nimmt der Fahrt ihren Charakter |
| `hand` | 0,7 | 120 | Gyroflow-Standard; hier liegt der eigentliche Gewinn |

Die Werte gehören als `gyroflow:`-Block in `defaults.yaml`, je Charge in `config.yaml` überschreibbar — wie
`telemetrie:`. Bei einer Änderung dort misst der nächste Lauf die betroffenen Clips neu (Preset-Hash im Cache).

## 3 — Anwendung in Resolve: Fusion-Comp

**Warum nicht der DRT-Roundtrip.** `drt_stabilisierung.py` (WTN, Wurst & Liebe, Assenheimer, Setzer) patcht
zstd-komprimiertes Protobuf im DRT-Body und trifft Parameter-IDs wie `271581208` — sauber gemacht, aber für ein
Fremd-Plugin müsste dieselbe Reverse-Engineering-Runde noch einmal gedreht werden. Dazu kommt: ein Reimport erzeugt eine
neue Timeline mitten in der 6d-Kette, `feinschnitt.json` und der Readback würden ungültig, 6e–6i müssten neu verdrahtet
werden.

**Der Weg** (am 22.09. in Resolve nachgemessen, Befund 1). Je V3-Clip `TimelineItem.AddFusionComp()`, darin
`Composition.AddTool("ofx.nl.smslv.gyroflowofx.fisheyestab_v1")`, dann `SetInput("gyrodata", <Pfad der Sidecar-Datei>)`.
Der Effekt sitzt *im Clip*: keine neue Timeline, keine Reimport-Runde, die Readback-Kette bleibt gültig.

Dazu je Clip **immer** `SetInput("Smoothness", …)` und `SetInput("FOV", …)` aus denselben Werten wie das Preset, weil
die OFX-Parameter das Sidecar überschreiben (Befund 1, Punkt 5) — und bei Zeitlupen-Shots `SetInput("VideoSpeed", 50)`
statt der Vorgabe 100 (Punkt 3).

**Preis:** Fusion-Comps kosten Abspielleistung, und Gyroflow empfiehlt für Tempo eigentlich die Edit/Color-Seite. Bei der
Shot-Zahl eines Reels vertretbar; wird es spürbar, ist der Ausweg ein Render-Cache auf den betroffenen Clips.

**Einordnung in 6d:** Der Feinschnitt-Plan steht fest, bevor gebaut wird — dort ist bekannt, welche B-Roll-Shots
vorkommen. Reihenfolge: Plan → `gyroflow_sidecars.py` über genau diese Shots → Bau. Damit läuft strukturell nie ein Clip
durch Gyroflow, der es nicht in den Schnitt schafft.

## 4 — Rand-Haushalt

Gyroflow drückt seinen Zoom in **Prozent** aus (100 = kein Beschnitt) und kennt mit `stabilization.max_zoom` eine eigene
Obergrenze — gemessen im Projekt-Export, Standard 130. Damit braucht es keine Rückkopplung zwischen beiden Beschnitten,
sondern nur einen richtig gewählten Deckel:

    max_zoom ≤ digitalzoom_max / digitalzoom_faktor × 100 = 1,5 / 1,25 × 100 = 120

Bei `max_zoom` 120 kann Gyroflow höchstens 1,2× nehmen, und der Brennweitenregel bleiben garantiert 1,25× — ihr voller
Sollwert. Die Priorität „Gyroflow zuerst" bleibt damit gewahrt, ohne dass die Brennweitenregel je zurückstecken muss.
Die Werte in Abschnitt 2 liegen darunter oder darauf; ändert jemand `digitalzoom_faktor` oder `digitalzoom_max`, muss
`max_zoom` mitgezogen werden — `gyroflow_sidecars.py` prüft die Ungleichung beim Start und bricht sonst ab.

6d rechnet den digitalen Zoom der Brennweitenregel dann wie bisher (`SetProperty` `ZoomX`/`ZoomY`, Bildmitte), ohne
Änderung. Es liest `gyroflow.json` nur für den Bericht: bei welchen Shots der Deckel griff, also Gyroflow schwächer
glättete als es könnte. Das ist der Punkt, an dem der User entscheiden kann, `digitalzoom_max` anzuheben.

Shots ohne Sidecar (keine Gyrospur) haben `zoom_ist` = 1,0 und damit das volle Budget.

## 5 — Plugin-Erneuerung (Handgriff des Users)

Das installierte OFX-Plugin ist v1.3.0 von November 2023 und trägt ein Quarantäne-Flag. Seit Gyroflow 1.6 gibt es im
Programm das Panel **„Video editor plugins"**, das Installation und Update übernimmt. Das ist ein einmaliger Handgriff je
Mac in der GUI; Claude kann ihn nicht abnehmen. Danach prüfen: Resolve → Einstellungen → Video-Plugins, Gyroflow aktiv.

## Fehler und Randfälle

- **Zeitlupe auf V3 — entschärft.** Gyroflow ordnet jedem Bild einen Gyro-Zeitstempel zu, und die Doku warnt bei
  abweichenden Frameraten vor kaputter Stabilisierung. Das OFX hat dafür aber einen eigenen Eingang `VideoSpeed`
  (Prozent, Vorgabe 100; Befund 1, Punkt 3): Shots mit `tempo50` bekommen 50. Welche das sind, steht in der
  `BROLL`-Tabelle der 6d-Vorlage. Die Sichtprüfung am echten Bau steht noch aus — sie gehört in den Bau-Schritt von
  6d, nicht in ein eigenes Gate.
- **Clips ohne Gyrospur.** In Wurst & Liebe 193 FX3- und 54 ZV-E10-Clips mit `quelle: keine`. Kein Sidecar, kein
  Gyroflow, heutiger Weg unverändert.
- **DJI (Mavic, Avata).** Die Telemetrie misst sie optisch, weil sie nur Sony-rtmd liest. Gyroflow unterstützt DJI aber
  nativ — ob es deren Gyro findet, ist ungeprüft. Wäre ein Bonus, besonders bei Avata, wo dann das Original statt des
  fertigen `_stabilized`-Exports verwendet werden könnte.
- **Sidecars laufen nicht über den Abgleich.** Sie liegen bei den Medien, nicht in der Charge. Wer die Charge ohne das
  Footage holt, hat keine Sidecars — er hat dann aber auch keine Medien.
- **Zweimal derselbe Clip im Schnitt.** Ein Sidecar je Quelldatei, nicht je Shot. Beide Verwendungen bekommen dieselbe
  Glättung. Das ist gewollt: die Glättung gehört zum Clip, nicht zum Schnitt.
- **`unsupported_lens: true`.** Steht in den Metadaten, wenn das Objektiv (hier Tamron 70-180) nicht in Gyroflows
  Profildatenbank ist. Unkritisch, solange Sony eigene Verzeichnungsdaten mitliefert (`distortion_model: "sony"`) — der
  Sidecar-Lauf soll es trotzdem protokollieren.

## Befund 1 — Verifikation am 22.09.2026 (Resolve 21.1, Projekt „MCP MEK Test")

Gemessen mit laufendem Resolve im Testprojekt, das der User freigegeben hat; Test-Timeline und Fusion-Comps danach
gelöscht, Timeline und Bin des Users wiederhergestellt.

**1. Tool-Kennung — geklärt.** In `Fusion.GetToolList()` (506 Werkzeuge) steht das Plugin als
`ofx.nl.smslv.gyroflowofx.fisheyestab_v1`, angezeigt als „Gyroflow". Es registriert sich **auch als Version 1.3.0 mit
gesetztem Quarantäne-Flag** — die Erneuerung aus Abschnitt 5 bleibt empfohlen, ist aber kein Blocker für die
Automatisierung.

**2. Anwendung per Skript — geklärt und tragfähig.** `TimelineItem.AddFusionComp()` liefert einen Comp,
`Composition.AddTool("ofx.nl.smslv.gyroflowofx.fisheyestab_v1")` legt das Werkzeug an (`TOOLS_Name` „Gyroflow1"), und
`SetInput` nimmt den Projektdatei-Pfad an. Der Parameter heißt **`gyrodata`**; der Readback liefert den gesetzten Pfad
zurück. Der Weg aus Abschnitt 3 steht damit.

**3. Tempo — entschärft.** Das Werkzeug hat 78 Eingänge, darunter einen ausdrücklichen **`VideoSpeed`** (Prozent,
Vorgabe 100). Die Zeitlupe ist damit kein Ratespiel, sondern eine Einstellung: B-Roll auf 50 % bekommt `VideoSpeed` 50.
Offen bleibt allein die Sichtprüfung am echten Bau — sie gehört in den Bau-Schritt von Baustein 6d, nicht mehr in ein
eigenes Gate.

**4. Weitere nutzbare Eingänge:** `FOV`, `Smoothness`, `LensCorrectionStrength`, `HorizonLockAmount`, `HorizonLockRoll`,
`PositionX`/`PositionY`, `InputRotation`, `Rotation`, `DisableStretch`, `UseGyroflowsKeyframes`, `IncludeProjectData`,
`Status`.

**5. Vorrang der Parameter — neue Erkenntnis mit Folgen.** Nach `SetInput("gyrodata", …)` lieferte der Readback
`Smoothness` 0,5 und `FOV` 1,0 — die **Vorgaben des Plugins**, nicht die Werte aus dem Sidecar (dort 0,7 bzw.
`max_zoom` 120). Die OFX-Parameter überschreiben das Projekt also offenbar.

**Folge:** Baustein 6d setzt beim Bau **zusätzlich** `Smoothness` und `FOV` je Clip aus denselben Werten, aus denen auch
das Preset gebaut wird. Damit ist der Vorrang gleichgültig. `max_zoom` hat keine OFX-Entsprechung und bleibt im Sidecar
— die Garantie aus Abschnitt 4 hängt daran und bleibt unberührt.

**6. Zoom-Readback — Zugriffsweg steht, Umrechnung nicht.** `adaptive_zoom_fovs` im Typ-3-Projekt ist basE91 über den
ganzen String (inklusive `q:`-Präfix), darunter zlib; entpackt ein Binärarray von 4743 Byte, weder durch 4 noch durch 8
teilbar — Struktur ungeklärt, Rückbau lohnt nicht. Sauberer Weg stattdessen: `--export-metadata 3:<datei>` liefert eine
Liste mit genau einem Eintrag je Frame (gemessen 528 bei 528 Frames), Felder `fov_scale` und `minimal_fov_scale`.
**Ungeklärt bleibt die Normierung:** `fov_scale` lag bei 0,459 für einen hochkant gedrehten 4K-Clip, ist also nicht auf
„1,0 = volles Bild" bezogen — Rotation und Seitenverhältnis stecken darin. Das ohne Kalibrierung über mehrere Clips zu
raten wäre schlechter als der Rückfall. **Es bleibt beim Rückfall:** `zoom_ist` ist der Deckelwert, im Bericht als
Obergrenze statt als Messwert ausgewiesen. Der Rand-Haushalt hängt nicht daran (Abschnitt 4 hält per Konstruktion).

**7. DJI — ungeprüft.** Bonus, gatet nichts. Clips ohne `quelle: rtmd` bleiben ausgeschlossen.

## Umgebung

Keine neue Abhängigkeit. Gyroflow 1.6.1 und das OFX-Plugin sind installiert (Plugin-Update: Abschnitt 5).
`gyroflow_sidecars.py` läuft im AutoCut-venv (`tools/autocut/venv/bin/python`) und ruft die CLI per `subprocess`.
Resolve nur beim Bau, nur im freigegebenen Projekt, nur anhängend — wie alle 6d-Bausteine.
