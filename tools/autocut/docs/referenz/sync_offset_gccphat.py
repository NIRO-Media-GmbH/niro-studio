"""
sync_offset.py — Versatz zweier Kameraaufnahmen aus dem Ton bestimmen.
Nur numpy + scipy (+ ffmpeg zum Laden). Getestet: Python 3.12, numpy 2.5.2, scipy 1.18.1, macOS arm64.

Konvention (überall gleich):
    offset > 0  ⇔  b beginnt SPÄTER als a, d. h. b[t] ≈ a[t + offset].
    Liegt a in der Timeline bei T_a, dann liegt b bei T_a + offset.

Pipeline:
    1. Grob: Onset-Stärke (Spektralfluss in log-verteilten Bändern, halbwellen-
       gleichgerichtet, 10 ms Hop) → z-Score → FFT-Kreuzkorrelation über die volle Länge;
       nur Lags mit >= min_overlap_s Überlappung zählen (teilweise Überlappung, N:M).
    2. Konfidenz: PSR (Peak / größter Nebenpeak außerhalb ±1 s) und z-Score des Peaks.
    3. Fein: GCC-PHAT auf der Wellenform in n_fine sprach-aktiven Fenstern, verteilt über
       den Überlappungsbereich, jeweils ±fine_search_s um den Grobwert → sample-genau.
    4. Verifikation + Drift: lineare Regression Offset(t) über die Fenster;
       Steigung = Drift (ppm), Residuen-Spread = Konsistenz (muss < 1 Frame sein).
    5. Frame-Rundung auf fps (25).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, asdict, field

import numpy as np
from scipy import signal


# ----------------------------------------------------------------------------
# Laden
# ----------------------------------------------------------------------------
def load_audio(path: str, sr: int = 16000, start: float | None = None,
               duration: float | None = None) -> np.ndarray:
    """Mono-float32 bei `sr` per ffmpeg (MP4/MOV/WAV …). Downmix aller Kanäle."""
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", path]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


# ----------------------------------------------------------------------------
# Merkmal: Onset-Stärke (Spektralfluss in log-verteilten Bändern)
# ----------------------------------------------------------------------------
def onset_strength(x: np.ndarray, sr: int, hop: int = 160, n_fft: int = 512,
                   fmin: float = 100.0, fmax: float = 5000.0, n_bands: int = 40) -> np.ndarray:
    """Merkmalsfolge mit Rate sr/hop (Standard 16000/160 = 100 Hz).
    Nachbildung von librosa.onset.onset_strength ohne librosa:
    Band-Leistung → dB → zeitliche Differenz → halbwellen-gleichgerichtet → Summe."""
    x = np.asarray(x, dtype=np.float32)
    if len(x) < n_fft * 4:
        raise ValueError("Signal zu kurz")
    win = signal.windows.hann(n_fft, sym=False)
    sft = signal.ShortTimeFFT(win=win, hop=hop, fs=sr, mfft=n_fft, scale_to="magnitude")
    P = (np.abs(sft.stft(x)) ** 2).astype(np.float32)        # (bins, frames), Frames zentriert
    edges = np.geomspace(fmin, fmax, n_bands + 1)
    idx = np.unique(np.clip(np.searchsorted(sft.f, edges), 0, len(sft.f) - 1))
    band_db = 10.0 * np.log10(np.add.reduceat(P, idx[:-1], axis=0) + 1e-10)
    flux = np.diff(band_db, axis=1, prepend=band_db[:, :1])
    env = np.maximum(flux, 0.0).sum(axis=0)
    if len(env) > 101:                                        # langsame Pegeltrends raus
        env = env - signal.savgol_filter(env, 101, 1)
    env = (env - env.mean()) / (env.std() + 1e-9)
    return np.clip(env, -5, 5).astype(np.float32)             # Ausreißer kappen


# ----------------------------------------------------------------------------
# Grob: Kreuzkorrelation der Merkmale mit Überlappungs-Maske
# ----------------------------------------------------------------------------
def _overlap_counts(n_a: int, n_b: int, lags: np.ndarray) -> np.ndarray:
    """Anzahl n mit 0<=n<n_b und 0<=n+lag<n_a (überlappende Frames je Lag)."""
    return np.maximum(0, np.minimum(n_b, n_a - lags) - np.maximum(0, -lags))


def coarse_offset(fa: np.ndarray, fb: np.ndarray, feat_rate: float,
                  min_overlap_s: float = 15.0, exclude_s: float = 1.0,
                  max_abs_offset_s: float | None = None) -> dict:
    fa = fa - fa.mean()
    fb = fb - fb.mean()
    corr = signal.correlate(fa, fb, mode="full", method="fft")
    lags = signal.correlation_lags(len(fa), len(fb), mode="full")   # lag>0 ⇒ b später
    ov = _overlap_counts(len(fa), len(fb), lags)
    valid = ov >= int(min_overlap_s * feat_rate)
    if max_abs_offset_s is not None:
        valid &= np.abs(lags) <= int(max_abs_offset_s * feat_rate)
    if not valid.any():
        raise ValueError("Keine Lags mit ausreichender Überlappung")
    r = np.full(corr.shape, -np.inf)
    r[valid] = corr[valid] / ov[valid]           # ≈ Korrelationskoeffizient je Lag
    k = int(np.argmax(r))
    peak = float(r[k])
    excl = int(exclude_s * feat_rate)
    side = r.copy(); side[max(0, k - excl): k + excl + 1] = -np.inf
    side = side[np.isfinite(side)]
    second = float(side.max()) if side.size else 0.0
    rv = r[valid]
    return {
        "lag_s": float(lags[k] / feat_rate),
        "r": peak,
        "psr": peak / second if second > 0 else float("inf"),
        "z": float((peak - rv.mean()) / (rv.std() + 1e-12)),
        "overlap_s": float(ov[k] / feat_rate),
    }


# ----------------------------------------------------------------------------
# Fein: GCC-PHAT auf der Wellenform (Knapp & Carter 1976)
# ----------------------------------------------------------------------------
def gcc_phat(x: np.ndarray, y: np.ndarray, sr: int, max_tau: float,
             fmin: float = 150.0, fmax: float = 4000.0, beta: float = 1.0) -> tuple[float, float]:
    """tau mit y[t] ≈ x[t + tau] (tau>0 ⇒ y später), parabolisch interpoliert.
    Rückgabe (tau_s, peak_ratio = Peak / größter Nebenpeak)."""
    nfft = 1 << (len(x) + len(y) - 1).bit_length()
    X = np.fft.rfft(x, nfft); Y = np.fft.rfft(y, nfft)
    G = X * np.conj(Y)
    w = np.abs(G) ** beta
    G = G / np.maximum(w, 1e-3 * w.max())                       # PHAT (mit Regularisierung)
    f = np.fft.rfftfreq(nfft, 1 / sr)
    G[(f < fmin) | (f > fmax)] = 0.0
    cc = np.fft.irfft(G, nfft)
    m = int(max_tau * sr)
    cc = np.concatenate((cc[-m:], cc[: m + 1]))                 # Lags −m … +m
    k = int(np.argmax(np.abs(cc)))
    frac = 0.0
    if 0 < k < len(cc) - 1:
        a_, b_, c_ = cc[k - 1], cc[k], cc[k + 1]
        d = a_ - 2 * b_ + c_
        frac = 0.5 * (a_ - c_) / d if abs(d) > 1e-12 else 0.0
    rest = np.abs(cc).copy(); rest[max(0, k - int(0.002 * sr)): k + int(0.002 * sr) + 1] = 0
    return float((k + frac - m) / sr), float(abs(cc[k]) / (rest.max() + 1e-12))


def _spread_windows(a: np.ndarray, sr: int, t0: float, t1: float, win_s: float,
                    n_win: int) -> list[float]:
    """Je Segment des Bereichs [t0,t1) das energiereichste Fenster (Startzeit in a)."""
    n_win = max(1, min(n_win, int((t1 - t0) // win_s)))   # kurze Überlappung: weniger Fenster
    seg = (t1 - t0) / n_win
    out = []
    for i in range(n_win):
        s0, s1 = t0 + i * seg, t0 + (i + 1) * seg - win_s
        if s1 <= s0:
            continue
        starts = np.arange(s0, s1, win_s / 2)
        rms = [np.sqrt(np.mean(a[int(s * sr): int((s + win_s) * sr)] ** 2)) for s in starts]
        out.append(float(starts[int(np.argmax(rms))]))
    return out


# ----------------------------------------------------------------------------
# Hauptfunktion
# ----------------------------------------------------------------------------
@dataclass
class SyncResult:
    offset_s: float            # feiner Offset, gültig für die MITTE des Überlappungsbereichs
    offset_start_s: float      # Offset am ANFANG der Überlappung (→ Clip-Position in der Timeline)
    offset_end_s: float        # Offset am ENDE der Überlappung (Differenz = Drift-Wirkung)
    offset_frames: int         # offset_start_s gerundet auf fps
    residual_ms: float         # Rest nach Frame-Rundung
    coarse_offset_s: float
    coarse_r: float            # ≈ Korrelationskoeffizient des Merkmals-Peaks
    coarse_psr: float          # Peak / größter Nebenpeak (falsch ≈ 1.0–1.2; richtig ≥ ~2)
    coarse_z: float            # z-Score des Peaks (falsch ≈ 7–8; richtig ≥ ~20)
    overlap_s: float
    fine_offsets_s: list = field(default_factory=list)
    fine_ratios: list = field(default_factory=list)
    fine_spread_ms: float = float("nan")   # Residuen-Spread der Fein-Fenster (Konsistenz)
    drift_ppm: float | None = None         # Uhr von b relativ zu a; >0 ⇒ b-Uhr läuft langsamer
    overlap_t0_s: float = 0.0    # Überlappung [t0, t1] in a-Zeit
    overlap_t1_s: float = 0.0
    ok: bool = False
    reason: str = ""

    def offset_at(self, t_a: float) -> float:
        """Driftkorrigierter Offset für a-Zeit t_a (für jedes Schnittsegment einzeln nutzen)."""
        if self.drift_ppm is None or (self.overlap_t1_s - self.overlap_t0_s) <= 0:
            return self.offset_s
        t_mid = (self.overlap_t0_s + self.overlap_t1_s) / 2
        return self.offset_s + self.drift_ppm * 1e-6 * (t_a - t_mid)


def offset_seconds(a: np.ndarray, b: np.ndarray, sr: int, fps: float = 25.0,
                   hop: int = 160, min_overlap_s: float = 15.0,
                   fine_win_s: float = 6.0, n_fine: int = 6, fine_search_s: float = 0.25,
                   fine_ratio_min: float = 1.3,
                   psr_min: float = 1.8, z_min: float = 12.0,
                   max_abs_offset_s: float | None = None) -> SyncResult:
    """a = Referenz (FX3/Lavalier), b = zweite Kamera (a7IV). Beide mono float bei sr."""
    feat_rate = sr / hop
    co = coarse_offset(onset_strength(a, sr, hop=hop), onset_strength(b, sr, hop=hop),
                       feat_rate, min_overlap_s=min_overlap_s, max_abs_offset_s=max_abs_offset_s)
    off0 = co["lag_s"]
    ok = co["psr"] >= psr_min and co["z"] >= z_min
    reason = "" if ok else f"Grobkorrelation schwach (psr={co['psr']:.2f}, z={co['z']:.1f})"

    t0 = max(0.0, off0)                          # Überlappung in a-Zeit
    t1 = min(len(a) / sr, off0 + len(b) / sr)
    fine, centers, ratios = [], [], []
    if co["z"] >= 0.5 * z_min and t1 - t0 > fine_win_s + 1.0:
        for s in _spread_windows(a, sr, t0 + 0.5, t1 - 0.5, fine_win_s, n_fine):
            ia0 = int(s * sr); ia1 = ia0 + int(fine_win_s * sr)
            ib0 = int((s - off0 - fine_search_s) * sr)
            ib1 = ib0 + int((fine_win_s + 2 * fine_search_s) * sr)
            if ib0 < 0 or ib1 > len(b) or ia1 > len(a):
                continue
            xa = a[ia0:ia1].astype(np.float64); xa -= xa.mean()
            xb = b[ib0:ib1].astype(np.float64); xb -= xb.mean()
            tau, ratio = gcc_phat(xa, xb, sr, max_tau=2 * fine_search_s)
            # xb startet bei b-Zeit (s − off0 − search); xb[t] ≈ xa[t + tau]
            # ⇒ a-Zeit s + t + tau ↔ b-Zeit (s − off0 − search) + t ⇒ offset = off0 + search + tau
            if ratio >= fine_ratio_min:
                fine.append(off0 + fine_search_s + tau); centers.append(s + fine_win_s / 2); ratios.append(ratio)

    drift = None; spread = float("nan")
    off_mid = off_start = off_end = off0
    if len(fine) >= 2:
        c = np.array(centers); o = np.array(fine)
        if c.max() - c.min() >= 120.0:            # Drift nur bei ausreichender Spanne schätzen
            p = np.polyfit(c, o, 1)
            drift = float(p[0] * 1e6)
            resid = o - np.polyval(p, c)
            spread = float((resid.max() - resid.min()) * 1000)
            off_mid, off_start, off_end = (float(np.polyval(p, t)) for t in ((t0 + t1) / 2, t0, t1))
        else:
            spread = float((o.max() - o.min()) * 1000)
            off_mid = off_start = off_end = float(np.median(o))
        if spread > 1000.0 / fps:
            ok = False; reason = f"Fein-Fenster inkonsistent (Spread {spread:.1f} ms)"
    elif len(fine) == 1:
        off_mid = off_start = off_end = fine[0]
    elif ok:
        ok = False; reason = "keine Fein-Fenster auswertbar"

    frames = int(np.rint(off_start * fps))
    return SyncResult(
        offset_s=off_mid, offset_start_s=off_start, offset_end_s=off_end,
        offset_frames=frames, residual_ms=(off_start - frames / fps) * 1000,
        coarse_offset_s=off0, coarse_r=co["r"], coarse_psr=co["psr"], coarse_z=co["z"],
        overlap_s=co["overlap_s"], fine_offsets_s=[float(v) for v in fine], fine_ratios=ratios,
        fine_spread_ms=spread, drift_ppm=drift, overlap_t0_s=t0, overlap_t1_s=t1,
        ok=ok, reason=reason,
    )


# ----------------------------------------------------------------------------
# N:M-Zuordnung
# ----------------------------------------------------------------------------
def match_files(ref_paths: list[str], sec_paths: list[str], sr: int = 16000, **kw) -> list[dict]:
    """Alle Paare (Referenz × Zweitkamera) prüfen; nur Paare mit ok=True zurückgeben.
    Merkmale werden je Datei einmal berechnet (Grobstufe ist billig, Laden dominiert)."""
    refs = {p: load_audio(p, sr) for p in ref_paths}
    secs = {p: load_audio(p, sr) for p in sec_paths}
    out = []
    for rp, ra in refs.items():
        for sp, sa in secs.items():
            try:
                res = offset_seconds(ra, sa, sr, **kw)
            except ValueError:
                continue
            if res.ok:
                out.append({"ref": rp, "sec": sp, **asdict(res)})
    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(asdict(offset_seconds(load_audio(sys.argv[1]), load_audio(sys.argv[2]), 16000)), indent=2))
