"""Waveform-Sync zweier Kameras: Onset-Hüllkurven + FFT-Kreuzkorrelation.

Konvention (Plan „Global Constraints“): ``other_time = ref_time + offset_s`` — ein positiver Versatz
heißt, die Kontext-Kamera (a7) lief schon, als die Ton-Kamera (FX3) startete; die a7-Position eines
FX3-Schnitts ist FX3-Position + offset.

Vorzeichen (empirisch gegen scipy festgenagelt, siehe tests/test_sync.py):
``correlate(ref, other)`` liefert bei ``lags[argmax]`` den Lag, um den ``other`` gegenüber ``ref``
verschoben ist; hat ``other`` Vorlauf, ist der Lag negativ → ``offset_s = -lag / fs``.
Ein Prüffenster, das bei ref-Sekunde ``a`` beginnt, liefert ``offset_fenster = offset + a``;
der Fensterstart wird deshalb ABGEZOGEN (der Prototyp hatte hier das Vorzeichen falsch).

Gearbeitet wird auf 16-kHz-Mono-WAVs der Originale (``media.extract_audio_16k``), nie auf dem NAS
geschrieben. Ergebnisse landen in ``<Charge>/_intern/autocut/sync.json``.
"""
from __future__ import annotations

import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate, correlation_lags

from .charge import AutoCutError
from .media import extract_audio_16k, seconds_to_frames

MIN_OVERLAP_S = 5.0          # darunter gilt ein Paar als „keine Überlappung“
MIN_WINDOW_S = 5.0           # Mindestlänge je Prüffenster (zwei disjunkte Fenster nötig, Spec 3.2)
MIN_ENVELOPE_POINTS = 10     # Hüllkurve muss mindestens so viele Stützstellen haben
WINDOW_TOL_FRAMES = 1.0      # Prüffenster müssen den Gesamtversatz auf ±1 Frame bestätigen


# --- WAV -----------------------------------------------------------------

def read_wav_mono(path: str | Path) -> tuple[np.ndarray, int]:
    """WAV als float32-Mono in [-1, 1] lesen (int16/int32/uint8/float; Stereo wird gemittelt)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Sync-WAV nicht gefunden: {p}")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", wavfile.WavFileWarning)   # LIST-Chunks von ffmpeg
        sr, x = wavfile.read(str(p))
    # Erst nach dtype normieren, dann Kanäle mitteln — nach dem Mitteln wäre der dtype float und die
    # Ganzzahl-Skalierung ginge verloren (Stereo-int16 bliebe im Bereich ±32767).
    if x.dtype == np.int16:
        y = x.astype(np.float32) / 32768.0
    elif x.dtype == np.int32:
        y = (x.astype(np.float64) / 2147483648.0).astype(np.float32)
    elif x.dtype == np.uint8:
        y = ((x.astype(np.float32) - 128.0) / 128.0).astype(np.float32)
    else:
        y = x.astype(np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1).astype(np.float32)
    return y, int(sr)


# --- Hüllkurve -----------------------------------------------------------

def onset_envelope(x: np.ndarray, sr: int, hop_s: float = 0.005, win_s: float = 0.02) -> tuple[np.ndarray, float]:
    """Onset-Hüllkurve: Kurzzeit-Energie in dB (Fenster win_s, Hop hop_s), Median-zentriert,
    halbwellen-gleichgerichtete 1. Ableitung, mittelwertfrei. Liefert (Hüllkurve, Abtastrate der Hüllkurve).

    Lavalier- und Kameramikro klingen verschieden, setzen aber an denselben Stellen ein — deshalb
    korrelieren wir Einsätze, nicht Rohsignale. Energie über Kumulativsumme (kein n×w-Zwischenspeicher).
    """
    h = max(1, int(round(sr * hop_s)))
    w = max(h, int(round(sr * win_s)))
    n = (len(x) - w) // h
    if n <= MIN_ENVELOPE_POINTS:
        raise AutoCutError(f"Audio zu kurz für den Sync ({len(x) / sr:.2f} s bei {sr} Hz).")
    sq = np.concatenate(([0.0], np.cumsum(x.astype(np.float64) ** 2)))
    starts = h * np.arange(n)
    e = np.sqrt((sq[starts + w] - sq[starts]) / w + 1e-10)
    db = 20.0 * np.log10(e + 1e-6)
    db = db - np.median(db)
    on = np.maximum(np.diff(db, prepend=db[0]), 0.0)
    on = on - on.mean()
    return on.astype(np.float32), float(sr) / h


# --- Kreuzkorrelation ------------------------------------------------------

def estimate_offset(ref_env: np.ndarray, other_env: np.ndarray, fs: float,
                    exclusion_s: float = 1.0) -> tuple[float, float]:
    """Versatz (Sekunden, Konvention other = ref + offset) und Konfidenz = Hauptpeak / zweitgrößter Peak
    außerhalb ±exclusion_s um den Hauptpeak."""
    if len(ref_env) < 2 or len(other_env) < 2:
        raise AutoCutError("Hüllkurve zu kurz für die Kreuzkorrelation.")
    c = correlate(ref_env, other_env, mode="full", method="fft")
    lags = correlation_lags(len(ref_env), len(other_env), mode="full")
    k = int(np.argmax(c))
    peak = float(c[k])
    excl = max(1, int(round(fs * exclusion_s)))
    c2 = c.copy()
    c2[max(0, k - excl):k + excl + 1] = -np.inf
    finite = np.isfinite(c2)
    second = float(c2[finite].max()) if finite.any() else 0.0
    if peak <= 0.0:
        conf = 0.0
    else:
        conf = peak / max(second, peak * 1e-6, 1e-9)   # Konfidenz ist damit nach oben auf 1e6 begrenzt
    return float(-lags[k] / fs), float(conf)


def window_offset(ref_env: np.ndarray, other_env: np.ndarray, fs: float, start_s: float, end_s: float,
                  exclusion_s: float = 1.0) -> tuple[float, float]:
    """Versatz nur aus dem ref-Fenster [start_s, end_s) gegen die ganze other-Hüllkurve, bereits um den
    Fensterstart korrigiert — also direkt mit ``estimate_offset`` auf dem Gesamtsignal vergleichbar."""
    i0 = max(0, int(round(start_s * fs)))
    i1 = min(len(ref_env), int(round(end_s * fs)))
    if i1 - i0 < MIN_ENVELOPE_POINTS:
        raise AutoCutError(f"Prüffenster {start_s:.1f}–{end_s:.1f} s zu kurz.")
    seg = ref_env[i0:i1]
    seg = seg - seg.mean()
    o_w, c_w = estimate_offset(seg, other_env, fs, exclusion_s)
    return o_w - i0 / fs, c_w


# --- Paar ------------------------------------------------------------------

@dataclass
class PairSync:
    """Sync-Ergebnis eines Kamerapaars. ``overlap_ref`` = gemeinsamer Bereich in ref-Sekunden [a, b]."""
    ref: str
    other: str
    offset_s: float
    offset_frames: int
    confidence: float
    overlap_ref: list[float]
    drift_frames: float
    ok: bool
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PairSync":
        return cls(ref=d["ref"], other=d["other"], offset_s=float(d["offset_s"]),
                   offset_frames=int(d["offset_frames"]), confidence=float(d["confidence"]),
                   overlap_ref=[float(v) for v in d["overlap_ref"]], drift_frames=float(d.get("drift_frames", 0.0)),
                   ok=bool(d["ok"]), note=str(d.get("note", "")))


def sync_pair(ref_wav: str | Path, other_wav: str | Path, fps: float, cfg: dict) -> PairSync:
    """Versatz zweier WAVs bestimmen und mit zwei disjunkten Prüffenstern absichern (Spec 3.2).

    ok nur, wenn Konfidenz ≥ min_confidence, Überlappung ≥ 5 s, beide Fensterhälften den Versatz auf
    ±1 Frame bestätigen und der Drift zwischen den Fenstern ≤ max_drift_frames bleibt.
    """
    ref, sr = read_wav_mono(ref_wav)
    oth, sr2 = read_wav_mono(other_wav)
    if sr != sr2:
        raise AutoCutError(f"Abtastraten der Sync-WAVs unterscheiden sich ({sr} / {sr2} Hz): "
                           f"{Path(ref_wav).name} × {Path(other_wav).name}")
    hop, win, excl = float(cfg["hop_s"]), float(cfg["win_s"]), float(cfg["exclusion_s"])
    min_conf, max_drift = float(cfg["min_confidence"]), float(cfg["max_drift_frames"])
    e_ref, fs = onset_envelope(ref, sr, hop, win)
    e_oth, _ = onset_envelope(oth, sr, hop, win)
    off, conf = estimate_offset(e_ref, e_oth, fs, excl)
    ref_dur, oth_dur = len(ref) / sr, len(oth) / sr
    ov0, ov1 = max(0.0, -off), min(ref_dur, oth_dur - off)
    overlap = ov1 - ov0
    drift = 0.0
    note = ""
    ok = True
    if overlap < MIN_OVERLAP_S:
        ok, note = False, "keine Überlappung"
    elif conf < min_conf:
        ok, note = False, f"Konfidenz {conf:.1f} unter {min_conf:g}"
    elif overlap < 2 * MIN_WINDOW_S:
        ok, note = False, f"Überlappung {overlap:.1f} s zu kurz für zwei Prüffenster"
    else:
        mid = (ov0 + ov1) / 2.0
        ests: list[float] = []
        for a, b in ((ov0, mid), (mid, ov1)):
            o_w, _ = window_offset(e_ref, e_oth, fs, a, b, excl)
            ests.append(o_w)
        drift = (ests[1] - ests[0]) * fps
        if any(abs(e - off) * fps > WINDOW_TOL_FRAMES for e in ests):
            ok, note = False, (f"Prüffenster uneinig ({ests[0]:+.3f} s / {ests[1]:+.3f} s "
                               f"gegen {off:+.3f} s gesamt)")
        elif abs(drift) > max_drift:
            ok, note = False, f"Drift {drift:+.2f} Frames über {max_drift:g}"
    return PairSync(ref=str(ref_wav), other=str(other_wav), offset_s=round(off, 4),
                    offset_frames=seconds_to_frames(off, fps), confidence=round(conf, 2),
                    overlap_ref=[round(ov0, 2), round(ov1, 2)], drift_frames=round(drift, 2) + 0.0,   # kein „-0.0“
                    ok=ok, note=note)


# --- Charge ----------------------------------------------------------------

def _ordner_of(path: str) -> str:
    return Path(path).parent.name


def sync_charge(charge, media: dict, nur_ordner: list[str] | None = None) -> dict:
    """Alle FX3×a7-Paare je Interview-Ordner rechnen; WAVs der ORIGINALE unter _intern/autocut/work/audio.

    Schreibt ``sync.json`` als ``{"fps": …, "paare": [PairSync…]}`` (ref/other = Original-Pfade).
    Mit ``nur_ordner`` werden nur diese Ordner gerechnet und die übrigen Paare einer vorhandenen
    sync.json übernommen. Ein Paar, dessen Audio nicht lesbar oder zu kurz ist, wird als ok=False mit
    Begründung eingetragen statt den ganzen Lauf abzubrechen.
    """
    fps = float(media["format"]["fps"])
    cfg = charge.config["sync"]
    audio_dir = charge.work / "audio"
    ordner_alle = media.get("ordner", {})
    if nur_ordner:
        fehlend = [o for o in nur_ordner if o not in ordner_alle]
        if fehlend:
            raise AutoCutError("Interview-Ordner nicht in media.json: " + ", ".join(fehlend)
                               + "\nVorhanden: " + ", ".join(sorted(ordner_alle)))
    paare: list[dict] = []
    for ordner, grp in ordner_alle.items():
        if nur_ordner and ordner not in nur_ordner:
            continue
        for ref_path in grp.get("ton", []):
            try:
                ref_wav: Path | None = extract_audio_16k(ref_path, audio_dir, int(cfg["sr"]))
                ref_err = ""
            except AutoCutError as e:
                ref_wav, ref_err = None, str(e)
            for oth_path in grp.get("kontext", []):
                try:
                    if ref_wav is None:
                        raise AutoCutError(ref_err)
                    oth_wav = extract_audio_16k(oth_path, audio_dir, int(cfg["sr"]))
                    p = sync_pair(ref_wav, oth_wav, fps, cfg)
                except AutoCutError as e:
                    p = PairSync(ref=ref_path, other=oth_path, offset_s=0.0, offset_frames=0, confidence=0.0,
                                 overlap_ref=[0.0, 0.0], drift_frames=0.0, ok=False, note=str(e).splitlines()[0])
                p.ref, p.other = ref_path, oth_path
                paare.append(p.to_dict())
                print(f"[{ordner}] {Path(ref_path).name} × {Path(oth_path).name}: "
                      f"{p.offset_frames:+d} Frames ({p.offset_s:+.3f} s), Konf {p.confidence}, "
                      f"Drift {p.drift_frames:+.2f}, ok={p.ok}{(' — ' + p.note) if p.note else ''}")
    if nur_ordner:
        alt = charge.read_json("sync.json") or {}
        behalten = [p for p in alt.get("paare", []) if _ordner_of(p["ref"]) not in nur_ordner]
        paare = behalten + paare
    out = {"fps": fps, "paare": paare}
    charge.write_json("sync.json", out)
    return out


def a7_for_cut(sync: dict, ref_clip: str, in_s: float, out_s: float) -> dict | None:
    """Das ok-Paar zu ref_clip, dessen Überlappung [in_s, out_s] voll abdeckt — bei mehreren das mit der
    höchsten Konfidenz; None, wenn keins passt."""
    cands = [p for p in sync.get("paare", []) if p["ref"] == ref_clip and p["ok"]
             and p["overlap_ref"][0] <= in_s and out_s <= p["overlap_ref"][1]]
    return max(cands, key=lambda p: p["confidence"]) if cands else None
