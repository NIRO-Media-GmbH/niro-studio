"""Ton-Prüfung Video 3 NEU: Sprachpegel je Passage (LUFS kurz), Musik-Versatz neu→alt in sprachfreien Lücken,
harte Sprünge/Knackser an Schnittstellen, Lage des Spitzenpegels."""
import subprocess, unicodedata, json
from pathlib import Path
import numpy as np
P = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Recruiting/2026-07 Erster Dreh")
PR = next(p for p in P.iterdir() if unicodedata.normalize("NFC", p.name) == "Prüfen")
ALT = next(p for p in PR.iterdir() if p.name.endswith("_720p.mp4")); NEU = next(p for p in PR.iterdir() if p.name.endswith("_NEU.mov"))
def pcm(path, sr, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", str(ch), "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch)
def lufs_seg(path, a, b):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{a}", "-t", f"{b-a}", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    line = [l for l in out.splitlines() if l.strip().startswith("I:")]
    return float(line[-1].split()[1]) if line else float("nan")
segs_neu = [("Hook Christian", 0.10, 4.98), ("Zoran NEU 'Beruf am Limit'", 10.12, 17.46), ("Christian Ausstattung", 19.90, 29.14),
            ("Zoran Augenhöhe", 32.88, 34.92), ("Katja Monitor", 35.40, 41.88), ("Zoran an die Hand", 42.46, 49.18), ("Christian CTA", 50.34, 56.98),
            ("Musik-Lücke nach Hook", 5.1, 10.0), ("Musik-Lücke vor Christian", 17.6, 19.8), ("Musik-Brücke #4", 29.3, 32.8)]
segs_alt = [("Hook Christian", 0.12, 4.88), ("Christian Ausstattung", 10.10, 19.30), ("Christian CAC", 20.00, 32.00), ("Zoran Technik+Augenhöhe", 35.92, 41.24),
            ("Katja Monitor", 41.74, 48.22), ("Zoran an die Hand", 49.30, 56.10), ("Christian CTA", 57.16, 63.80), ("Musik-Lücke nach Hook", 5.0, 10.0), ("Musik-Brücke", 32.2, 35.8)]
print("== Sprach-/Musikpegel je Passage (integriert, LUFS)")
for tag, path, segs in (("neu", NEU, segs_neu), ("alt", ALT, segs_alt)):
    for n, a, b in segs: print(f"  {tag}  {n:<30} {a:6.2f}–{b:6.2f}  {lufs_seg(path, a, b):6.1f} LUFS")
# Musik-Versatz per Kreuzkorrelation (8 kHz mono)
SR = 8000
x_new = pcm(NEU, SR)[:, 0]; x_old = pcm(ALT, SR)[:, 0]
def best_offset(seg):
    n = len(x_old) + len(seg)
    F = np.fft.rfft(x_old, n); G = np.fft.rfft(seg[::-1], n)
    corr = np.fft.irfft(F * G, n)[len(seg)-1:len(x_old)]
    # Normierung
    c2 = np.concatenate([[0], np.cumsum(x_old.astype(np.float64)**2)])
    energy = np.sqrt(c2[len(seg):len(seg)+len(corr)] - c2[:len(corr)]) * np.sqrt(np.sum(seg.astype(np.float64)**2)) + 1e-9
    nc = corr / energy
    k = int(np.argmax(nc)); return k / SR, float(nc[k])
print("\n== Versatz neu→alt je 0,5-s-Fenster (nur Fenster mit Korrelation ≥ 0,6)")
rows = []
for t in np.arange(0, len(x_new)/SR - 0.5, 0.25):
    seg = x_new[int(t*SR):int((t+0.5)*SR)]
    if np.sqrt(np.mean(seg**2)) < 1e-4: continue
    off, c = best_offset(seg)
    rows.append((t, off - t, c))
prev = None
for t, d, c in rows:
    tag = f"{d:+7.2f}s" if c >= 0.6 else "   —   "
    if c >= 0.6 and (prev is None or abs(d - prev) > 0.03):
        print(f"  ab neu {t:6.2f}s: Versatz alt−neu {d:+7.2f}s (Korr {c:.2f})"); prev = d
json.dump(rows, open(P/"_intern/review-v3-neu/audio_offsets.json", "w"))
# Knackser: Sprünge im Stereo-PCM (48 kHz) relativ zur lokalen Umgebung
X = pcm(NEU, 48000, 2); m = X.mean(axis=1)
d = np.abs(np.diff(m)); win = 480
loc = np.convolve(d, np.ones(win)/win, mode="same") + 1e-6
ratio = d / loc
idx = np.where((ratio > 25) & (d > 0.05))[0]
print("\n== auffällige Sample-Sprünge (Knackser-Verdacht) neu:")
last = -1
for i in idx:
    if i - last > 4800: print(f"  {i/48000:7.3f}s  Sprung {d[i]:.3f}  (×{ratio[i]:.0f} ggü. Umgebung)")
    last = i
pk = int(np.argmax(np.abs(X).max(axis=1))); print(f"\n== Sample-Spitze neu bei {pk/48000:.3f}s: {20*np.log10(np.abs(X).max()):.2f} dBFS")
