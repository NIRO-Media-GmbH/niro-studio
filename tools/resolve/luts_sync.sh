#!/bin/sh
#
# NIRO-Grading-LUTs zwischen NAS und DaVinci Resolve abgleichen — damit beide Macs dieselben LUTs haben.
#
# Gemeinsame Ablage (NAS): …/01_Projekte/03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading/<Resolve-Projekt>/*.cube
# Lokal (je Mac):          /Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/NIRO Grading/<Resolve-Projekt>/
# Grades verweisen auf den relativen Pfad „NIRO Grading/<Projekt>/<Datei>.cube"; Resolve liest nur lokal. Die lokale Kopie
# hält Grades und Renders auch ohne NAS funktionsfähig.
#
# Wann (User-Entscheid 17.09.2026: Abgleich nur beim Arbeiten, kein Hintergrunddienst):
#   vor jeder Arbeit in Resolve und nach jedem Grading — Claude ruft es selbst auf; sonst von Hand:
#   sh tools/resolve/luts_sync.sh
#
# Richtung: NAS → lokal (installieren) und nur lokal liegende NIRO-LUTs → NAS (für den anderen Mac).
# Löscht nie, überschreibt nur mit neueren Dateien, fasst nur „NIRO Grading" an. Ohne NAS: Hinweis, lokal bleibt alles.
# Beendet sich immer mit 0. Andere Pfade (Tests): NIRO_NAS_LUT_DIR=… NIRO_RESOLVE_LUT_DIR=… sh tools/resolve/luts_sync.sh

REPO=$(cd "$(dirname "$0")/../.." && pwd)
NAS=${NIRO_NAS_LUT_DIR:-"/Volumes/NIRO NAS/NIRO Productions/01_Projekte/03_Vorlagen und Tools/02_Davinci Resolve/LUTs/NIRO Grading"}
DST_ROOT=${NIRO_RESOLVE_LUT_DIR:-"/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"}
DST="$DST_ROOT/NIRO Grading"

if [ ! -d "$DST_ROOT" ]; then
	echo "LUT-Sync: Resolve-LUT-Ordner fehlt ($DST_ROOT) — ist DaVinci Resolve installiert? Nichts abgeglichen."
	exit 0
fi
if [ ! -w "$DST_ROOT" ]; then
	echo "LUT-Sync: kein Schreibrecht auf „$DST_ROOT“."
	echo "          Einmalig im Terminal:  sudo chmod a+w \"$DST_ROOT\"   — danach: sh tools/resolve/luts_sync.sh"
	exit 0
fi
if [ ! -d "$(dirname "$NAS")" ]; then
	echo "LUT-Sync: NAS nicht verbunden ($(dirname "$NAS")) — lokale LUTs bleiben unverändert."
	echo "          Nach dem Verbinden erneut: sh tools/resolve/luts_sync.sh"
	exit 0
fi
mkdir -p "$NAS" "$DST" || exit 0

abgleich() {
	rsync -rt --update --modify-window=2 --itemize-changes --include='*/' --include='*.cube' --exclude='*' \
		"$1/" "$2/" 2>/dev/null | grep -c '^>f' || true
}
installiert=$(abgleich "$NAS" "$DST")
hochgeladen=$(abgleich "$DST" "$NAS")

if [ "${installiert:-0}" -gt 0 ]; then
	echo "LUT-Sync: $installiert NIRO-LUT(s) vom NAS installiert ($DST)."
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
		echo "          In Resolve: Project Settings → Color Management → „Update Lists“ — oder Resolve neu starten."
	fi
fi
if [ "${hochgeladen:-0}" -gt 0 ]; then
	echo "LUT-Sync: $hochgeladen NIRO-LUT(s) aufs NAS kopiert — der andere Mac bekommt sie beim nächsten Abgleich."
fi
if [ "${installiert:-0}" -eq 0 ] && [ "${hochgeladen:-0}" -eq 0 ]; then
	echo "LUT-Sync: NIRO-LUTs aktuell (NAS ↔ lokal)."
fi
exit 0
