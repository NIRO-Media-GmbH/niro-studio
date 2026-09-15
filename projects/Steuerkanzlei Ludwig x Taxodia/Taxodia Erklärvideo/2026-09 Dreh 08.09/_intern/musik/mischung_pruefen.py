"""Tonmischung des Feinschnitts offline nachbauen und messen (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/musik/mischung_pruefen.py
Baut aus dem Feinschnitt-Plan zwei Stems (Sprache A1 mit den in Resolve zurückgelesenen Normalisierungs-Gains,
Musik A2/A3 mit Pegel + linearen Fades) und misst nach BS.1770 (K-Filter, 48 kHz):
  - integrierte Lautheit Mischung/Sprache/Musik, True Peak (4× überabgetastet)
  - Abstand Sprache − Musik in 3-s-Fenstern, in denen gesprochen wird
  - Pegelsprünge an den Musikübergängen (Musik-Stem, 2 s vor Überblendung vs. 2 s danach, Einbruch in der Blende)
Voice Isolation (nur in Resolve) fehlt in der Simulation; sie ändert den Sprachpegel kaum, senkt aber Raumhall/Rauschen.
Schreibt _intern/musik/mischung.json.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import lfilter, resample_poly

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
SR, SPF = 48000, 1920  # Samples je Frame bei 25 fps

spec = importlib.util.spec_from_file_location("fb", INTERN / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def lade_audio(datei: str, start_s: float, dauer_s: float) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start_s:.4f}", "-t", f"{dauer_s:.4f}", "-i", datei, "-map", "0:a:0",
                        "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


def k_filter(x: np.ndarray) -> np.ndarray:
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    return lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)


def bloecke(kx: np.ndarray, fenster_s: float, hop_s: float) -> tuple[np.ndarray, np.ndarray]:
    """Lautheit (LUFS) gleitender Fenster auf K-gefiltertem Signal; Rückgabe (Fenstermitte in s, LUFS)."""
    n, h = int(fenster_s * SR), int(hop_s * SR)
    p = (kx ** 2).sum(axis=1)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, len(p) - n + 1, h)
    ms = (cs[starts + n] - cs[starts]) / n
    return (starts + n / 2) / SR, -0.691 + 10 * np.log10(ms + 1e-12)


def integriert(kx: np.ndarray) -> float:
    _, l = bloecke(kx, 0.4, 0.1)
    l = l[l > -70]
    if not len(l):
        return float("-inf")
    rel = 10 * np.log10(np.mean(10 ** (l / 10))) - 10
    l = l[l > rel]
    return round(float(10 * np.log10(np.mean(10 ** (l / 10)))), 1)


def main() -> None:
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    fs = json.loads((INTERN / "autocut" / "feinschnitt.json").read_text())
    gains = fs["normalisierung_a1_db"]
    a1 = sorted(p["A1"], key=lambda i: i.rec_in_f)
    if len(gains) != len(a1):
        raise SystemExit(f"{len(gains)} Gains für {len(a1)} A1-Clips — Readback passt nicht zum Plan.")
    n = fb.ENDE * SPF
    sprache = np.zeros((n, 2), np.float32)
    musik = np.zeros((n, 2), np.float32)
    aktiv = np.zeros(fb.ENDE, bool)
    for it, g in zip(a1, gains):
        d = it.rec_out_f - it.rec_in_f
        x = lade_audio(it.clip, it.src_in_f / 25, d / 25)[: d * SPF]
        sprache[it.rec_in_f * SPF: it.rec_in_f * SPF + len(x)] += x * 10 ** (g / 20)
        aktiv[it.rec_in_f: it.rec_out_f] = True
    for spur, datei, si, ri, ro, db, fi, fo in fb.MUSIK_PLAN:
        d = ro - ri
        x = lade_audio(str(datei), si / 25, d / 25)[: d * SPF]
        huelle = np.ones(len(x), np.float32)
        if fi:
            huelle[: fi * SPF] = np.linspace(0, 1, fi * SPF, dtype=np.float32)
        if fo:
            huelle[-fo * SPF:] = np.minimum(huelle[-fo * SPF:], np.linspace(1, 0, fo * SPF, dtype=np.float32))
        musik[ri * SPF: ri * SPF + len(x)] += x * (10 ** (db / 20)) * huelle[:, None]
    mix = sprache + musik
    ks, km, kmix = k_filter(sprache), k_filter(musik), k_filter(mix)
    tp = float(20 * np.log10(np.abs(resample_poly(mix, 4, 1, axis=0)).max() + 1e-12))
    out = {"integriert_lufs": {"mischung": integriert(kmix), "sprache": integriert(ks), "musik": integriert(km)},
           "true_peak_dbtp": round(tp, 1)}
    # Abstand Sprache − Musik in 3-s-Fenstern mit ≥ 80 % Sprache
    t, ls = bloecke(ks, 3.0, 0.5)
    _, lm = bloecke(km, 3.0, 0.5)
    anteil = np.array([aktiv[max(0, int((m - 1.5) * 25)): int((m + 1.5) * 25)].mean() for m in t])
    sel = (anteil >= 0.8) & (ls > -40)
    abst = ls[sel] - lm[sel]
    out["abstand_sprache_musik_lu"] = {"median": round(float(np.median(abst)), 1), "p10": round(float(np.percentile(abst, 10)), 1),
                                      "p90": round(float(np.percentile(abst, 90)), 1), "fenster": int(sel.sum())}
    knapp = [(fb.tc(int(m * 25)), round(float(a), 1)) for m, a in zip(t[sel], abst) if a < 10]
    out["abstand_unter_10_lu"] = knapp[:20]
    # Musik ohne Sprache (Titel, Vollbild-Grafiken, Endcard): Lautheit der Mischung
    t4, lmix = bloecke(kmix, 3.0, 0.5)
    frei = np.array([not aktiv[max(0, int((m - 1.5) * 25)): int((m + 1.5) * 25)].any() for m in t4])
    out["musik_allein_kurzzeit_lufs"] = [(fb.tc(int(m * 25)), round(float(v), 1)) for m, v in zip(t4[frei][::4], lmix[frei][::4])]
    # Übergänge: Musik-Stem momentan (400 ms), 2 s vor Blendenbeginn vs. 2 s nach Blendenende, tiefster Wert dazwischen
    tm, lmm = bloecke(km, 0.4, 0.05)
    starts = sorted({ri for _, _, _, ri, _, _, _, _ in fb.MUSIK_PLAN if ri > 200})
    uebergaenge = []
    for ri in starts:
        vorher = [e for e in fb.MUSIK_PLAN if e[3] < ri < e[4]]
        if not vorher:
            continue
        ende = min(e[4] for e in vorher)
        a_s, b_s = ri / 25, ende / 25
        vor = lmm[(tm > a_s - 2) & (tm < a_s)]
        nach = lmm[(tm > b_s) & (tm < b_s + 2)]
        mitte = lmm[(tm >= a_s) & (tm <= b_s)]
        uebergaenge.append({"tc": fb.tc(ri), "blende_f": ende - ri, "vor_lufs": round(float(np.median(vor)), 1),
                            "nach_lufs": round(float(np.median(nach)), 1), "sprung_lu": round(float(np.median(nach) - np.median(vor)), 1),
                            "einbruch_lu": round(float(mitte.min() - min(np.median(vor), np.median(nach))), 1) if len(mitte) else None})
    out["uebergaenge_musik"] = uebergaenge
    (HIER / "mischung.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
