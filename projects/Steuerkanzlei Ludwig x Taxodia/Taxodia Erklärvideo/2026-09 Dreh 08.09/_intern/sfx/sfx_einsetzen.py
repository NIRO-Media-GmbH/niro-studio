"""SFX-Plan (sfx_plan.json) in den Feinschnitt setzen und mit den Grafik-Clips verknüpfen (Taxodia, 15.09.2026).

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_einsetzen.py [--ausfuehren]
- Grafik-Clips auf V4 werden über ihren Quellbereich (Left-Offset = Frame der Grafikdatei) dem Element zugeordnet. Hat der
  User einen Grafik-Clip verschoben, wandern die SFX dieses Elements um dieselbe Differenz mit.
- SFX-Dateien vom NAS (nur lesen) in den eigenen Bin AutoCut/video-1-taxodia-weg/SFX importiert (die User-Bins
  02_AUDIO/SFX sind offline, weil der NAS-Ordner inzwischen „03_Vorlagen und Tools" heißt — dort nichts verändert).
- Spuren A4 „SFX 1" / A5 „SFX 2" (nur anlegen, wenn sie fehlen und leer sind), Pegel + Fades je Platzierung,
  jede SFX mit ihrem Grafik-Clip verknüpft (SetClipsLinked), damit sie beim Verschieben mitgehen.
Ohne --ausfuehren nur Prüfung. Bericht: sfx_einsatz.json.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402

RA.TRACK_INDEX.update({"A3": 3, "A4": 4, "A5": 5})
HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
TIMELINE = "AutoCut video-1-taxodia-weg 2026-09-15 1149 Feinschnitt"
SPURNAMEN = {4: "SFX 1", 5: "SFX 2"}


def main() -> None:
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    platz = plan["platzierungen"] if isinstance(plan, dict) else plan
    tl_json, shots = fb.lade()
    p, fehler = fb.plan(tl_json, shots)
    elemente = {i.beat_nr: (i.rec_in_f, i.rec_out_f) for i in p["V4"]}
    probleme = []
    for e in platz:
        if e["element"] not in elemente:
            probleme.append(f"Element {e['element']} unbekannt")
        if not os.path.exists(e["pfad_nas"]):
            probleme.append(f"Datei fehlt: {e['pfad_nas']}")
    for spur in ("A4", "A5"):
        belegt = sorted((e["rec_frame"], e["rec_frame"] + e["dauer_frames"]) for e in platz if e["spur"] == spur)
        for (a0, a1), (b0, b1) in zip(belegt, belegt[1:]):
            if b0 < a1:
                probleme.append(f"{spur}: Überlappung {a0}–{a1} / {b0}–{b1}")
    if probleme:
        raise SystemExit("Plan fehlerhaft:\n  " + "\n  ".join(probleme))
    s = RA.ResolveSession(RA.connect(), probe=json.loads((fb.AC / "probe.json").read_text()))
    if s.project_name != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{fb.PROJEKT}' — nichts geschrieben.")
    proj, mp = s.project, s.media_pool
    tl = s.find_timeline(TIMELINE)
    start = int(tl.GetStartFrame())
    # V4-Clips ↔ Elemente über den Quellbereich; Verschiebung durch den User übernehmen
    v4 = tl.GetItemListInTrack("video", 4) or []
    zuordnung, versatz = {}, {}
    for eid, (a, b) in elemente.items():
        kand = [x for x in v4 if x.GetLeftOffset() < b and a < x.GetLeftOffset() + x.GetDuration()]
        if len(kand) != 1:
            probleme.append(f"Grafik-Clip für {eid} nicht eindeutig ({len(kand)})")
            continue
        x = kand[0]
        zuordnung[eid] = x
        versatz[eid] = (int(x.GetStart()) - start) - int(x.GetLeftOffset())  # 0, solange nicht verschoben
    belegt = {i: [(int(x.GetStart()) - start, int(x.GetStart()) - start + int(x.GetDuration()))
                  for x in (tl.GetItemListInTrack("audio", i) or [])] for i in (4, 5) if i <= int(tl.GetTrackCount("audio"))}
    if any(belegt.get(i) for i in (4, 5)):
        probleme.append(f"A4/A5 sind nicht leer: {belegt} — nichts geschrieben (erst abstimmen)")
    if probleme:
        raise SystemExit("\n".join(probleme))
    items = []
    for e in platz:
        rec = int(e["rec_frame"]) + versatz[e["element"]]
        src = int(round(float(e["src_in_s"]) * 25))
        items.append((e, Item(e["spur"], e["pfad_nas"], src, src + int(e["dauer_frames"]), rec, rec + int(e["dauer_frames"]),
                              True, e["element"], "sfx", False)))
    verschoben = {k: v for k, v in versatz.items() if v}
    print(f"{len(items)} SFX · A4 {sum(1 for e, _ in items if e['spur'] == 'A4')} · A5 {sum(1 for e, _ in items if e['spur'] == 'A5')}"
          f" · Grafik-Clips vom User verschoben: {verschoben or 'keine'}")
    if "--ausfuehren" not in sys.argv:
        return
    bin_vorher = mp.GetCurrentFolder()
    out = {"projekt": s.project_name, "timeline": TIMELINE, "aktiv": proj.GetCurrentTimeline().GetName(), "versatz": verschoben}
    try:
        # Der User hat die SFX-Bins neu verknüpft (15.09.): vorhandene Media-Pool-Items per Dateipfad wiederverwenden,
        # eigener Bin nur, falls eine Datei dort fehlt.
        pfade = sorted({it.clip for _, it in items})
        index = s._path_index()
        media = {pf: index[RA._norm(s.map_path(pf))] for pf in pfade if RA._norm(s.map_path(pf)) in index}
        fehlend = [pf for pf in pfade if pf not in media]
        out["sfx_aus_user_bin"], out["sfx_neu_importiert"] = len(media), len(fehlend)
        if fehlend:
            media.update(s.import_media(fehlend, s.ensure_bin(["AutoCut", "video-1-taxodia-weg", "SFX"])))
        while int(tl.GetTrackCount("audio")) < 5:
            if not tl.AddTrack("audio", "stereo"):
                raise SystemExit("Audiospur konnte nicht angelegt werden.")
        out["spurnamen"] = {i: bool(tl.SetTrackName("audio", i, n)) for i, n in SPURNAMEN.items()}
        gesetzt = []
        for spur in ("A4", "A5"):
            teil = [(e, it) for e, it in items if e["spur"] == spur]
            if not teil:
                continue
            neu = s.append_items(tl, [it for _, it in teil], media, start)
            for (e, it), x in zip(teil, neu):
                v = bool(x.SetProperties({"AudioVolume": float(e["gain_db"])}))
                f = bool(x.SetFades({"FadeIn": int(e.get("fade_in_f", 0)), "FadeOut": int(e.get("fade_out_f", 0))}))
                link = bool(tl.SetClipsLinked([zuordnung[e["element"]], x], True))
                gesetzt.append({"spur": spur, "start": int(x.GetStart()) - start, "element": e["element"], "sfx": e["sfx_name"],
                                "pegel": v, "fades": f, "verknuepft": link, "linked_readback": len(x.GetLinkedItems() or [])})
        out["gesetzt"] = gesetzt
    finally:
        if bin_vorher is not None:
            mp.SetCurrentFolder(bin_vorher)
        out["gespeichert"] = s.save_project()
        out["bin_nachher"] = mp.GetCurrentFolder().GetName() if mp.GetCurrentFolder() else None
        out["warnungen"] = s.warnings
        (HIER / "sfx_einsatz.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        ok = [g for g in out.get("gesetzt", []) if g["pegel"] and g["fades"] and g["verknuepft"]]
        print(json.dumps({k: v for k, v in out.items() if k != "gesetzt"}, ensure_ascii=False), f"| gesetzt {len(out.get('gesetzt', []))}, vollständig ok {len(ok)}")


if __name__ == "__main__":
    main()
