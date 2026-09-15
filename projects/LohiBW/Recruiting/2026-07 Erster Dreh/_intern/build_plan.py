"""Phase 2: Klassifikations-Ergebnisse -> Manifest (MovePlan) + Zuordnungsplan.
Verschiebt NICHTS. Prueft Vollstaendigkeit via MovePlan.validate."""
from __future__ import annotations

import json
import re
from pathlib import Path

from niro_transcribe.footage.discover import discover_clips
from niro_transcribe.footage.move_plan import Move, MovePlan

FOOTAGE = Path("/Volumes/NIRO-SSD-02/Lohi Backup/01_Footage")
SORT = Path("/Volumes/NIRO-SSD-02/Lohi Backup/sortiert")
PROJ = Path("projects/LohiBW Recruiting")

idx = {r["name"]: r for r in json.load(open(PROJ / "transcripts_index.json"))}
script = json.load(open(PROJ / "script_structured.json"))
# row_id -> (video_nr, titel, order, typ, text)
rowmap = {}
titel = {}
for v in script["videos"]:
    titel[v["nr"]] = v["titel"]
    for i, row in enumerate(v["rows"], 1):
        rowmap[row["id"]] = {"video_nr": v["nr"], "order": i, "typ": row["typ"], "text": row["text"]}


def slug(text: str, n: int = 32) -> str:
    text = re.sub(r"[^0-9A-Za-zÄÖÜäöüß ]", "", text)
    text = "-".join(text.split())
    return text[:n].strip("-")


# ASR-Schreibvarianten desselben Menschen zusammenführen (Nachnamen unsicher)
ALIAS = {
    "Suzan Baözen": "Suzan Baüsen",
    "Suzan Baüzen": "Suzan Baüsen",
}


def person_slug(name):
    if not name:
        return "_ohne_Namen"
    name = ALIAS.get(name.strip(), name.strip())
    return re.sub(r"[^0-9A-Za-zÄÖÜäöüß ._-]", "", name).strip()


clips = discover_clips(FOOTAGE)
by_name = {c.path.name: c for c in clips}
assert len(clips) == 135, len(clips)

# Alle Klassifikationen einsammeln
cls = {}
for b in ["batch1", "batch2", "batch3", "batch4"]:
    for o in json.load(open(PROJ / "cls" / f"{b}.json")):
        cls[o["name"]] = o
interviews = {o["name"]: o for o in json.load(open(PROJ / "cls" / "interviews.json"))}

moves = []
plan_rows = {"scripted": {}, "interview": {}, "broll": [], "nicht": []}
flags = []


def dst_for(name) -> tuple[Path, str, str]:
    """gibt (ziel, kategorie, detail)"""
    c = by_name[name]
    # Interview-Master (A/B)
    if name in interviews:
        o = interviews[name]
        person = o.get("person")
        note = (o.get("note") or "").lower()
        if not person or "interstitial" in note or "not an interview" in note or "kein interview" in note:
            if not person:
                flags.append(f"Interview ohne Namen: {name} ({o.get('note','')})")
            person = person_slug(person)
        else:
            person = person_slug(person)
        d = SORT / "Interviews" / person / c.camera / name
        return d, "interview", person
    # C-Clips
    o = cls.get(name, {})
    cat = o.get("category")
    if cat == "scripted" and o.get("row_id") in rowmap:
        r = rowmap[o["row_id"]]
        conf = o.get("confidence", "?")
        if conf == "niedrig" or (o.get("note") and "ambig" in (o.get("note") or "").lower()):
            flags.append(f"Gescriptet unsicher/mehrdeutig: {name} -> {o['row_id']} ({conf}) {o.get('note','')}")
        vid = r["video_nr"]
        folder = f"{r['order']:02d}_{o['row_id'].split('_',1)[1]}_{slug(r['text'])}"
        d = SORT / f"Video {vid} - {titel[vid]}" / folder / name
        return d, "scripted", f"V{vid}/{folder}"
    if cat == "scripted":  # scripted, aber keine Script-Zeile
        flags.append(f"Sprech-Take ohne passende Script-Zeile: {name} '{o.get('spoken_excerpt','')[:80]}'")
        return SORT / "_nicht_zugeordnet" / name, "nicht", "kein Row-Match"
    if cat == "interview":
        person = person_slug(o.get("person"))
        d = SORT / "Interviews" / person / c.camera / name
        return d, "interview", person
    if cat == "broll":
        return SORT / "B-Roll" / name, "broll", ""
    # unsure / None
    flags.append(f"Unsicher: {name} ({o.get('note','')})")
    return SORT / "_nicht_zugeordnet" / name, "nicht", o.get("note", "")


for c in clips:
    name = c.path.name
    d, cat, detail = dst_for(name)
    moves.append(Move(str(c.path), str(d)))
    if cat == "scripted":
        plan_rows["scripted"].setdefault(detail, []).append((name, c.camera))
    elif cat == "interview":
        plan_rows["interview"].setdefault(detail, []).append((name, c.camera))
    elif cat == "broll":
        plan_rows["broll"].append(name)
    else:
        plan_rows["nicht"].append((name, detail))

plan = MovePlan(moves=moves)
discovered = [str(c.path) for c in clips]
problems = plan.validate(discovered)

plan.save(PROJ / "manifest.json")

# Zuordnungsplan schreiben
L = []
L.append("# Zuordnungsplan — LohiBW Recruiting\n")
L.append(f"**Bilanz:** {len(clips)} Clips gefunden = "
         f"{sum(len(v) for v in plan_rows['scripted'].values())} gescriptet + "
         f"{sum(len(v) for v in plan_rows['interview'].values())} interview + "
         f"{len(plan_rows['broll'])} b-roll + {len(plan_rows['nicht'])} nicht-zugeordnet\n")
L.append(f"**validate():** {'OK (leer)' if not problems else 'PROBLEME: ' + '; '.join(problems)}\n")
L.append("\n## Gescriptete Szenen (Video → Szene → Takes)\n")
for folder in sorted(plan_rows["scripted"]):
    items = plan_rows["scripted"][folder]
    L.append(f"- **{folder}** ({len(items)} Take/s): " + ", ".join(n for n, _ in items))
L.append("\n## Interviews (nach Person, A/B-Winkel)\n")
for person in sorted(plan_rows["interview"]):
    items = plan_rows["interview"][person]
    L.append(f"- **{person}** ({len(items)}): " + ", ".join(f"{n}[{cam.split()[0]}]" for n, cam in items))
L.append(f"\n## B-Roll ({len(plan_rows['broll'])} Clips → sortiert/B-Roll/)\n")
L.append(", ".join(sorted(plan_rows["broll"])))
L.append(f"\n\n## _nicht_zugeordnet ({len(plan_rows['nicht'])})\n")
for n, d in plan_rows["nicht"]:
    L.append(f"- {n}: {d}")
L.append(f"\n## ⚠️ Bitte prüfen ({len(flags)})\n")
for f in flags:
    L.append(f"- {f}")
(PROJ / "zuordnungsplan.md").write_text("\n".join(L), encoding="utf-8")

print("Manifest:", len(moves), "Moves")
print("validate:", "OK" if not problems else problems)
print("scripted-Ordner:", len(plan_rows["scripted"]), "| interview-Personen:", len(plan_rows["interview"]),
      "| b-roll:", len(plan_rows["broll"]), "| nicht:", len(plan_rows["nicht"]), "| flags:", len(flags))
