#!/bin/zsh
# ============================================================
# WLC Recruiting — alle Overlay-/Karten-Renders neu bauen
# Ziel: Unterordner "2026-09-09 Neue Schrift (Wuerth Sans)", Dateien mit
# Suffix -WuerthSans, damit die Fassung auch einzeln verschickt eindeutig ist.
# Der Hauptordner Renders/ behält bewusst den alten Auslieferungsstand.
# Angelegt 09.09.2026 bei der Schrift-Umstellung auf Wuerth Sans.
#
# Hintergrund: Die Varianten-Renders (Endcards, V6-Outro) brauchen
# Props, die vorher nirgends gespeichert waren und aus den fertigen
# .mov-Dateien zurückgelesen werden mussten. Die JSONs in
# _intern/render-props/ halten sie jetzt fest — bitte dort pflegen,
# nicht wieder per --props von Hand tippen.
#
# Aufruf aus tools/motion:   zsh "<pfad>/render-all.sh"
# Einzelne Zeile auskommentieren, wenn nur Teile neu sollen.
# ============================================================
set -e
cd "$(dirname "$0")/../../../../../tools/motion"

OUT="../../projects/WLC/Recruiting/2026-07 Erster Dreh/Ergebnisse/Renders/2026-09-09 Neue Schrift (Wuerth Sans)"
PROPS="../../projects/WLC/Recruiting/2026-07 Erster Dreh/_intern/render-props"
# Flags bewusst ausgeschrieben: zsh splittet $VAR-Flaglisten nicht.
r() {  # r <CompId> <Zieldatei> [Props-JSON]
  local id="$1" out="$2" props="$3"
  echo "▶︎ $id → $out"
  if [[ -n "$props" ]]; then
    npx remotion render src/index.ts "$id" "$OUT/$out" \
      --image-format=png --pixel-format=yuva444p10le --codec=prores \
      --prores-profile=4444 --public-dir=public-wlc --props="$PROPS/$props"
  else
    npx remotion render src/index.ts "$id" "$OUT/$out" \
      --image-format=png --pixel-format=yuva444p10le --codec=prores \
      --prores-profile=4444 --public-dir=public-wlc
  fi
}

# --- Haupt-Overlays (Defaults im Code) ---
r WlcV1-Overlay      V1-overlay-captions-WuerthSans.mov
r WlcV2-Overlay      V2-overlay-captions-WuerthSans.mov
r WlcV3-Overlay      V3-overlay-captions-WuerthSans.mov
r WlcV4-Overlay      V4-overlay-captions-WuerthSans.mov
r WlcV5-Overlay      V5-overlay-captions-WuerthSans.mov
r WlcV7-Overlay      V7-overlay-captions-WuerthSans.mov

# --- V6-Bausteine ---
r WlcV6-WortBattle   V6-wort-battle-alpha-WuerthSans.mov
r WlcV6-Trio         V6-trio-alpha-WuerthSans.mov
r WlcV6-BeweisCard   V6-beweis-card-6-standorte-belegt-WuerthSans.mov
r WlcV6-Outro        V6-outro-map-cta-WAPPEN-WuerthSans.mov
r WlcV6-Outro        V6-outro-map-cta-LOGOBOX-WuerthSans.mov          v6-outro-LOGOBOX.json
r WlcV6-Outro        V6-outro-map-cta-WAPPEN-STELLEN-WuerthSans.mov   v6-outro-WAPPEN-STELLEN.json

# --- Endcards (Defaults = Lager/Wappen) ---
r WlcJob-Endcard     endcard-V1-V2-V4-V5-lager-WAPPEN-WuerthSans.mov
r WlcJob-Endcard     endcard-V1-V2-V4-V5-lager-LOGOBOX-WuerthSans.mov endcard-lager-LOGOBOX.json
r WlcJob-Endcard     endcard-V3-kaufmann-WAPPEN-WuerthSans.mov        endcard-kaufmann-WAPPEN.json
r WlcJob-Endcard     endcard-V3-kaufmann-LOGOBOX-WuerthSans.mov       endcard-kaufmann-LOGOBOX.json
r WlcJob-Endcard     endcard-V7-azubi-WAPPEN-WuerthSans.mov           endcard-azubi-WAPPEN.json
r WlcJob-Endcard     endcard-V7-azubi-LOGOBOX-WuerthSans.mov          endcard-azubi-LOGOBOX.json

echo "✓ Alle 18 Renders fertig."
