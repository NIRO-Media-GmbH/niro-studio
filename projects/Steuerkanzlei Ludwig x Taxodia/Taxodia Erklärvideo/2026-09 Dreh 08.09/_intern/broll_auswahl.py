"""B-Roll-Auswahl des Users aus Resolve lesen und je Shot Standbilder aus dem echten In/Out ziehen (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/broll_auswahl.py [--nur-lesen]

1. Liest NUR LESEND die Timeline „B-Roll Auswahl" (per Unique-ID) im offenen Projekt „Taxodia 09.26" und schreibt
   _intern/autocut/broll_auswahl.json: je Item Clip, Datei, Quell-In/Out in Sekunden (aus GetLeftOffset + Dauer,
   Timeline 25 fps, Clips laufen dort in Echtzeit), Record-Position in der Auswahl-Timeline.
2. Zieht aus dem Proxy (Ordner Proxy/<Stem>.mov, 1080p50) je Shot vier Standbilder (Anfang, 1/3, 2/3, Ende, jeweils
   innerhalb des Bereichs) und legt Kontaktbögen nach _intern/sichtung/broll-auswahl/ (8 Shots je Bogen).
User-Regel 15.09.: Nur die Bereiche aus der Auswahl verwenden — kürzen ja, nie verlängern.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut.resolve_api import connect  # noqa: E402

CH = Path(__file__).resolve().parent.parent
OUT_JSON = CH / "_intern" / "autocut" / "broll_auswahl.json"
SHEETS = CH / "_intern" / "sichtung" / "broll-auswahl"
PROJEKT = "Taxodia 09.26"
TIMELINE_ID = "192dcff5-4532-40a0-8d79-c959143f1580"  # „B-Roll Auswahl" des Users
TL_FPS = 25.0


def lesen() -> dict:
    r = connect()
    proj = r.GetProjectManager().GetCurrentProject()
    if proj.GetName() != PROJEKT:
        raise SystemExit(f"Offenes Projekt ist '{proj.GetName()}', erwartet '{PROJEKT}' — nichts gelesen.")
    tl = next((proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)
               if proj.GetTimelineByIndex(i).GetUniqueId() == TIMELINE_ID), None)
    if tl is None:
        raise SystemExit("Timeline „B-Roll Auswahl“ nicht gefunden.")
    start = tl.GetStartFrame()
    shots = []
    for kind in ("video",):
        for ti in range(1, tl.GetTrackCount(kind) + 1):
            for it in tl.GetItemListInTrack(kind, ti) or []:
                mpi = it.GetMediaPoolItem()
                left, dur = int(it.GetLeftOffset()), int(it.GetDuration())
                datei = unicodedata.normalize("NFC", mpi.GetClipProperty("File Path"))
                shots.append({
                    "nr": len(shots) + 1, "spur": f"V{ti}", "clip": Path(datei).stem, "datei": datei,
                    "clip_fps": float(mpi.GetClipProperty("FPS") or 0),
                    "in_s": round(left / TL_FPS, 3), "out_s": round((left + dur) / TL_FPS, 3),
                    "dauer_s": round(dur / TL_FPS, 3), "left_offset_f": left, "dauer_f": dur,
                    "auswahl_rec": [int(it.GetStart()) - start, int(it.GetEnd()) - start],
                })
    data = {"projekt": proj.GetName(), "timeline": tl.GetName(), "timeline_id": TIMELINE_ID,
            "timeline_fps": TL_FPS, "hinweis": "Nur diese Bereiche verwenden (User 15.09.): kürzen ja, nie verlängern.",
            "shots": shots}
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(shots)} Shots, {sum(s['dauer_s'] for s in shots):.1f} s → {OUT_JSON}")
    return data


def proxy_for(datei: str) -> Path:
    p = Path(datei)
    prox = p.parent / "Proxy" / f"{p.stem}.mov"
    return prox if prox.exists() else p


def sichten(data: dict) -> None:
    frames = SHEETS / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in data["shots"]:
        a, e = s["in_s"], s["out_s"]
        pos = [a + 0.1, a + (e - a) / 3, a + 2 * (e - a) / 3, e - 0.1]
        imgs = []
        for k, t in enumerate(pos):
            f = frames / f"{s['nr']:02d}_{s['clip']}_{k}.jpg"
            if not f.exists():
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(proxy_for(s["datei"])),
                                "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", str(f)], check=True)
            imgs.append(str(f))
        row = frames / f"row_{s['nr']:02d}.jpg"
        label = f"S{s['nr']:02d} {s['clip']} {a:.2f}-{e:.2f}s ({s['dauer_s']:.2f}s)"
        subprocess.run(["magick", *imgs, "+append", "-font", "/System/Library/Fonts/Supplemental/Arial.ttf",
                        "-gravity", "NorthWest", "-fill", "yellow", "-undercolor", "#000000A0",
                        "-pointsize", "28", "-annotate", "+8+6", label, str(row)], check=True)
        rows.append(str(row))
    for b in range(0, len(rows), 8):
        sheet = SHEETS / f"auswahl_{b // 8 + 1}.jpg"
        subprocess.run(["magick", *rows[b:b + 8], "-append", "-resize", "1600x", str(sheet)], check=True)
        print("Bogen:", sheet)


if __name__ == "__main__":
    d = lesen()
    if "--nur-lesen" not in sys.argv:
        sichten(d)
