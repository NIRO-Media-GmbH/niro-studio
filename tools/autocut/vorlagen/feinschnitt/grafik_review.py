"""Vorlage (Stand 15.09.2026): Review der Grafikebene auf echtem Bild.

Aufruf: python3 _intern/grafik_review.py <frame,frame,...>
Legt je Timeline-Frame das Remotion-Standbild (_intern/sichtung/grafik-review/stills/<COMP>_<frame>.png, 1920×1080 mit Alpha)
über das Bild, das an dieser Stelle in der Resolve-Timeline zu sehen ist: V3 (B-Roll) vor V2 (a7) vor V1 (FX3).
Liegt V2 oben, entsteht zusätzlich die FX3-Variante (der Cutter kann den Winkel wechseln).
Eingaben: _intern/autocut/timeline.json (V1/V2 laut roh-Plan, nicht der Live-Stand in Resolve) und
          _intern/autocut/broll_einsatz.json (V3, entsteht erst mit broll_einsetzen.py --bauen). Liest Resolve nicht.
          V3 mit digitalem Zoom der Brennweitenregel (plan → zoom, z > 1) wird wie beim Bau als Ausschnitt iw/z × ih/z
          auf die Bildmitte gezeigt (ältere broll_einsatz.json ohne zoom: 1,0).
Standbilder vorher rendern (Remotion-Frame = Timeline-Frame, Grafik liegt ab Frame 0):
          cd tools/motion && npx tsx scripts/stills-multi.ts <COMP> "<Charge>/_intern/sichtung/grafik-review/stills" <frame,frame,...>
          [--public-dir=…] — Ergebnis muss 1920×1080 sein (4K-Komposition: Standard --scale=0.5, 1080p: --scale=1).
Bildquelle: Proxys (1080p) aus <Kamera-Ordner>/Proxy/<Stem>.mov (sonst Original). Ergebnis: _intern/sichtung/grafik-review/review_*.jpg
          und bogen_*.jpg (6 Kacheln je Bogen). Braucht ffmpeg und ImageMagick (magick).

Herkunft: Taxodia-Charge, _intern/grafik_review.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
REV = CH / "_intern" / "sichtung" / "grafik-review"

# ── ANPASSEN je Charge ─────────────────────────────
FPS = 25.0  # Timeline-Bildrate [fps]; Standard (15.09.)
COMP = "<Remotion-Kompositions-ID>"  # ID der Grafikebenen-Komposition (tools/motion/src/Root.tsx) = Dateipräfix der Standbilder <COMP>_<frame>.png
# ── Ende ANPASSEN ──────────────────────────────────


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def bild_filter(zoom: float | None, breite: int = 1920, hoehe: int = 1080) -> str:
    """ffmpeg-Filter für das Hintergrundbild: digitaler Zoom z > 1 der Brennweitenregel (ZoomX/ZoomY auf die Bildmitte)
    als mittiger Ausschnitt crop=iw/z:ih/z vor dem Skalieren — wie beim Bau; ohne Zoom nur scale."""
    z = float(zoom or 1.0)
    return (f"crop=iw/{z:g}:ih/{z:g}," if z > 1.0 + 1e-9 else "") + f"scale={breite}:{hoehe}"


def schichten(frame: int, tl: dict, broll: dict) -> list[tuple[str, str, float, float]]:
    """[(Spur, Datei, Quellsekunde, digitaler Zoom)] von oben nach unten; Zoom nur auf V3 (plan → zoom), sonst 1,0."""
    out = []
    for z in broll["plan"]:
        if z["rec_in_f"] <= frame < z["rec_out_f"]:
            out.append(("V3", z["datei"], (z["left_offset_f"] + frame - z["rec_in_f"]) / FPS, float(z.get("zoom") or 1.0)))
    for spur in ("V2", "V1"):
        for it in tl["items"]:
            if it["track"] == spur and it["rec_in_f"] <= frame < it["rec_out_f"]:
                out.append((spur, it["clip"], (it["src_in_f"] + frame - it["rec_in_f"]) / FPS, 1.0))
    return out


def main() -> None:
    frames = [int(f) for f in sys.argv[1].split(",")]
    tl = json.loads((AC / "timeline.json").read_text())
    broll = json.loads((AC / "broll_einsatz.json").read_text())
    (REV / "bg").mkdir(parents=True, exist_ok=True)
    kacheln = []
    for f in frames:
        still = REV / "stills" / f"{COMP}_{f}.png"
        lagen = schichten(f, tl, broll)
        varianten = lagen[:1] + ([l for l in lagen if l[0] == "V1"][:1] if lagen and lagen[0][0] == "V2" else [])
        for spur, datei, t, zoom in varianten:
            bg = REV / "bg" / f"{f}_{spur}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", proxy(datei), "-frames:v", "1",
                            "-vf", bild_filter(zoom), "-q:v", "3", str(bg)], check=True)
            out = REV / f"review_{f}_{spur}.jpg"
            label = f"{f} ({int(f // FPS // 60):02d}:{int(f // FPS % 60):02d}:{int(f % FPS):02d}) {spur} {Path(datei).stem}"
            subprocess.run(["magick", str(bg), str(still), "-composite", "-font", "/System/Library/Fonts/Supplemental/Arial.ttf",
                            "-gravity", "NorthWest", "-fill", "yellow", "-undercolor", "#000000A0", "-pointsize", "34",
                            "-annotate", "+12+10", label, "-quality", "88", str(out)], check=True)
            kacheln.append(str(out))
            print(out.name)
    for i in range(0, len(kacheln), 6):
        bogen = REV / f"bogen_{i // 6 + 1}.jpg"
        subprocess.run(["magick", "montage", "-font", "/System/Library/Fonts/Supplemental/Arial.ttf", *kacheln[i:i + 6],
                        "-tile", "2x3", "-geometry", "960x540+6+6",
                        "-background", "#222222", str(bogen)], check=True)
        print("Bogen:", bogen)


if __name__ == "__main__":
    main()
