"""Testaufbau: Paket aus src/ importieren, Wurzeln auf Temp-Ordner, Testvideos per ffmpeg."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def wurzeln(tmp_path, monkeypatch):
    """Temp-Repo (mit projects/Kunde/Projekt/Charge), Review-Wurzel, Cache — alles über die Umgebung."""
    repo = tmp_path / "repo"
    charge = repo / "projects" / "Dold" / "Recruiting" / "2026-07 Dreh 27-28.07"
    charge.mkdir(parents=True)
    nas = tmp_path / "nas" / "NIRO Studio"
    nas.mkdir(parents=True)
    cache = tmp_path / "cache"
    monkeypatch.setenv("NIRO_STUDIO_REPO", str(repo))
    monkeypatch.setenv("NIRO_STUDIO_NAS", str(nas))
    monkeypatch.delenv("NIRO_REVIEW_ROOT", raising=False)
    monkeypatch.setenv("NIRO_REVIEW_CACHE", str(cache))
    return {"repo": repo, "charge": charge, "charge_rel": "projects/Dold/Recruiting/2026-07 Dreh 27-28.07",
            "nas": nas, "review": nas / "review", "cache": cache}


def _ffmpeg_da() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def _testvideo(ziel: Path, codec: list[str], dauer: float = 2.0) -> Path:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=size=320x180:rate=25:duration={dauer}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={dauer}", *codec, "-shortest", str(ziel)], check=True)
    return ziel


@pytest.fixture(scope="session")
def testvideo_h264(tmp_path_factory) -> Path:
    if not _ffmpeg_da():
        pytest.skip("ffmpeg fehlt")
    return _testvideo(tmp_path_factory.mktemp("medien") / "Dold 02 Fokus Bagger und Kran – Entwurf v1.mp4",
                      ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])


@pytest.fixture(scope="session")
def testvideo_mpeg4(tmp_path_factory) -> Path:
    if not _ffmpeg_da():
        pytest.skip("ffmpeg fehlt")
    return _testvideo(tmp_path_factory.mktemp("medien") / "Taxodia-Weg Messe V2.mov",
                      ["-c:v", "mpeg4", "-q:v", "3", "-c:a", "pcm_s16le"])
