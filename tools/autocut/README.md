# NIRO AutoCut

Sechste Funktion von NIRO Studio: Aus einem fertigen Cutter-Schnittplan
(`projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/O-Ton-Pläne/video-N-*.md`) entsteht eine
**roh-Timeline** in DaVinci Resolve Studio — O-Töne in Planreihenfolge auf V1 (FX3) und V2 (a7IV,
nur Bild, per Waveform-Sync), A1, Pausen, Platzhalter für VO/Bild/Grafik, Marker je Beat (kein A2
mehr, Spec v2). Danach werden alle B-Roll-Clips des Drehs per Claude-Vision indexiert (Stufe 2),
je Abschnitt genauer bestimmt (Stufe 2b, Nachlauf) und V3 nach Plan v2 (Fenster/Strecken/Szenen/
Shots), Index und Profil in die roh-Timeline gefüllt (Stufe 3). **Finalisieren** (Stufe 5) macht
daraus die End-Timeline: Pegel je FX3-Clip, Zeitlupen, Marker, Spurnamen — ohne „(roh)"-Suffix.

Trigger im Chat: **„AutoCut: <Kunde>/<Projekt>[/<Charge>]"** + „Rohschnitt" | „B-Roll-Index" |
„Nachlauf" | „B-Roll" | „Profil" | „Finalisieren". Anleitung: `WORKFLOW-AutoCut.md`. Einrichtung:
`SETUP.md`. Spec: `docs/superpowers/specs/2026-09-03-autocut-design.md`.

## Stufen

| Unterbefehl | Stufe | Ergebnis |
|---|---|---|
| „Rohschnitt" | 1 | roh-Timeline V1/V2/A1 (V3 leer) mit O-Tönen, Pausen, Platzhaltern, Markern + Bericht |
| „B-Roll-Index" | 2 | `broll_index.json` + `broll-index.md`: Beschreibung aller B-Roll-Clips |
| „Nachlauf" | 2b | Abschnittsfelder je Clip (Einstellung, Perspektive, Brennweite, Bewegungsrichtung, Hauptmotiv, `setup_hash`) |
| „B-Roll" | 3 | V3 in der roh-Timeline gefüllt nach Plan v2 (Fenster/Strecken/Szenen/Shots), Index und Profil + Bericht |
| „Profil" | 4 | Schnitt-Profil aus den Cloud-Timelines des Users (noch nicht gebaut, siehe `WORKFLOW-AutoCut.md`) |
| „Finalisieren" | 5 | End-Timeline mit Pegel/Zeitlupe aus der roh-Timeline |

Details, Fehlerbilder und Eiserne Regeln: `WORKFLOW-AutoCut.md`.

## Grundsätze

- Claude entscheidet in der Session (Cutlist, B-Roll-Layout), Code prüft hart und baut per
  Resolve-Scripting-API. Bestehende Tools werden nur importiert (`niro_transcribe` per `.pth`), nie geändert.
- NAS nur lesen. Schreiben nur nach `<Charge>/_intern/autocut/`, `<Charge>/Ergebnisse/Rohschnitt/`
  und ans `Protokoll.md` (anhängen). In Resolve nur neue Bins/Timelines/Media-Pool-Einträge — Ausnahme:
  Finalisieren löscht die eigene roh-Timeline desselben Laufs, Probe-Skripte löschen ihre eigenen Probe-Objekte.
- Prüfen vor Bauen: `autocut_build.py` läuft nur mit passender `verify.json` (Hash der Cutlist).
- Format und Bildrate kommen aus dem Material (`media.json`), nie aus dem Plan.

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

## Aufbau

    defaults.yaml            Standardwerte (Pause, Handles, Sync, Index-Modell, B-Roll-Regeln v2, Ton, Resolve-Namen);
                             pro Charge überschreibbar in <Charge>/_intern/autocut/config.yaml
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
    scripts/                 CLI je Schritt (siehe Schnellstart; autocut_read_timelines.py für Stufe 4,
                             resolve_probe_xml.py für die Finalisieren-Vorprobe,
                             resolve_probe_api.py für die 21.1-API-Probe (--project = Freigabe), setup_env.py für die .env)
    prompts/                 cutlist.md, index-clip.md, index-sections.md, place-broll.md (Anleitungen/System-Prompts)
    profile/                 default.md + default.yaml (Startprofil B-Roll v2, bis Stufe 4 vorliegt)
    tests/                   pytest (Einheiten + Fake-Resolve, Fixtures aus MEK-Auszügen)
    docs/referenz/           Recherche-Material außerhalb des Produktivpfads (GCC-PHAT-Sync-Rezept)

## Arbeitsdateien einer Charge

`_intern/autocut/`: `media.json`, `sync.json`, `cutlist.json`, `verify.json`, `probe.json`,
`timeline.json`, `build.json`, `broll_index.json` (+ Cache `broll_index/<fingerprint>.json`),
`broll_index_kompakt.json`, `raster.json`, `broll_plan.json`, `broll_build.json`, `probe_xml.json`,
`probe_api.json`, `ton.json`, `finalize.json`, `work/` (Audio, Frames, Kontaktbögen/Abschnittsbögen,
`ton_cache.json`, `xml/`, `probe_api/` [synthetische Medien, Render]).
`Ergebnisse/Rohschnitt/`: `<video>-rohschnitt.md` (mit Pegel-Abschnitt nach Stufe 5), `broll-index.md`,
`<video>-raster.md`, `<video>-broll.md`, `<Timeline>.xml`.

## Tests

    cd "/Users/jansantos/NIRO Studio/tools/autocut" && venv/bin/python -m pytest -q

Ohne Resolve, ohne NAS, ohne API-Key lauffähig (Fake-Resolve, synthetische Signale, Fixtures).
