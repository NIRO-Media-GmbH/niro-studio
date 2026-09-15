#!/usr/bin/env python3
"""Struktur-Scan MAN-Drehs: ffprobe-Metadaten aller Videodateien -> scan.csv"""
import csv, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

NAS = Path("/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/MAN Truck and Bus/02_Projekte")
OUT = Path(__file__).parent / "scan.csv"
EXTS = {".mp4", ".mov", ".mxf", ".m4v"}

def probe(p: Path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(p)],
            capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
        dur = float(d.get("format", {}).get("duration", 0))
        v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
        a = [s for s in d.get("streams", []) if s.get("codec_type") == "audio"]
        return {
            "dreh": p.relative_to(NAS).parts[0],
            "relpath": str(p.relative_to(NAS)),
            "size_gb": round(p.stat().st_size / 1e9, 2),
            "dur_min": round(dur / 60, 1),
            "breite": v.get("width", 0), "hoehe": v.get("height", 0),
            "audio_kanaele": sum(int(s.get("channels", 0)) for s in a),
        }
    except Exception as e:
        print(f"WARN {p}: {e}", file=sys.stderr)
        return None

files = [p for p in NAS.rglob("*") if p.suffix.lower() in EXTS
         and not p.name.startswith("._")]
print(f"{len(files)} Videodateien gefunden, probe läuft …")
with ThreadPoolExecutor(max_workers=8) as ex:
    rows = [r for r in ex.map(probe, files) if r]
rows.sort(key=lambda r: (r["dreh"], -r["size_gb"]))
with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"{len(rows)} Zeilen -> {OUT}")
