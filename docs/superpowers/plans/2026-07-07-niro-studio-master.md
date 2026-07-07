# NIRO Studio Master-Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Master-Ordner „NIRO Studio" mit den zwei Sub-Tools (transcribe, motion), zweistufigen Projektordnern `projects/<Kunde>/<Projekt>/` und einer Master-CLAUDE.md, die alle drei Workflows verbindet.

**Architecture:** Reine Umstrukturierung + Dokumentation — kein Python/TS-Code wird geändert. Sub-Tools bleiben eigenständige Repos unter `tools/`; Projektmedien wandern in `projects/`; Remotion erreicht Inputs per Symlink in `public/projects/`.

**Tech Stack:** zsh/mv/ln, git, Python venv (3.14), Remotion/npm.

## Global Constraints

- Studio-Wurzel: `/Users/jansantos/NIRO Studio` (mit Leerzeichen — Pfade immer quoten!)
- Nichts wird gelöscht, nur verschoben (`mv` auf demselben Volume) — außer `venv/` (wird neu erstellt) und `.DS_Store`.
- Mediendateien (mp4/mov/wav/gif/webm) kommen NIE in git.
- `NIRO Transcribe` wird als LETZTES verschoben (laufende Session arbeitet darin).
- Baseline: `pytest` = 55 passed. Nach Abschluss muss das wieder gelten.
- Abgeschlossene Projekte (`WTN 5x Ads`, `public/`-Bestand von motion) bleiben unangetastet.

---

### Task 1: Studio-Grundgerüst + Master-CLAUDE.md

**Files:**
- Create: `/Users/jansantos/NIRO Studio/.gitignore`
- Create: `/Users/jansantos/NIRO Studio/CLAUDE.md`
- Create: Ordner `projects/`, `tools/`, `docs/`

**Interfaces:**
- Produces: Studio-Wurzel, auf die alle folgenden Tasks aufbauen; Trigger-Konventionen für alle drei Workflows.

- [ ] **Step 1: Ordner anlegen**

```bash
mkdir -p "/Users/jansantos/NIRO Studio/projects" "/Users/jansantos/NIRO Studio/tools" "/Users/jansantos/NIRO Studio/docs"
```

- [ ] **Step 2: .gitignore schreiben**

```gitignore
# Sub-Repos und Projektdaten sind nicht Teil des Master-Repos
tools/
projects/
.DS_Store
```

- [ ] **Step 3: CLAUDE.md schreiben**

```markdown
# NIRO Studio

Master-Werkzeug von NIRO Media: drei Funktionen, ein Projektsystem, eine Session.

## Projektstruktur

Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/`:

    projects/<Kunde>/<Projekt>/
    ├── audio/            Interview-WAVs
    ├── script/           Konzept-PDF
    ├── cache/ output/ work/   Interview-Pipeline (Transkripte, O-Ton-Pläne)
    ├── footage/          Sortierer-Arbeitsdateien (Pläne, Manifeste, Undo-Logs)
    └── motion/
        ├── inputs/       Video-Inputs für Remotion
        └── renders/      fertige Animationen

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.

## Die drei Funktionen (Trigger)

| Trigger im Chat | Funktion | Anleitung |
|---|---|---|
| „Video-Auswahl: <Kunde>/<Projekt>" | Interviews → sortierte O-Ton-Pläne | `tools/transcribe/WORKFLOW.md` |
| „Footage sortieren: <Pfad>" + Konzept | Roh-MP4s nach Konzept-Script sortieren | `tools/transcribe/WORKFLOW-Footage.md` |
| „Animation: <Kunde>/<Projekt>" | Remotion Motion Graphics | `tools/motion/WORKFLOW-Motion.md` |

Beim Trigger die jeweilige Workflow-Datei lesen und ihr folgen.
Projektpfad-Konvention überall: `projects/<Kunde>/<Projekt>/` (relativ zu
dieser Studio-Wurzel).

## Umgebung

- **Python (transcribe):** `tools/transcribe/venv/bin/python`; `.env` mit
  API-Keys liegt in `tools/transcribe/.env`.
- **Remotion (motion):** `cd tools/motion && npm run studio`; Kompositionen
  und `brand.json` pro Kunde in `tools/motion/src/clients/<kunde>/`.
- **Neues Projekt:** Ordner nach Bedarf anlegen, z. B.
  `mkdir -p "projects/<Kunde>/<Projekt>/audio"`.
```

- [ ] **Step 4: git init + Erst-Commit**

```bash
cd "/Users/jansantos/NIRO Studio" && git init -q && git add -A && git commit -q -m "feat: NIRO Studio Grundgerüst (Master-CLAUDE.md, Projektstruktur)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Verifizieren**

Run: `ls "/Users/jansantos/NIRO Studio"` → `CLAUDE.md docs projects tools`; `git -C "/Users/jansantos/NIRO Studio" log --oneline` → 1 Commit.

---

### Task 2: Motion-Tool verschieben + git init

**Files:**
- Move: `/Users/jansantos/NIROmotiongraphics` → `/Users/jansantos/NIRO Studio/tools/motion`
- Modify: `tools/motion/.gitignore`

**Interfaces:**
- Consumes: Studio-Wurzel aus Task 1.
- Produces: `tools/motion/` als git-Repo; Grundlage für Task 3/4.

- [ ] **Step 1: Verschieben**

```bash
mv /Users/jansantos/NIROmotiongraphics "/Users/jansantos/NIRO Studio/tools/motion"
```

- [ ] **Step 2: .gitignore erweitern** (Medienquellen zusätzlich ausschließen; `*.mp4` etc. sind schon drin)

An bestehende `.gitignore` anhängen:

```gitignore
Videos/
Video inputs/
public/projects/
```

- [ ] **Step 3: git init + Erst-Commit**

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion" && git init -q && git add -A && git commit -q -m "feat: Erst-Commit NIRO Motion Graphics (Code, ohne Medien)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Verifizieren (Build intakt)**

Run: `cd "/Users/jansantos/NIRO Studio/tools/motion" && npx tsc --noEmit`
Expected: Exit 0 (keine Fehler). Zusätzlich `git status --short` → leer bis auf ignorierte Dateien.

---

### Task 3: WORKFLOW-Motion.md (Motion-Workflow dokumentieren)

**Files:**
- Create: `/Users/jansantos/NIRO Studio/tools/motion/WORKFLOW-Motion.md`

**Interfaces:**
- Consumes: Trigger-Konvention aus Task 1.
- Produces: Workflow-Datei, auf die Master-CLAUDE.md verweist.

- [ ] **Step 1: WORKFLOW-Motion.md schreiben**

```markdown
# Workflow — Animation (Motion Graphics, Claude in der Session)

Auslöser: **„Animation: <Kunde>/<Projekt>"** (+ Beschreibung, was animiert
werden soll).

Voraussetzung: `npm install` gelaufen (node_modules vorhanden).

Konventionen:
- Kompositionen + `brand.json` pro Kunde: `src/clients/<kunde>/`
  (kebab-case). Neuer Kunde: `npm run new:client`; neues Projekt:
  `npm run new:project`.
- **Inputs** liegen beim Projekt: `../../projects/<Kunde>/<Projekt>/motion/inputs/`.
  Für Remotion per Symlink erreichbar machen:
  `ln -s "../../../../projects/<Kunde>/<Projekt>/motion/inputs" "public/projects/<kunde>-<projekt>"`
  → im Code: `staticFile("projects/<kunde>-<projekt>/<datei>")`.
- **Renders** gehen direkt ins Projekt (nicht nach `out/`):
  `npx remotion render src/index.ts <CompId> "../../projects/<Kunde>/<Projekt>/motion/renders/<name>.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`
  (Web-Varianten: `--codec=h264 --crf=18`.)
- Alte `render:*`-Scripts in package.json gelten für Bestandsprojekte
  (Ausgabe nach `out/`); neue Projekte bekommen KEINE neuen package.json-
  Scripts mehr, sondern direkte render-Kommandos mit Projektpfad.

Ablauf:
1. Projektordner prüfen/anlegen (`motion/inputs/`, `motion/renders/`),
   Symlink setzen falls Inputs genutzt werden.
2. Komposition bauen/ändern in `src/clients/<kunde>/projects/<projekt>/`.
3. **Pre-Delivery Review nach CLAUDE.md** (Face Zone, Safe Zone, Guides aus
   vor Final-Render) — Pflicht.
4. Rendern in `projects/<Kunde>/<Projekt>/motion/renders/`.
5. Im Chat bilanzieren: was gerendert wurde, wohin, Auffälligkeiten.
```

- [ ] **Step 2: Commit**

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion" && git add WORKFLOW-Motion.md && git commit -q -m "docs: WORKFLOW-Motion (Trigger, Projekt-Inputs/Renders, Review-Pflicht)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Aktive Projekte migrieren

**Files:**
- Move: `NIRO Transcribe/projects/LohiBW Recruiting` → `NIRO Studio/projects/LohiBW/Recruiting`
- Move: `NIRO Transcribe/projects/REM 1x Website-Dienstleistungsfilm` → `NIRO Studio/projects/REM/Website-Dienstleistungsfilm`
- Move: `tools/motion/Video inputs/Seniorenstiftung` → `NIRO Studio/projects/Seniorenstiftung/Recruiting/motion/inputs`
- Move: `tools/motion/out/rem-dachbeschichtung-v2-notext-1080p.mp4` → `NIRO Studio/projects/REM/Dachbeschichtung/motion/renders/`
- Create: Symlink `tools/motion/public/projects/seniorenstiftung-recruiting`

**Interfaces:**
- Consumes: Studio-Wurzel (Task 1), tools/motion (Task 2).
- Produces: befüllte `projects/`-Struktur; `WTN 5x Ads` bleibt in transcribe/projects (abgeschlossen), WTN-Motion-Daten bleiben in `Video inputs/WTN` + `public/wtn` (abgeschlossen).

- [ ] **Step 1: Transcribe-Projekte verschieben**

```bash
mkdir -p "/Users/jansantos/NIRO Studio/projects/LohiBW" "/Users/jansantos/NIRO Studio/projects/REM"
mv "/Users/jansantos/NIRO Transcribe/projects/LohiBW Recruiting" "/Users/jansantos/NIRO Studio/projects/LohiBW/Recruiting"
mv "/Users/jansantos/NIRO Transcribe/projects/REM 1x Website-Dienstleistungsfilm" "/Users/jansantos/NIRO Studio/projects/REM/Website-Dienstleistungsfilm"
```

- [ ] **Step 2: Seniorenstiftung-Inputs + REM-Render verschieben**

```bash
mkdir -p "/Users/jansantos/NIRO Studio/projects/Seniorenstiftung/Recruiting/motion" "/Users/jansantos/NIRO Studio/projects/REM/Dachbeschichtung/motion/renders"
mv "/Users/jansantos/NIRO Studio/tools/motion/Video inputs/Seniorenstiftung" "/Users/jansantos/NIRO Studio/projects/Seniorenstiftung/Recruiting/motion/inputs"
mv "/Users/jansantos/NIRO Studio/tools/motion/out/rem-dachbeschichtung-v2-notext-1080p.mp4" "/Users/jansantos/NIRO Studio/projects/REM/Dachbeschichtung/motion/renders/"
```

- [ ] **Step 3: Symlink für Remotion**

```bash
mkdir -p "/Users/jansantos/NIRO Studio/tools/motion/public/projects"
ln -s "../../../../projects/Seniorenstiftung/Recruiting/motion/inputs" "/Users/jansantos/NIRO Studio/tools/motion/public/projects/seniorenstiftung-recruiting"
```

- [ ] **Step 4: Verifizieren**

Run: `ls "/Users/jansantos/NIRO Studio/projects/LohiBW/Recruiting"` → manifest.json, zuordnungsplan.md, …
Run: `ls -L "/Users/jansantos/NIRO Studio/tools/motion/public/projects/seniorenstiftung-recruiting"` → die 5 MP4s + transcripts (Symlink auflösbar).

---

### Task 5: Transcribe-Docs auf neue Konvention umstellen

**Files:**
- Modify: `NIRO Transcribe/WORKFLOW.md` (Ordnerkonvention)
- Modify: `NIRO Transcribe/WORKFLOW-Footage.md` (Arbeitsdateien-Pfad)
- Modify: `NIRO Transcribe/README.md`, `NIRO Transcribe/SETUP.md` (Kontext NIRO Studio)

**Interfaces:**
- Consumes: Pfadkonvention aus Task 1.
- Produces: konsistente Doku vor dem Umzug (Task 6).

- [ ] **Step 1: WORKFLOW.md — Konvention ersetzen**

Alt: `projects/<Name>/audio/` … Neu (Zeilen 5–7 ersetzen):

```markdown
   Ordnerkonvention pro Dreh (NIRO-Studio-Wurzel): `projects/<Kunde>/<Projekt>/audio/`
   (WAVs) und `projects/<Kunde>/<Projekt>/script/` (Konzept-PDF mit echtem Namen).
   Ausgabe → `…/output/`, Cache → `…/cache/`.
```

- [ ] **Step 2: WORKFLOW-Footage.md — Arbeitsdateien-Pfad ersetzen**

Alt: „Arbeitsdateien … im Repo unter `projects/<Name>/`" → Neu:

```markdown
Konvention: Rohmaterial `<Projekt-SSD>/01_Footage/<Kamera>/…`; Ausgabe →
`<Projekt-SSD>/sortiert/`. Arbeitsdateien (cache, index, plan, manifest, log)
in der NIRO-Studio-Wurzel unter `projects/<Kunde>/<Projekt>/footage/`.
```

- [ ] **Step 3: README.md + SETUP.md — Hinweis ergänzen**

README-Kopf ergänzen: „Teil von **NIRO Studio** (`~/NIRO Studio/`): Master-Einstieg
und Projektordner liegen dort, siehe `../../CLAUDE.md`. Dieses Tool liefert
Interview-Pipeline + Footage-Sortierer." SETUP.md: venv-Pfad-Hinweis
(`tools/transcribe/venv`).

- [ ] **Step 4: Commit**

```bash
cd "/Users/jansantos/NIRO Transcribe" && git add -A && git commit -q -m "docs: Pfadkonvention projects/<Kunde>/<Projekt> (NIRO Studio)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Transcribe verschieben (LETZTER Umbau-Schritt) + venv neu + Smoke-Tests

**Files:**
- Move: `/Users/jansantos/NIRO Transcribe` → `/Users/jansantos/NIRO Studio/tools/transcribe`
- Recreate: `tools/transcribe/venv/`

**Interfaces:**
- Consumes: Tasks 1–5 abgeschlossen, transcribe-Repo committed (clean).
- Produces: funktionsfähiges Gesamtsystem unter `NIRO Studio/`.

- [ ] **Step 1: Sicherstellen, dass das Repo clean ist**

Run: `git -C "/Users/jansantos/NIRO Transcribe" status --porcelain` → leer (sonst erst committen).

- [ ] **Step 2: Verschieben + venv neu**

```bash
mv "/Users/jansantos/NIRO Transcribe" "/Users/jansantos/NIRO Studio/tools/transcribe"
cd "/Users/jansantos/NIRO Studio/tools/transcribe" && rm -rf venv && python3 -m venv venv && ./venv/bin/pip -q install -e ".[dev]"
```

- [ ] **Step 3: Tests laufen lassen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/transcribe" && ./venv/bin/python -m pytest -q`
Expected: `55 passed` (wie Baseline).

- [ ] **Step 4: Remotion-Smoke-Test**

Run: `cd "/Users/jansantos/NIRO Studio/tools/motion" && npx remotion compositions src/index.ts 2>&1 | head -20`
Expected: Kompositions-Liste (WTN-…, Seniorenstiftung-…, …) ohne Fehler.

- [ ] **Step 5: git-Integrität prüfen**

Run: `git -C "/Users/jansantos/NIRO Studio/tools/transcribe" log --oneline -3` → Historie vorhanden.

---

### Task 7: Claude-Memory übertragen + Abschlussbilanz

**Files:**
- Create: `~/.claude/projects/-Users-jansantos-NIRO-Studio/memory/` (Kopie + Update der bisherigen Memories)

**Interfaces:**
- Consumes: fertige Struktur aus Task 6.
- Produces: Memory für künftige Sessions in `NIRO Studio/`; Abschlussmeldung an den User.

- [ ] **Step 1: Memory kopieren und aktualisieren**

```bash
mkdir -p "/Users/jansantos/.claude/projects/-Users-jansantos-NIRO-Studio/memory"
cp "/Users/jansantos/.claude/projects/-Users-jansantos-NIRO-Transcribe/memory/"*.md "/Users/jansantos/.claude/projects/-Users-jansantos-NIRO-Studio/memory/"
```

Danach die kopierten Dateien inhaltlich aktualisieren: neue Pfade
(`tools/transcribe`, `tools/motion`, `projects/<Kunde>/<Projekt>`), neues
Memory `niro-studio.md` (Struktur + Trigger) anlegen, MEMORY.md-Index anpassen.
Auch im ALTEN Memory-Verzeichnis einen Verweis hinterlegen („Projekt umgezogen
nach NIRO Studio").

- [ ] **Step 2: Abschlussbilanz an den User**

Melden: neue Struktur, was verschoben wurde, was liegen blieb (WTN, public/-
Bestand), dass nächste Sessions in `NIRO Studio/` geöffnet werden sollen,
Testergebnisse.
