"""Timeline-Offsets: alle 51 Szenen als EIN durchgehendes Video (DaVinci).

Annahme (mit David verifizieren): Reihenfolge A → M → S → TA → TP, innerhalb
der Gruppe natürlich sortiert (TA2 vor TA10), Stoß an Stoß ohne Lücken.
Dauern = echte Container-Dauern (ffprobe), `_intern/clip_durations.json`.

Ausgabe: `_intern/timeline_offsets.json` + `Ergebnisse/Transkripte/00-timeline-referenz.md`
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CHARGE = Path(__file__).resolve().parent.parent
DURATIONS = CHARGE / "_intern" / "clip_durations.json"
OUT_JSON = CHARGE / "_intern" / "timeline_offsets.json"
OUT_MD = CHARGE / "Ergebnisse" / "Transkripte" / "00-timeline-referenz.md"

GROUP_ORDER = ["A", "M", "S", "TA", "TP"]


def mmss(sec: float) -> str:
    total = int(sec)  # abschneiden, nie hinter den Moment zeigen (wie Transkripte)
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def natural_key(name: str) -> tuple[int, int]:
    m = re.fullmatch(r"([A-Z]+)(\d+)", name)
    return (GROUP_ORDER.index(m.group(1)), int(m.group(2)))


def build() -> dict[str, dict]:
    durs = json.loads(DURATIONS.read_text(encoding="utf-8"))
    order = sorted(durs, key=natural_key)
    offsets: dict[str, dict] = {}
    t = 0.0
    for name in order:
        offsets[name] = {"start": t, "end": t + durs[name], "dur": durs[name]}
        t += durs[name]
    return offsets


def main() -> None:
    offsets = build()
    OUT_JSON.write_text(json.dumps(offsets, ensure_ascii=False, indent=1), encoding="utf-8")

    total = max(v["end"] for v in offsets.values())
    lines = [
        "# Timeline-Referenz — alle Szenen als EIN Video",
        "",
        "Annahme: DaVinci-Timeline in Reihenfolge **A → M → S → TA → TP**, innerhalb",
        "der Gruppe aufsteigend (TA2 vor TA10), Clips Stoß an Stoß, keine Lücken.",
        "Dauern = echte Dateilängen (ffprobe). **Schnell-Check:** Stimmt der Start",
        "einer späten Szene (z. B. TP9) mit deiner Timeline überein? Wenn nicht →",
        "Reihenfolge melden, Tabelle wird neu gerechnet.",
        "",
        f"**Gesamtlänge: {mmss(total)}** · Sekundengenau — Feinschnitt nach Wellenform.",
        "",
        "| Szene | Timeline-Start | Timeline-Ende | Clip-Dauer |",
        "|---|---|---|---|",
    ]
    for name, o in offsets.items():
        lines.append(f"| {name} | {mmss(o['start'])} | {mmss(o['end'])} | {mmss(o['dur'])} |")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"geschrieben: {OUT_MD}")
    print(f"Gesamt: {mmss(total)}")


if __name__ == "__main__":
    main()
