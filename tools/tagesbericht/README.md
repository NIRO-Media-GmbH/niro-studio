# Tagesbericht — Sammler und Haupt-Check

Tagesstand je Mac (Git, Chargen, Claude-Sitzungen, Gedächtnis) als `berichte/<JJJJ-MM-TT>/<Mac>.md`, dazu
`<Mac>.patch` (Sicherung der unversionierten Werkzeug-Änderungen, nur für heute). `berichte/` liegt im Hauptordner des
Repos, ist gitignoriert und wird wie `projects/` übers NAS gespiegelt (`NIRO Studio/berichte/`, beide Richtungen,
neuere Datei gewinnt, nie löschen). Der Haupt-Check — Funktion „Tagesbericht", Anleitung `WORKFLOW-Tagesbericht.md` —
liest die Dateien beider Macs und schreibt `berichte/<Tag>/Tagesbericht.md`; er empfiehlt nur, er merged nichts.
Spec: `docs/superpowers/specs/2026-09-17-tagesbericht-design.md`. Gebaut 17.09.2026.

## Aufrufe

| Aufruf | Wirkung |
|---|---|
| `python3 tools/tagesbericht/sammler.py` | heute und gestern neu schreiben, dann `sh tools/studio_abgleich.sh --berichte` |
| `… --tag 2026-09-16` / `--tag gestern` / `--tag heute` | nur diesen Tag |
| `… --still` | keine Ausgabe auf stdout |
| `… --ohne-abgleich` | ohne Abgleich (so ruft `studio_abgleich.sh` den Sammler, damit keine Schleife entsteht) |
| `… --hook` | SessionStart-Hook: still, Abgleich mit 8 s Zeitlimit, einzige Ausgabe ist der Hinweis auf einen fehlenden Tagesbericht der letzten sieben Tage |

Endet immer mit 0; Fehler stehen auf stderr, betroffene Abschnitte bleiben „keine". Läuft aus jedem Ordner des Repos,
auch aus einem Worktree (Hauptordner = erste Zeile von `git worktree list`). Python 3 ≥ 3.9, nur Standardbibliothek.

## Auslöser

- **SessionStart-Hook** (`.claude/settings.json`, versioniert, gilt auf beiden Macs): `--hook`, Zeitlimit 20 s.
- **`tools/studio_abgleich.sh`** (ohne Option, `--charge`, `--nach-pull`): ruft `--still --ohne-abgleich` und spiegelt
  danach `berichte/`. `--berichte` spiegelt nur.
- **Trigger „Tagesbericht"** im Chat (siehe `WORKFLOW-Tagesbericht.md`).

## Mac-Name

`git config niro.mac "Studio-Mac"` bzw. `"MacBook"` (SETUP.md Schritt 2); sonst der Computername
(`scutil --get ComputerName`); `/` und `:` werden `-`. Umgebungsvariable `NIRO_STUDIO_MAC` überschreibt beides.

## Format `<Mac>.md`

    # Tagesstand <Mac> — <JJJJ-MM-TT>
    Stand: <JJJJ-MM-TT HH:MM> · Repo <Pfad> · HEAD <Branch> <Hash> · Sitzungen <n> · Commits <n>
    ## Git
    ### Auf main · ### Ungepusht · ### Branches ohne Commits heute · ### Unversioniert (<Worktree>, <Branch>) … · Stashes: n
    ## Chargen
    ### Protokoll-Einträge (Sammelzeile ab fünf gleichen Überschriften) · ### Neue Dateien unter Ergebnisse/
    ## Sitzungen
    ### <von>–<bis> · <Titel> · <Branch> · <n> Aufträge · <n> Tool-Fehler
    - Ordner · Aufträge (bis 12) · Schlussbericht (1.500 Zeichen) · Tool-Fehler (bis 5) · Dateien (bis 20) · Werkzeuge · Chargen
    ## Gedächtnis
    ## Hinweise   (Protokoll fehlt · Ohne Schlussbericht · Viele Tool-Fehler · Ungepusht · Worktree mit Änderungen · Fehler)

Leere Abschnitte enthalten „- keine". Tagesgrenzen in Ortszeit. Sitzungsquellen: alle Ordner
`~/.claude/projects/<Schlüssel>*` (Hauptordner, Worktrees, Unterordner); Subagenten-Verläufe und Sidechains zählen nicht.
`<Mac>.patch`: `git diff HEAD` je Worktree plus `git diff --no-index` je unversionierter Textdatei (≤ 1 MB), gesamt
höchstens 5 MB; wird bei jedem Lauf neu geschrieben, weil der Spiegel nie löscht.

## Umgebungsvariablen (Tests)

`NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_STUDIO_MAC`, `NIRO_STUDIO_HEUTE` (`JJJJ-MM-TT`), `NIRO_CLAUDE_PROJECTS_DIR`
(Standard `~/.claude/projects`), `NIRO_CLAUDE_MEMORY_DIR`, `NIRO_SAMMLER_ABGLEICH_CMD`, `NIRO_SAMMLER_ABGLEICH_TIMEOUT`
(Sekunden); für `studio_abgleich.sh`: `NIRO_SAMMLER_CMD` (Ersatz für den Sammler-Aufruf).

## Tests

```bash
python3 tools/tagesbericht/sammler_test.py     # alle *_test.py in diesem Ordner, Exit 0 = bestanden
sh tools/studio_abgleich_test.sh               # Tests 10/11: --berichte und Sammler-Aufruf
```
