# NIRO AutoCut

Sechste Funktion von NIRO Studio: Aus einem fertigen Cutter-Schnittplan
(`projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/O-Ton-Pläne/video-N-*.md`) entsteht eine
**roh-Timeline** in DaVinci Resolve Studio — O-Töne in Planreihenfolge auf V1 (FX3) und V2 (a7IV,
nur Bild, per Waveform-Sync), A1, Pausen, Platzhalter für VO/Bild/Grafik, Marker je Beat (kein A2
mehr, Spec v2). Danach werden alle B-Roll-Clips des Drehs per Claude-Vision indexiert (Stufe 2),
je Abschnitt genauer bestimmt (Stufe 2b, Nachlauf) und V3 nach Plan v2 (Fenster/Strecken/Szenen/
Shots), Index und Profil in die roh-Timeline gefüllt (Stufe 3). **Finalisieren** (Stufe 5) macht
daraus die End-Timeline: Pegel je FX3-Clip, Zeitlupen, Marker, Spurnamen — ohne „(roh)"-Suffix.

Seit 15.09.2026 (Taxodia) kommen zwei Stufen dazu:
- **B-Roll aus der Auswahl-Timeline des Users** (Stufe 3a),
- **Feinschnitt** (Stufe 6): A/B-Wechsel, Grafikebene V4, Ton, Musik, SFX, Grading, Begradigen und
  Kopfposition.
Beide gibt es vorerst nur als Vorlagen (`vorlagen/feinschnitt/`), noch nicht als getestete Stufen.

Trigger im Chat: **„AutoCut: <Kunde>/<Projekt>[/<Charge>]"** + „Rohschnitt" | „B-Roll-Index" |
„Nachlauf" | „B-Roll" | „B-Roll aus Auswahl" | „Profil" | „Finalisieren" | „Feinschnitt" | „Kanten". Anleitung:
`WORKFLOW-AutoCut.md`. Einrichtung: `SETUP.md`. Spec: `docs/superpowers/specs/2026-09-03-autocut-design.md`.

## Stufen

| Unterbefehl | Stufe | Ergebnis |
|---|---|---|
| „Rohschnitt" | 1 | roh-Timeline V1/V2/A1 (V3 leer) mit O-Tönen, Pausen, Platzhaltern, Markern + Bericht |
| „B-Roll-Index" | 2 | `broll_index.json` + `broll-index.md`: Beschreibung aller B-Roll-Clips |
| „Nachlauf" | 2b | Abschnittsfelder je Clip (Einstellung, Perspektive, Brennweite, Bewegungsrichtung, Hauptmotiv, `setup_hash`) |
| „B-Roll" | 3 | V3 in der roh-Timeline gefüllt nach Plan v2 (Fenster/Strecken/Szenen/Shots), Index und Profil + Bericht — ausgesetzt seit 09.09. |
| „B-Roll aus Auswahl" | 3a | V3 aus der Auswahl-Timeline des Users, nur deren In/Out-Bereiche (Vorlage) |
| „Profil" | 4 | Schnitt-Profil aus den Cloud-Timelines des Users (noch nicht gebaut, siehe `WORKFLOW-AutoCut.md`) |
| „Finalisieren" | 5 | End-Timeline mit Pegel/Zeitlupe aus der roh-Timeline |
| „Feinschnitt" | 6 | neue Feinschnitt-Timeline: A/B-Wechsel, B-Roll-Tempo/Stabilisierung, Grafik V4, Ton, Musik, SFX, danach Grading, Begradigen, Kopfposition (Vorlagen) |
| „Kanten" | – | Kantenprüfung am Export (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) + Schnittbilder; Resolve nur lesend |
| „Telemetrie" | – | Gyro, Beschleunigung, Brennweite je Clip aus der Sony-rtmd-Spur (optischer Rückfall) → `telemetrie.json`, `telemetrie.md`: wackeln, ruhige Fenster, Haltung, Bewegungsart, Brennweiten- und Perspektivklasse; Abnehmer Sichtung/Aftermovie, Stufe 2b, 6d |
| „Review" (Pflicht nach jedem Bau) | – | Timeline über die Render-Queue rendern (≤ 1920 px) und als Version in NIRO Review ablegen (`autocut_review.py`, http://localhost:4711) |
| „Replay" (nur Kundenrunden) | – | Timeline nach Dropbox Replay hochladen (Vorschau, Upload nach OK), einsortieren in `Autocut/<Kunde>/<Projekt>` |
| „Kommentare" | – | Replay-Kommentare holen (`kommentare.md` im Feedback-Ordner), Umsetzung in neuer Timeline-Version |

Details, Fehlerbilder und Eiserne Regeln: `WORKFLOW-AutoCut.md`.

## Grundsätze

- Claude entscheidet in der Session (Cutlist, B-Roll-Layout), Code prüft hart und baut per
  Resolve-Scripting-API. Bestehende Tools werden nur importiert (`niro_transcribe` per `.pth`), nie geändert.
- NAS nur lesen. Schreiben nur nach `<Charge>/_intern/autocut/`, `<Charge>/Ergebnisse/Rohschnitt/`
  und ans `Protokoll.md` (anhängen); `autocut_replay.py` zusätzlich nach `<Charge>/_intern/replay/` und
  `<Charge>/Material/Feedback/`. In Resolve nur neue Bins/Timelines/Media-Pool-Einträge — Ausnahme:
  Finalisieren löscht die eigene roh-Timeline desselben Laufs, Probe-Skripte löschen ihre eigenen Probe-Objekte.
- Prüfen vor Bauen: `autocut_build.py` läuft nur mit passender `verify.json` (Hash der Cutlist).
- Format und Bildrate kommen aus dem Material (`media.json`), nie aus dem Plan.
- Keine neue Abhängigkeit für die Telemetrie: `rtmd.py`, `telemetrie*.py` kommen mit numpy, scipy und ffmpeg der
  AutoCut-venv aus (kein OpenCV); die cv2-Gegenprobe der Kalibrierung liest nur vorhandene `ruhe.json`-Werte.

## Schnellstart

    TOOL="/Users/jansantos/NIRO Studio/tools/autocut"
    PY="$TOOL/venv/bin/python"
    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"

    "$PY" "$TOOL/scripts/autocut_prepare.py" "$CHARGE"            # media.json (Format, Proxies, Kamerapaare)
    "$PY" "$TOOL/scripts/autocut_sync.py" "$CHARGE"               # sync.json (FX3×a7-Versatz je Paar)
    # Cutlist nach prompts/cutlist.md: autocut_cutlist_draft.py + autocut_find_quote.py → cutlist.json
    "$PY" "$TOOL/scripts/autocut_verify.py" "$CHARGE"             # verify.json, Exit 0 nötig
    "$PY" "$TOOL/scripts/resolve_probe.py" "$CHARGE"              # einmalig je Resolve-Umgebung: probe.json
    "$PY" "$TOOL/scripts/autocut_build.py" "$CHARGE"              # roh-Timeline „AutoCut <Video> <Datum> (roh)" + Bericht
    "$PY" "$TOOL/scripts/autocut_export_xml.py" "$CHARGE"         # optional: FCP7-XML für Premiere
    "$PY" "$TOOL/scripts/autocut_index_broll.py" "$CHARGE" --dry-run   # Stufe 2: Clipzahl + Kosten
    "$PY" "$TOOL/scripts/autocut_index_broll.py" "$CHARGE" --limit 5   # Testlauf, dann ohne --limit
    "$PY" "$TOOL/scripts/autocut_index_sections.py" "$CHARGE" --dry-run   # Stufe 2b: Nachlauf, Clipzahl + Kosten
    "$PY" "$TOOL/scripts/autocut_index_sections.py" "$CHARGE" --limit 5   # Testlauf, dann ohne --limit
    # B-Roll-Layout nach prompts/place-broll.md → broll_plan.json (v2)
    "$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --compact
    "$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --raster
    "$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE" --verify-only
    "$PY" "$TOOL/scripts/autocut_place_broll.py" "$CHARGE"        # V3 in die roh-Timeline + Bericht
    "$PY" "$TOOL/scripts/resolve_probe_xml.py" "$CHARGE"          # einmalig je Resolve-Umgebung: probe_xml.json
    "$PY" "$TOOL/scripts/resolve_probe_api.py" "$CHARGE" --project "<Projekt>"   # einmalig je Resolve-Umgebung: probe_api.json (21.1-API)
    "$PY" "$TOOL/scripts/autocut_finalize.py" "$CHARGE"           # Stufe 5: End-Timeline (Pegel, Zeitlupe) + Bericht
    "$PY" "$TOOL/scripts/autocut_kanten.py" "$CHARGE"             # Kantenprüfung am Export (Resolve nur lesend)
    "$PY" "$TOOL/scripts/autocut_kanten.py" "$CHARGE" --ohne-export   # nur Wortkanten am Quellton, z. B. nach Handänderungen
    "$PY" "$TOOL/scripts/autocut_telemetrie.py" "$CHARGE" [--ordner <Pfad>] [--dry-run]   # Telemetrie je Clip: telemetrie.json + Bericht
    "$PY" "$TOOL/scripts/autocut_telemetrie.py" "$CHARGE" --kalibrieren                    # einmalig: Gyro ↔ optisch (defaults.yaml telemetrie:)
    "$PY" "$TOOL/scripts/autocut_schnittbild.py" "$CHARGE" --clip <Datei> --von 12.3 --bis 15.8   # Schnittbild Rohclip
    "$PY" "$TOOL/scripts/autocut_review.py" "$CHARGE" --project "<Projekt>"             # nach jedem Bau: Render + NIRO Review
    "$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE" hochladen --project "<Projekt>"   # Vorschau; --hochladen nur nach OK
    "$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE" einsortiert --titel "<Titel>"     # nach dem Verschieben im Chrome
    "$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE" kommentare                         # Replay-Kommentare holen
    "$PY" "$TOOL/scripts/autocut_readback.py" "$CHARGE" --timeline "<Name>"             # Bau-Readback nach Vorlagen-Bauten

## Aufbau

    defaults.yaml            Standardwerte (Pause, Handles, Sync, Index-Modell, B-Roll-Regeln v2, Ton, Resolve-Namen);
                             pro Charge überschreibbar in <Charge>/_intern/autocut/config.yaml. path_map ordnet die
                             Pfade der Arbeitsdateien dem aktuellen Ablageort zu (NAS → SSD), je Charge in config.yaml
    src/niro_autocut/
      charge.py              Charge öffnen, Config, Pfade, Schreibschutz, Protokoll-Eintrag
      media.py               ffprobe, Proxy-Suche, Format/Rotation, Fingerprint, Audio-Extraktion
      plan.py                Cutter-Plan-Tabelle lesen (Zeilen, Typen, Ziellänge, Sperren-Text)
      align.py               Zitat → Wortspanne (Hülle um quote_align.py)
      quote_align.py         Alignment-Engine (Levenshtein + Kölner Phonetik, „[…]"-Segmente, Take-Wahl)
      cutlist.py              Cutlist-Modell, Entwurf aus dem Plan, harte Prüfung, Hash
      sync.py                Waveform-Kreuzkorrelation, Kamerapaare, Konfidenz, Drift
      timeline_model.py      Beats → frame-genaue Items (Pausen, Platzhalter, Handles, Marker; V2 nur Bild, kein A2)
      resolve_api.py         Resolve-Anbindung: Bins, Media Pool (Dedupe), Timeline-Bau, Marker, Export, Lesen, XML-Import
      probe_media.py         synthetisches Testmaterial der API-Probe (ffmpeg-Argumentlisten, nur Fehlendes erzeugen)
      probe_api.py           Auswertung der API-Probe 21.1 (Erwartungswerte, Speed-/Align-Klassifikation)
      report.py              Berichte (Rohschnitt, B-Roll-Index, Pegel-Abschnitt)
      broll_index.py         Szenenwechsel, Frames, Kontaktbögen, Claude-Vision, Cache (Stufe 2)
      index_sections.py      Abschnitts-Nachlauf: Einstellung/Perspektive/Brennweite/Bewegungsrichtung/setup_hash (Stufe 2b)
      broll_layout.py        B-Roll-Layout v2: Fenster, Strecken, Szenen, Shots, harte Prüfung, V3-Items (Stufe 3)
      broll_plan.py          Profil laden (`load_profile`), Clip-Referenzen auflösen, ältere (v1) Hilfsfunktionen
      ton.py                 True-Peak-Messung je A1-Clip (ffmpeg ebur128), Gain auf Ziel-dBTP, Cache (Stufe 5)
      xml_patch.py           FCP7-XML lesen/patchen (Pegel, Zeitlupe) für den Finalisieren-Roundtrip
      finalize.py            Stufe 5: roh-Timeline → XML → Pegel/Zeitlupe → End-Timeline → prüfen → roh löschen
      kanten.py              Kantenprüfung: Schnappschuss, Schnitte, Befund-Regeln (AR-Knackser), Wortkanten, Grafik-Hinweise
      kanten_medien.py       Export lesen: ffprobe, Graustufen-Metriken je Frame (Cache), Ton als PCM
      kanten_bericht.py      Bericht <video>-kanten.md
      schnittbild.py         PNG: Filmstreifen + Pegel + Wörter + Schnitte (nach video-use, MIT)
      replay.py              Replay: Titel, Versionsname, Replay-Ordner, Bitrate-Grenze, Upload-Log, finde_upload
      replay_kommentare.py   Replay-Kommentare aus FrameIO-Markern/Chrome-JSON, Clips, Stand-Vergleich, kommentare.md
      readback.py            Bau-Readback (_intern/autocut/readback/) für „seit dem Bau von Hand geändert?"
      wiedergabe.py          Vollbild-Wiedergabe über werkzeuge/fenster.swift erkennen
      rtmd.py                Sony-rtmd-Datenspur: Samples, IMU-Blöcke, Brennweite/Fokus, Sidecar-XML, Kamera
      telemetrie.py          Kennzahlen (Gyro → px @480, wackeln, Fenster, Haltung, Bewegungsart, Lage, Zoomfahrten), Clip-Messung, Cache, 2b/6d-Helfer
      telemetrie_optisch.py  Graustufen-Frames + numpy-Phasenkorrelation (Rückfall ohne Datenspur, Kalibrier-Referenz)
      telemetrie_bericht.py  Bericht telemetrie.md, Vergleich mit dem B-Roll-Index
      telemetrie_kalibrierung.py  Gyro ↔ optisch auf demselben Fenster: Achsen, Vorzeichen, px_faktor, Spearman
    scripts/                 CLI je Schritt (siehe Schnellstart; autocut_read_timelines.py für Stufe 4,
                             resolve_probe_xml.py für die Finalisieren-Vorprobe,
                             resolve_probe_api.py für die 21.1-API-Probe (--project = Freigabe), setup_env.py für die .env)
    prompts/                 cutlist.md, index-clip.md, index-sections.md, place-broll.md (Anleitungen/System-Prompts)
    profile/                 default.md + default.yaml (Startprofil B-Roll v2, bis Stufe 4 vorliegt)
    vorlagen/feinschnitt/    Chargen-Skripte für Stufe 3a/6 (Stand Taxodia 15.09.2026) mit ANPASSEN-Block; spiegeln
                             <Charge>/_intern/ (musik/, sfx/, color/, gesichtscheck/, begradigen/, werkzeuge/) —
                             Ordner in die Charge kopieren, Übersicht in vorlagen/README.md
    werkzeuge/               fenster.swift (Fensterliste von Resolve, von wiedergabe.py aufgerufen)
    tests/                   pytest (Einheiten + Fake-Resolve, Fixtures aus MEK-Auszügen)
    docs/referenz/           Recherche-Material außerhalb des Produktivpfads (GCC-PHAT-Sync-Rezept)

## Arbeitsdateien einer Charge

`_intern/autocut/`: `media.json`, `sync.json`, `cutlist.json`, `verify.json`, `probe.json`,
`timeline.json`, `build.json`, `broll_index.json` (+ Cache `broll_index/<fingerprint>.json`),
`broll_index_kompakt.json`, `raster.json`, `broll_plan.json`, `broll_build.json`, `probe_xml.json`,
`probe_api.json`, `ton.json`, `finalize.json`, `kanten_readback.json`, `kanten.json`, `telemetrie.json`
(+ Cache `telemetrie/<fingerprint>.json`), `telemetrie_kalibrierung.json`, `work/` (Audio, Frames,
Kontaktbögen/Abschnittsbögen, `kanten/` Bild-Metriken, `schnittbild/` PNGs,
`ton_cache.json`, `xml/`, `probe_api/` (synthetische Medien, Render)).
`_intern/autocut/readback/<Titel>.json` (Bau-Readback). `_intern/replay/`: `uploads.json`, `schnappschuesse/`, `renders/`,
`<Titel>.chrome.json`. `Material/Feedback/<Upload-Datum> Replay <Titel>/`: `kommentare.md`, `kommentare.json`, `umsetzung.md`.
`Ergebnisse/Rohschnitt/`: `<video>-rohschnitt.md` (mit Pegel-Abschnitt nach Stufe 5), `broll-index.md`,
`<video>-raster.md`, `<video>-broll.md`, `<video>-kanten.md`, `telemetrie.md`, `<Timeline>.xml`.
Stufe 3a/6 (Vorlagen): `_intern/autocut/broll_auswahl.json`, `broll_einsatz.json`, `audio.json`,
`grafik_einsatz.json`, `feinschnitt.json`, `feinschnitt_umbau.json` sowie `_intern/grafik/`, `musik/`, `sfx/`,
`color/`, `begradigen/`, `gesichtscheck/`, `sichtung/` (Liste in `WORKFLOW-AutoCut.md`, Ausgabe-Konvention).

## Tests

    cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q

Ohne Resolve, ohne NAS, ohne API-Key lauffähig (Fake-Resolve, synthetische Signale, Fixtures).
