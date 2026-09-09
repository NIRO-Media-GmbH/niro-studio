# Cutlist erstellen — Arbeitsanleitung für Claude (AutoCut Stufe 1, Schritt „Cutlist")

Diese Anleitung gilt, wenn im Workflow „AutoCut: <Kunde>/<Projekt>[/<Charge>] Rohschnitt" der
Schritt **Cutlist** ansteht (nach `autocut_prepare.py` und `autocut_sync.py`, vor `autocut_verify.py`
und `autocut_build.py`). Ergebnis ist genau eine Datei:

    <Charge>/_intern/autocut/cutlist.json

Sie ist die einzige Quelle, aus der `autocut_build.py` die Timeline in DaVinci Resolve baut.
Der Code prüft hart (`autocut_verify.py`); die Entscheidungen — welcher Take, wo In und Out,
was gesperrt ist, welche Pause — triffst **du** in der Session, mit den Hilfsskripten unten.
Du schreibst dabei nur nach `<Charge>/_intern/autocut/`; das NAS wird ausschließlich gelesen.

## Pfade (absolut, zsh: alles in Anführungszeichen, Flags ausschreiben)

    TOOL="/Users/jansantos/NIRO Studio/tools/autocut"
    PY="$TOOL/venv/bin/python"
    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"

| Skript | Zweck |
|---|---|
| `"$PY" "$TOOL/scripts/autocut_cutlist_draft.py" "$CHARGE" [--video video-1-x.md] [--force]` | Entwurf aus dem Plan (Schritt 1) |
| `"$PY" "$TOOL/scripts/autocut_find_quote.py" "$CHARGE" --clip FX3_9557 --text "…" [--near 03:37] [--all] [--min-score 0.7]` | Zitat wortgenau im Transkript finden (Schritt 2) |
| `"$PY" "$TOOL/scripts/autocut_verify.py" "$CHARGE"` | harte Prüfung, schreibt `verify.json` (Schritt 7) |

## Eingaben (alle in der Charge, nur lesen)

- **Plan** `Ergebnisse/O-Ton-Pläne/video-N-*.md`: Kopf mit Ziellänge, Format, `**Verboten:**`-Zeile;
  Ablauf-Tabelle `# | Szene | O-Ton / VO (wörtlich) | Quelle | Bild | Sound | Caption | Kommentar`.
  Bei mehreren `video-*.md` den gewünschten mit `--video` wählen.
- **Index** `_intern/transcripts_index.json`: je Clip `name` (FX3_9557.MP4), `path` (voller NAS-Pfad),
  `person` (Ordnername, z. B. „Sandra_Notaufnahme"), `kamera_rolle` (`ton` = FX3, `kontext` = a7IV),
  `duration_s`, `fingerprint`.
- **Wörter** `_intern/cache/<fingerprint>.scribe.json` → `words[{text,start,end,speaker}]`.
- **Utterances** `_intern/utterances.json` (Sätze mit `von_s/bis_s/speaker` je Clip) — zum Nachlesen
  von Kontext und für Sperren ohne Endzeit.
- **media.json** `_intern/autocut/media.json` (aus `autocut_prepare.py`): `format.fps`,
  `format.orientation` — die Timeline-Werte für den Kopf der Cutlist.

## Aufbau von cutlist.json

```json
{
 "video": "video-1-imagefilm-zwei-haeuser.md",
 "ziel_laenge_s": 185,
 "fps": 25,
 "format": "16:9",
 "pause_s": 1.0,
 "beats": [
  {"nr": "1", "szene": "Kaltstart-Teaser", "typ": "oton",
   "person": "Sandra", "rolle": "Fachkrankenschwester Notfallpflege",
   "clip": "/Volumes/NIRO NAS/…/Standort 1/Sortiert/Interviews/Sandra_Notaufnahme/FX3_9557.MP4",
   "cuts": [{"in_s": 217.54, "out_s": 219.6, "text": "Weil das mein Job ist. Das ist meins.",
             "hart_in": false, "hart_out": true}],
   "pause_after_s": null, "platzhalter_s": null, "text": null,
   "bild_hinweis": "Gehaltenes Gesicht, roh, kein Logo",
   "kommentar": "OHNE Kontext, KEINE Bauchbinde. Harter Schnitt danach. ~3 s",
   "caption": null, "plan_dauer_s": 3, "sound": "Nur Raumton"},
  {"nr": "2", "szene": "VO: Vorurteil", "typ": "vo",
   "text": "Viele denken: In einem Haus dieser Größe kann man nichts lernen.",
   "platzhalter_s": 6, "bild_hinweis": "Gesichter-Montage beider Häuser",
   "kommentar": "Reibung zum Teaser. Kein Konter — Frage bleibt offen! ~6 s",
   "caption": null, "plan_dauer_s": 6, "sound": "Raumton/Atmo"},
  {"nr": "8", "szene": "Mensch 3: Familie", "typ": "oton",
   "person": "Jessi", "rolle": "Pflegekraft Intensiv",
   "clip": "/Volumes/NIRO NAS/…/Standort 2/Sortiert/Interviews/Jessi_Intensivstation/FX3_9993.MP4",
   "cuts": [{"in_s": 315.52, "out_s": 319.81, "text": "ich, äh, sag immer, das ist die Familie, die ich nie haben wollte, aber", "hart_in": false, "hart_out": true},
            {"in_s": 321.1, "out_s": 322.32, "text": "der Zusammenhalt ist einfach super.", "hart_in": true, "hart_out": false}],
   "bild_hinweis": "Frontal; Team-Momente (S2 Kolleginnen am Tisch)", "kommentar": "Langvariante mit Wendung ab 05:07 (…). ~7 s",
   "caption": null, "plan_dauer_s": 7, "sound": "Thema B"},
  {"nr": "11", "szene": "Beweis visuell", "typ": "bild", "platzhalter_s": 5,
   "bild_hinweis": "Geräte-B-Roll: S1 Herzkatetherlabor/Intensivstation → S2 Beatmungszimmer",
   "kommentar": "Fachbeweis rein visuell (V4-Regel). ~5 s",
   "caption": "Badge 1: „Zertifiziertes Cardiac Arrest Center.\" → Badge 2: „Zertifiziertes Weaning-Zentrum.\"",
   "plan_dauer_s": 5, "sound": "Themen im Wechsel"}
 ],
 "sperren": [
  {"clip": "/Volumes/NIRO NAS/…/Ramona_Leiterin Intensivstation/FX3_9994.MP4", "von_s": 16, "bis_s": 52, "grund": "Volkmarsen 9994 · 00:16–00:52 + 02:36–03:24"},
  {"clip": "/Volumes/NIRO NAS/…/Ramona_Leiterin Intensivstation/FX3_9994.MP4", "von_s": 156, "bis_s": 204, "grund": "Volkmarsen 9994 · 00:16–00:52 + 02:36–03:24"},
  {"clip": "/Volumes/NIRO NAS/…/Sodan_Intensivstation/FX3_9650.MP4", "von_s": 311, "bis_s": 618.9, "grund": "Zoran ab 9650 · 05:11"}
 ],
 "hinweise": [
  "Textsperre ohne Zeit (nicht automatisch prüfbar): Konkurrenz-Nennungen — alle Cut-Texte gegengelesen, keine Nennung"
 ]
}
```

Die Pfade sind hier gekürzt („…"); in der Datei steht **immer der volle `path` aus dem Index**,
Zeichen für Zeichen — sonst findet die Prüfung weder Transkript noch Datei.

### Feldreferenz

| Feld | Pflicht | Bedeutung |
|---|---|---|
| `video` | ja | Dateiname des Plans (`video-1-….md`) |
| `ziel_laenge_s` | nein | Ziellänge in Sekunden aus dem Plankopf (bei Bereich der obere Wert; „≈ 3:05" → 185) |
| `fps`, `format` | ja / ja | aus `media.json` (`format.fps`, `format.orientation`) — **Material bestimmt**, nicht der Plan |
| `pause_s` | ja | Standardlücke zwischen Beats, Config-Wert 1.0 (nur bei globaler Plananweisung ändern) |
| `beats[]` | ja | eine Zeile des Plans = ein Beat, **in Planreihenfolge, keine Zeile weglassen** |
| `beats[].nr` | ja | Plannummer als String („1", „18a" bei Aufteilung) |
| `beats[].szene`, `typ` | ja | Szene wörtlich; `typ` ∈ `oton`, `vo`, `bild`, `grafik` |
| `beats[].person`, `rolle` | oton | aus der Quelle-Spalte (Bauchbinde im Bericht); „(s. o.)" → Rolle des früheren Beats derselben Person |
| `beats[].clip` | oton | voller Index-`path` des **FX3**-Clips (`kamera_rolle: ton`) — nie ein a7-Clip |
| `beats[].cuts[]` | oton | Teilschnitte, jeder mit `in_s`/`out_s` (Sekunden im Clip, Anfang erstes Wort, Ende letztes Wort), `text` (gesprochener Wortlaut), `hart_in`/`hart_out` |
| `beats[].platzhalter_s` | vo/bild/grafik | Lückenlänge = Plan-Schätzung „~x s" (Bereich → oberer Wert) |
| `beats[].text` | vo | VO-Text ohne „VO:"-Präfix und ohne Anführungszeichen |
| `beats[].pause_after_s` | nein | nur setzen, wenn der Plan etwas anderes als die Standardpause verlangt |
| `beats[].bild_hinweis`, `kommentar`, `caption`, `sound` | nein | Spalten Bild/Kommentar/Caption/Sound wörtlich (landen im Marker und im Bericht); „—" → `null` bzw. `""` |
| `beats[].plan_dauer_s` | nein | Plan-Schätzung „~x s" — Plausibilitätsprüfung (50–200 %) |
| `sperren[]` | nein | gesperrte Bereiche `clip` (voller Pfad), `von_s`, `bis_s`, `grund` |
| `hinweise[]` | nein | freie Sätze für den Bericht: Textsperren ohne Zeit, bewusste Abweichungen vom Plan |

Unbekannte Felder (auch Tippfehler wie `hard_out`) lehnt der Lader mit Meldung ab.

## Ablauf

### Schritt 1 — Entwurf erzeugen

    "$PY" "$TOOL/scripts/autocut_cutlist_draft.py" "$CHARGE"

Das Skript liest den Plan, legt alle Beats in Planreihenfolge an, übernimmt Bild/Sound/Caption/
Kommentar/Plan-Schätzung, setzt bei VO/Bild/Grafik den Platzhalter, löst bei O-Tönen den Clip
über den Datei-Stem der Quelle auf und sucht das Zitat per Alignment nahe dem mm:ss-Hinweis
(„[…]" → mehrere Cuts; „In hart"/„Out HART" im Kommentar → Flags). Aus `**Verboten:**` werden
Sperren gebaut (Regeln in Schritt 4). Es schreibt `cutlist.json` (nur, wenn noch keine da ist —
sonst `--force`) und druckt **OFFEN:**-Zeilen für alles, was es nicht sicher entscheiden konnte.

Der Entwurf ist ein Startpunkt, kein Ergebnis: **jeden Beat gegen die Planzeile lesen** (Schritt 2)
und jede OFFEN-Zeile erledigen. Wenn du die Cutlist lieber vollständig von Hand schreibst, gelten
dieselben Regeln.

### Schritt 2 — Jeden O-Ton-Beat prüfen und vervollständigen

Für jede Planzeile mit Zitat:

1. **Clip**: Datei-Stem aus der Quelle (`…/Sandra_Notaufnahme/FX3_9557.MP4 · 03:37–03:39`) → Index-Eintrag
   mit diesem `name` → `path`. Timecodes im Plan sind FX3-Zeiten; die a7IV kommt beim Bau automatisch
   über `sync.json` auf V2.
2. **Zitat auflösen** (wortgenau, Sekunden ab Clipanfang):

       "$PY" "$TOOL/scripts/autocut_find_quote.py" "$CHARGE" --clip FX3_9557 \
         --text "Weil das mein Job ist. Das ist meins." --near 03:37

   Ausgabe: `{"gefunden": true, "clip": "<voller Pfad>", "start_s": 217.54, "end_s": 219.6,
   "start": "03:37.5", "end": "03:39.6", "score": 0.97, "text": "<Transkript-Wortlaut>",
   "speaker": "speaker_1", "segmente": [{"in_s", "out_s", "text"}, …], "hinweise": []}`.
   - `segmente` = ein Eintrag pro Fragment eines „[…]"-Zitats. **Achtung, Cutter-Standard (David):
     „[…]" kürzt das Zitat nur in der PDF — Anfang und Ende sind wörtlich, damit der Cutter In und
     Out findet; die Passage läuft im Schnitt DURCHGEHEND.** Standard ist deshalb **ein Cut** von
     `segmente[0].in_s` bis `segmente[-1].out_s` (`text` = Fragmente mit „ […] " verbunden).
     Mehrere Cuts nur, wenn der Kommentar es ausdrücklich verlangt: „Jumpcuts …", feste Fenster
     („Kurzfassung fest: 00:40–00:45 + 00:52–00:57"), „… mittig trimmen", „Zwischenrufe … raus".
     Kontrolle: die Plan-Schätzung „~x s" passt zur durchgehenden Dauer, nicht zur Summe der Fragmente.
   - `--near` ist der mm:ss-Hinweis aus der Quelle und entscheidet bei mehreren Takes (Interviewte
     sagen Kernsätze oft zweimal). Fehlt er, `--all` nutzen: bis zu 10 Kandidaten für das erste
     Fragment mit `start`/`score`; den nehmen, der zur Plan-Zeit passt.
   - `gefunden: false` → `--all` ansehen; Plan-Zitat ist oft leicht geglättet (Verhörer, Zahlwörter,
     „'n" → „ein"). Ggf. `--min-score 0.7`. Findet sich das Zitat nicht in diesem Clip: andere Clips
     derselben Person im Index probieren (gleiches `person`). Bleibt es unauffindbar → Beat ohne
     `cuts` lassen, im Bericht an den User melden. **Nie Zeiten erfinden oder aus dem Plan abschreiben.**
   - `hinweise` im Ergebnis (z. B. Alternativ-Takes, unsichere Fragmente) lesen und die Wahl prüfen.
3. **`text` je Cut** = gesprochener Wortlaut dieses Teilstücks. Vorlage ist das Plan-Zitat; weicht das
   Transkript hörbar ab (Verify meldet „stimmt nicht"), den `text` aus `segmente[].text` übernehmen —
   die Prüfung verlangt Score ≥ 0.8 gegen die Wörter im Intervall.
4. **In/Out-Hinweise aus dem Kommentar** umsetzen:

| Plan sagt | In der Cutlist |
|---|---|
| „In hart", „hart rein bei …" | `hart_in: true` am ersten Cut (kein 6-Frame-Vorlauf) |
| „Out HART", „Out hart nach „gehen."" | `hart_out: true` am letzten Cut (kein 8-Frame-Nachlauf) |
| „In bei „es gibt einem" (Vorlauf weglassen)" | Zitat beginnt genau dort: `--text` mit diesem Anfang, `in_s` = Anfang dieses Worts |
| „In NACH Scherz (08:16–08:21)" | `in_s` liegt nach 08:21: `--near 08:21`, Startwort im Ergebnis prüfen; `hart_in: true` (kein Vorlauf in den Scherz) |
| „Out VOR „Sonst muss man …"" | Zitat endet vor dieser Phrase: `--text` endet mit dem letzten erlaubten Wort; zur Kontrolle die verbotene Phrase mit `--all` suchen — ihr `start` muss ≥ dein `out_s` sein; `hart_out: true` (kein Nachlauf in die Phrase) |
| „[…]" im Zitat ohne weiteren Hinweis | **ein durchgehender Cut** vom ersten bis zum letzten Fragment (Cutter-Standard: die Auslassung ist nur PDF-Kürzung) |
| Ausdrückliche Jumpcut-Grenze **innerhalb** eines Beats (Kommentar sagt Jumpcut/Fenster/trimmen) | vorderer Cut `hart_out: true`, hinterer Cut `hart_in: true` — sonst ragen die Handles in die ausgelassenen Wörter derselben Sprecherin (der Entwurf setzt das automatisch) |
| „Kurzfassung fest: 00:40–00:45 + 00:52–00:57", „+" in der Quelle | ein Cut je Stück; jedes Stück einzeln mit passendem `--near` auflösen |
| „Jumpcuts 03:32–03:35/03:37–03:39/03:41–03:42; Zwischenrufe raus" | ein Cut je Stück; Interviewer-Zwischenrufe (anderer `speaker`) bleiben draußen |
| „Falschstart „das hat man," mittig trimmen" | zwei Cuts: bis zum Wort vor dem Falschstart (`hart_out: true`) und ab dem Wort nach dem Falschstart (`hart_in: true`); beide Teile einzeln mit `--text` auflösen. Nur wenn die Grenze im Transkript nicht sauber liegt: ein Cut plus `hinweise`-Eintrag |
| „1–2 s STILLE vor „…noch Mensch ist"" (Sound-Spalte) | Anweisung an den **Ton** (Musik/VO aussetzen), nicht an den O-Ton-Schnitt: Beat bleibt **ein** durchgehender Cut, der Hinweis steht im Marker (Kommentar/Sound) |
| „Harter Schnitt danach" | `hart_out: true` am letzten Cut (Schnitt direkt nach dem letzten Wort); keine Pausenangabe → Standardpause bleibt |
| „2. Take in Folge", „Bauchbinde über #9/#10" | Information für den Cutter → bleibt im `kommentar`, keine Aktion |

5. **Sperren beachten**: kein Cut darf — auch nicht mit Handles (6 Frames vor, 8 nach) — in eine Sperre
   ragen. Kollidiert ein Zitat mit einer Sperre, **nie die Sperre verkleinern**: anderen Take, kürzeren
   Cut oder `hart_in/hart_out` wählen — und es dem User sagen.
6. `person`/`rolle` aus der Quelle übernehmen (Rolle in Klammern). `plan_dauer_s` = „~x s" aus dem Kommentar.

### Schritt 3 — VO, Bild, Grafik

- `typ: "vo"`: `text` = VO-Text ohne „VO:" und ohne Anführungszeichen; `platzhalter_s` = Plan-Schätzung.
- `typ: "bild"` (B-Roll-Montage, Textkarte) und `typ: "grafik"` (Motion, Endcard): nur `platzhalter_s`;
  Bild-Spalte nach `bild_hinweis`, Captions nach `caption` (Stufe 3 füllt V3 nach diesen Hinweisen).
- Fehlt die Plan-Schätzung, `platzhalter_s` aus dem Kontext wählen (VO: ~3 Wörter/s; Montage: Plan-Rhythmus)
  und in `hinweise` begründen.

### Schritt 4 — Sperren aus „**Verboten:**"

Die Zeile ist mit „;" getrennt; jeder Eintrag wird zu null, einer oder mehreren Sperren. Die nackte Nummer
(„9994") ist der FX3-Stem (`FX3_9994.MP4`), `clip` immer der volle Index-Pfad, `grund` der Eintragstext.

| Eintrag | Sperre(n) |
|---|---|
| „Volkmarsen 9994 · 00:16–00:52 + 02:36–03:24" | zwei Sperren FX3_9994: 16–52 und 156–204 |
| „Zoran ab 9650 · 05:11 (Out Szene 6 HART 05:07!)" | FX3_9650: 311 bis Clip-Ende (`duration_s` aus dem Index); Klammer ist eine Anmerkung, keine Sperrzeit |
| „Sandra Fusions-Antwort 9557 · 02:38" | ganze Antwort: die Utterance, die bei 02:38 (±1 s / bis +5 s) **beginnt** — der Plan nennt den Anfang der Aussage, die Utterance, die 02:38 enthält, ist oft noch die Frage — plus direkt folgende Utterances derselben Sprecherin (in `utterances.json` Grenzen prüfen) |
| „Ramona „chillig" 9994 · 05:23" | wie oben — die bei 05:23 beginnende Antwort (bei MEK 323,9–358,6 s, nicht die Frage 309–323,4) |
| „Martina „gibt nichts, was es nicht gibt"" | Zitat ohne Zeit: mit `autocut_find_quote.py --all --min-score 0.7` in allen Clips von Martina suchen → Sperre über den Treffer (±0,5 s); mehrere Treffer → mehrere Sperren (bei MEK: FX3_9554 10:28, Score 0,73 — Verhörer im Transkript) |
| „Konkurrenz-Nennungen", „kein Gehalt" | keine Sperre möglich → Eintrag in `hinweise`; jeden Cut-`text` selbst darauf gegenlesen |

Der Entwurf setzt diese Regeln automatisch um und meldet Reste als OFFEN. Sperren, die ein Cut später
verletzt, meldet `autocut_verify.py` als Fehler. Explizite Bereiche („00:16–00:52") und „ab"-Sperren sind
fix. Nur eine aus einem Zeitpunkt abgeleitete Antwort-Sperre darfst du auf den Satz mit der verbotenen
Aussage eingrenzen — nie darunter, immer mit Begründung in `hinweise`.

### Schritt 5 — Pausen

`pause_s` (1,0 s) gilt zwischen allen Beats. `pause_after_s` nur, wenn der Plan es verlangt: „STILLE
1–2 s" → `2.0`; „direkt anschließen"/„ohne Luft" → `0.0`. Nach dem letzten Beat gibt es keine Pause.

### Schritt 6 — Kopf

`video` = Plandatei; `ziel_laenge_s` aus „Ziellänge ≈ 3:05" → 185 (Bereich → oberer Wert);
`fps`/`format` aus `media.json`. Sagt der Plan „16:9", das Material aber Hochformat, gilt das Material —
in `hinweise` vermerken. Ohne `media.json` erst `autocut_prepare.py` laufen lassen.

### Schritt 7 — Schreiben und prüfen

Die Datei mit `ensure_ascii=False`, `indent=1` schreiben (Umlaute lesbar), dann:

    "$PY" "$TOOL/scripts/autocut_verify.py" "$CHARGE"

Exit 0 = OK (Warnungen erlaubt), Exit 1 = Fehler beheben und erneut prüfen. Jede Änderung an
`cutlist.json` verlangt einen neuen Prüflauf — `autocut_build.py` vergleicht den Datei-Hash mit
`verify.json` und verweigert sonst.

| Meldung | Abhilfe |
|---|---|
| `Clip … hat kein Transkript oder ist nicht in der Charge` | `clip` muss exakt `path` aus dem Index sein; Clip ohne Cache → Transkription fehlt (Interview-Pipeline) |
| `Clip-Datei nicht gefunden … NAS gemountet?` / `kein Proxy für …` | NAS mounten; Proxy unter `<Ordner>/Proxy/<stem>.mov` erzeugen (Voraussetzung des Baus) |
| `kein Transkript-Wort in …` | Zeiten zeigen auf Stille/anderen Clip — mit `autocut_find_quote.py` neu auflösen |
| `Text stimmt nicht mit dem Transkript … Dort steht: „…"` | `text` an den Transkript-Wortlaut angleichen oder Intervall korrigieren |
| `Cut … ohne Text` | `text` ergänzen — jeder Cut braucht den Wortlaut |
| `überschneidet (inkl. Handles) die Sperre …` | anderen Take / kürzeren Cut / harte Kante; Sperre bleibt |
| `platzhalter_s fehlt` | Plan-Schätzung eintragen (Schritt 3) |
| `unbekannte Felder […]` | Tippfehler im Feldnamen (Feldreferenz) |
| Warnung `enthält Wörter, die nicht im Text stehen — vorn/hinten „…"` | Intervall ist weiter als der Text: `in_s`/`out_s` auf die Wortgrenzen setzen oder Text ergänzen |
| Warnung `Dauer … weicht stark von der Plan-Schätzung ab` | Take prüfen (falsche Stelle? zu viel/zu wenig?) — bewusste Abweichung in `hinweise` begründen |
| Warnung `keine a7-Abdeckung … (V2 bleibt leer)` | Information; ggf. anderes a7-Paar fehlt in `sync.json` (Sync-Bericht lesen) |
| Warnung `Gesamtlänge … weicht von der Ziellänge … ab` | mit dem User klären (Kürzpfad im Plan?), sonst hinnehmen |
| Warnung `sync.json fehlt` | erst `autocut_sync.py`, sonst bleibt V2 leer |

### Schritt 8 — Abschluss

Dem User kurz melden: Pfad der Cutlist, Zahl der Beats (O-Töne/Platzhalter), Zahl der Sperren,
Gesamtlänge gegen Ziellänge, alle Warnungen und alles, was du nicht auflösen konntest (Beat-Nummer,
Grund, Vorschlag). Erst dann folgt `autocut_build.py` laut `WORKFLOW-AutoCut.md`.

## Eiserne Regeln

- Nur `<Charge>/_intern/autocut/cutlist.json` schreiben. NAS nur lesen. Plan nicht verändern.
- Keine Zeiten erfinden: jede `in_s`/`out_s` kommt aus `autocut_find_quote.py` (oder den Wörtern im Cache).
- Nur FX3-Clips (`kamera_rolle: ton`) als `clip`; nie a7IV.
- Keine Planzeile weglassen, keine Reihenfolge ändern, keine Zitate „verbessern" — Abweichungen vom Plan
  nur mit Begründung in `hinweise` und im Bericht an den User.
- Sperren werden nie verkleinert oder weggelassen; Textsperren ohne Zeit werden gegengelesen und
  in `hinweise` dokumentiert.
- Vergütungs-/Gehalts-O-Töne und Kunden-Tabus aus dem Plankopf sind Sperren, keine Ermessenssache.
