"""Vorlage (Stand 15.09.2026): SFX-Bestand messen — Grundlage für die Auswahl des Sound-Designs (Messung statt Dateinamen).

Aufruf: PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python _intern/sfx/sfx_analyse.py
Liest _intern/sfx/inventar.json (sfx_inventar.py; genutzt: bin, name, pfad_nas), dekodiert je Datei aus BINS (pfad_nas, nur lesend)
auf 48 kHz Stereo und misst:
  Dauer, Sample-Peak, True Peak (4×), Lautheit (BS.1770: integriert, max. momentan 400 ms),
  Hüllkurve (RMS 10 ms, Hop 5 ms): Stille am Anfang, Onset (−30 dB unter Maximum), Zeit bis −10/−3 dB, Peak-Zeitpunkt,
  Ausklang (−40 dB), Spektralschwerpunkt/Rolloff/Flachheit (Rauschen ↔ Ton), Bandanteile, Transienten, Stereo-Korrelation.
Nicht gemessen: alle Bins außerhalb von BINS — Kategorien, die der User ausschließt (z. B. Logo-Jingles, Drones, Glitch), nicht eintragen.
Schreibt _intern/sfx/analyse/sfx_metriken.json — Liste je Datei: bin, name, pfad_nas, codec, sr, kanaele, dauer_s, samples, peak_dbfs,
  true_peak_dbtp, lufs_integriert, lufs_momentan_max, huelle_max_db, t_peak_s, t_onset_s, t_minus10_s, t_minus3_s, stille_anfang_s,
  t_ende_40db_s, t_ende_20db_s, profil_db (12 Abschnitte), schwerpunkt_hz, rolloff85_hz, rolloff15_hz, anteil_unter_150/_150_600/
  _600_2k4/_2k4_8k/_ueber_8k, flachheit, tonanteil, transienten, stereo_korrelation, crest_db; profil_db/transienten/stereo_korrelation
  fehlen bei sehr kurzen bzw. monophonen Dateien, bei Lesefehlern steht fehler statt der Messwerte.
Deutung (Messung 15.09.): Luft-Whooshes Flachheit ≈ 0,16–0,27 bei Tonanteil ≤ 0,05; Impacts 83–100 % der Energie unter 150 Hz;
  stammt der Peak von einem tieffrequenten Plopp (Crest ≈ 19 dB), ist die Datei unter der Peak-Grenze kaum hörbar (−26 dBFS ≈ −45 LUFS).
Weiter: sfx_spektren.py (Sichtprüfung der Kandidaten) → sfx_plan_bauen.py.
Herkunft: Taxodia-Charge, _intern/sfx/sfx_analyse.py
"""
from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.signal import lfilter, resample_poly

# ── ANPASSEN je Charge ─────────────────────────────
# Zu messende Bins (Feld „bin" in inventar.json, Wurzel „SFX"): nur Kategorien, die für das Sound-Design in Frage kommen.
BINS: tuple[str, ...] = (
    # "SFX/Whoosh/Fast",  # Bin-Pfad exakt wie in inventar.json (kein Präfix-Vergleich: Unterbins einzeln aufführen)
)
# ── Ende ANPASSEN ──────────────────────────────────

HIER = Path(__file__).resolve().parent
OUT = HIER / "analyse"
SR = 48000


def probe(pfad: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                        "stream=codec_name,sample_rate,channels,bits_per_sample:format=duration", "-of", "json", pfad],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    return {"codec": s.get("codec_name"), "sr": int(s.get("sample_rate", 0)), "kanaele": int(s.get("channels", 0)),
            "dauer_s": round(float(j["format"]["duration"]), 3)}


def lade(pfad: str) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", pfad, "-map", "0:a:0", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).astype(np.float64)


def k_filter(x: np.ndarray) -> np.ndarray:
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)


def lautheit(x: np.ndarray) -> tuple[float, float]:
    """(integriert LUFS mit Gating, max. momentan 400 ms LUFS)."""
    kx = k_filter(x)
    p = (kx ** 2).sum(axis=1)
    n, h = int(0.4 * SR), int(0.1 * SR)
    if len(p) < n:
        p = np.pad(p, (0, n - len(p)))
    cs = np.concatenate([[0.0], np.cumsum(p)])
    st = np.arange(0, len(p) - n + 1, h)
    l = -0.691 + 10 * np.log10((cs[st + n] - cs[st]) / n + 1e-12)
    mmax = float(l.max())
    g = l[l > -70]
    if not len(g):
        return float("-inf"), mmax
    rel = 10 * np.log10(np.mean(10 ** (g / 10))) - 10
    g = g[g > rel]
    return float(10 * np.log10(np.mean(10 ** (g / 10)))), mmax


def analyse(e: dict) -> dict:
    pfad = e["pfad_nas"]
    out = {"bin": e["bin"], "name": e["name"], "pfad_nas": pfad}
    try:
        out.update(probe(pfad))
        x = lade(pfad)
    except Exception as ex:  # noqa: BLE001
        out["fehler"] = str(ex)[:200]
        return out
    mono = x.mean(axis=1)
    out["samples"] = len(x)
    peak = float(np.abs(x).max())
    out["peak_dbfs"] = round(20 * np.log10(peak + 1e-12), 2)
    tp = float(np.abs(resample_poly(x, 4, 1, axis=0)).max())
    out["true_peak_dbtp"] = round(20 * np.log10(tp + 1e-12), 2)
    li, lm = lautheit(x)
    out["lufs_integriert"] = round(li, 2) if np.isfinite(li) else None
    out["lufs_momentan_max"] = round(lm, 2)
    # Hüllkurve
    win, hop = int(0.010 * SR), int(0.005 * SR)
    p = (x ** 2).mean(axis=1)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    st = np.arange(0, max(1, len(p) - win + 1), hop)
    rms = np.sqrt(np.maximum((cs[np.minimum(st + win, len(p))] - cs[st]) / win, 0))
    env = 20 * np.log10(rms + 1e-12)
    t = (st + win / 2) / SR
    emax = float(env.max())
    i_pk = int(env.argmax())
    out["huelle_max_db"] = round(emax, 2)
    out["t_peak_s"] = round(float(t[i_pk]), 3)
    schwelle_on = max(emax - 30, -75)
    on = np.nonzero(env > schwelle_on)[0]
    i_on = int(on[0]) if len(on) else 0
    out["t_onset_s"] = round(float(t[i_on]), 3)
    out["t_minus10_s"] = round(float(t[np.nonzero(env >= emax - 10)[0][0]]), 3)
    out["t_minus3_s"] = round(float(t[np.nonzero(env >= emax - 3)[0][0]]), 3)
    thr_abs = 10 ** (-60 / 20)
    nz = np.nonzero(np.abs(mono) > thr_abs)[0]
    out["stille_anfang_s"] = round(float(nz[0] / SR), 3) if len(nz) else None
    schwelle_end = max(emax - 40, -80)
    en = np.nonzero(env > schwelle_end)[0]
    i_end = int(en[-1]) if len(en) else len(env) - 1
    out["t_ende_40db_s"] = round(float(t[i_end]), 3)
    out["t_ende_20db_s"] = round(float(t[np.nonzero(env > emax - 20)[0][-1]]), 3)
    # Hüllkurven-Profil in 12 Abschnitten zwischen Onset und Ende (dB rel. Maximum) — Form (Swell, Hit, Flach)
    if i_end > i_on + 12:
        seg = np.array_split(env[i_on:i_end + 1], 12)
        out["profil_db"] = [round(float(s.max() - emax), 1) for s in seg]
    # Spektrum auf dem aktiven Bereich
    a0, a1 = int(t[i_on] * SR), int(t[i_end] * SR) + win
    seg = mono[a0:a1]
    nfft, h2 = 2048, 512
    if len(seg) < nfft:
        seg = np.pad(seg, (0, nfft - len(seg)))
    idx = np.arange(0, len(seg) - nfft + 1, h2)
    w = np.hanning(nfft)
    M = np.abs(np.fft.rfft(np.stack([seg[i:i + nfft] * w for i in idx]), axis=1))
    S = M ** 2
    f = np.fft.rfftfreq(nfft, 1 / SR)
    fe = S.sum(axis=1)
    wgt = fe / (fe.sum() + 1e-20)
    # Schwerpunkt auf dem Betragsspektrum (übliche Definition), energiegewichtet über die Frames
    cen = (M * f).sum(axis=1) / (M.sum(axis=1) + 1e-20)
    out["schwerpunkt_hz"] = int(round(float((cen * wgt).sum())))
    tot = S.sum(axis=0)
    cum = np.cumsum(tot) / (tot.sum() + 1e-20)
    out["rolloff85_hz"] = int(f[np.searchsorted(cum, 0.85)])
    out["rolloff15_hz"] = int(f[np.searchsorted(cum, 0.15)])
    band = lambda lo, hi: round(float(tot[(f >= lo) & (f < hi)].sum() / (tot.sum() + 1e-20)), 3)
    out["anteil_unter_150"] = band(0, 150)
    out["anteil_150_600"] = band(150, 600)
    out["anteil_600_2k4"] = band(600, 2400)
    out["anteil_2k4_8k"] = band(2400, 8000)
    out["anteil_ueber_8k"] = band(8000, SR / 2)
    # Flachheit nur 60 Hz–12 kHz (leere Bänder oberhalb der Bandgrenze von MP3/44,1 kHz verfälschen sonst): 1 = Rauschen, → 0 = Ton
    sel = (f >= 60) & (f <= 12000)
    Ss = S[:, sel] + 1e-14
    flat = np.exp(np.mean(np.log(Ss), axis=1)) / np.mean(Ss, axis=1)
    out["flachheit"] = round(float((flat * wgt).sum()), 3)
    # Tonanteil: Energie in schmalen Spitzen > 10 dB über dem median-geglätteten Spektrum (Glocken, Synth-Töne, Pfeifen)
    from scipy.ndimage import median_filter
    glatt = median_filter(Ss, size=(1, 31), mode="nearest")
    ton = (Ss * (Ss > 10 * glatt)).sum(axis=1) / Ss.sum(axis=1)
    out["tonanteil"] = round(float((ton * wgt).sum()), 3)
    # Transienten: positive spektrale Flussspitzen > 6 dB über Median
    flux = np.maximum(np.diff(np.log10(S + 1e-12), axis=0), 0).sum(axis=1)
    if len(flux) > 3:
        thr = np.median(flux) + 3 * (np.std(flux) + 1e-9)
        peaks = [i for i in range(1, len(flux) - 1) if flux[i] > thr and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
        out["transienten"] = len(peaks)
    # Stereo
    l, r = x[a0:a1, 0], x[a0:a1, 1]
    if l.std() > 0 and r.std() > 0:
        out["stereo_korrelation"] = round(float(np.corrcoef(l, r)[0, 1]), 3)
    out["crest_db"] = round(out["peak_dbfs"] - 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12), 1)
    return out


def main() -> None:
    if not BINS:
        raise SystemExit("ANPASSEN-Block ausfüllen: BINS ist leer (zu messende Bins aus inventar.json) — nichts gemessen.")
    inv = json.loads((HIER / "inventar.json").read_text())
    kandidaten = [e for e in inv if e["bin"] in BINS]
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(analyse, kandidaten))
    OUT.mkdir(exist_ok=True)
    (OUT / "sfx_metriken.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    fehler = [r for r in res if "fehler" in r]
    print(f"{len(res)} Dateien gemessen, {len(fehler)} Fehler")
    for r in fehler:
        print("  FEHLER", r["name"], r["fehler"])


if __name__ == "__main__":
    main()
