# WORKFLOW: AutoCut (Schnittplan → Rohschnitt → Feinschnitt in DaVinci Resolve)

Trigger: **„AutoCut: <Kunde>/<Projekt>[/<Charge>]"** plus Unterbefehl — aus einem fertigen
Cutter-Schnittplan (`Ergebnisse/O-Ton-Pläne/video-N-*.md`) entsteht eine **roh-Timeline** im
offenen Resolve-Projekt: alle O-Töne in Planreihenfolge, beide Kameras synchron (V2 = a7IV nur
Bild, kein A2 mehr), Pausen, Platzhalter für VO/Bild/Grafik, Marker. Danach werden alle B-Roll-Clips
des Drehs per Claude-Vision beschrieben (Stufe 2), je Abschnitt genauer bestimmt (Stufe 2b,
Nachlauf) und V3 nach Plan v2 (Fenster/Strecken/Szenen/Shots) in die roh-Timeline gefüllt
(Stufe 3). Zuletzt macht **Finalisieren** (Stufe 5) daraus die fertige End-Timeline: Pegel je
FX3-Clip, Zeitlupen, Marker, Spurnamen — ohne „(roh)"-Suffix.

Seit dem Taxodia-Erklärvideo (15.09.2026) geht AutoCut bis zum **Feinschnitt** (Stufe 6). Ziel sind zu 90 %
fertige Videos, an denen der User nur noch Timings nachstellt. Dazu gehören:
- **B-Roll aus der Auswahl-Timeline des Users** (Stufe 3a),
- **A/B-Kamerawechsel**, **Grafikebene auf V4**, **Ton** (Normalisierung und Voice Isolation), **Musik** und **SFX**,
- **Grading**, **Begradigen** und **Kopfposition**.
Stufe 3a und 6 bestehen aus **Vorlagen** (`vorlagen/feinschnitt/`, Chargen-Skripte mit ANPASSEN-Block), noch nicht
aus getesteten AutoCut-Stufen.

(Abgrenzung: „Schnittplan:" **erzeugt** den Plan in `tools/transcribe/WORKFLOW-Schnittplan.md`;
AutoCut **liest** ihn nur. Die Grafikebene selbst entsteht in „Animation:" (`tools/motion/WORKFLOW-Motion.md`).
VO-Stimme, Multicam-Objekte und Untertitel sind nicht Teil von AutoCut; Musik, SFX, Grafik und Grading
kommen nur in Stufe 6 vor.) Spec: `docs/superpowers/specs/2026-09-03-autocut-design.md` (v2 B-Roll-Layout, Review-Fix-Welle:
`docs/superpowers/specs/2026-09-04-autocut-v2-design.md`), Pläne: `docs/superpowers/plans/2026-09-03-autocut.md`,
`docs/superpowers/plans/2026-09-04-autocut-profil.md`, `docs/superpowers/plans/2026-09-04-autocut-v2.md`.
Erst-Referenz: MEK Imagefilm (`projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh/`).
Referenz Feinschnitt: Taxodia (`projects/Steuerkanzlei Ludwig x Taxodia/Taxodia Erklärvideo/2026-09 Dreh 08.09/`,
Original-Skripte in `_intern/`, Ablauf und Zahlen in `Protokoll.md`).

| Unterbefehl | Stufe | Ergebnis |
|---|---|---|
| „Rohschnitt" | 1 | roh-Timeline V1/V2/A1 (V3 leer) mit O-Tönen, Pausen, Platzhaltern, Markern + Bericht |
| „B-Roll-Index" | 2 | `broll_index.json` + `broll-index.md`: Beschreibung aller B-Roll-Clips |
| „Nachlauf" | 2b | Abschnittsfelder je Clip |
| „B-Roll" | 3 | V3 in der roh-Timeline gefüllt nach Plan v2 (Fenster/Strecken/Szenen/Shots), Index und Profil + Bericht — **ausgesetzt** |
| „B-Roll aus Auswahl" | 3a | V3 aus der Auswahl-Timeline des Users: nur deren In/Out-Bereiche, jeder Shot höchstens einmal (Vorlage) |
| „Profil" | 4 | Schnitt-Profil aus den Cloud-Timelines des Users (eigener Plan, Abschnitt unten) |
| „Finalisieren" | 5 | End-Timeline mit Pegel/Zeitlupe |
| „Feinschnitt" | 6 | neue Timeline „AutoCut <Video> <Datum> Feinschnitt": A/B-Wechsel, B-Roll-Tempo und Stabilisierung, Grafik V4, Ton, Musik, SFX; danach Grading, Begradigen, Kopfposition. Die Bausteine 6a–6i sind einzeln aufrufbar, z. B. „AutoCut: … Grading" (Vorlagen) |
| „Kanten" | – | Kantenprüfung am Export einer AutoCut-Timeline (Schwarzbild, Schnipsel, Knackser, Tonloch, Wort angeschnitten) mit Schnittbildern; Resolve nur lesend |
| „Replay" | – | Timeline nach Dropbox Replay hochladen: Vorschau, Upload nur nach OK im Chat, danach im Chrome in `Autocut/<Kunde>/<Projekt>` einsortieren |
| „Kommentare" | – | Replay-Kommentare selbstständig aus dem Replay-Ordner des Projekts holen, Eindeutiges in einer neuen Timeline-Version umsetzen, Handarbeit und Rückfragen melden |

Ohne Unterbefehl gilt „Rohschnitt". Bei nur einer Charge reicht Kunde/Projekt.

## Pfade (absolut; zsh: alles in Anführungszeichen, Flags ausschreiben, keine `$VAR`-Flaglisten)

    TOOL="/Users/jansantos/NIRO Studio/tools/autocut"
    PY="$TOOL/venv/bin/python"
    CHARGE="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>/<Charge>"
    VORLAGEN="$TOOL/vorlagen/feinschnitt"

Alle Skripte: `"$PY" "$TOOL/scripts/<skript>.py" "$CHARGE" [Flags]`. Jedes Skript druckt eine
Zusammenfassung; Exit ≠ 0 heißt Abbruch mit deutscher Meldung (Ursache + Abhilfe steht im Text).
Vorlagen (Stufe 3a/6) werden nach `$CHARGE/_intern/` kopiert, im ANPASSEN-Block gefüllt und dort gestartet:
`"$PY" "$CHARGE/_intern/<skript>.py" [Flags]`. Flags stehen im Docstring jeder Vorlage, vor dem ersten Lauf lesen.
Schreibende Vorlagen rechnen ohne Flag nur (Probelauf) und schreiben erst mit `--bauen` bzw. `--ausfuehren`.
Abweichend davon:
- `grading_anwenden.py` braucht `--test` oder `--alle`.
- `kalibrierung_resolve.py` und `pruefung_resolve.py` brauchen einen Schritt (`aufbauen`, `export`, `loeschen` …).
- Bewusst ohne Flag schreiben nur `werkzeuge/schreibtest*.py` (Schreibsperre testen) und
  `begradigen/karte_nachsetzen.py` (Hintergrund-Retry, nur mit Wissen des Users).

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

- **Stufe 3 „B-Roll" ist ausgesetzt (User 09.09.2026).** Urteil zum Schnitt vom 09.09.: „total unpassend und
  schlecht getrimmt — solange du das noch nicht besser kannst, lass es lieber ganz." Bis Teilprojekt 2
  („B-Roll-Index v3": zuverlässige Shot-Erkennung, Ausschuss-Metriken, Trimmung) abgenommen ist, **wählt
  AutoCut keinen B-Roll selbst**. Stufe 3 nur auf ausdrückliche Anweisung im Chat.
- **B-Roll nur aus der Auswahl des Users (Stufe 3a, User 15.09.2026).** Der User legt im Kundenprojekt eine
  Auswahl-Timeline an und gibt sie im Chat frei. Genutzt werden ausschließlich deren In/Out-Bereiche:
  „du darfst nur die Bereiche, die darin sind, nutzen, also die Clips nicht verlängern, kürzen geht natürlich."
  Jeder Shot höchstens einmal, Tempo wie in der Auswahl (Zeitlupe nur auf Wunsch), die Auswahl selbst nur lesen.
- **NAS nur lesen.** Kein Skript schreibt unter `/Volumes/`. Originale und Proxies bleiben unangetastet.
- **Schreibbereiche** (im Code über `Charge.assert_writable` erzwungen): nur `<Charge>/_intern/autocut/**`,
  `<Charge>/Ergebnisse/Rohschnitt/**` und `Protokoll.md` (anhängen); `autocut_replay.py` zusätzlich
  `<Charge>/_intern/replay/**` und `<Charge>/Material/Feedback/**` (`Charge.open_basis`). Sonst nichts unter `Material/`,
  `O-Ton-Pläne/` oder in anderen Tools. Die Vorlagen (Stufe 3a/6) sind Chargen-Skripte **ohne** diese
  Code-Sperre: Sie schreiben nur unter `<Charge>/_intern/` in eigene Unterordner, auch ihre Prüf-Renders.
  Pfade im ANPASSEN-Block vor dem ersten Lauf prüfen.
- **Resolve — nur anhängen, fast nie löschen:** neue Bin-, Timeline- und Media-Pool-Einträge anlegen,
  bestehende Timelines nie verändern. Löschen ist nur in zwei Fällen erlaubt: die **eigene
  roh-Timeline desselben Laufs** beim Finalisieren (Name muss exakt mit dem aus `build.json`
  übereinstimmen — sonst verweigert der Code das Löschen) und die **selbst angelegten
  Probe-Objekte** (`resolve_probe.py`, `resolve_probe_xml.py`; je mit `--keep` erhaltbar). Jede
  andere Timeline im Projekt bleibt unangetastet. Cloud-Projekte speichern sofort (Live Save) —
  deshalb keine Experimente an fremden Timelines. Der Feinschnitt (Stufe 6) ist eine **neue** Timeline;
  die roh-Timelines bleiben unverändert, spätere Bausteine (Umbau, SFX, Grading, Begradigen) ändern nur
  Items der eigenen Feinschnitt-Timeline. Eigene Prüf- und Kalibrier-Timelines werden danach wieder gelöscht.
- **Spurlayout ohne A2 (Spec v2):** V1 FX3 (Bild + Ton), V2 a7IV nur Bild (kein Ton, kein
  A2-Track mehr), V3 B-Roll (nur Bild), A1 FX3 Ton — jede AutoCut-Timeline der Stufen 1–5 hat 3 Videospuren und
  1 Audiospur. Der Feinschnitt (Stufe 6) hat zusätzlich V4 Grafik, A2/A3 Musik und A4/A5 SFX.
- **User-Timeline und Bin wiederherstellen:** jeder Resolve-Lauf merkt sich beim Verbinden die gerade
  offene Timeline des Users und aktiviert sie am Ende wieder — auch wenn der Lauf mit einem Fehler
  abbricht. Den **Media-Pool-Bin** stellt `autocut_build.py` nicht wieder her: Importe rufen `SetCurrentFolder`,
  bei Taxodia stand der Media Pool danach auf „Kamera-B". Deshalb vor dem Bau per MCP
  `project.GetMediaPool().GetCurrentFolder().GetUniqueId()` merken und danach zurücksetzen. Die Vorlagen
  sichern Timeline und Bin selbst.
- **Parallelbetrieb mit dem User:** Ein Bau wechselt für einige Sekunden die aktive Timeline. Arbeitet der
  User gerade in Resolve, vorher kurz abstimmen. **Während der User abspielt, nie schreiben:** Schreibaufrufe
  liefern dann `False` oder hängen, und ein abgebrochenes Skript schreibt nach der Wiedergabe trotzdem.
  Wiedergabe mit `vorlagen/feinschnitt/werkzeuge/fenster.swift` prüfen; nach jedem Abbruch den Zustand neu
  lesen und fehlende eigene Items wiederherstellen.
- **Aufbau für Handarbeit** (User 15.09.2026: „So kann ich manuell einfach noch die Timings da ändern"):
  - Die Zweitkamera (V2) liegt durchgehend unter jedem O-Ton-Stück und ist an den Wechselpunkten geteilt.
    Nur die sichtbaren Stücke sind aktiv, der Rest ist deaktiviert (`SetClipEnabled(False)`).
    Wechsel verschiebt der User per Roll-Edit.
  - Die Grafikebene (V4) hat je Grafik-Element einen Clip, getrimmt auf die sichtbaren Frames.
  - **Von Hand Geändertes nie überschreiben:** vor jedem Umbau oder Nachsetzen den eigenen Bau-Stand
    zurücklesen; weicht er ab, nichts schreiben.
  - **Grading erst nach einem Umbau:** ersetzte Items verlieren ihren Grade.
- **Tonspuren und Stereo Fixer** (Taxodia 15.09.2026):
  - Alle Tonspuren (Sprache, Musik, SFX) beim Bau anlegen, bevor der erste Clip angehängt wird. Per `AddTrack`
    nachträglich angelegte Spuren rendern stumm (−180 dB), obwohl die Spurmeter Pegel zeigen.
  - Auf jede SFX- und Sprachspur gehört der Track-Effekt **Stereo Fixer, Fix Mode 2** (User-Regel). Er ist per
    API nicht setzbar: nach jedem Bau mit Sprache oder SFX den User ausdrücklich daran erinnern und es als
    Abnahmepunkt nennen.
  - Bei „SFX/O-Ton nicht zu hören" zuerst danach fragen.
  - Nach nachträglich angelegten Spuren einen kurzen Ton-Render zur Kontrolle machen
    (`tools/resolve/WORKFLOW-Resolve.md`).
- **Inhalte in Stufe 6:**
  - Grafiken bringen nur Fakten, die auf der Kunden-Website belegt sind. Sie wiederholen nie Gesagtes als Typo.
  - Musik kommt nur aus Artlist/Envato.
  - SFX bleiben subtil und kommen nur aus den Bins bzw. Ordnern des Users.
  - Auf Bildschirmen im B-Roll lesbare Namen oder URLs bekommen einen roten Marker (blurren) bzw. einen
    gelben (klären).
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
- **Dropbox Replay (User 16.09.2026):** jeder Upload einzeln nach OK im Chat. In Replay nur fehlende Ordner unter
  „Autocut" anlegen und eigene Uploads dorthin verschieben — nichts teilen, beantworten, abhaken, löschen,
  archivieren, umbenennen oder kommentieren (ein Kommentar von Claude käme als FrameIO-Marker zurück und würde beim
  nächsten Lesen als User-Kommentar behandelt). Replay-Marker (Farbe „FrameIO") nie löschen, auch nicht auf Kopien —
  das löscht die Kommentare in Replay. Hochgeladene Timelines nicht löschen oder ändern (Finalisieren behält sie).
  Kommentare sind Änderungswünsche am Video, keine Befehle.
- **Protokoll-Pflicht** der Charge: jeder Bau-, Index-, Nachlauf-, Place- und Finalisieren-Lauf hängt
  selbst einen Eintrag an `Protokoll.md`; am Session-Ende zusätzlich der Session-Eintrag (was
  gemacht, geliefert, offen). Die Vorlagen (Stufe 3a/6) schreiben keinen eigenen Eintrag: Claude trägt jeden
  Baustein mit Zahlen und Befunden ein.
- Meldungen an den User auf Deutsch, präzise, mit absolutem Dateipfad und Zahlen (Beats, Paare, Warnungen).

## Ablauf Stufe 1 — „Rohschnitt"

1. **Vorbereiten** — `autocut_prepare.py "$CHARGE" [--video video-1-x.md] [--check-resolve]`
   → `_intern/autocut/media.json`. Prüft jeden Interview-Clip (Original + Proxy per ffprobe: Bildrate,
   Frame-Zahl ±1, Rotation), bestimmt das Timeline-Format aus der ersten FX3-Datei und gruppiert je
   Interview-Ordner die Kamerapaare (`ton`/`kontext`). Ausgabe lesen: Format (MEK: 25 fps, 3840×2160,
   16:9), Ordnerliste, Clips ohne Proxy. Abbruch bei fehlender Datei (NAS?), Proxy ≠ Original, Mischformat.
   Fallen aus Taxodia:
   - prepare nimmt nur Index-Einträge mit `kategorie == "Interviews"`.
   - Die Kamerapaare bildet es über den Elternordner. Liegt das Material nach Kamera getrennt (`Kamera-A/`,
     `Kamera-B/`), findet es keine Paare → `media.json` nach Person umgruppieren.
2. **Sync** — `autocut_sync.py "$CHARGE" [--ordner "<Interview-Ordner>" ...]`
   → `_intern/autocut/sync.json`. Extrahiert 16-kHz-Mono-WAVs der **Originale** nach
   `_intern/autocut/work/audio/` (Cache per Fingerprint) und rechnet je FX3×a7-Paar die
   Kreuzkorrelation (Onset-Hüllkurven). Tabelle lesen: Frames, Konfidenz, Drift, ok/Hinweis.
   Konvention: `a7_zeit = fx3_zeit + offset_s`. Kontrolle MEK: Johanna_Notaufnahme 48–49 Frames.
   Exit 1 = ein Ordner mit Paaren ohne ok-Paar (V2 bleibt dort leer, der Bericht sagt es) — kein Abbruch.
   `--ordner` rechnet nur diese Ordner neu, der Rest bleibt. Paare unter Konfidenz 4 bleiben „nicht ok" (V2 leer,
   roter Marker); den Versatz vorher über die Wortzeiten beider Kameras gegenprüfen, nie „passend rechnen".
3. **Cutlist** — Claude in der Session nach **`prompts/cutlist.md`** (dort steht alles: Entwurf per
   `autocut_cutlist_draft.py`, jedes Zitat per `autocut_find_quote.py --clip <Stem> --text "…" --near mm:ss`
   auflösen, In/Out-Hinweise, Sperren aus `**Verboten:**`, Pausen, Kopf aus `media.json`)
   → `_intern/autocut/cutlist.json`. Kein Beat wird weggelassen; VO/Bild/Grafik werden Platzhalter
   mit der Plan-Schätzung „~x s".
   **Innenschnitte und Sperren ohne Zeiten:** Der Draft folgt der Regel „[…]" = durchgehend. Deshalb
   verschmilzt er echte Innenschnitte (Quelle mit mehreren „+"-Bereichen) zu einem Cut, und aus Sperrhinweisen
   ohne Zeitbereich entstehen 0 Sperren (Taxodia). In dem Fall nach dem Draft die Vorlage
   `$VORLAGEN/cutlist_aus_plan.py` nutzen:
   - ein Cut je Bereich, Wortgrenzen aus dem Scribe-Cache,
   - `hart_in`/`hart_out`, wenn Nachbarwörter in den Handles liegen (`clamp_handles` schützt nur vor anderen
     Sprechern),
   - Sperren mit exakten Bereichen.
   Die Plan-Zeilen dafür liefert `plan_rows.py` (mit `find_tc.py`).
   **Unklare In/Outs** (Atmer, Blinzeln, Wackler an der Kante): `autocut_schnittbild.py "$CHARGE" --clip <Datei> --von <s>
   --bis <s>` legt Filmstreifen, Pegel und Wörter als PNG unter `_intern/autocut/work/schnittbild/` ab — mit Read ansehen,
   dann entscheiden.
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
   Punkte. Längen: `total_frames` enthält Pausen und Platzhalter; die Resolve-Timeline endet am letzten Clip,
   eine Endcard am Schluss ist nur ein Marker hinter dem Ende.
   Danach den Upload nach Replay nur anbieten, wenn der roh-Schnitt vor B-Roll, Finalisieren oder Feinschnitt
   begutachtet werden soll (Vorschau zeigen, Abschnitt „Review in Replay") — nach einem Upload läuft keine weitere
   Stufe mehr auf dieser Timeline: Stufe 3a, 5 und 6 brauchen dann eine neue Version per Neubau (Schritt 8).
8. **Neubau** (z. B. Kurzfassung „1 min kürzer"):
   1. Alte Stände nach `_intern/archiv/<Datum> <Name>/` sichern (Plan-Markdowns, PDF, `plan_rows`, Cutlist,
      `timeline`/`build`/`verify`, Bericht).
   2. Plan-Markdown und `plan_rows.py` anpassen.
   3. `autocut_cutlist_draft.py --force`, bei Innenschnitten danach `cutlist_aus_plan.py`.
   4. `autocut_verify.py`, dann `autocut_build.py --dry-run`, dann den Bau.
   Der Bau erzeugt eine neue roh-Timeline mit Uhrzeit im Namen, die alte bleibt stehen.

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

## Ablauf Stufe 3a — „B-Roll aus Auswahl" (Vorlagen, Stand Taxodia 15.09.2026)

**Voraussetzungen:**
- Stufe 1 ist gebaut (`timeline.json`, `build.json`, `probe.json`).
- Der User hat im Kundenprojekt eine Auswahl-Timeline angelegt und sie im Chat freigegeben, samt Schreibfreigabe
  für das Projekt.
- Ob die Shots in Blöcken oder lückenlos liegen, ist egal; Blöcke gelten als Szenen-Vorschlag.

1. **Vorlagen in die Charge** — beim ersten Mal `cp -Rn "$VORLAGEN/." "$CHARGE/_intern/"` (`-n`: vorhandene
   Chargen-Skripte nie überschreiben).
2. **Auswahl lesen** — `broll_auswahl.py [--nur-lesen]`, nur lesend. ANPASSEN: `PROJEKT`, `TIMELINE_ID` (per MCP
   `GetUniqueId()` der Auswahl) und `TL_FPS`.
   - Je Shot werden Clip, Datei und Quell-In/Out aus `GetLeftOffset()` + `GetDuration()` gelesen → `_intern/autocut/broll_auswahl.json`.
   - Je Shot entstehen vier Standbilder aus dem echten In/Out (Proxy) → Kontaktbögen `_intern/sichtung/broll-auswahl/`.
   - Die Rechnung setzt 100 % Tempo in der Auswahl voraus. Nach Änderungen an der Auswahl die Standbilder löschen.
3. **Sichten:**
   - Kontaktbögen lesen und Situationen/Motive notieren.
   - Bildschirm-Shots in voller Auflösung auf lesbare Namen, URLs und Kurspläne prüfen → Marker rot „BLUR …"
     bzw. gelb „klären …".
   - Sprechende Personen im B-Roll zuordnen.
4. **Plan** (Claude, in `broll_einsetzen.py` → `PLAN`, `MARKER`, `BIN`) — je Eintrag: Shot-Nr. der Auswahl,
   Versatz im Shot, Länge, Record-In (Frames), Beat, Inhalt. Regeln:
   - Verteilung nach Wortzeiten und „Bild-Vorschlag" des Plans.
   - **Gesicht bleibt** bei Kaltstart, Bauchbinden, Beweis-Aussagen und CTAs.
   - B-Roll deckt Titel, Innenschnitte und passende Motive.
   - Wer im B-Roll spricht, liegt nicht unter seinem eigenen O-Ton (Lippen).
   - Kein Einstellungs-Doppel in Folge.
   - Jeder Shot höchstens einmal, nie über die Grenzen der Auswahl hinaus.
5. **Probelauf** — `broll_einsetzen.py` ohne Flag. Er prüft Auswahl-Grenzen, Doppelnutzung und Überlappung und
   gibt die Tabelle aus. Die Frame-Umrechnung ist für 50p-Clips in 25p gemessen; andere Bildraten vorher prüfen.
6. **Vorlegen, dann bauen** — nach Freigabe `broll_einsetzen.py --bauen`:
   - V3 der roh-Timeline (muss leer sein) in einem Append, dazu Marker.
   - Readback: identisch, 0 außerhalb der Auswahl.
   - Timeline und Bin des Users zurück → `_intern/autocut/broll_einsatz.json`.
   - Rohschnitt-Bericht um „B-Roll" (Tabelle aller Shots) ergänzen, Protokoll-Eintrag.
   - Dem User melden: B-Roll-Anteil, ungenutzte Auswahl-Sekunden, Marker.

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
B-Roll-Bericht, keine Schwarzframes. Danach den Upload nach Replay anbieten.

## Stufe 6 — „Feinschnitt" (Vorlagen, Stand Taxodia 15.09.2026)

Stufe 6 besteht aus **Vorlagen**, nicht aus getesteten AutoCut-Stufen. Die Originale liefen im
Taxodia-Feinschnitt; die neutralisierten Vorlagen selbst sind ungetestet. Claude füllt die ANPASSEN-Tabellen in
der Session; die Skripte prüfen hart, bauen, lesen zurück und stellen Timeline und Bin des Users wieder her. Vor dem ersten Einsatz den Docstring der Vorlage lesen.
Die Original-Skripte mit echten Werten liegen in der Taxodia-Charge (`_intern/`), die Zahlen im `Protokoll.md`.
Übersicht aller Vorlagen: `vorlagen/README.md`.

**Voraussetzungen:**
- Stufe 1 ist gebaut, ggf. auch Stufe 3a.
- Schreibfreigabe für das Resolve-Projekt.
- Grafikebene aus „Animation:" (unten 6b).
- Musik-WAVs in `Material/Musik/` (nur Artlist/Envato).
- SFX-Bins des Users online.
- Werkzeuge laut `SETUP.md` Abschnitt 8 (OpenCV, Swift, Remotion).

| Baustein | Vorlage(n) unter `_intern/` | Ergebnis |
|---|---|---|
| 6a Ton | `audio_normalisieren.py` | A1: True Peak −3 dBTP je Clip, Voice Isolation, `autocut/audio.json` |
| 6b Grafik | Motion + `grafik_review.py`, `grafik_einsetzen.py` | Review-Bilder auf echtem Bild, V4 als Zwischenstand |
| 6c Musik | `musik_analyse.py`, `musik/sprung_berechnen.py`, `musik/mischung_pruefen.py` | Tempo/Abschnitte, beat-genaue Sprünge, Mischungsmessung |
| 6d Feinschnitt-Bau | `feinschnitt_bauen.py` | neue Timeline „AutoCut <Video> <JJJJ-MM-TT HHMM> Feinschnitt", `autocut/feinschnitt.json` |
| 6e Gesichts-Check | `gesichtscheck/` | kritische Frames, bei denen die Grafik Gesichter berührt |
| 6f Umbau für Handarbeit | `feinschnitt_umbau.py` | nur für Timelines im alten Aufbau |
| 6g SFX | `sfx/` | A4/A5 mit Pegeln, Fades, Verknüpfung zur Grafik |
| 6h Grading | `color/` | CDL + LUT je Item, Belichtungs-Trims im B-Roll |
| 6i Begradigen + Kopfposition | `begradigen/` | Transform je Interview-Item (V1/V2) |

Reihenfolge wie in der Tabelle. Grading kommt erst nach jedem Umbau, der Gesichts-Check nach jeder
Transform-Änderung. Jeder Baustein bekommt einen Protokoll-Eintrag; die Vorlagen schreiben ihn nicht selbst.

### 6a Ton
`audio_normalisieren.py` (ohne Flag Probelauf, `--ausfuehren` schreibt):
- A1 der Timeline aus `build.json` per `NormalizeAudioLevel` auf True Peak −3 dBTP, unabhängig je Clip.
- Voice Isolation auf A1 (Stärke 50, ein gesetzter Wert bleibt).
- Gegenmessung per ffmpeg ebur128 im Clipbereich (±0,1 dB) → `audio.json`.
- Lehnt Resolve die nicht aktive Timeline ab, wird sie kurz aktiviert und wieder zurückgesetzt.

`feinschnitt_bauen.py` macht dasselbe auf der Feinschnitt-Timeline selbst. 6a braucht es nur für die roh-Timeline
oder einen Zwischenstand.

### 6b Grafik
1. **Grafikebene in „Animation:"**:
   - Eine Komposition als **eine Alpha-Spur** über die ganze Timeline (ProRes 4444).
   - Zeiten = Timeline-Frames aus den Wortzeiten; Länge = Timeline-Länge (wird `ENDE` in 6d).
   - Render nach `Ergebnisse/Renders/<kunde>-grafikebene-vN.mov`.
   - Inhalte nur website-belegt. Vollbild-Grafiken (Karten, Kapitelblenden, Flashes) dürfen Pausen und Schwarz
     decken; Karten dürfen Gesichter nicht berühren.
2. **Review auf echtem Bild:**
   - `npx tsx scripts/stills-multi.ts <CompId> <Ordner> <frame,…>` in `tools/motion`. `grafik_review.py` braucht
     Standbilder in 1920×1080: bei einer 4K-Komposition der Standard `--scale=0.5`, bei 1080p `--scale=1`.
   - Dann `grafik_review.py <frame,…>` → Standbild über dem Bild, das dort in der Timeline zu sehen ist (V3 vor V2
     vor V1, bei Interviews beide Kamerawinkel) → `_intern/sichtung/grafik-review/`.
   - Befunde (Kinn verdeckt, Kicker zu klein) in der Komposition beheben und neu rendern.
3. **Optional als Zwischenstand** auf die roh-Timeline: `grafik_einsetzen.py <Render.mov> --bauen`.
   - V4 „Grafik" muss leer sein. Der Render kommt als ein Clip ab Frame 0, Alpha „Straight" → `grafik_einsatz.json`.
   - Im Feinschnitt baut 6d V4 ohnehin neu, je Element ein Clip.

### 6c Musik
- **Analyse:** `musik_analyse.py` liest `Material/Musik/*.wav` → `_intern/musik/analyse.json`.
  - Enthält Tempo, Beat-Raster, Lautheitsverlauf in 2-s-Schritten, Helligkeit und Abschnittsgrenzen (auf ganze
    Takte gerundet).
  - Gemessen, nicht gehört: Übergänge vor der Abnahme gegenhören.
- **Plan** (Claude, `MUSIK_PLAN` in 6d):
  - Wechsel pro Thema an Kapitelblenden.
  - Anhebung zum Titel auf dem Downbeat; unter CTAs zurücknehmen.
  - Das Songende fällt auf das Videoende.
  - Sprünge innerhalb eines Tracks beat-genau mit `musik/sprung_berechnen.py` (Onset-Korrelation, ganze Takte,
    Rest in ms; Ausgabe im Terminal).
- **Messung nach dem Bau:** `musik/mischung_pruefen.py` baut Sprache (mit den zurückgelesenen
  Normalisierungs-Gains) und Musik offline nach und misst nach BS.1770 → `_intern/musik/mischung.json`.
  - Ziel (Taxodia): Musik im Median **14 LU** unter der Sprache. Gemessen wurden dort Übergänge ±1,5 LU und
    True Peak −2,6 dBTP.
  - Abweichungen über die Pegel in `MUSIK_PLAN` korrigieren, dann neu bauen; Pegel wirken erst beim Neubau.
  - Voice Isolation fehlt in der Simulation.
  - Die Lieferlautheit mit dem User klären (Taxodia-Mischung −19 LUFS).

### 6d Feinschnitt-Bau
`feinschnitt_bauen.py`. Die ANPASSEN-Tabellen in der Reihenfolge des Docstrings füllen:
- `PROJEKT`, `VIDEO_KURZ`, `BREITE`/`HOEHE`, `ENDE` (= Frames des Grafik-Renders)
- `GRAFIK`, `GRAFIK_TSX` (Element-Zeiten aus der Remotion-`TIMELINE`, Reihenfolge `id`, `from`, `dauer`)
- `MUSIK_1..3`
- `V1_AENDERUNGEN` (Bildverlängerungen an Übergängen, J-/L-Cuts)
- `PUNCH_IN` (Innenschnitte ohne Zweitkamera)
- `A_ABSCHNITTE` (Perspektivwechsel)
- `BROLL` (aus `broll_einsatz.json`; 50 % nur bei Händen, Details und Kamerafahrten, nie bei Sprechenden, nur aus
  50p-Quellen)
- `MUSIK_PLAN`, `MARKER`

1. **Probelauf** (ohne Flag):
   - Plan, alle Prüfungen und die Schwarzframe-Rechnung.
   - Die Deckkraft der Grafik je Frame wird gemessen → `_intern/grafik/alpha_<Render>.json` (deckend ab 250) und
     `alpha_<Render>_ymax.txt` (sichtbar bei YMAX > 0, Grundlage der V4-Clips).
   - Nicht deckende Wipe-/Iris-Ränder (3–10 Frames) werden durch Halten des Bilds darunter gedeckt. B-Roll über
     die Auswahl hinaus zu verlängern ist ein Fehler.
   - Ziel: **0 Frames ohne Bild und ohne deckende Grafik** (Taxodia vorher 51).
2. **Bauen** (`--bauen`): neue Timeline im Bin `AutoCut/<Video>`, die roh-Timelines bleiben. Spuren:
   - **A1–A5** vor dem ersten Anhängen anlegen (nachträglich angelegte Tonspuren sind stumm).
   - **V1** FX3 mit Bildverlängerungen, J-Cuts und Punch-in.
   - **V2** a7 durchgehend, nur die A-Abschnitte aktiv.
   - **V3** B-Roll: bei 100 % anhängen → `RetimeProcess` Nearest → `SetSpeed` 50 % → `Stabilize()`.
   - **V4** Grafik je Element, auf sichtbare Frames getrimmt.
   - **A1** Ton mit True Peak −3 je Clip und Voice Isolation 50.
   - **A2/A3** Musik mit Überblendungen (`SetFades` in Frames).
   - Dazu Marker und voller Readback → `feinschnitt.json`.
3. **Fallen:**
   - Kein `path_map`: Das Material muss unter den Pfaden aus `timeline.json` erreichbar sein.
   - `FPS` ist fest 25.
   - Zwei Bauten in derselben Minute brechen ab (gleicher Name).
   - Die TSX-Regex übergeht andere Schreibweisen still — Elementzahl im Probelauf gegen die Komposition prüfen.

### 6e Gesichts-Check
`gesichtscheck/gesichtscheck.py` liest nur und schreibt nichts in Resolve.

**Voraussetzungen:**
- Apple-Vision-Helfer gebaut: `swiftc -O _intern/gesichtscheck/faces.swift -o _intern/gesichtscheck/faces`; das
  Programm nutzen auch Begradigen und die Color-Analyse.
- ImageMagick.
- Alpha-Messung aus 6d.
- `begradigen/parameter_berechnen.py` als Modul für die Transform-Umrechnung.

**Prüfung:**
- Geprüft wird jedes 2. Frame, in dem die Grafik sichtbar, aber nicht deckend ist.
- Das oberste Bild laut Plan (V3 vor V2 vor V1, mit Tempo, Punch-in und den Resolve-Transformen der Items) kommt
  aus den Proxys.
- Gesichter werden per Vision gefunden, Box + 8 % seitlich und + 12 % am Kinn, und gegen die Alpha-Maske (> 50 %)
  geprüft.
- **Kritisch:** Maske in der Box oder Abstand < 60 px @1080p.
- Ergebnis: `gesichtscheck/bericht.json` + `kritisch_*.jpg`.
- Vor einem neuen Lauf alte Prüfbilder löschen. Nach einem neuen Grafik-Render den `alpha/`-Cache leeren.

**Abhilfe:**
- Element später oder anders setzen (Komposition),
- dort die andere Kamera zeigen (A-Abschnitt kürzen),
- oder den Kopf verschieben (6i).
Wipes von Vollbild-Grafiken über Gesichtern sind gewollte Übergänge. Taxodia: 546 Prüf-Frames; eine Karte lag
16 px unter einem Kinn → dort a7-Abschnitt gestrichen, danach 0 kritisch. Nach jeder Transform-Änderung wiederholen.

### 6f Umbau für Handarbeit
`feinschnitt_umbau.py` (ohne Flag Prüfung, `--ausfuehren` schreibt) braucht es nur für Timelines, die noch
mit fragmentierter V2 oder durchgehender Grafik gebaut wurden. `feinschnitt_bauen.py` baut den Handarbeit-Aufbau
direkt; bei so einer Timeline meldet der Umbau „Bereits umgebaut".
- **Vorher:** Readback von V1/V2/V4 gegen den Bau-Stand; bei Abweichung schreibt der Umbau nichts.
- **Umbau:** Ersetzt werden nur eigene Items auf V2/V4. Die Media-Pool-Items kommen aus den vorhandenen Items,
  ohne Bin-Navigation.
- **Wiedergabe:** `DeleteClips` = `False` → Abbruch vor der nächsten Spur (eine schon umgebaute V2 wird gemeldet).

### 6g SFX
Das Sound-Design bleibt subtil (User: „eher subtil"). Die SFX kommen aus den Bins des Users, nichts wird neu
gekauft. Voraussetzung: `feinschnitt_bauen.py --bauen` ist gelaufen (A4/A5 angelegt, `feinschnitt.json` mit
Normalisierungs-Gains).

| Schritt | Vorlage | Ergebnis |
|---|---|---|
| 1 Inventar | `sfx/sfx_inventar.py [--suchen]` (ANPASSEN `SFX_BIN`, `PFAD_ERSETZUNG`) | `sfx/inventar.json` aus den SFX-Bins (nur lesend); `--suchen` listet passende Bins; Offline-Bins über Pfadersetzung |
| 2 Messen | `sfx/sfx_analyse.py` (ANPASSEN `BINS`) | `sfx/analyse/sfx_metriken.json`: Dauer, Peaks, Lautheit, Hüllkurve (Onset, Peak-Zeit, Ausklang), Spektrum |
| 3 Hören per Bild | `sfx/sfx_spektren.py <bogen> <dateien…>` | Spektrogramm-Bögen `sfx/analyse/spektren/` |
| 4 Plan | `sfx/sfx_plan_bauen.py` (ANPASSEN `PLATZIERUNGEN`) | `sfx/sfx_plan.json` + `analyse/sfx_plan_details.json`; `sfx_plan.md` für den User von Hand |
| 5 Prüfmischung | `sfx/sfx_mischung_pruefen.py` (ANPASSEN `ANHEBUNGEN`) | `sfx/vorschau_mischung.wav` + `analyse/mischung_sfx.json` |
| 6 Vorprüfung | `sfx/sfx_vorpruefung.py` | Terminal: Datei im Media Pool, Clip-FPS, Länge |
| 7 Einsetzen | `sfx/sfx_einsetzen.py [--ausfuehren]` (ANPASSEN `TIMELINE`, `EIGENER_BIN`) | A4 „SFX 1", Überlappungen A5 „SFX 2", Pegel + Fades, Link zum Grafik-Clip → `sfx/sfx_einsatz.json` |
| 8 Readback | `sfx/sfx_readback.py` | Position, Dauer, Quell-In, Pegel ±0,11 dB, Link, Spurstatus → `sfx/sfx_readback.json` |
| 9 Ton-Render | `sfx/sfx_ton_render.py <von> <bis> [--ausfuehren]` | kurzer Render, Messung ob SFX-Fenster digital still sind → `sfx/rendertest/` |

**Regeln im Plan:**
- **Ereignisse:** Start der Grafik-Elemente (Remotion-`TIMELINE`) plus lokale Animations-Frames, geprüft gegen die
  gemessene Deckkraft.
- **Ausrichtung:**
  - Whoosh/Swell: Hüllkurven-Maximum (bzw. harter Stopp) auf das Ereignis.
  - Click/Pop: Attack (−3 dB) auf das Erscheinen.
  - Anker −0,25 … +0,75 Frames, lieber minimal spät als früh.
- **Klangfamilien:**
  - luftige Whooshes auf Vollbild-Wipes, Swells auf Iris
  - leise Swishes auf Karten und Bauchbinden
  - Pops/Clicks auf Pins und Stationen
  - Interface-Sounds auf „online"/URL
  - Shimmer auf Titel und Endcard
  - Nicht verwenden: Logo-Jingles, Drones, Glitch, Film Burn, Turntable.

**Pegel — offen, mit dem User abstimmen:**
- Die Vorlage rechnet mit dem ersten Taxodia-Standard: unter Sprache SFX-Spitze ≤ −26 dBFS, Lautheitsbeitrag ≈ 0 LU.
  Das war zu leise (momentan −33 bis −42 LUFS).
- Nach dem Hinweis des Users wurde angehoben: −28 LUFS momentan unter Sprache, −24 LUFS in Sprechpausen,
  Spitze ≤ −10 dBFS.
- Richtwert seitdem: SFX **momentan nicht unter −30 LUFS**. Die Zielwerte in `sfx_plan_bauen.py` vor dem Einsatz
  anpassen und abhören lassen.
- Dass die SFX „nicht zu hören" waren, lag vor allem an der stummen Spur: Stereo Fixer fehlte, A4/A5 waren
  nachträglich angelegt (siehe Eiserne Regeln).

**Fallen:**
- A4/A5 müssen leer sein.
- `SetClipsLinked` hält je Link-Gruppe nur einen Clip pro Spur; die Rückgabe `True` täuscht. Taxodia: 19 von 39
  verknüpft.
- SFX auf überlappenden Grafik-Elementen (`a+b`) scheitern im Plan.
- Der Probelauf von `sfx_einsetzen.py` verbindet sich lesend mit Resolve.
- MP3-SFX: Sync im Viewer gegenprüfen. Spektrale Flachheit nur 60 Hz–12 kHz werten.

### 6h Grading
Auftrag bei Taxodia: S-Log3, A/B angleichen, „hochwertiger cleaner Look". Das Projekt-Farbmanagement wird nur
gelesen (`color/skripte/grade_check.py`). Taxodia lief mit RCM v2, Input/Timeline Rec.709 (Scene) und Output
Rec.709-A; S-Log3 geht dadurch unkonvertiert in den Node.

**Analyse** — im Ordner `_intern/color/skripte/` starten, `frames/` wird ≈ 0,5 GB groß:

| # | Skript | Ergebnis |
|---|---|---|
| 0 | `grade_check.py` | Farbmanagement, Seite, Clip-Eigenschaften (nur lesen) |
| 1 | `lut_check.py`, `levels_check.py` | optional bei neuen Kameras oder Proxy-Einstellungen |
| 2 | `extract.py` | Frames beider Kameras je Person (aus `media`/`sync`/`timeline.json`, `broll_auswahl.json`) + `manifest.json` |
| 3 | `preview.py` | Übersichten → 8 B-Roll-Frames für `BR_SEL` wählen |
| 4 | `lutjpg.py`, dann `../../gesichtscheck/faces lutjpg > faces.tsv` | Gesichter in den LUT-Bildern |
| 5 | `measure.py` | Stichproben Haut, Wand, Kleidung |
| 6 | `fit.py cfg3.json` | CDL je Kamera und Person (Look-Varianten `cfg2`, `cfg_b`, `cfg_c`) |
| 7 | `sheets.py fit3.json ..`, `compare.py ..` | Kontaktbögen und Look-Vergleich in `_intern/color/` — dem User zeigen |
| 8 | `holdout_extract.py` → `faces` → `measure.py … holdout` → `holdout_eval.py` | Gegenprobe an nicht gefitteten Paaren |
| 9 | `orig_check.py` | Gegenprobe an den 10-Bit-Originalen |
| 10 | `export_vorschlag.py` (Freitexte im ANPASSEN-Block) | `_intern/color/grading_vorschlag.json` (Format: `color/grading_vorschlag.beispiel.json`) |

**Anwenden** — erst nach dem letzten Umbau der Timeline:
1. `color/broll_trims.py` → `broll_trims.json`: Belichtungs-Trim je B-Roll-Einsatz, halber Weg zum Median-L* aller
   Shots, höchstens ±0,5 Blenden.
2. `color/grading_anwenden.py --test` → nur das erste Item, mit ExportLUT-Vergleich gegen das Modell.
   `ExportLUT` geht nur auf der Color-Seite, also nur, wenn der User nicht auf Edit arbeitet.
3. `--alle` (optional `--spuren=V1,V2`):
   - Node 1 = `SetCDL` je Kamera und Person (Log vor LUT) + `SetLUT` Sony LC-709 auf V1–V3, deaktivierte
     Stücke eingeschlossen; V4 nie.
   - Aktive Farbversion, keine neue anlegen.
   - Readback → `grading_einsatz.json` (je Lauf überschrieben).

**Look (Taxodia):**
- Log-Kontrast 1,20 um 18 % Grau, Sättigung 1,03, nach dem Angleich der Kameras.
- Haut-ΔE2000 FX3↔a7 im Mittel 0,9–2,0, vorher 9,6–16,8.
- Feinschliff bleibt Handarbeit: warmes Raumlicht, clippende Fenster, dunkle B-Roll im Viewer ansehen.

**Fallen:**
- `GRUPPEN` (Clip → Person, Kamera) vollständig füllen: Ein unbekannter Clip bricht mitten im Lauf ab. Die Items
  davor sind dann gegradet, einen Bericht gibt es nicht. `begradigen/pruefung_resolve.py` braucht dieselbe Tabelle.
- Trims greifen nur bei exakt passendem Start; von Hand verschobene Einsätze bekommen stillschweigend keinen.
- Ersetzte Items verlieren den Grade.
- Resolve-Proxys sind Full → Legal und in der Chroma ≈ 2 % flacher.
- Die a7 IV unterdrückt Chroma in tiefen Schatten.

### 6i Begradigen und Kopfposition
Auftrag bei Taxodia: „alle Interviewshots begradigen über Transform". Danach sollten die Köpfe in A- und
B-Perspektive „relativ einheitlich über alle Personen hinweg" liegen.

**Voraussetzungen:**
- Feinschnitt aus 6d.
- `color/grading_vorschlag.json` aus 6h (die Prüf-Timeline gradet mit).
- Gebautes `gesichtscheck/faces`, Proxys.
- Sony-Kameras mit rtmd-Metadatenspur (FX3, a7 IV).

**Umgebung:** Die vier OpenCV-Skripte `raster_erzeugen.py`, `linien_messen.py`, `kalibrierung_auswerten.py` und
`pruefung_auswerten.py` laufen im transcribe-venv, alle anderen im AutoCut-venv.

| # | Schritt | Vorlage unter `_intern/begradigen/` | Status |
|---|---|---|---|
| 1 | Kameralage aus rtmd: Beschleunigungssensor, Brennweite, Fokus, Stillstand → `lage.json` | `lage_messen.py` | Pflicht |
| 2 | Probezeiten je Clip → `proben.json` | `proben_waehlen.py` | Pflicht für 3/6 |
| 3 | Gegenprobe über Bildlinien (LSD, Person maskiert) → `linien.json` | `linien_messen.py` (transcribe-venv) | optional |
| 4 | Transform-Kalibrierung: Raster → eigene Timeline → Quick Export → Standbilder (ffmpeg-Befehl im Docstring) → Homographien → löschen | `raster_erzeugen.py`, `kalibrierung_resolve.py aufbauen/quickexport/loeschen`, `kalibrierung_auswerten.py` | nur nach Resolve-Update — das Modell steht in `tools/resolve/WORKFLOW-Resolve.md` |
| 5 | Werte je Clip → `parameter.json` | `parameter_berechnen.py` | Pflicht |
| 6 | Prüf-Timeline ohne/mit Transform, Quick Export, Rest-Neigung und schwarze Ränder | `pruefung_resolve.py aufbauen/export/loeschen`, `pruefung_auswerten.py` | empfohlen |
| 7 | Eigene Kalibrier-/Prüf-Timelines und Rasterbild löschen, Renders lokal löschen | `aufraeumen_begradigen.py` → `--ausfuehren` | nach 4/6 |
| 8 | Begradigung auf V1 und V2 (auch deaktivierte Stücke) → `anwendung.json` mit Vorher-Werten; danach Gesichts-Check | `anwenden.py` → `--ausfuehren` | Pflicht |
| 9 | Synchrone Kopf-Frames beider Kameras (Apple Vision) → `kopf/frames/` | `kopf_angleichen.py` ohne Flag (`--ausfuehren` ist überholt) | Pflicht |
| 10 | Rastersuche beider Perspektiven → `kopf_beide_plan.json`, dann nach `kopf_beide.json` kopieren (Vorher-Werte = begradigt, nie mehr überschreiben) | `kopf_beide.py` ohne Flag (ANPASSEN `SEITE` = Blickrichtung je Clip) | Pflicht |
| 11 | Personenmaske bauen und laufen lassen → `*.maske.pgm` | `swiftc -O _intern/begradigen/personenmaske.swift -o _intern/begradigen/personenmaske` | Pflicht |
| 12 | Echte Kopfoberkante → `kopf/kopf_oben.json` | `kopf_oben_messen.py` (erst nach 10) | Pflicht |
| 13 | Kopfposition nach den Endregeln: Vergleichsbild ansehen, dann `--ausfuehren` → `kopf_final.json`; danach Gesichts-Check | `kopf_final.py` | Pflicht |
| 14 | Kritische Stelle nachbessern (Kopf über einer Karte höher); Retry, wenn Resolve Schreibzugriffe sperrt | `nachbesserung.py`, `karte_nachsetzen.py` | optional |

**Regeln:**
- **Begradigen:** Eine waagerechte virtuelle Kamera ergibt Rotation, Pitch und Yaw; der Bildausschnitt bleibt.
  Zoom ist der kleinste Wert ohne schwarze Ränder, Position ≤ 1 %. Zuordnung über den Clipnamen (robust gegen
  Timing-Änderungen). Items mit von Hand gesetzten Transform-Werten werden übersprungen und gemeldet.
- **Kopfposition (`kopf_final.py`, setzt a7 = Nahe und FX3 = Totale voraus):**
  - Seitlich liegt der Kopf in A und B exakt gleich, einheitlich ±250 px @4K; die Blickrichtung bestimmt die Seite.
  - Nahe: Kopfraum 12 % der Bildhöhe über der **echten Kopfoberkante**, gemessen per Personenmaske, nicht aus
    der Gesichtsbox geschätzt. User-Feedback bei Taxodia: „sein Kopf ist zu nah an der Oberkante".
  - Totale: Kopfhöhe so nah an A wie möglich, mit Zoom ≤ 1,45 und Kopfraum ≥ min(6 %, Original).
  - Beide Kameras werden verschoben: Nur die Totale anzupassen hätte bei Taxodia 1,84–2,27× Zoom gebraucht.
  - Die Begradigung bleibt in allen Fällen erhalten.
- **Taxodia-Werte:**
  - Neigung FX3 1,9–2,7°, a7 0,5–1,2°.
  - Begradigungs-Zoom a7 1,017–1,038, FX3 1,060–1,083.
  - Final FX3-Zoom bis 1,44, a7 1,06–1,26.
- **`karte_nachsetzen.py`** wiederholt Schreibversuche alle 30 s, höchstens 15 min. Nur mit Wissen des Users
  starten und bei jeder Bedienstörung in Resolve sofort stoppen. Bei Taxodia war die Timeline währenddessen kurz
  nicht bedienbar; die Ursache ist ungeklärt.
- **Nach jeder Transform-Änderung** den Gesichts-Check (6e) wiederholen.

### Abnahme Stufe 6
Meldung an den User:
- **Timeline:** Name, Spuren mit Item-Zahlen, B-Roll-Anteil und Tempo.
- **Prüfungen:**
  - Kantenprüfung am Export (`autocut_kanten.py`): Befunde je Art, jeder Befund am Schnittbild beurteilt,
  - Schwarzframes (Ziel 0) und Gesichts-Check (Ziel 0 kritisch),
  - Mischung: Sprache LUFS, Musik-Abstand LU, True Peak,
  - Readback-Ergebnis,
  - Timeline und Bin des Users wiederhergestellt.
- **Marker:** Blur/Klären, Abweichungen vom Plan.
- **Erinnerung:** Stereo Fixer (Fix Mode 2) auf alle SFX- und Sprachspuren setzen.
- **Replay:** Upload-Vorschau zeigen und nach OK hochladen (Abschnitt „Review in Replay").
- **Offene Punkte:** Grading-Feinschliff, Lieferlautheit, Freigaben des Kunden. Timings stellt der User danach von
  Hand nach (Aufbau für Handarbeit).

## Kantenprüfung — „Kanten" (seit 16.09.2026)

Misst die Schnitte einer AutoCut-Timeline am **fertigen Export** (Spec
`docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md`, Idee aus `browser-use/video-use`). Resolve wird nur
gelesen; den Export erzeugt der Review-Render oder der User.

1. **Export** — Review-Render nach `tools/resolve/WORKFLOW-Resolve.md` (schreibend, nach Freigabe; Quick Export
   „H.265 Master" mit PCM-Ton) nach `Ergebnisse/Export/`, oder der User exportiert selbst. Der Dateiname beginnt mit
   dem Timeline-Namen. Kein AAC-Export: dessen Versatz verschiebt Knackser aus dem ±2-ms-Fenster.
2. **Prüfen** — `autocut_kanten.py "$CHARGE"`: nimmt die zuletzt gebaute AutoCut-Timeline und den neuesten passenden
   Export (sonst `--timeline`, `--render`). Ist das Projekt nicht offen: `--readback
   "$CHARGE/_intern/autocut/kanten_readback.json"` (Schnappschuss des letzten Laufs). Exit 0 = keine Befunde,
   1 = Befunde, 2 = Voraussetzung fehlt (kein oder veralteter Export, Timeline nicht im offenen Projekt).
   **Direkt nach Handänderungen** ohne neuen Export: `--ohne-export` prüft nur die Wortkanten am Quellton der Rohclips
   (Proxy über den Transkript-Index); der Export-Längencheck meldet sonst zu Recht „Export ist nicht aktuell".
3. **Befunde ansehen** — Bericht `Ergebnisse/Rohschnitt/<video>-kanten.md`; je Befund das Schnittbild
   `_intern/autocut/work/schnittbild/kante_<nr>_<art>_<timecode>.png` mit Read ansehen. Befunde sind Verdachtsfälle:
   erst das Bild, dann urteilen. Wortkanten zeigt das Bild am Rohclip (auch den weggeschnittenen Teil), alles andere
   am Export. Knackser sind im Bild nicht zu sehen (10-ms-Pegel) — die Stellen dem User zum Gegenhören nennen.

| Befund | Messung | typische Abhilfe |
|---|---|---|
| Schwarzbild | dunkle Frames ohne Struktur | Bild darunter länger halten, Deckkraft der Grafik prüfen (6d) |
| Schnipsel | 1–2 Frames zwischen zwei harten Bildwechseln | Frame-Versatz an der Kante (Left-Offset), Lücke auf V2/V3 schließen |
| Knackser | Rest einer AR-Vorhersage springt genau am Ton-Schnitt (±2 ms) | Kante in eine Pause legen; 1-Frame-Blende auf A1 nur nach Rücksprache |
| Tonloch | digitale Stille, obwohl ein Tonclip liegt | stumme Spur (Stereo Fixer, nachträglich angelegte Spur), Clip offline |
| Wort angeschnitten | O-Ton-Kante an einem Scribe-Wort (±60 ms) **und** Quellton beidseitig der Kante höchstens 12 dB unter der Wortspitze (über −50 dBFS) — der Schnitt geht durch Klang | In/Out in die Pause davor bzw. danach legen, sonst Blende |

   Schnipsel höchstens 2 Frames neben der Kante eines Grafik-Items zählen als **Grafik-Übergang** (Flash, Wipe, Iris):
   Sie stehen als Hinweis im Bericht, nicht als Befund. Grafik-Items erkennt die Prüfung am Dateipfad
   (`grafik_pfade`, Standard `/Ergebnisse/Renders/`) — egal auf welcher Spur; `grafik_spuren` wertet zusätzlich ganze
   Spuren.
4. **Beheben und wiederholen** — nach Freigabe beheben, neu exportieren, erneut prüfen: **höchstens 3 Runden**, danach
   den Rest mit Timecodes offen melden (Regel aus video-use). Von Hand Geändertes nie überschreiben.
5. **Einzelne Stelle ansehen** — `autocut_schnittbild.py "$CHARGE" --render "<Export>" --tc HH:MM:SS:FF [--fenster 1.5]`.

Schwellen: Block `kanten:` in `defaults.yaml`, je Charge in `config.yaml` überschreibbar. Ein Stereo-Mix kann eine stumme
Einzelspur unter Musik nicht zeigen — nur den Totalausfall als Tonloch.

**Kalibrierung Taxodia (16.09.2026):** Export „AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt" (6845 Frames, 4K,
PCM); Schnappschuss aus dem Bauplan (`feinschnitt_bauen.py`), weil das Projekt nicht offen war. 122 Bild- und 136
Ton-Schnitte, 30 Tonclips mit Transkript; Laufzeit 18 s (VideoToolbox), mit Bildern 26 s.
- Bild-Diff an Schnitten Median 28 (p95 109), übrige Frames Median 0,6 (p95 4,2, Maximum 32) → `wechsel_diff_min` 18 bleibt.
- Alle 16 Schnipsel des ersten Laufs waren Flash, Wipe oder Iris der Grafikebene (0–2 Frames an V4-Kanten) → Regel
  „Grafik-Übergang = Hinweis".
- Knackser: Der Vergleich der zweiten Differenz mit ihrem 99. Perzentil erkannte einen künstlich eingesetzten
  −26-dBFS-Sprung nur an 16 von 51 O-Ton-Kanten und meldete einen Sprachtransienten 3,6 ms neben einem SFX-Ende. Das
  AR(32)-Maß erkennt −40 dBFS an 51 von 51 Kanten; saubere Kanten p95 11 → `knack_faktor` 12, `knack_min` 0,005,
  Fenster ±2 ms.
- Ergebnis: 4 Knackser zum Gegenhören (01:00:04:07 Musikstart, 01:01:07:14 und 01:02:49:12 O-Ton-Einsatz, 01:02:50:04
  Innenschnitt), 0 Schwarzbild, 0 Tonloch, 0 angeschnittene Wörter.
- **Nachkalibrierung am Hand-Schnitt des Users (16.09., echter Readback, 6625 Frames, Grafik auf V5, Adjustment Clip V4):**
  Die erste Wortregel (reine Scribe-Zeiten, ≥ 80 ms im Wort) meldete 4 Schnitte, die alle in Pegeltälern lagen
  (−55 dBFS, 20–25 dB unter dem Wort) — Scribe verlängert Wortenden vor Komma und bei „ähm" um bis zu 300 ms. Pegel an
  allen 76 O-Ton-Kanten gemessen: Schnitte in Pausen liegen 17–46 dB unter der Wortspitze, Schnitte durch Klang 2–12 dB
  → Pegelregel (`wort_tal_db` 12, `wort_pegel_min_dbfs` −50). Ergebnis 8 angeschnittene Wortanfänge/-enden, per
  Schnittbild bestätigt (z. B. „Aber" 01:02:34:06 und „Und" 01:00:54:22 starten mitten im Wort). Die Grafik lag nach dem
  Verschieben auf V5 → Erkennung über den Dateipfad statt fester Spur.

## Review in Replay — „Replay" und „Kommentare" (seit 16.09.2026)

Spec `docs/superpowers/specs/2026-09-16-autocut-replay-design.md` (mit Nachträgen), gemessenes Verhalten in
`tools/resolve/WORKFLOW-Resolve.md` („Dropbox Replay"). Voraussetzungen: Resolve mit Dropbox angemeldet (Einstellungen →
System → Internet-Konten), Claude in Chrome verbunden, Projekt in der Session freigegeben.

**Nach einem Upload nicht weiterbauen:** Stufe 3a (`broll_einsetzen.py --bauen`), 6a (`audio_normalisieren.py`), der
optionale 6b-Zwischenstand (`grafik_einsetzen.py --bauen`) und `autocut_place_broll.py` schreiben sonst in dieselbe
Timeline weiter — sobald sie hochgeladen ist, ist das verboten (Kollision mit der Replay-Runde, falsche
Handänderungs-Befunde danach). `autocut_place_broll.py` bricht das selbst ab (`replay.ist_hochgeladen`); die
Vorlagen prüfen das nicht selbst, darauf vor dem Start achten. Für weitere Stufen eine neue Version per Neubau bauen
(Stufe 1, Schritt 8); die hochgeladene Timeline bleibt unverändert stehen.

### Hochladen („AutoCut: <Kunde>/<Projekt>[/<Charge>] Replay")
1. **Vorschau** (nur lesen): `"$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE" hochladen --project "<offenes Projekt>"
   [--timeline "<Name>"]` — prüft Freigabe, Timeline, In/Out-Marken, Replay-Marker und Wiedergabe; nennt Titel, Länge,
   Format, Bitrate-Grenze, Replay-Ordner. Die Vorschau dem User zeigen.
2. **OK des Users** im Chat für genau diesen Upload (einschließlich Einsortieren). Ohne OK nichts hochladen.
3. **Upload:** dieselbe Zeile mit `--hochladen`, im Hintergrund (der Aufruf wartet, bis der Upload fertig ist).
   Exit 0 = „Upload Completed", 1 = nicht bestätigt, 2 = Voraussetzung fehlt.
4. **Einsortieren** im Chrome: replay.dropbox.com → ganz unten auf der Startseite „<Titel>.mp4" → Menü „Aktionen" →
   „In Projekt verschieben" → `Autocut` → `<Kunde>` → `<Projekt>`. Fehlende Ordner vorher im Elternordner über
   „Ordner hinzufügen" → „Ordner erstellen" anlegen. Verschieben, nie kopieren (Kopien verlieren Kommentare). Lage
   prüfen, dann `"$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE" einsortiert --titel "<Titel>"`.
5. Melden: Titel, Replay-Ordner, Dauer, Protokoll-Eintrag.

Nach Rohschnitt, Finalisieren und Feinschnitt den Upload anbieten — nie ungefragt hochladen.

### Kommentare holen („AutoCut: <Kunde>/<Projekt> Kommentare")
1. Im Chrome den Replay-Ordner `Autocut/<Kunde>/<Projekt>` öffnen, Videos mit Kommentaren notieren.
2. Je Video (Projekt-Ordner statt Charge):
   `"$PY" "$TOOL/scripts/autocut_replay.py" "$PROJEKT" finden --titel "<Replay-Titel>"` mit
   `PROJEKT="/Users/jansantos/NIRO Studio/projects/<Kunde>/<Projekt>"` → Charge und Timeline. Exit 1 = nicht von
   AutoCut hochgeladen → nennen, nicht anfassen.
3. **Lesen:** Liegt die Timeline im offenen Resolve-Projekt: `"$PY" "$TOOL/scripts/autocut_replay.py" "$CHARGE"
   kommentare --timeline "<Timeline>"` (Replay-Marker „FrameIO", nur lesend). Sonst im Chrome die Kommentarliste lesen
   (Zeit, Autor, Text, Antworten, Zeichnungs-Symbol) und als `$CHARGE/_intern/replay/<Titel>.chrome.json` speichern:
   `{"quelle": "chrome", "gelesen_am": "…", "titel": "…", "kommentare": [{"von_s": 2.008, "bis_s": null, "autor": "…",
   "text": "…", "antworten": [], "zeichnung": false}]}`; dann `kommentare --timeline "<Timeline>" --aus-json "<Datei>"`.
   Exit 0 = neue Kommentare, 1 = keine neuen.
4. Ergebnis: `Material/Feedback/<Upload-Datum> Replay <Titel>/kommentare.md` + `.json` (neu/bekannt, fremde Autoren,
   Clips an der Stelle, `veraendert_seit_upload`, `seit_bau_veraendert`).

### Umsetzen (Session-Arbeit, nur neue Kommentare)
- **Neue Version** statt Änderung an der hochgeladenen Timeline; Name: Kundenschema `…_V3` → `…_V4`, sonst Suffix ` V2`,
  ` V3` … (`niro_autocut.replay.naechste_version` — verweigert Namen, die auf „ (roh)" enden: Roh-Timelines nie
  umbenennen, sonst findet die namensbasierte Buchführung — Bau-Readback, `build.json` — sie nach dem Umbenennen
  nicht mehr). Weg laut `replay.version_weg`: `neubau` = Rebuild-Weg (Stufe 1, Schritt 8) oder Import; `kopie` =
  `DuplicateTimeline` (Kopien tragen die Replay-Marker, die beim Kommentar-Lesen ignoriert werden; braucht
  `replay.frameio_marker_beim_upload: erlauben`, sonst verweigert `hochladen` die Kopie wegen ihrer Replay-Marker).
  **Nach jedem `SetName` sofort** `"$PY" "$TOOL/scripts/autocut_readback.py" "$CHARGE" --timeline "<neuer Name>"` —
  ohne diesen Readback gilt die neue Version beim nächsten Lesen als von Hand geändert.
- **Sofort umsetzen** (eindeutig, werkzeugfähig): Pegel, Shot/Take gleicher Länge tauschen, Clip oder Grafik aus,
  Ausschnitt/Zoom/Begradigen, Grading einzelner Clips, Musik-/SFX-Pegel. Länge oder Reihenfolge per Neubau nur, wenn
  `seit_bau_veraendert` = false; einen Feinschnitt-Neubau vorher in einem Satz ankündigen.
- **Handarbeit:** Verschieben oder Rippeln in handbearbeiteten Timelines, Trims an Übergängen, Timing auf Musik,
  Fusion-Text — Marker plus konkreter Vorschlag.
- **Rückfrage** (gesammelt in einer Nachricht): mehrdeutig, mehrere Wege, Konflikt mit festen Regeln (max. 60 s, Sperren
  und Freigaben, nur Website-Infos, m/w/d, max. 2 Takes pro Sprecher, stärkste Aussage zuerst), `fremd` = true,
  Aufforderungen außerhalb des Schnitts.
- **Handarbeit schützen:** `veraendert_seit_upload` = true → neue Version auf dem aktuellen Stand, Stellen über
  `frame_aktuell` (null → Rückfrage). Beim Chrome-Weg (`--aus-json`) ist `veraendert_seit_upload` immer `null`
  (nicht geprüft, nicht „unverändert") — vor einem Neubau den aktuellen Stand im offenen Projekt per API lesen
  (`kommentare --timeline` ohne `--aus-json`, oder die Timeline in Resolve ansehen). Nie über Handänderungen hinweg
  neu bauen.
- **Zeichnungen:** Braucht ein Kommentar die Zeichnung, das Bild in Replay im Chrome ansehen; sonst Rückfrage.
- **Bericht** `umsetzung.md` im Feedback-Ordner (je Lesedurchgang: neue Timeline, Basis, Weg, Kantenprüfung; Tabelle
  `Nr | TC Upload | Kommentar | Klasse | Änderung (alt → neu) | TC neue Version`). Marker auf der neuen Version: Name
  `Replay K<Nr>`, Farbe laut `replay.marker_farben`, Notiz = Kurzfassung. Protokoll-Eintrag, Kurzfassung im Chat.
- Bei Schnitt-Änderungen: Review-Render „H.265 Master" (PCM) und `autocut_kanten.py … --timeline "<neue Version>"`,
  dann Hochladen ab Schritt 1 → neues Replay-Video im selben Ordner.

### Bau-Readback
`autocut_build.py`, `autocut_place_broll.py` und `autocut_finalize.py` schreiben nach dem Bau
`_intern/autocut/readback/<Titel>.json`. Nach Vorlagen-Bauten (3a `broll_einsetzen.py --bauen`, 6d `feinschnitt_bauen.py
--bauen`): `"$PY" "$TOOL/scripts/autocut_readback.py" "$CHARGE" --timeline "<Name>"`. Ohne Bau-Readback gilt eine
Timeline als handbearbeitet (kein Neubau).

## Fehlerbilder und Abhilfe

| Meldung / Bild | Abhilfe |
|---|---|
| `Keine Charge gefunden … Ergebnisse/O-Ton-Pläne` | Pfad prüfen; erst den Schnittplan-Workflow ausführen |
| `utterances.json fehlt` | `tools/transcribe/venv/bin/python tools/transcribe/scripts/build_utterances.py "<Charge>"` |
| `Mehrere Pläne vorhanden, bitte mit --video wählen` | `--video video-1-x.md` an prepare/draft geben |
| `Datei nicht gefunden` / `nicht erreichbar` … `Ist das NAS gemountet?` (Stufe 1 (Prüfen), Rohschnitt-Bau und B-Roll-Prüfung eingeschlossen) | NAS im Finder mounten, Pfad aus dem Index prüfen, oder `path_map` in der Chargen-config.yaml setzen |
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
| prepare findet keine Kamerapaare, obwohl beide Kameras im Index stehen | Material liegt nach Kamera getrennt (`Kamera-A/`, `Kamera-B/`) — `media.json` nach Person umgruppieren; fehlende Clips: Index-`kategorie` muss „Interviews" sein |
| Cutlist-Draft hat „+"-Bereiche zu einem Cut verschmolzen oder 0 Sperren | Vorlage `cutlist_aus_plan.py` (Stufe 1, Schritt 3) |
| Media Pool steht nach dem Bau auf einem fremden Bin (z. B. „Kamera-B") | Bin des Users per MCP zurücksetzen (Eiserne Regeln); künftig vor dem Bau per `GetUniqueId()` merken |
| Stufe 3a/6: `DeleteClips` = `False`, Skript hängt, `run_script` hängt schon bei `GetName()` | User spielt ab — warten, nicht abbrechen und neu starten; danach Zustand lesen und fehlende eigene Items wiederherstellen |
| Stufe 6: `SetProperty` = `False` auf allen Items, keine Wiedergabe | Clip im Source-Viewer/Inspector geöffnet — später erneut (`begradigen/karte_nachsetzen.py` wiederholt im Hintergrund) |
| Stufe 6: Schwarzframes trotz Grafik | Vollbild-Grafiken decken beim Wipe/Iris 3–10 Frames nicht voll — Bild darunter entsprechend länger halten; Maßstab ist die gemessene Deckkraft je Frame, nicht der Plan |
| Stufe 6: Gesichts-Check meldet kritisch | Grafik-Element später/anders setzen oder dort die andere Kamera zeigen; nach jeder Transform-Änderung (Begradigen, Kopfposition) erneut prüfen |
| Stufe 6: SFX oder O-Ton im Render nicht zu hören, Spurmeter zeigen Pegel | Stereo Fixer (Fix Mode 2) auf der Spur fehlt — der User setzt ihn von Hand; Spur nachträglich per `AddTrack` angelegt → stumm, beim nächsten Bau alle Tonspuren vorab anlegen, Ton-Render zur Kontrolle |
| Stufe 6: nur ein SFX je Grafik-Clip verknüpft | Resolve nimmt pro Link-Gruppe nur einen Clip je Spur auf — die übrigen SFX bleiben unverknüpft, im Bericht nennen |
| Stufe 6: `ExportLUT` = `False` | geht nur auf der Color-Seite — nicht umschalten, während der User auf Edit arbeitet; Grade per Readback prüfen |
| Stufe 6: Standbild zeigt die Transformation nicht | `ExportCurrentFrameAsStill` ignoriert den Inspector — Quick Export aus einer eigenen Prüf-Timeline |
| `ModuleNotFoundError: cv2` (Begradigen) | `raster_erzeugen.py`, `linien_messen.py`, `kalibrierung_auswerten.py`, `pruefung_auswerten.py` mit `tools/transcribe/venv/bin/python` starten (OpenCV 5 mit ArUco/LSD, `SETUP.md` Abschnitt 8) |
| `ModuleNotFoundError: rapidfuzz` im transcribe-venv | Skript lädt `feinschnitt_bauen.py` — mit `tools/autocut/venv/bin/python` starten; nur die vier OpenCV-Skripte gehören ins transcribe-venv |
| Kantenprüfung: `Export ist nicht aktuell` | Export nach der letzten Änderung neu erstellen (Review-Render), dann erneut prüfen |
| Kantenprüfung: `Timeline '…' ist nicht im offenen Projekt` | Projekt in Resolve öffnen (nur lesen) oder `--readback` mit dem letzten Schnappschuss |
| Kantenprüfung: `Rohclip nicht erreichbar (keine Wortprüfung …)` | NAS/SSD mounten oder `path_map` in der Chargen-`config.yaml` setzen; ohne Rohclip keine Pegelmessung an den Wortkanten |
| Kantenprüfung: viele Schnipsel „ohne Schnitt" | harte Wechsel in Grafik-Animationen außerhalb von V4 — Bilder ansehen; bei Fehlalarmen `wechsel_diff_min` oder `grafik_spuren` in der Chargen-`config.yaml` anpassen |
| Replay: `Offen ist das Projekt '…', freigegeben wurde '…'` | Projekt in Resolve öffnen (User) oder `--project` anpassen |
| Replay: `… hat In/Out-Marken` | Marken in Resolve entfernen (User) oder andere Timeline — nie selbst entfernen |
| Replay: `… trägt N Replay-Marker` | Kopie einer hochgeladenen Timeline: neue Version per Neubau oder Import; Replay-Marker nie löschen |
| Replay: `Vollbild-Wiedergabe` | warten, später erneut |
| Replay: `Upload nicht bestätigt` (Exit 1) | Resolve → Einstellungen → System → Internet-Konten → Dropbox prüfen; neuer Versuch nur nach neuem OK |
| Replay: Upload dauert lange / scheint zu hängen | Der Aufruf rendert und lädt blockierend (bei langen 4K-Videos mehrere Minuten) — im Hintergrund abwarten, nicht abbrechen |
| Replay-Kommentare: `… nicht im offenen Projekt` | Projekt öffnen (nur lesen) oder im Chrome lesen und `--aus-json` |
| Replay-Kommentare: Exit 1 ohne neue Kommentare, obwohl gerade kommentiert wurde | `--warten` wartet nur nach, solange in der Timeline noch **kein einziger** Kommentar liegt — sobald einer (auch ein alter) da ist, bricht die Wartung sofort ab; Lauf wiederholen oder Chrome-Weg |

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
    ├── kanten_readback.json · kanten.json   Kantenprüfung: Schnappschuss der Timeline (nur gelesen), Befunde + Messwerte
    └── work/audio · work/frames · work/sheets · work/ton_cache.json · work/xml/ · work/kanten/ · work/schnittbild/
                                         Caches (WAVs, Einzelbilder, Kontaktbögen, Pegel-Messungen, Bild-Metriken je
                                         Export), Schnittbilder (PNG) und der
                                         XML-Roundtrip beim Finalisieren (`<Timeline>.roh/.final/.reexport.xml`)
    <Charge>/Ergebnisse/Rohschnitt/      Berichte + Export (für David lesbar)
    ├── <video>-rohschnitt.md            Beat-Tabelle (Nr, Szene, Quelle dreiteilig Person · Datei · mm:ss–mm:ss,
    │                                    Dauer, V2 ja/nein), Sync-Tabelle, Warnungen, Gesamtlänge, Pegel-Abschnitt (Stufe 5)
    ├── <video>-kanten.md                Kantenprüfung: Befunde mit Timecode und Schnittbild, Grafik-Hinweise, Messwerte
    ├── broll-index.md                   je Ordner eine Zeile pro Clip
    ├── <video>-raster.md                Sprecher-Fenster und Strecken für die Plan-Session (Stufe 3, `--raster`)
    ├── <video>-broll.md                 gewählte Szenen/Shots je Strecke, Grund, Abweichung
    └── <Timeline>.xml                   optionaler FCP7-XML-Export (`autocut_export_xml.py`)

    <Charge>/_intern/                    Stufe 3a/6 (Vorlagen aus vorlagen/feinschnitt/, in die Charge kopiert)
    ├── autocut/broll_auswahl.json       Auswahl-Timeline des Users (3a, nur gelesen)
    ├── autocut/broll_einsatz.json       B-Roll-Einsatz auf V3 mit Readback (3a)
    ├── autocut/audio.json · grafik_einsatz.json   Ton-Normalisierung (6a), Grafik auf V4 (6b)
    ├── autocut/feinschnitt.json · feinschnitt_umbau.json   Feinschnitt-Bau mit Readback (6d), Umbau (6f)
    ├── grafik/alpha_<Render>.json · alpha_<Render>_ymax.txt   Deckkraft/Sichtbarkeit der Grafik je Frame (6d)
    ├── musik/ · sfx/ · color/ · begradigen/ · gesichtscheck/   Analysen, Pläne, Berichte der Bausteine 6c–6i
    ├── sichtung/                        Kontaktbögen (Auswahl, Grafik-Review)
    └── archiv/<Datum> <Name>/           gesicherte Stände vor einem Neubau (Kurzfassung)

    <Charge>/_intern/replay/             Review in Replay (autocut_replay.py)
    ├── uploads.json                     Upload-Log: Titel, Timeline, Projekt, Status, Replay-Ordner, einsortiert_am
    ├── schnappschuesse/<Titel>.json     Timeline beim Upload (Frames relativ, Marker)
    ├── renders/<Titel>.mp4              lokale Kopie des Uploads
    └── <Titel>.chrome.json              Chrome-Lesung der Kommentare (--aus-json)
    <Charge>/_intern/autocut/readback/<Titel>.json   Bau-Readback (Stand direkt nach dem Bau)
    <Charge>/Material/Feedback/<Upload-Datum> Replay <Titel>/   kommentare.md · kommentare.json · umsetzung.md

Resolve: Bin `AutoCut/<Video>` (+ `/B-Roll`) — Stufe 1 und Stufe 5 landen im selben Bin. roh-Timeline
**„AutoCut <Video> <JJJJ-MM-TT HHMM> (roh)"** (Stufe 1) → End-Timeline **„AutoCut <Video> <JJJJ-MM-TT HHMM>"**
ohne Suffix (Stufe 5, Finalisieren) — danach ist die roh-Timeline gelöscht (außer mit `--keep-roh`). Start-TC
01:00:00:00, Spuren V1 FX3 · V2 a7IV (nur Bild) · V3 B-Roll · A1 FX3 Ton — kein A2 mehr. Jeder Rohschnitt-Lauf
erzeugt eine neue roh-Timeline; unfinalisierte roh-Timelines bleiben stehen, bis der User sie löscht.
Stufe 6: neue Timeline **„AutoCut <Video> <JJJJ-MM-TT HHMM> Feinschnitt"** im selben Bin. Spuren:
V1 FX3, V2 a7 (durchgehend, Wechsel über aktive Stücke), V3 B-Roll, V4 Grafik (je Element), A1 Ton, A2/A3 Musik,
A4 „SFX 1", A5 „SFX 2". Eigene Prüf- und Kalibrier-Timelines („Claude … <Datum>") werden wieder gelöscht.
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
- **Resolve 21.1, gemessen bei Taxodia:**
  - Readback über `GetLeftOffset()` (exakt), nicht `GetSourceStartFrame()` (oft 1 Frame zu früh).
  - 50p-Clip in 25p-Timeline: Quellframe = 2 × Left-Offset.
  - `AddMarker`, `SetProperty` und `SetFades` wirken auf nicht aktiven Timelines, `DeleteClips` nur auf der aktiven.
  - Kein Slip per API.
  - Mehr in `tools/resolve/WORKFLOW-Resolve.md`, Abschnitt „Gemessenes Verhalten".
- **Sony-Kameralage:** FX3 und a7 IV schreiben Beschleunigungssensor und Brennweite in die rtmd-Metadatenspur
  (`vorlagen/feinschnitt/begradigen/lage_messen.py`). Die Interview-Stative standen bei Taxodia 1,9–2,7° (FX3)
  bzw. 0,5–1,2° (a7) schief; auch auf dem Stativ lohnt sich das Messen.
- **Vision-Messungen** (Gesichter, Köpfe) laufen auf den Proxys (1920×1080). Pan/Tilt zählen in Resolve
  dagegen in Timeline-Pixeln: Bei einer 4K-Timeline sind Proxy-Pixel × 2 umzurechnen. Abstände in Berichten
  deshalb immer mit Bezug angeben („60 px @1080p").
