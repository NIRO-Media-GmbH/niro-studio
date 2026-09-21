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
| Bewegungsrichtung | `bewegungsrichtung` in 2b bleibt Motivbewegung (Claude). Die Kamera bekommt ein **neues** Feld `kamerabewegung`. |
| Vergleichbarkeit | Gyro-Werte werden über die KB-Brennweite in Bildpixel @480 umgerechnet — dieselbe Größe wie `jitter`/`bewegung` in `ruhe.py`. |
| Optischer Weg | Bleibt als zweiter Messweg im selben Modul (numpy statt cv2), für Clips ohne rtmd (Mavic) und als Referenz der Kalibrierung. |
| Abnehmer | Sichtung/Aftermovie, Stufe 2b, 6d — jede Anschlussstelle für sich abschaltbar. Stufe 3 (Layout) bleibt ausgesetzt. |
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
  Bericht `Ergebnisse/Sortierung/telemetrie.md`.

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
kamerabewegung            statisch | schwenk_links | schwenk_rechts | tilt_auf | tilt_ab | fahrt | gemischt
wackeln, bewegung         px @480 je Frame (25 fps), wie jitter/bewegung in ruhe.py
fenster                   [[t_s, wackeln, bewegung, kamerabewegung], …]   2-s-Fenster, Schritt 1 s
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
- **kamerabewegung** je 2-s-Fenster aus tiefpassgefiltertem ω (0,5 s): dominanter Schwenk ≥ `schwenk_min_grad_s` →
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
   `haltung`, `kamerabewegung` aus `telemetrie.json`. Bericht `Ergebnisse/Sortierung/telemetrie.md`: unruhigste Clips,
   Verteilung Haltung/Kamerabewegung/Brennweitenklasse, Clips ohne Daten.
2. **Stufe 2b** (`index_sections.py`). Liegt Telemetrie für den Clip vor: (a) der Abschnittsbogen bekommt eine
   Kontextzeile („Metadaten: KB 35 mm = normal, Pitch −12° = Aufsicht, Kamerabewegung Schwenk links, Haltung Gimbal");
   (b) nach der Antwort überschreibt der Code `brennweite` und `perspektive_hoehe` mit den Metadatenklassen und vermerkt
   `felder_quelle: {brennweite: rtmd, perspektive_hoehe: rtmd}`; (c) je Abschnitt kommen `kamerabewegung` und `haltung`
   dazu (Mehrheit der Fenster im Abschnittsbereich). Ohne Telemetrie bleibt alles wie heute; das Antwortschema bleibt
   unverändert. `--dry-run` zeigt, wie viele Clips Telemetrie haben.
3. **6d** (`vorlagen/feinschnitt/feinschnitt_bauen.py`). Der Probelauf liest `telemetrie.json` und schlägt je B-Roll-Shot
   vor (`wackeln` = Mittel der Fenster im genutzten Quellbereich des Shots): `hand` und `wackeln > ruhig_max_px` →
   stabilisieren; `stativ`/`gimbal` → nicht; keine Telemetrie → stabilisieren (bisheriger Standard). Tabelle im Probelauf (Shot, Haltung, wackeln, Vorschlag), Übernahme in `feinschnitt.json`
   (`stabilisiert`, `stabil_grund`); die ANPASSEN-Tabelle `BROLL` bekommt eine optionale Spalte `stabil`, mit der Claude
   den Vorschlag überstimmt. `roll_grad` > 2° → Warnung „schief". `Stabilize()` läuft nur für die ausgewählten Shots.
   Reine Funktion `stabil_vorschlag(shot, telemetrie, cfg)` im Modul, damit sie testbar ist.

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

Stufe-3-Layout mit `kamerabewegung`/`haltung`; Gyroflow-Vorstabilisierung (Punkt 11); Umbau von `lage_messen.py` auf das
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
