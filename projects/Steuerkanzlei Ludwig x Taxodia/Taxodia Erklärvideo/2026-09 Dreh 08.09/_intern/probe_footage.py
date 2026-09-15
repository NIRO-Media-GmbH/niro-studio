"""Technik-Inventar aller Clips (nur lesen): Codec, Auflösung, fps, Dauer,
Aufnahmezeit laut Kamera-XML (Uhr der Kamera, inkl. eingestellter Zeitzone),
Gamma/Gamut und Objektiv.

Zeitzonen-Falle 08.09.: a7MK4 und FX3 schreiben +01:00, die FX3A +02:00 —
deshalb wird die Kamera-Uhrzeit direkt aus der XML gelesen, nicht aus der
UTC-creation_time zurückgerechnet.

Schreibt _intern/footage_probe.json und druckt eine Ordner-Übersicht.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJEKTE = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "Steuerkanzlei Ludwig x Taxodia/02_Projekte"
)
OUT = Path(__file__).resolve().parent / "footage_probe.json"


def nas_projekt() -> Path:
    ziel = unicodedata.normalize("NFC", "01_Taxodia Erklärvideo")
    for name in os.listdir(PROJEKTE):
        if unicodedata.normalize("NFC", name) == ziel:
            return PROJEKTE / name
    raise SystemExit(f"NAS-Projektordner nicht gefunden: {ziel}")


FOOTAGE = nas_projekt() / "03_Medien" / "01_Footage"


def xml_meta(p: Path) -> dict:
    x = p.with_name(p.stem + "M01.XML")
    if not x.exists():
        return {}
    s = x.read_text(encoding="utf-8", errors="ignore")

    def g(pat: str) -> str | None:
        m = re.search(pat, s)
        return m.group(1) if m else None

    cd = g(r'CreationDate value="([^"]+)"')
    return {
        "kamera_modell": g(r'Device manufacturer="Sony" modelName="([^"]+)"'),
        "objektiv": g(r'Lens modelName="([^"]+)"'),
        "gamma": g(r'CaptureGammaEquation" value="([^"]+)"'),
        "gamut": g(r'CaptureColorPrimaries" value="([^"]+)"'),
        "creation_kamera": cd,
        "uhrzeit_lokal_ca": cd[11:19] if cd else None,
    }


def probe(p: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,channels:"
         "format=duration",
         "-of", "json", str(p)],
        capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = round(float(num) / float(den or 1), 3) if num else None
    return {
        "rel": str(p.relative_to(FOOTAGE)),
        "ordner": str(p.parent.relative_to(FOOTAGE)),
        "name": p.name,
        "codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "w": v.get("width"), "h": v.get("height"), "fps": fps,
        "audio_kanaele": a.get("channels"),
        "dauer_s": round(float(d.get("format", {}).get("duration", 0) or 0), 1),
        **xml_meta(p),
    }


def main() -> None:
    files = sorted(p for p in FOOTAGE.rglob("*")
                   if p.is_file() and not p.name.startswith("._")
                   and p.suffix.lower() in {".mp4", ".mov"})
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(probe, files))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    by = defaultdict(list)
    for r in rows:
        by[r["ordner"]].append(r)
    for ordner, rs in sorted(by.items()):
        tot = sum(r["dauer_s"] for r in rs)
        formate = sorted({f"{r['codec']} {r['w']}x{r['h']} {r['fps']}fps {r.get('gamma')} "
                          f"{r.get('kamera_modell')} | {r.get('objektiv')}" for r in rs})
        zeiten = sorted(r.get("uhrzeit_lokal_ca") or "?" for r in rs)
        print(f"{ordner}: {len(rs)} Clips, {tot/60:.1f} min, Uhr {zeiten[0]}–{zeiten[-1]}")
        for f in formate:
            print(f"     {f}")
        for r in sorted(rs, key=lambda r: r["name"]):
            print(f"       {r['name']:<28} {r['dauer_s']/60:5.1f} min  {r.get('creation_kamera')}")
    print(f"\n{len(rows)} Clips -> {OUT}")


if __name__ == "__main__":
    main()
