"""Vorlage (Stand 15.09.2026): Prüfmischung Sprache + Musik + SFX offline nachbauen und messen — nur zum Messen, nichts in Resolve.

Aufruf: PYTHONDONTWRITEBYTECODE=1 tools/autocut/venv/bin/python _intern/sfx/sfx_mischung_pruefen.py
Stems wie _intern/musik/mischung_pruefen.py (dessen Funktionen werden importiert: fb, lade_audio, k_filter, integriert):
  Sprache A1 mit den in Resolve zurückgelesenen Normalisierungs-Gains (autocut/feinschnitt.json → normalisierung_a1_db, je A1-Clip in
  Timeline-Reihenfolge), Musik A2/A3 aus MUSIK_PLAN (Pegel + lineare Fades), dazu SFX A4/A5 aus sfx_plan.json (Clip-Gain + lineare
  Fades, Quelle pfad_nas, nur lesend).
Voice Isolation (nur in Resolve) fehlt in der Simulation.
Messungen (BS.1770, 48 kHz):
  - integrierte Lautheit Mischung mit/ohne SFX, Sprache, Musik; Lautheitsbeitrag der SFX (Ziel ≈ 0 LU); True Peak (4×), Übersteuerung
  - je Platzierung: SFX-Sample-Peak gesamt und während Sprache (Sprachmaske aus dem Sprach-Stem: Frame > −40 LUFS → SFX ≤ −26 dBFS),
    je Frame mit deutlicher Sprache (> −32 LUFS) SFX-Peak unter dem Sprach-Peak (Wortfugen dürfen die SFX tragen), Sprach-Peak im Fenster,
    lautestes 400-ms-Fenster der SFX (momentan) gegen die Mischung ohne SFX im selben Fenster, Musik-Kurzzeitpegel
  - Grenze „nie lauter als die Musik-Anhebungen": SFX momentan max < Musik momentan max in den Anhebungen (ANHEBUNGEN, z. B. Titel, Endcard)
Schreibt vorschau_mischung.wav (48 kHz / 24 Bit, vor der Abnahme anhören) und analyse/mischung_sfx.json: integriert_lufs {mischung_mit_sfx,
  mischung_ohne_sfx, sprache, musik}, sfx_lautheitsbeitrag_lu, sfx_energieanteil_db, true_peak_dbtp, sample_peak_dbfs, uebersteuerte_samples,
  sprachmaske, musik_anhebung_momentan_max_lufs, platzierungen (je SFX: Peaks, Sprachframes, Abstände, Momentanwerte), zusammenfassung,
  pruefung (Befunde oder ["ok"]).
Optional SFX_STEM_CACHE=<Ordner>: Sprach-/Musik-Stems dort zwischenspeichern (Wiederholungsläufe). Der Cache wird nicht erneuert —
nach Änderungen an Schnitt, Normalisierung oder MUSIK_PLAN den Ordner leeren.
Wird von sfx_plan_bauen.py importiert (stems, sprachmaske, fb).
Nachtrag (15.09.): Nach der Pegelanhebung auf hörbare Werte (siehe sfx_plan_bauen.py) meldete diese Prüfung 38 Befunde bei 39
Platzierungen — bei neuen Zielwerten die Grenzen hier bewusst mitziehen.
Herkunft: Taxodia-Charge, _intern/sfx/sfx_mischung_pruefen.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

# ── ANPASSEN je Charge ─────────────────────────────
# Musik-Anhebungen ohne Sprache als (Record-In, Record-Out) in Timeline-Frames ab 0 — Obergrenze „SFX nie lauter als die
# Musik-Anhebungen"; Werte aus den Anhebungs-Zeilen von feinschnitt_bauen.MUSIK_PLAN (mindestens eine, je ≥ 0,4 s lang).
ANHEBUNGEN: list[tuple[int, int]] = [
    # (340, 480),  # Titel: Anhebung auf A3 (Record-In, Record-Out der MUSIK_PLAN-Zeile, Frames)
]
# ── Ende ANPASSEN ──────────────────────────────────

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
SR, SPF, FPS = 48000, 1920, 25

spec = importlib.util.spec_from_file_location("mp", INTERN / "musik" / "mischung_pruefen.py")
mp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mp)
fb = mp.fb

GRENZE_UNTER_SPRACHE = -25.5   # Standard (15.09.): −26 dBFS + 0,5 dB Toleranz


def stems() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cache = os.environ.get("SFX_STEM_CACHE")
    if cache and (Path(cache) / "sprache.npy").exists():
        return (np.load(Path(cache) / "sprache.npy"), np.load(Path(cache) / "musik.npy"), np.load(Path(cache) / "aktiv.npy"))
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    if fehler:
        raise SystemExit("Feinschnitt-Plan fehlerhaft: " + "; ".join(fehler))
    gains = json.loads((INTERN / "autocut" / "feinschnitt.json").read_text())["normalisierung_a1_db"]
    a1 = sorted(p["A1"], key=lambda i: i.rec_in_f)
    if len(gains) != len(a1):
        raise SystemExit(f"{len(gains)} Gains für {len(a1)} A1-Clips")
    n = fb.ENDE * SPF
    sprache = np.zeros((n, 2), np.float32)
    musik = np.zeros((n, 2), np.float32)
    aktiv = np.zeros(fb.ENDE, bool)
    for it, g in zip(a1, gains):
        d = it.rec_out_f - it.rec_in_f
        x = mp.lade_audio(it.clip, it.src_in_f / FPS, d / FPS)[: d * SPF]
        sprache[it.rec_in_f * SPF: it.rec_in_f * SPF + len(x)] += x * 10 ** (g / 20)
        aktiv[it.rec_in_f: it.rec_out_f] = True
    for spur, datei, si, ri, ro, db, fi, fo in fb.MUSIK_PLAN:
        d = ro - ri
        x = mp.lade_audio(str(datei), si / FPS, d / FPS)[: d * SPF]
        h = np.ones(len(x), np.float32)
        if fi:
            h[: fi * SPF] = np.linspace(0, 1, fi * SPF, dtype=np.float32)
        if fo:
            h[-fo * SPF:] = np.minimum(h[-fo * SPF:], np.linspace(1, 0, fo * SPF, dtype=np.float32))
        musik[ri * SPF: ri * SPF + len(x)] += x * (10 ** (db / 20)) * h[:, None]
    if cache:
        Path(cache).mkdir(parents=True, exist_ok=True)
        np.save(Path(cache) / "sprache.npy", sprache)
        np.save(Path(cache) / "musik.npy", musik)
        np.save(Path(cache) / "aktiv.npy", aktiv)
    return sprache, musik, aktiv


SPRACH_SCHWELLE = -40.0  # Standard (15.09.): K-gewichtete Lautheit je Frame (40 ms); Raumton normalisierter Clips lag bei ca. −43 … −45
SPRACHE_DEUTLICH = -32.0  # Standard (15.09.): Frames mit deutlich hörbarer Sprache (Median der Wort-Frames −24): dort SFX-Peak < Sprach-Peak


def sprachmaske(sprache: np.ndarray, aktiv_items: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Je Timeline-Frame: Sprache hörbar (Frame-Lautheit > SPRACH_SCHWELLE und innerhalb eines A1-Clips); dazu die Frame-Lautheit."""
    ks = mp.k_filter(sprache)
    pw = (ks.astype(np.float64) ** 2).sum(axis=1)[: fb.ENDE * SPF].reshape(fb.ENDE, SPF).mean(axis=1)
    l_frame = -0.691 + 10 * np.log10(pw + 1e-12)
    return (l_frame > SPRACH_SCHWELLE) & aktiv_items, l_frame


def sfx_signal(pl: dict) -> np.ndarray:
    d = pl["dauer_frames"]
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{pl['src_in_s']:.4f}", "-i", pl["pfad_nas"], "-map", "0:a:0", "-ac", "2",
                        "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)[: d * SPF].astype(np.float64)
    if len(x) < d * SPF:
        x = np.pad(x, ((0, d * SPF - len(x)), (0, 0)))
    h = np.ones(len(x))
    if pl["fade_in_f"]:
        k = pl["fade_in_f"] * SPF
        h[:k] = np.linspace(0, 1, k)
    if pl["fade_out_f"]:
        k = pl["fade_out_f"] * SPF
        h[-k:] = np.minimum(h[-k:], np.linspace(1, 0, k))
    return (x * h[:, None] * 10 ** (pl["gain_db"] / 20)).astype(np.float32)


def momentan(kx: np.ndarray, hop_s: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    """400-ms-Momentanlautheit (LUFS) ab Sample 0 im Hop-Raster; Rückgabe (Fensterstart in Samples, LUFS)."""
    n, h = int(0.4 * SR), int(hop_s * SR)
    pw = (kx.astype(np.float64) ** 2).sum(axis=1)
    cs = np.concatenate([[0.0], np.cumsum(pw)])
    st = np.arange(0, max(1, len(pw) - n + 1), h)
    return st, -0.691 + 10 * np.log10((cs[st + n] - cs[st]) / n + 1e-12)


def db(v: float) -> float:
    return round(float(20 * np.log10(v + 1e-12)), 1)


def main() -> None:
    if not ANHEBUNGEN:
        raise SystemExit("ANPASSEN-Block ausfüllen: ANHEBUNGEN ist leer (Musik-Anhebungen in Record-Frames) — nichts gemessen.")
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    sprache, musik, aktiv_items = stems()
    bett = sprache + musik
    n = len(bett)
    sfx = np.zeros_like(bett)
    signale = []
    for pl in plan:
        x = sfx_signal(pl)
        a = pl["rec_frame"] * SPF
        sfx[a: a + len(x)] += x[: n - a]
        signale.append((pl, a, x))
    mix = bett + sfx

    # Vorschau-WAV (nur zum Messen/Anhören)
    ff = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le",
                         str(HIER / "vorschau_mischung.wav")], input=np.clip(mix, -1, 1).astype(np.float32).tobytes(), capture_output=True)
    if ff.returncode:
        raise SystemExit(ff.stderr.decode()[:500])

    ks, km, kb, kx, ksfx = (mp.k_filter(s) for s in (sprache, musik, bett, mix, sfx))
    out: dict = {"integriert_lufs": {"mischung_mit_sfx": mp.integriert(kx), "mischung_ohne_sfx": mp.integriert(kb),
                                     "sprache": mp.integriert(ks), "musik": mp.integriert(km)}}
    out["sfx_lautheitsbeitrag_lu"] = round(out["integriert_lufs"]["mischung_mit_sfx"] - out["integriert_lufs"]["mischung_ohne_sfx"], 2)
    e_sfx, e_mix = float((ksfx.astype(np.float64) ** 2).sum()), float((kx.astype(np.float64) ** 2).sum())
    out["sfx_energieanteil_db"] = round(10 * np.log10(e_sfx / e_mix), 1)
    tp = lambda s: round(float(20 * np.log10(np.abs(resample_poly(s, 4, 1, axis=0)).max() + 1e-12)), 2)
    out["true_peak_dbtp"] = {"mischung_mit_sfx": tp(mix), "mischung_ohne_sfx": tp(bett), "sfx_stem": tp(sfx)}
    out["sample_peak_dbfs"] = {"mischung_mit_sfx": db(np.abs(mix).max()), "sfx_stem": db(np.abs(sfx).max())}
    out["uebersteuerte_samples"] = int((np.abs(mix) >= 1.0).sum())

    # Sprachmaske je Frame: K-gewichtete Frame-Lautheit des Sprach-Stems über Schwelle und innerhalb eines A1-Clips
    sprache_an, l_frame = sprachmaske(sprache, aktiv_items)
    out["sprachmaske"] = {"schwelle_lufs_frame": SPRACH_SCHWELLE, "frames_aktiv": int(sprache_an.sum()),
                          "frame_lautheit_p10_p50_p90_in_clips": [round(float(np.percentile(l_frame[aktiv_items], q)), 1) for q in (10, 50, 90)]}

    st, m_bett = momentan(kb)
    _, m_musik = momentan(km)
    lift_max = max(float(m_musik[(st >= a * SPF) & (st + int(0.4 * SR) <= b * SPF)].max()) for a, b in ANHEBUNGEN)
    out["musik_anhebung_momentan_max_lufs"] = round(lift_max, 1)

    rows, fehler = [], []
    for pl, a, x in signale:
        d = pl["dauer_frames"]
        f0 = pl["rec_frame"]
        peak = db(np.abs(x).max())
        # Peak während Sprache (framegenau) und Frame-Vergleich SFX-Peak gegen Sprach-Peak im selben Frame
        maske = np.repeat(sprache_an[f0: f0 + d], SPF)[: len(x)]
        p_spr = db(np.abs(x[maske]).max()) if maske.any() else None
        sp_peak = db(np.abs(sprache[a: a + len(x)][maske]).max()) if maske.any() else None
        min_abstand = None
        for k in range(d):
            if f0 + k < fb.ENDE and sprache_an[f0 + k] and l_frame[f0 + k] > SPRACHE_DEUTLICH:
                sx = np.abs(x[k * SPF:(k + 1) * SPF]).max()
                sp = np.abs(sprache[(f0 + k) * SPF:(f0 + k + 1) * SPF]).max()
                if sx > 0:
                    v = float(20 * np.log10(sp + 1e-12) - 20 * np.log10(sx))
                    min_abstand = v if min_abstand is None else min(min_abstand, v)
        # lautestes 400-ms-Fenster der SFX (eigenes Signal, K-gewichtet)
        kxs = mp.k_filter(np.pad(x, ((int(0.2 * SR), int(0.2 * SR)), (0, 0))))
        s_loc, m_loc = momentan(kxs)
        i = int(m_loc.argmax())
        w0 = a - int(0.2 * SR) + int(s_loc[i])
        j = int(np.clip(round(w0 / (0.01 * SR)), 0, len(st) - 1))
        m_sfx = round(float(m_loc[i]), 1)
        m_bed = round(float(m_bett[j]), 1)
        m_mus = round(float(m_musik[j]), 1)
        zeile = {"element": pl["element"], "ereignis": pl["ereignis"], "spur": pl["spur"], "rec_frame": f0, "tc": fb.tc(f0),
                 "sfx": pl["sfx_name"], "gain_db": pl["gain_db"], "sfx_peak_dbfs": peak, "sfx_peak_waehrend_sprache_dbfs": p_spr,
                 "sprach_peak_im_fenster_dbfs": sp_peak, "sprachframes": int(sprache_an[f0: f0 + d].sum()),
                 "min_abstand_sprachpeak_minus_sfxpeak_je_frame_db": None if min_abstand is None else round(min_abstand, 1),
                 "sfx_momentan_max_lufs": m_sfx, "bett_momentan_lufs": m_bed, "musik_momentan_lufs": m_mus,
                 "abstand_bett_minus_sfx_lu": round(m_bed - m_sfx, 1)}
        if p_spr is not None and p_spr > GRENZE_UNTER_SPRACHE:
            fehler.append(f"{fb.tc(f0)} {pl['element']}: SFX-Peak während Sprache {p_spr} dBFS > −26")
        if min_abstand is not None and min_abstand < 0:
            fehler.append(f"{fb.tc(f0)} {pl['element']}: SFX-Peak in einem Sprach-Frame {-min_abstand:.1f} dB über dem Sprach-Peak")
        if m_sfx >= lift_max:
            fehler.append(f"{fb.tc(f0)} {pl['element']}: SFX momentan {m_sfx} LUFS ≥ Musik-Anhebung {lift_max:.1f}")
        rows.append(zeile)
    out["platzierungen"] = rows
    unter = [r for r in rows if r["sfx_peak_waehrend_sprache_dbfs"] is not None]
    frei = [r for r in rows if r["sfx_peak_waehrend_sprache_dbfs"] is None]
    out["zusammenfassung"] = {
        "platzierungen": len(rows),
        "mit_sprache_im_fenster": len(unter),
        "sfx_peak_waehrend_sprache_spanne_dbfs": [min(r["sfx_peak_waehrend_sprache_dbfs"] for r in unter),
                                                  max(r["sfx_peak_waehrend_sprache_dbfs"] for r in unter)] if unter else None,
        "min_abstand_sprachpeak_minus_sfxpeak_je_frame_db": min(r["min_abstand_sprachpeak_minus_sfxpeak_je_frame_db"] for r in unter
                                                               if r["min_abstand_sprachpeak_minus_sfxpeak_je_frame_db"] is not None) if unter else None,
        "median_abstand_sprachpeak_minus_sfxpeak_je_frame_db": float(np.median([r["min_abstand_sprachpeak_minus_sfxpeak_je_frame_db"] for r in unter
                                                                        if r["min_abstand_sprachpeak_minus_sfxpeak_je_frame_db"] is not None])) if unter else None,
        "sfx_peak_spanne_gesamt_dbfs": [min(r["sfx_peak_dbfs"] for r in rows), max(r["sfx_peak_dbfs"] for r in rows)],
        "sfx_momentan_max_lufs": max(r["sfx_momentan_max_lufs"] for r in rows),
        "abstand_bett_minus_sfx_lu_unter_sprache_median": float(np.median([r["abstand_bett_minus_sfx_lu"] for r in unter])) if unter else None,
        "abstand_bett_minus_sfx_lu_sprachfrei": {r["tc"] + " " + r["element"]: r["abstand_bett_minus_sfx_lu"] for r in frei},
    }
    out["pruefung"] = fehler or ["ok"]
    (HIER / "analyse").mkdir(exist_ok=True)
    (HIER / "analyse" / "mischung_sfx.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "platzierungen"}, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"{r['tc']} {r['spur']} {r['element'][:22]:22s} {r['sfx'][:30]:30s} pk {r['sfx_peak_dbfs']:6.1f} "
              f"pkS {str(r['sfx_peak_waehrend_sprache_dbfs']):>6s} minΔF {str(r['min_abstand_sprachpeak_minus_sfxpeak_je_frame_db']):>5s} "
              f"M {r['sfx_momentan_max_lufs']:6.1f} Bett {r['bett_momentan_lufs']:6.1f} Musik {r['musik_momentan_lufs']:6.1f} "
              f"Δ {r['abstand_bett_minus_sfx_lu']:5.1f}")


if __name__ == "__main__":
    main()
