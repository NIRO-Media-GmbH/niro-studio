#!/bin/zsh
# Batch-Entwicklung: wendet einen LUT-Look auf entwickelte Basis-TIFFs an.
# Belichtung wird auf einer LACK-/MOTIV-ANKERREGION pro Bild verankert (nicht
# Gesamtbild-Mean — sonst schwankt die Auto-Helligkeit mit dem Bildausschnitt).
# Pro Bild: Anker-Gain (Linearlicht) → HALD-CLUT → Clarity → Vignette → Exporte.
# Aufruf: develop_batch.sh <lut.png> <tiff-verz> <ausgabe-verz> <ref_anchor> \
#           <NR:BILD:X:Y:W:H[:FAKTOR] ...>
#   X/Y/W/H = Ankerregion in % der Bildfläche; FAKTOR skaliert das Ziel
#   (z. B. 0.75 für bewusst dunklere Stimmungsbilder). ref_anchor = Anker-Mean
#   des Referenzbilds (vorab auf dessen TIFF-Region gemessen).
set -e
LUT="$1"; SRC="$2"; OUT="$3"; REF="$4"; shift 4

GAIN_MIN=0.40; GAIN_MAX=3.00
VIG=80            # Randhelligkeit % (kräftiger für Spotlight-Drama, v5)
QUAL=92

mkdir -p "$OUT/web"

for spec in "$@"; do
  parts=(${(s/:/)spec})
  NR=$parts[1]; N=$parts[2]; RX=$parts[3]; RY=$parts[4]; RW=$parts[5]; RH=$parts[6]
  FAC=${parts[7]:-1.0}
  IN="$SRC/_A7_$N.ARW.tiff"
  FULL="$OUT/BumbleClean_Boxster_${NR}_${N}.jpg"
  WEB="$OUT/web/BumbleClean_Boxster_${NR}_${N}_web.jpg"

  DIM=$(magick identify -format "%w %h" "$IN")
  IW=${DIM%% *}; IH=${DIM##* }
  PX=$((IW*RX/100)); PY=$((IH*RY/100)); PW=$((IW*RW/100)); PH=$((IH*RH/100))

  ANCHOR=$(magick "$IN" -crop "${PW}x${PH}+${PX}+${PY}" -colorspace gray -format "%[fx:mean]" info:)
  GAIN=$(python3 -c "a=$ANCHOR; g=($REF*$FAC)/max(a,0.005); print(round(min(max(g,$GAIN_MIN),$GAIN_MAX),3))")

  # Clarity als Resize-Highpass (entspricht USM Sigma ~ lange Kante/73, Stärke 0.13,
  # aber um Größenordnungen schneller als -unsharp bei 33 MP):
  # result = 1.13*Bild − 0.13*Tiefpass  (Tiefpass = 1/32 runter- und wieder hochskaliert)
  # WICHTIG: -clamp nach Gain und nach dem Highpass — Homebrew-IM ist Q16-HDRI,
  # Werte >1.0 liegen sonst außerhalb des LUT-Würfels und -hald-clut
  # verfärbt die Highlights (Magenta/Cyan-Artefakte).
  magick "$IN" \
    -colorspace RGB -evaluate multiply "$GAIN" -clamp -colorspace sRGB -clamp \
    "$LUT" -hald-clut \
    \( +clone -resize 3.125% -resize "${IW}x${IH}!" \) \
    -compose Mathematics -define compose:args='0,-0.24,1.24,0' -composite -clamp \
    \( -size "${IW}x${IH}" radial-gradient:"white-gray(${VIG}%)" \) \
    -compose multiply -composite \
    -quality "$QUAL" "$FULL"

  magick "$FULL" -resize 2048x2048 -unsharp 0x0.8+0.7+0.008 -quality 90 "$WEB"
  echo "$NR ($N): anchor=$ANCHOR gain=$GAIN -> $(basename $FULL)"
done
