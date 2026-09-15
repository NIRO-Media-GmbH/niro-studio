"""Dreh-01-Tonfrage: 60s-Sample aus Jan- (A7iv) und Bennet-Take (A7c) transkribieren.

Schneidet per ffmpeg (stream copy) 60 s aus der Mitte der jeweils größten Datei,
transkribiert beide Samples und druckt Wortzahl + Textanfang zum Vergleich.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

import os
for line in (TOOL / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip, find_sidecar
from niro_transcribe.footage.transcribe_clips import transcribe_clip

NAS = Path(
    "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/01_Kunden/"
    "MAN Truck and Bus/02_Projekte/01_Projekt-TikTok-Ads_April_2023/03_Medien/01_Footage"
)
SAMPLES = {
    "jan-a7iv": (NAS / "01 Cam - A7iv - Jan/Hauptkamera20230421_0830.MP4", "00:09:00"),
    "bennet-a7c": (NAS / "02 Cam - A7c - Bennet/Video/C3668.MP4", "00:08:00"),
}
HERE = Path(__file__).parent
work = HERE / "work"
work.mkdir(exist_ok=True)

for label, (src, mid) in SAMPLES.items():
    sample = work / f"sample_{label}.MP4"
    if not sample.exists():
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", mid,
             "-i", str(src), "-t", "60", "-c", "copy", str(sample)],
            check=True)
    clip = Clip(path=sample, camera=label, sidecar=find_sidecar(sample))
    t = transcribe_clip(clip, cache=TranscriptCache(HERE / "cache-samples"),
                        api_key=os.environ["ELEVENLABS_API_KEY"], work_dir=work)
    speakers = sorted({w.speaker for w in t.words if w.speaker})
    print(f"\n===== {label} ({src.name}, ab {mid}) =====")
    print(f"{len(t.words)} Wörter, Sprecher: {speakers}")
    print(t.text[:600])
