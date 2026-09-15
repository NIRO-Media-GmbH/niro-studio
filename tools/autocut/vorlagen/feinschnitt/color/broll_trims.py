"""Vorlage (Stand 15.09.2026): Belichtungs-Trim je B-Roll-Einsatz im Feinschnitt berechnen (nur lesen, nichts in Resolve).

Aufruf: tools/autocut/venv/bin/python _intern/color/broll_trims.py
Je V3-Item 3 Proxy-Frames aus dem tatsächlich genutzten Quellbereich (20/50/80 %) → Basis-Grade B-Roll (CDL + Sony LC-709)
→ Median-L* des Bildes. Ziel = Median aller Shots; Trim = halber Weg dorthin (Raster 0,05 Blenden), höchstens ±MAX_TRIM
Blenden (Analyse: „pro Shot ±0,3–0,5 Blende nachtrimmen").
Eingaben: _intern/color/grading_vorschlag.json (b_roll_FX3A → node1_gesamt_log_vor_LUT), Feinschnitt-Plan aus
_intern/feinschnitt_bauen.py (Modul fb: lade, plan → V3 + v3_meta, FPS, tc), Proxys <Ordner des Originals>/Proxy/<Clip>.mov
(fehlt der Proxy, wird das Original gelesen).
Ergebnis: _intern/color/broll_trims.json (Schlüssel = Timeline-Start des Einsatzes in Frames → shot, clip, blenden,
median_L_basis, median_L_trim) + kontaktbogen_BRoll_trims.jpg (je Einsatz links Basis, rechts mit Trim).
grading_anwenden.py addiert den Trim vor der CDL als Offset (Offset += Blenden · STOP · Slope), nur auf V3-Items, deren Start
einem Schlüssel entspricht. Deshalb nach dem letzten Umbau rechnen und nach Hand-Änderungen an V3 neu rechnen.
Herkunft: Taxodia-Charge, _intern/color/broll_trims.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

# ── ANPASSEN je Charge ─────────────────────────────
MAX_TRIM = 0.5  # größter Trim je Einsatz in Blenden (±) — Standard (15.09.)
QUELL_FPS_BROLL = 50  # Bildrate der B-Roll-Quelldateien in fps (Timeline = fb.FPS; „langsam" in fb.BROLL = 50 %) — Standard (15.09.)
LUT_DATEI = "SLog3SGamut3.CineToLC-709.cube"  # Sony-LUT in CL.LUTDIR, derselbe wie grading_anwenden.LUT_REL — Standard (15.09.)
# ── Ende ANPASSEN ──────────────────────────────────

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER / "skripte"))
import colorlib as CL  # noqa: E402

spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
W, H = 480, 270


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def frame_log(pfad: str, t: float) -> np.ndarray:
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", proxy(pfad), "-frames:v", "1", "-an",
                        "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "yuv444p", "-"],
                       capture_output=True, check=True).stdout
    return CL.yuv_to_rgb(np.frombuffer(b, np.uint8).reshape(3, H, W)).astype(np.float32)


def grade(x: np.ndarray, w: dict, blenden: float = 0.0) -> np.ndarray:
    off = [o + blenden * CL.STOP * s for o, s in zip(w["offset"], w["slope"])]
    return CL.apply_lut(CL.cdl(x, w["slope"], off, (1, 1, 1), w["saturation"]), LUT)


def median_l(bilder: list[np.ndarray], w: dict, blenden: float = 0.0) -> float:
    return float(np.median(np.concatenate([CL.disp_to_lab(grade(b, w, blenden))[..., 0].ravel() for b in bilder])))


LUT = CL.load_cube(CL.LUTDIR + LUT_DATEI)


def main() -> None:
    vorschlag = json.loads((HIER / "grading_vorschlag.json").read_text())
    w = vorschlag["b_roll_FX3A"]["node1_gesamt_log_vor_LUT"]
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    if fehler:
        raise SystemExit(f"Plan fehlerhaft: {fehler}")
    einsaetze = sorted(zip(p["v3_meta"], sorted(p["V3"], key=lambda i: i.rec_in_f)), key=lambda z: z[0]["rec_in_f"])

    def proben(z):
        m, it = z
        # Quellframes im genutzten Bereich (Standard 50p in 25p: 100 % = 2, „langsam" 50 % = 1 Quellbild je Timeline-Frame)
        quelle_n = m["dauer_f"] * QUELL_FPS_BROLL / fb.FPS * (0.5 if m["langsam"] else 1.0)
        return [frame_log(it.clip, (it.src_in_f + q * quelle_n) / QUELL_FPS_BROLL) for q in (0.2, 0.5, 0.8)]

    with ThreadPoolExecutor(6) as ex:
        bilder = list(ex.map(proben, einsaetze))
    basis = [median_l(b, w) for b in bilder]
    ziel = float(np.median(basis))
    raster = np.round(np.arange(-1.5, 1.51, 0.05), 2)
    trims, zeilen = {}, []
    for (m, it), b, l0 in zip(einsaetze, bilder, basis):
        werte = [median_l(b, w, k) for k in raster]
        k_voll = float(raster[int(np.argmin([abs(v - ziel) for v in werte]))])
        k = float(np.clip(round(k_voll / 2 / 0.05) * 0.05, -MAX_TRIM, MAX_TRIM))
        l1 = median_l(b, w, k)
        trims[str(m["rec_in_f"])] = {"shot": f"S{m['shot']:02d}", "clip": m["clip"], "blenden": round(k, 2),
                                     "median_L_basis": round(l0, 1), "median_L_trim": round(l1, 1)}
        zeilen.append((m, b, k, l0, l1))
        print(f"S{m['shot']:02d} {m['clip']} @{fb.tc(m['rec_in_f'])}: L* {l0:5.1f} → Trim {k:+.2f} Bl. → {l1:5.1f}")
    (HIER / "broll_trims.json").write_text(json.dumps(trims, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Ziel (Median aller Shots): L* {ziel:.1f}; Spanne vorher {min(basis):.1f}–{max(basis):.1f}, "
          f"nachher {min(z[4] for z in zeilen):.1f}–{max(z[4] for z in zeilen):.1f}")
    # Kontaktbogen: je Einsatz Basis | mit Trim (mittleres Probenbild)
    kacheln = []
    for m, b, k, l0, l1 in zeilen:
        paar = np.concatenate([grade(b[1], w), grade(b[1], w, k)], axis=1)
        im = Image.fromarray(CL.to_u8(paar)).resize((2 * 240, 135), Image.LANCZOS)
        kacheln.append(CL.label(im, f"S{m['shot']:02d} {m['clip']} {k:+.2f} Bl.", 13))
    spalten = 3
    bogen = Image.new("RGB", (spalten * 486, ((len(kacheln) + spalten - 1) // spalten) * 141), (20, 20, 20))
    for i, im in enumerate(kacheln):
        bogen.paste(im, ((i % spalten) * 486 + 3, (i // spalten) * 141 + 3))
    bogen.save(HIER / "kontaktbogen_BRoll_trims.jpg", quality=88)


if __name__ == "__main__":
    main()
