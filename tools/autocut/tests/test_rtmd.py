"""rtmd.py — Sony-Datenspur: BER, RDD-18-Distanz, Sample-Parser, IMU-Blöcke, Auswertung, Sidecar, Kamera (ohne NAS)."""
from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest

from niro_autocut import rtmd as R

FIXTURES = Path(__file__).parent / "fixtures"


def _imu(werte: list[tuple[int, int, int]], groesse: int = 6) -> bytes:
    """IMU-Block wie in der Kamera: n (u32), groesse (u32), dann n × groesse Bytes, je Probe int16 x, y, z."""
    out = struct.pack(">II", len(werte), groesse)
    for x, y, z in werte:
        out += struct.pack(">hhh", x, y, z) + b"\x00" * (groesse - 6)
    return out


def test_ber_kurz_und_lang():
    assert R.ber(b"\x24", 0) == (36, 1)
    assert R.ber(b"\x83\x00\x00\x24", 0) == (36, 4)


def test_distanz_rdd18():
    # Werte aus FX3_0330 (Nachtrag 21.09.): 0xc2cc → 71,6 mm KB, 0xc2a5 → 67,7 mm, 0xe62e → 15,82 m Fokus
    assert round(R.distanz(0xC2CC) * 1000, 1) == 71.6
    assert round(R.distanz(0xC2A5) * 1000, 1) == 67.7
    assert round(R.distanz(0xE62E), 2) == 15.82


def test_samples_parst_zwei_pakete_mit_fuellung():
    a = R.paket_bauen({0x8004: bytes.fromhex("c2cc"), 0x8005: bytes.fromhex("c2a5")}, groesse=256)
    b = R.paket_bauen({0x8004: bytes.fromhex("c2a5")}, groesse=256)
    s = R.samples(a + b)
    assert len(s) == 2 and s[0][0x8004] == bytes.fromhex("c2cc") and s[1][0x8004] == bytes.fromhex("c2a5")


def test_samples_ueberspringt_muell_vor_dem_header():
    p = R.paket_bauen({0x8004: bytes.fromhex("c2cc")})
    assert len(R.samples(b"\xf0\x10\x20\x00" + p)) == 1
    assert R.samples(b"") == [] and R.samples(b"\x00\x1c\x01\x00") == []


def test_imu_block_skaliert_und_liest_nur_xyz():
    blk = _imu([(655, -131, 65), (0, 0, 0)], groesse=8)
    g = R.imu_block(blk, 65.5)
    assert g.shape == (2, 3) and np.allclose(g[0], [10.0, -2.0, 65/65.5]) and np.allclose(g[1], 0)
    assert R.imu_block(struct.pack(">II", 0, 6), 65.5).shape == (0, 3)


def test_auswerten_gyro_acc_hz_brennweite_fokus():
    tags = {R.TAG_GYRO: _imu([(655, 0, 0)] * 4), R.TAG_GYRO_SKALA: struct.pack(">f", 65.5),
            R.TAG_ACC: _imu([(0, 8192, 0)] * 4), R.TAG_ACC_SKALA: struct.pack(">f", 8192.0),
            R.TAG_IMU_HZ: struct.pack(">I", 2000), R.TAG_KB_MM: bytes.fromhex("c2cc"),
            R.TAG_BRENNWEITE_MM: bytes.fromhex("c2a5"), R.TAG_FOKUS_M: bytes.fromhex("e62e")}
    d = R.auswerten(R.samples(R.paket_bauen(tags) + R.paket_bauen(tags)))
    assert d.samples == 2 and d.imu_hz == 2000.0 and d.proben_je_sample == 4
    assert d.gyro.shape == (8, 3) and np.allclose(d.gyro[:, 0], 10.0)
    assert d.acc.shape == (8, 3) and np.allclose(d.acc[:, 1], 1.0)
    assert d.kb_mm == [71.6, 71.6] and d.brennweite_mm == [67.7, 67.7] and d.fokus_m == [15.82, 15.82]


def test_auswerten_ohne_imu_und_mit_ffff():
    d = R.auswerten(R.samples(R.paket_bauen({R.TAG_KB_MM: b"\xff\xff"})))
    assert d.samples == 1 and d.imu_hz is None and d.gyro.shape == (0, 3) and d.kb_mm == []


def test_sidecar_modell_und_kamera(tmp_path):
    clip = tmp_path / "FX3_0330.MP4"
    clip.write_bytes(b"x")
    (tmp_path / "FX3_0330M01.XML").write_text(
        '<?xml version="1.0"?><NonRealTimeMeta xmlns="urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.20">'
        '<Device manufacturer="Sony" modelName="ILME-FX3" serialNo="1"/></NonRealTimeMeta>', encoding="utf-8")
    assert R.sidecar_modell(clip) == "ILME-FX3"
    assert R.sidecar_modell(tmp_path / "ohne.MP4") is None
    assert R.kamera_erkennen(clip, "ILME-FX3") == "FX3"
    assert R.kamera_erkennen("a7MK4_20260913_2128.MP4", "ILCE-7M4") == "a7IV"
    assert R.kamera_erkennen("a7MK4_20260913_2128.MP4") == "a7IV"
    assert R.kamera_erkennen("DJI_0504.MOV") == "DJI"
    assert R.kamera_erkennen("C0001.MP4", "ILME-FX30") == "Sony ILME-FX30"
    assert R.kamera_erkennen("C0001.MP4") == "unbekannt"


@pytest.mark.parametrize("name,fps,proben", [("rtmd_fx3_25p.bin", 25.0, 80), ("rtmd_a7iv_50p.bin", 50.0, 40)])
def test_echte_datenspur(name, fps, proben):
    """Echte 0,3-s-Auszüge (Task 7 legt sie an) — bis dahin übersprungen."""
    f = FIXTURES / name
    if not f.exists():
        pytest.skip(f"{name} fehlt (Kalibrierlauf Task 7)")
    d = R.auswerten(R.samples(f.read_bytes()))
    assert d.samples >= 5 and d.imu_hz == 2000.0 and d.proben_je_sample == proben
    assert d.gyro.shape[0] == d.samples * proben and np.abs(d.gyro).max() < 500
    betrag = np.linalg.norm(d.acc, axis=1)
    assert 0.8 < np.median(betrag) < 1.3          # a7 IV ≈ 1,0 g, FX3 ≈ 1,15 g
    assert 10 < np.median(d.kb_mm) < 600
