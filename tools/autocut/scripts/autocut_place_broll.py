"""B-Roll-Layout v2 prüfen und V3 in die Rohschnitt-Timeline bauen (Stufe 3, Spec v2 Abschnitt 3).

Aufruf:
    venv/bin/python scripts/autocut_place_broll.py "<Charge>" --compact
    venv/bin/python scripts/autocut_place_broll.py "<Charge>" --raster
    venv/bin/python scripts/autocut_place_broll.py "<Charge>" --verify-only [--profile default] [--timeline NAME]
    venv/bin/python scripts/autocut_place_broll.py "<Charge>" [--profile default] [--timeline NAME]

--compact      schreibt _intern/autocut/broll_index_kompakt.json — die Kurzform des B-Roll-Index (mit den
               Abschnittsfeldern aus dem Nachlauf) für die Session (siehe prompts/place-broll.md); sonst nichts.
--raster       berechnet die Sprecher-Fenster je O-Ton-Beat und die dazwischenliegenden Strecken; schreibt
               _intern/autocut/raster.json und Ergebnisse/Rohschnitt/<video>-raster.md, baut nichts. Ist bereits ein
               B-Roll-Plan (Version 2) vorhanden, gehen dessen eigene Fenster in die Rechnung ein; sonst gilt je
               O-Ton-Beat das Standardfenster. Liegt ein B-Roll-Plan im alten (v1) Format oder sonst kaputt vor,
               bricht --raster nicht ab, sondern meldet das als HINWEIS und rechnet mit Standardfenstern weiter.
               Exit 1, wenn das Raster Fehler meldet (z. B. Gesichtsanteil verfehlt).
Sonst: lädt cutlist.json (verify.json muss ok sein und zum Hash passen), broll_index.json, timeline.json (Beat-Positionen
aus autocut_build.py; fehlt sie, wird der Timeline-Plan nur für die Prüfung aus Cutlist, media.json und sync.json
berechnet), den B-Roll-Plan (Version 2: fenster/strecken/szenen/shots) und das Profil (profile/<name>.md/.yaml). Prüft
hart (verify_layout + Existenz von Original und Proxy je platziertem Shot) und schreibt broll_verify.json. Mit
--verify-only endet der Lauf hier (Exit 0 = OK, 1 = Fehler). Ein B-Roll-Plan im alten (v1) Format wird mit einem
Hinweis auf --raster abgelehnt.
Ohne --verify-only und bei OK: verbindet sich mit DaVinci Resolve, findet die Timeline aus build.json (oder
--timeline), importiert die B-Roll-Clips in den Bin AutoCut/<video>/B-Roll, verknüpft Proxys, hängt die V3-Items an
(nur Bild, roh — Zeitlupen-Shots enden bei roh_out_f und werden erst beim Finalisieren konformiert), setzt Cyan-Marker
je Szene und gelbe Marker je Abweichung, speichert das Projekt; schreibt broll_build.json (mit `items`/`markers` für
autocut_finalize.py), Ergebnisse/Rohschnitt/<video>-broll.md und einen Protokoll-Eintrag.

NAS wird nur gelesen. In Resolve wird nur angehängt (Bin, Media-Pool-Einträge, V3-Items, Marker) — nichts geändert,
nichts gelöscht; angefasst wird ausschließlich eine Timeline, deren Name mit resolve.timeline_prefix („AutoCut “)
beginnt, also von AutoCut stammt.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import traceback
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.broll_layout import (LayoutPlan, build_v3_items_v2, compact_index_v2, effective_windows,  # noqa: E402
                                       place_shots, raster, render_layout_md, render_raster_md, stretches,
                                       verify_layout, window_frames)
from niro_autocut.broll_plan import load_profile  # noqa: E402
from niro_autocut.charge import DEFAULTS_FILE, AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.cutlist import Cutlist, cutlist_hash  # noqa: E402
from niro_autocut.media import proxy_for  # noqa: E402
from niro_autocut import readback as RB  # noqa: E402
from niro_autocut import replay  # noqa: E402
from niro_autocut.report import write_report  # noqa: E402
from niro_autocut import telemetrie as TM  # noqa: E402

PLAN_FILE = "broll_plan.json"
RASTER_FILE = "raster.json"
VERIFY_FILE = "broll_verify.json"
BUILD_FILE = "broll_build.json"
COMPACT_FILE = "broll_index_kompakt.json"


# --------------------------------------------------------------------------- #
# Eingaben
# --------------------------------------------------------------------------- #

def video_kurz(cl: Cutlist) -> str:
    return Path(cl.video).stem if cl.video else "video"


def effective_broll_cfg(ch: Charge, profile: str) -> tuple[str, dict]:
    """broll-Werte: defaults.yaml < profile/<name>.yaml < Chargen-config.yaml (broll:). Liefert (Profil-Prosa, Werte)."""
    base = (yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8")) or {}).get("broll") or {}
    text, prof = load_profile(profile)
    local_file = ch.autocut / "config.yaml"
    local = {}
    if local_file.exists():
        local = (yaml.safe_load(local_file.read_text(encoding="utf-8")) or {}).get("broll") or {}
    return text, {**base, **prof, **local}


def load_words(ch: Charge) -> dict[str, list[dict]]:
    """Wörter je Interview-Clip aus dem Transkript-Cache (nur für den Timeline-Plan ohne timeline.json)."""
    words: dict[str, list[dict]] = {}
    for rec in ch.load_index():
        cached = ch.cache_transcript(rec["fingerprint"])
        if cached and cached.get("words") is not None:
            words[rec["path"]] = cached["words"]
    return words


def timeline_plan_dict(ch: Charge, cl: Cutlist) -> tuple[dict, str]:
    """Beat-Positionen: aus timeline.json (Bau aus Stufe 1) oder — nur zur Prüfung — frisch berechnet."""
    raw = ch.read_json("timeline.json")
    if raw is not None:
        tp = raw if "beats" in raw else next((raw[k] for k in ("plan", "timeline_plan") if isinstance(raw.get(k), dict)
                                              and "beats" in raw[k]), None)
        if tp is None:
            raise AutoCutError(f"{ch.autocut / 'timeline.json'} enthält keine Beat-Positionen ('beats') — "
                               f"autocut_build.py erneut ausführen.")
        tl, cp = ch.autocut / "timeline.json", ch.autocut / "cutlist.json"
        quelle = "timeline.json"
        if tl.stat().st_mtime < cp.stat().st_mtime:
            quelle += " (älter als cutlist.json — Beat-Positionen könnten veraltet sein; ggf. autocut_build.py erneut ausführen)"
        return tp, quelle
    from niro_autocut.timeline_model import build_timeline_plan
    media = ch.read_json("media.json")
    if media is None:
        raise AutoCutError("Weder timeline.json noch media.json vorhanden — erst autocut_prepare.py, autocut_sync.py und "
                           "autocut_build.py ausführen.")
    sync = ch.read_json("sync.json") or {"fps": media["format"]["fps"], "paare": []}
    tp = build_timeline_plan(cl, media, sync, load_words(ch), ch.config).to_dict()
    return tp, "berechnet aus cutlist.json/media.json/sync.json (timeline.json fehlt — Bau ohne Stufe-1-Timeline nicht möglich)"


def require_verified_cutlist(ch: Charge) -> Cutlist:
    cpath = ch.autocut / "cutlist.json"
    cl = Cutlist.load(cpath)
    v = ch.read_json("verify.json")
    if not v or not v.get("ok"):
        raise AutoCutError("verify.json fehlt oder ist nicht ok — erst autocut_verify.py ausführen.")
    if v.get("cutlist_hash") != cutlist_hash(cpath):
        raise AutoCutError("cutlist.json wurde seit der letzten Prüfung geändert — erst autocut_verify.py (und ggf. "
                           "autocut_build.py) erneut ausführen.")
    return cl


def check_shot_files(placed: list[dict], index: dict, map_path=None) -> list[str]:
    """Original und Proxy jedes platzierten Clips müssen da sein (nur Existenz-Tests; NAS wird nur gelesen)."""
    probs = []
    by_path = {c["path"]: c for c in (index.get("clips") or []) if c.get("path")}
    for clip in sorted({p["clip"] for p in placed}):
        p = Path(clip)
        mp = Path(map_path(clip)) if map_path else p
        if not mp.is_file():
            probs.append(f"Clip-Datei nicht gefunden: {mp} — ist das NAS/SSD gemountet? path_map prüfen.")
            continue
        proxy = (by_path.get(clip) or {}).get("proxy")
        proxy_mp = map_path(proxy) if (proxy and map_path) else proxy
        if not (proxy_mp and Path(proxy_mp).is_file()) and proxy_for(mp) is None:
            probs.append(f"kein Proxy für {mp.name} (erwartet {mp.parent / 'Proxy' / (mp.stem + '.mov')} oder .mp4).")
    return probs


# --------------------------------------------------------------------------- #
# Resolve
# --------------------------------------------------------------------------- #

def _timelines(session) -> list:
    if hasattr(session, "list_timelines"):
        return list(session.list_timelines())
    project = session.project
    return [t for t in (project.GetTimelineByIndex(i) for i in range(1, int(project.GetTimelineCount()) + 1)) if t]


def find_timeline(session, name: str):
    """Timeline mit exakt diesem Namen im offenen Projekt (über die Session-Methoden); sonst AutoCutError mit den
    vorhandenen Namen."""
    t = session.find_timeline(name) if hasattr(session, "find_timeline") else None
    if t is None:
        t = next((x for x in _timelines(session) if x.GetName() == name), None)
    if t is not None:
        return t
    names = [x.GetName() for x in _timelines(session)]
    raise AutoCutError(f"Timeline „{name}“ im Projekt nicht gefunden. Vorhanden: {', '.join(names) or 'keine'} — "
                       f"mit --timeline den Namen der Rohschnitt-Timeline angeben.")


def build_v3(session, timeline_name: str, video: str, items: list, markers: list, index: dict, cfg: dict) -> dict:
    """Fertige V3-Items und Marker an die bestehende Rohschnitt-Timeline anhängen (nur Anhängen, keine Änderung an
    V1/V2/A1/A2). Items/Marker kommen bereits gebaut herein (siehe ``broll_layout.build_v3_items_v2``).

    Angefasst wird nur eine Timeline, die AutoCut selbst angelegt hat (Name beginnt mit ``resolve.timeline_prefix`` + Leerzeichen);
    fremde Timelines des Projekts bleiben unberührt. Nicht-fatale Befunde der Session (Marker/Spurname nicht gesetzt) landen
    in ``warnings`` des Ergebnisses.
    """
    rcfg = cfg["resolve"]
    prefix = str(rcfg.get("timeline_prefix") or "AutoCut")
    if not timeline_name.startswith(prefix + " "):
        raise AutoCutError(f"Timeline „{timeline_name}“ wurde nicht von AutoCut angelegt (Name beginnt nicht mit „{prefix} “) — "
                           f"fremde Timelines werden nicht verändert. Die Rohschnitt-Timeline aus build.json verwenden oder mit "
                           f"--timeline eine AutoCut-Timeline nennen.")
    if not items:
        raise AutoCutError("Der B-Roll-Plan enthält keine Items — nichts zu bauen.")
    timeline = find_timeline(session, timeline_name)
    warnings: list[str] = []
    n_warn = len(getattr(session, "warnings", []))
    refresh = getattr(getattr(session, "media_pool", None), "RefreshFolders", None)
    if refresh is not None:
        try:
            refresh()      # Cloud-/Multi-User-Projekte: Ordnerstand vor Schreibzugriffen aktualisieren
        except Exception as e:
            warnings.append(f"RefreshFolders fehlgeschlagen ({e}) — Media-Pool-Stand könnte veraltet sein.")
    folder = session.ensure_bin([rcfg["bin_root"], video, "B-Roll"])
    clips = sorted({it.clip for it in items})
    media_items = session.import_media(clips, folder)
    by_path = {c["path"]: c for c in (index.get("clips") or []) if c.get("path")}
    for c in clips:
        proxy = (by_path.get(c) or {}).get("proxy") or proxy_for(session.map_path(c))
        if not session.link_proxy(media_items[c], str(proxy) if proxy else None):
            warnings.append(f"Proxy nicht verknüpft: {Path(c).name}")
    session.project.SetCurrentTimeline(timeline)      # zuerst aktivieren: Resolve setzt Spurnamen nur auf der aktiven Timeline
    session.ensure_tracks(timeline, 3, int(timeline.GetTrackCount("audio")), {"V3": rcfg["track_names"]["V3"]})
    start = session.timeline_start_frame(timeline)
    session.append_items(timeline, items, media_items, start)
    session.add_markers(timeline, markers, start)
    saved = False
    try:
        saved = session.save_project() if hasattr(session, "save_project") else bool(session.project.SaveProject())
    except Exception as e:  # Speichern ist Komfort, kein Bauschritt
        warnings.append(f"Projekt nicht gespeichert: {e}")
    warnings.extend(list(getattr(session, "warnings", []))[n_warn:])
    return {"timeline": timeline_name, "items": len(items), "markers": len(markers), "start_frame": start,
            "clips": len(clips), "warnings": warnings, "gespeichert": saved, "projekt": session.project.GetName(),
            "projekt_id": str(getattr(session, "project_id", "") or ""),
            "end_frame_inclusive": getattr(session, "end_frame_inclusive", None)}


# --------------------------------------------------------------------------- #
# Ablauf
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut Stufe 3: B-Roll-Plan prüfen und V3 in Resolve bauen.")
    ap.add_argument("charge", help="Pfad zur Charge (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--verify-only", action="store_true", help="nur prüfen, broll_verify.json schreiben, nichts bauen")
    ap.add_argument("--compact", action="store_true", help="nur den kompakten Index für die Session schreiben")
    ap.add_argument("--raster", action="store_true", help="Fenster/Strecken berechnen (raster.json + <video>-raster.md), nichts bauen")
    ap.add_argument("--profile", default="default", help="Schnitt-Profil aus tools/autocut/profile/ (Standard: default)")
    ap.add_argument("--timeline", help="Name der Rohschnitt-Timeline (Standard: aus build.json)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        index = ch.read_json("broll_index.json")
        if index is None:
            raise AutoCutError(f"{ch.autocut / 'broll_index.json'} fehlt — erst autocut_index_broll.py ausführen.")

        if args.compact:
            clips = compact_index_v2(index)
            p = ch.write_json(COMPACT_FILE, {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"),
                                             "anzahl": len(clips), "clips": clips})
            print(f"Kompakter Index: {p} ({len(clips)} Clips, {sum(1 for c in clips if c['verwendbar'])} mit verwendbaren "
                  f"Abschnitten, {p.stat().st_size // 1024} KB)\nProfil: {Path(__file__).resolve().parents[1] / 'profile' / (args.profile + '.md')}")
            return 0

        cl = require_verified_cutlist(ch)
        tp_dict, quelle = timeline_plan_dict(ch, cl)
        fps = float(tp_dict.get("fps") or cl.fps)
        _, cfg_broll = effective_broll_cfg(ch, args.profile)
        ppath = ch.autocut / PLAN_FILE

        if args.raster:
            # Ein vorhandener Plan darf --raster nicht verhindern: eine Charge mit einem alten (v1) oder sonst
            # kaputten broll_plan.json soll trotzdem ein Raster mit Standardfenstern bekommen (--raster ist ja
            # gerade der Weg, einen neuen Plan v2 vorzubereiten).
            try:
                plan = LayoutPlan.load(ppath) if ppath.exists() else None
            except AutoCutError as e:
                print(f"HINWEIS: {e} — Raster mit Standardfenstern.")
                plan = None
            r = raster(tp_dict, cl, cfg_broll, plan)
            ch.write_json(RASTER_FILE, r)
            md = write_report(ch, f"{video_kurz(cl)}-raster.md", render_raster_md(r, cl, tp_dict))
            print(f"Raster: {len(r['fenster'])} Fenster, {len(r['strecken'])} Strecken, Gesicht {r['gesicht_anteil'] * 100:.1f} % "
                  f"(Ziel {int(r['ziel_gesicht'][0] * 100)}–{int(r['ziel_gesicht'][1] * 100)} %)\n{ch.autocut / RASTER_FILE}\n{md}")
            for e in r["fehler"]:
                print("FEHLER:", e)
            return 1 if r["fehler"] else 0

        # Außerhalb --raster bleibt ein Plan im alten (v1) Format ein harter Fehler (LayoutPlan.load benennt
        # dabei --raster als Ausweg).
        plan = LayoutPlan.load(ppath) if ppath.exists() else None
        if plan is None:
            raise AutoCutError(f"{ppath} fehlt — erst `--raster`, dann Plan v2 nach prompts/place-broll.md schreiben.")

        print(f"Charge: {ch.root}\nCutlist: {cl.video} ({len(cl.beats)} Beats) · Index: {len(index.get('clips') or [])} Clips · "
              f"Beat-Positionen: {quelle}\nProfil: {args.profile} · B-Roll-Plan: {len(plan.strecken)} Strecken, "
              f"{sum(len(st.szenen) for st in plan.strecken)} Szenen, {len(plan.all_shots())} Shots\n")

        tele = TM.laden(ch.autocut)
        # cfg_broll ist nur der broll:-Block (effective_broll_cfg); telemetrie: liegt in defaults.yaml/config.yaml
        # als Geschwister-Schlüssel daneben und muss für die Brennweitenfolge in verify_layout extra rein — mit
        # Chargen-Override, wie ch.config["telemetrie"] ihn auch autocut_telemetrie.py liefert.
        res = verify_layout(plan, tp_dict, index, cl, {**cfg_broll, "telemetrie": ch.config["telemetrie"]}, fps, tele)
        if any(e.startswith("Config:") for e in res.errors):
            # cfg_broll fehlt ein Pflichtschlüssel — verify_layout hat das schon als Fehler gemeldet; die
            # Neuberechnung hier (nur um `placed` fürs Bauen/check_shot_files zu bekommen) würde mit demselben
            # unvollständigen cfg_broll einen rohen KeyError werfen statt der deutschen Fehlermeldung oben.
            placed = []
        else:
            wf, _ = window_frames(effective_windows(plan, tp_dict, cl, cfg_broll), tp_dict, fps, cfg_broll)
            placed, _ = place_shots(plan, tp_dict, index, cfg_broll, fps, strecken_frames=stretches(wf, int(tp_dict["total_frames"])))
        res.errors += check_shot_files(placed, index, map_path=ch.map_path)
        for e in res.errors:
            print("FEHLER:", e)
        for w in res.warnings:
            print("WARNUNG:", w)
        n_items = len(placed)
        ch.write_json(VERIFY_FILE, {"broll_plan_hash": cutlist_hash(ppath), "ok": res.ok, "errors": res.errors,
                                    "warnings": res.warnings, "video": cl.video, "profil": args.profile,
                                    "beat_positionen": quelle, "geprueft_am": _dt.datetime.now().isoformat(timespec="seconds"),
                                    "n_strecken": len(plan.strecken), "n_items": n_items})
        print(f"{'OK' if res.ok else 'NICHT OK'} — {len(res.errors)} Fehler, {len(res.warnings)} Warnungen → {ch.autocut / VERIFY_FILE}")
        if not res.ok:
            return 1
        if args.verify_only:
            return 0

        build = ch.read_json("build.json") or {}
        name = args.timeline or build.get("timeline") or build.get("timeline_name") or build.get("name")
        if not name:
            raise AutoCutError("Kein Timeline-Name: build.json fehlt (autocut_build.py noch nicht gelaufen) — "
                               "oder mit --timeline den Namen angeben.")
        if replay.ist_hochgeladen(ch.root, name):     # zählt auch gescheiterte Versuche und nicht auswertbare Logs
            raise AutoCutError(f"Timeline „{name}“ ist laut Replay-Upload-Log hochgeladen, war Ziel eines gescheiterten "
                               f"Upload-Versuchs oder das Log ist nicht auswertbar ({replay.replay_dir(ch) / replay.UPLOADS}) — "
                               f"im Zweifel geschützt: nicht mehr ändern, Log prüfen. Für weitere Stufen eine neue "
                               f"Version per Neubau bauen (Stufe 1, Schritt 8).")
        if ch.read_json("timeline.json") is None:
            raise AutoCutError("timeline.json fehlt — die Beat-Positionen wurden nur berechnet; bauen erst nach autocut_build.py.")
        from niro_autocut.resolve_api import ResolveSession, connect   # lazy: Prüfung läuft auch ohne Resolve
        probe = ch.read_json("probe.json")
        if not probe or probe.get("end_frame_inclusive") is None:
            print("HINWEIS: probe.json fehlt — endFrame-Semantik nicht gemessen (Annahme wie beim Rohschnitt-Bau).")
        session = ResolveSession(connect(), probe=probe, path_map=ch.config.get("path_map"))
        print(f"Resolve: {session.version}, Projekt '{session.project_name}' ({session.project_id or 'ohne ID'})")
        vk = video_kurz(cl)
        started = _dt.datetime.now()
        items, markers = build_v3_items_v2(placed, fps)
        try:
            try:
                out = build_v3(session, name, vk, items, markers, index, ch.config)
            except Exception as e:      # jeder API-Fehler: Lauf protokollieren, nichts löschen, nichts umbenennen (Stufe-1-Timeline)
                msg = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
                ch.write_json(BUILD_FILE, {"status": "fehler", "timeline": name, "fehler": msg,
                                           "traceback": None if isinstance(e, AutoCutError) else traceback.format_exc(),
                                           "video": cl.video, "profil": args.profile, "broll_plan_hash": cutlist_hash(ppath),
                                           "projekt": session.project_name, "projekt_id": session.project_id,
                                           "resolve_version": session.version,
                                           "gestartet_am": started.isoformat(timespec="seconds"),
                                           "gebaut_am": _dt.datetime.now().isoformat(timespec="seconds"),
                                           "warnings": res.warnings + list(session.warnings)})
                hinweis = (f"V3 ist möglicherweise nur teilweise gefüllt — Timeline „{name}“ in Resolve prüfen; es wurde nichts "
                           f"gelöscht und nichts umbenannt (die Timeline stammt aus Stufe 1).")
                append_protokoll(ch, "B-Roll FEHLER", [f"V3-Bau in Timeline „{name}“ abgebrochen: {msg}", hinweis,
                                                       f"Details: {ch.autocut / BUILD_FILE}"])
                print(f"FEHLER: {msg}\n{hinweis}", file=sys.stderr)
                return 1
            out.update({"status": "ok", "video": cl.video, "profil": args.profile, "broll_plan_hash": cutlist_hash(ppath),
                        "gestartet_am": started.isoformat(timespec="seconds"),
                        "gebaut_am": _dt.datetime.now().isoformat(timespec="seconds"), "verify_warnings": res.warnings})
            r_bericht = raster(tp_dict, cl, cfg_broll, plan)
            md_path = write_report(ch, f"{vk}-broll.md", render_layout_md(plan, placed, r_bericht, index, cl,
                                                                           warnings=res.warnings, build=out, tele=tele))
            out.update({"items": [i.to_dict() for i in items], "markers": [m.to_dict() for m in markers], "placed": placed})
            try:
                out["bau_readback"] = str(RB.schreiben(ch, session, session.find_timeline(name)))
            except Exception as e:      # Zusatz für die Replay-Runde — der Bau bleibt gültig
                out["bau_readback"] = None
                out.setdefault("warnings", []).append(f"Bau-Readback nicht geschrieben: {e}")
            ch.write_json(BUILD_FILE, out)
            for w in out["warnings"]:
                print("HINWEIS:", w)
            print(f"\nGebaut: Timeline „{name}“ — {len(items)} V3-Items aus {out['clips']} Clips, {len(markers)} Marker, "
                  f"Startframe {out['start_frame']}, Projekt {'gespeichert' if out['gespeichert'] else 'NICHT gespeichert'}\n"
                  f"Dateien: {ch.autocut / BUILD_FILE}\n         {md_path}\n"
                  f"→ Review-Ablage (Pflicht): scripts/autocut_review.py \"{ch.root}\" --project \"{session.project_name}\" "
                  f"--timeline \"{name}\"")
            n_szenen = len({(p["strecke"], p["szene_i"]) for p in placed})
            n_zeitlupen = sum(1 for p in placed if p["tempo"] > 1)
            zeilen = [f"B-Roll-Layout v2 auf V3: Timeline „{name}“, {len(items)} Shots in {n_szenen} Szenen, {n_zeitlupen} "
                      f"Zeitlupen, Gesicht {r_bericht['gesicht_anteil'] * 100:.1f} % (Profil {args.profile})",
                      f"Dateien: {ch.autocut / PLAN_FILE}, {ch.autocut / BUILD_FILE}, {md_path}"]
            zeilen += [f"Warnung: {w}" for w in (res.warnings + out["warnings"])[:10]]
            append_protokoll(ch, "B-Roll auf V3", zeilen)
        finally:
            session.restore_user_timeline()
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
