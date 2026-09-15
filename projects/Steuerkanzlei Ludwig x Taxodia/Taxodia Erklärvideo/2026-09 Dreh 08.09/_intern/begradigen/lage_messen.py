"""Kamerlage der Interview-Clips aus den Sony-Metadaten (rtmd) messen (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/lage_messen.py
Liest (nur lesend, NAS) je Interview-Clip an mehreren Stellen des genutzten Bereichs 1 s der Metadatenspur:
  - Brennweite tatsächlich (Tag 0x8005) und KB-äquivalent (0x8004), Fokusdistanz (0x8001) — RDD-18-Distanzformat
  - Beschleunigungssensor (Satz mit 0xe44b: 3 × int16 je Sample, Skala 0xe449 = LSB pro g) → Schwerkraftvektor
  - Gyroskop (0xe43b, Skala 0xe439) → steht die Kamera still?
Schreibt _intern/begradigen/lage.json. Vorzeichen/Achsen werden in geometrie_pruefen gegen Bildlinien geprüft.
"""
from __future__ import annotations

import importlib.util
import json
import math
import struct
import subprocess
from pathlib import Path

HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
UL = bytes.fromhex("060e2b34")


def ber(buf: bytes, i: int) -> tuple[int, int]:
    b = buf[i]
    if b < 0x80:
        return b, i + 1
    n = b & 0x7F
    return int.from_bytes(buf[i + 1:i + 1 + n], "big"), i + 1 + n


def distanz(v: int) -> float:
    """RDD-18-Distanzformat: obere 4 Bit = Exponent (vorzeichenbehaftet, Basis 10), untere 12 Bit = Mantisse, Einheit Meter."""
    e = v >> 12
    e = e - 16 if e >= 8 else e
    return (v & 0x0FFF) * 10.0 ** e


def samples(buf: bytes) -> list[dict]:
    """Alle rtmd-Samples im Puffer: je Sample Header (0x001c) + KLV-Sätze mit lokalen Tags."""
    out, i = [], 0
    while i + 28 < len(buf):
        if buf[i:i + 2] != b"\x00\x1c":
            nxt = buf.find(b"\x00\x1c\x01\x00", i + 1)
            if nxt == -1:
                break
            i = nxt
            continue
        j, tags = i + 28, {}
        while j + 17 < len(buf) and buf[j:j + 4] == UL:
            ln, k = ber(buf, j + 16)
            ende = k + ln
            while k + 4 <= ende:
                t, l = struct.unpack(">HH", buf[k:k + 4])
                tags.setdefault(t, buf[k + 4:k + 4 + l])
                k += 4 + l
            j = ende
        if tags:
            out.append(tags)
        i = max(j, i + 28)
    return out


def imu(block: bytes, skala: float) -> list[tuple[float, float, float]]:
    n, groesse = struct.unpack(">II", block[:8])
    return [tuple(v / skala for v in struct.unpack(">hhh", block[8 + q * groesse:8 + q * groesse + 6])) for q in range(n)]


def messen(datei: str, sekunde: float) -> dict:
    roh = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{sekunde:.2f}", "-i", datei, "-map", "0:d:0", "-c", "copy", "-t", "1",
                          "-f", "data", "-"], capture_output=True, check=True).stdout
    acc, gyr, f_ist, f_kb, fokus = [], [], set(), set(), set()
    for s in samples(roh):
        if 0x8005 in s:
            f_ist.add(round(distanz(struct.unpack(">H", s[0x8005])[0]) * 1000, 1))
        if 0x8004 in s:
            f_kb.add(round(distanz(struct.unpack(">H", s[0x8004])[0]) * 1000, 1))
        if 0x8001 in s:
            fokus.add(round(distanz(struct.unpack(">H", s[0x8001])[0]), 2))
        if 0xE44B in s and 0xE449 in s:
            acc += imu(s[0xE44B], struct.unpack(">f", s[0xE449])[0])
        if 0xE43B in s and 0xE439 in s:
            gyr += imu(s[0xE43B], struct.unpack(">f", s[0xE439])[0])
    mx = [sum(a[q] for a in acc) / len(acc) for q in range(3)] if acc else None
    streu = max(max(a[q] for a in acc) - min(a[q] for a in acc) for q in range(3)) if acc else None
    gyro_max = max(abs(v) for g in gyr for v in g) if gyr else None
    return {"sekunde": round(sekunde, 1), "brennweite_mm": sorted(f_ist), "kb_mm": sorted(f_kb), "fokus_m": sorted(fokus),
            "acc_mittel_g": [round(v, 4) for v in mx] if mx else None, "acc_streuung_g": round(streu, 3) if streu is not None else None,
            "gyro_max": round(gyro_max, 2) if gyro_max is not None else None, "imu_samples": len(acc),
            "neigung_xy_grad": round(math.degrees(math.atan2(mx[0], mx[1])), 2) if mx else None,
            "neigung_z_grad": round(math.degrees(math.atan2(mx[2], math.hypot(mx[0], mx[1]))), 2) if mx else None}


def main() -> None:
    tl, shots = fb.lade()
    p, fehler = fb.plan(tl, shots)
    clips: dict[str, list] = {}
    for it in p["V1"] + p["V2_voll"]:
        clips.setdefault(it.clip, []).append(it)
    out = {}
    for clip, items in sorted(clips.items()):
        # Stellen: Mitte jedes Items, höchstens 6, über den Clip verteilt
        stellen = sorted({round((i.src_in_f + i.src_out_f) / 2 / 25, 1) for i in items})
        if len(stellen) > 6:
            stellen = [stellen[round(q * (len(stellen) - 1) / 5)] for q in range(6)]
        mess = [messen(clip, s) for s in stellen]
        name = Path(clip).stem
        out[name] = {"datei": clip, "items": len(items), "messungen": mess}
        print(f"== {name} ({len(items)} Items)")
        for m in mess:
            print(f"   {m['sekunde']:>7}s f={m['brennweite_mm']} KB={m['kb_mm']} Fokus={m['fokus_m']} acc={m['acc_mittel_g']} "
                  f"±{m['acc_streuung_g']} gyro_max={m['gyro_max']} → xy {m['neigung_xy_grad']}°, z {m['neigung_z_grad']}°")
    (HIER / "lage.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
