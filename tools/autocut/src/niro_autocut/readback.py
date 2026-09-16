"""Bau-Readback (Spec 2026-09-16 Abschnitt 2.5): Stand einer Timeline direkt nach dem Bau als Schnappschuss unter
``_intern/autocut/readback/<Titel>.json`` — Grundlage für „seit dem Bau von Hand geändert?" in der Replay-Runde.
Resolve wird nur gelesen."""
from __future__ import annotations

import json
from pathlib import Path

from .kanten import snapshot_from_readback
from .replay import titel


def pfad(ch, timeline: str) -> Path:
    return ch.autocut / "readback" / f"{titel(timeline)}.json"


def schreiben(ch, session, timeline) -> Path:
    """Timeline lesen → Schnappschuss (Frames relativ zum Start) + Marker → Datei."""
    tl = session.read_timeline(timeline)
    snap = snapshot_from_readback(tl, session.project_name)
    snap["marker"] = tl.get("markers") or {}
    p = pfad(ch, str(tl["name"]))
    ch.assert_writable(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def laden(ch, timeline: str) -> dict | None:
    p = pfad(ch, timeline)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
