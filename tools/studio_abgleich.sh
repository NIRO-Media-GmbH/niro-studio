#!/bin/sh
#
# Studio-Abgleich über das NAS: Chargen (projects/), Claude-Gedächtnis, NIRO-Grading-LUTs und — nach einem Pull —
# Abhängigkeiten. Spec: docs/superpowers/specs/2026-09-17-studio-nas-abgleich-design.md
#
# Aufruf (im Repo):
#   sh tools/studio_abgleich.sh                     alles abgleichen
#   sh tools/studio_abgleich.sh --charge "<Pfad>"   nur eine Charge (unter projects/, relativ zum Repo oder absolut)
#   sh tools/studio_abgleich.sh --nach-pull         alles + Abhängigkeiten (so rufen es die Git-Hooks)
#   sh tools/studio_abgleich.sh --berichte          nur berichte/ (Tagesstände) spiegeln — so ruft es der Sammler
#   git fetch && git show origin/main:tools/studio_abgleich.sh | sh -s -- --umstieg    einmalig je Mac
#
# Regeln: beide Richtungen, neuere Datei gewinnt, nichts wird gelöscht; ohne Medien, Caches und Dateien > 20 MB.
# berichte/ (Tagesstände beider Macs, Spec docs/superpowers/specs/2026-09-17-tagesbericht-design.md) wird wie projects/ gespiegelt; vorher läuft tools/tagesbericht/sammler.py.
# projects/ liegt nur im Hauptordner des Repos: Aufrufe aus einem Worktree gleichen dessen projects/ ab, die Hooks
# eines Worktrees gleichen nichts ab.
# Außer --umstieg endet das Skript immer mit 0 und blockiert git nie. Tests: sh tools/studio_abgleich_test.sh

MODUS=alles
CHARGE=""
case "${1:-}" in
	--charge) MODUS=charge; CHARGE=${2:-} ;;
	--nach-pull) MODUS=nach-pull ;;
	--berichte) MODUS=berichte ;;
	--umstieg) MODUS=umstieg ;;
	"") ;;
	*) echo "Studio-Abgleich: unbekannte Option „$1“ (--charge <Pfad> | --nach-pull | --berichte | --umstieg)"; exit 0 ;;
esac

REPO=${NIRO_STUDIO_REPO:-$(git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p')}
[ -n "$REPO" ] || REPO=$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)
NAS=${NIRO_STUDIO_NAS:-"/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio"}
SCHLUESSEL=$(printf '%s' "$REPO" | sed 's/[^A-Za-z0-9]/-/g')
GEDAECHTNIS=${NIRO_CLAUDE_MEMORY_DIR:-"$HOME/.claude/projects/$SCHLUESSEL/memory"}
TEILE=""

teil() { if [ -z "$TEILE" ]; then TEILE=$1; else TEILE="$TEILE · $1"; fi; }
nas_da() { [ -d "$(dirname "$NAS")" ]; }
im_worktree() {
	[ -z "${NIRO_STUDIO_REPO:-}" ] || return 1
	eigen=$(git rev-parse --git-dir 2>/dev/null) && gemeinsam=$(git rev-parse --git-common-dir 2>/dev/null) || return 1
	[ "$(cd "$eigen" && pwd -P)" != "$(cd "$gemeinsam" && pwd -P)" ]
}

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

berichte_abgleichen() {
	lokal="$REPO/berichte"; fern="$NAS/berichte"
	mkdir -p "$lokal" "$fern" || { teil "Berichte: Ordner nicht anlegbar"; return; }
	abgleich "$fern" "$lokal" "NAS → lokal (Berichte)"; geholt=$ANZAHL
	abgleich "$lokal" "$fern" "lokal → NAS (Berichte)"; hochgeladen=$ANZAHL
	teil "Berichte: $geholt geholt, $hochgeladen hochgeladen"
}

# Tagesstand dieses Macs schreiben (tools/tagesbericht/sammler.py), ohne eigenen Abgleich — der folgt gleich hier.
sammler() {
	skript="$REPO/tools/tagesbericht/sammler.py"
	if [ -n "${NIRO_SAMMLER_CMD:-}" ]; then
		"$NIRO_SAMMLER_CMD" >/dev/null 2>&1 || teil "Sammler: fehlgeschlagen"
	elif [ -f "$skript" ] && command -v python3 >/dev/null 2>&1; then
		python3 "$skript" --still --ohne-abgleich >/dev/null 2>&1 || teil "Sammler: fehlgeschlagen"
	fi
}

# Index MEMORY.md ($1 lokal) in den NAS-Index ($2) einfügen: dessen Zeilen bleiben, lokale Zeilen zu einer dort noch
# nicht verzeichneten Notiz kommen ans Ende (unabhängig davon, welcher Index neuer ist).
index_vereinen() {
	[ -f "$1" ] || return 0
	[ -f "$2" ] || { cp -p "$1" "$2"; return; }
	[ -z "$(tail -c 1 "$2")" ] || echo >> "$2" || return 1
	while IFS= read -r zeile || [ -n "$zeile" ]; do
		[ -n "$zeile" ] || continue
		rest=${zeile#*"]("}
		if [ "$rest" != "$zeile" ]; then
			grep -Fq "](${rest%%")"*})" "$2" && continue
		else
			grep -Fxq -- "$zeile" "$2" && continue
		fi
		printf '%s\n' "$zeile" >> "$2" || return 1
	done < "$1"
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
		konflikte=0
		for datei in "$GEDAECHTNIS"/*; do
			name=${datei##*/}
			[ -f "$datei" ] && [ "$name" != MEMORY.md ] && [ -f "$ziel/$name" ] && ! cmp -s "$datei" "$ziel/$name" \
				&& konflikte=$((konflikte + 1))
		done
		if ! rsync -rt --update --modify-window=2 --exclude='.DS_Store' --exclude='/MEMORY.md' "$GEDAECHTNIS/" "$ziel/"; then
			teil "Gedächtnis: Hochladen fehlgeschlagen — nicht verknüpft"; return 1
		fi
		index_vereinen "$GEDAECHTNIS/MEMORY.md" "$ziel/MEMORY.md" || { teil "Gedächtnis: Index nicht zusammengeführt — nicht verknüpft"; return 1; }
		sicherung="$GEDAECHTNIS.vor-nas-$(date +%Y%m%d-%H%M%S)"
		mv "$GEDAECHTNIS" "$sicherung" || { teil "Gedächtnis: Sicherung fehlgeschlagen — nicht verknüpft"; return 1; }
		ln -s "$ziel" "$GEDAECHTNIS" || { mv "$sicherung" "$GEDAECHTNIS"; teil "Gedächtnis: Verknüpfung fehlgeschlagen"; return 1; }
		hinweis=""
		[ "$konflikte" -gt 0 ] && hinweis="; $konflikte gleichnamige Notiz(en) mit anderem Inhalt — neuere behalten, lokale Fassung in der Sicherung"
		teil "Gedächtnis zusammengeführt und verknüpft (Sicherung $(basename "$sicherung")$hinweis)"
		return 0
	fi
	mkdir -p "$(dirname "$GEDAECHTNIS")" && ln -s "$ziel" "$GEDAECHTNIS" && teil "Gedächtnis verknüpft (neu)"
}

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

umstieg() {
	if [ -z "$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null)" ]; then
		echo "Umstieg abgebrochen: bitte im Ordner des NIRO-Studio-Repos ausführen."; exit 1
	fi
	git -C "$REPO" config core.hooksPath .githooks
	if ! nas_da; then
		echo "Umstieg abgebrochen: NAS nicht verbunden ($(dirname "$NAS")) — nichts geändert."; exit 1
	fi
	mkdir -p "$NAS/projects" || { echo "Umstieg abgebrochen: NAS-Ordner nicht anlegbar."; exit 1; }
	# Unveränderte versionierte Projektdateien tragen das Datum ihres Checkouts, nicht ihrer Bearbeitung: Sie bekommen
	# das Jahr 2000, damit sie neuere Stände des anderen Macs auf dem NAS nicht überschreiben (Inhalt liegt in git).
	geaendert=$(mktemp -t studio_umstieg) || { echo "Umstieg abgebrochen: keine Temp-Datei."; exit 1; }
	git -C "$REPO" diff -z --name-only HEAD -- projects 2>/dev/null | tr '\0' '\n' > "$geaendert"
	git -C "$REPO" ls-files -z projects 2>/dev/null | tr '\0' '\n' | grep -Fxv -f "$geaendert" | tr '\n' '\0' \
		| (cd "$REPO" && xargs -0 touch -c -t 200001010000)
	rm -f "$geaendert"
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

[ "$MODUS" = "umstieg" ] && umstieg
if im_worktree; then
	[ "$MODUS" = "nach-pull" ] && { echo "Studio-Abgleich: Worktree — kein Abgleich (projects/ liegt im Hauptordner $REPO)"; exit 0; }
	teil "Worktree: abgeglichen wird der Hauptordner $REPO/projects"
fi
if ! nas_da; then
	echo "Studio-Abgleich: NAS nicht verbunden ($(dirname "$NAS")) — lokal bleibt alles, Abgleich später: sh tools/studio_abgleich.sh"
	[ "$MODUS" = "nach-pull" ] && abhaengigkeiten && [ -n "$TEILE" ] && echo "$TEILE"
	exit 0
fi
if [ "$MODUS" = "berichte" ]; then
	berichte_abgleichen
	echo "$TEILE"
	exit 0
fi
gedaechtnis_verknuepfen
chargen_abgleichen
[ -f "$REPO/tools/resolve/luts_sync.sh" ] && sh "$REPO/tools/resolve/luts_sync.sh"
sammler
berichte_abgleichen
[ "$MODUS" = "nach-pull" ] && abhaengigkeiten
echo "$TEILE"
exit 0
