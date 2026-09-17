# Studio-Abgleich über das NAS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein `git pull` auf jedem Mac sortiert Chargen-Daten, Claude-Gedächtnis, NIRO-Grading-LUTs und Abhängigkeiten ein;
der gemeinsame Stand liegt auf dem NAS statt auf GitHub.

**Architecture:** Ein POSIX-Shell-Skript `tools/studio_abgleich.sh` gleicht `projects/` mit einem NAS-Spiegel per
`rsync -rt --update` in beide Richtungen ab (nie löschen, Medien/Caches/>20 MB ausgeschlossen), verknüpft das
Claude-Gedächtnis mit einem NAS-Ordner, ruft den LUT-Abgleich auf und zieht nach einem Pull Abhängigkeiten nach. Git-Hooks
`post-merge`/`post-rewrite` rufen es nach jedem Pull; `--umstieg` stellt einen Mac einmalig um. `projects/` fliegt aus
der Git-Versionierung.

**Tech Stack:** POSIX `sh` (macOS `/bin/sh`), openrsync 2.6.9-kompatibel (`/usr/bin/rsync`), git, Test-Skript in `sh`.

Spec: `docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md`

## Global Constraints

- NAS-Ordner: `/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio` mit `projects/` und `claude-gedaechtnis/`.
- Abgleich: beide Richtungen, neuere Datei gewinnt, **nichts wird gelöscht**; `rsync -rt --update --modify-window=2 --max-size=20M`.
- Ausgeschlossen: `.DS_Store`, `__pycache__/`, `node_modules/`, `venv/`, `work/`, `frames/`, `Fotos/`, Medien `mov mp4 m4v mxf mts avi wav mp3 m4a aif aiff flac arw dng cr3 braw r3d` (Groß-/Kleinschreibung egal).
- Gedächtnis-Ziel: `$HOME/.claude/projects/<Schlüssel>/memory`, Schlüssel = Repo-Pfad, jedes Zeichen außer A–Z/a–z/0–9 → `-`.
- Außer `--umstieg` endet das Skript immer mit Exit 0 und blockiert git nie.
- Testvariablen: `NIRO_STUDIO_REPO`, `NIRO_STUDIO_NAS`, `NIRO_CLAUDE_MEMORY_DIR`, `NIRO_PIP_CMD`, `NIRO_NPM_CMD`, `NIRO_NAS_LUT_DIR`, `NIRO_RESOLVE_LUT_DIR`.
- Meldungen auf Deutsch. Resolve und das echte NAS fassen die Tests nie an.
- Commits enden mit `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`; nur eigene Pfade committen (fremde Änderungen an `tools/resolve/WORKFLOW-Resolve.md` nie mitnehmen).

---

### Task 1: Kern-Abgleich `projects/` ↔ NAS

**Files:**
- Create: `tools/studio_abgleich.sh`
- Create: `tools/studio_abgleich_test.sh`

**Interfaces:**
- Produces: Aufruf `sh tools/studio_abgleich.sh [--charge <Pfad>]`; Shell-Funktionen `spiegeln QUELLE ZIEL`,
  `abgleich QUELLE ZIEL TEXT` (setzt `ANZAHL`, `RC`), `nas_da` (0/1), Variablen `REPO`, `NAS`, `GEDAECHTNIS`, `MODUS`,
  `CHARGE`, `TEILE` (Zusammenfassung, Teile mit „ · " verbunden). Test-Helfer `neues_setup NAME`, `lauf ARGS…`, `pruefe TEXT BEDINGUNG`.

- [ ] **Step 1: Test-Skript mit den Kern-Tests schreiben**

`tools/studio_abgleich_test.sh`:

```sh
#!/bin/sh
# Tests für tools/studio_abgleich.sh — ohne echtes NAS, Gedächtnis, pip/npm oder Resolve.
# Aufruf: sh tools/studio_abgleich_test.sh   (Exit 0 = alle Tests bestanden)
set -u
HIER=$(cd "$(dirname "$0")" && pwd)
SKRIPT="$HIER/studio_abgleich.sh"
T=$(mktemp -d -t studio_abgleich_test)
FEHLER=0
pruefe() { if eval "$2"; then echo "  ok     $1"; else echo "  FEHLER $1"; FEHLER=$((FEHLER + 1)); fi; }

neues_setup() {
	R="$T/$1/repo"; N="$T/$1/nas/NIRO Studio"; G="$T/$1/home/.claude/projects/x/memory"
	mkdir -p "$R/projects" "$R/tools/resolve" "$(dirname "$N")" "$T/$1/lut_lokal" "$T/$1/lut_nas"
	cp "$SKRIPT" "$R/tools/studio_abgleich.sh"
	cp "$HIER/resolve/luts_sync.sh" "$R/tools/resolve/luts_sync.sh"
	(cd "$R" && git init -q && git config user.email test@test && git config user.name test)
	NIRO_STUDIO_REPO="$R"; NIRO_STUDIO_NAS="$N"; NIRO_CLAUDE_MEMORY_DIR="$G"
	NIRO_RESOLVE_LUT_DIR="$T/$1/lut_lokal"; NIRO_NAS_LUT_DIR="$T/$1/lut_nas/NIRO Grading"
	export NIRO_STUDIO_REPO NIRO_STUDIO_NAS NIRO_CLAUDE_MEMORY_DIR NIRO_RESOLVE_LUT_DIR NIRO_NAS_LUT_DIR
}
lauf() { (cd "$NIRO_STUDIO_REPO" && sh tools/studio_abgleich.sh "$@"); }

echo "Test 1: beide Richtungen, neuere Datei gewinnt, nichts gelöscht"
neues_setup t1
C="projects/Kunde/Projekt/2026-09 Charge"
mkdir -p "$R/$C" "$N/$C"
echo "lokal neu" > "$R/$C/Protokoll.md"; touch -t 202609171200 "$R/$C/Protokoll.md"
echo "nas alt" > "$N/$C/Protokoll.md"; touch -t 202001010000 "$N/$C/Protokoll.md"
echo "nur nas" > "$N/$C/Plan.md"
echo "nur lokal" > "$R/$C/notiz.json"
AUS=$(lauf)
pruefe "NAS-Protokoll hat den neueren lokalen Inhalt" '[ "$(cat "$N/$C/Protokoll.md")" = "lokal neu" ]'
pruefe "Plan.md vom NAS geholt" '[ "$(cat "$R/$C/Plan.md")" = "nur nas" ]'
pruefe "notiz.json aufs NAS gelegt" '[ -f "$N/$C/notiz.json" ]'
pruefe "Zusammenfassung nennt geholt/hochgeladen" 'printf "%s" "$AUS" | grep -q "1 geholt, 2 hochgeladen"'
echo "nas neuer" > "$N/$C/Protokoll.md"; touch -t 202609180900 "$N/$C/Protokoll.md"
rm "$R/$C/notiz.json"
lauf >/dev/null
pruefe "neuere NAS-Datei überschreibt lokal" '[ "$(cat "$R/$C/Protokoll.md")" = "nas neuer" ]'
pruefe "lokal gelöschte Datei kommt vom NAS zurück (kein Löschen)" '[ -f "$R/$C/notiz.json" ] && [ -f "$N/$C/notiz.json" ]'

echo "Test 2: Ausschlüsse"
neues_setup t2
C="projects/K/P/C"
mkdir -p "$R/$C/Material/Video" "$R/$C/_intern/autocut/work" "$R/$C/_intern/color/frames" "$R/$C/Ergebnisse/Fotos" "$R/$C/_intern/cache"
for f in "Material/Video/clip.MOV" "Material/Video/b.mp4" "Material/Audio.wav" "_intern/autocut/work/x.npz" \
	"_intern/color/frames/f.npy" "Ergebnisse/Fotos/a.jpg" ".DS_Store"; do mkdir -p "$(dirname "$R/$C/$f")"; echo x > "$R/$C/$f"; done
echo "{}" > "$R/$C/_intern/cache/abc.scribe.json"
dd if=/dev/zero of="$R/$C/gross.png" bs=1048576 count=21 2>/dev/null
lauf >/dev/null
pruefe "Scribe-Cache liegt auf dem NAS" '[ -f "$N/$C/_intern/cache/abc.scribe.json" ]'
pruefe "Medien (MOV/mp4/wav) nicht auf dem NAS" '[ ! -e "$N/$C/Material/Video/clip.MOV" ] && [ ! -e "$N/$C/Material/Video/b.mp4" ] && [ ! -e "$N/$C/Material/Audio.wav" ]'
pruefe "work/, frames/, Fotos/, .DS_Store nicht auf dem NAS" '[ ! -e "$N/$C/_intern/autocut/work/x.npz" ] && [ ! -e "$N/$C/_intern/color/frames/f.npy" ] && [ ! -e "$N/$C/Ergebnisse/Fotos/a.jpg" ] && [ ! -e "$N/$C/.DS_Store" ]'
pruefe "Datei über 20 MB nicht auf dem NAS" '[ ! -e "$N/$C/gross.png" ]'

echo "Test 3: --charge"
neues_setup t3
mkdir -p "$R/projects/K/P/C1" "$R/projects/K/P/C2" "$N/projects/K/P/C3"
echo 1 > "$R/projects/K/P/C1/a.md"; echo 2 > "$R/projects/K/P/C2/b.md"; echo 3 > "$N/projects/K/P/C3/c.md"
lauf --charge "projects/K/P/C1" >/dev/null
pruefe "nur C1 hochgeladen" '[ -f "$N/projects/K/P/C1/a.md" ] && [ ! -e "$N/projects/K/P/C2/b.md" ]'
lauf --charge "$R/projects/K/P/C3" >/dev/null
pruefe "C3 (nur auf dem NAS) per absolutem Pfad geholt" '[ -f "$R/projects/K/P/C3/c.md" ]'
AUS=$(lauf --charge "tools")
pruefe "Pfad außerhalb projects/ abgewiesen" 'printf "%s" "$AUS" | grep -q "liegt nicht unter projects/"'
pruefe "dabei nichts abgeglichen" '[ ! -e "$N/projects/K/P/C2/b.md" ]'

echo "Test 5: NAS fehlt"
neues_setup t5
NIRO_STUDIO_NAS="$T/t5/nicht_verbunden/NIRO Studio"; export NIRO_STUDIO_NAS
AUS=$(lauf); RC=$?
pruefe "Hinweis NAS nicht verbunden" 'printf "%s" "$AUS" | grep -q "NAS nicht verbunden"'
pruefe "Exit 0" '[ "$RC" -eq 0 ]'

echo
if [ "$FEHLER" -eq 0 ]; then echo "Alle Tests bestanden."; rm -rf "$T"; exit 0; fi
echo "$FEHLER Test(s) fehlgeschlagen — Testordner bleibt: $T"; exit 1
```

- [ ] **Step 2: Tests laufen lassen — sie müssen scheitern**

Run: `sh tools/studio_abgleich_test.sh`
Expected: FEHLER (Skript fehlt: `cp: …/studio_abgleich.sh: No such file or directory`), Exit 1.

- [ ] **Step 3: Kern-Skript schreiben**

`tools/studio_abgleich.sh`:

```sh
#!/bin/sh
#
# Studio-Abgleich über das NAS: Chargen (projects/), Claude-Gedächtnis, NIRO-Grading-LUTs und — nach einem Pull —
# Abhängigkeiten. Spec: docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md
#
# Aufruf (im Repo):
#   sh tools/studio_abgleich.sh                     alles abgleichen
#   sh tools/studio_abgleich.sh --charge "<Pfad>"   nur eine Charge (unter projects/, relativ zum Repo oder absolut)
#   sh tools/studio_abgleich.sh --nach-pull         alles + Abhängigkeiten (so rufen es die Git-Hooks)
#   git fetch && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg    einmalig je Mac
#
# Regeln: beide Richtungen, neuere Datei gewinnt, nichts wird gelöscht; ohne Medien, Caches und Dateien > 20 MB.
# Außer --umstieg endet das Skript immer mit 0 und blockiert git nie. Tests: sh tools/studio_abgleich_test.sh

MODUS=alles
CHARGE=""
case "${1:-}" in
	--charge) MODUS=charge; CHARGE=${2:-} ;;
	--nach-pull) MODUS=nach-pull ;;
	--umstieg) MODUS=umstieg ;;
	"") ;;
	*) echo "Studio-Abgleich: unbekannte Option „$1“ (--charge <Pfad> | --nach-pull | --umstieg)"; exit 0 ;;
esac

REPO=${NIRO_STUDIO_REPO:-$(git rev-parse --show-toplevel 2>/dev/null)}
[ -n "$REPO" ] || REPO=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)
NAS=${NIRO_STUDIO_NAS:-"/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio"}
SCHLUESSEL=$(printf '%s' "$REPO" | sed 's/[^A-Za-z0-9]/-/g')
GEDAECHTNIS=${NIRO_CLAUDE_MEMORY_DIR:-"$HOME/.claude/projects/$SCHLUESSEL/memory"}
TEILE=""

teil() { if [ -z "$TEILE" ]; then TEILE=$1; else TEILE="$TEILE · $1"; fi; }
nas_da() { [ -d "$(dirname "$NAS")" ]; }

spiegeln() {
	rsync -rt --update --modify-window=2 --itemize-changes --max-size=20M \
		--exclude='.DS_Store' --exclude='__pycache__/' --exclude='node_modules/' --exclude='venv/' \
		--exclude='work/' --exclude='frames/' --exclude='Fotos/' \
		--exclude='*.[Mm][Oo][Vv]' --exclude='*.[Mm][Pp]4' --exclude='*.[Mm]4[Vv]' --exclude='*.[Mm][Xx][Ff]' \
		--exclude='*.[Mm][Tt][Ss]' --exclude='*.[Aa][Vv][Ii]' --exclude='*.[Ww][Aa][Vv]' --exclude='*.[Mm][Pp]3' \
		--exclude='*.[Mm]4[Aa]' --exclude='*.[Aa][Ii][Ff]' --exclude='*.[Aa][Ii][Ff][Ff]' --exclude='*.[Ff][Ll][Aa][Cc]' \
		--exclude='*.[Aa][Rr][Ww]' --exclude='*.[Dd][Nn][Gg]' --exclude='*.[Cc][Rr]3' --exclude='*.[Bb][Rr][Aa][Ww]' \
		--exclude='*.[Rr]3[Dd]' \
		"$1/" "$2/"
}

abgleich() {
	protokoll=$(mktemp -t studio_abgleich) || { ANZAHL=0; RC=99; return; }
	spiegeln "$1" "$2" >"$protokoll" 2>"$protokoll.err"
	RC=$?
	ANZAHL=$(grep -c '^>f' "$protokoll" || true)
	if [ "$RC" -ne 0 ]; then
		echo "Studio-Abgleich: rsync-Fehler $RC ($3): $(tail -n 2 "$protokoll.err" | tr '\n' ' ')"
	fi
	rm -f "$protokoll" "$protokoll.err"
}

chargen_abgleichen() {
	if [ "$MODUS" = "charge" ]; then
		pfad=${CHARGE%/}
		case "$pfad" in
			"$REPO/projects/"?*) rel=${pfad#"$REPO/projects/"} ;;
			projects/?*) rel=${pfad#projects/} ;;
			*) echo "Studio-Abgleich: „$CHARGE“ liegt nicht unter projects/ — nichts abgeglichen."; return ;;
		esac
		lokal="$REPO/projects/$rel"; fern="$NAS/projects/$rel"
	else
		lokal="$REPO/projects"; fern="$NAS/projects"
	fi
	mkdir -p "$lokal" "$fern" || { teil "Chargen: Ordner nicht anlegbar"; return; }
	abgleich "$fern" "$lokal" "NAS → lokal"; geholt=$ANZAHL
	abgleich "$lokal" "$fern" "lokal → NAS"; hochgeladen=$ANZAHL
	teil "NAS-Abgleich: $geholt geholt, $hochgeladen hochgeladen"
}

if ! nas_da; then
	echo "Studio-Abgleich: NAS nicht verbunden ($(dirname "$NAS")) — lokal bleibt alles, Abgleich später: sh tools/studio_abgleich.sh"
	exit 0
fi
chargen_abgleichen
echo "$TEILE"
exit 0
```

- [ ] **Step 4: Tests laufen lassen — Tests 1, 2, 3, 5 müssen bestehen**

Run: `sh tools/studio_abgleich_test.sh`
Expected: alle `ok`, „Alle Tests bestanden.", Exit 0. Scheitert Test 2 an den Medien-Mustern (openrsync ohne
Zeichenklassen), die Muster als Einzelvarianten ausschreiben (`--exclude='*.mov' --exclude='*.MOV'` usw.) und erneut laufen lassen.

- [ ] **Step 5: Commit**

```bash
git add tools/studio_abgleich.sh tools/studio_abgleich_test.sh
git commit -m "feat(studio): NAS-Abgleich projects/ in beide Richtungen (ohne Medien/Caches, nie löschen)"
```

---

### Task 2: Gedächtnis-Verknüpfung

**Files:**
- Modify: `tools/studio_abgleich.sh` (Funktion `gedaechtnis_verknuepfen`, Aufruf vor `chargen_abgleichen`)
- Modify: `tools/studio_abgleich_test.sh` (Test 4 vor dem Abschluss-Block)

**Interfaces:**
- Consumes: `NAS`, `GEDAECHTNIS`, `teil` aus Task 1.
- Produces: `gedaechtnis_verknuepfen` (setzt `GEDAECHTNIS_TEXT`, ruft `teil`); Rückgabe 1, wenn das Hochladen scheitert.

- [ ] **Step 1: Test 4 ergänzen** (vor `echo` / Abschluss-Block einfügen)

```sh
echo "Test 4: Gedächtnis"
neues_setup t4
mkdir -p "$G" "$N/claude-gedaechtnis"
echo "lokal" > "$G/MEMORY.md"; echo "vom anderen Mac" > "$N/claude-gedaechtnis/andere.md"
AUS=$(lauf)
pruefe "Gedächtnis ist Verknüpfung aufs NAS" '[ -L "$G" ] && [ "$(readlink "$G")" = "$N/claude-gedaechtnis" ]'
pruefe "lokale Notiz liegt auf dem NAS" '[ "$(cat "$N/claude-gedaechtnis/MEMORY.md")" = "lokal" ]'
pruefe "Notiz vom anderen Mac über die Verknüpfung lesbar" '[ -f "$G/andere.md" ]'
pruefe "Sicherung angelegt" 'ls -d "$G".vor-nas-* >/dev/null 2>&1'
lauf >/dev/null
pruefe "zweiter Lauf: keine zweite Sicherung" '[ "$(ls -d "$G".vor-nas-* | wc -l | tr -d " ")" = "1" ]'
rm "$G"; mkdir -p "$T/t4/fremd"; ln -s "$T/t4/fremd" "$G"
AUS=$(lauf)
pruefe "fremde Verknüpfung bleibt unverändert" '[ "$(readlink "$G")" = "$T/t4/fremd" ]'
pruefe "Hinweis zur fremden Verknüpfung" 'printf "%s" "$AUS" | grep -q "nicht geändert"'
rm "$G"
lauf >/dev/null
pruefe "fehlendes Gedächtnis wird neu verknüpft" '[ -L "$G" ]'
```

- [ ] **Step 2: Tests laufen lassen — Test 4 muss scheitern**

Run: `sh tools/studio_abgleich_test.sh`
Expected: `FEHLER Gedächtnis ist Verknüpfung aufs NAS` (und Folgefehler), Exit 1.

- [ ] **Step 3: Funktion einbauen** (nach `chargen_abgleichen()`; Aufruf `gedaechtnis_verknuepfen` direkt vor `chargen_abgleichen` im Hauptteil)

```sh
gedaechtnis_verknuepfen() {
	ziel="$NAS/claude-gedaechtnis"
	mkdir -p "$ziel" || { teil "Gedächtnis: NAS-Ordner nicht anlegbar"; return 1; }
	if [ -L "$GEDAECHTNIS" ]; then
		jetzt=$(readlink "$GEDAECHTNIS")
		if [ "$jetzt" = "$ziel" ]; then teil "Gedächtnis verknüpft"
		else teil "Gedächtnis: Verknüpfung zeigt auf „$jetzt“ — nicht geändert"; fi
		return 0
	fi
	if [ -d "$GEDAECHTNIS" ]; then
		if ! rsync -rt --update --modify-window=2 --exclude='.DS_Store' "$GEDAECHTNIS/" "$ziel/"; then
			teil "Gedächtnis: Hochladen fehlgeschlagen — nicht verknüpft"; return 1
		fi
		sicherung="$GEDAECHTNIS.vor-nas-$(date +%Y%m%d-%H%M%S)"
		mv "$GEDAECHTNIS" "$sicherung" || { teil "Gedächtnis: Sicherung fehlgeschlagen — nicht verknüpft"; return 1; }
		ln -s "$ziel" "$GEDAECHTNIS" || { mv "$sicherung" "$GEDAECHTNIS"; teil "Gedächtnis: Verknüpfung fehlgeschlagen"; return 1; }
		teil "Gedächtnis zusammengeführt und verknüpft (Sicherung $(basename "$sicherung"))"
		return 0
	fi
	mkdir -p "$(dirname "$GEDAECHTNIS")" && ln -s "$ziel" "$GEDAECHTNIS" && teil "Gedächtnis verknüpft (neu)"
}
```

Hauptteil danach:

```sh
if ! nas_da; then
	echo "Studio-Abgleich: NAS nicht verbunden ($(dirname "$NAS")) — lokal bleibt alles, Abgleich später: sh tools/studio_abgleich.sh"
	exit 0
fi
gedaechtnis_verknuepfen
chargen_abgleichen
echo "$TEILE"
exit 0
```

- [ ] **Step 4: Tests laufen lassen — alle bestehen**

Run: `sh tools/studio_abgleich_test.sh`
Expected: „Alle Tests bestanden.", Exit 0.

- [ ] **Step 5: Commit**

```bash
git add tools/studio_abgleich.sh tools/studio_abgleich_test.sh
git commit -m "feat(studio): Claude-Gedächtnis per Verknüpfung auf den NAS-Ordner (Zusammenführen + Sicherung)"
```

---

### Task 3: LUT-Aufruf, Abhängigkeiten nach dem Pull, Hooks

**Files:**
- Modify: `tools/studio_abgleich.sh` (Funktion `abhaengigkeiten`, LUT-Aufruf, Hauptteil)
- Create: `.githooks/post-merge`, `.githooks/post-rewrite`
- Modify: `tools/studio_abgleich_test.sh` (Test 6)

**Interfaces:**
- Consumes: `REPO`, `MODUS`, `teil`.
- Produces: `abhaengigkeiten` (liest `git diff --name-only ORIG_HEAD HEAD`); Hook-Aufruf `sh "$(git rev-parse --show-toplevel)/tools/studio_abgleich.sh" --nach-pull`.

- [ ] **Step 1: Test 6 ergänzen**

```sh
echo "Test 6: Abhängigkeiten nach dem Pull"
neues_setup t6
LOG="$T/t6/aufrufe.log"; : > "$LOG"
printf '#!/bin/sh\necho "pip $*" >> "%s"\n' "$LOG" > "$T/t6/pip"; printf '#!/bin/sh\necho "npm $*" >> "%s"\n' "$LOG" > "$T/t6/npm"
chmod +x "$T/t6/pip" "$T/t6/npm"
NIRO_PIP_CMD="$T/t6/pip"; NIRO_NPM_CMD="$T/t6/npm"; export NIRO_PIP_CMD NIRO_NPM_CMD
mkdir -p "$R/tools/motion" "$R/tools/transcribe"
echo '{"v":1}' > "$R/tools/motion/package.json"; echo 'v=1' > "$R/tools/transcribe/pyproject.toml"
(cd "$R" && git add -A && git commit -qm eins && git update-ref ORIG_HEAD HEAD)
echo '{"v":2}' > "$R/tools/motion/package.json"
(cd "$R" && git commit -qam zwei)
lauf --nach-pull >/dev/null
pruefe "npm install bei geänderter package.json" 'grep -q "^npm install" "$LOG"'
pruefe "kein pip ohne geänderte pyproject.toml" '! grep -q "^pip" "$LOG"'
(cd "$R" && git update-ref ORIG_HEAD HEAD); : > "$LOG"
lauf --nach-pull >/dev/null
pruefe "ohne Änderungen kein Aufruf" '[ ! -s "$LOG" ]'
: > "$LOG"; lauf >/dev/null
pruefe "ohne --nach-pull keine Abhängigkeiten" '[ ! -s "$LOG" ]'
unset NIRO_PIP_CMD NIRO_NPM_CMD
```

- [ ] **Step 2: Tests laufen lassen — Test 6 muss scheitern**

Run: `sh tools/studio_abgleich_test.sh`
Expected: `FEHLER npm install bei geänderter package.json`, Exit 1.

- [ ] **Step 3: Funktion, LUT-Aufruf und Hooks einbauen**

In `tools/studio_abgleich.sh` nach `gedaechtnis_verknuepfen()`:

```sh
abhaengigkeiten() {
	aenderungen=$(git -C "$REPO" diff --name-only ORIG_HEAD HEAD 2>/dev/null) || return 0
	[ -n "$aenderungen" ] || return 0
	geaendert() { printf '%s\n' "$aenderungen" | grep -qx "$1"; }
	if geaendert 'tools/transcribe/pyproject.toml'; then
		pip_cmd=${NIRO_PIP_CMD:-"$REPO/tools/transcribe/venv/bin/pip"}
		if [ -x "$pip_cmd" ]; then
			if (cd "$REPO/tools/transcribe" && "$pip_cmd" install -q -e ".[dev]" >/dev/null 2>&1); then teil "Transcribe-Pakete aktualisiert"
			else teil "Transcribe-Pakete: pip fehlgeschlagen"; fi
		else teil "Transcribe: venv fehlt — SETUP.md Schritt 4"; fi
	fi
	if geaendert 'tools/motion/package.json' || geaendert 'tools/motion/package-lock.json'; then
		npm_cmd=${NIRO_NPM_CMD:-npm}
		if [ -n "${NIRO_NPM_CMD:-}" ] || [ -d "$REPO/tools/motion/node_modules" ]; then
			if (cd "$REPO/tools/motion" && "$npm_cmd" install --no-audit --no-fund >/dev/null 2>&1); then teil "Motion-Pakete aktualisiert"
			else teil "Motion-Pakete: npm install fehlgeschlagen"; fi
		else teil "Motion: node_modules fehlt — SETUP.md Schritt 5"; fi
	fi
	for datei in tools/autocut/SETUP.md tools/musik/README.md tools/sfx/README.md; do
		geaendert "$datei" && teil "$datei geändert — Abhängigkeiten prüfen"
	done
	return 0
}
```

Hauptteil (ersetzt den aus Task 2):

```sh
if ! nas_da; then
	echo "Studio-Abgleich: NAS nicht verbunden ($(dirname "$NAS")) — lokal bleibt alles, Abgleich später: sh tools/studio_abgleich.sh"
	[ "$MODUS" = "nach-pull" ] && abhaengigkeiten && [ -n "$TEILE" ] && echo "$TEILE"
	exit 0
fi
gedaechtnis_verknuepfen
chargen_abgleichen
[ -f "$REPO/tools/resolve/luts_sync.sh" ] && sh "$REPO/tools/resolve/luts_sync.sh"
[ "$MODUS" = "nach-pull" ] && abhaengigkeiten
echo "$TEILE"
exit 0
```

`.githooks/post-merge`:

```sh
#!/bin/sh
# Nach „git pull" (Merge): Studio-Abgleich mit dem NAS — Chargen, Gedächtnis, LUTs, Abhängigkeiten. Blockiert nie.
# Spec: docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md
sh "$(git rev-parse --show-toplevel)/tools/studio_abgleich.sh" --nach-pull
exit 0
```

`.githooks/post-rewrite`:

```sh
#!/bin/sh
# Nach „git pull --rebase": wie post-merge; bei „git commit --amend" nichts. Blockiert nie.
[ "$1" = "rebase" ] && sh "$(git rev-parse --show-toplevel)/tools/studio_abgleich.sh" --nach-pull
exit 0
```

Run: `chmod +x .githooks/post-merge .githooks/post-rewrite tools/studio_abgleich.sh tools/studio_abgleich_test.sh`

- [ ] **Step 4: Tests laufen lassen — alle bestehen**

Run: `sh tools/studio_abgleich_test.sh`
Expected: „Alle Tests bestanden.", Exit 0.

- [ ] **Step 5: Commit**

```bash
git add tools/studio_abgleich.sh tools/studio_abgleich_test.sh .githooks/post-merge .githooks/post-rewrite
git commit -m "feat(studio): Abgleich nach jedem Pull (Hooks), LUTs und Abhängigkeiten nachziehen"
```

---

### Task 4: `--umstieg`

**Files:**
- Modify: `tools/studio_abgleich.sh` (Funktion `umstieg`, Aufruf im Hauptteil)
- Modify: `tools/studio_abgleich_test.sh` (Test 7)

**Interfaces:**
- Consumes: `abgleich`, `gedaechtnis_verknuepfen`, `nas_da`, `REPO`, `NAS`.
- Produces: `umstieg` (Exit 0 bei Erfolg, 1 bei Abbruch).

- [ ] **Step 1: Test 7 ergänzen**

```sh
echo "Test 7: Umstieg eines Macs mit ungesicherten Projektänderungen"
unset NIRO_STUDIO_REPO
B="$T/t7"; mkdir -p "$B/nas_eltern" "$B/lut_lokal" "$B/lut_nas"
NIRO_STUDIO_NAS="$B/nas_eltern/NIRO Studio"; NIRO_CLAUDE_MEMORY_DIR="$B/home_b/memory"
NIRO_RESOLVE_LUT_DIR="$B/lut_lokal"; NIRO_NAS_LUT_DIR="$B/lut_nas/NIRO Grading"
export NIRO_STUDIO_NAS NIRO_CLAUDE_MEMORY_DIR NIRO_RESOLVE_LUT_DIR NIRO_NAS_LUT_DIR
git init -q --bare "$B/origin.git"
git -C "$B/origin.git" symbolic-ref HEAD refs/heads/main
git clone -q "$B/origin.git" "$B/a" 2>/dev/null
(cd "$B/a" && git config user.email a@test && git config user.name a && git symbolic-ref HEAD refs/heads/main \
	&& mkdir -p tools/resolve .githooks "projects/K/P/C/_intern" \
	&& cp "$SKRIPT" tools/studio_abgleich.sh && cp "$HIER/resolve/luts_sync.sh" tools/resolve/luts_sync.sh \
	&& cp "$HIER/../.githooks/post-merge" .githooks/post-merge \
	&& echo "v1" > projects/K/P/C/Protokoll.md && echo "plan v1" > projects/K/P/C/Plan.md \
	&& git add -A && git commit -qm start && git push -q origin main)
git clone -q "$B/origin.git" "$B/b"
(cd "$B/b" && git config user.email b@test && git config user.name b)
echo "B alt" > "$B/b/projects/K/P/C/Protokoll.md"; touch -t 202609161200 "$B/b/projects/K/P/C/Protokoll.md"
echo "B plan neu" > "$B/b/projects/K/P/C/Plan.md"; touch -t 202609171300 "$B/b/projects/K/P/C/Plan.md"
mkdir -p "$B/b/projects/K/P/C/_intern/cache"; echo "{}" > "$B/b/projects/K/P/C/_intern/cache/b.scribe.json"
echo "A neu" > "$B/a/projects/K/P/C/Protokoll.md"; touch -t 202609171200 "$B/a/projects/K/P/C/Protokoll.md"
touch -t 202609100000 "$B/a/projects/K/P/C/Plan.md"
(cd "$B/a" && sh tools/studio_abgleich.sh >/dev/null && printf '/projects/\n' > .gitignore \
	&& git rm -r -q --cached projects && git add .gitignore && git commit -qm "projects über NAS" && git push -q origin main)
AUS=$(cd "$B/b" && git fetch -q && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg 2>&1); RC=$?
pruefe "Umstieg Exit 0" '[ "$RC" -eq 0 ]'
pruefe "Hooks aktiviert" '[ "$(git -C "$B/b" config core.hooksPath)" = ".githooks" ]'
pruefe "Protokoll: neuerer Stand von A" '[ "$(cat "$B/b/projects/K/P/C/Protokoll.md")" = "A neu" ]'
pruefe "Plan: neuerer ungesicherter Stand von B erhalten" '[ "$(cat "$B/b/projects/K/P/C/Plan.md")" = "B plan neu" ] && [ "$(cat "$NIRO_STUDIO_NAS/projects/K/P/C/Plan.md")" = "B plan neu" ]'
pruefe "unversionierter Cache von B liegt auf dem NAS" '[ -f "$NIRO_STUDIO_NAS/projects/K/P/C/_intern/cache/b.scribe.json" ]'
pruefe "projects/ in B nicht mehr versioniert" '[ -z "$(git -C "$B/b" ls-files projects)" ]'
AUS=$(cd "$B/b" && NIRO_STUDIO_NAS="$B/weg/NIRO Studio" sh tools/studio_abgleich.sh --umstieg 2>&1); RC=$?
pruefe "Umstieg ohne NAS bricht mit 1 ab" '[ "$RC" -eq 1 ] && printf "%s" "$AUS" | grep -q "NAS nicht verbunden"'
```

- [ ] **Step 2: Tests laufen lassen — Test 7 muss scheitern**

Run: `sh tools/studio_abgleich_test.sh`
Expected: `FEHLER Umstieg Exit 0` (Option ohne Wirkung), Exit 1.

- [ ] **Step 3: Funktion einbauen** (nach `abhaengigkeiten()`; Aufruf `[ "$MODUS" = "umstieg" ] && umstieg` im Hauptteil als erste Zeile vor `if ! nas_da; then` — erst dort sind alle Funktionen definiert)

```sh
umstieg() {
	if [ -z "$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null)" ]; then
		echo "Umstieg abgebrochen: bitte im Ordner des NIRO-Studio-Repos ausführen."; exit 1
	fi
	git -C "$REPO" config core.hooksPath .githooks
	if ! nas_da; then
		echo "Umstieg abgebrochen: NAS nicht verbunden ($(dirname "$NAS")) — nichts geändert."; exit 1
	fi
	mkdir -p "$NAS/projects" || { echo "Umstieg abgebrochen: NAS-Ordner nicht anlegbar."; exit 1; }
	if [ -d "$REPO/projects" ]; then
		abgleich "$REPO/projects" "$NAS/projects" "lokal → NAS"
		if [ "$RC" -ne 0 ]; then echo "Umstieg abgebrochen: Hochladen fehlgeschlagen (rsync $RC) — nichts verworfen."; exit 1; fi
		echo "Umstieg: $ANZAHL Projektdateien aufs NAS gelegt."
	fi
	gedaechtnis_verknuepfen || { echo "Umstieg abgebrochen: $TEILE"; exit 1; }
	if [ -n "$(git -C "$REPO" ls-files projects 2>/dev/null)" ]; then
		marke=$(mktemp -t studio_umstieg)
		git -C "$REPO" reset -q -- projects
		git -C "$REPO" checkout -q -- projects
		find "$REPO/projects" -type f -newer "$marke" -exec touch -t 200001010000 {} +
		rm -f "$marke"
	fi
	if git -C "$REPO" pull -q --ff-only; then
		echo "Umstieg fertig ($TEILE). Ab jetzt reicht git pull."; exit 0
	fi
	echo "Umstieg: git pull --ff-only gescheitert (eigene lokale Commits?) — prüfen, danach git pull."; exit 1
}
```

Hinweis: `touch -t 200001010000` auf die von `git checkout` zurückgesetzten Dateien verhindert, dass alte Inhalte mit
frischem Zeitstempel beim nächsten Abgleich neuere NAS-Stände überschreiben, falls der Pull scheitert.

- [ ] **Step 4: Tests laufen lassen — alle bestehen**

Run: `sh tools/studio_abgleich_test.sh`
Expected: „Alle Tests bestanden.", Exit 0.

- [ ] **Step 5: Commit**

```bash
git add tools/studio_abgleich.sh tools/studio_abgleich_test.sh
git commit -m "feat(studio): --umstieg — Mac einmalig auf NAS-Abgleich umstellen, ohne ungesicherte Projektänderungen zu verlieren"
```

---

### Task 5: Inbetriebnahme auf diesem Mac

**Files:** keine Code-Änderung; schreibt aufs NAS und legt die Gedächtnis-Verknüpfung an.

- [ ] **Step 1: Probelauf-Zahlen** (nur lesen)

Run:
```bash
cd "/Users/jansantos/NIRO Studio" && rsync -rtn --stats --max-size=20M --exclude='.DS_Store' --exclude='__pycache__/' --exclude='node_modules/' --exclude='venv/' --exclude='work/' --exclude='frames/' --exclude='Fotos/' --exclude='*.[Mm][Oo][Vv]' --exclude='*.[Mm][Pp]4' --exclude='*.[Ww][Aa][Vv]' --exclude='*.[Aa][Rr][Ww]' projects/ /tmp/studio_probe_leer/ | grep -E "Number of files|Total transferred file size"
```
Expected: rund 6.900 Dateien, rund 3,2 GB (Stand 17.09.).

- [ ] **Step 2: Erster Abgleich (lädt einmalig hoch, verknüpft das Gedächtnis)**

Run: `sh tools/studio_abgleich.sh` (Zeitlimit großzügig, läuft einige Minuten)
Expected: „Gedächtnis zusammengeführt und verknüpft (Sicherung memory.vor-nas-…) · NAS-Abgleich: 0 geholt, ~6900 hochgeladen";
danach `readlink "$HOME/.claude/projects/-Users-jansantos-NIRO-Studio/memory"` = NAS-Pfad, `ls` zeigt MEMORY.md.

- [ ] **Step 3: Zweiter Lauf**

Run: `sh tools/studio_abgleich.sh`
Expected: „Gedächtnis verknüpft · NAS-Abgleich: 0 geholt, 0 hochgeladen", Laufzeit unter einer Minute.

---

### Task 6: Git-Umstellung, Doku, Push

**Files:**
- Modify: `.gitignore` (Positivliste `projects/` → `/projects/`)
- Modify: `CLAUDE.md` (Projektstruktur, Protokoll-Pflicht)
- Modify: `SETUP.md` (Schritt 2)
- Modify: `docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md` (Testvariable `NIRO_STUDIO_REPO`)
- Index: `git rm -r --cached projects`

- [ ] **Step 1: `.gitignore`** — den Block von „# Auf GitHub liegt das Werkzeug — aus projects/ nur die Referenzen." bis
  einschließlich der MAN-Schriften-Zeile ersetzen durch:

```gitignore
# projects/ (User-Entscheid 17.09.2026): Chargen-Daten laufen über den NAS-Spiegel
# 01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/projects (tools/studio_abgleich.sh), nicht über GitHub.
# Spec: docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md — die frühere Historie bleibt im Repo.
/projects/
```

- [ ] **Step 2: Aus der Versionierung nehmen**

Run: `git rm -r -q --cached projects && git status --porcelain | grep -c '^D  projects/'`
Expected: Anzahl der bisher versionierten Projektdateien (> 0); `ls projects` unverändert.

- [ ] **Step 3: `CLAUDE.md`**

Unter „## Projektstruktur" nach dem Absatz „Rohes Drehmaterial bleibt auf externen SSDs …" einfügen:

```markdown
**NAS-Spiegel statt GitHub (seit 17.09.2026):** `projects/` ist nicht versioniert. Der gemeinsame Stand beider Macs liegt
auf `NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio/projects` (ohne Medien und
Caches); `sh tools/studio_abgleich.sh` gleicht ab (beide Richtungen, neuere Datei gewinnt, nie löschen), nach jedem
`git pull` automatisch. Nie gleichzeitig auf beiden Macs an derselben Charge arbeiten. Das Claude-Gedächtnis ist auf
beiden Macs eine Verknüpfung auf `NIRO Studio/claude-gedaechtnis/`.
```

Den Absatz „**Protokoll-Pflicht:**" ergänzen um:

```markdown
Vor der Arbeit an einer Charge `sh tools/studio_abgleich.sh --charge "projects/<Kunde>/<Projekt>/<Charge>"` (neuester
Stand vom NAS), nach der Arbeit mit dem Protokoll-Eintrag dasselbe (Stand aufs NAS).
```

- [ ] **Step 4: `SETUP.md`** — in „## 2. Größensperre aktivieren" den Absatz „**DaVinci Resolve (Grading-LUTs):** …" (bis
  „Details in [tools/resolve/luts/README.md]…") ersetzen durch:

```markdown
Dieselbe Einstellung aktiviert den **Studio-Abgleich mit dem NAS**: Nach jedem `git pull` holt
`tools/studio_abgleich.sh` Chargen-Daten, Claude-Gedächtnis und NIRO-Grading-LUTs vom NAS, legt eigene Stände dort ab
und zieht geänderte Abhängigkeiten nach (Spec: `docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md`).

**Einmalig je Mac, der noch `projects/` aus GitHub hat** (statt des ersten Pulls, NAS verbunden):

```bash
git fetch && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg
```

Meldet der LUT-Abgleich fehlendes Schreibrecht, einmalig
`sudo chmod a+w "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"`.
```

- [ ] **Step 5: Spec** — in der Zeile „Testbarkeit:" `NIRO_STUDIO_REPO` (Repo-Pfad) ergänzen.

- [ ] **Step 6: Tests + Hook-Probe, dann Commit und Push**

Run: `sh tools/studio_abgleich_test.sh && sh .githooks/post-rewrite amend; echo "Hook-Exit $?"`
Expected: „Alle Tests bestanden.", „Hook-Exit 0".

```bash
git add .gitignore CLAUDE.md SETUP.md docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md docs/superpowers/plans/2026-09-17-studio-nas-abgleich.md
git commit -m "refactor(studio): projects/ über den NAS-Spiegel statt GitHub; Doku und Umstieg"
git push origin main
```

- [ ] **Step 7: Memory aktualisieren** — `studio-auf-nas-bewertung.md` (umgesetzt 17.09.), `github-push-referenzen-oeffentlich.md`
  (projects/ nicht mehr auf GitHub), `zweit-macbook-motion-quellen.md` (Umstieg-Befehl, danach nur `git pull`), Index-Zeilen in `MEMORY.md`.
