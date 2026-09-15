"""Ton-Prüfung Testcut: Pegel je Passage, Pause vor dem Peak, Quell-Abgleich an mehrdeutigen Schnittstellen (Kreuzkorrelation Schnitt ↔ FX3-Original)."""
import json, subprocess
from pathlib import Path
import numpy as np
CH = Path("/Users/jansantos/NIRO Studio/projects/Marien-Elisabeth-Kliniken/Imagefilm/2026-06 Ads und Imagefilm Dreh")
CUT = CH/"Material/Testcut/MEK Test1.mov"
idx = {r["name"].rsplit(".",1)[0]: r for r in json.load(open(CH/"_intern/transcripts_index.json"))}
SR = 16000
def pcm(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.3f}"] if ss is not None else []) + ["-i", str(path)] + (["-t", f"{t:.3f}"] if t else []) + ["-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(np.float64)
def lufs(path, a, b):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{a}", "-t", f"{b-a}", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    l = [x for x in out.splitlines() if x.strip().startswith("I:")]
    return float(l[-1].split()[1]) if l else float("nan")
cut = pcm(CUT)
print("== Pegel je Passage (LUFS)")
P = [("Intro B-Roll/Drohne", 0.0, 14.9), ("Atmo 'grüner Bereich'", 14.9, 16.6), ("vor Sandra", 16.6, 20.1), ("Sandra", 20.2, 26.3), ("Zoran", 28.3, 33.2), ("Ramona 1", 34.1, 39.9),
     ("Jessi", 40.9, 47.7), ("Marina", 48.2, 51.8), ("Martina", 53.4, 66.4), ("Simona", 67.3, 73.6), ("Lücke vor Alina", 73.6, 77.6), ("Alina", 77.6, 87.0),
     ("Christian", 88.1, 96.4), ("Ramona 2", 96.4, 103.6), ("Johanna", 103.6, 110.9), ("Lücke vor Marcel", 110.85, 111.95), ("Marcel (Peak)", 111.9, 122.1),
     ("Katja", 123.1, 130.9), ("Schluss", 130.9, 134.2)]
for n, a, b in P: print(f"  {n:<26} {a:6.2f}–{b:6.2f}  {lufs(CUT, a, b):6.1f}")
def rmsdb(x): return 20*np.log10(np.sqrt(np.mean(x**2))+1e-12)
print("\n== Pause vor dem Peak: RMS je 0,1 s (109,8–112,6 s)")
print("  " + " ".join(f"{t:.1f}:{rmsdb(cut[int(t*SR):int((t+0.1)*SR)]):.0f}" for t in np.arange(109.8, 112.6, 0.1)))
def locate(cut_a, cut_b, stem, src_a, src_b, win=0.3, hop=0.1):
    src = pcm(idx[stem]["path"], src_a, src_b - src_a)
    c2 = np.concatenate([[0], np.cumsum(src**2)])
    print(f"\n== {stem}: Schnitt {cut_a}–{cut_b} s gegen Quelle {src_a}–{src_b} s")
    for t in np.arange(cut_a, cut_b - win + 1e-9, hop):
        seg = cut[int(t*SR):int((t+win)*SR)]
        if np.linalg.norm(seg) < 1e-3: print(f"  {t:6.2f}: still"); continue
        n = 1 << int(np.ceil(np.log2(len(src) + len(seg))))
        corr = np.fft.irfft(np.fft.rfft(src, n) * np.fft.rfft(seg[::-1], n), n)[len(seg)-1:len(src)]
        en = np.sqrt(c2[len(seg):len(seg)+len(corr)] - c2[:len(corr)]) * np.linalg.norm(seg) + 1e-12
        nc = corr / en; k = int(np.argmax(nc))
        print(f"  Schnitt {t:6.2f} → Quelle {src_a + k/SR:7.2f} s  (Korr {nc[k]:.2f})")
locate(21.9, 24.6, "FX3_9557", 212.0, 222.0)      # Sandra: Zwischenruf „Und warum?" 03:36?
locate(124.6, 127.2, "FX3_9649", 58.0, 70.0)      # Katja: „vierundzwanzig Jahren hier" aus Vorstellung?
locate(124.6, 127.2, "FX3_9649", 498.0, 516.0)    # … oder aus 08:21 ff.
locate(120.9, 122.2, "FX3_9982", 452.0, 460.0)    # Marcel: zweites „Themen sind"
