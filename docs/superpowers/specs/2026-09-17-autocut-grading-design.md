# AutoCut — Grading mit Node-Baum (Spec)

Datum: 2026-09-17 · Status: Entwurf, Teile 1–4 im Chat vom User freigegeben; am selben Tag auf einer Taxodia-Kopie
getestet (Nachtrag am Ende, dort geänderte Regeln); Spec-Review durch den User ausstehend.
Ersetzt Stufe 6h „Grading" (Vorlagen `tools/autocut/vorlagen/feinschnitt/color/`).

## Anlass

User 17.09.2026: „Das Color Grading ist bisher noch nicht so gut, oft sind Shots viel zu dunkel und wirken übersättigt.
Zu hoher Kontrast und der Weißabgleich ist auch oft off. … Gerne darf mit mehreren Nodes gearbeitet werden, nicht
alles in einer."

Befund am einzigen Lauf der alten Stufe (Taxodia, 15.09., 101 Items), nachgerechnet mit `colorlib`
(S-Log3 → CDL → Sony LC-709 → Rec.709/BT.1886 → CIELAB; L\* 0 = schwarz, 100 = weiß):

| Problem | Ursache | Zahlen |
|---|---|---|
| Zu hoher Kontrast | Über der LC-709 lag zusätzlich ein Log-Kontrast von 1,20 um 18 % Grau; auf der a7 durch den Angleich 1,27–1,35. | 2 Blenden unter Grau: L\* 11 (nur LUT) → 6,9 (1,20) → 5,0 (1,31); 3 Blenden darunter: 3,5 → 1,3 → 0,7. Dunkle Kleidung landete bei L\* 5–13, Haut bei 68–75. |
| Übersättigt | Log-Kontrast skaliert auch die Kanalabstände (Farbverhältnisse in Szene-linear). | Test-Hautton: Chroma 18,8 → 23,4 (+24 %) bei Kontrast 1,20/Sättigung 1,03, → 24,8 (+32 %) bei 1,31. |
| Zu dunkel | B-Roll-Ziel Haut L\* 36 (Interviews 70); Trim je Einsatz nur halber Weg zum Median aller Shots, höchstens ±0,5 Blenden. | Dunkelste Einsätze Bild-Median L\* 17,9 → 27,1; 4 von 30 am Limit +0,5. C0261 (6 Einsätze) bekam Trims von +0,10 bis +0,50. |
| Weißabgleich | Eine gemeinsame CDL für alle 30 B-Roll-Einsätze aus 19 Clips, trotz Fenster-, Raum- und Monitorlicht. | C0246 orange (Protokoll: „bleibt durch das Raumlicht warm"), C0240/C0242 blau. |
| Nicht handhabbar | Alles in Node 1 (CDL + LUT). | — |
| Nie gegengeprüft | `ExportLUT` geht nur auf der Color-Seite; die Kontaktbögen zeigten die Rechnung, nicht Resolves Bild. | 101 von 101 Items „ExportLUT fehlgeschlagen". |

Die LUT ist nicht die Ursache: Sony LC-709 und die Phantom „Neutral A7s3" aus den Hand-Grades des Teams haben
praktisch dieselbe Tonkurve (18 % Grau → L\* 40, −2 Blenden → 11, +2 Blenden → 69).

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Look | **„Hell & natürlich"** (User): Haut in Interviews und B-Roll bei L\* ≈ 65, dunkle Kleidung mit Zeichnung, Weiß neutral mit einer Spur Wärme. Node 03 nach Variantenwahl am 17.09.: **Look C = Kontrast 1,05, Sättigung 1,00** (User: „Look C finde ich am besten"). |
| Ausgabe-Farbraum | **Rec.709-A bleibt** (User 17.09.). Die Rechnung bildet die Ausgabewandlung nach (Nachtrag); Zielwerte gelten für die Apple-Darstellung (= 2,4-Referenz). |
| Wo liegen LUT, Kontrast, Sättigung? | **Alles im Clip-Baum** (User). Globale Änderungen per Skript-Lauf `neu` oder von Hand je Clip. |
| Welcher Baum? | **Simpel, von Claude gebaut** (User: „Du kannst einen Simplen bauen"): 5 serielle Nodes, siehe Design 1. |
| Weg | **A: erzeugte DRX-Vorlage + CDL-Werte je Node** (User: „So wie wir das beste Ergebnis bekommen"). Begründung: Alle vier Probleme liegen in Werten und Messung; nur A ist exakt nachrechenbar und damit vorher prüfbar. Verworfen: B (native Resolve-Regler in der DRX — Regler-Mathematik undokumentiert, eine DRX je Clip), C (DWG-Ablauf mit DaVinci-Tonemapping — nicht exakt nachrechenbar, nicht simpel; die Hand-Grades enden ohnehin in Phantom Neutral ≈ LC-709). |
| Nodes anlegen | Die API kann keine Nodes anlegen. Der Baum kommt als erzeugte DRX (`Graph.ApplyGradeFromDRX`), die Werte per `TimelineItem.SetCDL` (NodeIndex 1–3) und `Graph.SetLUT(4, …)`. |
| LUT | `Sony/SLog3SGamut3.CineToLC-709.cube` — liegt jeder Resolve-Installation bei (auch Zweit-MacBook). |
| Messbasis | **10-Bit-Originale**, Proxy nur als Ersatz (Proxy-Chroma ≈ 2 % flacher, Original b\* ≈ +1). |
| Einheit | Belichtung und Weißabgleich **je Clip**; ein Einsatz bekommt nur bei deutlicher Abweichung einen eigenen Wert. |
| Wo geschrieben? | Auf einer **Kopie der Feinschnitt-Timeline** (`Timeline.DuplicateTimeline`), Name im Kundenschema mit Versionsnummer + 1; das Original bleibt unverändert. |
| Form | **Getestete AutoCut-Stufe** `scripts/autocut_grading.py` (wie „Kanten", „Replay") statt Kopiervorlage. |
| Projekt-Farbmanagement | Nur lesen. Die Rechnung setzt voraus, dass die Clips unkonvertiert als S-Log3 in den Node gehen (Befund Taxodia: RCM v2, Input = Timeline = Rec.709 (Scene), Output Rec.709-A, Clip-Data-Level „Auto", Input Color Space „Project"). |
| Handänderungen | API kann Node-Werte nicht lesen (kein `GetCDL`). Erkennung über `ExportLUT` je Clip (nur Color-Seite) gegen die zuletzt gesetzten Werte. |

## Design

### 1. Node-Baum

Serielle Kette, Nummern = API-`NodeIndex`. Nodes 01–03 arbeiten im S-Log3-Raum (normierter Codewert CV/1023) vor der
LUT, Node 05 im Rec.709-Raum danach.

| Nr | Name im Node | Inhalt | Werte |
|---|---|---|---|
| 01 | `BALANCE` | Belichtung + Weißabgleich | je Clip gemessen (Design 5) |
| 02 | `ANGLEICH` | Zweitkamera → Ton-Kamera | je Person gefittet; alle anderen Items neutral |
| 03 | `KONTRAST/SAT` | Look | global aus dem Look-Profil |
| 04 | `LUT` | Umwandlung S-Log3 → Rec.709 | `SetLUT` aus dem Look-Profil |
| 05 | `HAND` | leer, für Handarbeit | nie beschrieben |

Notation: `STOP` = 261,5 · log10(2) / 1023 = 0,07695 (eine Blende in S-Log3), `P` = S-Log3(0,18) = 420/1023 = 0,41056.
Jeder Node ist eine ASC-CDL mit Power 1: `y = x · slope + offset`, danach Sättigung mit Rec.709-Luma
(`L = 0,2126 R + 0,7152 G + 0,0722 B`, `y = L + sat · (y − L)`). Zwischen den Nodes wird nicht geklemmt, vor der LUT
auf 0–1 (LUT-Eingang).

- **Node 01:** slope (1, 1, 1), offset `(e + w_r, e, e + w_b) · STOP`, sat 1. `e` = Belichtung in Blenden,
  `w_r`/`w_b` = Weißabgleich in Blenden relativ zu Grün. In S-Log3 entspricht ein Offset einer linearen Verstärkung —
  exakt oberhalb von 4 Blenden unter 18 % Grau (Log-Abschnitt der Kurve), darunter angenähert.
- **Node 02** (nur Zweitkamera): `y = c · (x + d − P) + P` mit `d = (e₂ + v_r, e₂, e₂ + v_b) · STOP` →
  slope `c`, offset `c · d + P · (1 − c)`, sat `1 + Δs`. Sonst slope 1, offset 0, sat 1.
- **Node 03:** slope `k`, offset `P · (1 − k)`, sat `s` (`k` = Kontrast, `s` = Sättigung aus dem Look-Profil).

### 2. DRX-Vorlage (`src/niro_autocut/grading_drx.py`, Datei `tools/autocut/grading/NIRO_Basis_v1.drx`)

**Format** (gelesen an 29 Resolve-Stills aus 18.6 bis 21.0.4, darunter ein Hand-Grade mit drei seriellen Nodes vom
29.08.2026 und Bäume mit 22–29 benannten Nodes):

- XML `<Gallery::GyStill>` mit Metadaten (`SrcHint`, `GalleryPath`, `Label`, Timecodes, Größe, `CreateTime`, `DbId`s),
  Clip-Grade unter `pClipFullVer/ListMgt::LmVersion/Body`, leerer Track-Grade unter `pTrackVer/…/Body`,
  Vorschaubild `Vsr/BtThumnail/Buffer` (JPEG 576×324) und `ClipThumbnails` (Protobuf mit Bildern).
- `Body` = Byte `0x81` + zstd-Frame; entpackt ein Protobuf. Felder:
  - `1` Graph: `1.3` Auflösung, `1.7` Node (wiederholt), `1.8` Verbindung (wiederholt).
  - Node `1.7`: `1` ID, `2` Nummer, `4`/`5` Position im Node-Editor, `6` Name (UTF-8), `7` Typ (1 = Korrektur-Node),
    `9.1` Korrekturen (leer bei leerem Node; LUT als Parameter `0x860000A1` = relativer Pfad).
  - Verbindung `1.8`: `1` von Node-ID, `3` nach Node-ID, `7` eigene ID.
  - `1.1` höchste Node-ID; `1.9` Eingang = {1: Pad-ID, 2: 80, 3: {1: Link-ID, 2: 64, 3: Pad-ID, 4: **erster** Node}};
    `1.10` Ausgang = {1: Pad-ID, 2: 64, 3: {1: Link-ID, 2: 64, 3: Pad-ID, 4: **letzter** Node}} (bei einem einzelnen Node
    ist auch `1.9.2` = 64). Abgeleitet aus fünf echten Bäumen mit 1–3 Nodes und im Test 17.09. bestätigt: Resolve nahm den
    so erzeugten 5-Node-Baum an (Namen, NodeIndex, LUT zurückgelesen).

**Erzeugen** (`erzeuge_basis(pfad)`): Gerüst ist die Struktur des 3-Node-Stills; im Code stehen nur Feldnummern und der
Aufbau eines leeren Nodes, keine Bilddaten und keine Pfade aus dem Hand-Grade.
- 5 leere Korrektur-Nodes (IDs 1–5, Nummern 1–5, Positionen waagerecht im Abstand 300), Namen aus Design 1.
- Verbindungen 1→2→3→4→5, Eingang auf Node 1, Ausgang von Node 5, höchste ID 5.
- Keine LUT in der DRX (setzt `SetLUT`), keine Korrekturwerte.
- Neue `DbId`s (UUID4), `SrcHint` „NIRO Basis v1", `GalleryPath` leer, feste `CreateTime` des Erzeugens.
- **Vorschaubilder entfernt** (Repo ist öffentlich). Lehnt Resolve die DRX in der Probe ohne Vorschaubild ab, wird ein
  schwarzes JPEG 576×324 eingesetzt und `ClipThumbnails` weggelassen.

**Lesen** (`lies_drx(pfad)`): Node-Liste (Nummer, ID, Name, LUT), Verbindungen, Ein-/Ausgang — für Tests, Fake-Resolve
und das Prüfen eines Resolve-Exports (Design 7, `probe`).

### 3. Look-Profil (`tools/autocut/grading/hell_natuerlich.json`)

Alle Zielwerte und Grenzen stehen hier, nicht im Code. Startwerte:

```json
{
 "name": "hell_natuerlich", "stand": "2026-09-17", "drx": "NIRO_Basis_v1.drx",
 "lut": "Sony/SLog3SGamut3.CineToLC-709.cube",
 "look": {"kontrast": 1.05, "saettigung": 1.00, "gewaehlt": "2026-09-17 Taxodia-Test, Variante C"},
 "ausgabe": {"farbraum": "Rec.709-A", "code_exponent": 1.2239},
 "look_varianten": [[0.95, 0.90], [1.00, 0.95], [1.05, 1.00]],
 "belichtung": {"haut_L": 65, "gesicht_min_anteil": 0.004, "neutral_hell_L": 88, "neutral_hell_min_anteil": 0.05,
                "bild_L": 50, "bild_staerke": 0.7, "bild_ohne_ab_L": 90,
                "lichter_L": 98, "lichter_zusatz_max": 0.02, "grenze_blenden": 2.0},
 "weissabgleich": {"ziel_a": 0.0, "ziel_b": 2.0, "neutral_L": [30, 95], "neutral_C_runden": [12, 8, 5],
                   "neutral_min_anteil": 0.02, "haut_winkel": [45, 70], "haut_winkel_ziel": 57.5,
                   "mischlicht_abstand": 12, "grenze_blenden": 1.0},
 "einsatz_eigen": {"belichtung_blenden": 0.7, "weissabgleich_blenden": 0.3},
 "angleich": {"belichtung_max": 1.0, "wb_max": 0.5, "kontrast_max": 0.10, "saettigung_max": 0.15, "paare_max": 6},
 "ampel": {"haut_L": [60, 70], "haut_winkel": [45, 70], "neutral_a_max": 3, "neutral_b": [-1, 5],
           "dunkel_L_min": 8, "paar_haut_de2000_max": 2.0, "hinweise_widerspruch_blenden": 1.0},
 "gegenprobe": {"de2000_mittel_max": 2.0, "raster": [64, 36]}
}
```

Die Look-Wahl (Design 6) trägt `look.kontrast`, `look.saettigung` und `look.gewaehlt` (Datum, Charge) ein.
Abweichende Haut-Ziele je Interview-Person (z. B. dunklere Haut) stehen in der Charge unter
`_intern/autocut/config.yaml` → `grading.haut_L_je_person: {"<Person>": 55}`.

### 4. Farbrechnung (`src/niro_autocut/grading_modell.py`)

Übernommen aus `vorlagen/feinschnitt/color/skripte/colorlib.py` (dort gemessen und gegen ffmpeg `lut3d` geprüft):
S-Log3 ↔ linear, `.cube` laden, trilineare LUT (Resolve-Projekteinstellung „Trilinear"), Rec.709/BT.1886 → CIELAB
(D65), ΔE2000. Neu:
- `node_cdl(nr, werte)` → slope/offset/sat je Node nach Design 1; `resolve_cdl(nr, werte)` → Dict für `SetCDL`
  (`NodeIndex`, Strings mit 4 Nachkommastellen, Power „1.0000 1.0000 1.0000").
- `rendere(x, werte, look, lut)` → Rec.709-Displaywerte über Node 01 → 02 → 03 → Klemmen → LUT.
- `lab(x, …)` und `modell_lut(werte, look, lut, groesse=33)` (Gitter wie `ExportLUT`) für Gegenprobe und `neu`.

### 5. Messung (`src/niro_autocut/grading_messung.py`)

**5.1 Items und Gruppen.** Grundlage ist ein Schnappschuss der Feinschnitt-Timeline (`ResolveSession.read_timeline`, nur
lesend; oder `--readback <json>`): je Item Spur, Start, Dauer, Datei, `left_offset`, Tempo, aktiv.
- V1/V2 mit Datei im `transcripts_index.json` (NFC, `path_map`): Gruppe = (`person`, `kamera_rolle`). `ton` =
  Referenzkamera, `kontext` = Zweitkamera (Node 02). Fehlt `kamera_rolle`, gilt die AutoCut-Regel FX3 = ton, a7 = kontext.
- V3: B-Roll (Node 02 neutral).
- V1/V2 mit Datei, aber nicht im Index: wie B-Roll gemessen, Ampel mindestens gelb („nicht im Index").
- Items ohne Datei (Generator, Titel, Compound): ausgelassen und im Bericht gelistet. V4 wird nie betrachtet.
- Deaktivierte Items zählen mit (V2 liegt durchgehend unter jedem O-Ton-Stück).

**5.2 Bilder.** Je Einsatz 3 Quellbilder bei 20/50/80 % des genutzten Bereichs: Quellzeit =
`(left_offset + k · tempo/100) / fps_timeline` für den Timeline-Frame `k` ab Item-Start.
- Dekodieren wie `orig_check.py`: ffmpeg `-pix_fmt yuv422p10le` ohne Range-Wandlung, Y/1023 und (Cb, Cr − 512)/1023 →
  Rec.709-Matrix → CV/1023 je Kanal, verkleinert auf 960×540.
- Fehlt das Original (NAS nicht gemountet), der Proxy `<Ordner>/Proxy/<Stamm>.mov` wie in `broll_trims.py` (TV-Range,
  8 Bit; Befund 15.09.: Y8 = 16 + CV10 · 219/1023) — Ampel mindestens gelb („Proxy").
- Cache `_intern/autocut/work/grading/<fingerprint>/<quellframe>.npz` (uint16, komprimiert).
- Gesichter: Apple Vision (`tools/autocut/werkzeuge/faces.swift`, Kopie von `vorlagen/feinschnitt/gesichtscheck/faces.swift`,
  einmal je Charge nach `_intern/autocut/work/grading/faces` übersetzt) auf dem LUT-Vorschaubild ohne Korrektur.
  Gesicht zählt ab `gesicht_min_anteil` der Bildfläche.

**5.3 Belichtung `e` (Node 01).** Je Bild abwechselnd mit dem Weißabgleich in 3 Runden (Start `e = 0`, `w = 0`); jede
Zielsuche per Bisektion auf 0,01 Blenden über die volle Kette (Nodes 01–04, aktueller Look). Anker in dieser Reihenfolge:
1. **Haut** (Gesicht vorhanden): Pixel im inneren Gesichtsrechteck (Breite 25–75 %, Höhe 35–80 %), davon die mittleren
   60 % nach L\* (Haare, Brille, Glanz raus) → Median-L\* = `haut_L` (bzw. Wert je Person).
2. **Helle neutrale Fläche** (kein Gesicht): Pixel mit C\* ≤ 8 außerhalb von Gesichtern, in den hellsten 40 % des Bildes
   (nach L\*), nicht ausgebrannt (wie in 5.4: kein Kanal ≥ 0,90, L\* < 97); Anteil ≥ `neutral_hell_min_anteil` →
   Median-L\* = `neutral_hell_L`.
3. **Bild:** Median-L\* aller Pixel ohne die schon unkorrigiert hellen (L\* ≥ `bild_ohne_ab_L`: Fenster, Lampen,
   Bildschirme) → `bild_L`; angewendet wird nur `bild_staerke` · e (ein dunkler Schreibtisch bleibt dunkler).

Liefern Anker 1 und 2 beide Werte, die mehr als `hinweise_widerspruch_blenden` auseinanderliegen, gilt Anker 1, Ampel gelb.
**Lichterschutz:** Solange unter den Pixeln, die im Sensor nicht ausgebrannt sind (alle Kanäle S-Log3 < 0,90), mehr als
`lichter_zusatz_max` der Bildfläche bei `e` L\* ≥ `lichter_L` erreichen, wird `e` in 0,05-Schritten verkleinert (Ampel
gelb). Bezug war zuerst „Anteil bei e = 0 mit LUT" — damit brannte im Test das Fenster hinter Ludwig von 0 auf 10 % aus. **Grenze** ±`grenze_blenden` (gegriffen → gelb).

**5.4 Weißabgleich `w_r`, `w_b` (Node 01).**
- **Neutrale Kandidaten:** L\* in `neutral_L`, außerhalb der um 50 % vergrößerten Gesichtsrechtecke, kein Kanal ≥ 0,90
  (S-Log3) und L\* < 97; Chroma-Grenze je Runde aus `neutral_C_runden`.
- **Mit Anker** (Anteil ≥ `neutral_min_anteil`): Median von a\* und b\* über die neutraleren 50 % der Kandidaten →
  `w_r`, `w_b` per Newton-Schritten (numerische Ableitung über die Kette), bis Median a\* = `ziel_a`, b\* = `ziel_b`.
- **Mischlicht:** Zwei Häufungen der Kandidaten in a\*/b\* (2-Means) mit Zentren-Abstand > `mischlicht_abstand` und je
  ≥ 25 % → Abgleich auf die größere Häufung, Ampel gelb („Mischlicht — Gesicht von Hand"). Keine automatische Korrektur
  über den Hautton: Im Test (C0246) trieb sie die Haut-Chroma auf 50.
- **Gegenprobe Haut:** Farbwinkel h = atan2(b\*, a\*) der Hautpixel nach dem Abgleich in mindestens der Hälfte der Bilder
  eines Clips außerhalb `haut_winkel` → gelb (Hinweis, keine Korrektur).
- **Ohne neutralen Anker, mit Gesicht:** Abgleich nur auf der Warm-Kalt-Achse (`w_r = −w_b`), bis h = `haut_winkel_ziel`.
- **Ohne beides:** `w = 0`, gelb („kein Weißabgleich-Anker").
- **Grenze** ±`grenze_blenden` je Kanal (gegriffen → gelb).

**5.5 Clip und Einsatz.** Einsatz-Wert = Median seiner 3 Bilder; Clip-Wert = Median aller Bilder aller Einsätze des Clips.
Ein Einsatz behält seinen eigenen Wert, wenn er um mehr als `einsatz_eigen.belichtung_blenden` (e) oder
`einsatz_eigen.weissabgleich_blenden` (w_r oder w_b) vom Clip-Wert abweicht; sonst gilt der Clip-Wert.

**5.6 Angleich (Node 02).** Je Person bis `paare_max` zeitgleiche Paare Ton-/Zweitkamera aus V1/V2-Überlappungen
(Mitte der Überlappung, Versatz aus `_intern/autocut/sync.json`, nur Paare mit `ok`); beide Seiten mit ihrer Node 01.
Regionen: Haut (wie 5.3), dunkle Kleidung (dunkelste 30 % im Oberkörper: ±1,2 Gesichtsbreiten, 1,2–3,5 Gesichtshöhen
unter dem Gesicht), helles Hemd (hellste 25 % derselben Region, nur wenn in beiden Kameras L\* > 70). Robuster Fit
(soft-L1) von `e₂`, `v_r`, `v_b`, `c`, `Δs` in den Grenzen aus `angleich` gegen die Lab-Differenzen (Gewichte: Haut L 1,
a/b 1,5; dunkle Kleidung 0,6; Hemd 1,0), regularisiert. Ergebnis: mittleres Haut-ΔE2000 der Paare. Ohne Paare: neutral,
gelb („kein Kamera-Paar").

### 6. Ampel, Kontaktbögen, Bericht (`src/niro_autocut/grading_bericht.py`)

**Ampel je Clip** (gemessen an der Rechnung mit den Planwerten):
- **Grün:** alle zutreffenden Werte in `ampel` — Haut L\* und Farbwinkel (mit Gesicht), neutrale Flächen a\*/b\* (mit
  Anker), dunkle Kleidung L\* ≥ `dunkel_L_min` (Interviews), Lichter-Zusatz ≤ `lichter_zusatz_max`, Paar-Haut-ΔE2000
  ≤ `paar_haut_de2000_max` (Zweitkamera) — und keine Grenze gegriffen, kein Hinweis aus Design 5.
- **Gelb:** sonst. Jeder gelbe Clip steht mit Grund im Bericht; Claude sieht sich jeden gelben Clip im Kontaktbogen an.
- **Rot:** Bild nicht lesbar (Datei fehlt, ffmpeg-Fehler) oder keine auswertbaren Pixel (> 95 % schwarz oder
  ausgebrannt). Solange ein Clip rot ist, schreibt kein Schritt in Resolve; `--auslassen "<Clip>"` nimmt einen Clip
  ausdrücklich heraus (Bericht nennt ihn, Items behalten ihren bisherigen Grade).

**Kontaktbögen** unter `_intern/autocut/grading/`:
- `kontaktbogen_NN.jpg` (je Bogen höchstens 12 Zeilen): je Clip eine Zeile am 50-%-Bild des ersten Einsatzes —
  **nur LUT | bisher | neu** —
  mit Gruppe, Einsätzen, `e`/`w_r`/`w_b`, Anker, Haut-L\*, neutral a\*/b\*, Ampel. Spalte „bisher" nur, wenn die alte
  Stufe 6h in der Charge lief (`_intern/color/grading_einsatz*.json` → Gruppe je Item, `grading_vorschlag.json` → CDL,
  `broll_trims.json` → Trim).
- `look_varianten.jpg`: bis zu 8 typische Clips × die 3 `look_varianten` — je Person die Ton-Kamera (höchstens 3), eine
  Zweitkamera, dazu die B-Roll-Clips mit dem dunkelsten, dem hellsten und dem mittleren Bild und ein gelber Clip; freie
  Plätze füllen weitere B-Roll-Clips. Der User wählt einmal; Claude trägt die Wahl ins Look-Profil ein und startet
  `messen` erneut.
- `gegenprobe.jpg` (Design 7): je Probe Resolve-Standbild | Rechnung | Differenz (vierfach verstärkt).

**Bericht** `Ergebnisse/Rohschnitt/<video>-grading.md` (`<video>` wie bei der Kantenprüfung): Kopf (Projekt, Timeline,
Kopie, Look-Profil mit Werten, Farbmanagement-Befund), Tabelle je Clip (Gruppe, Einsätze, Werte, Anker, Messwerte,
Ampel, Grund), Paare je Person, ausgelassene Items, Gegenprobe, übersprungene Items bei `neu`. Dazu ein Protokoll-Eintrag
je Schritt.

### 7. Skript `scripts/autocut_grading.py`

```
"$PY" "$TOOL/scripts/autocut_grading.py" "$CHARGE" messen [--timeline "<Feinschnitt>"] [--readback "<json>"] [--look "<json>"] [--auslassen "<Clip>"]…
"$PY" "$TOOL/scripts/autocut_grading.py" "$CHARGE" probe      --projekt "<Projekt>" --kopie "<Timeline-Kopie>"
"$PY" "$TOOL/scripts/autocut_grading.py" "$CHARGE" gegenprobe --projekt "<Projekt>" --kopie "<Timeline-Kopie>"
"$PY" "$TOOL/scripts/autocut_grading.py" "$CHARGE" anwenden   --projekt "<Projekt>" --kopie "<Timeline-Kopie>"
"$PY" "$TOOL/scripts/autocut_grading.py" "$CHARGE" neu        --projekt "<Projekt>" --kopie "<Timeline-Kopie>"
```

`--timeline` fehlt → `letzte_timeline` (wie „Kanten"). `--projekt` ist die Schreibfreigabe des Users aus dem Chat und
muss exakt dem geöffneten Projekt entsprechen. Alle Schritte außer `messen` schreiben in Resolve und prüfen vorher:
Projektname, Wiedergabe (`wiedergabe.status`: „spielt_ab" → Abbruch; „unklar" → Hinweis „bitte nicht abspielen"),
`IsRenderingInProgress`. Am Ende sind Timeline, Seite und Media-Pool-Bin des Users wieder aktiv (auch nach Fehlern).
Schreibziele nur in den AutoCut-Bereichen (`Charge.assert_writable`).

**`messen`** (Resolve nur lesend):
1. Schnappschuss → `_intern/autocut/grading/readback.json`.
2. Farbmanagement lesen wie `grade_check.py` → `farbmanagement.json`. Zulässig: DaVinci YRGB ohne Farbmanagement oder
   RCM, bei dem der Input-Farbraum der Clips dem Timeline-Farbraum entspricht; Clip-Data-Level „Auto" oder „Full".
   Sonst (anderer Input-Farbraum, ACES, Clip-Data-Level „Video") Abbruch. Output ≠ Timeline wird nur gemeldet —
   entscheidend ist die Gegenprobe.
3. Gruppen, Bilder, Gesichter, Messung, Angleich (Design 5), Ampel (Design 6).
4. `grading_plan.json`: Look-Profil (Inhalt + SHA-256), Gruppen, Clip- und Einsatz-Werte, Node-02-Werte je Person,
   Ampel, ausgelassene Items; oben `plan_hash` (SHA-256 des Plans ohne Zeitstempel).
5. Kontaktbögen, Look-Varianten, Bericht, Protokoll.

**`probe`** (ein Clip):
1. Plan ohne rote Clips vorhanden.
2. Kopie: gibt es `--kopie` nicht, `DuplicateTimeline` der Feinschnitt-Timeline unter diesem Namen, Name zurücklesen,
   `grading/kopie.json` (Original, Kopie, Zeit). Gibt es sie schon, muss sie in `kopie.json` stehen — sonst Abbruch
   (nie in eine fremde Timeline schreiben).
3. Erstes V1-Item der Kopie: `GetProperty()` vorher; `ApplyGradeFromDRX(drx, 0)`; `GetNumNodes() == 5`;
   `GetNodeLabel(i)` = Namen; `SetCDL` für 1–3; `SetLUT(4, lut)`; `GetLUT(4) == lut`; `GetProperty()` nachher — jede
   geänderte Eigenschaft wird gemeldet, geänderte Stabilisierungs-Eigenschaften brechen ab.
4. `grading/probe.json` (ok, plan_hash, Einzelergebnisse). Scheitert ein Punkt: Abbruch, nichts weiter geschrieben.

**`gegenprobe`** (Voraussetzung: `probe.json` ok):
1. Proben: je Interview-Gruppe (Person × Kamera) ein Item plus 4 B-Roll-Items (Clips mit dem dunkelsten, hellsten und
   mittleren Bild, ein gelber Clip) — bei Taxodia 6 + 4 = 10 —, jeweils an einem Frame, an dem das Item aktiv und oben
   sichtbar ist (kein aktives Item auf höheren Spuren V1–V3).
2. Diese Items graden wie `anwenden` (Design unten), die Kopie kurz aktivieren (vorher im Chat angekündigt), V4 der
   Kopie ausschalten.
3. Je Probe ein Skriptaufruf `SetCurrentTimecode`, ein zweiter `ExportCurrentFrameAsStill(png)` (Befund 09.09.: je
   Skript nur ein neues Standbild; Inspector-Transformationen sind nicht enthalten, das Bild entspricht dem Quellbild).
4. V4-Zustand der Kopie und User-Timeline wiederherstellen.
5. Vergleich mit der Rechnung am selben Quellbild aus dem Original, **inklusive Ausgabewandlung** (Rec.709-A: Code =
   LUT-Ausgabe^`ausgabe.code_exponent`): Rechnung per SIFT-Merkmalen + RANSAC-Homographie auf das Standbild ausrichten
   (auf der Color-Seite enthält das Standbild die Begradigen-Transforms), Quellbild bei B-Roll ±2 Frames nach bestem
   Treffer, dann `gegenprobe.raster`-Zellen in 960×540 mitteln, ΔE2000 je Zelle, Median ≤ `de2000_mittel_max`; mit Gesicht
   zusätzlich Haut-ΔE2000 ≤ 2.
6. Steht Resolve auf der Color-Seite, zusätzlich (Kopie aktiv, Abspielkopf auf der Probe, siehe 3):
   - `ExportLUT` (33er) je Probe gegen `modell_lut` im Bereich 0,05–0,80 (Mittel, 95-%-Wert, Maximum in 8-Bit-Stufen).
   - An der ersten Probe `GrabStill` + `ExportStills(…, "drx")`, `lies_drx` → 5 Nodes, Namen, LUT in Node 4 (Beleg, dass
     Resolve den Baum so übernommen hat; belegt auch die erschlossenen Felder aus Design 2). Das eigene Still danach
     löschen; der Export wird ohne Vorschaubilder als Test-Fixture abgelegt.
7. `grading/gegenprobe.json` (ok, plan_hash, Werte je Probe), `gegenprobe.jpg`. Abweichung → Exit 1: Ursache klären
   (Datenpegel, CDL-Rechnung in Resolve, Farbmanagement), Rechnung korrigieren, `messen` und `gegenprobe` erneut.

**`anwenden`** (Voraussetzung: `gegenprobe.json` ok mit demselben `plan_hash`):
1. Alle V1–V3-Items der Kopie inklusive deaktivierter, nie V4. Zuordnung zum Plan über Clipname (Clip-Wert) und
   Spur + Start (Einsatz-Wert); ein Item ohne Plan-Eintrag wird ausgelassen und gemeldet.
2. Je Item: `ApplyGradeFromDRX` → `SetCDL` 1–3 → `SetLUT(4)` → Readback (5 Nodes, Namen, LUT). Geschrieben wird in die
   aktive Farbversion; keine neue Version.
3. Liefert Resolve `False` oder passt der Readback nicht: sofort stoppen, alle Items zurücklesen, Bericht, Exit 2. Ein
   erneuter Lauf überspringt Items, die in `grading_einsatz.json` als fertig stehen und deren Readback passt.
4. `SaveProject`, `grading/grading_einsatz.json` (je Item: Spur, Start, Clip, Gruppe, gesetzte Werte je Node, Readback,
   Ampel), Bericht, Protokoll.

**`neu`** (Werte-Neu-Lauf, z. B. nach geänderter Look-Wahl und erneutem `messen`; Voraussetzung: eine bestandene
Gegenprobe der Charge):
1. Resolve muss auf der Color-Seite stehen und die Kopie die aktive Timeline sein (der User öffnet sie selbst) — sonst
   Abbruch mit Hinweis; Seite und Timeline werden für `neu` nie per Skript gewechselt.
2. Je Item aus `grading_einsatz.json`: `ExportLUT` gegen `modell_lut` der zuletzt gesetzten Werte (95-%-Wert ≤ 2
   8-Bit-Stufen) → passt: `SetCDL` 1–3 und `SetLUT(4)` mit den neuen Planwerten, Readback; passt nicht: auslassen
   („von Hand geändert").
3. `grading_einsatz.json` fortschreiben, Bericht mit der Liste ausgelassener Items, Protokoll.

Exit-Codes aller Schritte: 0 = ok (alles grün bzw. geschrieben), 1 = Befunde (gelbe Clips; Gegenprobe abweichend;
`neu` mit ausgelassenen Items), 2 = Voraussetzung fehlt oder Fehler.

### 8. Dateien

| Pfad | Inhalt |
|---|---|
| `tools/autocut/scripts/autocut_grading.py` | Schritte `messen`, `probe`, `gegenprobe`, `anwenden`, `neu` |
| `tools/autocut/src/niro_autocut/grading_drx.py` | DRX lesen, Basis-DRX erzeugen |
| `tools/autocut/src/niro_autocut/grading_modell.py` | Farbrechnung, Node-CDLs, Modell-LUT |
| `tools/autocut/src/niro_autocut/grading_messung.py` | Gruppen, Bilder, Gesichter, Belichtung, Weißabgleich, Angleich |
| `tools/autocut/src/niro_autocut/grading_resolve.py` | Item graden und zurücklesen, Kopie anlegen, Standbilder, `ExportLUT` |
| `tools/autocut/src/niro_autocut/grading_bericht.py` | Ampel, Kontaktbögen, Bericht |
| `tools/autocut/grading/NIRO_Basis_v1.drx`, `hell_natuerlich.json` | Vorlage und Look-Profil |
| `tools/autocut/werkzeuge/faces.swift` | Vision-Gesichtsboxen |
| Charge: `_intern/autocut/grading/`, `_intern/autocut/work/grading/`, `Ergebnisse/Rohschnitt/<video>-grading.md` | Pläne, Nachweise, Cache, Bericht |

`grading_resolve.py` ist das gemeinsame Stück für die Vorlage `begradigen/pruefung_resolve.py`: Sie gradet ihre
Prüf-Timeline künftig mit Baum und Planwerten statt über `color/grading_anwenden.py`.

## Fehlerbehandlung

| Lage | Verhalten |
|---|---|
| Original und Proxy fehlen / ffmpeg-Fehler | Clip rot; kein Schreiben, bis behoben oder `--auslassen` |
| Farbmanagement passt nicht (Design 7, `messen` 2) | Exit 2 mit gelesenen Einstellungen; Einstellungen nie per Skript ändern |
| Offenes Projekt ≠ `--projekt` | Exit 2, nichts geschrieben |
| Wiedergabe läuft / Resolve rendert | Exit 2, nichts geschrieben |
| `--kopie` existiert, stammt nicht von dieser Stufe | Exit 2 |
| Resolve nimmt die DRX nicht an, Nodes/Namen/LUT falsch | `probe` Exit 2 nach dem ersten Clip; bei fehlendem Vorschaubild zuerst die Variante mit schwarzem JPEG (Design 2) |
| Stabilisierung ändert sich durch `ApplyGradeFromDRX` | `probe` Exit 2; Lösung klären, bevor ein weiterer Clip gegradet wird |
| Gegenprobe weicht ab | Exit 1; `anwenden` verweigert, bis eine Gegenprobe mit aktuellem `plan_hash` besteht |
| `SetCDL`/`SetLUT`/`ApplyGradeFromDRX` liefert `False` | Stopp, Readback aller Items, Exit 2; erneuter Lauf macht nur Fehlendes |
| `neu` nicht auf der Color-Seite oder Kopie nicht aktiv | Exit 2 mit Hinweis, Seite und Timeline nicht wechseln |
| Item ohne Plan-Eintrag (z. B. vom User neu eingefügt) | ausgelassen, im Bericht gelistet |

## Tests (pytest, ohne Resolve)

- `test_grading_drx.py`: `erzeuge_basis` → `lies_drx`: 5 Nodes, Nummern 1–5, Namen, Kette 1→…→5, Ein-/Ausgang, keine
  LUT, keine Vorschaubilder, gültiges XML, `0x81`+zstd; Protobuf-Kodierung (Varint, Längenfelder) gegen Handbeispiele;
  die eingecheckte `NIRO_Basis_v1.drx` entspricht dem Erzeuger (ohne `DbId`/Zeit); liegt der Resolve-Export aus der
  Gegenprobe als Fixture vor (Vorschaubilder entfernt), liest `lies_drx` ihn mit denselben Nodes, Namen und Verbindungen.
- `test_grading_modell.py`: S-Log3 ↔ linear; Node-Formeln (Node 01 reine Belichtung verschiebt 18 % Grau um genau
  `e · STOP`; Node 03 hält `P` fest); Kette 01→03 ohne Sättigung = eine zusammengesetzte CDL; trilineare LUT an
  Gitterpunkten und Zwischenwerten (kleiner synthetischer Würfel); ΔE2000 gegen Referenzpaare (Sharma et al.);
  `resolve_cdl`-Format.
- `test_grading_messung.py` mit synthetischen S-Log3-Bildern (Wand, Hautfläche mit Gesichtsbox, dunkle Kleidung, Fenster)
  und synthetischer LUT:
  - Fehlbelichtung −1,3 Blenden und Farbstich (R +0,2, B −0,3 Blenden) werden auf ±0,05 zurückgemessen.
  - Ankerwahl Haut → Wand → Bild; Bild-Anker mit Stärke 0,7; Widerspruch > 1 Blende → gelb.
  - Lichterschutz verkleinert `e`, bis ≤ 2 % zusätzlich ausbrennen; Grenzen ±2 / ±1 greifen und färben gelb.
  - Mischlicht mit zwei Lichtfarben → Abgleich auf die Häufung am Gesicht, gelb.
  - Ohne neutralen Anker: Abgleich nur auf der Warm-Kalt-Achse bis Farbwinkel 57,5°.
  - Clip-/Einsatz-Regel an den Schwellen 0,7 bzw. 0,3 Blenden.
  - Angleich findet einen eingebauten Versatz der Zweitkamera (e₂, v, c, Δs) in den Grenzen wieder.
  - Quellzeit-Rechnung bei Tempo 100 % und 50 %.
- `test_grading_bericht.py`: Ampel-Regeln (grün/gelb/rot mit Gründen), Bericht-Tabelle, Kontaktbogen-Datei entsteht.
- `test_grading_script.py` mit Fake-Resolve (erweitert um Graph mit Nodes, `ApplyGradeFromDRX` über `lies_drx`,
  `SetCDL` je NodeIndex, `SetLUT`/`GetLUT`, `GetNodeLabel`, `GetNumNodes`, `DuplicateTimeline`, `SetCurrentTimecode`,
  `ExportCurrentFrameAsStill`, `ExportLUT` aus `modell_lut`, `GetCurrentPage`) und Bild-Cache-Fixtures statt ffmpeg:
  - `messen` schreibt Plan, Bericht, Protokoll; roter Clip → Exit 2 in `probe`/`anwenden` ohne Schreibaufruf.
  - Falsches Projekt, laufende Wiedergabe, fremde Kopie → Exit 2 ohne Schreibaufruf.
  - `anwenden` ohne bestandene Gegenprobe oder mit altem `plan_hash` verweigert.
  - `anwenden` gradet V1–V3 inklusive deaktivierter Items, nie V4; richtige Werte je NodeIndex; User-Timeline zurück.
  - Schreibfehler mitten im Lauf → Exit 2; zweiter Lauf macht nur den Rest.
  - `neu` außerhalb der Color-Seite oder ohne aktive Kopie → Exit 2; von Hand geänderte Items (abweichender
    `ExportLUT`) werden ausgelassen.

## Doku

- `tools/autocut/WORKFLOW-AutoCut.md`: Unterbefehl „Grading" in der Tabelle; Abschnitt 6h neu (Schritte, Look-Wahl,
  Ampel, Gegenprobe, `neu`, Fallen); Hinweis, dass die alten Color-Vorlagen nur noch Taxodia-Referenz sind.
- `tools/autocut/vorlagen/README.md`: Zeile `color/*` als ersetzt markieren; `begradigen/pruefung_resolve.py` angepasst.
- `tools/autocut/README.md`: Stufen-Tabelle.
- `tools/resolve/WORKFLOW-Resolve.md`: DRX-Format, `ApplyGradeFromDRX`/`SetCDL` mit NodeIndex, Standbild mit Grade —
  mit den Befunden aus `probe` und `gegenprobe`.
- Memory: Grading-Stufe, Look-Profil, Probe-Befunde.

## Nicht im Umfang

Secondaries, Qualifier, Power Windows und Vignetten (Node 05 bleibt Handarbeit); Änderungen am Projekt-Farbmanagement;
DWG/CST-Ablauf (Weg C) und native Resolve-Regler (Weg B); Farbgruppen und Shared Nodes; neue Farbversionen; andere
Kamerasysteme als Sony S-Log3/S-Gamut3.Cine (brauchen eigene LUT und Pegel-Probe); Rauschunterdrückung; Grafikebene V4;
weitere Look-Profile (später als zusätzliche JSON-Dateien).

## Reihenfolge

1. `grading_drx.py` + Tests; `NIRO_Basis_v1.drx` erzeugen.
2. `grading_modell.py`, `grading_messung.py`, `grading_bericht.py` + Tests.
3. `grading_resolve.py`, `autocut_grading.py`, Fake-Resolve-Erweiterung + Tests; `venv/bin/python -m pytest -q` grün.
4. Taxodia `messen` (Originale vom NAS) → Kontaktbögen und Look-Varianten dem User zeigen → Wahl ins Look-Profil →
   `messen` erneut.
5. Freigabe des Projekts „Taxodia 09.26" im Chat → `probe` → `gegenprobe` (Timeline-Wechsel vorher abstimmen) →
   bei Abweichung Ursache klären → `anwenden` auf der Kopie → User vergleicht mit dem Original.
6. Doku, `begradigen/pruefung_resolve.py`, Memory. Commit und Push nur nach OK des Users.

## Nachtrag: Test auf einer Taxodia-Kopie (17.09.2026)

Auf Anweisung des Users („Taxodia ist offen, mache jetzt den Test") mit Prototyp-Skripten (Kopien in
`projects/…/2026-09 Dreh 08.09/_intern/autocut/grading/test_2026-09-17/prototyp_skripte/`), nicht mit der Stufe aus Design 7.

**Ablauf:**
- Kopie „AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test" der Feinschnitt-Timeline (Projekt „Taxodia 09.26").
- Probe an einem Item: eigene 3-Node-DRX neu verpackt → angenommen; erzeugter 5-Node-Baum ohne Vorschaubilder →
  angenommen, `SetCDL` 1–3 + `SetLUT(4)` wirken, Farbversion und `GetProperty()` unverändert.
- 8 Clips gemessen und gegradet (Look 1,00/0,95), 16 Standbilder (bisher/neu, V4/V5 der Kopie dafür aus), `ExportLUT` an
  3 Items, Look-Varianten A/B/C → User wählt C.
- Danach alle 115 Items der Kopie mit Look C (238 Messbilder, 25 Clips, Readback 115/115, 99 s).

**Belege:**
- Node-Rechnung: `ExportLUT` gegen Modell Mittel 0,15–0,25, 95-%-Wert 0,6–1,2 8-Bit-Stufen.
- Ausgabe: Standbild = LUT-Ausgabe^(2,4/1,961) — mittlerer Fehler 1,1 Stufen (ohne Wandlung 12,4; Hypothese
  Video-Pegel am Eingang 11,7). Mit Wandlung Gegenprobe an 8 Items ΔE2000 Median 0,47–0,78, p90 ≤ 1,64.
- Vorher/nachher an den Resolve-Standbildern (Darstellung wie am Mac): Schwarz (L\* ≤ 3) bis 16 % → 0 %, Chroma p95 −2 bis
  −5, Hautwinkel Flammann 32° → 43°, Haut Hein 76 → 65, Ludwig 58 → 62, B-Roll-Median 32 → 38–42.

**Geänderte Regeln** (oben eingearbeitet): Ausgabewandlung in Gegenprobe und Kontaktbögen (Design 3 `ausgabe`, 7);
Mischlicht ohne automatische Korrektur (5.4); Haut-Hinweis erst bei Mehrheit der Bilder (5.4); Lichterschutz bezogen auf
im Sensor nicht ausgebrannte Pixel (5.3); Standbild-Ausrichtung per SIFT/Homographie (7). Zusätzlich:
- **Weißabgleich Runde 1** nimmt die 20 % farbärmsten Kandidaten statt C\* ≤ 12 (ersetzt den ersten Wert von
  `neutral_C_runden`); hielt bei starkem Farbstich (C0242 blau). Runden 2/3 wie gehabt, mit demselben Rückfall.
- **Quellbild-Zeit** aus `GetSourceStartFrame` statt Left-Offset: Quellframe = `src_start + k · tempo/100 · fps_quelle/fps_timeline`.

**Offen für die Umsetzung:**
- 10 von 19 B-Roll-Clips stehen an der Belichtungsgrenze +2 Blenden (Material ≈ 2 Blenden dunkler belichtet): Grenze
  anheben oder gelb lassen — nach Sichtung mit dem User entscheiden.
- Bild-Anker (`bild_staerke` 0,7): C0255 wirkte mit Look B milchig; mit Look C erneut beurteilen.
- Node 02 (Angleich), Schritt `neu` und die Handänderungs-Erkennung über `ExportLUT` sind noch ungetestet.
- Hinweis „Mischlicht/Haut außerhalb" schlug im Prototyp bei 17 von 25 Clips an → mit der Mehrheitsregel erneut prüfen.
- **Belichtungsgrenze aufgehoben** (User 17.09.: „Hebe die Blendengrenze auf, ich kann später ja NR drauf machen"):
  `belichtung.grenze_blenden` entfällt bzw. ist nur noch ein Plausibilitätswert (8); Clips über +2 Blenden bekommen den
  Hinweis „NR prüfen". Test: B-Roll bis +3,12 Blenden.
- **Sensor-Clip statt fester Schwelle:** Das FX3-S-Log3 clippt in diesem Material bei CV 891/892 (Plateau im
  Max-Kanal-Histogramm, ≈ +6,1 Blenden), nicht bei 0,90. Der Lichterschutz muss den Clip je Kamera als Plateau erkennen und
  ausgebrannte Pixel ausnehmen: Abdunkeln macht sie nur grau, holt keine Zeichnung zurück (Fenster hinter Ludwig).
- **Power Windows** sind im DRX enthalten (Parameterfamilien 0x085…, 0x08f…, 0x0885… und Seitenverhältnis-Matrizen
  0x883…–0x88f… in den PW-Nodes der Team-Grades); Bedeutung der Werte ist noch per Versuch zu belegen. Nicht im Umfang, bis
  der User es beauftragt.
- **Belichtung als lineare Verstärkung, nicht als Log-Offset** (User-Feedback 17.09. zur B-Roll: „kaum Kontrast, Schwarz komplett
  zu hell gezogen", „nur die Interviews sind on point"): Ein CDL-Offset in S-Log3 ist nur im Log-Abschnitt eine Verstärkung; bei
  +2 … +3 Blenden hebt er den Schwarzpunkt (CV 95 → ≈ 340). Node 01 bekommt deshalb eine **1D-LUT je Clip** (exakt
  `lin_to_slog3(slog3_to_lin(x) · 2^(e + w_Kanal))`, 4096 Stützstellen), die CDL in Node 01 bleibt neutral für Handarbeit.
  Gegenprobe C0252: ΔE2000 Median 0,81 (Offset-Modell p90 5,7). Folgen: LUTs liegen im Resolve-LUT-Ordner
  (`NIRO Grading/<Projekt>/`) und müssen auf jeden Rechner mit dem Projekt (Cloud!) — Verteilung in der Umsetzung klären.
- **Ein Wert je Clip** (auch B-Roll): Einsatz-Sonderwerte entstanden aus wechselnden Messankern (Papier statt Haut), nicht aus
  anderem Licht, und machten Einsätze desselben Takes 1,5 Blenden dunkler. `einsatz_eigen` entfällt; Wechsel des Lichts im Take
  bleibt Handarbeit.
- **Lichterschutz-Toleranz 5 %** (nur nicht ausgebrannte Pixel), am Taxodia-Material aus 2/4/5/8 % gewählt; kein Schatten-Toe.
- **LUT-Verteilung auf beide Macs** (User 17.09.: „damit auf dem 2. Mac auch die LUTs drin sind" → „über einen gemeinsamen
  Ordner im NAS", Abgleich „nur beim Arbeiten"): gemeinsame Ablage `01_Projekte/03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading/<Resolve-Projekt>/` neben den
  Team-LUTs, lokale Kopie im Resolve-LUT-Ordner (Renders ohne NAS). `tools/resolve/luts_sync.sh` gleicht NAS ↔ lokal ab
  (löscht nie). Kein Hintergrunddienst, keine Git-Hooks: Die Stufe `autocut_grading.py` und Claude rufen den Abgleich vor
  Resolve-Arbeit und nach jedem Grading auf. Ausnahme von „NAS nur lesen" nur für diesen Ordner. Ein erster Weg über
  GitHub + Pull-Hooks (Commit 3fecd1e) ist damit ersetzt.
