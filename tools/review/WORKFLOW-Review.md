# Review — Ablauf für Claude (seit 18.09.2026)

Spec `docs/superpowers/specs/2026-09-18-review-tool-design.md`. Werkzeug `tools/review/review.py` (Python ≥ 3.9,
ffmpeg). Oberfläche `http://localhost:4711` (LaunchAgent `de.niro.review`, `python3 tools/review/review.py installieren`).
Ablage auf dem NAS: `08_Claude Tools/NIRO Studio/review/<Kunde>/<Projekt>/<Video>/V<n>/` (video.mp4, thumb.jpg,
version.json, kommentare.json); lokaler Cache `~/Library/Caches/NIRO Review`. Dropbox Replay bleibt das Werkzeug für
**Kunden**-Runden (`tools/autocut/WORKFLOW-AutoCut.md` „Review in Replay"); NIRO Review ist der interne Kreislauf
User ↔ Claude.

    PY=python3
    RV="/Users/jansantos/NIRO Studio/tools/review/review.py"
    CHARGE="projects/<Kunde>/<Projekt>/<Charge>"

## Regel: jeder fertige Stand geht ins Review

Sobald ein Stand fertig ist, der begutachtet werden soll — Rohschnitt, Feinschnitt, Entwurf, finalisierter Export,
Animation **als Komposit** (Alpha-Overlays allein werden abgelehnt), Aftermovie —, wird er sofort abgelegt und der Link
im Chat genannt. Nicht ins Review: Kontaktbögen, Fotos, PDFs, reine Grafik-Alphas, Zwischenstände ohne Bild.

    "$PY" "$RV" hinzufuegen "$CHARGE" --datei "<MP4/MOV>" [--video "<Titel>"] [--notiz "<was ist das, was ist neu>"]
    "$PY" "$RV" hinzufuegen "$CHARGE" --ordner "<Ordner>" [--muster "*.mp4"] [--version 1] [--notiz "…"]

- Titel = Dateiname ohne Endung und ohne Versionsmarke (`– Entwurf v1`, `_V6`, ` V2`, `(Claude …)`); `--video` setzt
  ihn ausdrücklich. Ein Video = ein Titel über alle Versionen; V-Nummer ergibt sich (`--version` nur, wenn nötig).
- `--notiz` immer füllen: bei V1 was es ist, ab V2 was sich geändert hat (eine Zeile).
- Kopie oder Umkodierung (H.264/AAC) macht das Werkzeug; die Review-Kopie hat höchstens 1920 px lange Kante (4K
  ruckelt im Browser; `--original` behält die Auflösung, nur wenn der User es verlangt). Frames und fps bleiben gleich,
  Timecodes gelten also 1:1 für den Original-Export. Exit 1 = Eingabe (Datei, belegte Nummer, Alpha), Exit 2 = NAS
  oder ffmpeg fehlt → melden, nicht umgehen.
- Im Chat melden: Titel, V-Nummer, Link (`http://localhost:4711/#/<Kunde>/<Projekt>[/<Titel>]`), Notiz. Protokoll-Eintrag.

## Kommentare holen („Review: <Kunde>/<Projekt>[/<Video>]" oder „fertig")

    "$PY" "$RV" kommentare "$CHARGE" [--video "<Titel>"] [--alle]

- Exit 0 = neue Kommentare (Ausgabe zeigt sie, Export liegt in `<Charge>/Material/Feedback/<Datum> Review <Titel>
  V<n>/kommentare.md` + `.json`), Exit 1 = nichts Neues, Exit 2 = NAS fehlt.
- Bei Aufruf mit `<Kunde>/<Projekt>` (ohne Charge) werden alle Videos des Projekts geholt; die Charge steht in
  `kommentare.json` (`charge`). Ist die Version nicht abgeschlossen („noch offen"), trotzdem umsetzen — der User hat
  „fertig" gesagt; im Bericht erwähnen.
- `kommentare.md` lesen: `ID` (K1 …) ist die Referenz für Umsetzung, Protokoll und Chat; `TC` = Timecode in **dieser**
  Version, `Bereich` = Out; `Antworten` = Thread (User kann auf Rückfragen antworten); `Neu` = seit dem letzten Holen.
- Status-Werte: `offen` (User) · `umgesetzt` / `rueckfrage` (Claude) · `erledigt` (User hakt ab).

## Umsetzen

Regeln wie beim Replay-Ablauf: **Sofort umsetzen**, was eindeutig und werkzeugfähig ist (Pegel, Shot/Take tauschen,
Clip oder Grafik raus, Ausschnitt/Zoom/Begradigen, Grading einzelner Clips, Musik/SFX-Pegel, Untertitel, Grafik-Text).
**Handarbeit** (Verschieben/Rippeln in handbearbeiteten Timelines, Trims an Übergängen, Timing auf Musik) →
`rueckfrage` mit konkretem Vorschlag. **Rückfrage** bei Mehrdeutigkeit, mehreren Wegen, Konflikt mit festen Regeln
(max. 60 s, Sperren/Freigaben, nur Website-Infos, m/w/d, max. 2 Takes pro Sprecher, stärkste Aussage zuerst) — alle
Rückfragen gesammelt in einer Chat-Nachricht **und** als Status `rueckfrage` am Kommentar.

`umsetzung.json` (im Feedback-Ordner der Runde ablegen):

    {"K1": {"status": "umgesetzt", "antwort": "Schmatzer entfernt, Cut auf 00:00:02:03 gezogen", "tc_neu": "00:00:02:00"},
     "K2": {"status": "rueckfrage", "antwort": "Welche Stellen meinst du — nur die Drohne oder auch die Handkamera?"},
     "K3": {"status": "umgesetzt", "antwort": "Musik −3 dB ab 00:00:10:00"}}

- `tc_neu` (oder `frame_neu`) = Stelle in der **neuen** Version, wenn sie sich verschoben hat; die Oberfläche zeigt
  „→ V<n+1> 00:00:02:00" mit Sprung.
- Neue Version ablegen und Umsetzung in einem Schritt:

      "$PY" "$RV" hinzufuegen "$CHARGE" --datei "<neuer Render>" --video "<Titel>" --notiz "V2: …" --umsetzung "<umsetzung.json>"

  (`--umsetzung` bezieht sich auf die Vorversion; unbekannte IDs → Exit 1, nichts angelegt.) Ohne neuen Render (nur
  Rückfragen): `"$PY" "$RV" umsetzung "$CHARGE" --video "<Titel>" --version <n> --datei umsetzung.json`.
- Antwort in einen Thread (z. B. auf eine User-Antwort): `"$PY" "$RV" antworten "$CHARGE" --video "<Titel>" --version <n>
  --kommentar K2 --text "…"`.
- Bericht im Chat: je Kommentar-ID eine Zeile (umgesetzt / Rückfrage / Handarbeit), Link zur neuen Version, offene
  Rückfragen zuletzt. `umsetzung.md` im Feedback-Ordner wie beim Replay-Ablauf (Tabelle `Nr | ID | TC | Kommentar |
  Klasse | Änderung | TC neu`). Protokoll-Eintrag in `Protokoll.md` der Charge.

## Übersicht und Aufräumen

    "$PY" "$RV" status ["<Kunde>/<Projekt>" | "$CHARGE"]        Zustand je Video (review-offen / bei-claude / freigegeben)
    "$PY" "$RV" entfernen "$CHARGE" --video "<Titel>" [--version n]   nur nach Auftrag; landet in review/_papierkorb
    "$PY" "$RV" oeffnen "<Kunde>/<Projekt>"                       Browser öffnen

Nie: `video.mp4` einer Version ersetzen, kommentare.json von Hand kürzen, Versionen umbenennen. Ein neuer Render ist
immer eine neue Version.

## Zweit-Mac

Gleicher Code (git pull), gleiches NAS, eigener Cache und eigener LaunchAgent (`installieren` dort einmal ausführen).
Videos vom Zweit-Mac erscheinen am Studio-Mac sofort; Reviews macht der User am Studio-Mac. Nicht auf beiden Macs
gleichzeitig am selben Video arbeiten.

## Fehlerbilder

- „NAS nicht verbunden" (Exit 2 / Banner in der Oberfläche): NAS mounten, dann wiederholen; nichts lokal ablegen.
- „V2 existiert — nächste freie: V3": ohne `--version` aufrufen.
- „Alpha-Overlay ohne Bild darunter": Komposit rendern (Grafik über Schnitt) oder mit `--trotzdem` bewusst ablegen.
- Oberfläche leer nach Code-Update: LaunchAgent lädt den alten Prozess — `launchctl kickstart -k gui/$(id -u)/de.niro.review`.
- Video ruckelt beim Scrubben: Cache füllt sich beim ersten Abspielen (`~/Library/Caches/NIRO Review`); danach flüssig.
