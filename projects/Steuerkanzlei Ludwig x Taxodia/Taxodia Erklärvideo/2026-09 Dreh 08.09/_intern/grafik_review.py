"""Review der Grafikebene auf echtem Bild (Taxodia, 15.09.2026).

Aufruf: python3 _intern/grafik_review.py <frame,frame,...>
Legt je Timeline-Frame das Remotion-Standbild (_intern/sichtung/grafik-review/stills/*_<frame>.png, 1920×1080 mit Alpha)
über das Bild, das an dieser Stelle in der Resolve-Timeline zu sehen ist: V3 (B-Roll) vor V2 (a7) vor V1 (FX3).
Liegt V2 oben, entsteht zusätzlich die FX3-Variante (der Cutter kann den Winkel wechseln).
Bildquelle: Proxys (1080p) aus <Kamera-Ordner>/Proxy/<Stem>.mov. Ergebnis: _intern/sichtung/grafik-review/review_*.jpg
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
REV = CH / "_intern" / "sichtung" / "grafik-review"
FPS = 25.0
COMP = "Taxodia-Erklaervideo-Grafikebene"


def proxy(pfad: str) -> str:
    p = Path(pfad)
    q = p.parent / "Proxy" / f"{p.stem}.mov"
    return str(q if q.exists() else p)


def schichten(frame: int, tl: dict, broll: dict) -> list[tuple[str, str, float]]:
    """[(Spur, Datei, Quellsekunde)] von oben nach unten."""
    out = []
    for z in broll["plan"]:
        if z["rec_in_f"] <= frame < z["rec_out_f"]:
            out.append(("V3", z["datei"], (z["left_offset_f"] + frame - z["rec_in_f"]) / FPS))
    for spur in ("V2", "V1"):
        for it in tl["items"]:
            if it["track"] == spur and it["rec_in_f"] <= frame < it["rec_out_f"]:
                out.append((spur, it["clip"], (it["src_in_f"] + frame - it["rec_in_f"]) / FPS))
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
        for spur, datei, t in varianten:
            bg = REV / "bg" / f"{f}_{spur}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", proxy(datei), "-frames:v", "1",
                            "-vf", "scale=1920:1080", "-q:v", "3", str(bg)], check=True)
            out = REV / f"review_{f}_{spur}.jpg"
            label = f"{f} ({int(f // FPS // 60):02d}:{int(f // FPS % 60):02d}:{f % 25:02d}) {spur} {Path(datei).stem}"
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
