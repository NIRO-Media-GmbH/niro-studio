"""Review in Dropbox Replay (Spec docs/superpowers/specs/2026-09-16-autocut-replay-design.md): Replay-Titel,
Versionsnamen, Replay-Ordner, Bitrate-Grenze und das Upload-Log ``<Charge>/_intern/replay/uploads.json``.

Reine Logik ohne Resolve; das Hochladen selbst steht in ``scripts/autocut_replay.py``.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path

from .charge import AutoCutError, Charge

UPLOADS = "uploads.json"
_UNSICHER = re.compile(r'[/\\:*?"<>|]+')
_VERSION = (re.compile(r"^(.*_V)(\d+)$"), re.compile(r"^(.* V)(\d+)$"))


def jetzt() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def replay_dir(ch: Charge) -> Path:
    return ch.intern / "replay"


def titel(timeline: str) -> str:
    """Timeline-Name → Replay-Titel und Dateiname (Replay zeigt ihn mit „.mp4"): ohne / \\ : * ? " < > |."""
    t = _UNSICHER.sub("-", str(timeline)).strip()
    if not t:
        raise AutoCutError(f"Aus dem Timeline-Namen {timeline!r} entsteht kein Dateiname.")
    return t


def naechste_version(name: str) -> str:
    """Kundenschema „…_V3" → „…_V4"; „… V2" → „… V3"; sonst „<Name> V2" (Spec Abschnitt 3)."""
    for muster in _VERSION:
        m = muster.match(name)
        if m:
            return f"{m.group(1)}{int(m.group(2)) + 1}"
    return f"{name} V2"


def replay_ordner(ch: Charge) -> str:
    """Replay-Pfad aus ``replay.ordner`` mit Kunde und Projekt der Charge, z. B. „Autocut/Kunde/Projekt"."""
    teile = (ch.config.get("replay") or {}).get("ordner") or ["Autocut", "{kunde}", "{projekt}"]
    return "/".join(str(t).format(kunde=ch.kunde, projekt=ch.projekt) for t in teile)


def video_quality(breite, hoehe, cfg: dict) -> int:
    """Bitrate-Grenze (kbit/s) für den Quick Export: nur bei Timelines über 1920 px; 0 = automatisch."""
    if max(int(breite or 0), int(hoehe or 0)) > 1920:
        return int(cfg.get("video_quality_ueber_1080p") or 0)
    return 0


def lade_uploads(ch: Charge) -> list[dict]:
    p = replay_dir(ch) / UPLOADS
    if not p.exists():
        return []
    daten = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(daten, list):
        raise AutoCutError(f"{p} ist keine Liste — Datei prüfen (nicht von Hand überschreiben).")
    return daten


def _schreibe_uploads(ch: Charge, eintraege: list[dict]) -> Path:
    p = replay_dir(ch) / UPLOADS
    ch.assert_writable(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(eintraege, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def speichere_upload(ch: Charge, eintrag: dict) -> Path:
    return _schreibe_uploads(ch, lade_uploads(ch) + [dict(eintrag)])


def upload_eintrag(ch: Charge, timeline: str | None = None, titel_: str | None = None) -> dict:
    """Jüngster Upload (optional zu Timeline oder Titel); AutoCutError, wenn keiner passt."""
    eintraege = [e for e in lade_uploads(ch)
                 if (timeline is None or e.get("timeline") == timeline) and (titel_ is None or e.get("titel") == titel_)]
    if not eintraege:
        wofuer = f" für '{timeline or titel_}'" if (timeline or titel_) else ""
        raise AutoCutError(f"Kein Upload{wofuer} in {replay_dir(ch) / UPLOADS} — erst 'autocut_replay.py ... hochladen'.")
    return max(eintraege, key=lambda e: str(e.get("hochgeladen_am") or ""))


def setze_einsortiert(ch: Charge, titel_: str, ordner: str, zeit: str | None = None) -> dict:
    """Einsortieren in Replay vermerken (jüngster Eintrag mit diesem Titel)."""
    eintraege = lade_uploads(ch)
    passend = [i for i, e in enumerate(eintraege) if e.get("titel") == titel_]
    if not passend:
        raise AutoCutError(f"Titel '{titel_}' steht nicht in {replay_dir(ch) / UPLOADS}.")
    i = max(passend, key=lambda j: str(eintraege[j].get("hochgeladen_am") or ""))
    eintraege[i]["replay_ordner"] = ordner
    eintraege[i]["einsortiert_am"] = zeit or jetzt()
    _schreibe_uploads(ch, eintraege)
    return eintraege[i]


def nicht_einsortiert(ch: Charge) -> list[dict]:
    return [e for e in lade_uploads(ch) if e.get("upload_status") == "Upload Completed" and not e.get("einsortiert_am")]


def ist_hochgeladen(charge_root, timeline: str) -> bool:
    """Steht die Timeline im Upload-Log der Charge? (Finalisieren behält sie dann.) Kaputtes Log → True."""
    p = Path(charge_root) / "_intern" / "replay" / UPLOADS
    if not p.exists():
        return False
    try:
        daten = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    return any(isinstance(e, dict) and e.get("timeline") == timeline for e in daten)


def finde_upload(projekt_ordner, replay_titel: str) -> tuple[Path, dict] | None:
    """Replay-Titel (mit oder ohne „.mp4") → (Chargen-Ordner, jüngster Upload) über alle Chargen des Projekts."""
    t = replay_titel[:-4] if replay_titel.lower().endswith(".mp4") else replay_titel
    treffer = []
    for p in sorted(Path(projekt_ordner).glob(f"*/_intern/replay/{UPLOADS}")):
        for e in json.loads(p.read_text(encoding="utf-8")):
            if isinstance(e, dict) and e.get("titel") == t:
                treffer.append((str(e.get("hochgeladen_am") or ""), p.parents[2], e))
    if not treffer:
        return None
    _, charge, e = max(treffer, key=lambda x: x[0])
    return charge, e


def feedback_ordner(ch: Charge, eintrag: dict) -> Path:
    """``Material/Feedback/<Upload-Datum> Replay <Titel>/``."""
    datum = str(eintrag.get("hochgeladen_am") or jetzt())[:10]
    return ch.root / "Material" / "Feedback" / f"{datum} Replay {eintrag['titel']}"
