#!/bin/zsh
# BumbleClean-Look „Ultraclean Dramatic" — Entwicklungs-Iteration auf einem Basis-TIFF.
# Aufruf: look_dev.sh <basis.tiff> <ausgabe.jpg> [breite]
# Stufen: selektive Gelb→Gold-Dämpfung (HSB), Tonwert-S-Kurve mit sattem
# Schwarz, kühle Schattennote, dezente Vignette. Parameter unten zentral.
set -e

IN="$1"; OUT="$2"; W="${3:-1600}"

# --- Look-Parameter (v3) ---
YELLOW_C=0.155      # Hue-Zentrum Gelb (HSB 0..1)
YELLOW_W=0.055      # Gauss-Breite der Hue-Maske
SAT_DROP=0.30       # max. Sättigungs-Reduktion im Gelb (0..1)
VAL_DROP=0.26       # max. Abdunklung im Gelb
HUE_SHIFT=0.032     # Hue-Verschiebung Richtung Gold (minus = wärmer)
GREEN_C=0.34        # Hue-Zentrum Grün (Tageslicht-Mischlicht dämpfen)
GREEN_W=0.10        # Gauss-Breite Grün
SAT_DROP_G=0.50     # Sättigungs-Reduktion im Grün
TARGET_MEAN=0.26    # Ziel-Helligkeit für Auto-Angleich (mean Luma 0..1)
GAIN_MIN=0.85       # Gain-Klemme unten
GAIN_MAX=2.10       # Gain-Klemme oben (Interieur-Push)
BLACK_PT=1.8        # Schwarzpunkt in %
WHITE_PT=99.6       # Weißpunkt in %
MID_GAMMA=0.90      # Mitteltöne (unter 1 = dunkler/dramatischer)
SCONTRAST="3.4x44%" # S-Kurve Stärke x Zentrum
GLOB_SAT=92         # globale Sättigung (%)
GLOB_HUE=99.3       # globaler Hue-Trim (unter 100 = Tick Richtung Magenta)
COOL_B=1.04         # Blau-Gamma Schatten (kühle Note)
CLARITY="0x22+0.13+0.02"  # Großradius-USM = Mikrokontrast/Klarheit
VIG_STRength=85     # Vignette: Randhelligkeit in % (100 = aus)

TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

# 0) Auto-Belichtungsangleich: mean Luma messen, Gain in Linearlicht anwenden
MEAN=$(magick "$IN" -resize 400x400 -colorspace gray -format "%[fx:mean]" info:)
GAIN=$(python3 -c "m=$MEAN; g=($TARGET_MEAN/max(m,0.01))**0.65; print(round(min(max(g,$GAIN_MIN),$GAIN_MAX),3))")

# 1) verkleinern, Gain, nach HSB
magick "$IN" -resize "${W}x${W}" \
  -colorspace RGB -evaluate multiply "$GAIN" -colorspace sRGB \
  -colorspace HSB "$TMP/hsb.miff"

# 2) selektive Farb-Behandlung: Gelb→Gold (Sättigung/Helligkeit/Hue),
#    Grün (Tageslicht-Mischlicht) nur entsättigen
magick "$TMP/hsb.miff" \
  -channel G -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); kb=exp(-pow((u.r-$GREEN_C)/$GREEN_W,2)); u*(1-$SAT_DROP*ka)*(1-$SAT_DROP_G*kb)" \
  -channel B -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); u*(1-$VAL_DROP*ka)" \
  -channel R -fx "ka=exp(-pow((u.r-$YELLOW_C)/$YELLOW_W,2)); u-$HUE_SHIFT*ka" \
  +channel -set colorspace HSB -colorspace sRGB "$TMP/graded.miff"

# 3) Tonwerte: Schwarzpunkt, S-Kurve, Mitteltöne, globale Sättigung, kühle Schatten
magick "$TMP/graded.miff" \
  -level "${BLACK_PT}%,${WHITE_PT}%,$MID_GAMMA" \
  -sigmoidal-contrast "$SCONTRAST" \
  -modulate "100,$GLOB_SAT,$GLOB_HUE" \
  -channel B -gamma "$COOL_B" +channel \
  -unsharp "$CLARITY" \
  "$TMP/toned.miff"

# 4) Vignette (radial multiply) + Ausgabe
magick "$TMP/toned.miff" \
  \( +clone -fill white -colorize 100 -size "%wx%h" radial-gradient:"white-gray($VIG_STRength%)" -delete 0 \) \
  -compose multiply -composite \
  -quality 92 "$OUT"
