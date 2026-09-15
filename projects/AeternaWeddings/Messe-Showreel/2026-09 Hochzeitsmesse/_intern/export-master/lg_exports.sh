#!/bin/bash
# LG-Testexporte aus dem Resolve-Master (Aeterna Messe-Screen v2, 4K50 ProRes 422 LT)
# Aufruf: bash lg_exports.sh 02 05 04 03   bzw.   bash lg_exports.sh 01
set -u
C="/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/2026-09 Hochzeitsmesse"
M="$C/_intern/export-master/Aeterna-Messe-Screen-v2_Master_4K50_ProRes422LT.mov"
E="$C/Ergebnisse/Export"
COLOR=(-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv)
AUDIO_IN=(-f lavfi -t 300 -i anullsrc=channel_layout=stereo:sample_rate=48000)
AUDIO_OUT=(-c:a aac -b:a 128k)
MUX=(-movflags +faststart)

run() {  # Dateiname, danach Video-Argumente
  local name="$1"; shift
  local out="$E/$name"
  local t0
  t0=$(date +%s)
  echo "== $name  Start $(date +%H:%M:%S)"
  if ffmpeg -hide_banner -v error -y -i "$M" "${AUDIO_IN[@]}" -map 0:v:0 -map 1:a:0 "$@" "${COLOR[@]}" "${AUDIO_OUT[@]}" "${MUX[@]}" "$out"; then
    echo "   fertig in $(( $(date +%s) - t0 )) s, $(du -h "$out" | cut -f1)"
  else
    echo "   FEHLER bei $name"
  fi
}

for v in "$@"; do
  case "$v" in
    01) run "01_Aeterna-Messe_4K50_H265_max40Mbps.mp4" \
          -vf format=yuv420p -c:v libx265 -preset medium -crf 18 -profile:v main -tag:v hvc1 \
          -x265-params "level-idc=51:high-tier=0:vbv-maxrate=40000:vbv-bufsize=40000:keyint=100:min-keyint=25:log-level=error" ;;
    02) run "02_Aeterna-Messe_4K50_H265-Apple_30Mbps.mp4" \
          -vf format=yuv420p -c:v hevc_videotoolbox -profile:v main -b:v 30M -g 100 -tag:v hvc1 ;;
    03) run "03_Aeterna-Messe_4K25_H265_max25Mbps.mp4" \
          -vf fps=25,format=yuv420p -c:v libx265 -preset fast -crf 19 -profile:v main -tag:v hvc1 \
          -x265-params "level-idc=50:high-tier=0:vbv-maxrate=25000:vbv-bufsize=25000:keyint=50:min-keyint=13:log-level=error" ;;
    04) run "04_Aeterna-Messe_4K25_H264_max40Mbps.mp4" \
          -vf fps=25,format=yuv420p -c:v libx264 -preset medium -crf 18 -profile:v high -level:v 5.1 -maxrate 40M -bufsize 40M -g 50 ;;
    05) run "05_Aeterna-Messe_1080p50_H264_max16Mbps.mp4" \
          -vf scale=1920:1080:flags=lanczos,format=yuv420p -c:v libx264 -preset medium -crf 18 -profile:v high -level:v 4.2 -maxrate 16M -bufsize 16M -g 100 ;;
    *) echo "unbekannte Variante: $v" ;;
  esac
done
echo "== angefragte Varianten durch $(date +%H:%M:%S)"
