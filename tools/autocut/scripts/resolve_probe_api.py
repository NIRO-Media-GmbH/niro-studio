"""Live-Probe der Scripting-API 21.1 (Spec „Grundlage Resolve 21.1", Abschnitt 2): misst, wie sich AudioVolume,
NormalizeAudioLevel, SetSpeed (Lücke / Nachbar / Ripple), SetFades, AddTransition, AutoAlignClips,
RenderWithQuickExport und der Alpha-Import verhalten. Testmaterial ist synthetisch (probe_media.py) — kein NAS,
kein Kundenmaterial.

Aufruf:
    venv/bin/python scripts/resolve_probe_api.py "<Charge>" --project "<offenes Projekt>" [--keep]

Schutz: läuft nur, wenn --project exakt dem geöffneten Projekt entspricht (Freigabe des Users) — sonst Exit 2
ohne jede Änderung. Legt Bin „AutoCut/PROBE-API" und die Timelines „AutoCut PROBE API <HHMM>" und „… SYNC" an;
am Ende werden die eigenen Objekte nur gelöscht, wenn alle Pflichtmessungen ok sind und kein Render-Timeout
auftrat — nur in diesem Lauf importierte Clips; der Bin nur, wenn er von diesem Lauf angelegt wurde
(--keep behält sie immer; bei Fehler heißen sie „… FEHLER" und bleiben stehen; bei „nicht ok" bleiben
sie zur Ansicht stehen). Die Timeline des Users wird immer wieder aktiviert.
Ergebnis → <Charge>/_intern/autocut/probe_api.json. Exit 0 = Pflichtmessungen ok (volume, speed, fades),
1 = Messung fehlgeschlagen oder Fehler, 2 = Vorbedingung (Projektname, Resolve, ffmpeg, Charge).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import probe_api as PA  # noqa: E402
from niro_autocut import probe_media as PM  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402
from niro_autocut.ton import measure_true_peak  # noqa: E402

FPS = 25
TON_CLIP1 = (25, 125)            # Quellframes Clip 1 (V1/A1, Record 0–100)
TON_CLIP2 = (150, 250)           # Quellframes Clip 2 (Record 100–200); Handles 125–150 für die Transition
V3_STARTS = (0, 100, 150, 200)   # A, Lücke 50–100, B, C, D — je 100 Quellframes des 50p-Clips = 50 Timeline-Frames
V3_SRC = (0, 100)
SYNC_REC = 100                   # Timeline B: beide Clips ab Record 100, damit V2 nach vorn wandern kann
OVERLAY_REC, OVERLAY_N = 25, 50
RENDER_PRESET = "H.265 Master"
RENDER_WAIT_S = 120


# --------------------------------------------------------------------------- #
# Hilfen
# --------------------------------------------------------------------------- #

def _v3(timeline) -> list:
    """V3-Items nach Start sortiert — nach SetSpeed frisch holen, weil Handles veralten können."""
    items = RA._safe(timeline.GetItemListInTrack, None, "video", 3) or []
    return sorted(items, key=lambda it: int(it.GetStart()))


def _first_item(timeline, kind: str, index: int):
    items = RA._safe(timeline.GetItemListInTrack, None, kind, index) or []
    return min(items, key=lambda it: int(it.GetStart())) if items else None


def _src(it) -> tuple[int, int]:
    return int(RA._safe(it.GetSourceStartFrame, 0) or 0), int(RA._safe(it.GetSourceEndFrame, 0) or 0)


def _project_resolution(session) -> tuple[int, int]:
    w = RA._safe(lambda: int(float(session.project.GetSetting("timelineResolutionWidth"))), None)
    h = RA._safe(lambda: int(float(session.project.GetSetting("timelineResolutionHeight"))), None)
    return int(w or 1920), int(h or 1080)


# --------------------------------------------------------------------------- #
# Bau
# --------------------------------------------------------------------------- #

def build_timelines(session, files: dict, name: str, rcfg: dict) -> dict:
    """Bin, Import, Timeline A (V1/A1 Ton, V3 Zähler A/Lücke/B/C/D, V4 leer) und Timeline B (Sync-Paar mit Ton)."""
    root = session.media_pool.GetRootFolder()
    ac = next((f for f in (root.GetSubFolderList() or []) if f.GetName() == str(rcfg["bin_root"])), None)
    bin_neu = ac is None or not any(f.GetName() == "PROBE-API" for f in (ac.GetSubFolderList() or []))
    folder = session.ensure_bin([str(rcfg["bin_root"]), "PROBE-API"])
    ton, versetzt, zaehler = str(files["ton"]), str(files["versetzt"]), str(files["zaehler"])
    neu = [p for p in (ton, versetzt, zaehler) if session.find_media_item(p) is None]
    mi = session.import_media([ton, versetzt, zaehler], folder)
    own_clips = [mi[p] for p in neu]
    w, h = _project_resolution(session)      # Projektauflösung: kein useCustomSettings (BMD-Bug bleibt außen vor)
    tl_a = session.create_timeline(name, FPS, w, h, str(rcfg["start_timecode"]))
    session.ensure_tracks(tl_a, 4, 1, {"V1": "Ton", "V3": "B-Roll", "V4": "Grafik", "A1": "Ton"})
    start_a = session.timeline_start_frame(tl_a)
    items_a = [Item("V1", ton, TON_CLIP1[0], TON_CLIP1[1], 0, 100, True, "P"),
               Item("A1", ton, TON_CLIP1[0], TON_CLIP1[1], 0, 100, True, "P"),
               Item("V1", ton, TON_CLIP2[0], TON_CLIP2[1], 100, 200, True, "P"),
               Item("A1", ton, TON_CLIP2[0], TON_CLIP2[1], 100, 200, True, "P")]
    items_a += [Item("V3", zaehler, V3_SRC[0], V3_SRC[1], s, s + 50, True, "P", "broll", True, tempo=2) for s in V3_STARTS]
    added_a = session.append_items(tl_a, items_a, mi, start_a)
    tl_b = session.create_timeline(name + " SYNC", FPS, w, h, str(rcfg["start_timecode"]))
    session.ensure_tracks(tl_b, 2, 2, {"V1": "FX3", "V2": "a7IV", "A1": "FX3 Ton", "A2": "a7IV Ton"})
    start_b = session.timeline_start_frame(tl_b)
    items_b = [Item("V1", ton, 0, 250, SYNC_REC, SYNC_REC + 250, True, "P"),
               Item("A1", ton, 0, 250, SYNC_REC, SYNC_REC + 250, True, "P"),
               Item("V2", versetzt, 0, 300, SYNC_REC, SYNC_REC + 300, True, "P"),
               Item("A2", versetzt, 0, 300, SYNC_REC, SYNC_REC + 300, True, "P")]
    added_b = session.append_items(tl_b, items_b, mi, start_b)
    return {"folder": folder, "media": mi, "own_clips": own_clips, "bin_neu": bin_neu,
            "tl_a": tl_a, "tl_b": tl_b, "start_a": start_a, "start_b": start_b,
            "v1c1": added_a[0], "a1c1": added_a[1], "v1c2": added_a[2], "a1c2": added_a[3],
            "v1b": added_b[0], "v2b": added_b[2],
            "baseline": {"A": session.read_timeline(tl_a), "B": session.read_timeline(tl_b)}}


# --------------------------------------------------------------------------- #
# Messungen (Spec 2.3)
# --------------------------------------------------------------------------- #

def measure_volume(h: dict) -> dict:
    it = h["a1c1"]
    ok = bool(RA._safe(it.SetProperties, False, {"AudioVolume": PA.VOLUME_SOLL_DB}))
    props = RA._safe(it.GetProperties, None) or {}
    return PA.eval_volume(ok, props.get("AudioVolume"), props.get("AudioVolumeEnabled"))


def measure_normalize(session, h: dict, files: dict) -> dict:
    tl, it = h["tl_a"], h["a1c2"]
    modi = list(RA._safe(tl.GetNormalizeAudioModes, None) or [])
    const = getattr(session.resolve, "NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT", None)
    if "True Peak" not in modi:
        return {"uebersprungen": f"Modus 'True Peak' fehlt (Modi: {modi})", "modi": modi}
    if const is None:
        return {"uebersprungen": "Konstante NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT fehlt", "modi": modi}
    tpk = measure_true_peak(files["ton"], TON_CLIP2[0] / FPS, (TON_CLIP2[1] - TON_CLIP2[0]) / FPS)
    opts = {"normalizationMode": "True Peak", "targetLevel": PA.ZIEL_DBTP, "setLevelMode": const}
    ok = bool(RA._safe(tl.NormalizeAudioLevel, False, [it], opts))
    props = RA._safe(it.GetProperties, None) or {}
    return PA.eval_normalize(ok, props.get("AudioVolume"), tpk, modi)


def measure_speed(h: dict) -> dict:
    tl = h["tl_a"]
    items = _v3(tl)
    if len(items) < 4:
        raise AutoCutError(f"V3 hat {len(items)} Items statt 4 — Timeline-Bau prüfen.")
    a, b, c, d = items[:4]
    res: dict = {}
    dur0, src0 = int(a.GetDuration()), _src(a)
    ok1 = bool(RA._safe(a.SetSpeed, False, {"Percentage": 50.0, "RippleTimeline": False}))
    a, b, c, d = _v3(tl)[:4]
    dur1, src1 = int(a.GetDuration()), _src(a)
    res["a"] = {"dauer_vorher": dur0, "dauer_nachher": dur1, "src_vorher": list(src0), "src_nachher": list(src1),
                "speed": RA._safe(a.GetSpeed, None)}
    res["gap"] = PA.classify_speed_gap(dur0, dur1)
    res["source_kept"] = PA.source_kept(src0, src1)
    b_dur0, c_start0 = int(b.GetDuration()), int(c.GetStart())
    ok2 = bool(RA._safe(b.SetSpeed, False, {"Percentage": 50.0, "RippleTimeline": False}))
    a, b, c, d = _v3(tl)[:4]
    res["blocked"] = {"b_dauer_vorher": b_dur0, "b_dauer_nachher": int(b.GetDuration()),
                      "c_start_vorher": c_start0, "c_start_nachher": int(c.GetStart())}
    c_dur0, d_start0 = int(c.GetDuration()), int(d.GetStart())
    ok3 = bool(RA._safe(c.SetSpeed, False, {"Percentage": 50.0, "RippleTimeline": True}))
    a, b, c, d = _v3(tl)[:4]
    d_start1 = int(d.GetStart())
    res["ripple"] = PA.classify_ripple(d_start0, d_start1, c_dur0)
    res["d_start_vorher"], res["d_start_nachher"], res["c_dauer_nachher"] = d_start0, d_start1, int(c.GetDuration())
    speeds = [RA._safe(x.GetSpeed, None) for x in (a, b, c)]
    res["speeds"] = speeds
    res["set_returned"] = [ok1, ok2, ok3]
    res["ok"] = ok1 and ok2 and ok3 and all(PA.speed_percent_ok(s) for s in speeds)
    return res


def measure_fades(h: dict) -> dict:
    a, v = h["a1c1"], h["v1c1"]
    ok_a = bool(RA._safe(a.SetFades, False, dict(PA.FADES_SOLL)))
    ist_a = RA._safe(a.GetFades, None)
    ok_v = bool(RA._safe(v.SetFades, False, dict(PA.FADES_SOLL)))
    ist_v = RA._safe(v.GetFades, None)
    return {"ok": ok_a and PA.fades_match(PA.FADES_SOLL, ist_a), "video_ok": ok_v and PA.fades_match(PA.FADES_SOLL, ist_v),
            "ist": ist_a, "ist_video": ist_v}


def measure_transition(h: dict) -> dict:
    tr = RA._safe(h["v1c2"].AddTransition, None, dict(PA.TRANSITION_SOLL))
    typ = RA._safe(tr.GetType, None) if tr is not None else None
    dauer = RA._safe(lambda: int(tr.GetDuration()), None) if tr is not None else None
    return {"ok": tr is not None and typ == "transition" and dauer == PA.TRANSITION_SOLL["duration"],
            "typ": typ, "dauer": dauer}


def measure_autoalign(session, h: dict) -> dict:
    tl, r = h["tl_b"], session.resolve
    using = getattr(r, "AUTO_ALIGN_CLIPS_USING_WAVEFORM", None)
    if using is None:
        return {"uebersprungen": "Konstante AUTO_ALIGN_CLIPS_USING_WAVEFORM fehlt"}
    session.project.SetCurrentTimeline(tl)
    v1, v2 = _first_item(tl, "video", 1), _first_item(tl, "video", 2)
    if v1 is None or v2 is None:
        return {"uebersprungen": "Sync-Paar nicht gefunden (V1/V2 leer)"}
    s1, s2 = int(v1.GetStart()), int(v2.GetStart())
    opts = {"SyncUsing": using}
    track = getattr(r, "AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_AUTOMATIC", None)
    if track is not None:
        opts["UseTrack"] = track
    ok = bool(RA._safe(tl.AutoAlignClips, False, [v1, v2], opts))
    v1, v2 = _first_item(tl, "video", 1), _first_item(tl, "video", 2)
    out = PA.classify_align(s1, int(v1.GetStart()), s2, int(v2.GetStart()))
    out["ok"] = ok and out["ok"]
    out["set_returned"] = ok
    return out


def measure_inactive(session, h: dict) -> dict:
    """Timeline B bleibt aktiv; Fades auf einem Item der inaktiven Timeline A — nur Befund."""
    session.project.SetCurrentTimeline(h["tl_b"])
    it = h["a1c2"]
    ok = bool(RA._safe(it.SetFades, False, dict(PA.FADES_INAKTIV_SOLL)))
    ist = RA._safe(it.GetFades, None)
    good = ok and PA.fades_match(PA.FADES_INAKTIV_SOLL, ist)
    return {"ok": good, "fades_on_inactive_ok": good, "ist": ist, "hinweis": "nur Befund, keine Pflicht"}


def measure_quickexport(session, h: dict, target_dir: Path) -> dict:
    p = session.project
    presets = list(RA._safe(p.GetQuickExportRenderPresets, None) or [])
    if RENDER_PRESET not in presets:
        return {"uebersprungen": f"Preset '{RENDER_PRESET}' fehlt (vorhanden: {presets})"}
    p.SetCurrentTimeline(h["tl_a"])
    target_dir.mkdir(parents=True, exist_ok=True)
    for f in target_dir.glob("probe_api*"):     # Reste eines früheren Laufs dürfen nicht als Erfolg zählen
        f.unlink()
    t0 = time.monotonic()
    status = RA._safe(p.RenderWithQuickExport, None, RENDER_PRESET, {"TargetDir": str(target_dir), "CustomName": "probe_api"}) or {}
    wand = round(time.monotonic() - t0, 2)
    gewartet = 0
    while RA._safe(p.IsRenderingInProgress, False) and gewartet < RENDER_WAIT_S:
        time.sleep(1)
        gewartet += 1
    files = sorted(f for f in target_dir.glob("probe_api*") if f.is_file() and f.stat().st_size > 0)
    ok = status.get("JobStatus") == "Render Complete" and bool(files)
    return {"ok": ok, "status": status.get("JobStatus"), "ms": status.get("TimeTakenToRenderInMs"), "wanddauer_s": wand,
            "gewartet_s": gewartet, "datei": files[0].name if files else None, "fehler": status.get("Error")}


def measure_alpha_import(session, h: dict, files: dict) -> tuple[dict, object]:
    """Alpha-Overlay importieren und auf V4 legen. Liefert (Befund, Media-Pool-Item fürs Aufräumen oder None)."""
    overlay = str(files["overlay"])
    try:
        war_neu = session.find_media_item(overlay) is None
        mi = session.import_media([overlay], h["folder"])
        ov = mi[overlay]
        alpha = RA._safe(ov.GetClipProperty, None, "Alpha mode") or RA._safe(ov.GetClipProperty, None, "Alpha Mode")
        item = Item("V4", overlay, 0, OVERLAY_N, OVERLAY_REC, OVERLAY_REC + OVERLAY_N, True, "P", "broll", True)
        added = session.append_items(h["tl_a"], [item], mi, h["start_a"])
        start, dauer = int(added[0].GetStart()), int(added[0].GetDuration())
        return ({"ok": start == h["start_a"] + OVERLAY_REC and dauer == OVERLAY_N, "start": start, "dauer": dauer,
                 "alpha_mode": alpha}, ov if war_neu else None)
    except AutoCutError as e:
        return ({"ok": False, "fehler": str(e)}, None)


# --------------------------------------------------------------------------- #
# Ablauf
# --------------------------------------------------------------------------- #

def run_probe_api(ch: Charge, session, files: dict, name: str, keep: bool) -> dict:
    res: dict = {"ok": False, "gemessen_am": _dt.datetime.now().isoformat(timespec="seconds"),
                 "resolve_version": session.version, "project": session.project_name,
                 "timelines": {"A": name, "B": name + " SYNC"}, "warnings": [], "cleanup": None, "fehler": None}
    rcfg = ch.config["resolve"]
    h: dict | None = None
    extra_clips: list = []
    try:
        h = build_timelines(session, files, name, rcfg)
        res["baseline"] = h["baseline"]
        session.project.SetCurrentTimeline(h["tl_a"])
        res["volume"] = measure_volume(h)
        res["normalize"] = measure_normalize(session, h, files)
        res["speed"] = measure_speed(h)
        res["fades"] = measure_fades(h)
        res["transition"] = measure_transition(h)
        res["autoalign"] = measure_autoalign(session, h)
        res["inactive"] = measure_inactive(session, h)
        res["quickexport"] = measure_quickexport(session, h, ch.work / "probe_api" / "render")
        alpha, ov = measure_alpha_import(session, h, files)
        res["alpha_import"] = alpha
        if ov is not None:
            extra_clips.append(ov)
        res["ok"] = PA.overall_ok(res)
    except Exception as e:
        res["fehler"] = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
        res["traceback"] = None if isinstance(e, AutoCutError) else traceback.format_exc()
        wanted = {name, name + " SYNC"}
        timelines = [t for t in session.list_timelines() if str(RA._safe(t.GetName, "") or "") in wanted]
        if not timelines and session.current_timeline is not None:
            timelines = [session.current_timeline]
        for tl in timelines:
            RA._safe(tl.SetName, False, str(RA._safe(tl.GetName, "") or "") + " FEHLER")
    finally:
        render_timeout = int((res.get("quickexport") or {}).get("gewartet_s") or 0) >= RENDER_WAIT_S
        if h is not None and not keep and not res["fehler"]:
            if res["ok"] and not render_timeout:
                clips = list(h["own_clips"]) + extra_clips
                folders = [h["folder"]] if h["bin_neu"] else []
                res["cleanup"] = session.delete_probe_objects([h["tl_a"], h["tl_b"]], clips, folders)
                if not h["bin_neu"]:
                    res["cleanup"]["folders"] = "uebersprungen: Bin PROBE-API bestand schon vor diesem Lauf"
            else:
                gruende = []
                if render_timeout:
                    gruende.append("Render-Timeout — Resolve rendert womöglich noch")
                if not res["ok"]:
                    gruende.append("Pflichtmessung nicht ok")
                grund = " und ".join(gruende)
                res["cleanup"] = {"uebersprungen": f"{grund} — Probe-Objekte bleiben zur Ansicht stehen"}
        res["warnings"] = list(session.warnings)
        session.restore_user_timeline()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Live-Probe der Scripting-API 21.1 (Volume, Normalize, Speed, Fades, "
                                             "Transition, AutoAlign, QuickExport, Alpha-Import).")
    ap.add_argument("charge")
    ap.add_argument("--project", required=True,
                    help="Name des geöffneten Resolve-Projekts (Freigabe des Users) — muss exakt passen")
    ap.add_argument("--keep", action="store_true", help="Probe-Objekte behalten")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        session = RA.ResolveSession(RA.connect(), probe=ch.read_json("probe.json"), path_map=ch.config.get("path_map"))
        if session.project_name != args.project:
            raise AutoCutError(f"Offen ist das Projekt '{session.project_name}', freigegeben wurde '{args.project}'. "
                               f"Nichts geändert — Projekt öffnen oder --project anpassen.")
        proj_fps = session.project.GetSetting("timelineFrameRate")
        if not RA._fps_matches(proj_fps, FPS):
            raise AutoCutError(f"Projekt '{session.project_name}' läuft mit {proj_fps} fps, die Probe braucht {FPS} fps "
                               f"(Projekt-Setting timelineFrameRate). Nichts geändert.")
        files = PM.ensure_probe_media(ch.work / "probe_api")
    except AutoCutError as e:
        print(f"FEHLER (Vorbedingung): {e}", file=sys.stderr)
        return 2
    name = f"AutoCut PROBE API {_dt.datetime.now():%H%M}"
    print(f"Resolve {session.version}, Projekt '{session.project_name}' — Probe '{name}'")
    res = run_probe_api(ch, session, files, name, args.keep)
    out = ch.write_json("probe_api.json", json.loads(json.dumps(res, default=str, ensure_ascii=False)))
    print("\n".join(PA.summary_lines(res)) + f"\n  cleanup: {res.get('cleanup')}\n→ {out}")
    if res.get("fehler"):
        print("FEHLER:", res["fehler"], file=sys.stderr)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
