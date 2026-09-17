# Tagesbericht beider Studio-Macs (Spec)

Datum: 2026-09-17 · Status: Design im Chat freigegeben (Teile 1–4 „Passt so"), Umsetzung noch nicht beauftragt.

## Anlass

User 17.09.2026: „Wie wäre es, wenn wir einen Tagesbericht von beiden Studio-Versionen Mac1 und Mac2 anlegen und du als
Haupt dann täglich checkst, was heute gemacht wurde, welche neuen Funktionen dazukamen und was sinnvoll ist, in den Main zu
packen. Auch wo es vielleicht Probleme gab."

Vorgeschichte: Seit 17.09. laufen Chargen-Daten und Gedächtnis übers NAS (`docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md`),
das Werkzeug über GitHub `main`. Am selben Tag lagen auf dem Studio-Mac Werkzeug-Änderungen aus mehreren Sessions
unversioniert (Motion Craiss/Dold/Schmitt, `tools/musik`, `tools/sfx`), ein Commit ungepusht auf einem Claude-Branch, und
parallel liefen drei Sessions im selben Arbeitsbaum. Was auf dem anderen Mac passiert, ist von hier aus nicht sichtbar.

Gemessen 17.09.: Ein Sammler-Prototyp über die 23 an diesem Tag berührten Sitzungsverläufe (529 MB) läuft in 0,7 s und
findet 7 Sitzungen mit Nachrichten des Tages, je Sitzung Titel, Zeitraum, Aufträge, Schlussbericht, Tool-Fehler und
editierte Dateien. Sitzungen aus Worktrees liegen in eigenen Ordnern neben dem Hauptordner
(`~/.claude/projects/-Users-jansantos-NIRO-Studio--claude-worktrees-<name>`), Sitzungen aus Unterordnern ebenso
(`…-NIRO-Studio-tools-autocut`).

## Entscheidungen (User, 17.09.2026)

| Frage | Entscheidung |
|---|---|
| Wann läuft der Haupt-Check? | **Nur per Trigger** „Tagesbericht" im Chat. Kein Zeitplan, kein Hintergrunddienst. |
| Wie weit geht „in den Main packen"? | **Nur empfehlen.** Der Bericht nennt Kandidaten, Begründung und Befehle; ausgeführt wird nichts. |
| Ansatz | **Sammler je Mac + Haupt-Check** (statt „nur Protokolle + Git" oder „Live-Journal per Stop-Hook"). |
| Sitzungsverläufe auswerten? | Ja: Titel, Aufträge, Schlussbericht, Fehler, Dateien. Sie sind die einzige Spur von Werkzeug-Sessions ohne Commit. |
| Sicherungs-Patch der unversionierten Änderungen | Ja, Teil des Sammlers. |
| Hook-Hinweis bei fehlendem Tagesbericht | Ja, eine Zeile beim Sitzungsstart, sonst still. |
| Mac-Namen | `git config niro.mac`, Vorschlag „Studio-Mac" (bisheriger Studio-Rechner) und „MacBook" (Zweit-MacBook). |

## Design

### 1. Ablage

    <Repo>/berichte/<JJJJ-MM-TT>/
      <Mac>.md            Tagesstand dieses Macs (Sammler, deterministisch)
      <Mac>.patch         Sicherung der unversionierten Werkzeug-Änderungen (immer geschrieben, Kopfzeile mit Stand)
      Tagesbericht.md     Zusammenfassung des Haupt-Checks (Claude), ein Bericht je Tag

- `berichte/` liegt im Hauptordner des Repos (erste Zeile von `git worktree list`), ist gitignoriert (`/berichte/`) und
  wird von `tools/studio_abgleich.sh` mit denselben Regeln wie `projects/` nach `NIRO Studio/berichte/` auf dem NAS
  gespiegelt: beide Richtungen, neuere Datei gewinnt, nie löschen. Nach dem Abgleich liegen die Dateien beider Macs
  lokal, der Haupt-Check liest nur lokal.
- Die Berichte enthalten Auszüge aus Aufträgen und Dateinamen. Sie bleiben lokal und auf dem NAS, nie auf GitHub.
- **Mac-Name:** `git config --get niro.mac` im Repo, einmal je Mac gesetzt (SETUP.md). Fehlt der Eintrag:
  `scutil --get ComputerName`. Für den Dateinamen werden `/` und `:` durch `-` ersetzt. Umgebungsvariable
  `NIRO_STUDIO_MAC` überschreibt beides (Tests).

### 2. Sammler `tools/tagesbericht/sammler.py`

Python 3 (≥ 3.9, nur Standardbibliothek, `python3` aus dem PATH). Endet immer mit 0, meldet Fehler als Zeile auf stderr
und lässt betroffene Abschnitte leer. Läuft aus jedem Ordner des Repos, auch aus einem Worktree; Repo = Hauptordner wie
in `studio_abgleich.sh` (`NIRO_STUDIO_REPO` überschreibt).

| Aufruf | Wirkung |
|---|---|
| `python3 tools/tagesbericht/sammler.py` | heute und gestern neu schreiben, dann `berichte/` abgleichen |
| `… --tag 2026-09-16` / `… --tag gestern` | nur diesen Tag |
| `… --still` | keine Ausgabe auf stdout |
| `… --ohne-abgleich` | kein Aufruf von `studio_abgleich.sh --berichte` (so ruft der Abgleich selbst den Sammler) |
| `… --hook` | für den SessionStart-Hook: wie ohne Argument, still; Abgleich mit 8 s Zeitlimit (SMB-Hänger blockieren keinen Sitzungsstart, lokaler Stand bleibt); einzige Ausgabe ist die Hinweiszeile (Abschnitt 4) |

Heute und gestern werden bei jedem Lauf **vollständig neu** erzeugt (idempotent), damit späte Sitzungen und Commits beim
nächsten Lauf nachrutschen. Tagesgrenzen in Ortszeit; ein Sitzungs-Datensatz gehört zu dem Tag, auf den sein
`timestamp` in Ortszeit fällt. Sitzungen über Mitternacht erscheinen an beiden Tagen mit den jeweiligen Nachrichten.

Umgebungsvariablen für Tests: `NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_STUDIO_MAC`, `NIRO_STUDIO_HEUTE`
(festes „heute", `JJJJ-MM-TT`), `NIRO_CLAUDE_PROJECTS_DIR` (Standard `~/.claude/projects`), `NIRO_CLAUDE_MEMORY_DIR`
(Standard `<projects-dir>/<Schlüssel>/memory`).

#### 2.1 Quelle Git

Alles über `git` im Hauptordner, ohne `git fetch` (kein Netz im Hook; den Live-Stand holt der Haupt-Check).

- **Auf main:** Commits des Tages, die von `origin/main` erreichbar sind (`git log origin/main --since --until`), mit
  Uhrzeit, Kurzhash, Betreff.
- **Ungepusht:** je lokalem Branch (auch `main`) die Commits des Tages, die von `origin/main` nicht erreichbar sind
  (`git log <Branch> --not origin/main --since --until`). Dazu je Branch Vorsprung/Rückstand zu `origin/main`
  (`git rev-list --left-right --count`), Datum des letzten Commits, Worktree-Pfad, falls ausgecheckt.
- **Branches ohne Commits des Tages:** eine Zeile je Branch mit Vorsprung/Rückstand und letztem Commit-Datum, damit
  überholte Branches (0 vor, viele hinter) sichtbar werden.
- **Unversioniert je Worktree:** für den Hauptordner und jeden Worktree aus `git worktree list --porcelain`:
  `git status --porcelain -uall -z`, gruppiert nach den ersten zwei Pfadteilen (`tools/motion/`, `docs/superpowers/`,
  Wurzeldateien einzeln): Anzahl geändert / neu / gelöscht, jüngste Änderungszeit, bis zu 8 Pfade je Gruppe.
  `projects/` und `berichte/` sind ignoriert und tauchen nicht auf.
- **Stashes:** Anzahl aus `git stash list`.
- **Kopfzeile:** Branch und Kurzhash von HEAD im Hauptordner.

#### 2.2 Quelle Chargen

- Protokolle: `projects/*/*/Protokoll.md` und `projects/*/*/*/Protokoll.md` (beide Tiefen kommen vor). Ein Eintrag zählt
  zum Tag, wenn seine `## `-Überschrift das Datum als `JJJJ-MM-TT` oder `TT.MM.JJJJ` enthält (vorkommende Formen:
  `## 2026-09-16 11:07 — …`, `## 2026-09-17 — …`, `## Session 15.09.2026 — …`, `## Overlay-Export Video 1 (2026-08-05)`).
  Ausgabe je Charge: Überschriften ohne `## `, auf 120 Zeichen gekürzt. Steht dieselbe Überschrift bei fünf oder mehr
  Chargen (17.09.: „Medien aufs NAS verschoben" in 40 Chargen), wird sie zu einer Zeile mit Anzahl zusammengefasst.
- Lieferungen: Dateien unter `<Charge>/Ergebnisse/**` mit Änderungszeit an dem Tag (ohne `.DS_Store`): Anzahl je Charge
  und bis zu 5 Pfade relativ zur Charge. Hinweis im Bericht: Der Abgleich behält Änderungszeiten, solche Dateien können
  vom anderen Mac stammen.

#### 2.3 Quelle Sitzungen

- Ordner: alle `<projects-dir>/<Schlüssel>*` (Schlüssel = Repo-Pfad, jedes Zeichen außer A–Z/a–z/0–9 als `-`), also
  Hauptordner, Worktrees und Unterordner. Nur `*.jsonl` direkt im Ordner; Subagenten-Verläufe (`<Sitzung>/subagents/`)
  und Datensätze mit `isSidechain` bleiben draußen. Dateien mit Änderungszeit vor dem Tagesbeginn werden nicht geöffnet.
  Unlesbare Zeilen werden übersprungen.
- Je Sitzung mit `user`- oder `assistant`-Datensätzen des Tages:
  - **Titel:** `customTitle` des letzten `custom-title`-Datensatzes, sonst die ersten 80 Zeichen des ersten Auftrags.
  - **Zeitraum:** erster und letzter Zeitstempel des Tages; **Branch:** letztes `gitBranch`; **Ordner:** `cwd` relativ zum Repo.
  - **Aufträge:** `user`-Datensätze ohne `isMeta`, Inhalt als Text oder `text`-Blöcke; Texte, die mit `<system-reminder>`
    oder `[Request interrupted` beginnen, zählen nicht. Je Auftrag 200 Zeichen, höchstens 12 aufgeführt, Rest als „+N weitere".
  - **Schlussbericht:** letzter `text`-Block eines `assistant`-Datensatzes des Tages, 1.500 Zeichen. Endet der Tag der
    Sitzung mit einem Auftrag ohne Antwort, steht „ohne Schlussbericht".
  - **Tool-Fehler:** Anzahl der `tool_result`-Blöcke mit `is_error`; erste Zeile der ersten fünf, je 160 Zeichen.
  - **Dateien:** `file_path` aus `tool_use`-Blöcken `Edit`, `Write`, `NotebookEdit`, relativ zum Repo, eindeutig, bis zu 20.
  - **Werkzeuge:** die fünf häufigsten Tool-Namen mit Anzahl.
  - **Chargen-Bezug:** Chargen-Pfade (`projects/<Kunde>/<Projekt>/<Charge>` bzw. zwei Ebenen) aus den editierten Dateien.

#### 2.4 Quelle Gedächtnis

Notizen (`*.md` außer `MEMORY.md`) im Gedächtnis-Ordner mit Änderungszeit an dem Tag: Name und `description` aus dem
Frontmatter, 160 Zeichen. Der Ordner ist auf beiden Macs derselbe NAS-Ordner; die Liste steht deshalb in beiden Berichten gleich.

#### 2.5 Hinweise (deterministische Prüfungen)

- **Protokoll fehlt:** Sitzung mit Chargen-Bezug, deren Charge keinen Protokoll-Eintrag des Tages hat.
- **Ohne Schlussbericht:** Sitzungen nach 2.3.
- **Viele Tool-Fehler:** Sitzungen mit mindestens fünf Fehlern.
- **Ungepusht:** Branches mit Vorsprung zu `origin/main`; **Worktree mit Änderungen:** Worktrees mit unversionierten Dateien.

#### 2.6 Sicherung `<Mac>.patch`

Je Worktree (Hauptordner zuerst) ein Abschnitt mit Kopfzeile `# Worktree: <Pfad> (<Branch>)`: `git diff HEAD` für
versionierte Dateien, danach für jede unversionierte Datei (`git ls-files --others --exclude-standard`) bis 1 MB ohne
NUL-Byte in den ersten 8 KB ein `git diff --no-index /dev/null <Datei>`. Größere oder binäre Dateien nur als Namen in
einer Kommentarzeile. Gesamtgröße höchstens 5 MB, danach Abbruch mit Kommentarzeile. Erste Zeile immer
`# Sicherung <Mac> <JJJJ-MM-TT HH:MM>`; gibt es keine Änderungen, folgt nur `# keine unversionierten Änderungen`. Die Datei
wird bei jedem Lauf neu geschrieben, weil der Spiegel nie löscht und eine veraltete Sicherung sonst vom NAS zurückkäme.

#### 2.7 Ausgabeformat `<Mac>.md`

Feste Überschriften, damit der Haupt-Check sie verlässlich findet:

    # Tagesstand <Mac> — <JJJJ-MM-TT>
    Stand: <JJJJ-MM-TT HH:MM> · Repo <Pfad> · HEAD <Branch> <Hash> · Sitzungen <n> · Commits <n>
    ## Git
    ### Auf main
    ### Ungepusht
    ### Branches ohne Commits heute
    ### Unversioniert (<Worktree>, <Branch>)      je Worktree ein Abschnitt, „Stashes: n" am Ende
    ## Chargen
    ### Protokoll-Einträge
    ### Neue Dateien unter Ergebnisse/
    ## Sitzungen
    ### <HH:MM>–<HH:MM> · <Titel> · <Branch> · <n> Aufträge · <n> Tool-Fehler
    - Aufträge: 1. „…" 2. „…" (+N weitere)
    - Schlussbericht: „…"
    - Tool-Fehler: „…"
    - Dateien: … (+N)
    - Chargen: …
    ## Gedächtnis
    ## Hinweise

Leere Abschnitte enthalten die Zeile „keine". Sitzungen chronologisch.

### 3. Abgleich `tools/studio_abgleich.sh`

- Neue Funktion `berichte_abgleichen`: `$REPO/berichte` ↔ `$NAS/berichte`, beide Richtungen, Filter wie `projects/`;
  Zusammenfassungsteil „Berichte: X geholt, Y hochgeladen".
- Neue Option `--berichte`: NAS prüfen, nur `berichte_abgleichen`. Ruft den Sammler **nicht** auf (keine Schleife).
- Modi `alles`, `--charge`, `--nach-pull`: vor `berichte_abgleichen` den Sammler mit `--still --ohne-abgleich` starten,
  falls `tools/tagesbericht/sammler.py` im Stand liegt; Fehler des Sammlers blockieren nichts.
- `--umstieg` unverändert.

### 4. SessionStart-Hook `.claude/settings.json` (versioniert, neu)

    {
      "hooks": {
        "SessionStart": [
          {
            "matcher": "startup|resume",
            "hooks": [
              { "type": "command",
                "command": "python3 \"${CLAUDE_PROJECT_DIR:-.}/tools/tagesbericht/sammler.py\" --hook 2>/dev/null || true",
                "timeout": 20 }
            ]
          }
        ]
      }
    }

- Gilt nach dem Pull auf beiden Macs ohne Rückfrage. Der Hook blockiert die Sitzung, bis er fertig ist; der Sammler
  läuft in unter zwei Sekunden, das Zeitlimit von 20 s sichert den Rest ab.
- **Hinweiszeile** (einzige Ausgabe, landet im Kontext der Sitzung): Der jüngste Tag vor heute innerhalb der letzten
  sieben Tage, für den unter `berichte/` ein `<Mac>.md` irgendeines Macs liegt, aber kein `Tagesbericht.md`, ergibt
  eine Zeile: „Tagesbericht für <TT.MM.JJJJ> fehlt — Trigger: „Tagesbericht: <JJJJ-MM-TT>"." Gibt es keinen solchen Tag,
  keine Ausgabe. Fehlt das NAS, gilt der lokale Stand. Der Hook-Lauf selbst schreibt den heutigen Tagesstand, deshalb
  zählt „heute" nie als fehlend.
- Aus einem Worktree oder Unterordner heraus findet der Sammler den Hauptordner selbst.

### 5. Haupt-Check: Funktion „Tagesbericht" (`tools/tagesbericht/WORKFLOW-Tagesbericht.md`)

Trigger (CLAUDE.md): „Tagesbericht" (heute), „Tagesbericht: gestern", „Tagesbericht: <JJJJ-MM-TT>". Läuft auf dem Mac,
an dem der Trigger geschrieben wird. Ablauf:

1. Tag bestimmen. `git fetch -q` im Hauptordner (Live-Stand der Branches, Fehler nur melden).
2. `python3 tools/tagesbericht/sammler.py --tag <Tag>` und `sh tools/studio_abgleich.sh --berichte`.
3. Lesen: alle `berichte/<Tag>/*.md` außer `Tagesbericht.md`; den jüngsten `berichte/<früherer Tag>/Tagesbericht.md`
   für den Übertrag; bei Bedarf `<Mac>.patch`, Protokolle, Specs. Bekannte Macs = alle `<Mac>.md`-Namen unter
   `berichte/`; fehlt einer für den Tag, seinen jüngsten vorhandenen Tag nennen.
4. `berichte/<Tag>/Tagesbericht.md` schreiben, feste Abschnitte:
   - **Stand:** je Mac Zeit des Sammler-Laufs, Sitzungen, Commits; fehlende Macs mit letztem bekannten Stand ganz oben.
   - **Gemacht:** je Mac, gruppiert nach Chargen und Werkzeug, ein bis zwei Sätze je Sitzung; die Sammelzeile aus 2.2
     bleibt eine Zeile.
   - **Neue Funktionen und Werkzeug-Änderungen:** je Werkzeug, was auf main kam, was auf Branches liegt, was unversioniert ist.
   - **Empfehlung für main:** nummerierte Kandidaten mit Begründung und fertigem Befehl, ohne Ausführung:
     ungepushte Branch-Commits (Merge/Fast-Forward), unversionierte Änderungen mit Einschätzung „fertig / halbfertig /
     Wegwerf" (Quelle: Schlussberichte, Patch), überholte Branches zum Löschen. Punkte des anderen Macs als Auftrag
     „auf <Mac>:" formuliert.
   - **Probleme und Auffälligkeiten:** gehäufte Tool-Fehler, abgebrochene Sitzungen, Sitzungen ohne Schlussbericht,
     offene Fragen aus Schlussberichten, Hinweise des Sammlers.
   - **Offen und Übertrag:** offene Punkte des Tages plus Punkte des Vorberichts mit Alter in Tagen („seit 3 Tagen");
     was laut Tagesstand erledigt ist, wird gestrichen und einmal als erledigt genannt.
   - **Chargen-Stand:** berührte Chargen, Lieferungen, fehlende Protokoll-Einträge.
   Existiert für den Tag schon ein Tagesbericht, wird er ersetzt; erste Zeile nennt „ersetzt Fassung von <HH:MM>".
5. `sh tools/studio_abgleich.sh --berichte`. Im Chat die Kurzfassung (eine Bildschirmseite: Stand, Empfehlungen,
   Probleme, Offen) und der Pfad der Datei.

Regeln: Es wird nur unter `berichte/` geschrieben; keine Commits, Merges, Pushes, keine Änderungen an Chargen oder
Werkzeug. Jede Aussage nennt Mac und Sitzung oder Commit als Quelle; Unsicheres ist als Vermutung markiert; nichts wird
aus dem Gedächtnis ergänzt, was nicht in den Quellen steht. Deutsch, Stil der Protokolle. Merges führt Claude nur in
einer eigenen Session auf ausdrücklichen Auftrag aus.

## Fehlerbehandlung

| Lage | Verhalten |
|---|---|
| NAS nicht verbunden | Sammler schreibt lokal, Abgleich meldet wie bisher; Haupt-Check nennt den fehlenden Mac mit letztem Stand |
| Sitzungsordner fehlt oder Datei unlesbar | Abschnitt „Sitzungen: keine", Fehlerzeile auf stderr, Ende 0 |
| Kaputte JSONL-Zeile | übersprungen |
| Kein `origin/main` (Test-Repo ohne Remote) | „Auf main" leer, alle Commits des Tages unter „Ungepusht" |
| `git` fehlt oder Repo nicht erkannt | Abschnitt „Git: keine", Fehlerzeile, Ende 0 |
| Kein `niro.mac` und kein Computername | Name „Mac" |
| Patch über 5 MB | Abbruch mit Kommentarzeile, Rest als Namen |
| Sammler im Hook länger als 20 s | Claude Code bricht ab, Sitzung startet trotzdem |
| Zwei Sammler gleichzeitig (parallele Sitzungen) | Schreiben über Temp-Datei und `os.replace`; letzter gewinnt, Inhalt gleich |
| Tagesbericht-Trigger ohne Mac-Datei des anderen Macs | Bericht entsteht trotzdem, Lücke steht im Abschnitt „Stand" |

## Tests

`tools/tagesbericht/sammler_test.py` (`unittest`, Aufruf `python3 tools/tagesbericht/sammler_test.py`, Exit 0 = bestanden),
ohne echtes NAS, Gedächtnis oder Sitzungsordner. Fixture: Wegwerf-Repo mit Bare-Remote als `origin` (Commit A gepusht,
Commit B auf `claude/x` ungepusht, ein Worktree mit Änderung), geänderte und neue Dateien unter `tools/`, Chargen in
beiden Tiefen mit Protokoll-Überschriften aller vier Formen, `Ergebnisse/`-Datei mit gesetzter Änderungszeit,
Sitzungsordner für Hauptordner und Worktree mit kleinen JSONL-Verläufen (custom-title, Aufträge als Text und Blöcke,
`isMeta`, `<system-reminder>`, `[Request interrupted`, Edit auf Chargen-Datei, `tool_result` mit `is_error`,
Zeitstempel am Tag und am Vortag, kaputte Zeile, Subagenten-Datei, `isSidechain`), Gedächtnis-Notiz mit Frontmatter,
Test-NAS-Ordner, `NIRO_STUDIO_HEUTE` fest.

Geprüft wird:
- `berichte/<Tag>/<Mac>.md` mit allen Abschnitten; Commit A unter „Auf main", B unter „Ungepusht" mit „+1";
  Unversioniert-Gruppen mit Zählern; Worktree-Abschnitt; Stashes.
- Protokoll-Einträge aller vier Formen, Vortag nicht; Sammelzeile bei fünf gleichen Überschriften; Ergebnisse-Zählung.
- Sitzung: Titel, Zeitraum, Aufträge ohne Meta/System-Reminder/Abbruch, „+N weitere", Schlussbericht, Fehlerzeile,
  Dateien, Chargen-Bezug; Vortags-Datensätze fehlen; Subagenten und Sidechain fehlen; kaputte Zeile stört nicht;
  Sitzung ohne Antwort → „ohne Schlussbericht".
- Gedächtnis-Zeile; Hinweise „Protokoll fehlt", „Ohne Schlussbericht", „Ungepusht", „Worktree mit Änderungen".
- Patch: Diff der versionierten Datei, `--no-index`-Diff der neuen Datei, Binärdatei nur als Name, Worktree-Abschnitt.
- `--hook`: Hinweiszeile nur für den jüngsten Tag mit Tagesstand ohne Tagesbericht innerhalb von sieben Tagen; mit
  vorhandenem Tagesbericht oder ohne Tagesstand leer; Abgleich-Zeitlimit greift (Ersatzbefehl, der schläft).
- Ende 0 bei fehlendem NAS, fehlendem Sitzungsordner, Repo ohne Remote; zwei Läufe liefern gleichen Inhalt.
- Abgleich nach NAS: Datei liegt danach unter `<NAS>/berichte/<Tag>/`; `--ohne-abgleich` lässt das NAS unberührt.

`tools/studio_abgleich_test.sh` erweitert: `--berichte` spiegelt in beide Richtungen und ruft den Sammler nicht;
ein normaler Lauf ruft den Sammler (Ersatzbefehl per `NIRO_SAMMLER_CMD`) und spiegelt `berichte/`.

Abnahme auf dem Studio-Mac: Sammler auf den echten Daten des 17.09. (nur lesend außer `berichte/`), Zahlen mit dem
Prototyp vergleichen, dann erster „Tagesbericht: 2026-09-17" im Chat.

## Doku

- `CLAUDE.md`: Trigger-Zeile „Tagesbericht[: gestern | <JJJJ-MM-TT>]" in der Funktionstabelle; im NAS-Absatz der Satz,
  dass `berichte/` mitgespiegelt wird. Erst einarbeiten, wenn der parallel laufende CLAUDE.md-Stand (Medien aufs NAS,
  Session „Niro Studio Speicheroptimierung") committet ist.
- `SETUP.md`: Schritt „Mac-Name: `git config niro.mac "MacBook"`" und Hinweis auf den Hook.
- `tools/tagesbericht/README.md`: Aufrufe, Ablage, Format, Tests. `.gitignore`: `/berichte/` mit Verweis auf diesen Spec.
- Gedächtnis: Notiz `tagesbericht-funktion` (Trigger, Ablage, nur Empfehlung, Mac-Namen).

## Nicht im Umfang

Zeitplan oder Hintergrunddienst; Merges, Commits oder Pushes durch den Haupt-Check; Journal je Zug; Auslösen des Sammlers
auf dem anderen Mac von hier aus; Protokoll der Abgleich-Fehler; Auswertung von Subagenten-Verläufen; Berichte über
mehrere Tage in einer Datei.

## Reihenfolge

1. Sammler mit Tests (Abschnitte 2, 2.1–2.7).
2. Abgleich `--berichte` und Sammler-Aufruf mit Tests (3); `.gitignore`.
3. Hook, SETUP.md, README (4, Doku).
4. Workflow-Datei und CLAUDE.md-Trigger nach Freigabe des parallelen CLAUDE.md-Stands (5, Doku); Gedächtnis-Notiz.
5. Abnahme: echter Lauf 17.09., erster Tagesbericht im Chat; Commit und Push auf `main`; auf dem MacBook `git pull`
   und `git config niro.mac "MacBook"`.
