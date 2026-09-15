#!/bin/bash
# MAN Wartezimmervideo — alle Remotion-Renders (ProRes 4444 mit Alpha)
set -u
cd "/Users/jansantos/NIRO Studio/tools/motion"
OUT="/Users/jansantos/NIRO Studio/projects/MAN/Wartezimmervideo/2026-07 Erste Fassung/Ergebnisse/Renders"
mkdir -p "$OUT"
FLAGS="--image-format=png --pixel-format=yuva444p10le --codec=prores --prores-profile=4444"

r() { # id, outname, props(optional)
  local id="$1" name="$2" props="${3:-}"
  if [ -n "$props" ]; then
    npx remotion render src/index.ts "$id" "$OUT/$name.mov" $FLAGS --props="$props" 2>&1 | tail -1
  else
    npx remotion render src/index.ts "$id" "$OUT/$name.mov" $FLAGS 2>&1 | tail -1
  fi
  echo "== $name fertig =="
}

r MAN-WZ-Frame-Solo     frame-solo
r MAN-WZ-Frame-Versetzt frame-versetzt
r MAN-WZ-Frame-Duo      frame-duo
r MAN-WZ-Opener         opener
r MAN-WZ-Endcard        endcard

r MAN-WZ-Trenner trenner-kap1 '{"titel":"VOLLE KONZENTRATION"}'
r MAN-WZ-Trenner trenner-kap2 '{"titel":"EIN STARKES TEAM"}'
r MAN-WZ-Trenner trenner-kap3 '{"titel":"TEILE IM TAKT"}'
r MAN-WZ-Trenner trenner-kap4 '{"titel":"FASZINATION NUTZFAHRZEUG"}'
r MAN-WZ-Trenner trenner-kap5 '{"titel":"MIT HERZ DABEI"}'

r MAN-WZ-Insert insert-O-01 '{"durationInSeconds":16,"zitat":"Nichts passt schon —\nhundert Prozent und nichts anderes.","person":"Julia","rolle":"Nutzfahrzeugmechatronikerin"}'
r MAN-WZ-Insert insert-O-04 '{"durationInSeconds":12,"zitat":"Das Arbeitsklima ist überragend —\nein bisschen eine kleine Familie.","person":"Marcel","rolle":"Geselle"}'
r MAN-WZ-Insert insert-O-05 '{"durationInSeconds":9,"zitat":"Ohne das Team würde es\ndefinitiv nicht gehen.","person":"Julia","rolle":"Nutzfahrzeugmechatronikerin"}'
r MAN-WZ-Insert insert-O-08 '{"durationInSeconds":20,"zitat":"Der Kunde ruft an: Ich brauche dieses Ersatzteil.\nDann schauen wir nach, ob wir das dahaben.","person":"Alexander","rolle":"Teilelager"}'
r MAN-WZ-Insert insert-O-10 '{"durationInSeconds":17,"zitat":"Immer wenn er einen MAN sieht, schreit er:\n„Papa, schau, da ist ein MAN.“ Manchmal kann ich\nauch sagen: Ich habe ihn repariert.","person":"Marcel","rolle":"Geselle"}'
r MAN-WZ-Insert insert-O-12 '{"durationInSeconds":19,"zitat":"Vom TGE bis zum Bundeswehrfahrzeug —\nsechzig, siebzig Tonnen. Sehr beeindruckend.","person":"Hannes","rolle":"Azubi Nutzfahrzeugtechnik"}'
r MAN-WZ-Insert insert-O-15 '{"durationInSeconds":4,"zitat":"Die Stimmung bei MAN ist super.","person":"MAN Werkstatt-Team","rolle":"Servicebetrieb"}'

echo "ALLE RENDERS FERTIG"
ls -la "$OUT"
