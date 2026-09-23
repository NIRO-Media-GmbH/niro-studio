# AutoCut — Gyroflow-Stabilisierung für B-Roll (Spec)

Datum: 2026-09-22 · Status: umgesetzt (Tasks 1–9, Branch `autocut-gyroflow`, 23.09.2026); die Sichtprüfung am
echten Chargen-Bau steht aus. Abschnitt 4 trägt eine Korrektur vom 23.09. Baut auf der Kamera-Telemetrie
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
| Rand-Haushalt | **Gyroflow zuerst**, gedeckelt über `max_zoom` statt über eine Rückkopplung (Abschnitt 4). `digitalzoom_max` (1,5) bleibt unverändert. **Korrektur 23.09.:** Der Deckel begrenzt nur Gyroflows eigenen Beschnitt; der digitale Zoom der Brennweitenregel kommt obendrauf (heute bis 1,2 × 1,5 = 1,8× gesamt). Die Rückkopplung ist damit doch nötig und als eigener Zyklus vereinbart. |
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
   Der Deckel aus Abschnitt 4 begrenzt Gyroflows Beschnitt ohnehin nach oben; der Bericht weist den Wert als
   Obergrenze statt als Messwert aus (Deckelwert, nicht gemessen).

**Ausgabe:** `_intern/autocut/gyroflow.json` — je Clip Pfad der Sidecar-Datei, verwendetes Preset, erkannte Kamera und
Objektiv, `zoom_ist` und `zoom_gedeckelt` (heute immer wahr: der Wert ist der Deckel, keine Messung). Dazu ein
Bericht: welche Clips ein Sidecar bekamen und welche warum nicht. Der Zoom steht dort als Obergrenze
(„≤ 1,20× (Deckelwert, nicht gemessen)"), nicht als Befund — ein Abschnitt „Deckel griff" hätte jeden exportierten
Clip aufgeführt und über jeden dasselbe Ungemessene behauptet.

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
Obergrenze — gemessen im Projekt-Export, Standard 130. `max_zoom` deckelt **nur Gyroflows eigenen Beschnitt**; die
Werte aus Abschnitt 2 (105/110/120) begrenzen ihn auf 1,05× bis 1,2×.

**Keine Garantie gegenüber der Brennweitenregel** (Korrektur 23.09.2026). Die ursprüngliche Fassung dieser Spec
behauptete hier, `max_zoom ≤ digitalzoom_max / digitalzoom_faktor × 100 = 1,5 / 1,25 × 100 = 120` mache beide
Beschnitte per Konstruktion verträglich, weil die Brennweitenregel höchstens `digitalzoom_faktor` (1,25×) nehme. Diese
Prämisse ist falsch: `telemetrie.digitalzoom()` rechnet `gesamt = zoom × faktor × längere / kürzere` und lässt jeden
Kandidaten bis `digitalzoom_max` (1,5) zu. Der Shot mit der kürzeren scheinbaren Brennweite braucht regelmäßig mehr als
1,25× — bis zu 1,5×, wie die Regel selbst zulässt.

    heutiger schlimmster Fall:  Gyroflow 1,2×  ×  Brennweitenregel 1,5×  =  1,8× gesamt

Timelines und Quellen sind beide 4K, jeder Zoom über 1,0 skaliert also hoch. 1,5× war bewusst als „leicht" abgenommen,
1,8× nie. Der digitale Zoom kommt heute **obendrauf**, ungeprüft.

**Vereinbarter nächster Schritt (noch nicht umgesetzt):** Gyroflows Beschnitt als bereits vorhandenen Zoom des Shots in
die Brennweitenregel geben, damit deren Prüfung gegen `digitalzoom_max` wieder ehrlich das Gesamtergebnis misst. Das
ändert eine kalibrierte, von einer anderen Pipeline-Stufe mitbenutzte Funktion und bekommt einen eigenen Zyklus.

Bis dahin bleibt der Deckel trotzdem sinnvoll — Gyroflows Beschnitt zu begrenzen ist für sich genommen richtig, und
`gyroflow.py` (`pruefe_deckel`) prüft die Ungleichung weiter beim Start und bricht sonst ab. Sie ist nur keine
Gesamtzusage, sondern die Regel, an der die Startwerte aus Abschnitt 2 gewählt wurden.

6d rechnet den digitalen Zoom der Brennweitenregel wie bisher (`SetProperty` `ZoomX`/`ZoomY`, Bildmitte), ohne
Änderung. Es liest `gyroflow.json` nur für den Bericht.

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

**3. Tempo — geklärt und am Bild belegt.** Das Werkzeug hat 78 Eingänge, darunter einen ausdrücklichen **`VideoSpeed`**
(Prozent, Vorgabe 100). Gegenprobe am 23.09. an einem FX3-Shot, zweimal auf einer Probe-Timeline: einmal 100 %, einmal
`SetSpeed({"Percentage": 50.0})` plus `RETIME_NEAREST`, beide mit demselben Sidecar, `Smoothness` 0,7, `VideoSpeed` 100
bzw. 50. Gerendert und die Frames verglichen (RMSE):

| Vergleich | RMSE |
|---|---|
| 100 % bei Quellframe 20 ↔ **50 % bei Quellframe 20** | **201 (0,31 %)** |
| 100 % bei Quellframe 20 ↔ 100 % bei Quellframe 40 (Gegenprobe) | 2467 (3,76 %) |
| 100 % bei Quellframe 40 ↔ 50 % an derselben Timeline-Position | 2469 (3,77 %) |

Die Zeitlupen-Instanz zeigt an ihrer Position denselben Quellframe wie die 100-%-Instanz, pixelgleich bis auf
Codec-Rauschen — und nicht den Frame, den sie zeigen würde, wenn `VideoSpeed` wirkungslos wäre. **Das Risiko aus der
ursprünglichen Fassung dieser Spec ist damit erledigt.**

Nebenbefund: Die Probe-Timeline war 3840×2160 quer, der Clip 2160×3840 hochkant — das Bild saß dann klein in der Mitte
(Pillarbox). Artefakt des Testaufbaus, kein Plugin-Fehler; im echten 6d-Bau stimmen Timeline und Clips überein. Die
Warnung der Gyroflow-Doku vor abweichenden Seitenverhältnissen ist aber real: **Timeline-Auflösung und Clip-Auflösung
müssen zusammenpassen**, sonst skaliert der Fusion-Comp das Bild.

**4. Weitere nutzbare Eingänge:** `FOV`, `Smoothness`, `LensCorrectionStrength`, `HorizonLockAmount`, `HorizonLockRoll`,
`PositionX`/`PositionY`, `InputRotation`, `Rotation`, `DisableStretch`, `UseGyroflowsKeyframes`, `IncludeProjectData`,
`Status`.

**5. Vorrang der Parameter — neue Erkenntnis mit Folgen.** Nach `SetInput("gyrodata", …)` lieferte der Readback
`Smoothness` 0,5 und `FOV` 1,0 — die **Vorgaben des Plugins**, nicht die Werte aus dem Sidecar (dort 0,7 bzw.
`max_zoom` 120). Die OFX-Parameter überschreiben das Projekt also offenbar.

**Folge:** Baustein 6d setzt beim Bau **zusätzlich** `Smoothness` und `FOV` je Clip aus denselben Werten, aus denen auch
das Preset gebaut wird. Damit ist der Vorrang gleichgültig. `max_zoom` hat keine OFX-Entsprechung und bleibt im Sidecar
— Gyroflows eigener Beschnitt bleibt also gedeckelt wie in Abschnitt 4 beschrieben (was er nicht leistet, steht dort).

**6. Zoom-Readback — Zugriffsweg steht, Umrechnung nicht.** `adaptive_zoom_fovs` im Typ-3-Projekt ist basE91 über den
ganzen String (inklusive `q:`-Präfix), darunter zlib; entpackt ein Binärarray von 4743 Byte, weder durch 4 noch durch 8
teilbar — Struktur ungeklärt, Rückbau lohnt nicht. Sauberer Weg stattdessen: `--export-metadata 3:<datei>` liefert eine
Liste mit genau einem Eintrag je Frame (gemessen 528 bei 528 Frames), Felder `fov_scale` und `minimal_fov_scale`.
**Ungeklärt bleibt die Normierung:** `fov_scale` lag bei 0,459 für einen hochkant gedrehten 4K-Clip, ist also nicht auf
„1,0 = volles Bild" bezogen — Rotation und Seitenverhältnis stecken darin. Das ohne Kalibrierung über mehrere Clips zu
raten wäre schlechter als der Rückfall. **Es bleibt beim Rückfall:** `zoom_ist` ist der Deckelwert, im Bericht als
Obergrenze statt als Messwert ausgewiesen („≤ 1,20× (Deckelwert, nicht gemessen)"). Wie viel Gyroflow tatsächlich
nimmt, weiß die Pipeline damit nicht — für die offene Frage aus Abschnitt 4 (Gesamtzoom über 1,5×) ist genau das die
fehlende Messung.

**7. DJI — ungeprüft.** Bonus, gatet nichts. Clips ohne `quelle: rtmd` bleiben ausgeschlossen.

## Umgebung

Keine neue Abhängigkeit. Gyroflow 1.6.1 und das OFX-Plugin sind installiert (Plugin-Update: Abschnitt 5).
`gyroflow_sidecars.py` läuft im AutoCut-venv (`tools/autocut/venv/bin/python`) und ruft die CLI per `subprocess`.
Resolve nur beim Bau, nur im freigegebenen Projekt, nur anhängend — wie alle 6d-Bausteine.

## Befund 2 — Rand-Haushalt: Messung vom 23.09.2026

Der User hat am 23.09. entschieden, den Gyroflow-Beschnitt in die Brennweitenregel einzuspeisen, und zwar mit einem
**festen** Beschnitt je Haltung, damit der eingespeiste Wert exakt statt geschätzt ist. Die Umsetzung scheitert vorerst
an der Messung; hier der Stand, damit niemand sie wiederholen muss.

**Warum es überhaupt einen festen Beschnitt bräuchte.** `brennweitenfolge` rechnet mit `schein = kb × zoom` — der Zoom
verändert die scheinbare Brennweite, nach der die Regel entscheidet. Gyroflows Beschnitt tut dasselbe. Einspeisen heißt
also nicht nur „Budget abziehen", sondern die Regel würde endlich mit dem rechnen, was man sieht. Dafür muss der Wert
aber bekannt sein — und der adaptive Zoom ist nicht auslesbar (Befund 1, Punkt 6).

**Gemessen (CLI, `--export-metadata 3`, FX3-Clip, 216 Frames):**

| Einstellung | `fov_scale` | konstant |
|---|---|---|
| adaptiv an, `max_zoom` 110 | 0,437–0,496 | nein |
| adaptiv an, `max_zoom` 130 (Standard) | 0,412–0,478 | nein |
| adaptiv an, `max_zoom` 200 | 0,324–0,399 | nein |
| **`adaptive_zoom_window: 0`** | **1,00000** | **ja** |

- **`max_zoom` greift** über `--preset`: die drei Werte erzeugen monoton verschiedene Beschnitte, und der Wert landet
  im Projekt. Die Deckelung ist also wirksam.
- **Der Absolutwert bleibt unübersetzbar.** Bei Deckel 110 liegt `1/fov_scale` bei 2,0–2,3, nicht bei 1,10; kein
  konstanter Faktor bringt die drei Messreihen zur Deckung. In `fov_scale` stecken Rotation und Seitenverhältnis mit
  drin. Ein daraus geschätzter Umrechnungsfaktor wäre schlechter als gar keiner.
- **`adaptive_zoom_window: 0` ist ein sauber bekannter Zustand:** Beschnitt exakt 1,0, und der Render ist einwandfrei
  (geprüft an einem Standbild: stabilisiert, vollflächig, keine schwarzen Ränder).

**Woran es scheitert.** Der feste Beschnitt müsste dann über den OFX-Eingang `FOV` kommen. Gegenprobe in Resolve,
derselbe Clip zweimal auf einer Timeline in Quellauflösung, Sidecar mit `adaptive_zoom_window: 0`, einmal `FOV` 1,0 und
einmal 0,8333 (= 1/1,2), gerendert und die Standbilder verglichen:

- `FOV` 1,0 → **sauberes Bild**.
- `FOV` 0,8333 → **kaputtes Bild**: ein ausgewaschenes Band quer durch die Bildmitte. Kein Beschnitt, sondern ein
  Darstellungsfehler. Keine der drei Vergleichshypothesen (A unverändert, A × 1,2, A × 0,833) passte auf B
  (RMSE 0,196 / 0,212 / 0,343 — alle weit von den 0,003 der gelungenen Tempo-Messung entfernt).

**Stand.** Der feste Beschnitt ist mit diesem Wissen nicht baubar. Offen ist, was `FOV` tatsächlich erwartet
(Wertebereich, Richtung, Zusammenspiel mit abgeschaltetem adaptivem Zoom) — das gehört gemessen, nicht geraten, und
am besten am erneuerten Plugin (Abschnitt 5), denn die installierte 1.3.0 ist von November 2023.

**Bis dahin gilt Abschnitt 4 unverändert:** `max_zoom` deckelt nur Gyroflows eigenen Beschnitt, der digitale Zoom der
Brennweitenregel kommt obendrauf, Gesamtzoom bis 1,8×. Das ist dokumentiert und nicht behauptet.
