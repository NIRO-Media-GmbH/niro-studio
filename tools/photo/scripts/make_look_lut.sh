#!/bin/zsh
# Backt den Farb-/Tonwert-Teil eines Looks in eine HALD-CLUT (punktweise Ops only —
# Gain, Clarity und Vignette bleiben bildabhängig im Batch-Skript).
# Aufruf: make_look_lut.sh <ausgabe.png>
set -e
OUT="$1"

# v5 — Feedback Runde 3: mehr Punch/Drama. Kern: MITTELTÖNE-SENKE — dunkelt
# gezielt die Umgebung (Boden/Wände, Luma ~0.2–0.45) ab, lässt schwarzen Lack
# (tiefer) und Reflexe (heller) stehen → Spotlight-Wirkung wie in den
# Referenzen, ohne den v3-Fehler (global dunkel) zu wiederholen.
YELLOW_C=0.155; YELLOW_W=0.055; SAT_DROP=0.42; VAL_DROP=0.26; HUE_SHIFT=0.032
GREEN_C=0.34;   GREEN_W=0.10;   SAT_DROP_G=0.65
BLACK_PT=2.5;   WHITE_PT=99.6;  MID_GAMMA=1.00
SCONTRAST="3.2x47%"; GLOB_SAT=95; GLOB_HUE=98.9; COOL_B=1.03
HILIGHT_STRETCH=97.5   # obere Töne auf 100% strecken → Glanz
VALLEY_C=0.32; VALLEY_W=0.14; VALLEY_A=0.13   # Mitteltöne-Senke (Umgebung)

magick hald:12 \
  -colorspace HSB \
  -channel G -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); kb=exp(-pow((u.r-$GREEN_C)/$GREEN_W,2)); u*(1-$SAT_DROP*ka)*(1-$SAT_DROP_G*kb)" \
  -channel B -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); u*(1-$VAL_DROP*ka)" \
  -channel R -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); u-$HUE_SHIFT*ka" \
  +channel -set colorspace HSB -colorspace sRGB \
  -fx "lum=0.299*u.r+0.587*u.g+0.114*u.b; kf=1-($VALLEY_A*exp(-pow((lum-$VALLEY_C)/$VALLEY_W,2)))/max(lum,0.01); u*kf" \
  -level "${BLACK_PT}%,${WHITE_PT}%,$MID_GAMMA" \
  -sigmoidal-contrast "$SCONTRAST" \
  -modulate "100,$GLOB_SAT,$GLOB_HUE" \
  -channel B -gamma "$COOL_B" +channel \
  -level "0%,${HILIGHT_STRETCH}%" -clamp \
  "$OUT"
echo "LUT geschrieben: $OUT"
