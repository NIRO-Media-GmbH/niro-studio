# Projektstruktur mit Chargen-Ebene — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle Projektordner auf das Schema `projects/<Kunde>/<Projekt>/<Charge>/{Material,Ergebnisse,_intern}` migrieren und Doku + Code nachziehen.

**Architecture:** Reine Datei-Reorganisation plus Pfad-Konstanten-Änderung in zwei Python-Modulen. Drei getrennte Git-Repos: Master (`CLAUDE.md`, Specs), `tools/transcribe` (Code, Tests, 2 Workflow-Docs), `tools/motion` (1 Workflow-Doc). `projects/` ist gitignored → Migration per `mv`, kein git.

**Tech Stack:** bash (mv, ln), Python/pytest (tools/transcribe, venv unter `tools/transcribe/venv`).

## Global Constraints

- Studio-Wurzel: `/Users/jansantos/NIRO Studio` (Leerzeichen im Pfad → immer quoten).
- Chargen-Name Bestandsprojekte: `2026-07 Erster Dreh` (Nutzer benennt ggf. um).
- Neue Ordnernamen exakt: `Material/Audio`, `Material/Konzept`, `Material/Video`, `Ergebnisse/O-Ton-Pläne`, `Ergebnisse/Sortierung`, `Ergebnisse/Renders`, `_intern`.
- Nichts löschen, nur verschieben.
- Testlauf: `cd tools/transcribe && venv/bin/python -m pytest -q`.

---

### Task 1: Projektdaten migrieren (alle 4 Projekte) + Remotion-Symlink

**Files:**
- Verschieben unter `projects/` (gitignored, kein Commit)
- Symlink: `tools/motion/public/projects/seniorenstiftung-recruiting`

**Interfaces:**
- Produces: neue Ordnerstruktur, auf die Tasks 2–5 sich in Doku/Code beziehen.

- [ ] **Step 1: LohiBW/Recruiting migrieren**

```bash
cd "/Users/jansantos/NIRO Studio/projects/LohiBW/Recruiting"
mkdir -p "2026-07 Erster Dreh/Material/Konzept" "2026-07 Erster Dreh/Ergebnisse/Sortierung" "2026-07 Erster Dreh/_intern"
mv script/* "2026-07 Erster Dreh/Material/Konzept/" && rmdir script
mv zuordnungsplan.md "2026-07 Erster Dreh/Ergebnisse/Sortierung/"
mv cache work cls build_plan.py run_phase1.py run_phase3.py manifest.json \
   script_structured.json transcripts_index.json phase1_progress.txt \
   phase1_stdout.log "2026-07 Erster Dreh/_intern/"
```

- [ ] **Step 2: REM/Website-Dienstleistungsfilm migrieren**

```bash
cd "/Users/jansantos/NIRO Studio/projects/REM/Website-Dienstleistungsfilm"
mkdir -p "2026-07 Erster Dreh/Material" "2026-07 Erster Dreh/Ergebnisse" "2026-07 Erster Dreh/_intern"
mv audio "2026-07 Erster Dreh/Material/Audio"
mv output "2026-07 Erster Dreh/Ergebnisse/O-Ton-Pläne"
mv cache work "2026-07 Erster Dreh/_intern/"
```

- [ ] **Step 3: REM/Dachbeschichtung + Seniorenstiftung/Recruiting migrieren**

```bash
cd "/Users/jansantos/NIRO Studio/projects/REM/Dachbeschichtung"
mkdir -p "2026-07 Erster Dreh/Ergebnisse"
mv motion/renders "2026-07 Erster Dreh/Ergebnisse/Renders" && rmdir motion
cd "/Users/jansantos/NIRO Studio/projects/Seniorenstiftung/Recruiting"
mkdir -p "2026-07 Erster Dreh/Material"
mv motion/inputs "2026-07 Erster Dreh/Material/Video" && rmdir motion
```

- [ ] **Step 4: Remotion-Symlink neu setzen und prüfen**

```bash
cd "/Users/jansantos/NIRO Studio/tools/motion/public/projects"
rm seniorenstiftung-recruiting
ln -s "../../../../projects/Seniorenstiftung/Recruiting/2026-07 Erster Dreh/Material/Video" seniorenstiftung-recruiting
ls -l seniorenstiftung-recruiting && ls seniorenstiftung-recruiting/
```
Expected: Symlink zeigt auf neuen Pfad, `ls` durch den Link listet die Inputs (kein Fehler).

- [ ] **Step 5: Struktur verifizieren**

```bash
find "/Users/jansantos/NIRO Studio/projects" -maxdepth 4 -type d | sort
```
Expected: Jedes Projekt hat genau einen Chargen-Ordner `2026-07 Erster Dreh` mit den neuen Unterordnern; keine alten Ordner (`audio`, `script`, `output`, `cache`, `work`, `cls`, `motion`, `footage`) mehr auf Projektebene.

---

### Task 2: `project.py` auf neue Pfade (TDD)

**Files:**
- Modify: `tools/transcribe/src/niro_transcribe/project.py:21-25`
- Test: `tools/transcribe/tests/test_project.py`

**Interfaces:**
- Produces: `Project.open(root)` mit `audio_dir=root/"Material"/"Audio"`, `cache_dir=root/"_intern"/"cache"`, `output_dir=root/"Ergebnisse"/"O-Ton-Pläne"`, `skript_pdf=root/"Material"/"Konzept"/"skript.pdf"`, `briefs_yaml=root/"_intern"/"briefs.yaml"`. `root` ist der **Chargen-Ordner**.

- [ ] **Step 1: Test anpassen (erst rot)**

`tests/test_project.py`, Funktion `test_open_creates_dirs` ersetzen:

```python
def test_open_creates_dirs(tmp_path):
    proj = Project.open(tmp_path)
    assert proj.audio_dir == tmp_path / "Material" / "Audio"
    assert proj.cache_dir == tmp_path / "_intern" / "cache"
    assert proj.output_dir == tmp_path / "Ergebnisse" / "O-Ton-Pläne"
    assert proj.audio_dir.is_dir()
    assert proj.cache_dir.is_dir()
    assert proj.output_dir.is_dir()
    assert proj.skript_pdf == tmp_path / "Material" / "Konzept" / "skript.pdf"
    assert proj.briefs_yaml == tmp_path / "_intern" / "briefs.yaml"
```

- [ ] **Step 2: Test rot sehen**

Run: `cd "/Users/jansantos/NIRO Studio/tools/transcribe" && venv/bin/python -m pytest tests/test_project.py -q`
Expected: FAIL (Pfad-Assertions).

- [ ] **Step 3: `project.py` ändern**

In `Project.open` die Zuweisungen ersetzen:

```python
        proj = cls(
            root=root,
            audio_dir=root / "Material" / "Audio",
            cache_dir=root / "_intern" / "cache",
            output_dir=root / "Ergebnisse" / "O-Ton-Pläne",
            skript_pdf=root / "Material" / "Konzept" / "skript.pdf",
            briefs_yaml=root / "_intern" / "briefs.yaml",
        )
```

- [ ] **Step 4: Test grün sehen**

Run: `venv/bin/python -m pytest tests/test_project.py -q`
Expected: PASS (2 Tests).

- [ ] **Step 5: Commit (Repo tools/transcribe)**

```bash
cd "/Users/jansantos/NIRO Studio/tools/transcribe"
git add src/niro_transcribe/project.py tests/test_project.py
git commit -m "feat: Projektpfade auf Material/Ergebnisse/_intern-Schema"
```

---

### Task 3: `footage/pipeline.py` auf `_intern/` (TDD)

**Files:**
- Modify: `tools/transcribe/src/niro_transcribe/footage/pipeline.py:18-20`
- Test: `tools/transcribe/tests/footage/test_pipeline.py`

**Interfaces:**
- Consumes: —
- Produces: `transcribe_all(footage_root, project_dir, ...)` schreibt `cache`, `work`, `transcripts_index.json` nach `project_dir/"_intern"/…`. `project_dir` ist der **Chargen-Ordner**.

- [ ] **Step 1: Test anpassen (erst rot)**

`tests/footage/test_pipeline.py`, Zeilen 39 und 42 ersetzen:

```python
    idx = json.loads((proj / "_intern" / "transcripts_index.json").read_text(encoding="utf-8"))
```
```python
    assert not (proj / "_intern" / "work" / "GOOD.wav").exists()
```

- [ ] **Step 2: Test rot sehen**

Run: `venv/bin/python -m pytest tests/footage/test_pipeline.py -q`
Expected: FAIL (FileNotFoundError auf `_intern/transcripts_index.json`).

- [ ] **Step 3: `pipeline.py` ändern**

Zeilen 17–20 ersetzen durch:

```python
    project_dir = Path(project_dir)
    intern = project_dir / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    index_path = intern / "transcripts_index.json"
```

- [ ] **Step 4: Test grün sehen**

Run: `venv/bin/python -m pytest tests/footage/test_pipeline.py -q`
Expected: PASS.

- [ ] **Step 5: Commit (Repo tools/transcribe)**

```bash
git add src/niro_transcribe/footage/pipeline.py tests/footage/test_pipeline.py
git commit -m "feat: Footage-Arbeitsdateien nach _intern/"
```

---

### Task 4: Workflow-Dokus umstellen (transcribe + motion)

**Files:**
- Modify: `tools/transcribe/WORKFLOW.md:5-15,27-28`
- Modify: `tools/transcribe/WORKFLOW-Footage.md:9-11,17-18`
- Modify: `tools/motion/WORKFLOW-Motion.md:12-17,24,29`

**Interfaces:**
- Consumes: Pfad-Schema aus Task 2/3.
- Produces: Doku, auf die CLAUDE.md (Task 5) verweist.

- [ ] **Step 1: WORKFLOW.md anpassen**

Ordnerkonvention (Zeilen 5–7) ersetzen durch:

```
   Ordnerkonvention pro Charge (NIRO-Studio-Wurzel):
   `projects/<Kunde>/<Projekt>/<Charge>/Material/Audio/` (WAVs) und
   `…/<Charge>/Material/Konzept/` (Konzept-PDF mit echtem Namen).
   Ausgabe → `…/<Charge>/Ergebnisse/O-Ton-Pläne/`, Cache → `…/<Charge>/_intern/cache/`.
```

Weitere Ersetzungen im Fließtext: `audio/` → `Material/Audio/` (Zeilen 10, 12), `cache/` und `output/` → `_intern/cache/` und `Ergebnisse/O-Ton-Pläne/` (Zeile 10), `<script>/*.pdf` → `<Material/Konzept>/*.pdf` (Zeile 14), `output/<video>.md` und `output/uebersicht.md` → `Ergebnisse/O-Ton-Pläne/<video>.md` und `Ergebnisse/O-Ton-Pläne/uebersicht.md` (Zeilen 27–28).

- [ ] **Step 2: WORKFLOW-Footage.md anpassen**

Zeilen 9–11 ersetzen durch:

```
Konvention: Rohmaterial `<Projekt-SSD>/01_Footage/<Kamera>/…`; Ausgabe →
`<Projekt-SSD>/sortiert/`. Arbeitsdateien (cache, index, manifest, log) unter
`projects/<Kunde>/<Projekt>/<Charge>/_intern/`; der fertige Zuordnungsplan →
`…/<Charge>/Ergebnisse/Sortierung/zuordnungsplan.md`.
```

Zeile 18 (`schreibt transcripts_index.json`) ergänzen zu `schreibt _intern/transcripts_index.json`. In Schritt 4 hinter `zuordnungsplan.md`-Text ergänzen: `(ablegen unter Ergebnisse/Sortierung/)`.

- [ ] **Step 3: WORKFLOW-Motion.md anpassen**

Zeile 3: Auslöser um Charge ergänzen: `**„Animation: <Kunde>/<Projekt>[/<Charge>]"**`. Zeilen 12–17 ersetzen durch:

```
- **Inputs** liegen beim Projekt: `../../projects/<Kunde>/<Projekt>/<Charge>/Material/Video/`.
  Für Remotion per Symlink erreichbar machen:
  `ln -s "../../../../projects/<Kunde>/<Projekt>/<Charge>/Material/Video" "public/projects/<kunde>-<projekt>"`
  → im Code: `staticFile("projects/<kunde>-<projekt>/<datei>")`.
- **Renders** gehen direkt ins Projekt (nicht nach `out/`):
  `npx remotion render src/index.ts <CompId> "../../projects/<Kunde>/<Projekt>/<Charge>/Ergebnisse/Renders/<name>.mov" --image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444`
```

Zeile 24: `(motion/inputs/, motion/renders/)` → `(<Charge>/Material/Video/, <Charge>/Ergebnisse/Renders/)`. Zeile 29: `motion/renders/` → `<Charge>/Ergebnisse/Renders/`.

- [ ] **Step 4: Commits (beide Repos)**

```bash
cd "/Users/jansantos/NIRO Studio/tools/transcribe"
git add WORKFLOW.md WORKFLOW-Footage.md
git commit -m "docs: Workflows auf Chargen-Struktur Material/Ergebnisse/_intern"
cd "/Users/jansantos/NIRO Studio/tools/motion"
git add WORKFLOW-Motion.md
git commit -m "docs: Motion-Workflow auf Chargen-Struktur"
```

---

### Task 5: Master-CLAUDE.md + Memory aktualisieren

**Files:**
- Modify: `CLAUDE.md` (Projektstruktur-Block, Trigger-Tabelle, Beispiel-mkdir)
- Modify: `~/.claude/projects/-Users-jansantos-NIRO-Studio/memory/niro-studio.md` (+ ggf. `footage-sortierer.md`, `niro-transcribe-project.md`)

**Interfaces:**
- Consumes: Struktur aus Task 1, Doku aus Task 4.

- [ ] **Step 1: CLAUDE.md-Strukturblock ersetzen**

Neuer Block (ersetzt den bisherigen `projects/…`-Baum samt Erklärung):

```
Alle Projektdaten liegen unter `projects/<Kunde>/<Projekt>/<Charge>/`.
Chargen-Name: `JJJJ-MM Beschreibung` (z. B. „2026-07 Erster Dreh") — die
Chargen-Ebene existiert immer, auch bei nur einer Charge.

    projects/<Kunde>/<Projekt>/<Charge>/
    ├── Material/           was reinkommt
    │   ├── Audio/             Interview-WAVs
    │   ├── Konzept/           Konzept-PDF
    │   └── Video/             Inputs für Animationen
    ├── Ergebnisse/         was fertig ist
    │   ├── O-Ton-Pläne/       Interview-Pipeline
    │   ├── Sortierung/        Zuordnungspläne Footage
    │   └── Renders/           fertige Animationen
    └── _intern/            was die Tools brauchen (cache, work, Logs, Manifeste)

Rohes Drehmaterial bleibt auf externen SSDs; hier liegen nur Arbeits- und
Ergebnisdateien. Unterordner nur anlegen, wenn die Funktion genutzt wird.
```

Trigger-Tabelle: `„Video-Auswahl: <Kunde>/<Projekt>"` → `„Video-Auswahl: <Kunde>/<Projekt>[/<Charge>]"`, analog `„Animation: …"`. Darunter ergänzen: „Bei nur einer Charge reicht Kunde/Projekt — die Charge wird automatisch gefunden." Beispiel unter „Neues Projekt": `mkdir -p "projects/<Kunde>/<Projekt>/<Charge>/Material/Audio"`.

- [ ] **Step 2: Commit (Master-Repo)**

```bash
cd "/Users/jansantos/NIRO Studio"
git add CLAUDE.md && git commit -m "docs: Projektstruktur auf Chargen-Schema umgestellt"
```

- [ ] **Step 3: Memory aktualisieren**

`niro-studio.md`: Strukturbeschreibung auf `<Kunde>/<Projekt>/<Charge>/{Material,Ergebnisse,_intern}` umstellen. `footage-sortierer.md` und `niro-transcribe-project.md`: Pfadangaben prüfen, alte Ordnernamen ersetzen. `MEMORY.md`-Hooks anpassen, falls sie alte Struktur nennen.

---

### Task 6: End-Verifikation

- [ ] **Step 1: Komplette Test-Suite**

Run: `cd "/Users/jansantos/NIRO Studio/tools/transcribe" && venv/bin/python -m pytest -q`
Expected: alle Tests PASS, 0 failed.

- [ ] **Step 2: Keine Alt-Pfade mehr in Doku**

Run: `grep -rn -E 'motion/inputs|motion/renders|/audio/|/script/|/output/|<Projekt>/footage' "/Users/jansantos/NIRO Studio/CLAUDE.md" "/Users/jansantos/NIRO Studio/tools/transcribe/WORKFLOW.md" "/Users/jansantos/NIRO Studio/tools/transcribe/WORKFLOW-Footage.md" "/Users/jansantos/NIRO Studio/tools/motion/WORKFLOW-Motion.md"`
Expected: keine Treffer.

- [ ] **Step 3: Symlink funktioniert**

Run: `ls "/Users/jansantos/NIRO Studio/tools/motion/public/projects/seniorenstiftung-recruiting/"`
Expected: listet die Video-Inputs ohne Fehler.
