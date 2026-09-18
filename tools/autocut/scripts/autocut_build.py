"""Rohschnitt-Timeline in DaVinci Resolve bauen (Spec 3.5) — Pflicht davor: autocut_verify.py.

Aufruf:
    venv/bin/python scripts/autocut_build.py "<Charge>" [--name "<Timeline-Name>"] [--dry-run]

Liest    <Charge>/_intern/autocut/cutlist.json, verify.json (muss ok sein, Hash muss zur Cutlist passen),
         media.json, sync.json, probe.json (optional, endFrame-Semantik), Transkript-Index + Cache der Charge.
Schreibt <Charge>/_intern/autocut/timeline.json (TimelinePlan + Timeline-Name + Startframe),
         build.json (Lauf-Protokoll inkl. Projektname/-ID, SaveProject-Rückgabe, Warnungen),
         Ergebnisse/Rohschnitt/<video>-rohschnitt.md (über report.py, Task 9), Protokoll-Eintrag.
Resolve: nur NEUE Bin „AutoCut/<video>" (Medien darin, Dedupe per Pfad) und eine NEUE Timeline
         „AutoCut <video> <JJJJ-MM-TT HHMM>". Bricht ein API-Schritt ab, wird die angefangene Timeline in
         „… FEHLER" umbenannt und nichts gelöscht (Spec 6).
--dry-run: Plan rechnen und zusammenfassen, Resolve nicht anfassen, nichts schreiben.

Exit 0 = gebaut, 1 = Fehler beim Bau, 2 = Vorbedingung fehlt (erst autocut_verify.py / autocut_prepare.py).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import readback as RB  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.cutlist import Cutlist, cutlist_hash  # noqa: E402
from niro_autocut.timeline_model import TimelinePlan, build_timeline_plan  # noqa: E402


class PreconditionError(AutoCutError):
    """Vorbedingung fehlt — Exit 2, damit der Aufrufer weiß: erst verify/prepare."""


def _mmss(frames: int, fps: float) -> str:
    s = int(round(frames / fps)) if fps else 0
    return f"{s // 60:02d}:{s % 60:02d}"


def check_verified(ch: Charge, cutlist_path: Path) -> dict:
    """verify.json muss existieren, ok sein und den Hash der aktuellen cutlist.json tragen."""
    verify = ch.read_json("verify.json")
    if not verify:
        raise PreconditionError(f"{ch.autocut / 'verify.json'} fehlt — erst scripts/autocut_verify.py ausführen.")
    if verify.get("cutlist_hash") != cutlist_hash(cutlist_path):
        raise PreconditionError("cutlist.json wurde seit der letzten Prüfung geändert — erst scripts/autocut_verify.py "
                                "erneut ausführen.")
    if not verify.get("ok"):
        raise PreconditionError(f"Cutlist ist nicht ok ({len(verify.get('errors') or [])} Fehler laut verify.json) — "
                                f"Fehler beheben und scripts/autocut_verify.py erneut ausführen.")
    return verify


def words_by_clip(ch: Charge) -> dict[str, list[dict]]:
    """Wörter je Clip-Pfad aus Transkript-Index + Scribe-Cache (Schlüssel wie in cutlist.json: rec['path'])."""
    out: dict[str, list[dict]] = {}
    for rec in ch.load_index():
        cached = ch.cache_transcript(rec["fingerprint"]) if rec.get("fingerprint") else None
        if cached and cached.get("words") is not None:
            out[rec["path"]] = cached["words"]
    return out


def check_files(tp: TimelinePlan, map_path=None) -> None:
    missing = set()
    for it in tp.items:
        at = map_path(it.clip) if map_path else it.clip
        if not Path(at).is_file():
            missing.add(at)
    if missing:
        raise PreconditionError("Clip-Dateien nicht erreichbar (NAS/SSD gemountet? path_map in config.yaml?):\n  "
                                + "\n  ".join(sorted(missing)))


def plan_summary(tp: TimelinePlan) -> list[str]:
    by_track: dict[str, int] = {}
    for it in tp.items:
        by_track[it.track] = by_track.get(it.track, 0) + 1
    tracks = ", ".join(f"{k} {by_track[k]}" for k in ("V1", "A1", "V2", "V3") if k in by_track)
    v2_fehlt = [m.name for m in tp.markers if m.name.startswith("V2 fehlt")]
    lines = [f"{len(tp.items)} Items ({tracks}), {len(tp.markers)} Marker, {len(tp.beats)} Beats, "
             f"Länge {_mmss(tp.total_frames, tp.fps)} ({tp.total_frames} Frames @ {tp.fps:g} fps, {tp.width}x{tp.height})"]
    if v2_fehlt:
        lines.append(f"V2 fehlt bei {len(v2_fehlt)} Schnitt(en): " + "; ".join(v2_fehlt))
    return lines


def write_report(ch: Charge, cl: Cutlist, tp: TimelinePlan, sync: dict, build: dict, verify: dict,
                 media: dict) -> tuple[Path | None, str, list[str]]:
    """Bericht über report.py (Task 9) — fehlt das Modul oder die Funktion, sauber melden statt abbrechen.

    Gibt (Pfad | None, Hinweis, Protokoll-Zeilen aus report.py) zurück; die Zeilen sind leer ohne report.py.
    """
    try:
        from niro_autocut import report  # noqa: WPS433 — lazy, Task 9 kann später kommen
        render, write = report.render_rohschnitt, report.write_report
    except (ImportError, AttributeError) as e:
        return None, f"Bericht übersprungen: report.py (Task 9) nicht verfügbar ({e}).", []
    text = render(cl, tp, sync, build, verify, media)
    path = write(ch, f"{Path(cl.video).stem}-rohschnitt.md", text)
    zeilen_fn = getattr(report, "protokoll_zeilen_rohschnitt", None)
    zeilen = list(zeilen_fn(cl, tp, build, verify, path)) if zeilen_fn else []
    return path, "Bericht geschrieben.", zeilen


def _rename_failed(session: RA.ResolveSession, name: str) -> str | None:
    tl = session.current_timeline
    if tl is None or RA._safe(tl.GetName, None) != name:
        return None
    failed = name + " FEHLER"
    return failed if RA._safe(tl.SetName, False, failed) else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Rohschnitt-Timeline in Resolve bauen (Spec 3.5).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--name", help="Timeline-Name (Standard: '<prefix> <video> <JJJJ-MM-TT HHMM>')")
    ap.add_argument("--dry-run", action="store_true", help="nur rechnen und zusammenfassen, Resolve nicht anfassen")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        cpath = ch.autocut / "cutlist.json"
        if not cpath.exists():
            raise PreconditionError(f"{cpath} fehlt — Cutlist nach prompts/cutlist.md erstellen und prüfen.")
        cl = Cutlist.load(cpath)
        verify = check_verified(ch, cpath)
        media = ch.read_json("media.json")
        if not media:
            raise PreconditionError(f"{ch.autocut / 'media.json'} fehlt — erst scripts/autocut_prepare.py ausführen.")
        warnungen: list[str] = []
        sync = ch.read_json("sync.json")
        if not sync:
            sync = {"fps": media["format"]["fps"], "paare": []}
            warnungen.append("sync.json fehlt — V2/A2 bleiben leer (erst scripts/autocut_sync.py, wenn a7-Material da ist).")
        tp = build_timeline_plan(cl, media, sync, words_by_clip(ch), ch.config)
        if not tp.items:
            raise PreconditionError("Die Cutlist ergibt keine Timeline-Items (keine O-Ton-Beats?).")
        check_files(tp, map_path=ch.map_path)
        print(f"Charge:  {ch.root}\nPlan:    " + "\n         ".join(plan_summary(tp)))
        for w in warnungen:
            print("WARNUNG:", w)
        if args.dry_run:
            print("Probelauf — Resolve nicht angefasst, nichts geschrieben.")
            return 0

        probe = ch.read_json("probe.json")
        if not probe or probe.get("end_frame_inclusive") is None:
            warnungen.append("probe.json fehlt — endFrame-Semantik nicht gemessen (Annahme: inklusiv); der Readback "
                             "bricht bei Abweichung ab. Empfohlen: scripts/resolve_probe.py vorher ausführen.")
            print("WARNUNG:", warnungen[-1])
        rcfg = ch.config["resolve"]
        video_kurz = Path(cl.video).stem
        suffix = str(rcfg.get("roh_suffix") or " (roh)")
        name = args.name or (RA.timeline_name(str(rcfg["timeline_prefix"]), video_kurz) + suffix)
        if not name.endswith(suffix):
            name += suffix
        session = RA.ResolveSession(RA.connect(), probe=probe, path_map=ch.config.get("path_map"))
        print(f"Resolve: {session.version}, Projekt '{session.project_name}' ({session.project_id or 'ohne ID'})")
        if session.find_timeline(name) is not None:
            raise AutoCutError(f"Timeline '{name}' existiert bereits — eine Minute warten oder --name setzen.")
        started = _dt.datetime.now()
        try:
            try:
                res = RA.build_from_plan(session, tp, media, name, ch.config)
            except Exception as e:      # jeder API-Fehler: Timeline kennzeichnen, Lauf protokollieren, nichts löschen
                failed = _rename_failed(session, name)
                msg = str(e) if isinstance(e, AutoCutError) else f"{type(e).__name__}: {e}"
                ch.write_json("build.json", {
                    "status": "fehler", "timeline": failed or name, "timeline_umbenannt": failed is not None,
                    "fehler": msg, "traceback": traceback.format_exc() if not isinstance(e, AutoCutError) else None,
                    "project": session.project_name, "project_id": session.project_id,
                    "resolve_version": session.version, "video": cl.video, "cutlist_hash": verify["cutlist_hash"],
                    "gestartet_am": started.isoformat(timespec="seconds"), "warnings": warnungen + session.warnings})
                append_protokoll(ch, "Rohschnitt FEHLER", [
                    f"Bau der Timeline '{name}' abgebrochen: {msg}",
                    (f"Angefangene Timeline heißt jetzt '{failed}' (nichts gelöscht)." if failed
                     else "Keine Timeline angelegt oder Umbenennung nicht möglich."),
                    f"Details: {ch.autocut / 'build.json'}"])
                print(f"FEHLER: {msg}", file=sys.stderr)
                if failed:
                    print(f"Angefangene Timeline umbenannt: '{failed}' — in Resolve prüfen, nichts wurde gelöscht.",
                          file=sys.stderr)
                return 1

            res["warnings"] = warnungen + list(res.get("warnings") or [])
            stamp = _dt.datetime.now().isoformat(timespec="seconds")
            tl_json = ch.write_json("timeline.json", {
                **tp.to_dict(), "timeline": name, "timeline_id": res.get("timeline_id", ""),
                "start_frame": res["start_frame"], "end_frame_inclusive": res["end_frame_inclusive"],
                "video": cl.video, "project": res["project"], "gebaut_am": stamp})
            build = {**res, "status": "ok", "video": cl.video, "cutlist_hash": verify["cutlist_hash"],
                     "gestartet_am": started.isoformat(timespec="seconds"), "gebaut_am": stamp,
                     "laenge_frames": tp.total_frames, "laenge": _mmss(tp.total_frames, tp.fps),
                     "fps": tp.fps, "width": tp.width, "height": tp.height, "timeline_json": str(tl_json),
                     "roh": True, "roh_suffix": suffix, "timeline_final": name[: -len(suffix)]}
            report_path, report_note, report_zeilen = write_report(ch, cl, tp, sync, build, verify, media)
            build["bericht"] = str(report_path) if report_path else None
            if report_path is None:
                build["bericht_hinweis"] = report_note
            try:
                build["bau_readback"] = str(RB.schreiben(ch, session, session.find_timeline(name)))
            except Exception as e:      # Zusatz für die Replay-Runde — der Bau bleibt gültig
                build["bau_readback"] = None
                res["warnings"].append(f"Bau-Readback nicht geschrieben: {e}")
            build_json = ch.write_json("build.json", build)

            dateien = [str(tl_json), str(build_json)] + ([str(report_path)] if report_path else [])
            zeilen = list(report_zeilen) + [
                f"Resolve: Projekt '{res['project']}', Bin {res['bin']}, {res['items']} Items, {res['markers']} Marker, "
                f"SaveProject {'ok' if res['saved'] else 'NICHT bestätigt'}",
                f"Dateien: {', '.join(dateien)}"]
            if not report_zeilen:
                zeilen.insert(0, f"Rohschnitt gebaut: Timeline '{name}' aus {cl.video}, Länge {build['laenge']}")
                if res["warnings"]:
                    zeilen.append(f"{len(res['warnings'])} Warnung(en): " + " | ".join(res["warnings"]))
            if report_path is None:
                zeilen.append(report_note)
            append_protokoll(ch, "Rohschnitt", zeilen)

            print(f"\nTimeline '{name}' gebaut (roh — Pegel/Zeitlupe kommen mit scripts/autocut_finalize.py): "
                  f"{res['items']} Items, {res['markers']} Marker, Länge {build['laenge']}, "
                  f"Bin {res['bin']}, {res['clips']} Clips ({res['proxies_linked']} Proxys verknüpft), "
                  f"SaveProject {'ok' if res['saved'] else 'NICHT bestätigt'}")
            for w in res["warnings"]:
                print("WARNUNG:", w)
            print(report_note if report_path is None else f"Bericht: {report_path}")
            print(f"Geschrieben: {tl_json}\n             {build_json}")
            print(f"→ Review-Ablage (Pflicht): scripts/autocut_review.py \"{ch.root}\" --project \"{session.project_name}\"")
            return 0
        finally:
            session.restore_user_timeline()
    except PreconditionError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
