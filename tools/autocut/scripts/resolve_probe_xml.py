"""Live-Probe des XML-Roundtrips (Spec v2 Abschnitt 6): Pegel- und Zeitlupen-Import, Marker, Spurnamen, Medien-Zuordnung,
Duplikat-Import und FPS-Attribut. Legt Bin „AutoCut/PROBE-XML“, zwei eigene Timelines und Duplikate an und löscht sie wieder.

Aufruf:
    venv/bin/python scripts/resolve_probe_xml.py "<Charge>" [--keep]

Schreibt <Charge>/_intern/autocut/probe_xml.json. Exit 0 = level_import_ok (Pflicht fürs Finalisieren), 1 sonst.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import xml_patch as X  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.media import proxy_for  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

FX_IN, FX_N = 250, 50          # FX3: 50 Frames ab Frame 250 auf V1/A1
BR_IN, BR_N = 0, 100           # 50p-B-Roll: 100 Quellframes (2 s) → Ziel 100 Timeline-Frames bei 2×
LEVEL = 0.5                    # −6 dB


def pick_clips(media: dict, index: dict) -> tuple[str, str, float]:
    fx = next((c for grp in (media.get("ordner") or {}).values() for c in grp.get("ton") or []), None)
    if not fx:
        raise AutoCutError("Kein FX3-Clip in media.json — erst autocut_prepare.py.")
    br = next((c for c in (index.get("clips") or []) if float(c.get("fps") or 0) >= 50 and float(c.get("dauer_s") or 0) >= 4), None)
    if br is None:
        raise AutoCutError("Kein B-Roll-Clip mit ≥ 50 fps und ≥ 4 s im Index — Zeitlupen-Probe braucht einen.")
    return fx, str(br["path"]), float(br["fps"])


def run_probe_xml(ch: Charge, session: RA.ResolveSession, media: dict, index: dict, name: str, keep: bool) -> dict:
    res: dict = {"ok": False, "gemessen_am": _dt.datetime.now().isoformat(timespec="seconds"), "resolve_version": session.version,
                 "project": session.project_name, "warnings": [], "cleanup": None}
    rcfg = ch.config["resolve"]
    fx, br, br_fps = pick_clips(media, index)
    res.update({"fx3": fx, "broll": br, "broll_fps": br_fps})
    fps = float(media["format"]["fps"])
    tl_roh = tl_final = None
    dups: list = []
    folder = session.ensure_bin([str(rcfg["bin_root"]), "PROBE-XML"])
    try:
        mi = session.import_media([fx, br], folder)
        session.link_proxy(mi[fx], ((media.get("clips") or {}).get(fx) or {}).get("proxy_path") or (str(proxy_for(fx)) if proxy_for(fx) else None))
        tl_roh = session.create_timeline(name + " (roh)", fps, int(media["format"]["width"]), int(media["format"]["height"]),
                                         str(rcfg["start_timecode"]))
        session.ensure_tracks(tl_roh, 3, 1, {"V1": "FX3", "V3": "B-Roll", "A1": "FX3 Ton"})
        start = session.timeline_start_frame(tl_roh)
        n_roh = int(round(BR_N * fps / br_fps))           # 50p: 100 Quellframes → 50 Timeline-Frames bei Tempo 1
        items = [Item("V1", fx, FX_IN, FX_IN + FX_N, 0, FX_N, True, "P"), Item("A1", fx, FX_IN, FX_IN + FX_N, 0, FX_N, True, "P"),
                 Item("V3", br, BR_IN, BR_IN + BR_N, 0, n_roh, True, "P", "broll", True, tempo=int(round(br_fps / fps)))]
        session.append_items(tl_roh, items, mi, start)
        session.add_markers(tl_roh, [MarkerSpec(10, "PROBE Marker", "", "Blue")], start)
        xml_dir = ch.work / "xml"
        xml_dir.mkdir(parents=True, exist_ok=True)
        roh_xml = session.export_timeline(tl_roh, xml_dir / "probe.roh.xml")
        tree = X.load_xml(roh_xml)
        rep = X.apply_patches(tree, [{"track": 1, "start": 0, "name": Path(fx).name, "level": LEVEL}],
                              [{"track": 3, "start": 0, "name": Path(br).name, "tempo": items[2].tempo, "end": BR_N}])
        res["patch"] = rep
        final_xml = X.save_xml(tree, xml_dir / "probe.final.xml")
        tl_final = session.import_timeline_xml(final_xml, name, session.all_folders())   # alle Bins: Dedupe legt Clips anderswo ab
        rb = session.read_timeline(tl_final)
        v3 = (rb["tracks"].get("V3") or {}).get("items") or []
        a1 = (rb["tracks"].get("A1") or {}).get("items") or []
        res["readback"] = {"V3": v3, "A1": a1}
        res["speed_import_ok"] = bool(v3 and int(v3[0]["duration"]) == BR_N)
        res["source_range_ok"] = bool(v3 and v3[0].get("src_in") is not None and v3[0].get("src_out") is not None
                                      and abs((int(v3[0]["src_out"]) - int(v3[0]["src_in"])) - BR_N) <= 1)
        res["speed_source"] = "end+filter" if res["speed_import_ok"] else "unbekannt"
        re_xml = session.export_timeline(tl_final, xml_dir / "probe.reexport.xml")
        lv = {l["start"]: l["level"] for l in X.read_levels(X.load_xml(re_xml), 1)}
        res["level_import_ok"] = abs(lv.get(0, 1.0) - LEVEL) < 0.01
        res["markers_survive"] = bool(RA._safe(tl_final.GetMarkers, None))
        res["tracknames_survive"] = RA._safe(tl_final.GetTrackName, None, "video", 3) == "B-Roll"
        # Beleg fürs Finalisieren (Live 04.09.: vier „Spurname … nicht gesetzt“ auf der importierten End-Timeline trotz
        # SetCurrentTimeline): klappt SetTrackName auf dem Import-Handle, und auf dem frisch geholten aktuellen Handle?
        RA._safe(session.project.SetCurrentTimeline, False, tl_final)
        res["trackname_set_on_import_handle"] = bool(RA._safe(tl_final.SetTrackName, False, "video", 3, "B-Roll"))
        cur = RA._safe(session.project.GetCurrentTimeline, None)
        res["trackname_set_on_current_handle"] = bool(cur is not None
                                                      and RA._safe(cur.SetTrackName, False, "video", 3, "B-Roll (aktuell)"))
        v1_items = RA._safe(tl_final.GetItemListInTrack, None, "video", 1) or []
        mpi = RA._safe(v1_items[0].GetMediaPoolItem, None) if v1_items else None
        res["media_relinked"] = bool(mpi and RA._safe(mpi.GetClipProperty, "", "File Path"))
        dup = session.add_duplicate_media(br, folder)
        res["duplicate_item_created"] = bool(dup is not None and RA._safe(dup.GetUniqueId, "a") != RA._safe(mi[br].GetUniqueId, "b"))
        res["fps_settable"] = bool(dup is not None and session.set_clip_fps(dup, fps))
        if dup is not None:
            dups.append(dup)
        res["ok"] = bool(res["level_import_ok"])
    except Exception as e:
        res["fehler"] = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
        res["traceback"] = None if isinstance(e, AutoCutError) else traceback.format_exc()
    finally:
        if not keep and not res.get("fehler"):
            res["cleanup"] = session.delete_probe_objects([t for t in (tl_roh, tl_final) if t is not None], dups, [folder])
        res["warnings"] = list(session.warnings)
        session.restore_user_timeline()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Live-Probe des XML-Roundtrips (Pegel, Zeitlupe, Duplikat, FPS).")
    ap.add_argument("charge")
    ap.add_argument("--keep", action="store_true", help="Probe-Objekte behalten")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        media, index = ch.read_json("media.json"), ch.read_json("broll_index.json")
        if not media or not index:
            raise AutoCutError("media.json und broll_index.json werden gebraucht (autocut_prepare.py, autocut_index_broll.py).")
        session = RA.ResolveSession(RA.connect(), probe=ch.read_json("probe.json"))
        name = f"AutoCut PROBE XML {_dt.datetime.now():%H%M%S}"
        print(f"Resolve {session.version}, Projekt '{session.project_name}' — Probe '{name}'")
        res = run_probe_xml(ch, session, media, index, name, args.keep)
        out = ch.write_json("probe_xml.json", res)
        keys = ("level_import_ok", "speed_import_ok", "source_range_ok", "markers_survive", "tracknames_survive",
                "trackname_set_on_import_handle", "trackname_set_on_current_handle", "media_relinked",
                "duplicate_item_created", "fps_settable")
        print("\n".join(f"  {k}: {res.get(k)}" for k in keys) + f"\n  cleanup: {res.get('cleanup')}\n→ {out}")
        if res.get("fehler"):
            print("FEHLER:", res["fehler"], file=sys.stderr)
        return 0 if res.get("ok") else 1
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
