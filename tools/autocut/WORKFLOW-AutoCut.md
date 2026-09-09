# WORKFLOW: AutoCut (Schnittplan → Rohschnitt-Timeline in DaVinci Resolve)

Trigger: **„AutoCut: <Kunde>/<Projekt>[/<Charge>]"** plus Unterbefehl — aus einem fertigen
Cutter-Schnittplan (`Ergebnisse/O-Ton-Pläne/video-N-*.md`) entsteht eine **roh-Timeline** im
offenen Resolve-Projekt: alle O-Töne in Planreihenfolge, beide Kameras synchron (V2 = a7IV nur
Bild, kein A2 mehr), Pausen, Platzhalter für VO/Bild/Grafik, Marker. Danach werden alle B-Roll-Clips
des Drehs per Claude-Vision beschrieben (Stufe 2), je Abschnitt genauer bestimmt (Stufe 2b,
Nachlauf) und V3 nach Plan v2 (Fenster/Strecken/Szenen/Shots) in die roh-Timeline gefüllt
(Stufe 3). Zuletzt macht **Finalisieren** (Stufe 5) daraus die fertige End-Timeline: Pegel je
FX3-Clip, Zeitlupen, Marker, Spurnamen — ohne „(roh)"-Suffix.
(Abgrenzung: „Schnittplan:" **erzeugt** den Plan in `tools/transcribe/WORKFLOW-Schnittplan.md`;
AutoCut **liest** ihn nur. Musik, VO-Stimme, Multicam-Objekte, Grading, Untertitel sind nicht Teil
von Stufe 1–5.) Spec: `docs/superpowers/specs/2026-09-03-autocut-design.md` (v2 B-Roll-Layout, Review-Fix-Welle:
`docs/superpowers/specs/2026-09-04-autocut-v2-design.md`), Pläne: `docs/superpowers/plans/2026-09-03-autocut.md`,
`docs/superpowers/plans/2026-09-04-autocut-profil.md`, `docs/superpowers/plans/2026-09-04-autocut-v2.md`.
Erst-Referenz: MEK Imagefilm (`projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/`).

| Unterbefehl | Stufe | Ergebnis |
|---|---|---|
| „Rohschnitt" | 1 | roh-Timeline V1/V2/A1 (V3 leer) mit O-Tönen, Pausen, Platzhaltern, Markern + Bericht |
| „B-Roll-Index" | 2 | `broll_index.json` + `broll-index.md`: Beschreibung aller B-Roll-Clips |
| „Nachlauf" | 2b | Abschnittsfelder je Clip |
| „B-Roll" | 3 | V3 in der roh-Timeline gefüllt nach Plan v2 (Fenster/Strecken/Szenen/Shots), Index und Profil + Bericht |
| „Profil" | 4 | Schnitt-Profil aus den Cloud-Timelines des Users (eigener Plan, Abschnitt unten) |
| „Finalisieren" | 5 | End-Timeline mit Pegel/Zeitlupe |

Ohne Unterbefehl gilt „Rohschnitt". Bei nur einer Charge reicht Kunde/Projekt.

## Pfade (absolut; zsh: alles in Anführungszeichen, Flags ausschreiben, keine `$VAR`-Flaglisten)

    TOOL="/Users/jansantos/NIRO Studio/tools/autocut"
    PY="$TOOL/venv/bin/python"
    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"

Alle Skripte: `"$PY" "$TOOL/scripts/<skript>.py" "$CHARGE" [Flags]`. Jedes Skript druckt eine
Zusammenfassung; Exit ≠ 0 heißt Abbruch mit deutscher Meldung (Ursache + Abhilfe steht im Text).

## Voraussetzungen (vor jedem Lauf prüfen)

- **Charge fertig aus dem Schnittplan-Workflow:** `Ergebnisse/O-Ton-Pläne/video-N-*.md` (Cutter-
  Kompaktfassung mit Ablauf-Tabelle, Ziellänge, `**Verboten:**`), `_intern/utterances.json`,
  `_intern/transcripts_index.json` (Felder `path`, `person`, `kamera_rolle` ton|kontext,
  `fingerprint`, `kategorie`), `_intern/cache/<fingerprint>.scribe.json` (Wort-Zeitstempel).
  Fehlt `kamera_rolle`, gilt FX3 = ton, a7MK4 = kontext. Mehrere `video-*.md` → `--video` angeben.
- **NAS gemountet** (`/Volumes/NIRO NAS/...`, die `path`-Einträge des Index) mit den Resolve-Proxies
  `<Clip-Ordner>/Proxy/<stem>.mov` (1920×1080) für jeden Interview- und B-Roll-Clip.
  Liegt das Material inzwischen unter einem anderen Präfix (SSD statt NAS), `path_map` in
  `<Charge>/_intern/autocut/config.yaml` setzen (`"<alter Präfix>": "<neuer Präfix>"`) — die Arbeitsdateien bleiben
  unverändert, AutoCut ordnet nur beim Zugriff zu (Media Pool, Proxy, Pegelmessung).
- **DaVinci Resolve Studio 21.1 läuft**, das Zielprojekt ist geöffnet, Einstellungen → System → General →
  „External scripting using" = **Local**. Nur für Bau-Schritte (build, place, export, probe,
  probe_xml, finalize, read).
- **Probe der 21.1-API** einmal je Resolve-Umgebung:
  `resolve_probe_api.py "$CHARGE" --project "<offenes Projekt>"` → `probe_api.json` (Semantik von SetSpeed,
  AudioVolume, Normalize, AutoAlign; Grundlage für AutoCut v3). `--project` ist die Freigabe des Users und muss
  exakt dem geöffneten Projekt entsprechen.
- **`tools/autocut/.env`** mit `ANTHROPIC_API_KEY` (Stufe 2 und 2b; `scripts/setup_env.py`, siehe `SETUP.md`).
- Einrichtung (venv, `.pth` auf `tools/transcribe/src`, ffmpeg 8): `SETUP.md`. Test: `venv/bin/python -m pytest -q`.

## Eiserne Regeln

- **NAS nur lesen.** Kein Skript schreibt unter `/Volumes/`. Originale und Proxies bleiben unangetastet.
- **Schreibbereiche** (im Code über `Charge.assert_writable` erzwungen): nur `<Charge>/_intern/autocut/**`,
  `<Charge>/Ergebnisse/Rohschnitt/**` und `Protokoll.md` (anhängen). Nichts unter `Material/`,
  `O-Ton-Pläne/` oder in anderen Tools.
- **Resolve — nur anhängen, fast nie löschen:** neue Bin-, Timeline- und Media-Pool-Einträge anlegen,
  bestehende Timelines nie verändern. Löschen ist nur in zwei Fällen erlaubt: die **eigene
  roh-Timeline desselben Laufs** beim Finalisieren (Name muss exakt mit dem aus `build.json`
  übereinstimmen — sonst verweigert der Code das Löschen) und die **selbst angelegten
  Probe-Objekte** (`resolve_probe.py`, `resolve_probe_xml.py`; je mit `--keep` erhaltbar). Jede
  andere Timeline im Projekt bleibt unangetastet. Cloud-Projekte speichern sofort (Live Save) —
  deshalb keine Experimente an fremden Timelines.
- **Spurlayout ohne A2 (Spec v2):** V1 FX3 (Bild + Ton), V2 a7IV nur Bild (kein Ton, kein
  A2-Track mehr), V3 B-Roll (nur Bild), A1 FX3 Ton — jede AutoCut-Timeline hat 3 Videospuren und
  1 Audiospur.
- **User-Timeline wiederherstellen:** jeder Resolve-Lauf merkt sich beim Verbinden die gerade
  offene Timeline des Users und aktiviert sie am Ende wieder — auch wenn der Lauf mit einem Fehler
  abbricht. Der User kann also parallel in Resolve weiterarbeiten; kein AutoCut-Lauf hinterlässt
  eine andere Timeline im Vordergrund, als der User sie vorgefunden hat.
- **Prüfen vor Bauen:** `autocut_build.py` verweigert ohne `verify.json` mit `ok: true` oder wenn der
  Hash der `cutlist.json` nicht mehr zu `verify.json` passt. Jede Änderung an `cutlist.json` →
  `autocut_verify.py` erneut.
- **Claude entscheidet, Code prüft hart:** Cutlist und B-Roll-Layout schreibt Claude in der Session
  nach `prompts/cutlist.md` bzw. `prompts/place-broll.md`; Zeiten kommen immer aus
  `autocut_find_quote.py`/dem Cache, nie aus dem Plan abgeschrieben, nie erfunden. Sperren werden nie
  verkleinert. Nur FX3-Clips (`kamera_rolle: ton`) als Quelle; die a7IV kommt über `sync.json` auf V2.
- **Format bestimmt das Material**, nicht der Plan (Rotations-Flag der FX3-Datei → 9:16, sonst 16:9;
  Bildrate aus der Datei). Abweichung vom Plan wird gemeldet, nicht „korrigiert".
- **Kosten-Schutz Stufe 2 und 2b:** vor jedem Index-Lauf und jedem Nachlauf Clipzahl + Schätzung
  lesen, erst `--limit 5`.
- **Protokoll-Pflicht** der Charge: jeder Bau-, Index-, Nachlauf-, Place- und Finalisieren-Lauf hängt
  selbst einen Eintrag an `Protokoll.md`; am Session-Ende zusätzlich der Session-Eintrag (was
  gemacht, geliefert, offen).
- Meldungen an den User auf Deutsch, präzise, mit absolutem Dateipfad und Zahlen (Beats, Paare, Warnungen).

## Ablauf Stufe 1 — „Rohschnitt"

1. **Vorbereiten** — `autocut_prepare.py "$CHARGE" [--video video-1-x.md] [--check-resolve]`
   → `_intern/autocut/media.json`. Prüft jeden Interview-Clip (Original + Proxy per ffprobe: Bildrate,
   Frame-Zahl ±1, Rotation), bestimmt das Timeline-Format aus der ersten FX3-Datei und gruppiert je
   Interview-Ordner die Kamerapaare (`ton`/`kontext`). Ausgabe lesen: Format (MEK: 25 fps, 3840×2160,
   16:9), Ordnerliste, Clips ohne Proxy. Abbruch bei fehlender Datei (NAS?), Proxy ≠ Original, Mischformat.
2. **Sync** — `autocut_sync.py "$CHARGE" [--ordner "<Interview-Ordner>" ...]`
   → `_intern/autocut/sync.json`. Extrahiert 16-kHz-Mono-WAVs der **Originale** nach
   `_intern/autocut/work/audio/` (Cache per Fingerprint) und rechnet je FX3×a7-Paar die
   Kreuzkorrelation (Onset-Hüllkurven). Tabelle lesen: Frames, Konfidenz, Drift, ok/Hinweis.
   Konvention: `a7_zeit = fx3_zeit + offset_s`. Kontrolle MEK: Johanna_Notaufnahme 48–49 Frames.
   Exit 1 = ein Ordner mit Paaren ohne ok-Paar (V2 bleibt dort leer, der Bericht sagt es) — kein Abbruch.
   `--ordner` rechnet nur diese Ordner neu, der Rest bleibt.
3. **Cutlist** — Claude in der Session nach **`prompts/cutlist.md`** (dort steht alles: Entwurf per
   `autocut_cutlist_draft.py`, jedes Zitat per `autocut_find_quote.py --clip <Stem> --text "…" --near mm:ss`
   auflösen, In/Out-Hinweise, Sperren aus `**Verboten:**`, Pausen, Kopf aus `media.json`)
   → `_intern/autocut/cutlist.json`. Kein Beat wird weggelassen; VO/Bild/Grafik werden Platzhalter
   mit der Plan-Schätzung „~x s".
4. **Prüfen** — `autocut_verify.py "$CHARGE"` → `_intern/autocut/verify.json` (Hash, ok, errors,
   warnings, Gesamtlänge). Exit 0 nötig; Warnungen (Plan-Schätzung, Ziellänge, fehlende a7-Abdeckung)
   lesen und dem User nennen. Fehler nach der Tabelle in `prompts/cutlist.md` beheben, erneut prüfen.
5. **Bauen** — beim ersten Lauf in einer Resolve-Umgebung einmal `resolve_probe.py "$CHARGE"`
   (legt „AutoCut PROBE <Uhrzeit>" an, misst `endFrame`-Semantik und Record-Positionen, löscht nur
   diese Probe wieder, schreibt `_intern/autocut/probe.json`; Ergebnis lesen). Dann
   `autocut_build.py "$CHARGE"`: Bin `AutoCut/<Video>`, Media Pool per Dateipfad dedupliziert, Proxies
   verknüpft, **roh-Timeline „AutoCut <Video> <JJJJ-MM-TT HHMM> (roh)"** (Spuren V1 „FX3", V2 „a7IV"
   — nur Bild, kein A2 mehr —, V3 „B-Roll" — leer, wird erst in Stufe 3 gefüllt —, A1 „FX3 Ton"),
   Marker je Beat (Blau O-Ton, Gelb VO, Grün Bild, Lila Grafik, Rot „V2 fehlt"). Schreibt
   `timeline.json`, `build.json`, den Bericht `Ergebnisse/Rohschnitt/<video>-rohschnitt.md` und den
   Protokoll-Eintrag. Bricht ein API-Schritt ab, heißt die angefangene Timeline „… FEHLER" und bleibt
   stehen (nichts wird automatisch gelöscht). Die roh-Timeline ist ein Zwischenstand ohne
   Pegel/Zeitlupe — **Finalisieren** (Stufe 5, Abschnitt unten) macht daraus nach Stufe 2/2b/3 die
   End-Timeline ohne „(roh)"-Suffix.
6. **Optional Export** — `autocut_export_xml.py "$CHARGE" [--otio]` → FCP7-XML der zuletzt gebauten
   Timeline nach `Ergebnisse/Rohschnitt/<Timeline>.xml` (Premiere-Probecutter).
7. **Abnahme** — Bericht lesen, in Resolve die roh-Timeline öffnen (Länge ≈ Ziellänge? V2 dort leer,
   wo Sync fehlt? V3 noch leer?), dem User melden: Timeline-Name (mit „(roh)"), Beats
   (O-Töne/Platzhalter), Gesamtlänge gegen Ziellänge, Sync-Paare ok/nicht ok, alle Warnungen, offene
   Punkte.

## Ablauf Stufe 2 — „B-Roll-Index"

1. **Umfang und Kosten** — `autocut_index_broll.py "$CHARGE" --dry-run [--extra "<Pfad>" ...]`: findet
   alle Clips unter `…/Sortiert/B-Roll/**` beider Standorte (aus den Interview-Pfaden des Index abgeleitet),
   meldet Clipzahl, Cache-Stand und Kostenschätzung. `--extra` ergänzt Wurzeln (Mavic, Actioncam).
   Zahl und Schätzung dem User nennen, bevor Geld ausgegeben wird (MEK, 464 Clips: grob 25–50 € mit Opus 5).
2. **Testlauf** — `autocut_index_broll.py "$CHARGE" --limit 5`: fünf Clips (Proxy → Szenenwechsel →
   Frames → Kontaktbögen 4×3 → Claude mit Structured Output, Modell `index.model` aus `defaults.yaml`).
   `Ergebnisse/Rohschnitt/broll-index.md` lesen: stimmen Beschreibung, Einstellung, Mängel, Abschnitte?
   Bei Bedarf `prompts/index-clip.md` schärfen und die Testclips mit `--force` neu anfragen. Ein Testlauf
   ergänzt einen vorhandenen `broll_index.json` (alle anderen Clips bleiben erhalten), er ersetzt ihn nicht.
3. **Volllauf** — `autocut_index_broll.py "$CHARGE" --parallel 4`. Jeder Clip landet im Cache
   `_intern/autocut/broll_index/<fingerprint>.json`; Ctrl-C bricht ab, der nächste Lauf setzt am Cache
   fort. Ergebnis `_intern/autocut/broll_index.json` + `broll-index.md` + Protokoll-Eintrag.
   Exit 1 = einzelne Clips fehlgeschlagen (Index trotzdem geschrieben; Fehlerliste lesen, Lauf wiederholen).

## Ablauf Stufe 2b — „Nachlauf" (Pflicht vor Stufe 3 v2)

1. **Umfang und Kosten** — `autocut_index_sections.py "$CHARGE" --dry-run`: Clipzahl, Cache-Stand,
   Kostenschätzung (Abschnittsbögen aus dem Frame-Cache, keine neue Extraktion). Zahl und Schätzung
   dem User nennen.
2. **Testlauf** — `autocut_index_sections.py "$CHARGE" --limit 5`: Ergebnis in `broll_index.json`
   (Felder `einstellung`, `perspektive_hoehe`, `perspektive_ansicht`, `brennweite`, `bewegungsrichtung`,
   `hauptmotiv`, `setup_hash` je Abschnitt) stichprobenhaft gegen den Abschnittsbogen prüfen.
3. **Volllauf** — `autocut_index_sections.py "$CHARGE" --parallel 4`. Schema-Verstöße der Modellantwort
   (falsche Zahl der Einträge, abweichende Schreibweise) gleicht der Code an bzw. fragt genau einmal mit
   Fehlerliste nach; der Protokoll-Eintrag nennt die Zahl der Nachfragen. Exit 1 = einzelne Clips
   fehlgeschlagen (Lauf wiederholen; Cache hält Fertiges).

## Ablauf Stufe 3 — „B-Roll" (v2)

Voraussetzung: Stufe 1 gebaut (`timeline.json`, `build.json`), Stufe 2 vollständig (`broll_index.json`)
und Stufe 2b gelaufen (Abschnittsfelder je Clip in `broll_index.json`).

1. **Kompakter Index** — `autocut_place_broll.py "$CHARGE" --compact` → `broll_index_kompakt.json`.
2. **Raster** — `autocut_place_broll.py "$CHARGE" --raster` → `raster.json` + `<video>-raster.md`:
   Sprecher-Fenster, Strecken, Gesichtsanteil. Nach jeder Fenster-Änderung im Plan wiederholen.
3. **Plan v2** — Claude in der Session nach **`prompts/place-broll.md`**: Strecken → Szenen → Shots,
   `tempo` → `_intern/autocut/broll_plan.json` (Version 2: `fenster`/`strecken`/`szenen`/`shots`). Vor einem Plan
   mit `tempo > 1` muss `resolve_probe_xml.py "$CHARGE"` einmal in dieser Resolve-Umgebung gelaufen sein
   (`probe_xml.json` mit `speed_import_ok`) — sonst ist der Zeitlupen-Import dort nicht belegt (Stufe 5).
4. **Prüfen** — `autocut_place_broll.py "$CHARGE" --verify-only` → `broll_verify.json`. Fehler beheben
   (Tabelle in `prompts/place-broll.md`), erneut prüfen.
5. **Dem User vorlegen** — Gesichtsanteil, Zahl der Strecken/Szenen/Shots/Zeitlupen, Ausnahmen und
   Abweichungen mit Grund, offene Motive. Erst nach Freigabe bauen.
6. **Bauen** — `autocut_place_broll.py "$CHARGE"`: V3 in die roh-Timeline (Bin `AutoCut/<Video>/B-Roll`,
   nur Bild, kein Ton), Cyan-Marker je Szene, gelbe Marker je Abweichung. Schreibt `broll_build.json`,
   Bericht `Ergebnisse/Rohschnitt/<video>-broll.md`, Protokoll-Eintrag.
7. **Finalisieren** — Stufe 5 (Abschnitt unten): Pegel, Zeitlupen, End-Timeline.

## Stufe 4 — „Profil" (eigener Plan: `docs/superpowers/plans/2026-09-04-autocut-profil.md`, Spec Abschnitt 8)

Noch nicht gebaut; Grundlage ist `autocut_read_timelines.py "<Ausgabe.json>"` (liest alle Timelines des
offenen Projekts mit Items, Source-Frames und Markern; schreibt nur unter `tools/autocut/profile/` oder in
eine Charge). Geplant: Cloud-Projekte per `LoadCloudProject` lesen, als OTIO/XML in
`tools/autocut/profile/archiv/` sichern, Kennzahlen je Videotyp (Sprecher-Fenster, B-Roll-Längen,
Gesichtsanteil, Pausen), Regeln als `profile/<typ>.md` + `.yaml` (überschreibt `defaults.yaml`),
Korrektur-Schleife über die vom User korrigierte Timeline. Bis dahin gilt `profile/default.*`.

## Ablauf Stufe 5 — „Finalisieren"

Voraussetzung: `probe_xml.json` mit `level_import_ok` (einmal je Resolve-Umgebung: `resolve_probe_xml.py "$CHARGE"`;
braucht media.json + broll_index.json; legt eigene Probe-Objekte an und löscht sie). Dann
`autocut_finalize.py "$CHARGE" [--keep-roh]`: misst je A1-Clip den True Peak (ffmpeg), exportiert die roh-Timeline als
FCP7-XML, setzt Pegel (Ziel −3 dBTP) und Zeitlupen (Time Remap), importiert die End-Timeline „AutoCut <Video> <Datum>",
prüft per Readback und Re-Export, setzt Spurnamen, Marker, Clip-Farbe Teal für Zeitlupen, löscht die roh-Timeline
(außer mit `--keep-roh`). In der roh-Timeline liegt unter jedem Zeitlupen-Shot (`tempo > 1`) planmäßig eine Lücke
(V3-Items enden dort bei `roh_out_f`, vor dem echten Konformieren) — das ist kein Fehler, erst das Finalisieren
schließt sie beim Bau der End-Timeline. Bericht: Pegel-Tabelle im Rohschnitt-Bericht, `finalize.json`. Exit 0 = fertig, 1 = Fehler
(End-Timeline „… FEHLER", roh bleibt stehen), 2 = Vorbedingung fehlt (erst `autocut_build.py` bzw. `resolve_probe_xml.py`).
Abnahme: End-Timeline in Resolve öffnen (A1-Pegel im Inspector, V3 lückenlos, Zeitlupen-Clips teal), Gesichtsanteil im
B-Roll-Bericht, keine Schwarzframes.

## Fehlerbilder und Abhilfe

| Meldung / Bild | Abhilfe |
|---|---|
| `Keine Charge gefunden … Ergebnisse/O-Ton-Pläne` | Pfad prüfen; erst den Schnittplan-Workflow ausführen |
| `utterances.json fehlt` | `tools/transcribe/venv/bin/python tools/transcribe/scripts/build_utterances.py "<Charge>"` |
| `Mehrere Pläne vorhanden, bitte mit --video wählen` | `--video video-1-x.md` an prepare/draft geben |
| `Datei nicht gefunden … Ist das NAS gemountet?` | NAS im Finder mounten, Pfad aus dem Index prüfen, oder `path_map` in der Chargen-config.yaml setzen |
| prepare-Warnung `kein Proxy unter …/Proxy — Resolve nutzt das Original` bzw. verify-Fehler `kein Proxy für …` / `Frames weichen ab: Original … / Proxy …` | Proxy in Resolve neu erzeugen (`<Ordner>/Proxy/<stem>.mov`); nie das Original anfassen |
| `Mischformate im Interview-Material, media.json nicht geschrieben` (fps/Hochformat/Auflösung der Ton-Clips uneinheitlich) | Clips prüfen; Cutlist nur aus einem Format, Rest im Bericht |
| Sync-Zeile `ok=False` (Konfidenz unter 4 / keine Überlappung / Prüffenster uneinig) | Paar bleibt ohne V2; Kamera-Zuordnung im Index prüfen (`kamera_rolle`), ggf. `--ordner` neu rechnen; Rückfall: Resolve-Auto-Sync von Hand |
| `verify.json fehlt` / `Cutlist wurde nach der Prüfung geändert` | `autocut_verify.py` laufen lassen (Hash muss passen) |
| `Text stimmt nicht mit dem Transkript … Dort steht: „…"` | `text` an den Transkript-Wortlaut angleichen oder Intervall neu auflösen (`autocut_find_quote.py`) |
| `überschneidet … Sperre` | anderen Take, kürzeren Cut oder harte Kante — Sperre bleibt |
| `Resolve-Scripting-Modul nicht ladbar` / `Resolve ist nicht erreichbar` | Resolve Studio starten, Projekt öffnen, External Scripting = Local; Pfade in `SETUP.md` |
| Probe: `Offen ist das Projekt '…', freigegeben wurde '…'` (Exit 2) | Das freigegebene Projekt in Resolve öffnen oder `--project` auf den exakten Namen setzen; ohne Übereinstimmung ändert die Probe nichts |
| `In Resolve ist kein Projekt geöffnet` | Zielprojekt öffnen (Cloud-Projekt: erst laden) |
| `Timeline '…' existiert bereits` | Name enthält Datum + Uhrzeit — eine Minute warten oder alte Timeline umbenennen (nicht löschen lassen) |
| `AppendToTimeline fehlgeschlagen …` / Readback-Abweichung Soll/Ist | `resolve_probe.py` laufen lassen (`probe.json` liefert die endFrame-Semantik), Proxy-Link prüfen; Timeline „… FEHLER" im Bericht nennen |
| Timeline im falschen Format (z. B. Hochkant) | Rotations-Flag der FX3-Datei war gesetzt — Material gilt; Plan-Abweichung im Bericht |
| `ANTHROPIC_API_KEY fehlt — in … .env eintragen` / `Kein Anthropic-Key im Schlüsselbund` / 401 | `scripts/setup_env.py` (Schlüsselbund `niro_autocut`) oder Key von Hand in `.env` |
| Index: `Claude-Anfrage … fehlgeschlagen` (Ratelimit/Netz) | Lauf wiederholen — Cache hält Fertiges; `--parallel 2` |
| Index-Beschreibungen ungenau | `prompts/index-clip.md` schärfen, `--limit 5 --force`, dann Volllauf |
| Place (Stufe 3 v2): `Gesichtsanteil … außerhalb` / `zu kurz`/`zu lang` / `ragt über das Streckenende` / `verwendbar` | `broll_plan.json`/Fenster anpassen (Tabelle in `prompts/place-broll.md`), `--verify-only` erneut |
| `Strecke … fehlt im Plan` / `ist leer` | jede Raster-Strecke aus `raster.json` mit Szenen füllen — Schwarz ist verboten |
| `Abschnittsfelder fehlen` | `autocut_index_sections.py "$CHARGE"` laufen lassen (Stufe 2b, Nachlauf) |
| Nachlauf: `Antwort verletzt das Schema (auch nach 1 Nachfrage)` | Lauf wiederholen (Cache hält Fertiges); bleibt der Clip hängen, Abschnittsbogen unter `work/sheets/<stem>…_A.jpg` ansehen und `prompts/index-sections.md` schärfen |
| `level_import_ok=false` in `probe_xml.json` | Pegel-Import in dieser Resolve-Umgebung nicht belegt — `resolve_probe_xml.py` wiederholen; bleibt es dabei, Rückfall auf separate WAVs statt XML-Gain (eigener Task) |
| `speed_import_ok=false` in `probe_xml.json` | Zeitlupen-Import nicht belegt — `tempo` aus dem B-Roll-Plan nehmen (nur `tempo: 1`) oder Rückfall am Duplikat einrichten |
| `End-Timeline weicht ab` (Readback/Re-Export in `autocut_finalize.py`) | roh-Timeline bleibt stehen, End-Timeline heißt „… FEHLER"; XML unter `work/xml/<Timeline>.*.xml` prüfen |

## Ausgabe-Konvention

    <Charge>/_intern/autocut/            Arbeitsdateien (überschreibbar, im Bericht referenziert)
    ├── config.yaml                      optional: Überschreibungen von tools/autocut/defaults.yaml, `path_map`
    ├── media.json · sync.json           Stufe 1: Medien/Format, Kamerapaare
    ├── cutlist.json · verify.json       Stufe 1: Claude-Cutlist, Prüfergebnis mit Hash
    ├── probe.json                       Resolve-Probe (endFrame-Semantik, Positionen)
    ├── timeline.json · build.json       Stufe 1: gesetzte Items (rel. Frames), roh-Timeline-Name, Startframe
    ├── broll_index.json · broll_index/  Stufe 2 + 2b: Index gesamt (inkl. Abschnittsfelder) + Cache je Clip (Fingerprint)
    ├── broll_index_kompakt.json         Stufe 3: kompakter Index für die Session (`--compact`)
    ├── raster.json                      Stufe 3: Sprecher-Fenster, Strecken, Gesichtsanteil (`--raster`)
    ├── broll_plan.json · broll_build.json   Stufe 3: Zuordnung (v2: fenster/strecken/szenen/shots), Bau-Ergebnis
    ├── probe_xml.json                   Resolve-Probe des XML-Roundtrips (Pegel-/Zeitlupen-Import, Marker, FPS,
    │                                    Spurnamen setzbar auf Import-/aktuellem Handle)
    ├── probe_api.json                   Resolve-Probe der 21.1-API (AudioVolume, Normalize, SetSpeed-Semantik, Fades,
    │                                    Transition, AutoAlign, QuickExport, Alpha-Import); Medien in work/probe_api/
    ├── ton.json · finalize.json         Stufe 5: True-Peak/Gain je A1-Clip, Finalisieren-Ergebnis (End-Timeline)
    └── work/audio · work/frames · work/sheets · work/ton_cache.json · work/xml/
                                         Caches (WAVs, Einzelbilder, Kontaktbögen, Pegel-Messungen) und der
                                         XML-Roundtrip beim Finalisieren (`<Timeline>.roh/.final/.reexport.xml`)
    <Charge>/Ergebnisse/Rohschnitt/      Berichte + Export (für David lesbar)
    ├── <video>-rohschnitt.md            Beat-Tabelle (Nr, Szene, Quelle dreiteilig Person · Datei · mm:ss–mm:ss,
    │                                    Dauer, V2 ja/nein), Sync-Tabelle, Warnungen, Gesamtlänge, Pegel-Abschnitt (Stufe 5)
    ├── broll-index.md                   je Ordner eine Zeile pro Clip
    ├── <video>-raster.md                Sprecher-Fenster und Strecken für die Plan-Session (Stufe 3, `--raster`)
    ├── <video>-broll.md                 gewählte Szenen/Shots je Strecke, Grund, Abweichung
    └── <Timeline>.xml                   optionaler FCP7-XML-Export (`autocut_export_xml.py`)

Resolve: Bin `AutoCut/<Video>` (+ `/B-Roll`) — Stufe 1 und Stufe 5 landen im selben Bin. roh-Timeline
**„AutoCut <Video> <JJJJ-MM-TT HHMM> (roh)"** (Stufe 1) → End-Timeline **„AutoCut <Video> <JJJJ-MM-TT HHMM>"**
ohne Suffix (Stufe 5, Finalisieren) — danach ist die roh-Timeline gelöscht (außer mit `--keep-roh`). Start-TC
01:00:00:00, Spuren V1 FX3 · V2 a7IV (nur Bild) · V3 B-Roll · A1 FX3 Ton — kein A2 mehr. Jeder Rohschnitt-Lauf
erzeugt eine neue roh-Timeline; unfinalisierte roh-Timelines bleiben stehen, bis der User sie löscht.
Meldung an den User immer mit: Timeline-Name, Berichtspfad, Zahlen, Warnungen, offene Punkte.

## Bekannte Fallen

- **zsh** splittet `$VAR`-Flaglisten nicht — Flags ausschreiben, Pfade mit Leerzeichen in Anführungszeichen.
- **Resolve-API:** `recordFrame` ist absolut (Start-TC 01:00:00:00 @ 25 fps = Frame 90000 + Offset),
  `AddMarker(frameId)` relativ zum Timeline-Start; `endFrame` inklusiv/exklusiv wird per `resolve_probe.py`
  gemessen (`probe.json`), nicht geraten. `useCustomSettings = 1` setzt Color-Management-Keys zurück
  (BMD-Bug) — der Code sichert und schreibt sie zurück. `AppendToTimeline` schreibt nur in die aktuelle Timeline.
- **Cloud-Projekte** speichern sofort; deshalb ausschließlich eigene, neue Timelines anfassen.
- **Proxy-Link:** `LinkProxyMedia` nur, wenn `GetClipProperty('Proxy')` noch keine Auflösung nennt.
- **Rotation:** Sony schreibt das Flag nur bei hochkant gedrehten Clips (Craiss 90°); MEK-Interviews sind
  quer (kein Flag). Nie aus dem Plan schließen, immer aus `media.json`.
- **Scribe-Verhörer** und Annotationen („(übersprechen 00:01:31)") im Wortstrom: Alignment gleicht
  Verhörer aus (Score ≥ 0,8), Annotationen zählen weder als Wort noch als Stille.
- **„[…]" im Plan** ist Kürzung nur für die PDF — die Passage läuft im Schnitt durchgehend (Cutter-Standard,
  David); Jumpcuts nur bei ausdrücklichem Kommentar (Details in `prompts/cutlist.md`).
- **Kosten Stufe 2 und 2b** entstehen pro Anfrage; Cache verhindert Doppelzahlung, `--force` nicht.
- **macOS hat kein `timeout`** in der Shell — lange Läufe im Hintergrund starten, nicht mit `timeout` wrappen.
