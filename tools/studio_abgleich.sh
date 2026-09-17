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

if ! nas_da; then
	echo "Studio-Abgleich: NAS nicht verbunden ($(dirname "$NAS")) — lokal bleibt alles, Abgleich später: sh tools/studio_abgleich.sh"
	exit 0
fi
gedaechtnis_verknuepfen
chargen_abgleichen
echo "$TEILE"
exit 0
