# AutoCut — Telemetrie in der B-Roll-Auswahl (Stufe 3 v2) (Spec)

Datum: 2026-09-22 · Status: entworfen, nicht umgesetzt. Folgeschritt von
`docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md` (Telemetrie) und
`docs/superpowers/specs/2026-09-21-autocut-zoom-brennweite-design.md` (Zoomfahrten, kalibriert 21.09.).

## Anlass

Der User will, dass die automatische B-Roll-Auswahl (Stufe 3 v2) gut genug wird, um die Auswahl-Timeline von Hand
(Stufe 3a) überflüssig zu machen. Dafür sollen die gemessenen Daten in die Auswahl einfließen — Zoom und Gyro.

**Befund vor dem Entwurf: sie tun es heute nicht.** `compact_index_v2()` (`broll_layout.py`) gibt je Abschnitt nur
`von_s`, `bis_s`, `kurz`, `q`, `einstellung`, `perspektive`, `brennweite`, `richtung`, `motiv` weiter. `brennweite` ist
dort **Claudes Klasse**, nicht `brennweite_mm`; `zoom`, `bewegungsart`, `haltung`, `wackeln` und `zooms` kommen gar nicht
vor. `verify_layout()` prüft keine Telemetrie-Regel: das Shot-Doppel erkennt es über das Klassen-Tripel
`einstellung`/`perspektive`/`brennweite`. Die Telemetrie erreicht heute nur Stufe 2b (Abschnittsbogen,
`perspektive_hoehe`), die Vorlagen 3a und 6d (dort als **Prüfung nach dem Plan**) und den Aftermovie-Sonderfall.

Die Auswahl läuft damit auf der Brennweitenklasse, die in der Kalibrierung vom 21.09. (MEK, 463 Clips) nur zu **47 %**
mit der gemessenen KB-Brennweite übereinstimmte — während der gemessene Wert danebenliegt und ungenutzt bleibt.

## Entscheidungen (Chat 22.09.)

1. **Weg A**: die Messwerte werden durchgereicht und als Prüfregeln geprüft; die inhaltliche Auswahl (Motiv ↔ Wort)
   bleibt beim Modell. Verworfen: Kandidaten-Vorsortierung im Code und rein rechnerische Auswahl — beide bräuchten eine
   Gewichtung, die niemand kalibriert hat, und die rechnerische kann Motiv ↔ Wort ohnehin nicht.
2. **Kein Vorfilter vor dem bezahlten Index.** Ursprünglich gewählt, nach der Kalibrierung verworfen (unten).
3. **Drei Regeln, zwei hart, eine weich** — eine nicht kalibrierte Regel darf nichts blockieren.

## Kalibrierung Umschwenken — negatives Ergebnis (22.09.)

Charge `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/` (nicht im Repo), Skript
`_intern/skripte/schwenk_beispiele.py`, Quelle MEK-Telemetrie.

Gesucht war die Grenze für **Umschwenken zwischen zwei Ausrichtungen** (Ausschuss) gegenüber gewollter Bewegung —
ausdrücklich nicht „viel Bewegung", schnelle Bewegung darf gewollt sein. Zwei Runden mit 12 und 18 Beispielen
(je 5 s, Nummern gemischt), Urteile des Users in `_intern/urteile.json` / `urteile2.json`.

**Runde 1** widerlegte die Vorannahme: `spitze` (Tempo) und `verhaeltnis` (Herausstechen aus dem eigenen Clip)
überlappen zwischen gewollt und ungewollt vollständig. Entscheidendes Paar #3 / #8 — spitze 1,99 vs. 1,92,
verhaeltnis 1,01 vs. 1,31, Urteile gegensätzlich.

**Runde 2** war ein Vorhersage-Test: die Prognosen beider nachträglich gefundener Muster wurden vor der Vorlage in
`_intern/vorhersagen2.json` festgeschrieben, die Beispiele so gewählt, dass die Muster sich bei 12 von 18
widersprechen.

| | richtig von 18 |
|---|---|
| Muster 1 (`wackeln` > 0,5 oder Umschwenk-Signatur) | 10 (56 %) |
| Muster 2 (waagerechter Schwenk) | 10 (56 %) |
| trivial „immer ungewollt" | **15 (83 %)** |

Beide Muster sind **schlechter als die triviale Konstante**; auf den 12 Streitfällen traf jedes genau 6. Damit sind
`spitze`, `verhaeltnis`, `wackeln` und `bewegungsart` als Träger einer Grenze erledigt (30 Beispiele, 6× gewollt).

**Der tragende Befund steht in den Anmerkungen:** bei 6 von 18 urteilt der User über **Teilbereiche**, nicht über das
Beispiel („brauchbarer Teil in der Mitte", „gewollt bis auf den Shake am Ende", ausdrücklich „**komplett** ungewollt"
als Abgrenzung). Ein Filter auf Clip-Ebene würde die brauchbaren Teile mit wegwerfen. Und #17 („gewollt, aber ich
musste der Hand schnell folgen") zeigt, dass die Absicht am Bildinhalt hängt, nicht an der Bewegung.

**Folge:** kein Vorfilter. Die Telemetrie liefert Bereichs-Hinweise, keine Urteile über Absicht. Die 30 Urteile
bleiben als Testsatz: jeder künftige Versuch muss gegen sie antreten und 83 % schlagen.

## 1 — Stufe 2b (`index_sections.py`): `bewegung_spitzen` je Abschnitt

`telemetrie_anwenden` ergänzt je Abschnitt `bewegung_spitzen` = Liste `[t_s, bewegung]` der lokalen Maxima der
Fenster-Reihe (`fenster` = `[t_s, wackeln, bewegung, bewegungsart, schaerfe]`) innerhalb von `[von_s, bis_s]`. Ein
Fenster ist lokales Maximum, wenn sein `bewegung` ≥ dem der beiden Nachbarn ist. Ohne `fenster` bleibt die Liste leer.
`felder_quelle` führt das Feld wie die übrigen; Cache-Treffer bekommen es ohne API-Aufruf (bestehender Zweig in
`index_sections_clip`).

Damit betritt die Telemetrie den Index an **genau einer Stelle**; alles Weitere liest nur noch `broll_index.json`.

## 2 — `compact_index_v2()` (`broll_layout.py`): durchreichen statt filtern

Je Abschnitt zusätzlich: `brennweite_mm`, `zoom`, `bewegungsart`, `haltung`, `bewegung_spitzen`. Bestehende Felder
bleiben unverändert (auch `brennweite` als Klasse — sie steht weiter im Datensatz, trägt aber keine Regel mehr).
Fehlen die Felder (Charge ohne Telemetrie), bleiben sie `None` bzw. leer.

Größe: MEK hat 1026 Abschnitte, `broll_index_kompakt.json` liegt bei 574 KB; der Zuwachs beträgt grob 60 KB.

## 3 — `verify_layout()` (`broll_layout.py`): drei Regeln

Alle drei setzen Telemetrie voraus und werden je Shot übersprungen, wenn der Clip keine hat. Der Bericht nennt die
Zahl der ungeprüften Shots mit Grund („keine Telemetrie", „alte Telemetrie ohne Brennweitenverlauf", „mit anderen
Telemetrie-Schwellen gemessen") — wie die Vorlagen 3a und 6d es seit 21.09. tun.

**3a — KB-Brennweitenfolge (Fehler).** Für in der Timeline direkt aufeinanderfolgende Shots (Reihenfolge nach
`rec_in_f`, **über Szenen- und Streckengrenzen hinweg** — der Schnitt ist auch dort ein Schnitt) die scheinbare KB-Brennweite am
Schnitt: `kb_am(rec_A, out_A, seite="ende")` und `kb_am(rec_B, in_B, seite="anfang")`. Liegt `max/min − 1` unter
`telemetrie.brennweite_gleich_max` (0,2), ist es ein Fehler mit Nennung beider Werte. Kalibriert und seit 21.09. in
3a/6d produktiv.

**3b — Kein schneller Zoom im genutzten Bereich (Fehler).** `zooms_im_bereich(rec, in_s, out_s)` (liefert mit dem
Vorgabewert `nur_schnelle=True` genau die Fahrten mit `urteil == "schnell"`, die den Bereich echt schneiden) → Fehler,
außer der Shot ist als `abweichung` mit `abweichung_grund` markiert. Die Grenze
(100 %/s Spitze bzw. 12 % in 0,12 s) hat der User am 21.09. an 10 Beispielen abgenommen.

**3c — Schnittgrenze in einer Bewegungsspitze (nur Warnung).** Liegt `in_s` oder `out_s` innerhalb von
`bewegung_rand_s` (0,5 s) um eine `bewegung_spitzen`-Stelle, deren Wert mindestens `bewegung_spitze_faktor` (3,0) über
dem Grundniveau des Clips liegt, gibt es eine **Warnung**. Grundniveau = Median der `bewegung` aller Fenster des Clips,
die mindestens 3 s von der Spitze entfernt liegen.

> Beide Werte sind **unkalibrierte Startwerte**. Nach dem Ergebnis vom 22.09. darf diese Regel nichts blockieren; sie
> steht im Bericht, damit sich zeigt, ob sie etwas taugt. Eine Erhebung zum Fehler setzt eine Kalibrierung voraus, die
> den Testsatz der 30 Urteile schlägt.

## 4 — Shot-Doppel ohne Brennweitenklasse

Die Dublettenprüfung (heute `einstellung == einstellung and perspektive == perspektive and brennweite == brennweite`)
verliert die Klasse `brennweite` und bekommt stattdessen den mm-Abstand aus 3a: zwei Shots sind dasselbe Setup, wenn
Einstellung und Perspektive gleich sind **und** die KB-Brennweiten weniger als `brennweite_gleich_max` auseinander
liegen. Ohne Telemetrie fällt die Prüfung auf das bisherige Klassen-Tripel zurück (Verhalten unverändert).

## Konfiguration

Keine neuen Schlüssel unter `broll:`. Genutzt werden die bestehenden unter `telemetrie:`
(`brennweite_gleich_max`, `zoom_schnell_proz_s`, `zoom_sprung_proz`, `fenster_s`). Neu unter `telemetrie:`, nur für
Regel 3c und als Warnung:

```yaml
  bewegung_rand_s: 0.5        # Abstand einer Schnittgrenze zu einer Bewegungsspitze (unkalibriert)
  bewegung_spitze_faktor: 3.0 # ab dem Vielfachen des Grundniveaus zählt eine Spitze (unkalibriert)
```

Die Schlüssel gehören nicht in den Config-Hash der Telemetrie-Messung (sie ändern keine Messung), analog zu den
Vorlagen-Schlüsseln der Brennweitenfolge.

## Fehler und Randfälle

- **Charge ohne `telemetrie.json`**: alle drei Regeln entfallen, der Bericht sagt „keine Telemetrie — Brennweiten- und
  Zoomregel nicht geprüft". Kein Fehler, kein Abbruch.
- **Clip ohne `kb_verlauf`** (Mavic, Avata, alte Telemetrie): 3a und 3b entfallen für diesen Shot und werden gezählt.
- **Telemetrie mit anderem Config-Hash**: wie in 3a/6d gemeldet, Regeln für diese Clips als ungeprüft gezählt.
- **Abschnitt ohne `bewegung_spitzen`**: 3c entfällt.
- **Erster Shot einer Strecke**: 3a braucht einen Vorgänger; der erste Shot der Timeline wird übersprungen.
- **Shot mit `tempo > 1` (Zeitlupe)**: der genutzte Quellbereich ist kürzer als die Timeline-Dauer;
  `genutzter_quellbereich_s()` liefert ihn, 3b und 3c rechnen darauf (wie 6d).

## Tests (pytest, ohne NAS, ohne Resolve)

- `test_index_sections.py`: `bewegung_spitzen` aus einer Fenster-Reihe (lokale Maxima, Abschnittsgrenzen, leer ohne
  `fenster`); Cache-Treffer trägt das Feld ohne API-Aufruf nach.
- `test_broll_layout.py`: `compact_index_v2` reicht die fünf Felder durch und lässt sie bei fehlender Telemetrie `None`;
  `verify_layout` meldet 3a und 3b als Fehler, 3c als Warnung; ohne Telemetrie keine der drei; Dublettenprüfung mit und
  ohne mm-Abstand.
- Fixture mit echten Werten aus MEK (kurze Fenster-Reihe und `kb_verlauf`), damit die Regeln gegen gemessene Daten
  laufen und nicht nur gegen erfundene.

## Erste Probe (MEK, `projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh`)

Einzige Charge mit v2-Plan **und** vollständiger, aktueller Telemetrie (463 Clips, inkl. `kb_verlauf`/`zooms`).
Medien liegen auf `NIRO-SSD-03` unter `01_Projekt-2xAds1xImagefilm_24.06.26` (alle 463 erreichbar). Die
Abschnittsfelder aus 2b fehlen dort noch (`felder_quelle` = 0 von 1026).

1. `autocut_index_sections.py "$CHARGE"` → trägt die Felder aus dem Cache nach, **ohne API-Kosten**.
2. `autocut_place_broll.py "$CHARGE" --compact` → kompakter Index mit den Messwerten.
3. `autocut_place_broll.py "$CHARGE" --verify-only` auf den **vorhandenen** `broll_plan.json`: Der Plan entstand blind
   für die Telemetrie. Die Zahl der Verstöße nach 3a/3b misst direkt, was die Daten beitragen.
4. Erst danach neu planen und beide Pläne auf denselben Strecken vergleichen.

Schritt 3 ist die eigentliche Probe: bringt der alte Plan kaum Verstöße, war die Brennweite nie das Problem — dann
wird der Entwurf verworfen statt gebaut.

## Doku

- `tools/autocut/WORKFLOW-AutoCut.md`: Stufe 3 (Regeln in `--verify-only`), Stufe 2b (`bewegung_spitzen`),
  Telemetrie-Abschnitt (Abnehmer um Stufe 3 ergänzen, Kalibrierwerte um das negative Ergebnis vom 22.09.)
- `tools/autocut/prompts/place-broll.md`: die neuen Felder im kompakten Index und die drei Regeln
- `tools/autocut/README.md`: Tabellenzeile

## Nicht enthalten

- **Vorfilter vor dem Index** — am 22.09. widerlegt (oben).
- **Digitaler Zoom in v2** — 3a und 6d setzen ihn, v2 nicht; eigener Schritt, wenn der Vergleich zeigt, dass die
  Brennweitenregel ohne ihn zu oft keinen Ausweg hat.
- **Erkennen von Absicht** — braucht den Bildinhalt; gehört in den Index, nicht in die Telemetrie.
- **Ablösung von Stufe 3a** — Ziel des Users, aber erst nach dem Vergleich zu entscheiden; 3a bleibt unverändert.
