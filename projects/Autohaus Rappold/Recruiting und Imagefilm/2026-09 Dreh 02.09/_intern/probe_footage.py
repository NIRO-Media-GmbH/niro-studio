"""Technik-Inventar aller Clips (nur lesen): Codec, Auflösung, fps, Rotation,
Dauer, Aufnahmezeit (Sony: creation_time in UTC -> +2 h MESZ).

Schreibt _intern/footage_probe.json und druckt eine Ordner-Übersicht.
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

FOOTAGE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Autohaus Rappold GmbH/02_Projekte/01_Dreh_2026.09 Image & Ads, Schlüsselbox/"
    "03_Medien/01_Footage"
)
OUT = Path(__file__).resolve().parent / "footage_probe.json"


def probe(p: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:"
         "stream_side_data=rotation:format=duration:format_tags=creation_time",
         "-of", "json", str(p)],
        capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    rot = None
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = sd["rotation"]
    fmt = d.get("format", {})
    ct = fmt.get("tags", {}).get("creation_time")
    lokal = None
    if ct:
        lokal = (datetime.fromisoformat(ct.replace("Z", "+00:00")) + timedelta(hours=2)).strftime("%H:%M:%S")
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = round(float(num) / float(den or 1), 3) if num else None
    return {
        "rel": str(p.relative_to(FOOTAGE)),
        "ordner": str(p.parent.relative_to(FOOTAGE)),
        "name": p.name,
        "codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "w": v.get("width"), "h": v.get("height"), "fps": fps, "rotation": rot,
        "audio": has_audio,
        "dauer_s": round(float(fmt.get("duration", 0) or 0), 1),
        "creation_utc": ct, "uhrzeit_lokal_ca": lokal,
    }


def main() -> None:
    files = sorted(p for p in FOOTAGE.rglob("*")
                   if p.is_file() and p.suffix.lower() in {".mp4", ".mov"})
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(probe, files))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    by = defaultdict(list)
    for r in rows:
        by[r["ordner"]].append(r)
    for ordner, rs in sorted(by.items()):
        tot = sum(r["dauer_s"] for r in rs)
        formate = sorted({f"{r['codec']} {r['w']}x{r['h']} {r['fps']}fps rot={r['rotation']}" for r in rs})
        zeiten = sorted(r["uhrzeit_lokal_ca"] or "?" for r in rs)
        kams = sorted({r["name"].split("_")[0] for r in rs})
        print(f"{ordner}: {len(rs)} Clips, {tot/60:.1f} min, Kameras {kams}, "
              f"Uhr {zeiten[0]}–{zeiten[-1]}")
        for f in formate:
            print(f"     {f}")
    print(f"\n{len(rows)} Clips -> {OUT}")


if __name__ == "__main__":
    main()
