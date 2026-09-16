"""Schnittbild: Filmstreifen, Pegelband, Wörter und Schnittlinien eines Zeitbereichs als ein PNG (Spec 2026-09-16, 4).

Idee und Grundlayout nach browser-use/video-use, helpers/timeline_view.py (MIT License, Copyright (c) 2026 Browser Use).
Eigene Umsetzung: Pegel in dBFS statt normierter Wellenform, Wörter in zwei Zeilen, Bild- und Ton-Schnittlinien,
Befund-Marken und Timecode-Leiste.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .charge import AutoCutError
from .kanten import timecode
from .media import _which

BREITE, RAND = 1920, 50
KOPF_Y, LABEL_Y, STREIFEN_Y, STREIFEN_H = 10, 42, 60, 180
WORT_Y = STREIFEN_Y + STREIFEN_H + 14
PEGEL_Y, PEGEL_H = WORT_Y + 40, 200
LEISTE_Y = PEGEL_Y + PEGEL_H + 8
HOEHE = LEISTE_Y + 56
DB_MIN = -60.0
HG, ZELLE, TEXT, DIM = (18, 18, 22), (28, 28, 34), (235, 235, 235), (125, 125, 135)
PEGEL, PAUSE = (140, 180, 255), (60, 100, 150, 90)
BILD_LINIE, TON_LINIE, MARKE = (0, 200, 220), (255, 150, 40), (235, 60, 60)
SCHRIFTEN = ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Helvetica.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")


def _schrift(groesse: int):
    for p in SCHRIFTEN:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, groesse)
            except OSError:
                continue
    return ImageFont.load_default()


def _standbild(video: Path, t: float, ziel: Path) -> Image.Image | None:
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
           "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "4", str(ziel)]
    if subprocess.run(cmd, capture_output=True).returncode != 0 or not ziel.exists():
        return None
    with Image.open(ziel) as im:
        return im.convert("RGB")


def pegel_db(video, von_s: float, bis_s: float, schritt_s: float = 0.01) -> np.ndarray:
    """RMS in dBFS je ``schritt_s`` (Mono-Mix, 16 kHz); ohne Ton oder bei Fehler ein leeres Array."""
    sr = 16000
    cmd = [_which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, von_s):.3f}", "-i", str(video),
           "-t", f"{max(0.01, bis_s - von_s):.3f}", "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le",
           "-acodec", "pcm_f32le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return np.zeros(0)
    x = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
    n = max(1, int(round(schritt_s * sr)))
    k = x.size // n
    if k == 0:
        return np.zeros(0)
    rms = np.sqrt(np.mean(x[: k * n].reshape(k, n) ** 2, axis=1))
    return np.maximum(20.0 * np.log10(np.maximum(rms, 1e-10)), -200.0)


def zeichne(video, von_s: float, bis_s: float, ausgabe, *, woerter=(), bild_schnitte=(), ton_schnitte=(), marken=(),
            frames: int = 10, beschriftung: str | None = None, tc_start: str | None = None,
            fps: float | None = None) -> Path:
    """PNG für [von_s, bis_s] (Sekunden in ``video``).

    ``woerter``: Dicts mit ``text``/``start``/``end`` in denselben Sekunden; ``bild_schnitte``/``ton_schnitte``:
    Sekunden; ``marken``: (Sekunde, Kurztext). Mit ``tc_start`` und ``fps`` zeigen Kopf, Frames und Leiste Timecodes
    (Sekunde 0 = ``tc_start``).
    """
    video, ausgabe = Path(video), Path(ausgabe)
    if not video.is_file():
        raise AutoCutError(f"Schnittbild: Datei nicht gefunden: {video}")
    if bis_s <= von_s:
        raise AutoCutError(f"Schnittbild: Ende {bis_s:.2f} s liegt nicht nach dem Anfang {von_s:.2f} s.")
    frames = max(1, int(frames))
    spanne = bis_s - von_s
    x0, x1 = RAND, BREITE - RAND

    def x_von(t: float) -> int:
        return int(round(x0 + (t - von_s) / spanne * (x1 - x0)))

    def zeit(t: float) -> str:
        return timecode(int(round(t * fps)), fps, tc_start) if (tc_start and fps) else f"{t:.2f}s"

    def y_db(v: float) -> int:
        return PEGEL_Y + PEGEL_H - int(round((max(DB_MIN, min(0.0, v)) - DB_MIN) / -DB_MIN * PEGEL_H))

    bild = Image.new("RGB", (BREITE, HOEHE), HG)
    z = ImageDraw.Draw(bild, "RGBA")
    gross, klein = _schrift(22), _schrift(13)
    kopf = f"{video.name}   {zeit(von_s)} → {zeit(bis_s)}   ({spanne:.2f} s)"
    if beschriftung:
        kopf += f"   · {beschriftung}"
    z.text((RAND, KOPF_Y), kopf, fill=TEXT, font=gross)

    # 1. Filmstreifen
    zelle = (x1 - x0 - 4 * (frames - 1)) // frames
    zeiten = [von_s + spanne / 2] if frames == 1 else [von_s + i * spanne / (frames - 1) for i in range(frames)]
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(zeiten):
            cx = x0 + i * (zelle + 4)
            z.rectangle((cx, STREIFEN_Y, cx + zelle, STREIFEN_Y + STREIFEN_H), fill=ZELLE)
            z.text((cx, LABEL_Y), zeit(t), fill=DIM, font=klein)
            t_bild = max(von_s, bis_s - 0.05) if (frames > 1 and i == frames - 1) else t
            im = _standbild(video, t_bild, Path(tmp) / f"{i:03d}.jpg")
            if im is None:
                continue
            sk = min(zelle / im.width, STREIFEN_H / im.height)
            im = im.resize((max(1, int(im.width * sk)), max(1, int(im.height * sk))), Image.LANCZOS)
            bild.paste(im, (cx + (zelle - im.width) // 2, STREIFEN_Y + (STREIFEN_H - im.height) // 2))

    # 2. Pegelband mit Pausen ≥ 400 ms
    z.rectangle((x0, PEGEL_Y, x1, PEGEL_Y + PEGEL_H), fill=ZELLE)
    gueltig = [w for w in woerter if w.get("start") is not None and w.get("end") is not None]
    ende = None
    for s, e in sorted((float(w["start"]), float(w["end"])) for w in gueltig):
        if ende is not None and s - ende >= 0.4 and s > von_s and ende < bis_s:
            z.rectangle((x_von(max(ende, von_s)), PEGEL_Y, x_von(min(s, bis_s)), PEGEL_Y + PEGEL_H), fill=PAUSE)
        ende = e if ende is None else max(ende, e)
    for linie in (-20.0, -40.0):
        y = y_db(linie)
        z.line((x0, y, x1, y), fill=(70, 70, 80), width=1)
        z.text((x1 + 6, y - 8), f"{int(linie)}", fill=DIM, font=klein)
    db = pegel_db(video, von_s, bis_s)
    pts = [(x_von(von_s + (i + 0.5) * 0.01), y_db(float(v))) for i, v in enumerate(db)
           if von_s + (i + 0.5) * 0.01 <= bis_s]
    if len(pts) > 1:
        z.polygon(pts + [(pts[-1][0], PEGEL_Y + PEGEL_H), (pts[0][0], PEGEL_Y + PEGEL_H)], fill=(*PEGEL, 80))
        z.line(pts, fill=PEGEL, width=1)

    # 3. Wörter in zwei Zeilen
    frei = [-10**6, -10**6]
    for w in sorted(gueltig, key=lambda w: float(w["start"])):
        s, e = float(w["start"]), float(w["end"])
        text = str(w.get("text") or "").strip()
        if not text or e < von_s or s > bis_s:
            continue
        x = x_von(max(s, von_s))
        breite = int(z.textlength(text, font=klein))
        for zeile in (0, 1):
            if x >= frei[zeile]:
                z.text((x, WORT_Y + zeile * 18), text, fill=TEXT, font=klein)
                frei[zeile] = x + breite + 6
                break
        z.line((x, PEGEL_Y - 5, x, PEGEL_Y), fill=DIM, width=1)

    # 4. Schnitte und Befund-Marken
    for t in bild_schnitte:
        if von_s <= t <= bis_s:
            x = x_von(t)
            z.line((x, STREIFEN_Y + STREIFEN_H + 2, x, PEGEL_Y + PEGEL_H), fill=BILD_LINIE, width=2)
    for t in ton_schnitte:
        if von_s <= t <= bis_s:
            x = x_von(t) + 2
            z.line((x, PEGEL_Y, x, PEGEL_Y + PEGEL_H), fill=TON_LINIE, width=2)
    for t, text in marken:
        if von_s <= t <= bis_s:
            x = x_von(t)
            for y in range(STREIFEN_Y, PEGEL_Y + PEGEL_H, 8):
                z.line((x, y, x, min(y + 4, PEGEL_Y + PEGEL_H)), fill=MARKE, width=2)
            z.text((x + 6, PEGEL_Y + 4), str(text), fill=MARKE, font=klein)

    # 5. Zeitleiste und Legende
    for i in range(7):
        t = von_s + i * spanne / 6
        x = x_von(t)
        z.line((x, LEISTE_Y, x, LEISTE_Y + 6), fill=DIM, width=1)
        z.text((max(0, x - 40), LEISTE_Y + 9), zeit(t), fill=DIM, font=klein)
    z.text((RAND, LEISTE_Y + 32), "cyan Bild-Schnitt · orange Ton-Schnitt · rot Befund · blau Pause ≥ 400 ms · "
           "Pegel −60…0 dBFS (Linien −20/−40)", fill=DIM, font=klein)
    ausgabe.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ausgabe, "PNG", optimize=True)
    return ausgabe
