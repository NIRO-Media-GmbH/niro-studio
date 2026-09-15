"""Farbrechnung: Proxy-YUV -> S-Log3-Codewerte (Resolve-intern, CV/1023) -> CDL -> Sony-LUT -> Rec.709."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

LUTDIR = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Sony/"
KR, KB = 0.2126, 0.0722
KG = 1 - KR - KB
LUMA = np.array([KR, KG, KB])


def yuv_to_rgb(yuv):
    """yuv: uint8 (3,H,W) TV-Range Rec.709 -> float32 (H,W,3), 0..1 = S-Log3-Codewert/1023 (Befund Proxy Generator)."""
    y = (yuv[0].astype(np.float32) - 16) / 219
    pb = (yuv[1].astype(np.float32) - 128) / 224
    pr = (yuv[2].astype(np.float32) - 128) / 224
    r = y + 2 * (1 - KR) * pr
    b = y + 2 * (1 - KB) * pb
    g = (y - KR * r - KB * b) / KG
    return np.stack([r, g, b], -1)


def downscale(img, f=2):
    h, w, c = img.shape
    return img[:h // f * f, :w // f * f].reshape(h // f, f, w // f, f, c).mean(axis=(1, 3))


def load_cube(path):
    size = None; vals = []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("LUT_3D_SIZE"):
            size = int(s.split()[1]); continue
        if s[0].isalpha():
            continue
        vals.append([float(v) for v in s.split()[:3]])
    v = np.array(vals, dtype=np.float32)
    assert v.shape[0] == size ** 3
    return v.reshape(size, size, size, 3)  # [b,g,r]


def apply_lut(rgb, lut):
    """Trilinear (Resolve-Standard: 'Trilinear' in Projekteinstellungen)."""
    n = lut.shape[0]
    x = np.clip(rgb, 0, 1) * (n - 1)
    i0 = np.clip(np.floor(x).astype(np.int32), 0, n - 2)
    f = (x - i0).astype(np.float32)
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]
    def c(db, dg, dr):
        return lut[b0 + db, g0 + dg, r0 + dr]
    c0 = (c(0, 0, 0) * (1 - fr) + c(0, 0, 1) * fr) * (1 - fg) + (c(0, 1, 0) * (1 - fr) + c(0, 1, 1) * fr) * fg
    c1 = (c(1, 0, 0) * (1 - fr) + c(1, 0, 1) * fr) * (1 - fg) + (c(1, 1, 0) * (1 - fr) + c(1, 1, 1) * fr) * fg
    return c0 * (1 - fb) + c1 * fb


def cdl(rgb, slope=(1, 1, 1), offset=(0, 0, 0), power=(1, 1, 1), sat=1.0, clamp=True):
    """ASC CDL v1.2: out = clamp(in*slope+offset)^power, danach Saettigung mit Rec.709-Luma."""
    x = rgb * np.asarray(slope, np.float32) + np.asarray(offset, np.float32)
    if clamp:
        x = np.clip(x, 0, 1)
    else:
        x = np.maximum(x, 0)
    x = x ** np.asarray(power, np.float32)
    if sat != 1.0:
        l = (x * LUMA.astype(np.float32)).sum(-1, keepdims=True)
        x = l + sat * (x - l)
        if clamp:
            x = np.clip(x, 0, 1)
    return x


def slog3_to_lin(v):
    """S-Log3 (CV/1023) -> Szene linear (0.18 = 18 % Grau)."""
    v = np.asarray(v, np.float64)
    return np.where(v >= 171.2102946929 / 1023,
                    10 ** ((v * 1023 - 420) / 261.5) * 0.19 - 0.01,
                    (v * 1023 - 95) * 0.01125 / (171.2102946929 - 95))


def lin_to_slog3(x):
    x = np.asarray(x, np.float64)
    return np.where(x >= 0.01125, (420 + np.log10((x + 0.01) / 0.19) * 261.5) / 1023,
                    (x * (171.2102946929 - 95) / 0.01125 + 95) / 1023)


STOP = 261.5 * np.log10(2) / 1023  # S-Log3: eine Blende = 0.07695 im normierten Codewert


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def srgb_view(rgb709):
    """Rec.709-Displaysignal (Gamma 2.4-Monitor) wird fuer JPG unveraendert als sRGB-Code gespeichert
    (so wie ein Resolve-Export 'Rec.709 Gamma 2.4' auf einem Rechner-Viewer aussieht)."""
    return to_u8(rgb709)


def font(size):
    for p in ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def label(im, text, size=22, pos=(8, 6)):
    d = ImageDraw.Draw(im)
    f = font(size)
    x, y = pos
    bb = d.textbbox((x, y), text, font=f)
    d.rectangle([bb[0] - 5, bb[1] - 3, bb[2] + 5, bb[3] + 3], fill=(0, 0, 0))
    d.text((x, y), text, fill=(255, 255, 255), font=f)
    return im


# ---- Farbmetrik: Rec.709-Displaysignal (BT.1886, Gamma 2.4) -> CIELAB (D65) ----
M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def disp_to_lab(rgb):
    lin = np.clip(np.asarray(rgb, np.float64), 0, 1) ** 2.4
    xyz = lin @ M709.T / WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de2000(lab1, lab2):
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, float), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, float), -1, 0)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(np.abs(dh) > 180, dh - 360 * np.sign(dh), dh)
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    hsum = h1p + h2p
    hpm = np.where(np.abs(h1p - h2p) > 180, (hsum + 360) / 2, hsum / 2)
    hpm = np.where(C1p * C2p == 0, hsum, hpm)
    T = 1 - 0.17 * np.cos(np.radians(hpm - 30)) + 0.24 * np.cos(np.radians(2 * hpm)) + 0.32 * np.cos(np.radians(3 * hpm + 6)) - 0.20 * np.cos(np.radians(4 * hpm - 63))
    dtheta = 30 * np.exp(-((hpm - 275) / 25) ** 2)
    Rc = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / np.sqrt(20 + (Lpm - 50) ** 2)
    Sc = 1 + 0.045 * Cpm
    Sh = 1 + 0.015 * Cpm * T
    Rt = -np.sin(np.radians(2 * dtheta)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))
