"""Prüft die LG-Testexporte: Codec/Profil/Level/Tag, Auflösung, fps, Frames, Dauer, Größe,
Tonspur, faststart (moov vor mdat) und Spitzen-Bitrate über 1-s-Fenster."""
import json
import struct
import subprocess
import sys
from pathlib import Path

E = Path("/Users/jansantos/NIRO Studio/projects/AeternaWeddings/Messe-Showreel/2026-09 Hochzeitsmesse/Ergebnisse/Export")
namen = sys.argv[1:] or sorted(p.name for p in E.glob("0*_Aeterna-Messe_*.mp4"))


def atome(pfad):
    reihenfolge = []
    with open(pfad, "rb") as f:
        while len(reihenfolge) < 12:
            kopf = f.read(8)
            if len(kopf) < 8:
                break
            groesse, typ = struct.unpack(">I4s", kopf)
            if groesse == 1:
                groesse = struct.unpack(">Q", f.read(8))[0]
                f.seek(groesse - 16, 1)
            else:
                f.seek(groesse - 8, 1)
            reihenfolge.append(typ.decode("latin-1"))
            if groesse == 0:
                break
    return reihenfolge


def spitze_mbps(pfad, fps):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "packet=pts_time,size", "-of", "csv=p=0", str(pfad)], text=True)
    fenster = {}
    for zeile in out.splitlines():
        teile = zeile.split(",")
        if len(teile) < 2 or teile[0] in ("", "N/A"):
            continue
        sek = int(float(teile[0]))
        fenster[sek] = fenster.get(sek, 0) + int(teile[1])
    return max(fenster.values()) * 8 / 1e6 if fenster else None


for name in namen:
    p = E / name
    if not p.exists():
        print(f"{name}: fehlt")
        continue
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(p)]))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    fps = eval(v["r_frame_rate"])
    atoms = atome(p)
    fast = "ja" if "moov" in atoms and "mdat" in atoms and atoms.index("moov") < atoms.index("mdat") else "nein"
    groesse = int(info["format"]["size"])
    print(f"{name}")
    print(f"  {v['codec_name']} {v.get('profile')} Level {v.get('level')} Tag {v.get('codec_tag_string')} | "
          f"{v['width']}x{v['height']} {fps:g} fps {v.get('pix_fmt')} | Frames {v.get('nb_frames')} | "
          f"Farbe {v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')} {v.get('color_range')}")
    print(f"  Dauer {float(info['format']['duration']):.2f} s | {groesse / 1e9:.2f} GB | "
          f"Mittel {int(info['format']['bit_rate']) / 1e6:.1f} Mbit/s | Spitze (1 s) {spitze_mbps(p, fps):.1f} Mbit/s | "
          f"Ton {a['codec_name'] + ' ' + str(a.get('channels')) + 'ch ' + a.get('sample_rate', '') if a else 'keiner'} | faststart {fast}")
