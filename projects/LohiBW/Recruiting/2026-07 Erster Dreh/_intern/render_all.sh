#!/bin/bash
# Rendert die vier Untertitel-Overlays und brennt sie aufs Original.
#
# Zweistufig mit Absicht: Remotion rendert nur die transparente
# Textspur (muss das 4K-Video also gar nicht dekodieren), ffmpeg legt
# sie danach in einem Durchgang darüber. Die Alpha-Master bleiben
# liegen — Textkorrekturen brauchen dann keinen Remotion-Lauf mehr.
set -euo pipefail

STUDIO="/Users/jansantos/NIRO Studio"
CHARGE="$STUDIO/projects/LohiBW/Recruiting/2026-07 Erster Dreh"
MOTION="$STUDIO/tools/motion"
ALPHA="$CHARGE/_intern/work/alpha"
OUT="$CHARGE/Ergebnisse/Renders"

mkdir -p "$ALPHA" "$OUT"

# Sperre: zwei gleichzeitige Läufe schreiben dieselben Dateien und
# vermischen alte und neue Untertitel (passiert am 13.08.2026, als ein
# hängender Lauf verspätet ansprang). mkdir ist atomar.
LOCK="$CHARGE/_intern/work/.render.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "ABBRUCH: Es läuft bereits ein Render (Sperre: $LOCK)." >&2
  echo "Wenn sicher kein Lauf mehr aktiv ist: rmdir \"$LOCK\"" >&2
  exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT INT TERM

cd "$MOTION"

titles=(
  "Video 1 - Der schnellere Weg nach oben"
  "Video 2 - Raus aus dem Fristen-Hamsterrad"
  "Video 3 - Wieder mit Menschen arbeiten"
  "Video 4 - Der Steuerjob, der sich nach deinem Leben richtet"
)

for i in 1 2 3 4; do
  title="${titles[$((i-1))]}"
  src="$CHARGE/Material/Video/$title.mp4"
  mov="$ALPHA/untertitel-$i.mov"
  dst="$OUT/$title - Untertitel.mp4"

  echo "=== [$i/4] $title"

  if [ ! -f "$mov" ]; then
    echo "  -> Alpha-Overlay rendern"
    npx remotion render src/index.ts "LohiBW-Untertitel-$i" "$mov" \
      --image-format=png \
      --pixel-format=yuva444p10le \
      --codec=prores \
      --prores-profile=4444 \
      --public-dir=public-lohi \
      --log=error
  else
    echo "  -> Alpha liegt schon vor, überspringe"
  fi

  echo "  -> einbrennen"
  ffmpeg -v error -stats \
    -i "$src" -i "$mov" \
    -filter_complex "[0:v][1:v]overlay=format=auto:eof_action=pass[v]" \
    -map "[v]" -map 0:a? \
    -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p \
    -c:a aac -b:a 192k \
    -movflags +faststart \
    -y "$dst"

  echo "  fertig: $(basename "$dst")"
done

echo
echo "ALLE VIER FERTIG"
ls -la "$OUT"
