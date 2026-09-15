#!/bin/bash
# Flacker-Pruefung fuer exportierte Overlays.   ./flicker-check.sh <datei.mov>
#
# Hintergrund: Ein Element mit Deckkraft < 1 bekommt in Chrome eine eigene
# Render-Surface. Remotion-Federn konvergieren gegen 1, erreichen es aber nie
# exakt — die Surface bleibt also bestehen und laesst auf einzelnen Frames
# Kindknoten (typisch: eine Textzeile) weg. Im Standbild faellt das nie auf.
#
# Gemessen wird die BREITE der Bounding-Box der Grafik, nicht ihre Deckung:
# faellt eine Textzeile weg, schrumpft die Box schlagartig, waehrend die
# mittlere Deckkraft nur wenig sinkt. Ein Ausreisser gegen den lokalen Median
# ist der Treffer. Szenenwechsel schlagen ebenfalls an — die Liste ist eine
# Kandidatenliste, kein Urteil: Treffer an Szenengrenzen sind normal.
set -e
FILE="$1"
[ -f "$FILE" ] || { echo "Datei nicht gefunden: $FILE"; exit 1; }
DIR=$(mktemp -d); trap 'rm -rf "$DIR"' EXIT
ffmpeg -v error -i "$FILE" -vf "scale=270:-1" -pix_fmt rgba "$DIR/f%05d.png" -y
( cd "$DIR" && ls *.png | xargs -P 8 -n 1 sh -c \
    'printf "%s %s\n" "$(basename "$0" .png | tr -d f)" \
     "$(magick "$0" -alpha extract -threshold 40% -morphology Open Disk:1 -format "%@" info: 2>/dev/null || echo 0x0+0+0)"' \
  ) > "$DIR/box.txt"
python3 - "$DIR/box.txt" <<'PY'
import sys, re, statistics
v = {}
for line in open(sys.argv[1]):
    p = line.split()
    if len(p) < 2: continue
    m = re.match(r'(\d+)x', p[1])
    if m: v[int(p[0]) - 1] = int(m.group(1))   # ffmpeg zaehlt ab 1, Remotion ab 0
bad = []
for i in sorted(v):
    win = [v[j] for j in range(i - 5, i + 6) if j in v and j != i]
    if len(win) < 8: continue
    med = statistics.median(win)
    if med > 40 and v[i] < 0.6 * med:
        bad.append((i, v[i], int(med)))
print(f"{len(v)} Frames geprueft, {len(bad)} Kandidaten")
for i, w, m in bad:
    print(f"  Frame {i}: Breite {w} statt ~{m}")
PY
