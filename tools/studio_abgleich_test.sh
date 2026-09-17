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

echo "Test 5: NAS fehlt"
neues_setup t5
NIRO_STUDIO_NAS="$T/t5/nicht_verbunden/NIRO Studio"; export NIRO_STUDIO_NAS
AUS=$(lauf); RC=$?
pruefe "Hinweis NAS nicht verbunden" 'printf "%s" "$AUS" | grep -q "NAS nicht verbunden"'
pruefe "Exit 0" '[ "$RC" -eq 0 ]'

echo
if [ "$FEHLER" -eq 0 ]; then echo "Alle Tests bestanden."; rm -rf "$T"; exit 0; fi
echo "$FEHLER Test(s) fehlgeschlagen — Testordner bleibt: $T"; exit 1
