"""Sony-rtmd-Datenspur (FX3, a7 IV) lesen und auswerten: Gyro, Beschleunigung, Brennweite, Fokus; Sidecar-XML → Kamera.

Aufbau der Datenspur (gemessen 21.09.2026, Spec-Nachtrag): ein rtmd-Sample je Videoframe, 19 456 Bytes, Header
``00 1c 01 00`` + 24 Bytes, dann KLV-Sätze (16-Byte-Key ab ``06 0e 2b 34``, BER-Länge, lokale Tags ``>HH`` Tag/Länge + Wert),
Rest Füllung. IMU-Block (0xE43B Gyro, 0xE44B Beschleunigung): n (u32), groesse (u32),
n × groesse Bytes, je Probe int16 x/y/z; Skalen 0xE439/0xE449 (float32, LSB je °/s bzw. je g); 0xE435 = IMU-Rate (u32, 2000).
Distanzen (0x8001 Fokus, 0x8004 KB, 0x8005 Brennweite) im RDD-18-Format, 0xFFFF = unbekannt.
Achsen: x links, y oben, z vorwärts. Alles nur lesend; ``datenspur_lesen`` liest die ganze Datei (≈ 300 MB/s übers NAS).
"""
from __future__ import annotations

import struct
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .charge import AutoCutError
from .media import _which

HEADER = b"\x00\x1c\x01\x00"
UL = bytes.fromhex("060e2b34")
KLV_KEY = bytes.fromhex("060e2b3402530101" "0c02010101010000")   # Key des Sony-Satzes mit den Objektivdaten (Beispiel)
TAG_FOKUS_M, TAG_KB_MM, TAG_BRENNWEITE_MM = 0x8001, 0x8004, 0x8005
TAG_IMU_HZ = 0xE435
TAG_GYRO, TAG_GYRO_SKALA = 0xE43B, 0xE439
TAG_ACC, TAG_ACC_SKALA = 0xE44B, 0xE449
# Tags, die ``auswerten`` liest — ``samples`` behält nur diese (ein Sample trägt 148–161 Tags, ≈ 7–8 KB Werte; bei langen
# Interview-Clips wären das mehrere GB). ``samples(buf, tags=None)`` liefert zur Diagnose alle (z. B. 0xE437/0xE43A).
TAGS_AUSWERTUNG = frozenset({TAG_GYRO, TAG_GYRO_SKALA, TAG_ACC, TAG_ACC_SKALA, TAG_IMU_HZ, TAG_KB_MM, TAG_BRENNWEITE_MM,
                             TAG_FOKUS_M})
MODELLE = {"ILME-FX3": "FX3", "ILCE-7M4": "a7IV"}
KEINE_DATENSPUR = (b"matches no streams", b"does not contain any stream")


@dataclass
class RtmdDaten:
    samples: int                      # rtmd-Samples = Videoframes
    imu_hz: float | None              # aus Tag 0xE435, sonst None (dann Proben je Sample × fps)
    proben_je_sample: int             # IMU-Proben je rtmd-Sample (80 bei 25p, 40 bei 50p)
    gyro: np.ndarray                  # (n, 3) °/s, alle Proben in Reihenfolge; (0, 3) ohne IMU
    acc: np.ndarray                   # (n, 3) g
    brennweite_mm: list[float] = field(default_factory=list)   # je Sample
    kb_mm: list[float] = field(default_factory=list)
    fokus_m: list[float] = field(default_factory=list)


def datenspur_lesen(path: str | Path) -> bytes:
    """Datenspur 0:d:0 als Rohbytes; leer, wenn die Datei keine Datenspur hat (Mavic, fremde Kamera)."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-v", "error", "-i", str(p), "-map", "0:d:0", "-c", "copy", "-f", "data", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        if any(m in r.stderr for m in KEINE_DATENSPUR):
            return b""
        raise AutoCutError(f"Datenspur nicht lesbar für {p.name}: {r.stderr[-300:].decode(errors='replace')}")
    return r.stdout


def ber(buf: bytes, i: int) -> tuple[int, int]:
    """BER-Länge ab buf[i]: (Länge, Index nach der Länge)."""
    b = buf[i]
    if b < 0x80:
        return b, i + 1
    n = b & 0x7F
    return int.from_bytes(buf[i + 1:i + 1 + n], "big"), i + 1 + n


def distanz(v: int) -> float:
    """RDD-18: obere 4 Bit Exponent (Zweierkomplement, Basis 10), untere 12 Bit Mantisse; Meter."""
    e = v >> 12
    e = e - 16 if e >= 8 else e
    return (v & 0x0FFF) * 10.0 ** e


def samples(buf: bytes, tags: frozenset[int] | set[int] | None = TAGS_AUSWERTUNG) -> list[dict[int, bytes]]:
    """Alle rtmd-Samples: je Sample ein Dict Tag → Wert (erster Treffer je Tag über alle KLV-Sätze des Samples), nur für
    ``tags`` (Standard: die von ``auswerten`` gelesenen; None = alle). Jedes Sample mit mindestens einem Tag zählt, auch
    wenn keiner davon behalten wird (Samples = Videoframes)."""
    out: list[dict[int, bytes]] = []
    i = 0
    while i + 28 < len(buf):
        if buf[i:i + 4] != HEADER:
            nxt = buf.find(HEADER, i + 1)
            if nxt == -1:
                break
            i = nxt
            continue
        j, werte, gefunden = i + 28, {}, False
        while j + 17 < len(buf) and buf[j:j + 4] == UL:
            ln, k = ber(buf, j + 16)
            ende = min(k + ln, len(buf))
            while k + 4 <= ende:
                t, l = struct.unpack(">HH", buf[k:k + 4])
                gefunden = True
                if (tags is None or t in tags) and t not in werte:
                    werte[t] = buf[k + 4:k + 4 + l]
                k += 4 + l
            j = ende
        if gefunden:
            out.append(werte)
        i = max(j, i + 28)
    return out


def imu_block(block: bytes, skala: float) -> np.ndarray:
    """IMU-Block → (n, 3) float64 in °/s bzw. g; leer bei n = 0, zu kleiner Probe oder Skala ≤ 0."""
    if len(block) < 8:
        return np.zeros((0, 3), np.float64)
    n, groesse = struct.unpack(">II", block[:8])
    if n == 0 or groesse < 6 or skala <= 0 or len(block) < 8 + n * groesse:
        return np.zeros((0, 3), np.float64)
    raw = np.frombuffer(block[8:8 + n * groesse], dtype=">i2")
    return raw.reshape(n, groesse // 2)[:, :3].astype(np.float64) / skala


def auswerten(sample_list: list[dict[int, bytes]]) -> RtmdDaten:
    """Samples → RtmdDaten (Gyro/Acc aneinandergehängt, Distanzen je Sample; 0xFFFF und fehlende Tags übersprungen)."""
    gyro, acc, f_ist, f_kb, fokus = [], [], [], [], []
    hz = None
    for s in sample_list:
        if TAG_GYRO in s and TAG_GYRO_SKALA in s and len(s[TAG_GYRO_SKALA]) == 4:
            gyro.append(imu_block(s[TAG_GYRO], struct.unpack(">f", s[TAG_GYRO_SKALA])[0]))
        if TAG_ACC in s and TAG_ACC_SKALA in s and len(s[TAG_ACC_SKALA]) == 4:
            acc.append(imu_block(s[TAG_ACC], struct.unpack(">f", s[TAG_ACC_SKALA])[0]))
        if hz is None and TAG_IMU_HZ in s and len(s[TAG_IMU_HZ]) == 4:
            hz = float(struct.unpack(">I", s[TAG_IMU_HZ])[0]) or None
        for tag, ziel, faktor, stellen in ((TAG_BRENNWEITE_MM, f_ist, 1000.0, 1), (TAG_KB_MM, f_kb, 1000.0, 1),
                                           (TAG_FOKUS_M, fokus, 1.0, 2)):
            if tag in s and len(s[tag]) == 2:
                v = struct.unpack(">H", s[tag])[0]
                if v != 0xFFFF:
                    ziel.append(round(distanz(v) * faktor, stellen))
    g = np.concatenate(gyro) if gyro else np.zeros((0, 3), np.float64)
    a = np.concatenate(acc) if acc else np.zeros((0, 3), np.float64)
    proben = int(gyro[0].shape[0]) if gyro else 0
    return RtmdDaten(samples=len(sample_list), imu_hz=hz, proben_je_sample=proben, gyro=g, acc=a,
                     brennweite_mm=f_ist, kb_mm=f_kb, fokus_m=fokus)


def sidecar_modell(path: str | Path) -> str | None:
    """Kameramodell aus der Sony-Sidecar ``<Clip>M01.XML`` neben der Datei (``<Device modelName="ILME-FX3"/>``)."""
    p = Path(path)
    xml = p.with_name(p.stem + "M01.XML")
    if not xml.is_file():
        return None
    try:
        for el in ET.parse(xml).iter():
            if str(el.tag).endswith("Device") and el.get("modelName"):
                return el.get("modelName")
    except ET.ParseError:
        return None
    return None


def kamera_erkennen(path: str | Path, modell: str | None = None) -> str:
    """Kamera-Kürzel: Sidecar-Modell zuerst, dann Dateinamen-Präfix (FX3_, beliebiger a7-Präfix, DJI_), sonst „unbekannt"."""
    if modell:
        if modell in MODELLE:
            return MODELLE[modell]
        return f"Sony {modell}" if modell.startswith(("ILME", "ILCE", "ZV")) else modell
    name = Path(path).name.upper()
    if name.startswith("FX3"):
        return "FX3"
    if name.startswith("A7"):
        return "a7IV"
    if name.startswith("DJI"):
        return "DJI"
    return "unbekannt"


def paket_bauen(tags: dict[int, bytes], groesse: int = 0) -> bytes:
    """Ein rtmd-Sample mit Header und einem KLV-Satz aus ``tags`` (für Tests); ``groesse`` > 0 füllt auf feste Länge auf."""
    body = b"".join(struct.pack(">HH", t, len(v)) + v for t, v in tags.items())
    laenge = bytes([len(body)]) if len(body) < 0x80 else b"\x83" + len(body).to_bytes(3, "big")
    paket = HEADER + b"\x00" * 24 + KLV_KEY + laenge + body
    if groesse > len(paket):
        paket += b"\xf0\x10\x20\x00" * ((groesse - len(paket)) // 4) + b"\x00" * ((groesse - len(paket)) % 4)
    return paket
