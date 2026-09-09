"""Live-Probe der Resolve-Scripting-API (Task 8 Step 5) — misst, was die Doku offenlässt.

Aufruf:
    venv/bin/python scripts/resolve_probe.py "<Charge>" [--ordner NAME] [--keep]

Legt im offenen Projekt die Bin „AutoCut/PROBE" und EINE Timeline „AutoCut PROBE <HHMMSS>" an, setzt zwei
Clips der Charge (FX3 auf V1/A1, a7 auf V2/A2 mit Sync-Versatz, A2 stumm) plus Marker, liest alles zurück
und prüft. Gemessen werden:
  - endFrame-Semantik: Clip startFrame=100/endFrame=149 → GetDuration()==50 inklusiv, ==49 exklusiv
  - recordFrame absolut (GetStart()==Startframe der Timeline) / AddMarker relativ (GetMarkers-Schlüssel 0)
  - A2 per SetClipEnabled(False) stumm; Auflösung/Start-Timecode/Color-Keys nach useCustomSettings
  - ob Resolve Marker hinter dem letzten Clip annimmt
Ergebnis → <Charge>/_intern/autocut/probe.json (autocut_build.py liest ``end_frame_inclusive`` daraus).
Bei Erfolg wird NUR diese eine, selbst erzeugte Timeline wieder gelöscht (mit --keep bleibt sie);
bei Fehlschlag bleibt sie als „… FEHLER" zur Ansicht. Bin und Media-Pool-Einträge bleiben immer.
Exit 0 = alle Prüfungen bestanden, 1 = Abweichung/Fehler (probe.json enthält die Details).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.media import seconds_to_frames  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

WINDOW_FRAMES = 72          # Länge des Probe-Schnitts (wie Plan-Test: 250–322)
MEASURE_IN, MEASURE_OUT = 100, 149   # endFrame-Messung: inklusiv → 50 Frames, exklusiv → 49


def pick_pair(media: dict, sync: dict | None, ordner: str | None) -> dict:
    """Ein FX3/a7-Paar der Charge: bestes ok-Sync-Paar (höchste Konfidenz), sonst erstes Ordnerpaar ohne Versatz."""
    paare = [p for p in (sync or {}).get("paare", []) if p.get("ok")]
    if ordner:
        paare = [p for p in paare if Path(p["ref"]).parent.name == ordner]
    if paare:
        best = max(paare, key=lambda p: p["confidence"])
        return {"ref": best["ref"], "other": best["other"], "offset_frames": int(best["offset_frames"]),
                "overlap_ref": list(best["overlap_ref"]), "sync": True}
    for name, grp in (media.get("ordner") or {}).items():
        if ordner and name != ordner:
            continue
        if grp.get("ton") and grp.get("kontext"):
            return {"ref": grp["ton"][0], "other": grp["kontext"][0], "offset_frames": 0, "overlap_ref": [0.0, 0.0],
                    "sync": False}
    raise AutoCutError("Kein Interview-Ordner mit FX3- und a7-Clip in media.json — Probe braucht ein Kamerapaar.")


def pick_window(pair: dict, media: dict, fps: float) -> tuple[int, int]:
    """72-Frame-Fenster, das in beiden Clips liegt (nach Versatz)."""
    clips = media["clips"]
    fx_n = int(clips[pair["ref"]]["original"]["nb_frames"])
    a7_n = int(clips[pair["other"]]["original"]["nb_frames"])
    off = pair["offset_frames"]
    ov0 = seconds_to_frames(float(pair["overlap_ref"][0]), fps)
    for start in (ov0 + 250, ov0 + 25, max(0, -off) + 25, max(0, -off)):
        end = start + WINDOW_FRAMES
        if start >= 0 and end <= fx_n and start + off >= 0 and end + off <= a7_n:
            return start, end
    raise AutoCutError(f"Kein gemeinsames {WINDOW_FRAMES}-Frame-Fenster für {Path(pair['ref']).name} / "
                       f"{Path(pair['other']).name} (Versatz {off:+d}, Längen {fx_n}/{a7_n}).")


def measure_end_frame(session: RA.ResolveSession, timeline, mi, start_frame: int) -> dict:
    """Roh-Append eines Clips [100..149] auf V3 (Video) bei Record 0 → Dauer sagt inklusiv/exklusiv."""
    info = {"mediaPoolItem": mi, "startFrame": MEASURE_IN, "endFrame": MEASURE_OUT, "recordFrame": start_frame,
            "trackIndex": 3, "mediaType": 1}
    session.project.SetCurrentTimeline(timeline)
    RA._safe(session.media_pool.SetSelectedClip, None, mi)
    added = session.media_pool.AppendToTimeline([info]) or []
    if len(added) != 1:
        raise AutoCutError("Messclip konnte nicht angehängt werden (AppendToTimeline lieferte nichts).")
    dur, start = int(added[0].GetDuration()), int(added[0].GetStart())
    n = MEASURE_OUT - MEASURE_IN
    inclusive = True if dur == n + 1 else False if dur == n else None
    if inclusive is None:
        raise AutoCutError(f"endFrame-Messung unklar: Dauer {dur} für startFrame {MEASURE_IN}/endFrame {MEASURE_OUT} "
                           f"(erwartet {n + 1} oder {n}).")
    return {"end_frame_inclusive": inclusive, "measure_duration": dur, "measure_start": start,
            "record_frame_absolute": start == start_frame, "measure_start_expected": start_frame}


def run_probe(ch: Charge, session: RA.ResolveSession, media: dict, sync: dict | None, ordner: str | None,
              keep: bool, name: str, result: dict) -> dict:
    """Probe ausführen; ``result`` wird laufend gefüllt, damit bei einem Abbruch die Teilmessungen erhalten bleiben."""
    fps = float(media["format"]["fps"])
    rcfg = ch.config["resolve"]
    pair = pick_pair(media, sync, ordner)
    s_in, s_out = pick_window(pair, media, fps)
    off = pair["offset_frames"]
    result.update({"fx3": pair["ref"], "a7": pair["other"], "offset_frames": off, "sync_paar": pair["sync"],
                   "fenster": [s_in, s_out], "checks": {}})
    checks = result["checks"]

    folder = session.ensure_bin([str(rcfg["bin_root"]), "PROBE"])
    mi = session.import_media([pair["ref"], pair["other"]], folder)
    for c in (pair["ref"], pair["other"]):
        proxy = (media["clips"].get(c) or {}).get("proxy_path")
        result[f"proxy_{Path(c).stem}"] = session.link_proxy(mi[c], proxy) if proxy else None

    timeline = session.create_timeline(name, fps, int(media["format"]["width"]), int(media["format"]["height"]),
                                       str(rcfg["start_timecode"]))
    session.ensure_tracks(timeline, 3, 2, dict(rcfg.get("track_names") or {}))
    start = session.timeline_start_frame(timeline)
    result["start_frame"] = start
    result["start_timecode"] = RA._safe(timeline.GetStartTimecode, None)
    result["settings"] = {k: timeline.GetSetting(k) for k in
                          ("useCustomSettings", "timelineResolutionWidth", "timelineResolutionHeight",
                           "timelineFrameRate") + RA.COLOR_KEYS}
    checks["start_timecode"] = result["start_timecode"] == str(rcfg["start_timecode"])
    checks["resolution"] = (str(timeline.GetSetting("timelineResolutionWidth")) == str(media["format"]["width"])
                            and str(timeline.GetSetting("timelineResolutionHeight")) == str(media["format"]["height"]))
    checks["tracks"] = int(timeline.GetTrackCount("video")) >= 3 and int(timeline.GetTrackCount("audio")) >= 2

    m = measure_end_frame(session, timeline, mi[pair["ref"]], start)
    result.update(m)
    checks["record_frame_absolute"] = m["record_frame_absolute"]
    session.end_frame_inclusive = m["end_frame_inclusive"]

    items = [Item("V1", pair["ref"], s_in, s_out, 0, WINDOW_FRAMES, True, "P"),
             Item("A1", pair["ref"], s_in, s_out, 0, WINDOW_FRAMES, True, "P"),
             Item("V2", pair["other"], s_in + off, s_out + off, 0, WINDOW_FRAMES, True, "P"),
             Item("A2", pair["other"], s_in + off, s_out + off, 0, WINDOW_FRAMES, False, "P")]
    added = session.append_items(timeline, items, mi, start)
    checks["readback_append"] = len(added) == 4
    checks["a2_disabled"] = RA._safe(added[3].GetClipEnabled, None) is False
    checks["a1_enabled"] = RA._safe(added[0].GetClipEnabled, None) is True

    session.add_markers(timeline, [MarkerSpec(0, "PROBE Start", "AutoCut-Probe", "Blue"),
                                   MarkerSpec(36, "PROBE Mitte", "", "Yellow")], start)
    markers = RA._safe(timeline.GetMarkers, None) or {}
    keys = {int(float(k)) for k in markers}
    checks["marker_relative"] = keys == {0, 36}
    result["marker_keys"] = sorted(keys)
    beyond = int(WINDOW_FRAMES + 200)
    result["marker_beyond_end_ok"] = bool(timeline.AddMarker(beyond, "Red", "PROBE hinter Ende", "", 1, ""))

    rb = session.read_timeline(timeline)
    result["readback"] = rb

    def row(track: str, idx: int = 0):
        rows = rb["tracks"].get(track, {}).get("items", [])
        return rows[idx] if len(rows) > idx else None

    v1, a1, v2, a2, v3 = row("V1"), row("A1"), row("V2"), row("A2"), row("V3")
    checks["v1_position"] = bool(v1 and v1["start"] == start and v1["duration"] == WINDOW_FRAMES)
    checks["a1_position"] = bool(a1 and a1["start"] == start and a1["duration"] == WINDOW_FRAMES)
    checks["v2_position"] = bool(v2 and v2["start"] == start and v2["duration"] == WINDOW_FRAMES)
    checks["a2_position"] = bool(a2 and a2["start"] == start and a2["duration"] == WINDOW_FRAMES and a2["enabled"] is False)
    checks["v3_measure"] = bool(v3 and v3["start"] == start and v3["duration"] == m["measure_duration"])
    checks["v1_source"] = bool(v1 and v1["src_in"] == s_in)
    result["warnings"] = list(session.warnings)
    result["ok"] = all(checks.values())
    if result["ok"] and not keep:
        result["timeline_geloescht"] = bool(session.media_pool.DeleteTimelines([timeline]))
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Live-Probe der Resolve-API (eine eigene Timeline, danach gelöscht).")
    ap.add_argument("charge", help="Chargen-Ordner mit media.json (und sync.json)")
    ap.add_argument("--ordner", help="Interview-Ordner für das Kamerapaar (Standard: bestes Sync-Paar)")
    ap.add_argument("--keep", action="store_true", help="Probe-Timeline nach Erfolg behalten")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        media = ch.read_json("media.json")
        if not media:
            raise AutoCutError(f"{ch.autocut / 'media.json'} fehlt — erst scripts/autocut_prepare.py ausführen.")
        sync = ch.read_json("sync.json")
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
        name = f"AutoCut PROBE {_dt.datetime.now():%H%M%S}"
        print(f"Resolve {session.version}, Projekt '{session.project_name}' — Probe-Timeline '{name}'")
        result: dict = {"ok": False, "gemessen_am": _dt.datetime.now().isoformat(timespec="seconds"),
                        "resolve_version": session.version, "project": session.project_name,
                        "project_id": session.project_id, "timeline": name, "warnings": [],
                        "timeline_geloescht": False}
        try:
            run_probe(ch, session, media, sync, args.ordner, args.keep, name, result)
        except Exception as e:
            failed = None
            tl = session.current_timeline
            if tl is not None and RA._safe(tl.GetName, None) == name:
                failed = name + " FEHLER"
                if not RA._safe(tl.SetName, False, failed):
                    failed = None
            result.update({"ok": False, "timeline": failed or name,
                           "fehler": str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}",
                           "traceback": None if isinstance(e, AutoCutError) else traceback.format_exc(),
                           "warnings": list(session.warnings), "timeline_geloescht": False})
        finally:
            session.restore_user_timeline()
        out = ch.write_json("probe.json", result)
        if result["ok"]:
            print(f"PROBE OK — endFrame {'inklusiv' if result['end_frame_inclusive'] else 'EXKLUSIV'}, recordFrame "
                  f"absolut, Marker relativ, A2 stumm; Marker hinter Ende: "
                  f"{'angenommen' if result['marker_beyond_end_ok'] else 'abgelehnt'}; Timeline "
                  f"{'gelöscht' if result['timeline_geloescht'] else 'behalten'} → {out}")
            for w in result["warnings"]:
                print("WARNUNG:", w)
            return 0
        print("PROBE FEHLGESCHLAGEN → " + str(out), file=sys.stderr)
        if result.get("fehler"):
            print("FEHLER:", result["fehler"], file=sys.stderr)
        for k, v in (result.get("checks") or {}).items():
            if not v:
                print(f"  Prüfung nicht bestanden: {k}", file=sys.stderr)
        for w in result.get("warnings") or []:
            print("WARNUNG:", w, file=sys.stderr)
        print(f"Timeline '{result['timeline']}' bleibt zur Ansicht in Resolve (nichts gelöscht).", file=sys.stderr)
        return 1
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
