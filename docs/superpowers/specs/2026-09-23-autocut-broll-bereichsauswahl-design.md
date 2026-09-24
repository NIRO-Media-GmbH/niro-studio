# AutoCut — B-Roll-Auswahl auf Bereichsebene (Spec)

Datum: 2026-09-23 · Status: entworfen, nicht umgesetzt. Folgeschritt von
`docs/superpowers/specs/2026-09-22-autocut-broll-auswahl-telemetrie-design.md` (Telemetrie in der Auswahl).

**Berichtigt 24.09.2026** nach dem Schluss-Review (Task 8, User-Entscheid): Stufe 2b speichert die ungeschnittenen
stabilen Läufe in `stabil_quelle.laeufe`, `stabil` je Abschnitt hat keine Mindestlänge je Stück, und stabile Stücke
legen sich nur innerhalb desselben Laufs zusammen (Abschnitt 3, „Fehler und Randfälle"; „Erste Probe" Schritt 3: der
Nachlauf braucht nach `--force` die API). Ein gesperrter Mangel, den ein Clip nur clip-weit nennt und kein Abschnitt
führt, sperrt nicht — `verify_layout()` warnt dann einmal je Clip („Bild prüfen").

## Anlass

Beim WLC-Test am 23.09. (`projects/WLC/Recruiting/2026-07 Erster Dreh/Protokoll.md`, Abschnitt „Nachtrag gleicher
Tag — Review des Users: Auswahl auf falscher Ebene") hat der User vier verworfene Clips zurückgeholt: „diese shots
hätte ich zB mit ins video reingenommen, man müsste sie halt trimmen teilweise aber da sind gute Stellen dabei."

Die Auswahl arbeitet auf zu grober Ebene. `maengel` und `verwendbar` aus Stufe 2 hängen am ganzen Clip, die
Abschnitte aus Stufe 2b sind 8–40 s lang. Ein Clip mit einer verwackelten Sekunde fliegt komplett raus, obwohl 90 %
davon brauchbar sind. Derselbe Befund steht schon in der Kalibrierung vom 22.09. („ein Filter auf Clip-Ebene würde
die brauchbaren Teile mit wegwerfen") — hier ist er an zweitem Material bestätigt.

## Drei Befunde vor dem Entwurf

**Befund 1 — Der Index verortet inhaltliche Mängel bereits, der Prüfer ignoriert das.** `prompts/index-clip.md:31`
schreibt ausdrücklich vor: „Ein Mangel steht auch dann in der Liste, wenn er nur in einem Abschnitt auftritt; welcher
Abschnitt betroffen ist, steht in dessen `beschreibung` und `verwendbar`." FX3_8636 hält sich daran — Abschnitt
0–4 s `verwendbar=false` („lächelt in Richtung Kamera"), 4–8 s und 8–11,5 s `verwendbar=true`. Trotzdem sperrt
`verify_layout()` (`broll_layout.py:656`) den **ganzen Clip** über `maengel & forbidden` plus
`personen.blick_in_kamera`. Der Clip fiel nicht am Index durch, sondern an einer Regel, die ein bewusst clip-weites
Feld shot-genau benutzt. Telemetrie kann diesen Fall nicht retten — er ist kein Messproblem.

**Befund 2 — Abschnitte sind in beide Richtungen zu grob.** Bei FX3_8663 ist 0–8 s `verwendbar=true`; genau dort
liegen die Fenster mit Bewegung 3,6–10,3. Ein Shot bei 2–5 s wäre formal regelkonform und unbrauchbar. Umgekehrt
verdeckt ein `verwendbar=false` über 8 s die guten Sekunden darin.

**Befund 3 — Die Messung widerspricht „Wackler" nur am unteren Rand sauber.** Über alle 51 indexierten WLC-Clips:

| | n | `wackeln` min / Median / max |
|---|---|---|
| Clips mit Mangel „Wackler" | 9 | 0,059 / 0,365 / 2,197 |
| Clips ohne | 42 | 0,012 / 0,079 / 0,688 |

Die beiden vom User zurückgeholten (FX3_8641 0,059 · FX3_8660 0,077) sind die zwei niedrigsten der Wackler-Gruppe
und liegen unter dem Median der Gruppe *ohne* Wackler. Am oberen Rand überlappen beide Gruppen — eine Grenze auf dem
Clip-Mittelwert ist also nicht tragfähig, ein Bereichsurteil schon.

**Die Reihenfolge der Hebel ist damit umgedreht:** solange die Mangel-Sperre clip-weit greift, holt die Messung fast
nichts zurück. Gerechnet an den 51 WLC-Clips, Kandidat = Lauf benachbarter Fenster mit `wackeln ≤ 0,15` und
`bewegung ≤ 2,0`, mindestens 2 s:

| `forbidden_maengel` der Charge | verworfene Abschnitte in nicht clip-gesperrten Clips | davon mit stabilem Bereich |
|---|---|---|
| Standard inkl. „Logo/Marke" | 7 | **0** (0 s) |
| WLC-korrekt, ohne „Logo/Marke" | 21 | **10** (69 s) |
| ganz ohne Sperre (Obergrenze) | 38 | **20** (128 s) |

Die Telemetrie sagt *wo* in einem Clip geschnitten werden kann. Ob der Clip überhaupt in Frage kommt, entscheidet
weiter der Index — nur eben je Abschnitt statt je Clip.

## Was der Testsatz vom 22.09. hier misst und was nicht

Die 30 Urteile aus `projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/` beantworten „gewollt vs. ungewollt"
(Absicht). Der neue Mechanismus beantwortet „ruhig genug zum Schneiden". Ein *gewollter* Schwenk ist nicht ruhig;
ein Vorhersage-Test gegen die Labels würde den Mechanismus aus den falschen Gründen durchfallen lassen, und die
triviale Konstante „immer ungewollt" heißt hier übersetzt „nie etwas vorschlagen" — also der heutige Zustand.

Was sauber überträgt, ist die **Fehlalarm-Richtung**: der Mechanismus darf in Material, das der User als unbrauchbar
bezeichnet hat, keine schneidbare Stelle behaupten. Gemessen an der MEK-Telemetrie (neu gemessen 23.09.,
Config-Hash `40b5745652f3`, derselbe Stand wie WLC):

| Schwelle | Beispiele mit Kandidat | Treffer | Fehlalarm | Verpasst |
|---|---|---|---|---|
| `wackeln ≤ 0,15` allein | 5 / 30 | R2#10 („brauchbar am Anfang") → Kandidat 2,5–5 s = genau der Anfang | R2#9: `wackeln` 0,03–0,18, aber `bewegung` 3,1–5,3 — glatter schneller Schwenk, User „ungewollt" | R2#4, R2#8 („brauchbarer Teil in der Mitte") |
| dazu `bewegung ≤ 2,0` | 4 / 30 | wie oben | keiner | dieselben zwei |

R2#12 („**komplett** ungewollt") bekommt in beiden Fällen nichts — der wichtigste Nicht-Treffer sitzt.

Die zwei Verpassten sind ehrlich: dort liegt der ruhigste Wert bei `wackeln` 0,19–0,26, also über der Schwelle. Der
User meint mit „brauchbar" dort etwas Weicheres als „ruhig". Genau deshalb darf der Mechanismus **vorschlagen und
nicht entscheiden**.

`wackeln` misst Zittern, nicht Tempo. R2#9 zeigt, dass ein glatter schneller Schwenk danach „ruhig" heißt und als
2-s-Einsetzer trotzdem nichts taugt. Deshalb der zweite Deckel auf `bewegung`. Datenlage: die vier vom User
zurückgeholten Bereiche haben maximal `bewegung` **1,64** (FX3_8660 bei 12,5 s), der einzige Fehlalarm liegt bei
**3,1–5,3**; 2,0 liegt in der Lücke, mit je einem Datenpunkt auf jeder Seite. Der Wert ist damit ein **Startwert,
nicht kalibriert**, und wird so in `defaults.yaml` gekennzeichnet.

Der Grundsatz vom 22.09. („eine nicht kalibrierte Regel darf nichts blockieren") bleibt gewahrt: der Deckel verengt
nur eine **neue Zugabe**. Er verwirft nichts, was der Index heute schon erlaubt.

## 1 — Stufe 2 (`broll_index.py`): Mängel je Abschnitt

Neues Feld `abschnitte[].maengel`, Werte aus der bestehenden Liste `MAENGEL`, darf leer sein; im Schema required
wie alle übrigen Felder (Structured Outputs). Der clip-weite `maengel`-Eintrag bleibt als Vereinigung erhalten.

`prompts/index-clip.md` bekommt dazu einen Satz: welche Mängel in *diesem* Abschnitt zu sehen sind, gehören in sein
`maengel`; die clip-weite Liste bleibt die Vereinigung aller Abschnitte. Beispiel 2 im Prompt (Kapelle, „Blick in
Kamera" nur im zweiten Abschnitt) wird entsprechend ergänzt — es zeigt den Fall bereits.

**Migration:** Der Cache-Schlüssel ist der Fingerprint des Clips, nicht ein Schema-Hash; `index_clip()` liefert
Cache-Treffer ungeprüft zurück. Datensätze ohne das neue Feld bleiben also gültig, und der Prüfer fällt für sie auf
das heutige clip-weite Verhalten zurück. **Kein Zwangs-Neuindex.**

## 2 — Telemetrie: `stabile_bereiche()`

Neue Funktion in `telemetrie.py`, reine Ableitung aus einem vorhandenen Datensatz — keine Messung, keine API,
keine Mediendatei:

```
stabile_bereiche(rec, cfg) -> list[[von_s, bis_s, wackeln_max, bewegung_max]]
```

- Basis sind die Fenster, deren `t_s` in `ruhige_fenster` steht. Damit gilt `wackeln ≤ ruhig_max_px` **und** der
  bestehende Ausschluss schneller Zoomfahrten (`ruhige_ohne_schnelle_zooms`) gratis mit.
- Zusätzlich muss `bewegung ≤ bewegung_max` sein (Fenster-Wert aus `fenster`, Spalte 3).
- Maximale Läufe benachbarter Fenster (Abstand ≤ `schritt_s`); Ende = `t_s` des letzten Fensters + `fenster_s`, auf
  `dauer_s` gekappt.
- Läufe kürzer als `stabil_min_s` fallen weg.
- `wackeln_max`/`bewegung_max` sind die Höchstwerte der Fenster des Laufs — sie gehen in den kompakten Index, damit
  das Planungsmodell den Bereich einschätzen kann.
- Ohne `fenster` (Clip mit `fehler`, `quelle: "keine"`, alte Telemetrie) leere Liste.

Die Fensterauflösung (`fenster_s` 2,0 / `schritt_s` 1,0) macht die Bereichsgrenzen auf **±1 s genau**. Für Shots von
2–5 s reicht das; der kürzeste mögliche Bereich ist ein einzelnes Fenster = 2,0 s.

## 3 — Stufe 2b (`index_sections.py`): `stabil` je Abschnitt

`telemetrie_anwenden` ergänzt je Abschnitt `stabil` = die mit `[von_s, bis_s]` geschnittenen Bereiche aus
`stabile_bereiche()`, ohne Mindestlänge je Stück: `stabil_min_s` gilt für den Lauf (das garantiert
`stabile_bereiche()`), ein kürzeres Stück entsteht nur an einer Abschnittsgrenze, wo sein Lauf im Nachbarabschnitt
weitergeht; nur Stücke ohne Länge fallen weg (berichtigt 24.09.2026, Task 8: der frühere Filter je Stück verwarf
solche Randstücke — ein Shot 12,5–15,5 s im Lauf 12–18 s fiel an der Abschnittsgrenze bei 13 s durch). Dieselbe
Stelle und dieselbe Mechanik wie `bewegung_spitzen` seit dem 22.09.: Cache-Treffer bekommen das Feld ohne
API-Aufruf, `felder_quelle` führt es wie die übrigen. Die Schleife läuft über **alle** Abschnitte, auch über die
mit `verwendbar=false` — genau die brauchen das Feld.

Dazu je Clip `stabil_quelle: {ruhig_max_px, bewegung_max, stabil_min_s, config_hash, laeufe}` — die drei Schwellen
der Ableitung, der Config-Hash des Telemetrie-Datensatzes, aus dem sie stammt, und `laeufe`, die ungeschnittenen
Läufe aus `stabile_bereiche()` (berichtigt 24.09.2026, Task 8: gegen sie prüft `verify_layout()`, und
`compact_index_v2()` gibt sie je Clip als `stabil_laeufe` aus). Damit können `compact_index_v2()` und
`verify_layout()` veraltete Bereiche erkennen, **ohne die Telemetrie selbst laden zu müssen** (der kompakte Index
hat sie nicht).

Damit betritt die Telemetrie den Index weiterhin an genau einer Stelle.

## 4 — `compact_index_v2()` (`broll_layout.py`)

Je Abschnitt zusätzlich `maengel` (aus Stufe 2, leer wenn das Feld fehlt) und `stabil`. Die Abschnittsgrenzen
bleiben, was das Modell gesagt hat — gemessen und geurteilt bleiben unterscheidbar.

Neu aufgenommen werden Abschnitte mit `verwendbar=false`, wenn beides gilt:

1. sie haben mindestens einen `stabil`-Bereich, und
2. ihre sperrenden Mängel sind leer: `(maengel − {"Wackler"}) ∩ forbidden_maengel = ∅`. „Wackler" fällt hier immer
   heraus, weil der Abschnitt ohnehin nur über seine `stabil`-Bereiche angeboten wird und die per Definition ruhig
   gemessen sind. Beim Prüfen hängt dieselbe Ausnahme am konkreten Shot (siehe 5).

Diese Abschnitte tragen `gerettet: true` und `trotz: [...]` — die übrigen, nicht sperrenden Mängel, die das Modell
zum `verwendbar=false` bewogen haben (typisch „Unschärfe"). Das Planungsmodell sieht damit, worauf es sich einlässt;
„Wackler" steht nicht in `trotz`, wenn die Messung ihn im Bereich widerlegt.

`verwendbar` auf Clip-Ebene bleibt `bool(abschnitte)` und wird dadurch für gerettete Clips wahr.

`compact_index_v2()` braucht dafür `forbidden_maengel`, also einen zweiten Parameter (`cfg`), und ist damit von der
Charge abhängig — der Aufruf in `autocut_place_broll.py` (`--compact`) hat `effective_broll_cfg()` schon zur Hand,
muss es aber vor dem `--compact`-Zweig laden.

`prompts/place-broll.md` beschreibt die neuen Felder (dazu je Clip `stabil_laeufe`) und die Regel: ein Shot in
geretteten Abschnitten muss vollständig in EINEM Lauf aus `stabil_laeufe` liegen und darf dabei über
Abschnittsgrenzen laufen, solange jeder berührte Abschnitt verwendbar oder gerettet ist; in einem normalen Abschnitt
ist `stabil` ein Hinweis, wo es ruhig ist — außer die Charge sperrt „Wackler" und der Abschnitt nennt ihn, dann muss
der Shot auch dort vollständig in einem Lauf liegen (berichtigt 24.09.2026, Task 8: bisher „nur innerhalb von
`stabil`" und ohne Ausnahme „ein Hinweis").

## 5 — `verify_layout()` (`broll_layout.py`): drei Änderungen

| | heute | neu |
|---|---|---|
| **Mangel-Sperre** | `clip.maengel ∩ forbidden`, dazu erzwingt `personen.blick_in_kamera` den Mangel „Blick in Kamera" | `maengel ∩ forbidden` des Abschnitts, in dem der Shot liegt. „Wackler" entfällt, wenn der genutzte Quellbereich in einem `stabil`-Bereich liegt — **das ist das Überstimmen, Schwelle = `ruhig_max_px`, keine neue Zahl.** Fehlt der **Schlüssel** `maengel` in allen Abschnitten des Clips (alter Cache), bleibt alles clip-weit wie heute und der Bericht zählt diese Clips; ein vorhandener, aber leerer `maengel`-Eintrag ist eine Aussage („hier ist nichts") und kein Rückfall |
| **Lage des Shots** | muss in einem `verwendbar`-Abschnitt liegen (`_usable_spans()`, angrenzende zusammengelegt) | `_usable_spans()` nimmt zusätzlich die `stabil`-Bereiche geretteter Abschnitte auf, **vor** dem Zusammenlegen. Ohne das fiele FX3_8641 1,5–4,0 s durch, weil es die Abschnittsgrenze bei 2,0 s überschreitet |
| **Bewegung im genutzten Bereich** | — | **Warnung, kein Fehler:** Shot liegt in einem `verwendbar`-Abschnitt, aber außerhalb jedes `stabil`-Bereichs → „Bereich nicht als stabil gemessen (bewegung max 10,3)". Das ist der FX3_8663-Fall 0–8 s. Bewusst nur Warnung: ein gewollter Schwenk ist nicht ruhig und bleibt erlaubt (Grundsatz 22.09.) |

`_usable_spans()` liegt in `broll_plan.py` und wird von **beiden** Prüfern benutzt — v1 (`broll_plan.py:339`) und v2
(`broll_layout.py:653`). Die Erweiterung kommt deshalb als Vorgabewert-Parameter (`gerettet=False`), den nur v2
setzt. Der Plan-v1-Pfad bleibt unverändert.

Inhaltliche Mängel („Blick in Kamera", „Crew im Bild", „Mikro im Bild") rührt die Telemetrie an keiner Stelle an.
Sie werden **genauer**, nicht schwächer: die Verortung kommt vom Index (Abschnitt 1), nicht von der Messung.
`personen.blick_in_kamera` wird nur noch dann clip-weit zum Mangel erhoben, wenn die Abschnitte keine eigenen
`maengel` tragen.

Zeitlupen: `stabil` liegt in Quell-Sekunden; der Prüfer rechnet über `genutzter_quellbereich_s()` wie 3b und 3c.

## Konfiguration

Neu unter `telemetrie:`:

```yaml
  bewegung_max: 2.0     # Obergrenze der Bewegung je Fenster eines stabilen Bereichs (UNKALIBRIERT, Startwert 23.09.2026)
  stabil_min_s: 2.0     # kürzester stabiler Bereich (= kürzester Shot aus broll.shot_len_s)
```

`ruhig_max_px` bleibt bei 0,15. Beide neuen Schlüssel gehören in `OHNE_MESSWIRKUNG`: sie ändern keine Messung, nur
die Ableitung aus `fenster`. Folge — eine Änderung macht die Telemetrie **nicht** ungültig, aber `stabil` im Index
veraltet. Dagegen `stabil_quelle` je Clip (Abschnitt 3) und ein Hinweis im Bericht: „mit anderen Stabil-Schwellen
abgeleitet — `autocut_index_sections.py` erneut laufen lassen" (kostenlos aus dem Cache, keine API).

## Fehler und Randfälle

- **Charge ohne `telemetrie.json`**: kein `stabil`, keine Rettung, keine neue Warnung — Verhalten wie heute. Der
  Bericht nennt die Zahl der Shots mit Grund, wie die Regeln 3a–3c es seit dem 21.09. tun.
- **Clip mit `fehler` oder `quelle: "keine"`**: wie ohne Telemetrie.
- **Telemetrie mit anderem Config-Hash**: Stufe 2b schreibt `stabil` trotzdem (sie kennt nur den vorliegenden
  Datensatz), aber **`verify_layout()` und `compact_index_v2()` ignorieren es für diese Clips und zählen sie** — die
  Bereiche hängen an `ruhig_max_px` und `fenster_s`, die beide in den Hash eingehen. Betroffene Clips verhalten sich
  wie ohne Telemetrie: keine Rettung, keine neue Warnung. Beide lesen dafür `stabil_quelle.config_hash` aus dem
  Index und vergleichen ihn mit `TM.config_hash(cfg["telemetrie"])` — dieselbe Prüfung wie die bestehende für 3b/3c,
  Meldung über `HINWEIS_SCHWELLEN`.
- **Index aus altem Cache ohne `abschnitte[].maengel`**: Sperre bleibt clip-weit, der Bericht nennt die Zahl der
  betroffenen Clips und rät zu `autocut_index_broll.py --force`.
- **Abschnitt mit `verwendbar=true`, aber sperrendem Mangel**: bleibt gesperrt. Die Charge-Config gewinnt über das
  Modellurteil — das ist der Sinn von `forbidden_maengel`.
- **Gerettete Abschnitte in Folge**: mehrere gerettete Abschnitte nebeneinander legen ihre `stabil`-Stücke
  zusammen, wenn sie zum selben gemessenen Lauf gehören (FX3_8641: 0–2 s und 2–4,8 s aus dem Lauf 0–4,8 s →
  0–4,8 s); zwei Läufe, die sich genau an einer Abschnittsgrenze berühren, bleiben getrennt (berichtigt 24.09.2026,
  Task 8: bisher genügte das Aneinandergrenzen — das überbrückte ein unruhiges Fenster genau auf der Grenze). Ein
  Index ohne `laeufe` (Stufe 2b von vorher) legt wie bisher an Abschnittsgrenzen zusammen.

## Tests (pytest, ohne NAS, ohne Resolve, ohne API)

**Fixture A — die 30 Urteile** als `tools/autocut/tests/fixtures/schwenk-urteile.json`: je Beispiel Clip, Bereich
(`quelle_start_s` … +5 s), die Fenster-Reihe aus der MEK-Telemetrie, Urteil und Anmerkung. Keine Medien. Kriterien:

1. **Hart:** R2#12 („komplett ungewollt") bekommt keinen Kandidaten.
2. **Hart:** höchstens 2 der 24 „ungewollt"-Beispiele bekommen einen. Heute exakt 2 — R2#10 ist durch die Anmerkung
   gedeckt (Kandidat 2,5–5 s = „brauchbar am Anfang"), **R1#2 ist ungeklärt**, weil Runde 1 ohne Anmerkungen lief.
   Der Test hält die Zahl fest, nicht das Urteil.
3. Der Test liest die Schwellen aus `defaults.yaml` — jede künftige Änderung an `ruhig_max_px` oder `bewegung_max`
   muss erneut antreten.

R1#2 ist ohne neuen Aufwand klärbar: der 5-s-Ausschnitt liegt noch in
`projects/NIRO/Werkzeug-Kalibrierung/2026-09 Schwenks/_intern/work/schwenk-beispiele.mp4` bei 5–10 s. Fällt das
Urteil „da ist nichts Brauchbares", muss die Zahl in Kriterium 2 auf 1 sinken.

**Fixture B — die vier WLC-Clips**: Fenster-Reihen von FX3_8636/8641/8660/8663 und die vom User genannten Bereiche.
Abnahme: jeder Bereich liegt in einem Kandidaten. Nachgerechnet trifft das zu:

| Clip | Bereich des Users | Kandidat |
|---|---|---|
| FX3_8636 | 4,5–7,5 s | 0–11,5 s |
| FX3_8641 | 1,5–4,0 s | 0–4,8 s |
| FX3_8660 | 12,5–15,5 s | 12–18,7 s |
| FX3_8663 | 9–12 s · 63,5–66,5 s | 8–15 s · 63–71 s (von acht Kandidaten) |

**Unit-Tests:**

- `test_telemetrie.py`: `stabile_bereiche` — Läufe und Lücken, Fenster am Clipende, Kappung an `dauer_s`,
  Mindestlänge, leer ohne `fenster`, Ausschluss über `ruhige_fenster` (schnelle Zoomfahrt), `bewegung_max` greift.
- `test_index_sections.py`: `stabil` je Abschnitt inkl. Schnitt an den Abschnittsgrenzen; Cache-Treffer trägt das
  Feld ohne API-Aufruf nach; `stabil_quelle` wird mit Schwellen und Config-Hash geschrieben.
- `test_broll_index.py`: `CLIP_SCHEMA` kennt `abschnitte[].maengel` mit dem Enum aus `MAENGEL`; der Prompt nennt das
  Feld.
- `test_broll_layout.py`: `compact_index_v2` liefert `maengel`/`stabil`, nimmt gerettete Abschnitte mit
  `gerettet`/`trotz` auf und lässt sie weg, wenn ein sperrender Mangel bleibt; `verify_layout` sperrt je Abschnitt
  statt je Clip, lässt „Wackler" im `stabil`-Bereich durch, akzeptiert einen Shot über die Grenze zweier
  angrenzender geretteter Abschnitte, warnt bei einem Shot außerhalb jedes `stabil`-Bereichs und verhält sich ohne
  die neuen Felder wie heute.

Fixtures mit echten Werten aus WLC und MEK, nicht mit erfundenen — wie beim Entwurf vom 22.09.

## Erste Probe (WLC Video 1)

1. `broll.forbidden_maengel: ["Blick in Kamera", "Crew im Bild"]` in `_intern/autocut/config.yaml` — steht als
   offener Punkt schon im Protokoll vom 23.09.
2. `autocut_index_broll.py "$CHARGE" --force` für die 51 Clips (~2,50 €) — bringt `abschnitte[].maengel`.
3. `autocut_index_sections.py "$CHARGE"` — trägt die Abschnittsfelder samt `stabil` und `stabil_quelle.laeufe` neu
   ein, **mit API-Kosten**: `--force` in Schritt 2 schreibt je Clip einen frischen Datensatz ohne die Felder aus
   Stufe 2b, der Nachlauf fragt deshalb jeden Clip neu an; vorher `--dry-run` für Clipzahl und Schätzung (berichtigt
   24.09.2026, Task 8, wie im Plan).
4. `autocut_place_broll.py "$CHARGE" --compact` — kompakter Index mit geretteten Abschnitten.
5. Auswahl für Video 1 neu, Ergebnis wieder als Sichtungs-Video gegen
   `Ergebnisse/Rohschnitt/video-1-broll-sichtung.mp4` und `…-nachtrag.mp4` halten.

Maßgeblich ist Schritt 5: kommen die vier vom User genannten Bereiche in der neuen Auswahl vor, und wird nichts
hereingeholt, was er verworfen hat.

## Doku

- `tools/autocut/WORKFLOW-AutoCut.md`: Stufe 2 (`abschnitte[].maengel`), Stufe 2b (`stabil`, `stabil_quelle`), Stufe 3
  (Sperre je Abschnitt, gerettete Abschnitte, neue Warnung), Telemetrie-Abschnitt um die Ableitung ergänzen
- `tools/autocut/prompts/index-clip.md`: das neue Feld
- `tools/autocut/prompts/place-broll.md`: die neuen Felder im kompakten Index und die Regel für `gerettet`
- `tools/autocut/README.md`: Tabellenzeile

## Nicht enthalten

- **Unschärfe messen.** `schaerfe` gibt es nur auf dem optischen Weg (11 von 102 WLC-Clips, 10 von 464 MEK). Eine
  Schärfe-Regel bräuchte erst eine Messung für den rtmd-Weg — deshalb bleibt „Unschärfe" ein Modellurteil und taucht
  nur als `trotz` auf.
- **Absicht erkennen** und **Vorfilter vor dem bezahlten Index** — beides am 22.09. widerlegt.
- **Feinere Fensterauflösung.** ±1 s reicht für Shots von 2–5 s; feiner messen wäre ein eigener Schritt mit eigenem
  Config-Hash und vollständiger Neumessung.
- **Kalibrierung von `bewegung_max`.** Der Startwert steht auf zwei Datenpunkten. Eine eigene Runde („würdest du
  diese 2 s so schneiden?") an 15–20 Kandidaten-Bereichen wäre der saubere Weg — erst wenn der Mechanismus im echten
  Lauf steht und zeigt, wo er danebenliegt.
- **Ablösung von Stufe 3a** — unverändert offen.
