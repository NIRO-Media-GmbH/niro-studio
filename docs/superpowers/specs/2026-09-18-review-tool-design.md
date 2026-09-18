# NIRO Review — lokales Review-Werkzeug (Spec)

Datum: 2026-09-18 · Status: Entwurf, Weichen mit dem User abgestimmt (Chat 18.09.: Ablage in einem eigenen
Review-Ordner auf dem NAS mit lokalem Cache, Server als LaunchAgent „immer an", Kommentare als Text an Zeitpunkt
oder Bereich, kein Zeichnen).

## Anlass

Der User will Claude-Stände (Rohschnitte, Feinschnitte, Entwürfe, Animationen) wie in Dropbox Replay oder Frame.io
begutachten: übersichtlich nach Kunde und Projekt, Kommentare an der Stelle im Video, danach „fertig" sagen, Claude
setzt um, eine neue Version erscheint, bis alles freigegeben ist. Reviews passieren immer am Studio-Mac; der
Zweit-Mac (MacBook, `/Users/sergio/NIRO Studio`) muss dieselben Kommentare sehen und eigene Videos einreihen.

Dropbox Replay bleibt das Werkzeug für **Kunden**-Feedback (`tools/autocut/WORKFLOW-AutoCut.md` „Review in Replay").
Das neue Werkzeug ist der **interne** Kreislauf User ↔ Claude — ohne Upload-Grenzen, ohne Dropbox-Anmeldung, ohne
Chrome-Lesung.

## Ziel und Nicht-Ziel

**Ziel**

- Neunte Studio-Funktion „Review": Web-Oberfläche im NIRO-CI unter `http://localhost:4711`, Ordnung Kunde →
  Projekt → Video → Versionen V1, V2 …, Kommentare an Frame oder Bereich, Antworten, Status, „Review abschließen",
  „Freigeben".
- Claude legt Versionen per Befehl ab und meldet den Link im Chat; Claude holt Kommentare per Befehl als
  `kommentare.md`/`.json` in die Charge (`Material/Feedback/…`), setzt um und legt V+1 mit Antworten je Kommentar ab.
- Beide Macs sehen denselben Stand (NAS); Videos vom Zweit-Mac sind am Studio-Mac abspielbar.

**Nicht-Ziel (jetzt)**

- Kunden-Reviews, Freigabe-Links, Login, Nutzerverwaltung.
- Zeichnen im Bild, Bild-an-Bild-Vergleich zweier Versionen, Upload aus dem Browser.
- Automatisches Erkennen fertiger Renders: Claude ruft den Befehl bewusst auf (Regel in CLAUDE.md), kein Watcher.

## Der Kreislauf

1. Claude rendert (Resolve-Export, Remotion, Entwurfs-Pipeline) und legt die Datei ab:
   `python3 tools/review/review.py hinzufuegen "<Charge>" --datei "<MP4>" [--video "<Titel>"] [--version N] [--notiz "…"]`.
   Der Befehl nennt den Link (`http://localhost:4711/#/<Kunde>/<Projekt>`); Claude meldet ihn im Chat.
2. Der User kommentiert im Browser und klickt „Review abschließen" (die Version wird für neue Kommentare gesperrt,
   Status „bei Claude"). Er sagt im Chat Bescheid („fertig" oder Trigger „Review: <Kunde>/<Projekt>").
3. Claude holt die Kommentare: `review.py kommentare "<Charge>" [--video "<Titel>"]` →
   `<Charge>/Material/Feedback/<Datum> Review <Titel> V<n>/kommentare.md` + `.json`, setzt um (Regeln wie im
   Replay-Ablauf: Eindeutiges sofort, Handarbeit melden, Unklares gesammelt fragen — Rückfragen per
   `review.py umsetzung … --datei umsetzung.json` als Status „Rückfrage" in den Kommentar-Thread) und legt die
   nächste Version ab: `hinzufuegen … --version n+1 --umsetzung umsetzung.json` — jeder Kommentar von V<n> bekommt
   Status „umgesetzt" oder „Rückfrage", Claudes Antwort und wahlweise den neuen Timecode.
4. In V<n+1> sieht der User „Seit V<n> geändert" (alle beantworteten Kommentare, Sprung zur neuen Stelle), hakt ab
   („erledigt") oder kommentiert neu. Weiter bei 2, bis er das Video „freigibt".

## Ablage

**Wurzel auf dem NAS**, neben `projects/`, `berichte/`, `claude-gedaechtnis/`, `tools-medien/`:
`/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/review/`
(Umgebungsvariable `NIRO_STUDIO_NAS` wie beim Abgleich; `NIRO_REVIEW_ROOT` setzt die Wurzel direkt, für Tests).

    review/
    ├── <Kunde>/
    │   └── <Projekt>/
    │       └── <Video-Titel>/
    │           ├── video.json          Titel, Sortierung, Charge (relativ), Freigabe
    │           ├── V1/
    │           │   ├── version.json    Datum, Mac, Quelle, Dauer, fps, Auflösung, Notiz, abgeschlossen, geholt_am
    │           │   ├── video.mp4       Review-Kopie (H.264/AAC, browser-tauglich)
    │           │   ├── thumb.jpg       Vorschaubild
    │           │   └── kommentare.json Kommentare des Users + Status/Antworten von Claude
    │           └── V2/ …
    └── _papierkorb/                   entfernte Videos/Versionen (nie hart gelöscht)

- Kunde und Projekt kommen aus dem Chargen-Pfad `projects/<Kunde>/<Projekt>/<Charge>` (Schreibweise wie dort;
  `--kunde`/`--projekt` überschreiben). Videos mehrerer Chargen desselben Projekts liegen unter einem Projekt; die
  Charge steht am Video.
- Ordnernamen werden NFC-normalisiert gelesen und geschrieben; beim Nachschlagen zählt der normalisierte Vergleich
  (macOS legt Umlaute als NFD ab — bekannte Falle).
- Versionen sind unveränderlich: `video.mp4` einer Version wird nie ersetzt; ein neuer Render ist eine neue Version.
- **Lokaler Cache** je Mac: `~/Library/Caches/NIRO Review/<Kunde>/<Projekt>/<Video>/V<n>/video.mp4` (+ `thumb.jpg`;
  `NIRO_REVIEW_CACHE` überschreibt). `hinzufuegen` schreibt die Review-Kopie erst in den Cache, dann aufs NAS. Der
  Server spielt aus dem Cache, sonst vom NAS und füllt den Cache dabei im Hintergrund (gültig, wenn die Größe stimmt).
  Der Cache darf jederzeit gelöscht werden.
- Ohne verbundenes NAS: `hinzufuegen`/`kommentare` brechen mit Exit 2 ab; der Server zeigt „NAS nicht verbunden" und
  prüft alle 10 s neu. Kein Offline-Modus.

## Datenmodell

`video.json`

    {"titel": "Dold 02 Fokus Bagger und Kran", "kunde": "Dold", "projekt": "Recruiting",
     "charge": "projects/Dold/Recruiting/2026-07 Dreh 27-28.07", "sortierung": "02",
     "angelegt": "2026-09-18T14:02:11", "freigegeben": null}

- `sortierung`: führende Nummer im Titel (z. B. „02"), sonst der Titel; `--sortierung` überschreibt.
- `freigegeben`: `{"am": "…", "von": "Jan"}` oder `null` — setzt der User in der Oberfläche.

`version.json`

    {"nr": 2, "angelegt": "2026-09-18T15:12:00", "von": "Studio-Mac",
     "quelle": "projects/Dold/…/Ergebnisse/Export/…/Dold 02 … – Entwurf v2.mp4",
     "dauer_s": 23.04, "fps": 25.0, "frames": 576, "breite": 2160, "hoehe": 3840, "groesse": 35497873,
     "umkodiert": false, "notiz": "v2: ruhige Shots, LUT dold_v3, Karten raus",
     "basis": 1, "abgeschlossen": null, "geholt_am": null}

- `von`: `git config niro.mac` (Studio-Mac / MacBook), sonst Rechnername. `quelle`: Pfad relativ zur Studio-Wurzel
  oder absolut, nur zur Nachvollziehbarkeit. `basis`: Vorversion, auf die sich `--umsetzung` bezieht.
- `abgeschlossen`: `{"am": "…", "von": "Jan"}` oder `null` (User-Knopf „Review abschließen" / „Wieder öffnen").
- `geholt_am`: Zeitpunkt des letzten `kommentare`-Laufs — Kommentare mit späterem `angelegt` gelten als neu.

`kommentare.json`

    {"naechste_id": 4, "kommentare": [
      {"id": "K1", "frame": 50, "bis_frame": null, "autor": "Jan", "text": "Schmatzer raus",
       "angelegt": "2026-09-18T14:20:03", "geaendert": null, "status": "offen",
       "antworten": [{"autor": "Claude", "text": "…", "angelegt": "…"}],
       "antwort_claude": null, "tc_neu": null},
      {"id": "K2", "frame": null, "bis_frame": null, "autor": "Jan", "text": "Insgesamt zu hektisch", …}]}

- Frames sind die Wahrheit (Timecode `HH:MM:SS:FF` wird aus `fps` gerechnet); `frame: null` = allgemeiner Kommentar
  ohne Zeit; `bis_frame` gesetzt = Bereich.
- IDs `K1, K2 …` in Anlagereihenfolge, stabil (so verweisen Chat, `umsetzung.json` und Protokoll darauf); die
  Anzeige sortiert nach Frame, allgemeine Kommentare zuerst.
- `status`: `offen` (User, Standard) → `umgesetzt` / `rueckfrage` (Claude, mit `antwort_claude`, wahlweise
  `tc_neu` in der Folgeversion) → `erledigt` (User hakt ab). Der User kann `offen` ↔ `erledigt` jederzeit setzen.
- `antworten`: Thread; der User antwortet in der Oberfläche, Claude per `review.py antworten`.

**Zustand eines Videos** (abgeleitet, nicht gespeichert): `freigegeben` wenn `video.freigegeben`; sonst
`bei-claude`, wenn die neueste Version abgeschlossen ist; sonst `review-offen`. Zähler je Video: offene Kommentare
der neuesten Version, neue seit `geholt_am`.

## Werkzeug `tools/review/`

    tools/review/
    ├── review.py                 Einstieg (CLI), Python ≥ 3.9, nur Standardbibliothek + ffmpeg/ffprobe
    ├── src/niro_review/
    │   ├── ablage.py             Wurzeln (Repo, NAS, Cache), Kunde/Projekt aus Charge, NFC-Nachschlagen, atomares Schreiben
    │   ├── modell.py             video.json / version.json / kommentare.json lesen, schreiben, Zustände, nächste Versionsnummer
    │   ├── medien.py             ffprobe, Entscheidung Kopie/Umkodierung, ffmpeg-Aufrufe, Vorschaubild, Timecode
    │   ├── kommentare.py         Kommentar-Operationen, Export kommentare.md/.json, umsetzung.json anwenden
    │   ├── server.py             HTTP-Server (Oberfläche, API, Medien mit Range)
    │   ├── launchagent.py        Plist schreiben, laden, entfernen
    │   └── cli.py                Unterbefehle, Ausgabe, Exit-Codes
    ├── ui/                       index.html, app.js, style.css, fonts/Meutas-{Regular,Medium,SemiBold,Bold}.otf, niro-symbol.svg
    ├── tests/                    pytest (läuft mit tools/autocut/venv/bin/python -m pytest tools/review/tests)
    ├── WORKFLOW-Review.md        Ablauf für Claude (Trigger, Befehle, Umsetzungsregeln)
    └── README.md                 Einrichtung (LaunchAgent), Bedienung, Tastenkürzel

### Befehle

| Befehl | Wirkung | Exit |
|---|---|---|
| `hinzufuegen "<Charge>" --datei "<Video>" [--video "<Titel>"] [--version N] [--notiz "…"] [--umsetzung <json>] [--sortierung 02] [--kunde/--projekt] [--original]` | Version anlegen: ffprobe, Kopie oder Umkodierung in den Cache, Vorschaubild, aufs NAS kopieren, Größe prüfen, `version.json` zuletzt schreiben; Link ausgeben | 0 ok · 1 Eingabefehler (Datei fehlt, Version belegt, Alpha-Datei) · 2 NAS/ffmpeg fehlt |
| `hinzufuegen "<Charge>" --ordner "<Ordner>" [--muster "*.mp4"] …` | Stapel: jede Datei ein eigenes Video, Titel aus dem Dateinamen, gleiche `--version` (sonst je Video die nächste) | wie oben; Fehler je Datei gesammelt, Exit 1 wenn eine scheiterte |
| `kommentare "<Charge>" [--video "<Titel>"] [--version N] [--alle] [--json]` | Kommentare der neuesten (oder genannten) Version je Video lesen, Export nach `Material/Feedback/<Datum> Review <Titel> V<n>/kommentare.{md,json}`, `geholt_am` setzen, Kurzfassung ausgeben; `--alle` auch schon geholte | 0 neue Kommentare · 1 keine neuen · 2 NAS fehlt |
| `umsetzung "<Charge>" --video "<Titel>" --version N --datei umsetzung.json` | Status/Antwort/`tc_neu` je Kommentar-ID setzen (`{"K1": {"status": "umgesetzt", "antwort": "…", "tc_neu": "00:00:29:04"}}`) | 0 · 1 unbekannte ID/Status · 2 |
| `antworten "<Charge>" --video "<Titel>" --version N --kommentar K3 --text "…"` | Antwort von Claude in den Thread | 0 · 1 · 2 |
| `status ["<Charge>" \| "<Kunde>/<Projekt>"]` | Tabelle: Video, neueste Version, Zustand, offene/neue Kommentare, Link | 0 |
| `entfernen "<Charge>" --video "<Titel>" [--version N]` | nach `_papierkorb/<Datum> <Kunde> <Projekt> <Titel>[ V<n>]/` verschieben | 0 · 1 |
| `server [--port 4711]` | Server im Vordergrund (so startet ihn der LaunchAgent) | — |
| `installieren [--port 4711]` / `deinstallieren` | LaunchAgent `de.niro.review` anlegen/laden bzw. entladen/entfernen | 0 · 1 |
| `oeffnen ["<Kunde>/<Projekt>[/<Titel>]"]` | Browser mit passender Adresse öffnen | 0 |

- Titel aus Dateinamen: Endung weg, Versionsmarken am Ende weg (` – Entwurf v1`, ` - Entwurf v1`, ` V6`, `_V6`,
  ` (Claude 2026-09-17)`), Leerraum trimmen. `--version` fehlt → nächste freie Nummer des Videos (Start 1).
- Review-Kopie: Container MP4/MOV mit H.264 `yuv420p`, Ton AAC (oder ohne Ton) **und lange Kante ≤ 1920 px** →
  byte-gleiche Kopie (`umkodiert: false`). Sonst ffmpeg → MP4, `h264_videotoolbox` (Fallback `libx264` CRF 18),
  `yuv420p`, lange Kante auf 1920 px begrenzt (nie vergrößert; 2160×3840 → 1080×1920, 3840×2160 → 1920×1080), AAC
  192 kbit/s, `+faststart`; `--original` behält die Auflösung. Grund (Messung 18.09.): 4K-Vertikalvideo verwirft im
  Browser 131 von 142 Frames, 1080p läuft ohne Drop; Replay und Frame.io kodieren ebenfalls auf 1080p. Frames und
  fps bleiben erhalten; `version.json` trägt `quelle_breite/quelle_hoehe/quelle_codec`. Dateien mit Alpha-Kanal
  (`yuva…`, ProRes 4444 Alpha) werden abgelehnt (Exit 1: „Alpha-Overlay ohne Bild darunter — erst als Komposit
  rendern"), `--trotzdem` erzwingt.
- Vorschaubild: Frame bei 25 % der Dauer, 640 px breit, JPEG.
- Kopie aufs NAS mit `shutil.copy2`, danach Größenvergleich; bei Abweichung Fehler und Aufräumen des V-Ordners.

### Export `kommentare.md` (für Claude)

    # Review-Kommentare „Dold 02 Fokus Bagger und Kran" V1 (18.09.2026, abgeschlossen 18.09. 14:41 von Jan)

    Charge: projects/Dold/Recruiting/2026-07 Dreh 27-28.07 · 25 fps · 23,04 s · Notiz V1: …

    | Nr | ID | TC | Bereich | Kommentar | Antworten | Status |
    |---|---|---|---|---|---|---|
    | 1 | K2 | — | — | Insgesamt zu hektisch | | offen |
    | 2 | K1 | 00:00:02:00 | | Schmatzer raus | Claude: … / Jan: … | offen |

`kommentare.json` enthält dieselben Kommentare vollständig plus `video`, `version`, `charge`, `fps`, `neu` (seit
`geholt_am`). Beide Dateien werden bei jedem Lauf überschrieben (Ordnername trägt Datum und Version).

## Server und API

- `http.server.ThreadingHTTPServer` (Python-Standardbibliothek), nur `127.0.0.1`, Port 4711, kein Login.
- `GET /` Oberfläche; `GET /ui/*` statische Dateien.
- `GET /api/index` → Kunden → Projekte → Videos (Titel, Sortierung, Charge, Zustand, neueste Version, Zähler,
  Vorschaubild-URL). Ergebnis wird 15 s im Speicher gehalten (NAS-Verzeichnisse sind langsam), `?frisch=1` erzwingt.
- `GET /api/video?kunde=&projekt=&video=` → `video.json`, alle Versionen mit Kommentaren.
- `POST /api/kommentar` (anlegen), `POST /api/kommentar/aendern` (Text, Status offen/erledigt, löschen — nur mit
  gleichem Autor), `POST /api/antwort`, `POST /api/version/abschliessen` (und `wieder_oeffnen`),
  `POST /api/video/freigeben` (und `freigabe_zuruecknehmen`). JSON rein, JSON raus; 409, wenn die Version
  abgeschlossen ist und ein Kommentar angelegt werden soll; 404 bei unbekanntem Pfad; 503 ohne NAS.
- `GET /media/<Kunde>/<Projekt>/<Video>/V<n>/video.mp4|thumb.jpg` → Range-Streaming (206, `Content-Range`,
  `Accept-Ranges`, 416 bei ungültigem Bereich, HEAD), 1-MiB-Blöcke, abgebrochene Verbindungen still; Quelle Cache
  → NAS, Cache-Füllung im Hintergrund.
- `GET /api/zustand` → NAS verbunden?, Wurzeln, Version des Werkzeugs.
- Schreiben: Datei neu lesen, ändern, atomar schreiben (Temp-Datei + `os.replace`), prozessweite Sperre. Zwischen
  Server und CLI schützt die Regel: der Server legt keine Kommentare auf abgeschlossenen Versionen an, die CLI
  schreibt Status/Antworten nur dort — Kollisionen sind damit praktisch ausgeschlossen, Restrisiko akzeptiert.
- Pfadsicherheit: nur unter Review-Wurzel und Cache, `..` und absolute Pfade abgelehnt, Prozent-Dekodierung + NFC.

## Oberfläche

Eine Seite, Vanilla JS, kein Build-Schritt. Dunkel wie Replay/Frame.io, NIRO-CI aus `tools/motion/src/clients/niro/brand.json`:
Grund `#1A211C`, Flächen `#232B26`/`#2C352F`, Linien `#3A453E`, Text `#F4F6F2`, gedämpft `#9AA59D`, Grün `#A1D334`
(Primäraktionen, Marker, Zustand „Review offen"), Blau `#7DD1FF` (Zustand „bei Claude", Rückfragen), Radius 12 px,
Überschriften Meutas (mitgelieferte OTFs), Fließtext Roboto (lokal installiert) mit System-Fallback, Logo-Symbol
`niro-symbol.svg` links oben.

**Übersicht:** links Baum Kunde → Projekt mit Zählern (offene Kommentare, Videos „bei Claude"); Suchfeld. Rechts
Karten des gewählten Projekts: Vorschaubild, Titel, Chip „V3", Zustand, Kommentarzahl, Datum, Charge klein. Sortiert
nach `sortierung`. Klick öffnet den Player.

**Player:** Kopfzeile Brotkrumen · Versions-Pillen V1 … Vn (neueste vorausgewählt) · Zustand · Knöpfe „Review
abschließen"/„Wieder öffnen", „Freigeben"/„Freigabe zurücknehmen". Mitte Video (9:16 und 16:9 passend, dunkler
Rahmen) mit Leiste: Play/Pause, Frame zurück/vor, Timecode `HH:MM:SS:FF` + Frame, Dauer, Lautstärke, Schleife,
Vollbild; Scrubber mit Kommentar-Markern (Punkt = Zeitpunkt, Balken = Bereich; Klick springt und hebt den Kommentar
hervor). Rechts Kommentarliste (allgemeine zuerst, dann nach Zeit): Timecode (klickbar), Autor, Text, Status-Chip,
Antworten, Claudes Antwort mit Sprung „→ V2 00:00:03:12"; Hover: bearbeiten, löschen, erledigt. Unten Eingabe:
Tippen pausiert das Video (wie Frame.io), Kommentar landet am aktuellen Frame; „Bereich" (In am aktuellen Frame, Out
per Knopf/`O`); „Allgemein" ohne Zeit; `⌘↩`/Strg+↩ sendet. Auf abgeschlossenen Versionen ist die Eingabe gesperrt
(Hinweis + „Wieder öffnen").

**„Seit V<n−1> geändert":** in V≥2 ein aufklappbarer Block mit allen beantworteten Kommentaren der Basisversion
(Status, Claudes Antwort, Sprung zur neuen Stelle), Haken „erledigt" direkt dort.

**Autor:** einmalige Namensabfrage (David / Jan / Sergio / frei), gespeichert im Browser, oben änderbar.

**Tasten:** Leertaste Play/Pause · ←/→ ein Frame · ⇧←/⇧→ eine Sekunde · Home/End · I/O Bereich · C Eingabe
fokussieren · Esc Eingabe verlassen · M stumm · F Vollbild · 1–9 Version wechseln.

**Frame-Genauigkeit:** `requestVideoFrameCallback` (Chrome/Safari) liefert `mediaTime`; Frame = `round(t·fps)`;
Sprung zu Frame `f` per `currentTime = (f + 0,5)/fps`.

**Aktualisierung:** Player fragt alle 5 s die Version ab (neue Version, Status von Claude), Übersicht alle 15 s;
neue Version erscheint als Hinweis „V3 ist da" mit Sprung.

## Zweit-Mac

Gleicher Code über `git pull`, gleiches NAS, eigener Cache unter `~/Library/Caches`, LaunchAgent per
`installieren` (Plist trägt den jeweiligen Repo-Pfad und das jeweilige `python3`). Kommentieren ist technisch auch
dort möglich; die Regel bleibt: Reviews am Studio-Mac. Zwei Macs am selben Video zur selben Zeit vermeiden (wie bei
Chargen).

## LaunchAgent

`~/Library/LaunchAgents/de.niro.review.plist`: `ProgramArguments` [`sys.executable`, `<Repo>/tools/review/review.py`,
`server`, `--port`, `4711`], `RunAtLoad`, `KeepAlive`, `WorkingDirectory` Repo, Log `~/Library/Logs/NIRO
Review/server.log`, Umgebung `NIRO_STUDIO_NAS` falls gesetzt. `installieren` schreibt die Datei, entlädt eine alte
Fassung und lädt per `launchctl bootstrap gui/<uid>`; `deinstallieren` per `launchctl bootout`. Repo verschoben → neu
installieren. Der Server nimmt Änderungen am Code erst nach Neustart des Agents (`deinstallieren` + `installieren`
oder `launchctl kickstart -k`).

## Fehlerbehandlung

- NAS fehlt: CLI Exit 2 mit Pfad; Server 503 + Hinweisseite, keine Schreibversuche.
- ffmpeg/ffprobe fehlen: Exit 2 mit Hinweis auf SETUP.md.
- Datei nicht lesbar / kein Videostream / Alpha: Exit 1, nichts angelegt.
- Kopie aufs NAS unvollständig: V-Ordner entfernt, Exit 2.
- Versionsnummer belegt: Exit 1 („V2 existiert — nächste freie: V3").
- Kommentar auf abgeschlossener Version: 409 mit Text für die Oberfläche.
- Unbekannte Kommentar-ID in `umsetzung.json`: Exit 1, nichts geschrieben (alles-oder-nichts).
- Abgebrochene Media-Verbindungen (BrokenPipe/ConnectionReset): still ignoriert.

## Tests

- `ablage`: Kunde/Projekt aus Chargenpfad (relativ/absolut, Umlaute NFD/NFC), Wurzeln aus Umgebung, atomares
  Schreiben, Pfadsicherheit (`..`, absolut, Prozent-Tricks).
- `modell`: Video anlegen, nächste Versionsnummer, Zustände (review-offen / bei-claude / freigegeben), Zähler.
- `medien`: Kopie-oder-Umkodierung aus ffprobe-JSON (h264/yuv420p/aac → Kopie; HEVC, ProRes, yuv422 → Umkodierung;
  Alpha → Ablehnung), ffmpeg-Befehlszeilen, Titel aus Dateinamen, Timecode aus Frames für 25/23,976/50 fps.
- `kommentare`: anlegen/ändern/löschen, Sperre bei abgeschlossener Version, Export-Tabelle und JSON, Sortierung,
  `umsetzung.json` (alles-oder-nichts), `geholt_am`/neu.
- `server`: mit temporärer Wurzel — Index, Video, Kommentar-Roundtrip, 409/404/503, Range (206/416/HEAD), Cache-Füllung.
- `launchagent`: Plist-Inhalt (ohne `launchctl`).
- Oberfläche: Sichtprüfung im Browser-Fenster der App (Übersicht, Player, Kommentar anlegen, Bereich, Abschließen,
  V2-Block, dunkles CI, 9:16 und 16:9), Konsole ohne Fehler.

## Einbindung ins Studio

- `CLAUDE.md`: neue Zeile in der Funktionstabelle — Trigger „Review: <Kunde>/<Projekt>[/<Video>]" (Status zeigen,
  Kommentare holen) und Regel: **Jeder fertige Review-Stand** (Rohschnitt, Feinschnitt, Entwurf, Animation als
  Komposit, Foto-Kontaktbogen nicht) wird sofort per `hinzufuegen` abgelegt und der Link im Chat gemeldet; nach
  „fertig" des Users `kommentare` → umsetzen → V+1 mit `--umsetzung`. Hinweis im Umgebungsabschnitt (Port, LaunchAgent).
- `tools/review/WORKFLOW-Review.md`: Ablauf, Befehle, Umsetzungsregeln (übernommen aus „Umsetzen" des
  Replay-Ablaufs), Protokoll-Pflicht (Eintrag je Version und je Kommentar-Lauf in `Protokoll.md` der Charge).
- `SETUP.md`: Schritt „Review" (`python3 tools/review/review.py installieren`).
- `tools/autocut/WORKFLOW-AutoCut.md`: nach Rohschnitt/Finalisieren/Feinschnitt Review-Ablage statt Replay-Angebot;
  Replay bleibt für Kunden-Runden.
- `studio_abgleich.sh` bleibt unverändert (`review/` liegt nur auf dem NAS).

## Erste Befüllung

Dold Recruiting: die 24 Entwürfe v1 aus `Ergebnisse/Export/Entwürfe Resolve 2026-09-17/` als V1 (Stapel, Notiz
„Entwurf v1 vom 17.09. — Feedback vom 18.09. kam im Chat"), die laufenden v2-Renders danach als V2 mit Notiz, was
gegenüber v1 geändert wurde; der Kreislauf über Kommentare beginnt mit V2. Kopie aufs NAS ≈ 1,3 GB.

## Später möglich

Bild-an-Bild-Vergleich zweier Versionen, Zeichnen im Bild (als PNG am Kommentar), macOS-Mitteilung beim Anlegen,
Kunden-Freigabelink über Replay-Export, Versionsvergleich der Kommentare als Änderungsliste im Protokoll.
