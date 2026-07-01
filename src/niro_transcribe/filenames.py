from __future__ import annotations

import re
from pathlib import Path
from .models import InterviewMeta


def guess_meta(filename: str) -> InterviewMeta:
    stem = Path(filename).stem
    parts = [p for p in re.split(r"[_\-\s]+", stem) if p]
    if len(parts) >= 3:
        typ, name, bereich = parts[0], parts[-1], " ".join(parts[1:-1])
    elif len(parts) == 2:
        typ, name, bereich = parts[0], parts[1], ""
    elif len(parts) == 1:
        typ, name, bereich = "", parts[0], ""
    else:
        typ = name = bereich = ""
    return InterviewMeta(quelldatei=filename, typ=typ, bereich=bereich, name=name)
