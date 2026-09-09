"""Stufe 5 — Finalisieren: roh-Timeline → FCP7-XML → Pegel/Zeitlupe patchen → End-Timeline importieren → prüfen →
Spurnamen, Marker, Clip-Farben → roh-Timeline löschen (Spec v2 Abschnitt 4).

Eingaben: build.json (roh-Timeline, Startframe), timeline.json (Items/Marker), optional broll_build.json (V3-Items mit
tempo, Szenen-Marker), probe_xml.json (level_import_ok Pflicht; speed_import_ok Pflicht, wenn tempo-Items vorkommen).
Ausgaben: ton.json, work/xml/<name>.roh.xml / .final.xml / .reexport.xml, finalize.json, Pegel-Abschnitt im Rohschnitt-
Bericht, Protokoll-Eintrag (Skript). Bei jeder Abweichung: End-Timeline „… FEHLER", roh bleibt, AutoCutError.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from .charge import AutoCutError
from .timeline_model import Item, MarkerSpec
from .ton import build_ton, measure_true_peak
from . import xml_patch as X

_UNSAFE = re.compile(r'[/\\:*?"<>|]+')


def final_name(roh_name: str, suffix: str) -> str:
    if not suffix or not roh_name.endswith(suffix):
        raise AutoCutError(f"Timeline '{roh_name}' trägt nicht das Suffix '{suffix}' — nur roh-Timelines aus autocut_build.py "
                           f"lassen sich finalisieren.")
    return roh_name[: -len(suffix)]


def expected_items(tp_dict: dict, broll_build: dict | None) -> list[dict]:
    """Soll-Items der End-Timeline: Stufe 1 (V1/A1/V2) + V3; tempo-Items mit Ziel-Länge = Quellframes (Konform)."""
    out = []
    for d in (tp_dict.get("items") or []):
        it = Item.from_dict(d)
        out.append({"track": it.track, "rec_in_f": it.rec_in_f, "dur_f": it.rec_out_f - it.rec_in_f, "name": Path(it.clip).name,
                    "tempo": 1})
    for d in ((broll_build or {}).get("items") or []):
        it = Item.from_dict(d)
        dur = (it.src_out_f - it.src_in_f) if it.tempo > 1 else (it.rec_out_f - it.rec_in_f)
        out.append({"track": it.track, "rec_in_f": it.rec_in_f, "dur_f": dur, "name": Path(it.clip).name, "tempo": int(it.tempo)})
    return out


def level_patches(ton: dict) -> list[dict]:
    return [{"track": 1, "start": int(i["rec_in_f"]), "name": i["name"], "level": float(i["gain_lin"])}
            for i in (ton.get("items") or [])]


def speed_patches(broll_build: dict | None) -> list[dict]:
    out = []
    for d in ((broll_build or {}).get("items") or []):
        it = Item.from_dict(d)
        if it.tempo > 1:
            out.append({"track": 3, "start": it.rec_in_f, "name": Path(it.clip).name, "tempo": int(it.tempo),
                        "end": it.rec_in_f + (it.src_out_f - it.src_in_f)})
    return out


def verify_final(readback: dict, expected: list[dict], start_frame: int) -> list[str]:
    """Jedes Soll-Item muss auf seiner Spur mit Start (absolut) und Dauer vorkommen; Überzählige werden gemeldet."""
    probs = []
    tracks = readback.get("tracks") or {}
    for e in expected:
        rows = (tracks.get(e["track"]) or {}).get("items") or []
        hit = next((r for r in rows if int(r.get("start") or -1) == start_frame + int(e["rec_in_f"])), None)
        if hit is None:
            probs.append(f"{e['track']} Frame {e['rec_in_f']} ({e['name']}): Item fehlt in der End-Timeline.")
            continue
        if int(hit.get("duration") or -1) != int(e["dur_f"]):
            probs.append(f"{e['track']} Frame {e['rec_in_f']} ({e['name']}): Dauer {hit.get('duration')} statt {e['dur_f']}"
                         + (f" (tempo {e['tempo']} — Zeitlupe nicht übernommen?)" if e["tempo"] > 1 else "") + ".")
    for track, rows in tracks.items():
        n_exp = sum(1 for e in expected if e["track"] == track)
        n_got = len((rows or {}).get("items") or [])
        if n_got != n_exp:
            probs.append(f"{track}: {n_got} Items in der End-Timeline, erwartet {n_exp}.")
    return probs


def verify_reexport(tree, levels: list[dict], speeds: list[dict]) -> list[str]:
    probs = []
    got_l = {(l["start"], l["name"]): l["level"] for l in X.read_levels(tree, 1)}
    for lv in levels:
        g = got_l.get((int(lv["start"]), lv["name"]))
        if g is None or abs(g - float(lv["level"])) > 0.01 * max(1.0, float(lv["level"])):
            probs.append(f"A1 Frame {lv['start']} ({lv['name']}): Pegel im Re-Export {g}, Soll {lv['level']:.4g}.")
    got_s = {(s["start"], s["name"]): s["speed"] for s in X.read_speeds(tree, 3)}
    for sp in speeds:
        g = got_s.get((int(sp["start"]), sp["name"]))
        if g is None or abs(g - 100.0 / int(sp["tempo"])) > 0.5:
            probs.append(f"V3 Frame {sp['start']} ({sp['name']}): Speed im Re-Export {g}, Soll {100.0 / int(sp['tempo']):g} %.")
    return probs


def _xml_dir(charge) -> Path:
    d = charge.work / "xml"
    d.mkdir(parents=True, exist_ok=True)
    return d


def finalize(charge, session, cfg: dict, keep_roh: bool = False, measure=None) -> dict:
    """Ablauf nach Spec v2 Abschnitt 4; ``measure`` ersetzt die ffmpeg-Messung in Tests.

    Erst die billigen, Resolve-freien Vorbedingungen (build.json/timeline.json/probe_xml.json/Zeitlupen-Gate) —
    schlagen die fehl, wird weder Resolve angefasst noch finalize.json geschrieben. Ab der roh-Timeline-Suche
    steht ALLES (auch die ffmpeg-Pegelmessung) in einem gemeinsamen try/except/finally: jeder Fehler — auch eine
    rohe, nicht-AutoCutError-Exception aus der Resolve-Session — schreibt finalize.json (status "fehler"), benennt
    eine bereits importierte End-Timeline nach "… FEHLER" um (nur wenn eine existiert) und gibt am Ende IMMER die
    User-Timeline zurück (finally), egal wie früh der Fehler auftrat.
    """
    rcfg = cfg["resolve"]
    suffix = str(rcfg.get("roh_suffix") or " (roh)")
    build = charge.read_json("build.json") or {}
    tp = charge.read_json("timeline.json")
    if not build.get("timeline") or build.get("status") != "ok" or not tp:
        raise AutoCutError(f"{charge.autocut / 'build.json'}/timeline.json fehlen oder der letzte Bau war nicht ok — erst "
                           f"scripts/autocut_build.py ausführen.")
    roh_name = str(build["timeline"])
    name = final_name(roh_name, suffix)
    probe = charge.read_json("probe_xml.json") or {}
    if not probe.get("level_import_ok"):
        raise AutoCutError(f"{charge.autocut / 'probe_xml.json'} fehlt oder meldet level_import_ok=false — erst "
                           f"scripts/resolve_probe_xml.py ausführen (Pegel-Import muss belegt sein).")
    bb = charge.read_json("broll_build.json")
    if bb and bb.get("timeline") != roh_name:
        bb = None                                     # V3 gehört zu einer anderen roh-Timeline
    speeds = speed_patches(bb)
    if speeds and not probe.get("speed_import_ok"):
        raise AutoCutError("Der B-Roll-Plan enthält Zeitlupen (tempo > 1), aber probe_xml.json meldet speed_import_ok=false — "
                           "Zeitlupen aus dem Plan nehmen oder Rückfall (Konform am Duplikat) einrichten.")
    build_sf, tp_sf = build.get("start_frame"), tp.get("start_frame")
    start_frame = int(build_sf) if build_sf is not None else int(tp_sf) if tp_sf is not None else 0
    started = _dt.datetime.now()
    final = None
    result = {"status": "fehler", "timeline": name, "timeline_roh": roh_name, "roh_geloescht": False, "xml_roh": None,
              "xml_final": None, "xml_reexport": None, "levels_set": 0, "speeds_set": 0, "items_geprueft": 0, "markers": 0,
              "warnings": [], "ton_json": str(charge.autocut / "ton.json"), "gestartet_am": started.isoformat(timespec="seconds")}
    try:
        roh = session.find_timeline(roh_name)
        if roh is None:
            raise AutoCutError(f"roh-Timeline '{roh_name}' nicht im Projekt '{session.project_name}' — richtiges Projekt offen?")
        if session.find_timeline(name) is not None:
            raise AutoCutError(f"End-Timeline '{name}' existiert bereits — vorhandene umbenennen oder neu bauen.")
        ton = build_ton(charge, tp, cfg["ton"], measure or measure_true_peak)
        levels = level_patches(ton)
        expected = expected_items(tp, bb)
        warnings: list[str] = list(ton.get("warnungen") or [])
        result["items_geprueft"] = len(expected)
        result["warnings"] = warnings
        safe = _UNSAFE.sub("-", name).strip()
        xml_dir = _xml_dir(charge)
        xml_roh = session.export_timeline(roh, xml_dir / f"{safe}.roh.xml")
        result["xml_roh"] = str(xml_roh)
        tree = X.load_xml(xml_roh)
        rep = X.apply_patches(tree, levels, speeds)
        if rep["missing"]:
            raise AutoCutError("Clipitems im XML nicht gefunden: " + "; ".join(rep["missing"]) + f"\nXML: {xml_roh}")
        xml_final = X.save_xml(tree, xml_dir / f"{safe}.final.xml")
        result["xml_final"] = str(xml_final)
        result["levels_set"] = rep["levels_set"]
        result["speeds_set"] = rep["speeds_set"]
        folders = [session.ensure_bin([str(rcfg["bin_root"]), _bin_name(name, rcfg)]),
                   session.ensure_bin([str(rcfg["bin_root"]), _bin_name(name, rcfg), "B-Roll"])]
        folders += [fo for fo in session.all_folders() if fo not in folders]   # Live-Probe: alle Bins durchsuchen
        final = session.import_timeline_xml(xml_final, name, folders)
        rb = session.read_timeline(final)
        probs = verify_final(rb, expected, start_frame)
        xml_re = session.export_timeline(final, xml_dir / f"{safe}.reexport.xml")
        result["xml_reexport"] = str(xml_re)
        probs += verify_reexport(X.load_xml(xml_re), levels, speeds)
        if probs:
            raise AutoCutError("End-Timeline weicht ab:\n  " + "\n  ".join(probs))
        _safe_current(session, final)          # Live 04.09.: SetTrackName wirkt nur auf der aktiven Timeline
        session.ensure_tracks(final, 3, 1, dict(rcfg.get("track_names") or {}))
        markers = [MarkerSpec.from_dict(m) for m in (tp.get("markers") or [])]
        markers += [MarkerSpec.from_dict(m) for m in ((bb or {}).get("markers") or [])]
        session.add_markers(final, markers, start_frame)
        result["markers"] = len(markers)
        starts = {start_frame + int(s["start"]) for s in speeds}
        if starts:
            n = session.color_items(final, 3, starts, "Teal")
            if n != len(starts):
                warnings.append(f"Clip-Farbe Teal nur bei {n} von {len(starts)} Zeitlupen-Items gesetzt.")
        if not keep_roh:
            result["roh_geloescht"] = session.delete_own_timeline(roh, suffix, roh_name)
        result["status"] = "ok"
    except Exception as e:
        if final is not None:
            failed = name + " FEHLER"
            if session.find_timeline(failed) is None and _safe_rename(final, failed):
                result["timeline"] = failed
        result["fehler"] = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
        result["gebaut_am"] = _dt.datetime.now().isoformat(timespec="seconds")
        charge.write_json("finalize.json", result)
        if final is not None:
            hint = f"\nEnd-Timeline heißt jetzt '{result['timeline']}', roh-Timeline '{roh_name}' bleibt stehen."
        else:
            hint = f"\nroh-Timeline '{roh_name}' bleibt stehen."
        xml_hint = result["xml_final"] or result["xml_roh"]
        if xml_hint:
            hint += f" XML: {xml_hint}"
        raise AutoCutError(result["fehler"] + hint) from e
    finally:
        session.restore_user_timeline()
    result["warnings"] = warnings + list(getattr(session, "warnings", []))
    result["gebaut_am"] = _dt.datetime.now().isoformat(timespec="seconds")
    charge.write_json("finalize.json", result)
    return result


def _bin_name(name: str, rcfg: dict) -> str:
    from .resolve_api import bin_name_for
    return bin_name_for(name, str(rcfg.get("timeline_prefix") or ""))


def _safe_current(session, timeline) -> bool:
    try:
        return bool(session.project.SetCurrentTimeline(timeline))
    except Exception:
        return False


def _safe_rename(timeline, new_name: str) -> bool:
    try:
        return bool(timeline.SetName(new_name))
    except Exception:
        return False
