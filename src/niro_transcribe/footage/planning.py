from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .move_plan import Move, MovePlan


@dataclass
class PlanResult:
    plan: MovePlan
    markdown: str
    flags: list
    balance: dict


def slug(text: str, n: int = 32) -> str:
    text = re.sub(r"[^0-9A-Za-zÄÖÜäöüß ]", "", text)
    return "-".join(text.split())[:n].strip("-")


def person_slug(name, aliases=None) -> str:
    if not name:
        return "_ohne_Namen"
    name = (aliases or {}).get(name.strip(), name.strip())
    return re.sub(r"[^0-9A-Za-zÄÖÜäöüß ._-]", "", name).strip()


def build_move_plan(clips, classifications, script, sort_root, *, aliases=None) -> PlanResult:
    sort_root = Path(sort_root)
    rowmap = {}
    titel = {}
    for v in script["videos"]:
        titel[v["nr"]] = v["titel"]
        for i, row in enumerate(v["rows"], 1):
            rowmap[row["id"]] = {"video_nr": v["nr"], "order": i, "typ": row["typ"], "text": row["text"]}

    moves = []
    flags = []
    groups = {"scripted": {}, "interview": {}, "broll": [], "nicht": []}
    for c in clips:
        name = c.path.name
        o = classifications.get(name, {}) or {}
        cat = o.get("category")
        if cat == "scripted" and o.get("row_id") in rowmap:
            r = rowmap[o["row_id"]]
            vid = r["video_nr"]
            if o.get("confidence") == "niedrig":
                flags.append(f"Gescriptet unsicher: {name} -> {o['row_id']}")
            suffix = o["row_id"].split("_", 1)[1] if "_" in o["row_id"] else o["row_id"]
            folder = f"{r['order']:02d}_{suffix}_{slug(r['text'])}"
            dst = sort_root / f"Video {vid} - {titel[vid]}" / folder / name
            groups["scripted"].setdefault(f"V{vid}/{folder}", []).append(name)
        elif cat == "scripted":
            flags.append(f"Sprech-Take ohne Script-Zeile: {name}")
            dst = sort_root / "_nicht_zugeordnet" / name
            groups["nicht"].append((name, "kein Row-Match"))
        elif cat == "interview":
            person = person_slug(o.get("person"), aliases)
            dst = sort_root / "Interviews" / person / c.camera / name
            groups["interview"].setdefault(person, []).append((name, c.camera))
            if person == "_ohne_Namen":
                flags.append(f"Interview ohne Namen: {name}")
        elif cat == "broll":
            dst = sort_root / "B-Roll" / name
            groups["broll"].append(name)
        else:
            flags.append(f"Unsicher/unbekannt: {name} ({o.get('note', '')})")
            dst = sort_root / "_nicht_zugeordnet" / name
            groups["nicht"].append((name, o.get("note", "") or "unsure"))
        moves.append(Move(str(c.path), str(dst)))

    plan = MovePlan(moves=moves)
    discovered = [str(c.path) for c in clips]
    problems = plan.validate(discovered)
    balance = {
        "clips": len(clips),
        "scripted": sum(len(v) for v in groups["scripted"].values()),
        "interview": sum(len(v) for v in groups["interview"].values()),
        "broll": len(groups["broll"]),
        "nicht": len(groups["nicht"]),
        "validate_ok": not problems,
    }

    L = [
        "# Zuordnungsplan\n",
        f"**Bilanz:** {balance['clips']} Clips = {balance['scripted']} gescriptet + "
        f"{balance['interview']} interview + {balance['broll']} b-roll + {balance['nicht']} nicht-zugeordnet\n",
        f"**validate():** {'OK (leer)' if not problems else '; '.join(problems)}\n",
        "\n## Gescriptete Szenen\n",
    ]
    for f in sorted(groups["scripted"]):
        L.append(f"- **{f}** ({len(groups['scripted'][f])}): " + ", ".join(groups["scripted"][f]))
    L.append("\n## Interviews (nach Person)\n")
    for p in sorted(groups["interview"]):
        items = groups["interview"][p]
        L.append(f"- **{p}** ({len(items)}): " + ", ".join(f"{n}[{(cam or '?').split()[0]}]" for n, cam in items))
    L.append(f"\n## B-Roll ({len(groups['broll'])})\n" + ", ".join(sorted(groups["broll"])))
    L.append(f"\n\n## _nicht_zugeordnet ({len(groups['nicht'])})\n")
    for n, d in groups["nicht"]:
        L.append(f"- {n}: {d}")
    if flags:
        L.append(f"\n## ⚠️ Bitte prüfen ({len(flags)})\n")
        for fl in flags:
            L.append(f"- {fl}")

    return PlanResult(plan=plan, markdown="\n".join(L), flags=flags, balance=balance)
