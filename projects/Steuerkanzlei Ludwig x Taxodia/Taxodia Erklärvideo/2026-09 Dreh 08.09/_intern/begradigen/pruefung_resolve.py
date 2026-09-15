"""Begradigung in Resolve selbst prüfen: eigene Prüf-Timeline + Quick Export (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/pruefung_resolve.py [aufbauen|export|loeschen]
aufbauen: eigene Timeline „Claude Begradigung-Prüfung 2026-09-15" — je Interview-Clip 10 Frames ohne und 10 Frames mit
          Transform (parameter.json), beide mit Grade (CDL + LC-709), dazu FX3_0223 mit Punch-in-Werten.
export:   Prüf-Timeline kurz aktivieren, Quick Export ProRes 422 HQ nach pruefung/, danach Timeline und Bin des Users zurück.
loeschen: eigene Prüf-Timeline löschen.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
sys.path.insert(0, str(HIER.parent / "color"))
sys.path.insert(0, str(HIER.parent / "color" / "skripte"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402
import grading_anwenden as GA  # noqa: E402

PROJEKT = "Taxodia 09.26"
NAME = "Claude Begradigung-Prüfung 2026-09-15"
AUS = HIER / "pruefung"
N = 10


def plan() -> list[dict]:
    proben = json.loads((HIER / "proben.json").read_text())
    par = json.loads((HIER / "parameter.json").read_text())
    stuecke = []
    for clip, zeiten in sorted(proben.items()):
        stem = Path(clip).stem
        src = round(zeiten[1] * 25)
        for art in ("ohne", "mit") + (("punch",) if stem == "FX3_0223" else ()):
            props = {} if art == "ohne" else par[stem]["resolve" if art == "mit" else "resolve_punch_in"]
            stuecke.append({"clip": clip, "stem": stem, "art": art, "src": src, "rec": len(stuecke) * N, "props": props})
    return stuecke


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "aufbauen"
    s = RA.ResolveSession(RA.connect(), probe=json.loads((HIER.parent / "autocut" / "probe.json").read_text()))
    if s.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    proj, mp = s.project, s.media_pool
    AUS.mkdir(exist_ok=True)
    zustand = AUS / "zustand.json"
    if cmd == "aufbauen":
        if s.find_timeline(NAME):
            raise SystemExit("Prüf-Timeline existiert schon.")
        user_tl, user_bin = proj.GetCurrentTimeline(), mp.GetCurrentFolder()
        zustand.write_text(json.dumps({"user_timeline": user_tl.GetName(), "user_bin_id": user_bin.GetUniqueId()}, ensure_ascii=False))
        stuecke = plan()
        vorschlag = json.loads((HIER.parent / "color" / "grading_vorschlag.json").read_text())
        try:
            folder = s.ensure_bin(["AutoCut", "video-1-taxodia-weg"])
            media = s.import_media(sorted({x["clip"] for x in stuecke}), folder)
            tl = s.create_timeline(NAME, 25.0, 3840, 2160, "01:00:00:00")
            start = int(tl.GetStartFrame())
            items = [Item("V1", x["clip"], x["src"], x["src"] + N, x["rec"], x["rec"] + N, True, x["art"], "pruef", True) for x in stuecke]
            added = s.append_items(tl, items, media, start)
            erg = []
            for x, it in zip(stuecke, added):
                ok_t = bool(it.SetProperties(x["props"])) if x["props"] else True
                _, w = GA.cdl_fuer(vorschlag, it.GetName())
                ok_c = bool(it.SetCDL(GA.resolve_cdl(w))) and bool(it.GetNodeGraph().SetLUT(1, GA.LUT_REL))
                erg.append((x["stem"], x["art"], ok_t, ok_c))
            print(json.dumps({"timeline": NAME, "stuecke": erg}, ensure_ascii=False))
        finally:
            user = s.find_timeline(json.loads(zustand.read_text())["user_timeline"])
            proj.SetCurrentTimeline(user)
            ordner = next((f for f in s.all_folders() if f.GetUniqueId() == json.loads(zustand.read_text())["user_bin_id"]), None)
            if ordner is not None:
                mp.SetCurrentFolder(ordner)
            print("zurück:", proj.GetCurrentTimeline().GetName(), mp.GetCurrentFolder().GetName())
    elif cmd == "export":
        z = json.loads(zustand.read_text())
        user_tl, user_bin = proj.GetCurrentTimeline(), mp.GetCurrentFolder()
        try:
            proj.SetCurrentTimeline(s.find_timeline(NAME))
            time.sleep(1.0)
            print("Quick Export:", proj.RenderWithQuickExport("ProRes 422 HQ", {"TargetDir": str(AUS), "CustomName": "pruefung_render",
                                                                                "EnableUpload": False}), flush=True)
        finally:
            proj.SetCurrentTimeline(user_tl)
            if user_bin is not None:
                mp.SetCurrentFolder(user_bin)
            print("zurück:", proj.GetCurrentTimeline().GetName(), mp.GetCurrentFolder().GetName(), "| Zustand beim Aufbau:", z)
        (AUS / "plan.json").write_text(json.dumps(plan(), ensure_ascii=False, indent=1))
    elif cmd == "loeschen":
        tl = s.find_timeline(NAME)
        if tl is not None and proj.GetCurrentTimeline().GetName() != NAME:
            print("gelöscht:", mp.DeleteTimelines([tl]), s.save_project())


if __name__ == "__main__":
    main()
