"""Nur lesen: alle V1-V3-Items der Grading-Test-Kopie -> proto/kopie_items.json."""
import json, sys
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA
KOPIE = "AutoCut video-1-taxodia-weg 2026-09-17 1040 Grading-Test"
r = RA.connect()
p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == "Taxodia 09.26", p.GetName()
k = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == KOPIE)
s = k.GetStartFrame()
items = []
for ti in (1, 2, 3):
    for x in k.GetItemListInTrack("video", ti) or []:
        mpi = x.GetMediaPoolItem()
        items.append({"spur": ti, "start": x.GetStart() - s, "dauer": x.GetDuration(), "name": x.GetName(),
                      "left": x.GetLeftOffset(), "src": x.GetSourceStartFrame(), "tempo": x.GetSpeed().get("Percentage"),
                      "aktiv": bool(x.GetClipEnabled()), "fps": float(mpi.GetClipProperty("FPS")),
                      "pfad": mpi.GetClipProperty("File Path"), "nodes": x.GetNodeGraph().GetNumNodes()})
cur = p.GetCurrentTimeline()
out = {"projekt": p.GetName(), "kopie": KOPIE, "seite": r.GetCurrentPage(), "aktiv": cur.GetName() if cur else None,
       "items": items}
json.dump(out, open("proto/kopie_items.json", "w"), indent=1, ensure_ascii=False)
from collections import Counter
print("Seite", out["seite"], "| aktiv", out["aktiv"])
print("Items je Spur:", Counter(i["spur"] for i in items), "| aktiv je Spur:", Counter(i["spur"] for i in items if i["aktiv"]))
print("Clips:", len({i["name"] for i in items}), "| Tempo:", Counter(i["tempo"] for i in items), "| fps:", Counter(i["fps"] for i in items))
print("Nodes:", Counter(i["nodes"] for i in items))
