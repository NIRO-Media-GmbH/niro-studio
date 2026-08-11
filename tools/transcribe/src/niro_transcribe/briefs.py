from __future__ import annotations

from pathlib import Path
import yaml
from .models import VideoBrief, GlobalConfig


def load_briefs(path: str | Path) -> tuple[list[VideoBrief], GlobalConfig]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    g = data.get("global", {}) or {}
    gconf = GlobalConfig(
        wiederverwendung=g.get("wiederverwendung", "exklusiv"),
        anzahl_videos=g.get("anzahl_videos"),
    )
    briefs: list[VideoBrief] = []
    for v in data.get("videos", []) or []:
        briefs.append(
            VideoBrief(
                titel=v["titel"],
                fokus=v["fokus"],
                person=v["person"],
                ziel_laenge_sek=v.get("ziel_laenge_sek"),
                dramaturgie=v.get("dramaturgie"),
                tonalitaet=v.get("tonalitaet"),
            )
        )
    return briefs, gconf
