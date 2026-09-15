"""Vorlage (Stand 15.09.2026): Echte Kopfoberkante je Proben-Frame aus der Vision-Personenmaske messen → kopf/kopf_oben.json.

Aufruf (im Chargen-Ordner, nach kopf_angleichen.py und kopf_beide.py, vor kopf_final.py):
  swiftc -O _intern/begradigen/personenmaske.swift -o _intern/begradigen/personenmaske   (einmal bauen)
  _intern/begradigen/personenmaske "$PWD/_intern/begradigen/kopf/frames"                 (Masken; vorhandene werden übersprungen)
  tools/autocut/venv/bin/python _intern/begradigen/kopf_oben_messen.py
Eingaben: kopf/frames/a_<Frame>.jpg (a7) und b_<Frame>.jpg (FX3) aus kopf_angleichen.py/kopf_beide.py (dort auch die
  Stücke ohne a7), je <Name>.maske.pgm (personenmaske), ../gesichtscheck/faces (Gesichtsboxen normiert, Ursprung oben links),
  parameter_berechnen.py (H).
Je Frame mit Gesicht (Konfidenz ≥ 0,5, größte Box) und Maske: in den Spalten ±0,25 Boxbreiten um die Gesichtsmitte die
oberste Maskenzeile oberhalb der Gesichtsmitte (Maske > 128); Median über mind. 3 Spalten = Kopfoberkante (normiert).
Kopfmitte wie in kopf_angleichen.py = Boxmitte − 0,08 Boxhöhen.
Schreibt kopf/kopf_oben.json {Frame-Datei: {top_px_rel (Kopfoberkante − Kopfmitte in Timeline-px, negativ = darüber),
gesicht_h_px, am_rand (Maske berührt die Bildoberkante → Kopf angeschnitten, Wert unsicher)}}; Konsole: Schädeldach in
Gesichtshöhen je Kamera. Nichts in Resolve.
Befund (15.09.): Schädeldach ≈ 1,0 Gesichtshöhen über der Kopfmitte (a7 1,01 mit p10 0,94 / p90 1,08; FX3 0,98 mit
p10 0,91 / p90 1,05). Die Vision-Maske (accurate) kommt bei 960×540-Frames (16:9) in 2016×1512 (4:3) → nur normiert rechnen.
Herkunft: Taxodia-Session, inline im Session-Transkript (15.09.2026, kein eigenes Skript)
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import numpy as np

HIER = Path(__file__).resolve().parent
INTERN = HIER.parent
spec = importlib.util.spec_from_file_location("pb", HIER / "parameter_berechnen.py")
pb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pb)

# ── ANPASSEN je Charge ─────────────────────────────
# keine eigenen Werte: Timeline-Höhe H aus parameter_berechnen.py, Frames aus kopf/frames
# ── Ende ANPASSEN ──────────────────────────────────

H = pb.H
FRAMES = HIER / "kopf" / "frames"


def pgm(p: Path) -> np.ndarray:
    d = p.read_bytes()
    teile = d.split(b"\n", 3)
    w, h = map(int, teile[1].split())
    return np.frombuffer(teile[3], np.uint8).reshape(h, w)


def main() -> None:
    tsv = subprocess.run([str(INTERN / "gesichtscheck" / "faces"), str(FRAMES.resolve())], capture_output=True, text=True).stdout
    oben, ohne_maske = {}, []
    for z in tsv.splitlines():
        name, _, rest = z.partition("\t")
        boxen = [tuple(map(float, b.split(","))) for b in rest.split(";")] if rest and rest != "ERR" else []
        boxen = [b for b in boxen if b[4] >= 0.5]
        mp = FRAMES / (name[:-4] + ".maske.pgm")
        if boxen and not mp.exists():
            ohne_maske.append(name)
        if not boxen or not mp.exists():
            continue
        x0, y0, x1, y1, _ = max(boxen, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        m = pgm(mp) > 128
        mh, mw = m.shape
        cx = (x0 + x1) / 2
        bw = x1 - x0
        spalten = range(int((cx - 0.25 * bw) * mw), int((cx + 0.25 * bw) * mw))
        cy_row = int((y0 + y1) / 2 * mh)
        tops = []
        for c in spalten:
            col = m[:cy_row, c]
            idx = np.argmax(col) if col.any() else None
            if idx is not None and col[idx]:
                tops.append(idx / mh)
        if len(tops) < 3:
            continue
        top_norm = float(np.median(tops))
        kopf_mitte_y = ((y0 + y1) / 2 - 0.08 * (y1 - y0))
        oben[name] = {"top_px_rel": (top_norm - kopf_mitte_y) * H, "gesicht_h_px": (y1 - y0) * H, "am_rand": top_norm <= 0.002}
    (HIER / "kopf" / "kopf_oben.json").write_text(json.dumps(oben, indent=1), encoding="utf-8")
    if ohne_maske:
        print(f"Ohne Maske (erst personenmaske laufen lassen): {len(ohne_maske)}, z. B. {ohne_maske[:3]}")
    a = [v for k, v in oben.items() if k.startswith("a_")]
    b = [v for k, v in oben.items() if k.startswith("b_")]
    for name, vals in (("a7", a), ("FX3", b)):
        r = np.array([-v["top_px_rel"] / v["gesicht_h_px"] for v in vals if not v["am_rand"]])
        print(f"{name}: Schädeldach über Kopfmitte = {np.median(r):.2f} × Gesichtshöhe (p10 {np.percentile(r, 10):.2f}, "
              f"p90 {np.percentile(r, 90):.2f}); Maske am oberen Bildrand: {sum(v['am_rand'] for v in vals)} von {len(vals)}")


if __name__ == "__main__":
    main()
