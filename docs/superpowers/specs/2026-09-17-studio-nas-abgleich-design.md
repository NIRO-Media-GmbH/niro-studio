# Studio-Abgleich über das NAS (Spec)

Datum: 2026-09-17 · Status: Teile 1–3 im Chat vom User freigegeben („Ja"), Umsetzung beauftragt.

## Anlass

User 17.09.2026: „Was können wir noch aufs NAS machen, was Sinn macht? … Ich will, dass am Ende auf dem 2. Mac einfach
ein git pull nötig ist und er seine Sachen dann auch einsortiert."

Vorgeschichte:
- **Bewertung 16.09.** (Memory `studio-auf-nas-bewertung`): SMB über WLAN 14,8 ms je kleiner Datei statt 0,13 ms lokal →
  NAS nicht als Arbeitsordner; Vorschlag „Werkzeug über GitHub, `projects/` und Gedächtnis aufs NAS", Entscheidung offen.
- **17.09. vormittags:** NIRO-Grading-LUTs über den NAS-Ordner `03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading`
  und `tools/resolve/luts_sync.sh`, Abgleich nur beim Arbeiten (Commit 54ad111).
- **Befund heute:** Auf diesem Mac liegen Protokoll-Änderungen aus vier Chargen (Rappold, Craiss, Dold, Schmitt), die nie
  committet wurden — die Übergabe über GitHub verliert alles, was nicht gepusht ist.

Gemessen 17.09.: Verzeichnis-Vergleich über das NAS 625 Dateien in 0,7–1,4 s (rsync-Liste); `projects/` ohne Medien und
Caches (Filter unten) = 6.916 Dateien, 3,2 GB (MEK Imagefilm 0,9 GB, Schmitt 0,7 GB).

## Entscheidungen

| Frage | Entscheidung |
|---|---|
| Ist das NAS verfügbar? | **Immer** — das Zweit-MacBook arbeitet nie ohne NAS (User). Verknüpfungen aufs NAS sind zulässig. |
| Wie arbeiten die Macs an Chargen? | **Übergabe, nie gleichzeitig** (User) → Kopien mit „neuere Datei gewinnt", ohne Sperren. |
| Kanal für Chargen-Daten | **Alles über das NAS** (User). `projects/` wird nicht mehr auf GitHub versioniert; die Historie bleibt. |
| Ort auf dem NAS | `NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/` (User). |
| Gedächtnis | Verknüpfung (Symlink) des Claude-Gedächtnis-Ordners je Mac auf `NIRO Studio/claude-gedaechtnis/`. |
| Auslöser | Nach jedem `git pull` (Hooks), durch Claude vor und nach jeder Arbeit an einer Charge, jederzeit von Hand. Kein Hintergrunddienst (User 17.09.). |
| Resolve-Team-Bibliothek | Später, eigener Schritt (Zuordnung zu bisherigen Hand-Installationen prüfen). |

## Design

### 1. NAS-Ablage

    …/08_Claude Tools/NIRO Studio/
      projects/<Kunde>/<Projekt>/<Charge>/…     Spiegel des lokalen projects/ (Filter Abschnitt 2)
      claude-gedaechtnis/                       MEMORY.md + Notizen (Ziel der Verknüpfungen beider Macs)
    …/03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading/   unverändert (luts_sync.sh)

### 2. Abgleich-Regeln

- `rsync -rt --update --modify-window=2` in **beide Richtungen** (lokal → NAS, NAS → lokal); die neuere Datei gewinnt;
  **nichts wird gelöscht** (kein `--delete`). Rechte/Eigentümer werden nicht übertragen (SMB).
- **Ausgeschlossen:**
  - Dateien und Ordner: `.DS_Store`, `__pycache__/`, `node_modules/`, `venv/`, `work/`, `frames/`, `Fotos/`
  - Medien (Groß-/Kleinschreibung egal): `mov mp4 m4v mxf mts avi wav mp3 m4a aif aiff flac arw dng cr3 braw r3d`
  - Einzeldateien über 20 MB (`--max-size=20M`)
- **Folge der Regeln:** Eine gelöschte oder umbenannte Datei kommt vom anderen Stand zurück. Endgültig löschen heißt: lokal
  und auf dem NAS löschen.
- Medien, die Resolve von der lokalen Platte einbindet (z. B. `Ergebnisse/Renders`), brauchen auf dem anderen Mac
  weiterhin einen Relink — nicht im Umfang.

### 3. Skript `tools/studio_abgleich.sh`

POSIX-`sh`, läuft auch über eine Pipe (`git show … | sh -s -- …`): Repo = `git rev-parse --show-toplevel` im aktuellen
Ordner, sonst der Ordner über dem Skript.

| Aufruf | Wirkung |
|---|---|
| `sh tools/studio_abgleich.sh` | Schritte 1–4, 6 für alle Chargen |
| `… --charge "<Pfad>"` | Schritte 1–4, 6, aber Schritt 3 nur für diese Charge (Pfad relativ zum Repo oder absolut, muss unter `projects/` liegen) |
| `… --nach-pull` | Schritte 1–6 (so rufen es die Hooks) |
| `… --umstieg` | Einmalige Umstellung eines Macs (Abschnitt 6) |

Schritte:
1. **NAS prüfen:** Fehlt `…/08_Claude Tools`, Hinweis „NAS nicht verbunden — Abgleich später: sh tools/studio_abgleich.sh",
   Ende mit 0 (bei `--umstieg` mit 1).
2. **Gedächtnis:** Ziel `$HOME/.claude/projects/<Schlüssel>/memory`, Schlüssel = Repo-Pfad mit jedem Zeichen außer
   A–Z/a–z/0–9 als `-` (`/Users/jansantos/NIRO Studio` → `-Users-jansantos-NIRO-Studio`).
   - Ist das Ziel schon eine Verknüpfung auf `claude-gedaechtnis/` → nichts tun.
   - Ist es ein echter Ordner → Inhalt nach `claude-gedaechtnis/` abgleichen (neuere gewinnt), Ordner in
     `memory.vor-nas-<JJJJMMTT-HHMM>` umbenennen, Verknüpfung anlegen.
   - Fehlt es → Elternordner anlegen, Verknüpfung anlegen.
   - Zeigt eine Verknüpfung woandershin → nichts ändern, Hinweis.
3. **Chargen:** `projects/` ↔ `NIRO Studio/projects/` nach Abschnitt 2; gezählt werden geholte und hochgeladene Dateien.
4. **LUTs:** `sh tools/resolve/luts_sync.sh` (unverändert).
5. **Abhängigkeiten** (nur `--nach-pull`): geänderte Dateien = `git diff --name-only ORIG_HEAD HEAD` (nach Merge und
   Rebase gesetzt).
   - `tools/transcribe/pyproject.toml` → `tools/transcribe/venv/bin/pip install -q -e ".[dev]"` (fehlt das venv: Hinweis auf SETUP.md)
   - `tools/motion/package.json` oder `package-lock.json` → `npm install` in `tools/motion`
   - `tools/autocut/SETUP.md`, `tools/musik/README.md` oder `tools/sfx/README.md` geändert → Hinweis „Abhängigkeiten prüfen"
6. **Zusammenfassung** in einem Block, z. B. „NAS-Abgleich: 12 geholt, 3 hochgeladen · Gedächtnis verknüpft ·
   LUTs aktuell · Motion-Pakete aktualisiert".

Testbarkeit: `NIRO_STUDIO_REPO` (Repo-Pfad), `NIRO_STUDIO_NAS` (Ordner „NIRO Studio"), `NIRO_CLAUDE_MEMORY_DIR` (Gedächtnis-Ziel), `NIRO_PIP_CMD` und
`NIRO_NPM_CMD` (Ersatzbefehle für pip/npm), dazu die vorhandenen `NIRO_NAS_LUT_DIR`/`NIRO_RESOLVE_LUT_DIR`. Außer
`--umstieg` endet das Skript immer mit 0 und blockiert git nie.

### 4. Hooks

- `.githooks/post-merge` → `sh tools/studio_abgleich.sh --nach-pull`
- `.githooks/post-rewrite` → dasselbe, nur wenn `$1 = rebase`
- Voraussetzung `git config core.hooksPath .githooks` (SETUP.md Schritt 2; `--umstieg` setzt es).

### 5. Git-Umstellung

- `.gitignore`: Positivliste für `projects/` ersetzt durch `/projects/` (komplett ignoriert), mit Verweis auf diesen Spec.
- `git rm -r -q --cached projects` — nur aus der Versionierung, die Dateien bleiben lokal.

### 6. Umstieg eines Macs (einmalig, statt des ersten Pulls)

    git fetch && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg

1. `git config core.hooksPath .githooks`.
2. NAS prüfen (sonst Abbruch mit 1, nichts geändert).
3. Lokales `projects/` → NAS hochladen (nur diese Richtung); rsync-Fehler → Abbruch mit 1, nichts verworfen.
4. Gedächtnis-Verknüpfung (Schritt 2).
5. `git reset -q -- projects` und `git checkout -q -- projects`: verwirft nur git-Änderungen an versionierten Dateien unter
   `projects/` — deren Inhalt liegt seit Punkt 3 auf dem NAS. Unversionierte Dateien bleiben unberührt.
6. `git pull --ff-only`; der Hook holt danach den vollständigen, neuesten Stand. Schlägt der Pull fehl (eigene lokale
   Commits), Hinweis mit dem nächsten Schritt.

### 7. Claude-Regeln (CLAUDE.md)

- **Protokoll-Pflicht erweitert:** Vor der Arbeit an einer Charge `sh tools/studio_abgleich.sh --charge "<Charge>"`
  (neuesten Stand holen), nach der Arbeit mit dem Protokoll-Eintrag dasselbe (Stand aufs NAS).
- **Projektstruktur:** `projects/` liegt lokal, der gemeinsame Stand auf dem NAS-Spiegel; nicht auf GitHub.
- Die Resolve-Regel zu `luts_sync.sh` bleibt; `studio_abgleich.sh` ruft es mit auf.

## Fehlerbehandlung

| Lage | Verhalten |
|---|---|
| NAS nicht verbunden | Hinweis, lokal bleibt alles, Ende 0 (`--umstieg`: 1, nichts geändert) |
| rsync-Fehler (z. B. SMB-Sperre) | Meldung mit rsync-Code und betroffener Richtung, Ende 0; `--umstieg`: Abbruch 1 vor dem Verwerfen |
| Gedächtnis-Verknüpfung zeigt woandershin | nichts ändern, Hinweis |
| venv fehlt bei geänderter pyproject | Hinweis auf SETUP.md |
| `npm install` scheitert | Meldung, Ende 0 |
| `--charge` außerhalb von `projects/` | Meldung, nichts abgeglichen |
| `git pull --ff-only` scheitert beim Umstieg | Hinweis: lokale Commits prüfen, danach `git pull` |

## Tests (`tools/studio_abgleich_test.sh`, ohne echtes NAS und Gedächtnis)

- Abgleich beide Richtungen: neuere Datei gewinnt, keine Löschung.
- Ausschlüsse: Medien (auch Großbuchstaben), `work/`, `frames/`, `Fotos/`, Datei > 20 MB bleiben lokal.
- `--charge` gleicht nur die Charge ab; Pfad außerhalb `projects/` wird abgewiesen.
- Gedächtnis: echter Ordner → zusammengeführt, gesichert, verknüpft; zweiter Lauf ändert nichts; fremde Verknüpfung bleibt.
- NAS fehlt → Hinweis, Ende 0.
- `--nach-pull` in einem Test-Repo: geänderte `tools/motion/package.json` → npm-Schritt ausgelöst (Befehl per
  Umgebungsvariable durch ein Echo ersetzt); unveränderte Dateien → kein Schritt.
- `--umstieg` in einem Test-Klon mit versionierten `projects/`-Dateien und einer ungesicherten Änderung: Änderung landet
  auf dem Test-NAS, Pull läuft durch, nach dem Hook sind alle Dateien mit neuestem Inhalt da.

## Doku

- `CLAUDE.md` (Projektstruktur, Protokoll-Pflicht), `SETUP.md` (Schritt 2: Hooks + Studio-Abgleich; Umstieg-Befehl),
  `.gitignore`.
- Memory: `studio-auf-nas-bewertung` (umgesetzt), `github-push-referenzen-oeffentlich` (projects/ nicht mehr auf GitHub),
  `zweit-macbook-motion-quellen`.

## Nicht im Umfang

Relink lokaler Medien in Resolve; automatische Installation der Team-Resolve-Bibliothek (LUT-Ordner, DCTLs, Fusion-Titel,
Schriften); Konfliktlösung bei gleichzeitiger Arbeit; Umschreiben der GitHub-Historie; Gedächtnis-Ersatz ohne NAS;
Hintergrunddienst.

## Reihenfolge

1. Skript, Hooks, Testskript; Tests grün.
2. Auf diesem Mac: Probelauf (Zahlen), erster Abgleich, Gedächtnis-Verknüpfung.
3. Git-Umstellung, Doku, Commit, Push.
4. User führt auf dem anderen Mac den Umstieg-Befehl aus.
