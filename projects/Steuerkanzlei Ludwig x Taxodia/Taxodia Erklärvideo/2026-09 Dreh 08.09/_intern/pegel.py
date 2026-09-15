"""Ton-Check (nur lesen): je Bereich RMS/Peak pro Kanal (CH1/CH2) + integrierte Lautheit.
Aufruf: pegel.py  -> druckt Tabelle für die Liste BEREICHE unten."""
import os, re, subprocess, sys, unicodedata
from pathlib import Path
B = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/Steuerkanzlei Ludwig x Taxodia/02_Projekte")
proj = B / [n for n in os.listdir(B) if unicodedata.normalize("NFC", n) == "01_Taxodia Erklärvideo"][0]
KB = proj / "03_Medien" / "01_Footage" / "Kamera-B"

def secs(tc):
    m, s = tc.split(":"); return int(m) * 60 + float(s.replace(",", "."))

BEREICHE = [l.split("|") for l in sys.stdin.read().strip().splitlines()]
for lab, clip, a, b in BEREICHE:
    t0, t1 = secs(a), secs(b)
    fc = ("[0:a]channelsplit=channel_layout=stereo[L][R];"
          "[L]astats=measure_overall=RMS_level+Peak_level:measure_perchannel=none[l];"
          "[R]astats=measure_overall=RMS_level+Peak_level:measure_perchannel=none[r]")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.2f}", "-t", f"{t1-t0:.2f}", "-i", str(KB / f"{clip}.MP4"),
                        "-filter_complex", fc, "-map", "[l]", "-f", "null", "-", "-map", "[r]", "-f", "null", "-"],
                       capture_output=True, text=True)
    rms = re.findall(r"RMS level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    pk = re.findall(r"Peak level dB:\s*(-?[\d.]+|-inf)", r.stderr)
    e = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.2f}", "-t", f"{t1-t0:.2f}", "-i", str(KB / f"{clip}.MP4"),
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = re.findall(r"I:\s*(-?[\d.]+) LUFS", e.stderr); tp = re.findall(r"Peak:\s*(-?[\d.]+) dBFS", e.stderr)
    print(f"{lab:<16} {clip} {a}–{b}  CH1 RMS {rms[0] if rms else '?':>6} Pk {pk[0] if pk else '?':>6} | CH2 RMS {rms[1] if len(rms)>1 else '?':>6} Pk {pk[1] if len(pk)>1 else '?':>6} | I {I[-1] if I else '?'} LUFS TP {tp[-1] if tp else '?'}")
