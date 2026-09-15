"""Kontaktbögen für die Sichtung (nur lesen): pro Ordner ein Bild,
eine Zeile pro Clip mit N Keyframes (gleichmäßig verteilt) + Dateiname/Dauer.

Aufruf: contact_sheets.py [N=5] [Ordner-Filter]
Schreibt: _intern/sichtung/<Ordner>.jpg
Material ist S-Log3 — die Kacheln wirken flau, das ist kein Fehler.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INTERN = Path(__file__).resolve().parent
PROJEKTE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Steuerkanzlei Ludwig x Taxodia/02_Projekte"
)
OUT = INTERN / "sichtung"
TW, TH = 288, 162          # Kachel quer; Hochkant-Clips werden eingepasst
LABEL_W = 230


def nas_projekt() -> Path:
    ziel = unicodedata.normalize("NFC", "01_Taxodia Erklärvideo")
    for name in os.listdir(PROJEKTE):
        if unicodedata.normalize("NFC", name) == ziel:
            return PROJEKTE / name
    raise SystemExit(f"NAS-Projektordner nicht gefunden: {ziel}")


FOOTAGE = nas_projekt() / "03_Medien" / "01_Footage"


def frame(path: Path, t: float, target: Path) -> Path | None:
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-skip_frame", "nokey", "-ss", f"{t:.2f}",
         "-i", str(path), "-frames:v", "1", "-vf", f"scale={TW*2}:-2", str(target)],
        capture_output=True, text=True)
    return target if r.returncode == 0 and target.exists() else None


def tile(img_path: Path | None) -> Image.Image:
    canvas = Image.new("RGB", (TW, TH), (30, 30, 30))
    if img_path is None:
        return canvas
    im = Image.open(img_path).convert("RGB")
    im.thumbnail((TW, TH))
    canvas.paste(im, ((TW - im.width) // 2, (TH - im.height) // 2))
    return canvas


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    filt = sys.argv[2] if len(sys.argv) > 2 else ""
    probe = json.loads((INTERN / "footage_probe.json").read_text())
    OUT.mkdir(exist_ok=True)
    folders: dict[str, list[dict]] = {}
    filt = unicodedata.normalize("NFC", filt)
    for r in probe:
        ordner = unicodedata.normalize("NFC", r["ordner"])
        if "Proxy" in ordner or (filt and filt not in ordner):
            continue
        folders.setdefault(ordner, []).append(r)
    font = ImageFont.load_default()

    for ordner, clips in sorted(folders.items()):
        clips.sort(key=lambda r: r["name"])
        with tempfile.TemporaryDirectory() as td:
            jobs = []
            for ci, c in enumerate(clips):
                d = max(c["dauer_s"], 0.5)
                for k in range(n):
                    t = d * (k + 0.5) / n
                    jobs.append((ci, k, FOOTAGE / c["rel"], t, Path(td) / f"{ci}_{k}.jpg"))
            with ThreadPoolExecutor(max_workers=4) as pool:
                res = list(pool.map(lambda j: (j[0], j[1], frame(j[2], j[3], j[4])), jobs))
            sheet = Image.new("RGB", (LABEL_W + n * TW, len(clips) * TH), (255, 255, 255))
            draw = ImageDraw.Draw(sheet)
            for ci, k, p in res:
                sheet.paste(tile(p), (LABEL_W + k * TW, ci * TH))
            for ci, c in enumerate(clips):
                y = ci * TH
                draw.text((6, y + 8), c["name"], fill=(0, 0, 0), font=font)
                draw.text((6, y + 24), f"{c['dauer_s']:.0f} s · {c['fps']} fps", fill=(0, 0, 0), font=font)
                draw.text((6, y + 40), f"Uhr ~{c.get('uhrzeit_lokal_ca')}", fill=(90, 90, 90), font=font)
                draw.line([(0, y), (sheet.width, y)], fill=(200, 200, 200))
        name = ordner.replace("/", " - ")
        target = OUT / f"{name}.jpg"
        sheet.save(target, quality=82)
        print(f"{ordner}: {len(clips)} Clips -> {target.name}", flush=True)


if __name__ == "__main__":
    main()
