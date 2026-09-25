# AutoCut — Schnittkanten frame-genau (Spec)

Datum: 2026-09-25 · Status: entworfen, nicht umgesetzt. Folgeschritt von
`docs/superpowers/specs/2026-09-23-autocut-broll-bereichsauswahl-design.md`; löst dort Abschnitt 2 (stabile Bereiche aus
2-s-Fenstern, „±1 s reicht für Shots von 2–5 s") und die beiden Bewegungs-Warnungen aus Abschnitt 5 ab.

## Anlass

Der erste Praxislauf der Bereichsauswahl (Klebl, Nachtlauf 24./25.09.) hat 32 B-Roll-Shots gesetzt; 97 % lagen in
gemessen ruhigen Läufen. Die Klebl-Session hat danach im Render vier Shots als wacklig eingestuft — **per Messung, nicht
durch den User**. Die Nachprüfung am 25.09. (Gyro frame-genau aus der rtmd-Spur, Skript
`projects/Klebl/…/_intern/analyse/bewegung_frames.py`, Befund im Klebl-`Protokoll.md`) bestätigt alle vier:

| Shot | Stelle | frame-genau |
|---|---|---|
| FX3_0260 1,5–3,5 s | V1 0:04 | Kamera schwingt bis 2,1 s nach (wackeln bis 0,29); Lauf laut Telemetrie ab 1,0 s |
| FX3_0700 7,0–9,64 s | V2 0:23 | In-Punkt 0,12 s nach schnellem Zoom 59 → 25 mm, wackeln bis 0,52; ruhig ab 7,28 s |
| FX3_0653 4,0–6,68 s | V2 0:53 | Schwenk läuft bis 5,0 s mit 2,3–3,9 px/Frame aus; im ganzen Clip kein ruhiger Lauf |
| FX3_0267 6,2–8,52 s | V2 0:34 | Schwenk bis 5,0 px/Frame am In-Punkt; ruhig frühestens ab 7,32 s |

Dasselbe Muster zeigen FX3_0705 (0,8 s Schwenk-Auslauf am In-Punkt) und FX3_0675 (In-Punkt 1–2 Frames nach einem Ruck).

**Ursachen — alle im Werkzeug:**
1. `stabile_bereiche()` baut Läufe aus 2-s-Fenstern im 1-s-Raster; die Einzelframes wirft die Messung weg. Grenzen
   liegen bis 1,2 s daneben — bei 2-s-Shots der halbe Shot.
2. Das Fenster-Mittel verdünnt kurze Stöße: FX3_0260 wackelt 1,2 s lang mit 0,16–0,29, das Fenster 1–3 s ergibt 0,13
   (< 0,15, also „ruhig").
3. `bewegung` = Mittel aus |dx| und |dy| — ein reiner Schwenk zählt halb; `bewegung_max` 2,0 lässt Schwenks bis ≈ 4
   px/Frame durch.
4. `verify_layout()` prüft nur „liegt im Lauf". FX3_0653 wurde 0,2 s verschoben, bis die Warnung schwieg; der Schwenk
   blieb gleich.
5. Nebenbefund: Gyro → Pixel rechnet mit der Median-Brennweite des Clips. 63 von 181 Klebl-Clips zoomen um mehr als
   20 % — dort ist die Bewegung abschnittsweise falsch skaliert (FX3_0700 im Shot mit 59,5 statt 25 mm).

**Prototyp** (frame-genau, 0,4 s geglättet, wackeln ≤ 0,15, Betrag der Bewegung ≤ Grenze): alle vier Shots fallen bei
jeder getesteten Grenze (1,0 / 1,5 / 2,0 px/Frame) aus den Läufen, die ruhigen Shots bleiben drin; nicht ruhig sind
dann 20 / 15 / 11 von 32. An den User-Urteilen: R2#12 („komplett ungewollt") bekommt nie einen Lauf; „ungewollt"-Beispiele
mit Lauf 0 / 0 / 1 (R2#14) bei 1,0 / 1,5 / 2,0, zwei bei 2,5–3,0 (R2#10, R2#14). Der WLC-Bereich FX3_8660 12,5–15,5 s,
den der User am 23.09. als gut benannt hat, ist ein sauber auslaufender Schwenk (2,9 → 0,8 px/Frame, wackeln ≤ 0,05) und
liegt erst ab 2,9 in einem Lauf. Die Grenze ist damit Sache des Users, nicht der Messung.

## Entscheidungen des Users (25.09.2026)

- **Ansatz:** Bewegung je Frame in der Telemetrie speichern; Läufe und Prüfung rechnen daraus, ohne Mediendatei.
- **Strenge:** Schnittkanten hart (Fehler, der Bau stoppt), Bewegung in der Mitte des Shots nur Warnung.
- **Grenze:** kurze Review-Runde (ca. 10 Einsetzer), parallel zur Umsetzung; am Ende ändert sich nur `bewegung_max`.
- Handkamera-Clips unterliegen derselben Kantenregel (im Entwurf genannt, kein Widerspruch).

## 1 — Messung (`telemetrie.py`)

- **Neue Reihe `verschiebung`** je Datensatz: `{"fps": 25.0, "t0_s": 0.0, "dx": [...], "dy": [...]}` — Verschiebung des
  Bildinhalts in px @480 je 25-fps-Frame, auf 2 Stellen gerundet, Frame `i` bei `t0_s + i / 25`. `t0_s` ist im Werkzeug
  immer 0,0 (ganzer Clip); Test-Fixtures dürfen die Reihe beschneiden. Beide Messwege schreiben sie: rtmd (Gyro) und
  optisch (Phasenkorrelation). Ohne Messung (`quelle: "keine"`, `fehler`) ist sie `None`.
- **Brennweite je Frame.** `verschiebung_aus_rate()` nimmt eine Zahl oder die KB-Brennweite je Frame (`kb_je_frame()`,
  auf die Länge der Gyro-Reihe gebracht, Ränder gehalten). Ohne Brennweitenverlauf bleibt der Median wie heute. Fenster,
  Haltung, Bewegungsart und `ruhige_fenster` rechnen aus derselben, jetzt richtig skalierten Reihe; ihre Form bleibt.
  `schwellen_px()` für die Bewegungsart-Klassen behält den Median.
- **Neu messen erzwingen.** `MESS_VERSION = 2` geht in `config_hash()` ein. Jeder alte Datensatz trägt damit einen anderen
  Hash, gilt im Cache als veraltet und wird beim nächsten `autocut_telemetrie.py` neu gemessen. Bis dahin greifen die
  bestehenden Hinweise (`HINWEIS_SCHWELLEN`, „erst `autocut_telemetrie.py`, dann `autocut_index_sections.py`").
- **Größe:** ≈ 250 Zeichen je Sekunde Material; `telemetrie.json` einer Charge wächst um ≈ 1–2 MB (MEK, 464 Clips).

## 2 — Bewegung je Frame und stabile Läufe (`telemetrie.py`)

- `bewegung_je_frame(rec, glatt_s)` → `(t0_s, wackeln, bewegung)` als numpy-Reihen je Frame, beide zentriert über
  `glatt_s` gemittelt (Ränder normiert wie `_tiefpass`):
  - `wackeln[i]` = Mittel aus |dx[i] − dx[i−1]| und |dy[i] − dy[i−1]| — dieselbe Größe wie `wackeln` der Fenster;
    Frame 0 übernimmt den Wert von Frame 1.
  - `bewegung[i]` = √(dx[i]² + dy[i]²) — der Betrag, nicht mehr das Achsmittel der Fenster. Ein reiner Schwenk zählt
    voll. (Die Fenster behalten ihr `bewegung` als Achsmittel; gemeint ist in dieser Spec immer die Reihe je Frame.)
- `ruhe_je_frame(rec, cfg)` → bool je Frame: `wackeln ≤ ruhig_max_px` **und** `bewegung ≤ bewegung_max` **und** der Frame
  liegt in keiner schnellen Zoomfahrt (`zooms[].urteil == "schnell"`, `[von_s, bis_s)`).
- `stabile_bereiche(rec, cfg)` rechnet neu aus `ruhe_je_frame`: maximale Folgen ruhiger Frames, mindestens
  `stabil_min_s` lang, Grenzen auf den Frame genau (2 Stellen), `bis_s` auf `dauer_s` gekappt. Rückgabeformat bleibt
  `[von_s, bis_s, wackeln_max, bewegung_max]` (Höchstwerte der geglätteten Reihen im Lauf) — Index, kompakter Index,
  `_usable_spans()` und Planer bekommen dieselben Felder, nur genau. Ohne `verschiebung` (alter Datensatz): `[]`.
- Beispiel Klebl (Prototyp, `bewegung_max` 2,0): FX3_0260 [1,0–11,52] → [2,12–11,04]; FX3_0700 [0–2, 3–6, 7–10, 13–15]
  → [3,2–5,64, 7,28–10,32]; FX3_0653 [0–2, 4–7] → keiner.

## 3 — Stufe 2b (`index_sections.py`)

`telemetrie_anwenden()` bleibt, wie sie ist: `stabil` je Abschnitt = die Läufe auf den Abschnitt geschnitten,
`stabil_quelle.laeufe` = die ungeschnittenen Läufe. `stabil_quelle` bekommt zusätzlich `glatt_s` (die Läufe hängen daran);
der Prüfer meldet eine Abweichung wie heute bei `bewegung_max`/`stabil_min_s` („mit anderen Stabil-Schwellen abgeleitet —
`autocut_index_sections.py` erneut laufen lassen").

## 4 — Prüfung (`broll_layout.py`, `verify_layout()`)

Für jeden Shot mit frischem Telemetrie-Datensatz (Hash wie heute) und `verschiebung` misst der Prüfer die tatsächlich
genutzten Quell-Frames (`_quellbereich_s()`):

- **Schnittkanten — Fehler.** Die ersten und letzten `kante_s` (0,3 s Timeline) des Shots müssen ruhig sein. Kante =
  alle Frames der Reihe mit `q_von ≤ t < q_von + kante_s·f` bzw. `q_bis − kante_s·f ≤ t < q_bis`; ruhig heißt dort
  `wackeln·f ≤ ruhig_max_px` und `bewegung·f ≤ bewegung_max`, mit `f = 1 / tempo` des Shots (Zeitlupe: sichtbare
  Bewegung, 0,3 s Timeline = 0,3·f s Quelle). Die Glättung reicht 0,2 s über die Kante hinaus — ein Sicherheitsabstand
  zur Bewegung davor bzw. danach. Meldung mit Stelle, Werten und Vorschlag:
  „Strecke 4 Szene 1 Shot 1 (FX3_0700.MP4 7–9,64 s): In-Punkt liegt in Bewegung (7,0–7,3 s: wackeln 0,52, Bewegung
  1,4 px/Frame) — gleich lang passend ab 7,28 s. Shot verschieben, anderen Bereich wählen oder `abweichung` mit Grund."
  - **Vorschlag:** die Lage gleicher Länge mit der kleinsten Verschiebung (in Frame-Schritten; bei gleichem Abstand die
    spätere), deren beide Kanten ruhig sind und die in dem erlaubten Bereich bleibt, in dem der Shot liegt
    (`_usable_spans(c, stabil=frisch)`; in geretteten Abschnitten zusätzlich in einem Lauf). Liegt der Shot in keinem
    erlaubten Bereich, gibt es schon den Lage-Fehler und keinen Vorschlag. Gibt es keine ruhige Lage: „im erlaubten
    Bereich keine ruhige Lage gleicher Länge — kürzer schneiden oder anderen Bereich". Ein Vorschlag, keine Automatik —
    der Plan bleibt beim Planer.
  - `abweichung: true` mit Grund hebt die Kantenregel auf, wie beim schnellen Zoom (gewollter Reißschwenk).
- **Mitte — Warnung.** Eine Warnung je Shot, wenn Frames zwischen den Kanten nicht ruhig sind — vom ersten bis zum
  letzten solchen Frame, mit den Höchstwerten: „Bewegung im Shot bei 7,8–8,1 s (wackeln 0,12, Bewegung 2,1 px/Frame) —
  Hinweis." Entfällt bei `abweichung`.
- **Gerettete Abschnitte** bleiben streng: der ganze Shot muss in einem Lauf liegen (Fehler wie heute, jetzt
  frame-genau). Ebenso hebt „Wackler" nur auf, wer ganz in einem Lauf liegt (`stabil_ok`).
- **Entfällt, weil ersetzt:** die Warnung „Schnittgrenze … liegt in einer Bewegungsspitze" (samt `bewegung_rand_s`,
  `bewegung_spitze_faktor`, `bewegung_grundniveau()`) und die Warnung „Bereich nicht als stabil gemessen" (samt
  `bewegung_max_im_bereich()`). `bewegung_spitzen` im Index bleibt als Hinweis für den Planer.
- Die Regeln zu schnellem Zoom und Brennweitenfolge bleiben unverändert und laufen unabhängig davon.

## 5 — Planer und Bericht

- `prompts/place-broll.md`: `stabil_laeufe`/`stabil` sind frame-genau; Kantenregel („In- und Out-Punkt je 0,3 s in
  ruhigen Frames — am sichersten den Shot ganz in einen Lauf legen; Bewegung in der Mitte ist erlaubt"); neue Zeile in
  der Fehlertabelle („In-/Out-Punkt liegt in Bewegung" → auf die vorgeschlagene Lage schieben oder anderen Bereich;
  gewollter Schwenk: `abweichung` + Grund). Die Zeile zu „Bereich nicht als stabil gemessen" entfällt.
- `telemetrie_bericht.py`: Spalte „ruhige Fenster (s)" wird „ruhige Läufe (s)" aus `stabile_bereiche()`, damit Bericht
  und Regeln dasselbe sagen.

## Konfiguration (`defaults.yaml`, `telemetrie:`)

| Schlüssel | Wert | Bedeutung |
|---|---|---|
| `ruhig_max_px` | 0,15 (unverändert) | jetzt auch je Frame, geglättet über `glatt_s` |
| `bewegung_max` | 2,0 bis zur Kalibrierung | **neu gedeutet:** Bewegung (Betrag, px/Frame) je Frame, geglättet — UNKALIBRIERT, Wert aus der Review-Runde |
| `glatt_s` | 0,4 (neu) | Glättung der Reihen je Frame |
| `kante_s` | 0,3 (neu) | Länge einer Schnittkante (Timeline-Sekunden) |
| `stabil_min_s` | 2,0 (unverändert) | kürzester Lauf |
| `bewegung_rand_s`, `bewegung_spitze_faktor` | entfallen | ersetzt durch die Kantenregel |

`glatt_s` und `kante_s` stehen in `OHNE_MESSWIRKUNG` (reine Ableitung, kein Neumessen). `fenster_s`/`schritt_s` bleiben —
Bewegungsart, Haltung und 6d (`stabil_vorschlag()`) lesen weiter die Fenster.

## Kalibrierung (Review-Runde, parallel zur Umsetzung)

Charge `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schnittkanten/`, Skript `_intern/skripte/kanten_beispiele.py` nach
dem Muster der Schwenk-Runde (`../2026-09 Schwenks/_intern/skripte/schwenk_beispiele.py`): 1080×1920, 25p, S-Log3 über
LUT LC-709 Type A, Nummer im Bild, Reihenfolge gemischt (fester Seed), je Beispiel genau der Einsetzer, wie AutoCut ihn
setzen würde.

- **Beispiele (≈ 12):** Klebl FX3_0260, 0700, 0653, 0267, 0705, 0675 (wie gebaut); die Mitzieh-Schwenks FX3_0252, 0710,
  0674; WLC FX3_8660 12,5–15,5 s als „gut"-Anker; 1–2 Handkamera-Kanten; 2–3 korrigierte Varianten (z. B. FX3_0260 ab
  2,2 s, FX3_0700 ab 7,32 s).
- **Vorhersage vor den Urteilen:** je Beispiel `wackeln`/`bewegung` an beiden Kanten → `_intern/vorhersagen.json`,
  festgeschrieben vor der Ablage.
- **Ablage:** NIRO Review (`review.py hinzufuegen`), Link im Chat. Der User urteilt je Nummer „so schneiden: ja/nein",
  gern mit „stört am Anfang / in der Mitte / am Ende" → `_intern/urteile.json`.
- **Ableitung:** `bewegung_max` zwischen dem schnellsten „ja" und dem langsamsten „nein" (Bewegung an der Kante); `ruhig_max_px`
  wird an den Wackel-Beispielen gegengeprüft. Lassen sich die Urteile mit einer Grenze nicht trennen, wird das mit dem
  User besprochen, nicht passend gemacht.

## Fehler und Randfälle

- **Alter Datensatz ohne `verschiebung`:** hat nach `MESS_VERSION` ohnehin einen anderen Hash → bestehende Hinweise, keine
  Läufe, keine Kantenprüfung für diesen Shot (gezählt wie heute unter „mit anderen Schwellen gemessen").
- **Clip ohne Telemetrie / mit `fehler`:** keine Kantenprüfung; die bestehende Meldung zählt die Shots.
- **Kurzer Shot** (unter 2 × `kante_s`): die Kanten überlappen, der ganze Shot gilt als Kante.
- **Kante außerhalb der Reihe** (Reihe kürzer als der genutzte Bereich, z. B. letztes rtmd-Sample fehlt): geprüft wird
  der vorhandene Teil; ohne einen einzigen gemessenen Frame an einer Kante eine Warnung „Kante ohne Messung", kein Fehler.
- **Optischer Weg** (Drohne, Actioncam): gleiche Regeln für beide Wege. Das Rauschen der Phasenkorrelation je Frame ist
  ungeprüft — der Plan misst vorab mindestens fünf ruhige DJI-Clips einer bestehenden Charge; fällt ein vom Auge ruhiger
  Drohnen-Shot durch, wird das vor dem Merge mit dem User geklärt.
- **Zeitlupe `tempo` 4:** `f = 0,25`; Kanten 0,075 s Quelle.

## Tests (pytest, ohne NAS, ohne Resolve, ohne API)

- **Unit-Tests zuerst (TDD):** Reihe und `t0_s`, Brennweite je Frame in `verschiebung_aus_rate()`, `MESS_VERSION` im Hash,
  `bewegung_je_frame()` (Achsbetrag, Glättung, Ränder), `ruhe_je_frame()` inkl. Zoom-Ausschluss, `stabile_bereiche()`
  (frame-genaue Grenzen, Mindestlänge, `[]` ohne Reihe), Kantenprüfung (Fehler an der Kante, Warnung in der Mitte,
  `abweichung`, Zeitlupe, kurzer Shot, Kante ohne Messung), Vorschlag (früher/später, Grenzen des erlaubten Bereichs,
  keiner möglich), `stabil_quelle.glatt_s`, entfallene Warnungen und Config-Schlüssel.
- **Fixtures neu vom NAS** (`tests/fixtures/gen_bereiche_fixture.py`, einmalig von Hand): der Generator misst die 30
  Urteils-Clips (MEK) und die 4 WLC-Clips direkt mit `clip_messen()` (Pfad-Umleitung SSD → NAS) statt `telemetrie.json`
  der Chargen zu lesen — die Chargen bleiben unberührt. Neu: `bereiche-klebl.json` mit den 32 gebauten Shots (Bereich,
  `tempo`, Reihe ± 3 s) und nach der Review-Runde den Urteilen. Reihen werden auf den Bereich ± 10 s bzw. ± 3 s beschnitten
  (`t0_s`).
- **Abnahme:** R2#12 ohne Lauf; höchstens 2 der 24 „ungewollt"-Beispiele mit Lauf; jede Review-Nummer mit „ja" besteht
  die Kantenprüfung, jede mit „nein" fällt durch; die frame-genauen Läufe der vier WLC-Clips als Änderungsmelder.

## Umstieg

Je Charge beim nächsten AutoCut-Lauf: `autocut_telemetrie.py` (misst alles neu, ≈ 2 s je Clip übers NAS, Klebl 181
Clips ≈ 3–6 min), dann `autocut_index_sections.py` (aus dem Cache, keine API-Kosten). Der bezahlte Index bleibt.
Fertige Timelines und Pläne werden nicht angefasst; ein alter Plan meldet beim nächsten Prüfen die neuen Fehler.

## Doku

- `tools/autocut/WORKFLOW-AutoCut.md`: Telemetrie (Reihe, Brennweite je Frame, Neumessen), Stufe 2b, Stufe 3
  (Kantenregel, Fehlertabelle), Kalibrier-Stand von `bewegung_max`.
- `tools/autocut/README.md`: Tabellenzeile.
- `tools/autocut/prompts/place-broll.md`: siehe Abschnitt 5.
- Spec vom 23.09.: Vermerk „Abschnitt 2 und die Bewegungs-Warnungen aus Abschnitt 5 abgelöst durch
  `2026-09-25-autocut-schnittkanten-framegenau-design.md`".

## Nicht enthalten

- **Automatisches Verschieben** von In-Punkten — nur der Vorschlag in der Meldung.
- **Bewegung relativ zum Bildformat.** px @480 gilt für Hoch- und Querformat gleich, obwohl ein waagerechter Schwenk im
  Hochkant-Bild relativ 1,8× schneller wirkt. Die Kalibrierung läuft an Hochkant-Material (Hauptformat); ein Umrechnen
  käme erst, wenn Querformat-Läufe danebenliegen.
- **Absicht erkennen** (gewollter vs. ungewollter Schwenk) — bleibt `abweichung` mit Grund.
- **6d** (`stabil_vorschlag()`) bleibt auf den Fenstern.
- **Klebl neu bauen** — die Feinschnitt-Session korrigiert die Shots dort von Hand; Klebl dient nur als Testmaterial.
- **O-Ton-Nachlauf in Folgewörter** (Befund der Klebl-Feinschnitt-Session) — eigene Aufgabe.
