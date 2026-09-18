#!/usr/bin/env python3
"""NIRO Review — Einstieg. Aufruf: python3 tools/review/review.py <Befehl> …  (Python ≥ 3.9, ffmpeg/ffprobe).

Spec: docs/superpowers/specs/2026-09-18-review-tool-design.md · Ablauf: tools/review/WORKFLOW-Review.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from niro_review.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
