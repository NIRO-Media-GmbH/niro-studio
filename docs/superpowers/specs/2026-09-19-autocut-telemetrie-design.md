# AutoCut — Kamera-Telemetrie je Clip (Spec)

Datum: 2026-09-19 · Status: Abschnitte 1–3 im Chat vom User freigegeben (19.09.), Nachtrag mit Messwerten vom 21.09.
Erster Baustein aus der GitHub-Recherche (`tools/autocut/docs/referenz/2026-09-19-github-recherche.md`, Punkt 1).

## Anlass

Drei Stellen in AutoCut messen oder schätzen heute, was in den Sony-Metadaten (rtmd-Datenspur von FX3 und a7 IV)
exakt steht:

| Stelle | Heute | Metadaten |
|---|---|---|
| Sichtung/Aftermovie (`_intern/skripte/ruhe.py`, `ruhe_fenster.py` der Hochzeitszauber-Charge) | Wackeln optisch per Phasenkorrelation (cv2, transcribe-venv), 4 s je Clip; ganze Clips nur einzeln auf Zuruf | Gyro (0xE43B) und Beschleunigung (0xE44B) je Frame, ohne Dekodierung |
| Stufe 2b (`index_sections.py`) | Claude Vision schätzt `brennweite` (weit/normal/tele) und `perspektive_hoehe` aus zwei Kacheln | KB-Brennweite (0x8004), Kamera-Pitch aus dem Schwerkraftvektor |
| Feinschnitt 6d (`vorlagen/feinschnitt/feinschnitt_bauen.py`) | `Stabilize()` auf jeden B-Roll-Shot (Standard seit 15.09.) | Haltung (Stativ/Gimbal/Hand) und Wackeln aus dem Gyro |

`vorlagen/feinschnitt/begradigen/lage_messen.py` parst die rtmd-Spur bereits vollständig (KLV mit lokalen Tags; Gyro,
Beschleunigung, Brennweite ist/KB, Fokus), aber nur in 1-s-Fenstern an wenigen Stellen der Interview-Clips.

Haltung im Team (User 19.09.): a7 IV meist aus der Hand mit IBIS (Active aus), FX3 meist auf dem Gimbal (DJI RS).
Auf dem Gimbal misst der Gyro die sichtbare Bewegung; bei IBIS sieht er die Handbewegung, das Bild ist glatter — der
Gyro-Wert taugt dort zur Rangfolge, die absolute Schwelle braucht einen Kamerafaktor (Kalibrierung, unten).

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Leser | Eigener rtmd-Parser (aus `lage_messen.py`) als Modul. `telemetry-parser` (PyPI 0.3.0 von 01/2024) brächte nur die Avata dazu (8 von 368 Clips bei Hochzeitszauber), keine Brennweite/Fokus — Folgeschritt, falls Drohnen-Gyro häufiger wird. Gyroflow bleibt Punkt 11 (Stabilisierung). |
| Bewegungsrichtung | `bewegungsrichtung` in 2b bleibt Motivbewegung (Claude). Die Kamera bekommt ein **neues** Feld `bewegungsart` — nicht `kamerabewegung`, denn so heißt schon das Claude-Feld des Erst-Index (statisch/Schwenk/Fahrt/Handkamera/Gimbal/Drohne/Zoom/gemischt), das unangetastet bleibt. |
| Vergleichbarkeit | Gyro-Werte werden über die KB-Brennweite in Bildpixel @480 umgerechnet — dieselbe Größe wie `jitter`/`bewegung` in `ruhe.py`. |
| Optischer Weg | Bleibt als zweiter Messweg im selben Modul (numpy statt cv2), für Clips ohne rtmd (Mavic) und als Referenz der Kalibrierung. |
| Abnehmer | Sichtung/Aftermovie, Stufe 2b, 6d — jede Anschlussstelle für sich abschaltbar. Stufe 3 (Layout) bleibt ausgesetzt. |
| Umsetzung | Plan `docs/superpowers/plans/2026-09-21-autocut-telemetrie.md` (10 Tasks, TDD, keine neue Abhängigkeit). |
| Hochzeitszauber | Die Chargen-Skripte werden nicht umgebaut; das Material dient der Kalibrierung. Der nächste Aftermovie nutzt die CLI. |
| Umgebung | AutoCut-venv (numpy/scipy), ffmpeg; ohne Resolve; NAS nur lesend. |

## Aufbau

- Modul `tools/autocut/src/niro_autocut/telemetrie.py`, CLI `tools/autocut/scripts/autocut_telemetrie.py`.
- Aufruf: `autocut_telemetrie.py "<Charge>" [--ordner <Pfad> …] [--limit N] [--force] [--ohne-optisch] [--kalibrieren]`.
- Clip-Quelle, erste vorhandene: `--ordner`-Pfade (rekursiv, Videodateien) → `_intern/autocut/broll_index.json` →
  `_intern/autocut/inventar.json` → B-Roll-Wurzeln aus dem Transkript-Index (`broll_index.discover_broll`) →
  `media.json` (Interview-Clips). Damit läuft es für AutoCut-Chargen und für den Aftermovie-Sonderfall ohne `Charge.open`.
- Ergebnis `_intern/autocut/telemetrie.json` (Liste, ein Eintrag je Clip, `path` + `clip`-Stamm), Cache je Clip
  `_intern/autocut/telemetrie/<fingerprint>.json` (Fingerprint wie im B-Roll-Index: Name, Größe, mtime; `--force` misst neu),
  Bericht `Ergebnisse/Rohschnitt/telemetrie.md`.

### Messweg 1 — rtmd

`ffmpeg -v error -i <Clip> -map 0:d:0 -c copy -f data -` liefert nur die Datenspur, liest dafür aber die ganze Datei
(gemessen 21.09.: ≈ 300 MB/s übers NAS, also die Lesezeit der Datei ohne Dekodierung; siehe Nachtrag). Parser aus `lage_messen.py`: Sample-Header
`00 1c 01 00`, KLV-Sätze (UL `060e2b34`, BER-Länge), lokale Tags:

| Tag | Inhalt |
|---|---|
| 0xE43B / 0xE439 | Gyro-Block (n Proben × int16 x/y/z) / Skala (LSB je Einheit, float) |
| 0xE44B / 0xE449 | Beschleunigung (n × int16) / Skala (LSB je g, gemessen 8192) |
| 0x8005 / 0x8004 | Brennweite ist / KB-äquivalent (RDD-18-Distanzformat) |
| 0x8001 | Fokusdistanz (RDD-18) |

Zeitachse: ein rtmd-Sample je Videoframe (t = i / fps), IMU-Unterproben gleichmäßig im Frame, Rate = n × fps.
Achsen wie in `lage_messen.py`: x links, y oben, z vorwärts → Drehung um y = Schwenk, um x = Tilt, um z = Rollen.
Vorzeichen und Gyro-Einheit werden nicht dem Datenblatt entnommen, sondern in der Kalibrierung aus dem Vergleich mit
der optischen Verschiebung bestimmt (unten).

### Messweg 2 — optisch

Phasenkorrelation aus `ruhe.py`, in numpy (`fft2`, Kreuzleistungsspektrum, Subpixel-Peak über Parabelanpassung)
statt cv2, damit sie im AutoCut-venv läuft: `ffmpeg … -vf fps=25,scale=480:270 -pix_fmt gray` über den ganzen Clip,
globale Verschiebung zwischen Nachbarframes. Einsatz: Clips ohne rtmd bzw. ohne IMU-Tags (Standard; `--ohne-optisch`
→ `quelle: keine`), Kameras aus `telemetrie.optisch_fuer`, und die Kalibrierung.

## Datenmodell (je Clip)

```
path, clip                dauer_s, fps, imu_hz, samples
quelle                    rtmd | optisch | keine
kamera                    FX3 | a7IV | DJI | unbekannt   (Dateinamen-Präfix FX3_/a7MK4_/DJI_, sonst Sony-Sidecar-XML
                          <Clip>M01.XML „modelName“, sonst unbekannt)
brennweite_mm, kb_mm, fokus_m        Median über den Clip; bei Zoomfahrt zusätzlich kb_min/kb_max, zoomfahrt: true
brennweitenklasse         weit | normal | tele            kb_mm < 30 | 30–60 | > 60
pitch_grad, roll_grad     aus dem Schwerkraftvektor (Median), nur bei |a| ≈ 1 g, sonst null mit grund
perspektive_hoehe         Vogelperspektive | Aufsicht | Untersicht | Augenhöhe   pitch ≤ −60 | ≤ −8 | ≥ +8 | sonst
haltung                   stativ | gimbal | hand
bewegungsart              statisch | schwenk_links | schwenk_rechts | tilt_auf | tilt_ab | fahrt | gemischt
wackeln, bewegung         px @480 je Frame (25 fps), wie jitter/bewegung in ruhe.py
schaerfe_p10              relative Schärfe (10. Perzentil der Frames, 1,0 = so scharf wie das schärfste Zehntel des Clips);
                          optischer Weg immer, rtmd-Weg nur mit --schaerfe (braucht Dekodierung); sonst null
fenster                   [[t_s, wackeln, bewegung, bewegungsart, schaerfe], …]   2-s-Fenster, Schritt 1 s; schaerfe = p10 im Fenster oder null
ruhige_fenster            [t_s, …]   Fenster mit wackeln ≤ ruhig_max_px (nach Kamerafaktor)
fehler                    nur wenn etwas nicht lesbar war
```

## Kennzahlen

- **Umrechnung:** `f_px = 480 · kb_mm / 36`; je 25-fps-Frame `dx = ω_schwenk · f_px / 25`, `dy = ω_tilt · f_px / 25`
  (ω in rad/s, Frame-Mittel; 50p-Quellen werden auf 25-fps-Frames zusammengefasst).
- **wackeln** = Mittel von |Δdx| und |Δdy| zwischen Nachbarframes (Änderung der Verschiebung = sichtbares Zittern);
  **bewegung** = Mittel von |dx| und |dy| (langsame Kamerabewegung). Beide Größen multipliziert mit `px_faktor[kamera]`.
- **haltung** über den Clip: Gesamt-RMS des Gyros < `stativ_max_grad_s` → `stativ`; Energieanteil über `hf_grenze_hz`
  hoch → `hand`; Bewegung vorhanden, fast nur unter der Grenze → `gimbal`. Schwellen aus drei Referenzmengen: FX3 bei
  Hochzeitszauber (Gimbal), a7 IV dort (Hand), Taxodia-Interviews (Stativ). Beim optischen Weg dieselbe Logik auf der
  Verschiebungsreihe in px (Stativ: `bewegung` und `wackeln` < 0,02 px).
- **bewegungsart** je 2-s-Fenster aus tiefpassgefiltertem ω (0,5 s): dominanter Schwenk ≥ `schwenk_min_grad_s` →
  `schwenk_links/rechts`, dominanter Tilt → `tilt_auf/ab`, RMS < `stativ_max_grad_s` → `statisch`, Bewegung ohne
  dominante Drehachse (Gimbal-Gang, Slider) → `fahrt`, Richtungswechsel im Fenster → `gemischt`. Clip-Wert = Mehrheit
  der Fenster (≥ 60 %), sonst `gemischt`. Konvention: `schwenk_links` = die Kamera dreht nach links, der Bildinhalt
  wandert nach rechts (beim optischen Weg aus dem Vorzeichen von dx, beim Gyro nach der Kalibrierung).
- **perspektive_hoehe** und **brennweitenklasse** nach den Schwellen im Datenmodell; `roll_grad` wird nur mitgeliefert
  (Warnung „schief" in 6d, keine Korrektur — das bleibt Begradigen).

### Standardwerte (`defaults.yaml`, je Charge in `config.yaml` überschreibbar)

```
telemetrie:
  fenster_s: 2.0
  schritt_s: 1.0
  ruhig_max_px: 0.15          # Startwert = optische Faustregel (18.09.: ruhige Handkamera 0,05–0,15)
  stativ_max_grad_s: 0.3
  schwenk_min_grad_s: 3.0
  hf_grenze_hz: 3.0
  brennweite_klassen_kb: [30, 60]
  pitch_klassen_grad: [-60, -8, 8]
  px_faktor: {FX3: 1.0, a7IV: 1.0}   # nach der Kalibrierung eingetragen
  optisch_fuer: []                    # Kameras, deren Gyro-Wert nicht belastbar ist (Kalibrierung)
  optisch_breite: 480
```

### Kalibrierung (einmalig, `--kalibrieren`, NAS gemountet)

Beide Messwege auf demselben Material und demselben Zeitbereich je Clip (Hochzeitszauber-Charge: 301 FX3, 59 a7 IV,
8 DJI; Fenster wie in `ruhe.py`: ab `von_s` aus `katalog.json`, 4 s). Die vorhandenen cv2-Werte in
`_intern/sichtung/ruhe.json` dienen dabei als Gegenprobe der numpy-Phasenkorrelation. Ergebnis
`_intern/autocut/telemetrie_kalibrierung.json` in der Kalibrier-Charge:

1. **Vorzeichen und Einheit:** Vorzeichen von Schwenk/Tilt und der Umrechnungsfaktor der Gyro-Einheit kommen aus dem
   Vergleich der Gyro-Verschiebung mit der optischen Verschiebungsrichtung und -größe — kein Raten am Datenblatt.
2. **Kamerafaktor:** lineare Anpassung Gyro-px ↔ optisch-px je Kamera plus Rangkorrelation (Spearman) →
   `telemetrie.px_faktor`.
3. **Sicherung:** Rangkorrelation < 0,7 → Kamera nach `telemetrie.optisch_fuer`; für sie gilt dann der optische Weg.
4. Ergebnis als Tabelle im Spec-Nachtrag und im WORKFLOW; Protokoll-Eintrag in der Kalibrier-Charge; je Kamera 2 s
   Datenspur als Test-Fixture extrahiert (≤ 200 KB).

## Abnehmer

1. **Sichtung/Aftermovie.** Im WORKFLOW-Sonderfall ersetzt `autocut_telemetrie.py "<Charge>"` den Schritt „Ruhe"
   (`ruhe.py` + `ruhe_fenster.py`). Die Schnittskripte der nächsten Aftermovie-Charge lesen `ruhige_fenster`, `wackeln`,
   `haltung`, `bewegungsart` aus `telemetrie.json`. Bericht `Ergebnisse/Rohschnitt/telemetrie.md` (Schreibbereich von
   `Charge.open_basis`, wie `broll-index.md`; Planänderung 21.09.): unruhigste Clips,
   Verteilung Haltung/Kamerabewegung/Brennweitenklasse, Clips ohne Daten.
2. **Stufe 2b** (`index_sections.py`). Liegt Telemetrie für den Clip vor: (a) der Abschnittsbogen bekommt eine
   Kontextzeile („Metadaten: KB 35 mm = normal, Pitch −12° = Aufsicht, Kamerabewegung Schwenk links, Haltung Gimbal");
   (b) nach der Antwort überschreibt der Code `brennweite` und `perspektive_hoehe` mit den Metadatenklassen und vermerkt
   `felder_quelle: {brennweite: rtmd, perspektive_hoehe: rtmd}`; (c) je Abschnitt kommen `bewegungsart` und `haltung`
   dazu (Mehrheit der Fenster im Abschnittsbereich). Ohne Telemetrie bleibt alles wie heute; das Antwortschema bleibt
   unverändert. `--dry-run` zeigt, wie viele Clips Telemetrie haben.
3. **6d** (`vorlagen/feinschnitt/feinschnitt_bauen.py`). Der Probelauf liest `telemetrie.json` und schlägt je B-Roll-Shot
   vor (`wackeln` = Mittel der Fenster im genutzten Quellbereich des Shots): `hand` und `wackeln > ruhig_max_px` →
   stabilisieren; `stativ`/`gimbal` → nicht; keine Telemetrie → stabilisieren (bisheriger Standard). Tabelle im Probelauf (Shot, Haltung, wackeln, Vorschlag), Übernahme in `feinschnitt.json`
   (`stabilisiert`, `stabil_grund`); die ANPASSEN-Tabelle `BROLL` bekommt eine optionale Spalte `stabil`, mit der Claude
   den Vorschlag überstimmt. `roll_grad` > 2° → Warnung „schief". `Stabilize()` läuft nur für die ausgewählten Shots.
   Reine Funktion `stabil_vorschlag(shot, telemetrie, cfg)` im Modul, damit sie testbar ist. Dateien mit `_stabilized` im Namen
   (Avata-Exporte, Regel des Users vom 18.09.) werden nie stabilisiert. Den Stabilisierungs-**Modus** (User-Standard Translation,
   Smooth 0,25) setzt weiterhin der DRT-Roundtrip der Chargen (`drt_stabilisierung.py`, WTN/Wurst & Liebe/Assenheimer) — die
   Vorlage entscheidet nur, ob `Stabilize()` läuft.

## Fehler

| Fall | Verhalten |
|---|---|
| Keine Datenspur oder keine IMU-Tags (Mavic, ältere Firmware) | `quelle: optisch` (Standard); mit `--ohne-optisch` → `keine` |
| Datei nicht lesbar, ffmpeg-Fehler | Eintrag mit `fehler`, Lauf geht weiter, Zusammenfassung am Ende |
| NAS nicht gemountet | `AutoCutError` mit klarer Meldung (wie `media.fingerprint`) |
| Kamera unbekannt | `px_faktor` 1,0, Hinweis im Bericht |
| Pitch bei starker Beschleunigung (|a| weit von 1 g) | `pitch_grad`/`perspektive_hoehe` null mit `grund` |
| Zoomfahrt | Klasse aus dem Median, `zoomfahrt: true`, kb_min/kb_max |
| Kamera mit Rangkorrelation < 0,7 | steht in `optisch_fuer`, optischer Weg |

## Tests (pytest, ohne NAS, ohne Resolve, ohne API-Key)

- KLV-Parser gegen synthetische rtmd-Pakete mit bekannten Werten (Header, UL, BER-Längen, alle Tags); je Kamera 2 s echte
  Datenspur als Fixture → Rate, Brennweite, Schwerkraftvektor plausibel (Fixture kommt aus dem Kalibrierlauf; bis dahin
  werden diese Tests übersprungen, wenn die Datei fehlt).
- Kennzahlen gegen synthetische ω-Verläufe: reiner Schwenk 10 °/s → `schwenk_*` und erwartete px; Rauschen über 3 Hz →
  `hand`; Null → `stativ`/`statisch`; Fensterlisten und `ruhige_fenster`.
- numpy-Phasenkorrelation gegen synthetisch verschobene Bilder (ganz- und subpixel, ±0,1 px); einmaliger Handvergleich mit
  `cv2.phaseCorrelate` im transcribe-venv, Ergebnis im WORKFLOW notiert.
- CLI auf einer Fake-Charge (`inventar.json` auf ffmpeg-`testsrc`-Clips ohne Datenspur) → `quelle: optisch`, Cache-Treffer
  im zweiten Lauf, `--force`, `--limit`.
- 2b mit gefakter Claude-Antwort: Felder überschrieben und markiert; ohne Telemetrie unverändert.
- 6d: `stabil_vorschlag` mit Tabellen-Tests (hand/gimbal/stativ, mit und ohne Telemetrie, Überstimmen per `stabil`).

## Doku

WORKFLOW-AutoCut.md: neuer Abschnitt „Telemetrie" (Aufruf, Felder, Kalibrierwerte, I/O-Messung) mit Verweisen aus
Stufe 2b, 6d und dem Aftermovie-Sonderfall; README (Stufen-Tabelle, Aufbau, Schnellstart, Arbeitsdateien);
`defaults.yaml`-Block; `vorlagen/README.md` (Spalte `stabil`); Protokoll-Eintrag in der Kalibrier-Charge.

## Nicht enthalten (Folgeschritte)

Stufe-3-Layout mit `bewegungsart`/`haltung`; Gyroflow-Vorstabilisierung (Punkt 11); Umbau von `lage_messen.py` auf das
Modul; Avata-Gyro über `telemetry-parser`; Stufe 2 (Erst-Index) mit Telemetrie-Kontext.

## Nachtrag 21.09.2026 — Messwerte an Hochzeitszauber-Clips (FX3_0330 25p, a7MK4_20260913_2128 50p)

| Punkt | Befund |
|---|---|
| Datenspur | Stream 2 „Timed Metadata Media Handler", ein Sample je Videoframe, ≈ 19,5 KB je Sample (≈ 170 Tags). Lesen = ganze Datei: 537 MB in 1,7 s, 202 MB in 0,7 s (≈ 300 MB/s NAS); Hochzeitszauber komplett ≈ 6 min. |
| IMU-Rate | Tag 0xE435 = 2000 → **2000 Hz** in beiden Kameras: 80 Gyro-/Acc-Proben je 25p-Frame, 40 je 50p-Frame (Blockheader n, groesse 6). |
| Gyro-Einheit | Skala (0xE439) = 65,5 LSB → **°/s** (±500-°/s-MEMS-Bereich). Gimbal-FX3 im Stand: RMS 0,3–0,45 °/s; a7-Hand mit Bewegung: RMS bis 9,9, Spitze 82 °/s. |
| Beschleunigung | Skala 8192 LSB/g. a7 IV Betrag 1,007 g, **FX3 konstant 1,154 g** → die 1-g-Prüfung für Pitch/Roll gilt relativ zum Clip-Median (±10 %), nicht absolut. |
| Brennweite | 0x8004 (KB) berücksichtigt den Crop: a7 IV in 4K50p (Super-35) 180 mm → 283,8 mm KB; FX3 67,7 → 71,6 mm. Fokus 0x8001 in m. |
| Sidecar | `<Clip>M01.XML` liegt neben jeder Sony-Datei: `<Device manufacturer="Sony" modelName="ILME-FX3"/>`, Objektiv als `modelName`. |
| Achsen | Stichprobe a7-Clip, Gyro je 25-fps-Frame gegen numpy-Phasenkorrelation (480×270): Gyro-y ↔ dx r = −0,91 (Schwenk: Bildinhalt wandert entgegen), Gyro-x ↔ dx r = +0,86 (im Clip korrelierte Achsen). Zeitachsen decken sich exakt (72 ↔ 72). Bei > ≈ 60 px/Frame sättigt die Phasenkorrelation → Kalibrierregression nur auf Fenstern mit |dx|,|dy| < 40 px, robust (Median-Steigung). |
| Weitere Tags | 0xE437 (int32, −3609/−3562) und 0xE43A (0x0420) neben den IMU-Blöcken — vermutlich Zeitversatz/Intervall in µs; für diese Stufe nicht nötig, im Parser mitloggen. |
| Umgebung | Homebrew hatte x265 auf 4.3 gehoben, ffmpeg 8.0.1_4 startete nicht mehr; `brew reinstall ffmpeg` installierte **ffmpeg 9.0.2** — AutoCut-Tests danach laufen lassen. |

## Nachtrag 21.09.2026 — Abgleich mit dem MacBook-Stand (Tagesstände 18./19.09.)

Auf dem zweiten Mac entstanden je Charge Skripte, die Teile dieses Specs vorwegnehmen: `broll_qualitaet.py` (Wurst & Liebe:
Schärfe und Verwacklung je B-Roll-Einsatz, optisch), `katalog_*.json` (Assenheimer: Jitter, Schärfe je Clip),
`drt_stabilisierung.py`/`translation_ads.py` (Stabilisierungs-Modus Translation per DRT-Roundtrip), `avata_entstabilisieren.py`
(Avata nur `…_stabilized.mov`, nie Resolve-Stabilizer). Daraus zwei Ergänzungen:

| Ergänzung | Entscheidung |
|---|---|
| Schärfe | `schaerfe` je Fenster und `schaerfe_p10` je Clip: mittlere quadrierte Laplace-Antwort nach Glättung (σ 1), geteilt durch die Bildvarianz (kontrastunabhängig, S-Log ist flach), relativ zum 90. Perzentil des Clips — Verfahren aus `broll_qualitaet.py`. Beim optischen Weg kostenlos, beim rtmd-Weg nur mit `--schaerfe` (Dekodierung 480×270). Keine Schwelle in dieser Stufe; der Bericht listet die unschärfsten Fenster. |
| `_stabilized` | `stabil_vorschlag` liefert für Dateien mit `_stabilized` im Namen immer „nicht stabilisieren". |
| Modus | Der Modus (Translation, Smooth 0,25) bleibt Sache des DRT-Roundtrips; Kandidat für ein eigenes gemeinsames Werkzeug (liegt in drei Chargen). |

Nicht Teil dieses Specs, aber durch den MacBook-Stand belegt: Musik als gemeinsames Werkzeug (`musik_scan.json` mit 267 Titeln,
`musik_struktur.py` mit Drops/Breaks → beat_this, all-in-one, CLAP), DRT-Stabilisierung als Modul, 9:16-Reframe-Vorschlag aus der
Gesichtslage (`pan_korrektur.py`, `gesicht_check.py`).

## Nachtrag 21.09.2026 — Kalibrierung (Hochzeitszauber, MEK)

Kalibrierlauf `autocut_telemetrie.py --kalibrieren` über Hochzeitszauber: 368 Clips, davon 355 mit Gyro und Brennweite (ohne:
6 Mavic, 2 Avata, 5 a7 IV), je Clip 4 s ab `von_s` des Sichtungs-Katalogs, Gyro und optischer Weg auf denselben Frames.

| Kamera | Clips | Frames | Schwenk (Achse, Vorzeichen, r) | Tilt (Achse, Vorzeichen, r) | px_faktor | Spearman | belastbar |
|---|---|---|---|---|---|---|---|
| FX3 | 301 | 28 553 | y, +, 0,65 | x, −, −0,83 | 0,597 | 0,76 | ja |
| a7 IV | 54 | 4 844 | y, +, 0,58 | x, −, −0,27 | 0,689 | 0,71 | ja |

| Punkt | Befund und gesetzter Wert |
|---|---|
| Achsen, Vorzeichen | Beide Kameras gleich: Schwenk um y (+), Tilt um x (−); Basis FX3 (\|r\| ≥ 0,6), die a7 IV korreliert schwächer (IBIS glättet das Bild) und bleibt mit 0,58/0,27 unter der Plan-Schwelle \|r\| ≥ 0,6 für beide Kameras; die Regel nennt für „gleiche Achse und gleiches Vorzeichen, eine Kamera schwach" keinen eigenen Zweig — übernommen, weil die Empfehlung auf der belastbaren Kamera mit den meisten Frames (FX3) beruht und die a7 IV ihr Spearman-Kriterium (≥ 0,7) erfüllt. Gesetzt `achsen: {schwenk: 1, tilt: 0}`, `vorzeichen: {schwenk: 1, tilt: -1, pitch: 1}`. Physikalisch stimmig mit x links, y oben, z vorwärts: +y = Drehung nach links → Inhalt wandert nach rechts (dx > 0); +x = Neigen nach unten → Inhalt wandert nach oben (dy < 0). Die Stichprobe im Messwerte-Nachtrag (Gyro-y ↔ dx −0,91, ein a7-Clip mit korrelierten Achsen) ist damit überholt. |
| px_faktor | FX3 0,60, a7 IV 0,69 — IBIS und Gimbal dämpfen, das Bild wackelt weniger, als der Gyro misst. `optisch_fuer` bleibt leer (beide Spearman ≥ 0,7). |
| Gegenprobe cv2 | Eingebaut gegen `ruhe.json`: n 341, r 0,748, Verhältnis 0,97 — unter der Schwelle 0,9. Ursache: `ruhe.py` rechnete `cv2.phaseCorrelate` ohne Hanning-Fenster, und 99 Clips auf kürzerem Fenster (`bis_s − von_s` < 4 s). Gleichartig nachgemessen (identische Frames, 4-s-Fenster, 355 Clips): numpy ↔ cv2 mit Hanning r 0,967, Spearman 0,979, Verhältnis 1,00 (FX3 0,955, a7 IV 0,950); numpy ↔ cv2 ohne Fenster 0,868. `telemetrie_optisch.py` ist bestätigt; das Fenster ist gewollt (ohne Fenster springt der Peak zwischen echter Verschiebung und Randeffekt). |
| `hand_hf_anteil_min` | Messlauf Hochzeitszauber, `hf_anteil` ohne Stativ: FX3-Gimbal (290 Clips) P10/25/50/75/90 = 0,009/0,018/0,046/0,107/0,175, a7-IV-Hand (54) = 0,152/0,191/0,281/0,377/0,507. Keine Überlappung von P75 und P25 → Mitte 0,149 → **0,15** (vorher 0,35: 36 von 59 a7-IV-Clips galten als gimbal). Im Schlusslauf mit 0,15 gelten 43 von 290 FX3-Clips als hand und 6 von 58 a7-IV-Clips als gimbal. |
| Schlusslauf Hochzeitszauber | `--force --schaerfe` mit allen Endwerten: 368 Clips (355 rtmd, 13 optisch, 0 Fehler), Schärfe für alle. Haltung FX3 gimbal 247 / hand 43 / stativ 11, a7 IV hand 52 / gimbal 6 / stativ 1, DJI gimbal 8 — FX3 überwiegend gimbal, a7 IV überwiegend hand. Bericht `Ergebnisse/Rohschnitt/telemetrie.md`. |
| MEK: Perspektive Höhe | 463 B-Roll-Clips (453 rtmd, 10 optisch) gegen den Stufe-2b-Index: 765 von 1000 Abschnitten gleich (76 %); Aufsicht ↔ Untersicht vertauscht nur 7 → Pitch-Vorzeichen +1 und Grenzen −60/−8/8 bleiben. |
| MEK: Brennweite | 483 von 1017 gleich (47 %); `brennweite_klassen_kb` [30, 60] und [35, 70] beide 47 % → bleibt [30, 60]. Claude nennt KB-Brennweiten bis etwa 75 mm „normal" (Median der normal-Abschnitte 73,6 mm, P90 139,8); ein an Claude angelehntes Raster [30, 85] käme auf 62 %. 157 von 463 Clips haben eine Zoomfahrt (`kb_max/kb_min` > 1,3; Zoom, a7-IV-Crop und Klarbild-Zoom), 447 der 1017 Abschnitte liegen darin — die Clip-Klasse (Median) passt dort nicht auf jeden Abschnitt (ohne Zoomfahrt 49 %, mit 45 %). |
| MEK: Haltung | 136 von 463 gleich (29 %): hand ↔ Handkamera 72, gimbal ↔ Gimbal 46, gimbal ↔ Handkamera 127. Verteilung FX3 gimbal 175 / hand 84 / stativ 19, a7 IV hand 116 / gimbal 69. Nur Doku, Schwelle bleibt. |
| Fixtures | `tests/fixtures/rtmd_fx3_25p.bin` (FX3_0330, 0,3 s, 156 KB), `rtmd_a7iv_50p.bin` (a7MK4_20260913_2128, 0,3 s, 292 KB); `test_rtmd.py` ohne Skips. |

Offen (Entscheidung User): (1) Brennweitengrenzen — Filmkonvention (tele ab 60 mm KB) oder an Claudes Wahrnehmung angelehnt
([30, 85]); (2) Zoomfahrten — Stufe 2b überschreibt `brennweite` je Abschnitt mit der Clip-Klasse; bei Zoomfahrten besser die
KB-Reihe je Abschnitt auswerten oder dort Claudes Wert behalten.
