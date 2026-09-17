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

echo "Test 4b: Gedächtnis-Index beider Macs zusammenführen"
neues_setup t4b
GN="$N/claude-gedaechtnis"
mkdir -p "$G" "$GN"
printf '%s\n%s' '- [A-Notiz](a.md) — von A' '- [Gemeinsam](gemeinsam.md) — Fassung A' > "$GN/MEMORY.md"
touch -t 202609100000 "$GN/MEMORY.md"
printf '%s\n%s\n' '- [Gemeinsam](gemeinsam.md) — Fassung B' '- [B-Notiz](b.md) — von B' > "$G/MEMORY.md"
touch -t 202609171500 "$G/MEMORY.md"
echo "A" > "$GN/gemeinsam.md"; touch -t 202609171500 "$GN/gemeinsam.md"
echo "B" > "$G/gemeinsam.md"; touch -t 202609100000 "$G/gemeinsam.md"
echo "B" > "$G/b.md"
AUS=$(lauf)
pruefe "Index: Zeilen vom NAS bleiben vorn (auch wenn der lokale Index neuer ist)" '[ "$(sed -n 1p "$GN/MEMORY.md")" = "- [A-Notiz](a.md) — von A" ] && [ "$(sed -n 2p "$GN/MEMORY.md")" = "- [Gemeinsam](gemeinsam.md) — Fassung A" ]'
pruefe "Index: fehlende lokale Zeile angehängt, keine doppelte" '[ "$(sed -n 3p "$GN/MEMORY.md")" = "- [B-Notiz](b.md) — von B" ] && [ "$(grep -c . "$GN/MEMORY.md")" = "3" ]'
pruefe "Notiz von B liegt auf dem NAS" '[ -f "$GN/b.md" ]'
pruefe "gleichnamige Notiz: neuere behalten, Hinweis" '[ "$(cat "$GN/gemeinsam.md")" = "A" ] && printf "%s" "$AUS" | grep -q "1 gleichnamige Notiz"'

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
	&& echo "notiz v1" > projects/K/P/C/Notiz.md \
	&& git add -A && git commit -qm start && git push -q origin main)
git clone -q "$B/origin.git" "$B/b"
(cd "$B/b" && git config user.email b@test && git config user.name b)
# B: Notiz.md unverändert wie in git, aber mit jüngerem Checkout-Datum als A's ungepushte Änderung
touch -t 202609171400 "$B/b/projects/K/P/C/Notiz.md"
echo "A notiz neu" > "$B/a/projects/K/P/C/Notiz.md"; touch -t 202609150900 "$B/a/projects/K/P/C/Notiz.md"
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
pruefe "unveränderte Git-Kopie von B überschreibt neueren NAS-Stand nicht" '[ "$(cat "$NIRO_STUDIO_NAS/projects/K/P/C/Notiz.md")" = "A notiz neu" ] && [ "$(cat "$B/b/projects/K/P/C/Notiz.md")" = "A notiz neu" ]'
AUS=$(cd "$B/b" && NIRO_STUDIO_NAS="$B/weg/NIRO Studio" sh tools/studio_abgleich.sh --umstieg 2>&1); RC=$?
pruefe "Umstieg ohne NAS bricht mit 1 ab" '[ "$RC" -eq 1 ] && printf "%s" "$AUS" | grep -q "NAS nicht verbunden"'

echo "Test 8: Worktree gleicht nur den Hauptordner ab"
git -C "$B/b" worktree add -q "$B/wt" 2>/dev/null
echo "neu im Hauptordner" > "$B/b/projects/K/P/C/haupt.md"
AUS=$(cd "$B/wt" && sh tools/studio_abgleich.sh --nach-pull 2>&1)
pruefe "Hook im Worktree: kein Abgleich, Hinweis" 'printf "%s" "$AUS" | grep -q "Worktree" && [ ! -e "$B/wt/projects" ] && [ ! -e "$NIRO_STUDIO_NAS/projects/K/P/C/haupt.md" ]'
AUS=$(cd "$B/wt" && sh tools/studio_abgleich.sh 2>&1)
pruefe "Aufruf im Worktree gleicht projects/ des Hauptordners ab" '[ -f "$NIRO_STUDIO_NAS/projects/K/P/C/haupt.md" ] && [ ! -e "$B/wt/projects" ] && printf "%s" "$AUS" | grep -q "Hauptordner"'

echo "Test 9: Hooks in einem Stand ohne Skript (z. B. alter Worktree-Branch bei absolutem core.hooksPath)"
git init -q "$T/t9"
AUS=$(cd "$T/t9" && sh "$HIER/../.githooks/post-merge" 2>&1 && sh "$HIER/../.githooks/post-rewrite" rebase 2>&1); RC=$?
pruefe "still und Exit 0" '[ -z "$AUS" ] && [ "$RC" -eq 0 ]'

echo "Test 5: NAS fehlt"
neues_setup t5
NIRO_STUDIO_NAS="$T/t5/nicht_verbunden/NIRO Studio"; export NIRO_STUDIO_NAS
AUS=$(lauf); RC=$?
pruefe "Hinweis NAS nicht verbunden" 'printf "%s" "$AUS" | grep -q "NAS nicht verbunden"'
pruefe "Exit 0" '[ "$RC" -eq 0 ]'

echo
if [ "$FEHLER" -eq 0 ]; then echo "Alle Tests bestanden."; rm -rf "$T"; exit 0; fi
echo "$FEHLER Test(s) fehlgeschlagen — Testordner bleibt: $T"; exit 1
