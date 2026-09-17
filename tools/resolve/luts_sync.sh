#!/bin/sh
#
# NIRO-Grading-LUTs zwischen Repo und DaVinci Resolve abgleichen — damit beide Macs dieselben LUTs haben.
#
# Quelle ist das Repo: tools/resolve/luts/NIRO Grading/<Resolve-Projekt>/*.cube
# Ziel ist Resolves LUT-Ordner:  /Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/NIRO Grading/
# Die Grades in Resolve verweisen auf den relativen Pfad „NIRO Grading/<Projekt>/<Datei>.cube" — der muss auf jedem
# Rechner gleich sein, sonst zeigt Resolve die LUT als fehlend.
#
# Aufruf:
#   sh tools/resolve/luts_sync.sh                     Repo → Resolve installieren UND in Resolve neu angelegte
#                                                     NIRO-LUTs ins Repo holen (danach committen + pushen)
#   sh tools/resolve/luts_sync.sh --nur-installieren  nur Repo → Resolve (so rufen es die Git-Hooks nach pull/checkout)
#
# Löscht nie etwas und überschreibt nur mit neueren Dateien. Beendet sich immer mit 0 — darf git nie blockieren.
# Test mit anderem Zielordner: NIRO_RESOLVE_LUT_DIR=/tmp/lut sh tools/resolve/luts_sync.sh

REPO=$(cd "$(dirname "$0")/../.." && pwd)
SRC="$REPO/tools/resolve/luts/NIRO Grading"
DST_ROOT=${NIRO_RESOLVE_LUT_DIR:-"/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"}
DST="$DST_ROOT/NIRO Grading"
MODUS=${1:-}

if [ ! -d "$DST_ROOT" ]; then
	echo "LUT-Sync: Resolve-LUT-Ordner fehlt ($DST_ROOT) — ist DaVinci Resolve installiert? Nichts kopiert."
	exit 0
fi
if [ ! -w "$DST_ROOT" ]; then
	echo "LUT-Sync: kein Schreibrecht auf „$DST_ROOT“."
	echo "          Einmalig im Terminal:  sudo chmod a+w \"$DST_ROOT\"   — danach: sh tools/resolve/luts_sync.sh"
	exit 0
fi
mkdir -p "$SRC" "$DST" || exit 0

zaehle() { grep -c '^>f' || true; }

installiert=$(rsync -a --update --itemize-changes --include='*/' --include='*.cube' --exclude='*' "$SRC/" "$DST/" 2>/dev/null | zaehle)
geholt=0
if [ "$MODUS" != "--nur-installieren" ]; then
	geholt=$(rsync -a --update --itemize-changes --include='*/' --include='*.cube' --exclude='*' "$DST/" "$SRC/" 2>/dev/null | zaehle)
fi

if [ "${installiert:-0}" -gt 0 ]; then
	echo "LUT-Sync: $installiert NIRO-LUT(s) in Resolve installiert ($DST)."
	aktualisiert=""
	PY="$REPO/tools/autocut/venv/bin/python"
	if [ -z "${NIRO_RESOLVE_LUT_DIR:-}" ] && [ -x "$PY" ] && pgrep -f "DaVinci Resolve.app/Contents/MacOS/Resolve" >/dev/null 2>&1; then
		aktualisiert=$("$PY" - "$REPO" 2>/dev/null <<'PYEOF'
import signal, sys
signal.alarm(10)
sys.path.insert(0, sys.argv[1] + "/tools/autocut/src")
from niro_autocut import resolve_api as RA
p = RA.connect().GetProjectManager().GetCurrentProject()
print("ja" if p and p.RefreshLUTList() else "")
PYEOF
)
	fi
	if [ "$aktualisiert" = "ja" ]; then
		echo "          LUT-Liste im offenen Resolve-Projekt aktualisiert."
	else
		echo "          In Resolve: Projekteinstellungen → Color Management → „Update Lists“ — oder Resolve neu starten."
	fi
fi
if [ "${geholt:-0}" -gt 0 ]; then
	echo "LUT-Sync: $geholt neue NIRO-LUT(s) aus Resolve ins Repo geholt (tools/resolve/luts/NIRO Grading) —"
	echo "          committen und pushen, damit der andere Mac sie beim nächsten Pull bekommt."
fi
exit 0
