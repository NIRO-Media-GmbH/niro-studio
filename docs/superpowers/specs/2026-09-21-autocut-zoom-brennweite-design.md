# AutoCut — Zoomfahrten und Brennweitenwechsel (Spec)

Datum: 2026-09-21 · Status: umgesetzt (Plan `docs/superpowers/plans/2026-09-21-autocut-zoom-brennweite.md`), kalibriert
(Nachtrag unten). Folgeschritt der Kamera-Telemetrie
(`docs/superpowers/specs/2026-09-19-autocut-telemetrie-design.md`, umgesetzt und auf main seit 21.09.).

## Anlass

Nach der Telemetrie-Kalibrierung (MEK: 157 von 463 B-Roll-Clips mit Brennweitenänderung, Brennweitenklassen nur 47 % gleich
mit Claude) hat der User zwei Regeln festgelegt:

1. **Zoomfahrten nur langsam und smooth** — wie die Essens-Closeups auf dem Drehteller bei Wurst & Liebe. Schnelle Zooms
   gehören nicht in den Schnitt.
2. **Keine Brennweitenklassen.** Gedreht wird mit konkreten Brennweiten (24, 50, 70 mm …). Neu: **nie zweimal dieselbe
   Brennweite direkt hintereinander** — weiche Regel; gibt das Material nichts anderes her, darf es sein, dann mit digitalem
   Zoom als Ausweg.

## Entscheidungen (Chat 21.09.)

| Frage | Entscheidung |
|---|---|
| Messweg | Nur Sony-Datenspur (rtmd, Tag 0x8004 = KB-Brennweite je Frame, inkl. Crop/Klarbild-Zoom). Clips ohne Spur (Mavic, Avata): „Brennweite unbekannt", keine Regel. Kein optischer Zoom-Schätzer. |
| Schneller Zoom im genutzten Quellbereich | **Nur Hinweis** im Probelauf (Zeit, Tempo); gebaut wird trotzdem. Kein automatisches Kürzen, kein Fehler. |
| „Dieselbe Brennweite" | Abstand = größere / kleinere KB-Brennweite − 1; **gleich, wenn unter 20 %** (50/55 gleich, 24/28 gleich, 35/50 verschieden, 70/85 knapp verschieden). |
| Welche Schnitte | **B-Roll auf B-Roll**, nur direkt aneinanderstoßende Shots auf V3 (keine Lücke, kein Interview dazwischen). |
| Wenn gleich | **Digitaler Zoom automatisch** auf einen der beiden Shots; Grenze **1,5×** für den Zoom des Shots (Produkt, falls schon ein Zoom vergeben ist). Geht es nicht, Hinweis. Timelines und Quellen sind 4K — der Zoom skaliert also bewusst leicht hoch (W&L-Reels arbeiten schon mit 1,2×). |
| Brennweitenklassen | Entfallen: `brennweitenklasse` und `brennweite_klassen_kb` werden gestrichen. |
| Stufe 2b | Je Abschnitt kommen `brennweite_mm` und `zoom` dazu; Claudes Klasse `brennweite` bleibt, wie Claude sie schätzt — das Überschreiben aus der Telemetrie wird zurückgenommen (`perspektive_hoehe` wird weiter aus den Metadaten gesetzt). |
| Schwellen | Aus den Daten (W&L-Drehteller = „ok"-Referenz, MEK) plus Stichprobe: 8–10 Grenzfälle als ein Beispielvideo in NIRO Review, der User urteilt je Nummer „ok"/„zu schnell". |
| Umgebung | Wie die Telemetrie: AutoCut-venv (numpy/scipy), ffmpeg; keine neue Abhängigkeit; NAS nur lesend; Resolve nur in den Vorlagen beim Bau. |

## 1 — Messung (`telemetrie.py`)

Grundlage ist die KB-Brennweite je rtmd-Sample (ein Sample je Videoframe), die `rtmd.auswerten` schon liefert.

**Aufbereitung:** gleitender Median über 0,2 s (Ausreißer, Quantisierung), dann auf 25-fps-Frames wie der Gyro.
Tempo `v(t)` = Änderung von ln(KB) je Sekunde, geglättet über 0,2 s, in % pro Sekunde.

**Zoomfahrt:** zusammenhängender Bereich, in dem |v| über einer Rauschgrenze liegt und die Brennweite sich insgesamt um
mindestens `zoom_min_proz` (Start 3 %) ändert; Bereiche mit weniger als 0,3 s Abstand werden zusammengefasst
(Stop-and-go = eine Fahrt). Fokus-Atmen und Wackeln der Anzeige bleiben unter der 3-%-Grenze.

**Urteil je Zoomfahrt:**
- `tempo_max` = Spitze von |v| (% pro s), `tempo_mittel` = Mittel über die Fahrt.
- `ruck` = Maß für Ungleichmäßigkeit: Variationskoeffizient von |v| über 0,2-s-Schritte im Kern der Fahrt (ohne je 10 % am
  Anfang/Ende); Stocken (|v| fällt mitten in der Fahrt unter 20 % der Spitze und steigt wieder) zählt als ruckartig.
- `sprung_proz` = größte Änderung von ln(KB) innerhalb von 0,12 s (`ZOOM_SPRUNG_S`, 3 Frames bei 25 fps) auf der
  median-gefilterten 25-fps-Reihe, also vor dem Gleitmittel des Tempos (Nachtrag Final Review 21.09., siehe „Fehler
  und Randfälle").
- **schnell**, wenn `tempo_max` > `zoom_schnell_proz_s` **oder** `ruck` > `zoom_ruck_max` **oder** `sprung_proz` ≥
  `zoom_sprung_proz` (`sprunghaft`); sonst **langsam**.
- Startwerte bis zur Kalibrierung: `zoom_schnell_proz_s: 20`, `zoom_ruck_max: 0.6`.

**Neue Felder je Clip** (`telemetrie.json`, Cache):

```
kb_verlauf   [[t_s, kb_mm], …]   5 Werte je Sekunde (zoom_verlauf_hz); bei gleichbleibender Brennweite genau ein Eintrag [0.0, kb]
zooms        [{von_s, bis_s, von_mm, bis_mm, tempo_max, tempo_mittel, ruck, ruckartig, sprung_proz, sprunghaft,
               urteil: langsam|schnell}, …]
zoomfahrt    true, wenn zooms nicht leer ist (ersetzt die bisherige kb_max/kb_min-Regel)
```

Entfällt: `brennweitenklasse`. Bleibt: `kb_mm` (Median), `kb_min`, `kb_max`, `brennweite_mm`, `fokus_m`.
Ohne rtmd-Brennweite: `kb_verlauf` leer, `zooms` leer.

**`ruhige_fenster`:** Fenster, die eine schnelle Zoomfahrt schneiden, zählen nicht mehr als ruhig.

**Helfer (Abschnitt „Helfer für Stufe 2b und 6d"):**
- `kb_am(rec, t_s, spanne_s=0.5, seite="mitte") -> float | None` — Median der Brennweite über `spanne_s` an `t_s`
  (`seite="ende"`: die 0,5 s bis `t_s`; `"anfang"`: ab `t_s`); None ohne Verlauf.
- `kb_im_bereich(rec, von_s, bis_s) -> float | None` — Median im Bereich (für Stufe 2b).
- `zooms_im_bereich(rec, von_s, bis_s, nur_schnelle=True) -> list[dict]` — Zoomfahrten, die den Bereich schneiden.
- `brennweite_abstand(kb_a, kb_b) -> float` = max/min − 1; `gleiche_brennweite(kb_a, kb_b, abstand_max) -> bool`.
- `digitalzoom(kb_a, kb_b, zoom_a, zoom_b, cfg, a_erlaubt=True) -> tuple[str, float] | None` — Zoom für ein Paar, siehe Abschnitt 2.
- `brennweitenfolge(eintraege, cfg) -> list[dict]` — die ganze Regel als reine Funktion: Eingabe je Shot (in Record-Reihenfolge)
  `{id, rec_in, rec_out, kb_anfang, kb_ende, zoom_erzwungen}`; Ausgabe je Shot `{id, zoom, hinweis}`. Die Vorlagen rechnen nur
  `kb_anfang`/`kb_ende` über `kb_am` aus und rufen sie auf — getestet wird die Logik hier, nicht in den Vorlagen.

**Bericht (`telemetrie.md`):** Spalte Brennweite je Kamera in mm (Median, Spanne) statt weit/normal/tele; neuer Abschnitt
„Schnelle Zoomfahrten" (Clip, von–bis s, mm → mm, Tempo, ruckartig, Sprung in 0,12 s); der Index-Vergleich zeigt keine
Brennweite mehr (nur Perspektive Höhe und Haltung).

## 2 — Regeln im Probelauf (Vorlagen 3a und 6d)

Betroffen: `vorlagen/feinschnitt/broll_einsetzen.py` (Stufe 3a, `PLAN`) und `vorlagen/feinschnitt/feinschnitt_bauen.py`
(6d, `BROLL`). Beide laden `telemetrie.json` wie 6d heute (`TM.laden`, `TM.finden`, Config aus `load_config`).

**Schneller Zoom:** je Shot der tatsächlich genutzte Quellbereich (6d über `genutzter_quellbereich_s`, bei 50 % entsprechend
kürzer; 3a bei 100 %) → `zooms_im_bereich(…, nur_schnelle=True)`. Treffer = Hinweiszeile
„S07: schneller Zoom 2,4–3,1 s (24 → 70 mm, 85 %/s)"; kein Fehler, der Bau läuft. Bei Zeitlupe (6d, 50 %) zählt das
**sichtbare** Tempo (halb so hoch): ein Zoom, der nur wegen des Tempos schnell war, fällt weg, wenn er sichtbar unter der
Schwelle bleibt; ruckartige bleiben (Nachtrag 21.09., folgt aus „so, wie es im Schnitt aussieht").

**Gleiche Brennweite:** Shots nach Record-In sortiert; ein Paar A → B wird nur geprüft, wenn B direkt an A anschließt
(Record-Out A = Record-In B) und beide eine bekannte Brennweite haben. Verglichen wird die scheinbare Brennweite am Schnitt:
`kb_am(A, Quell-Out A, seite="ende") × Zoom A` gegen `kb_am(B, Quell-In B, seite="anfang") × Zoom B`. Unter 20 % Abstand →
digitaler Zoom:
- Kandidaten sind beide Shots. Für den Shot mit der längeren scheinbaren Brennweite reicht der Faktor `digitalzoom_faktor`
  (1,25); für den kürzeren braucht es `1,25 × (längere / kürzere)`. Zulässig ist ein Kandidat, wenn vorhandener Zoom × Faktor
  ≤ `digitalzoom_max` (1,5). Gewählt wird der zulässige Kandidat mit dem kleineren Gesamtzoom (mehr Reserve), bei Gleichstand B.
- Neue V3-Items haben Zoom 1,0 (Begradigen setzt nur die Interview-Spuren V1/V2, die 9:16-Füllung steckt im Timeline-Scaling
  „scaleToCrop", nicht in `ZoomX`) — „vorhandener Zoom" ist also der in dieser Folge schon vergebene digitale oder ein
  erzwungener Zoom.
- Die Paare werden von links nach rechts abgearbeitet; ein gesetzter Zoom zählt für das nächste Paar mit. Shot A eines Paares
  kommt nur in Frage, wenn er noch keinen Zoom hat und der Zoom den Schnitt zu seinem Vorgänger nicht wieder „gleich" macht;
  sonst nur B.
- Kein Kandidat zulässig → Hinweis „S12: gleiche Brennweite wie S11 (50/52 mm), Zoom nicht möglich (1,5×-Grenze)".
- Probelauf zeigt je gesetztem Zoom: „S12: 50 → 52 mm am Schnitt, Zoom 1,25× auf S12".

**Spalte `zoom`:** optional — 3a: 7. Spalte von `PLAN`; 6d: 8. Spalte von `BROLL` (nach `stabil`, dort `None` = Vorschlag).
Eine Zahl erzwingt diesen Zoom (auch 1.0 = kein digitaler Zoom für diesen Shot); weggelassen = Automatik. Ein erzwungener
Wert unter 1,0 (Rand würde sichtbar) oder über `digitalzoom_max` ist ein Plan-Fehler. Ein in 3a erzwungener Zoom muss in
6d als Spalte 8 übernommen werden; den automatischen rechnet 6d aus den eigenen Quellbereichen neu.

**Bau:** Der Zoom wird nach dem Append per `SetProperty("ZoomX"/"ZoomY")` gesetzt (Zoom auf die Bildmitte, Pan/Tilt
bleiben 0); der Readback prüft den Wert, die Tabelle im Bericht nennt ihn. Ohne Telemetrie läuft alles wie bisher
(Hinweis „keine Telemetrie — Brennweitenregel nicht geprüft").

## 3 — Stufe 2b (`index_sections.py`)

- Je Abschnitt `brennweite_mm` = `kb_im_bereich` (eine Nachkommastelle) und `zoom` = `keiner` | `langsam` | `schnell` (die
  schnellste Zoomfahrt im Abschnitt).
- `brennweite` (Claudes Klasse) wird nicht mehr überschrieben; `felder_quelle` und `claude` führen nur noch
  `perspektive_hoehe`. Altdaten gibt es keine: Stufe 2b lief seit dem Merge noch auf keiner Charge mit Telemetrie
  (MEK-Index vom 04.09., ohne `felder_quelle`).
- Kontextzeile: „KB 71,6 mm" (bei Zoom: „KB 24–70 mm, langsamer Zoom") statt „= tele".

## 4 — Kalibrierung

1. Telemetrie-Lauf über die B-Roll von Wurst & Liebe (Charge `projects/Wurst & Liebe/Social-Reels/2026-08 Dreh 05.08`,
   Clip-Quellen per `--ordner` auf die B-Roll-Ordner am NAS, nur lesend) und über MEK (Cache wird wegen des Config-Hashs
   neu gemessen).
2. Referenz „ok": die Drehteller-Closeups von W&L — gefunden über die Sichtungsdaten der Charge; sind sie nicht eindeutig,
   nennt der User 2–3 Clipnamen.
3. Stichprobe: 8–10 Zoomfahrten knapp um die vorläufigen Schwellen (Tempo, Ruck) als **ein** Beispielvideo (je 3–5 s,
   Nummer eingeblendet, 1080p) in NIRO Review (`review.py hinzufuegen`); der User kommentiert je Nummer „ok" oder „zu schnell".
4. Schwellen `zoom_schnell_proz_s` und `zoom_ruck_max` so setzen, dass die „ok"-Beispiele und die Drehteller-Zooms
   langsam, die „zu schnell"-Beispiele schnell sind; Werte und Beispiele im Spec-Nachtrag und im WORKFLOW festhalten.
5. Gegenprobe: W&L-Drehteller-Zooms → langsam, schnelle MEK-Zooms (z. B. a7 IV 74 → 169 mm) → schnell.

## Konfiguration (`defaults.yaml`, Block `telemetrie:`)

| Schlüssel | Start | Bedeutung |
|---|---|---|
| `zoom_min_proz` | 3.0 | Mindeständerung der Brennweite für eine Zoomfahrt (%) |
| `zoom_schnell_proz_s` | 20.0 | Spitzentempo, ab dem eine Zoomfahrt schnell ist (% pro s) — Kalibrierung |
| `zoom_ruck_max` | 0.6 | Ungleichmäßigkeit, ab der eine Zoomfahrt als ruckartig (= schnell) gilt — Kalibrierung |
| `zoom_sprung_proz` | 12.0 | Sprung: Änderung der Brennweite in 0,12 s (%, ln), ab der eine Zoomfahrt schnell ist; = `zoom_schnell_proz_s` × 0,12 s (100 %/s × 0,12 s), nur zusammen ändern (Final Review 21.09.) |
| `zoom_verlauf_hz` | 5 | Auflösung von `kb_verlauf` |
| `brennweite_gleich_max` | 0.20 | unter diesem Abstand gilt die Brennweite als gleich |
| `digitalzoom_faktor` | 1.25 | Zoom für den Shot mit der längeren scheinbaren Brennweite |
| `digitalzoom_max` | 1.5 | Obergrenze für das Produkt aller Zooms eines Shots |

Entfällt: `brennweite_klassen_kb`. Der Config-Hash der Telemetrie ändert sich dadurch → jeder Clip wird einmal neu gemessen.

## Fehler und Randfälle

| Fall | Verhalten |
|---|---|
| Clip ohne rtmd-Brennweite (Drohne) | keine Zoom- und Brennweitenprüfung für ihn; Paar mit ihm wird übersprungen |
| keine `telemetrie.json` | Vorlagen laufen wie bisher, eine Hinweiszeile |
| Datensätze genutzter Clips von vor der Umstellung (rtmd ohne `kb_verlauf`) oder mit anderem `config_hash` | Hinweiszeilen im Probelauf („N Clips ohne Brennweitenverlauf (alte Telemetrie)", „N Clips mit anderen Telemetrie-Schwellen gemessen" — `autocut_telemetrie.py` neu laufen lassen); sonst bliebe die Regel stumm (Final Review 21.09., `telemetrie_hinweise`) |
| erzwungener `zoom` < 1,0 oder > `digitalzoom_max` | Plan-Fehler (Bau stoppt) |
| schneller Zoom im genutzten Bereich | Hinweis, kein Fehler |
| Verlauf mit Sprüngen (Klarbild-Zoom a7 IV schaltet stufig) | Sprung innerhalb weniger Frames = Zoomfahrt mit hohem Tempo → schnell. Umsetzung (Final Review 21.09.): ändert sich ln(KB) innerhalb von 0,12 s (3 Frames, vor dem 0,2-s-Gleitmittel, das die Spitze eines Sprungs auf Δln / 0,2 s kappt) um mindestens `zoom_sprung_proz` (12 % = 100 %/s × 0,12 s: die Tempo-Grenze des Users auf dem kürzeren Fenster), ist die Fahrt schnell; Felder `sprung_proz` und `sprunghaft` je Fahrt. Sonst gälten mit 100 %/s Sprünge unter ≈ 20 % als langsam (50 → 60 mm in 2 Frames: 91 %/s) |

## Tests (pytest, ohne NAS, ohne Resolve)

- Zoom-Erkennung an künstlichen Verläufen: Festbrennweite (keine Fahrt), Rauschen/Quantisierung (keine), langsamer
  gleichmäßiger Zoom (langsam), schneller Zoom (schnell), ruckartiger Zoom mit Stocken (schnell), Stop-and-go unter 0,3 s
  (eine Fahrt), stufiger Sprung (schnell), `kb_verlauf` kompakt bei Festbrennweite.
- `ruhige_fenster` ohne Fenster mit schnellem Zoom.
- Helfer: `kb_am` (Seiten, Randbereiche, ohne Verlauf), `kb_im_bereich`, `zooms_im_bereich`, Abstand/`gleiche_brennweite`
  an der 20-%-Grenze, `digitalzoom` (längerer Shot 1,25×, kürzerer mit Aufschlag, vorhandener Zoom, 1,5×-Grenze, Gleichstand).
- `brennweitenfolge`: automatischer Zoom bei gleicher Brennweite, Spalte `zoom` erzwingt/verbietet, Kette über drei und mehr
  Shots (A schon gezoomt → nur B; kein Rückfall auf „gleich" zum Vorgänger), Lücke = keine Prüfung, unbekannte Brennweite,
  Zoom nicht möglich → Hinweis.
- Vorlagen 3a und 6d: Aufruf der Helfer, Hinweiszeilen, Spalte `zoom`, `SetProperty` beim Bau — Text-/Syntaxprüfung wie
  bisher plus je ein Probelauf-Test der Planfunktion mit Telemetrie-Datensätzen, soweit die Vorlage ohne Resolve ladbar ist.
- Stufe 2b: `brennweite_mm`/`zoom` je Abschnitt, Claudes Klasse bleibt unangetastet, Kontextzeile in mm.
- Bericht: mm-Spalte, Abschnitt „Schnelle Zoomfahrten", kein Brennweiten-Vergleich mehr.

## Doku

`WORKFLOW-AutoCut.md`: Abschnitt Telemetrie (Zoomfahrten, `kb_verlauf`, Schwellen nach Kalibrierung), Stufe 3a Regeln
(„Kein Einstellungs-Doppel in Folge" um „nie zweimal dieselbe Brennweite; sonst digitaler Zoom" ergänzen; schnelle Zooms
meiden), 6d (Spalte `zoom`), Stufe 2b (mm statt Klasse). `vorlagen/README.md`: Spalte `zoom`. `README.md`: Arbeitsdateien
unverändert, Kurzbeschreibung Telemetrie um Zoomfahrten ergänzen.

## Nicht enthalten

Optische Zoom-Erkennung für Drohnen; automatisches Umsortieren der Shots (bleibt Claudes redaktionelle Entscheidung im
Plan); automatisches Kürzen schneller Zooms (User: nur Hinweis); Pan-Nachführung beim digitalen Zoom (Zoom auf die Mitte).

## Nachtrag 21.09.2026 — Kalibrierung Zoom

**Datenbasis:** Telemetrie-Läufe mit dem Code dieses Plans über die B-Roll von Wurst & Liebe (2026-08 Dreh 05.08,
„00 - B-Roll", nur rtmd: 324 Clips, 499 Zoomfahrten in 121 Clips) und MEK (2026-06 Ads und Imagefilm Dreh, 463 Clips,
444 Zoomfahrten in 178 Clips), je 0 Fehler. Spitzentempo P10/25/50/75/90: W&L 21/38/90/175/264 %/s, MEK
21/41/82/153/241 %/s — die meisten Fahrten sind Umzooms zwischen zwei Einstellungen. Mit den Startwerten galten 473 von
499 (95 %) bzw. 418 von 444 (94 %) als schnell; nach der Kalibrierung sind es 242 (48 %) und 191 (43 %), ruckartig bleiben
24 bzw. 5.

**Beispiele** (Kalibrier-Charge `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Zoomfahrten`, `zoom_beispiele.py`, NIRO Review
„Zoom-Beispiele" V1, 38 s):

| Nr | Charge | Clip | von–bis s | mm → mm | Spitze %/s | ruck | Auswahlgrund | Urteil User | Urteil neu |
|---|---|---|---|---|---|---|---|---|---|
| 1 | W&L | a7MK4_20260805_0091 | 8,2–12,2 | 146,6 → 283,8 | 30 | 0,27 | Tempo um 30 | ok | langsam |
| 2 | W&L | a7MK4_20260805_0080 | 10,4–16,0 | 116,7 → 283,8 | 28 | 0,24 | Drehteller | ok | langsam |
| 3 | MEK | a7MK4_20260624_9900 | 13,2–14,6 | 158,7 → 178,7 | 14 | 0,23 | Tempo um 15 | ok | langsam |
| 4 | W&L | a7MK4_20260805_0090 | 14,8–20,9 | 110,4 → 283,8 | 30 | 0,30 | Drehteller | ok | langsam |
| 5 | MEK | a7MK4_20260624_9933 | 7,9–11,6 | 234,9 → 184,5 | 18 | 0,74 | ruckartig | ok | langsam |
| 6 | W&L | FX3_0716 | 36,0–37,9 | 36,7 → 64,8 | 55 | 0,47 | Tempo um 55 | ok | langsam |
| 7 | MEK | FX3_9664 | 98,4–100,8 | 39,3 → 51 | 20 | 0,40 | Tempo um 20 | ok | langsam |
| 8 | MEK | a7MK4_20260624_9855 | 10,1–11,1 | 117,7 → 141,9 | 40 | 0,49 | Tempo um 40 | ok | langsam |
| 9 | MEK | a7MK4_20260624_9831 | 13,6–14,4 | 189,2 → 169,2 | 25 | 0,25 | Tempo um 25 | ok | langsam |
| 10 | W&L | a7MK4_20260805_0070 | 72,0–74,2 | 241,2 → 283,8 | 21 | 0,77 | ruckartig | ok | langsam |

**Urteil (Chat 21.09.):** alle 10 „ok" — „sie wackeln zwar, aber das testen wir ja gerade nicht" (Wackeln misst `wackeln`,
nicht die Zoom-Regel). Wo „zu schnell" beginnt, zeigte die Stichprobe damit nicht; auf Rückfrage (zweite Runde mit
60–200 %/s, vorsichtig ab 60 oder grob ab 100) entschied der User **„grob: ab 100 %/s"**.

**Rechnung** (`zoom_kalibrieren.py`, Raster Tempo 15–100 × ruck 0,4–1,0 × Stocken 0/0,1/0,15/0,2; Fälle: 10 Urteile plus
Referenz „schnell" = schnellster Drehteller-Rück-Zoom a7MK4_20260805_0698, 283,8 → 110,4 mm, 194 %/s). Fehler je Tempo
(bestes ruck/Stocken): 15: 9 · 20: 7 · 25: 6 · 30: 4 · 35: 2 · 40–55: 1 · 60–100: 0. Bei 100 %/s fehlerfrei nur mit
Stocken 0 und ruck ≥ 0,8 — die Stocken-Regel markierte die „ok"-Fahrten 5 und 10 (und den ersten Drehteller-Zoom von
0085) als schnell.

**Gesetzt:** `zoom_schnell_proz_s` 100 (User), `zoom_ruck_max` 1,0 (Skript-Empfehlung 0,8 bei gleicher Fehlerzahl; 1,0
für Abstand zu den ruckartigen „ok"-Beispielen 0,74/0,77, passend zu „grob"), `zoom_stocken_anteil` 0,0 = Regel aus.

**Gegenproben:** gleichmäßige Drehteller-Zooms 28–39 %/s langsam; Rück-Zooms 0697/0698/0699/0700 (123–194 %/s) schnell;
0085-Rück-Zoom 99 %/s und 0087 89 %/s knapp unter der Grenze → langsam (Entscheidung „grob"; 0085 seit dem
Sprung-Kriterium schnell, siehe unten). Die im Plan vorgesehene
MEK-Gegenprobe a7MK4_20260624_9885 (109 → 169 mm) hat nur 50 %/s Spitze → langsam; sie taugt bei dieser Grenze nicht als
„schnell"-Referenz, der Regressionstest nimmt stattdessen den Rück-Zoom 0698.

**Fixture/Test:** `tools/autocut/tests/fixtures/kb_zoom_kalibrierung.json` (Drehteller 0090 „langsam", Rück-Zoom 0698
„schnell", KB-Reihen aus der rtmd-Spur), `test_kalibrierung_zoom_an_echten_reihen` — mit den Startwerten 20/0,6/0,2 wäre
die Drehteller-Referenz „schnell".

**Offen:** Der Bereich 55–100 %/s ist nicht durch Urteile belegt (User: „grob"). Melden die Hinweise zu wenig, die Grenze
später senken; eine zweite Stichprobe mit 60–200 %/s ist mit `zoom_beispiele.py` schnell gemacht.

**Sprung-Kriterium (Final Review 21.09.2026):** Das 0,2-s-Gleitmittel des Tempos kappt die Spitze eines stufigen Sprungs
auf Δln / 0,2 s — mit 100 %/s galten Sprünge unter ≈ 20 % als langsam (50 → 60 mm in 2 Frames 91 %/s, 24 → 28 mm in
1 Frame 77 %/s, 70 → 85 mm in 1 Frame 97 %/s), obwohl die Tabelle „Fehler und Randfälle" sie schnell verlangt. Neu je
Fahrt `sprung_proz` = größte Änderung von ln(KB) innerhalb von 0,12 s (`ZOOM_SPRUNG_S`) auf der median-gefilterten Reihe;
ab `zoom_sprung_proz` 12 % ist die Fahrt schnell (`sprunghaft`; Test: `test_sprung_zooms_mit_ausgelieferten_werten`).
12 % = 100 %/s × 0,12 s: das Kriterium misst die Grenze des Users („grob ab 100 %/s") auf dem kürzeren Fenster, statt sie
zu senken — gleichmäßige Fahrten bleiben bis 100 %/s langsam (Controller-Entscheidung 21.09.; der erste Wert 10 % hätte
die Grenze auf ≈ 83 %/s gesenkt und 9 Fahrten der Kalibrier-Reihen mit 66–99 %/s schnell gemacht). Prüfung an den
echten Reihen (`_intern/kb_reihen.json` der Kalibrier-Charge): Beispiele 1–10 haben 2,5–7,2 % (alle weiter langsam,
Nr. 6 mit 55 %/s = 7,2 %), Drehteller 0090 4,4 % langsam, Rück-Zoom 0698 29,0 % schnell. In den Kalibrier-Reihen
wechseln drei Fahrten zu schnell: der Drehteller-Rück-Zoom 0085 (geglättet 98,7 %/s, in 0,12 s 12,1 % ≙ 101 %/s) und
zwei kurze Fahrten von FX3_9664 (66 %/s, 13,3 %); 0087 (10,8 %), drei Fahrten von 0070 (11,2–11,8 %) und zwei von MEK
9885 (10,1/11,2 %) bleiben langsam. Die Zählungen 242/191 oben stammen von vor dem Sprung-Kriterium. Bei Zeitlupe (6d)
zählt der sichtbare Sprung (`sprung_proz` × Tempo) wie das sichtbare Tempo; der Hinweis nennt den Sprung, wenn er und
nicht das Tempo den Zoom schnell macht; `telemetrie.md` zeigt ihn in der Spalte „Sprung in 0,12 s".
