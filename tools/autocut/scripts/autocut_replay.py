"""Review in Dropbox Replay: Timeline hochladen (mit Vorschau), Einsortieren vermerken, Kommentare holen
(Spec docs/superpowers/specs/2026-09-16-autocut-replay-design.md, Plan docs/superpowers/plans/2026-09-16-autocut-replay.md).

Aufruf:
    venv/bin/python scripts/autocut_replay.py "<Charge>" hochladen --project "<offenes Projekt>" [--timeline "<Name>"] [--hochladen]

hochladen ohne --hochladen = Vorschau (Resolve nur lesend). Mit --hochladen (nur nach OK des Users im Chat): Quick Export
„Replay" mit Upload für die ganze Timeline, danach Timeline, Seite und Media-Pool-Bin des Users zurück; schreibt
_intern/replay/uploads.json, _intern/replay/schnappschuesse/<Titel>.json, _intern/replay/renders/ und das Protokoll.
Exit 0 = Vorschau ok bzw. „Upload Completed", 1 = Upload nicht bestätigt, 2 = Voraussetzung fehlt.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut import replay as R  # noqa: E402
from niro_autocut import replay_kommentare as KO  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import wiedergabe as W  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll, letzte_timeline  # noqa: E402

UPLOAD_OK = "Upload Completed"


def _cfg(ch: Charge) -> dict:
    return dict(ch.config.get("replay") or {})


def _pruefen(ch: Charge, session, name: str, project: str, cfg: dict):
    """Vorbedingungen, nur lesend: Freigabe, Timeline, In/Out-Marken, Replay-Marker, Wiedergabe."""
    if session.project_name != project:
        raise AutoCutError(f"Offen ist das Projekt '{session.project_name}', freigegeben wurde '{project}'. "
                           f"Nichts hochgeladen — Projekt öffnen oder --project anpassen.")
    tl = session.find_timeline(name)
    if tl is None:
        raise AutoCutError(f"Timeline '{name}' ist nicht im offenen Projekt '{session.project_name}'.")
    marken = tl.GetMarkInOut() or {}
    if any(marken.values()):
        raise AutoCutError(f"Timeline '{name}' hat In/Out-Marken ({marken}) — in Resolve entfernen oder andere Timeline. "
                           f"Hochgeladen wird immer die ganze Timeline; Marken des Users werden nie entfernt.")
    tl_dict = session.read_timeline(tl)
    merkmal = cfg.get("dropbox_marker") or {}
    replay_marker = KO.aus_markern(tl_dict["markers"], merkmal) if merkmal else []
    if replay_marker and str(cfg.get("frameio_marker_beim_upload") or "sperren") != "erlauben":
        raise AutoCutError(f"Timeline '{name}' trägt {len(replay_marker)} Replay-Marker (Kopie einer hochgeladenen "
                           f"Timeline?) — nicht hochgeladen (replay.frameio_marker_beim_upload = sperren). Neue Version "
                           f"per Neubau oder Import anlegen; Replay-Marker nie löschen.")
    status = W.status(W.fenster_ausgabe(), tuple(cfg.get("vollbild_min") or (1900, 1000)))
    if status == "spielt_ab":
        raise AutoCutError("In Resolve läuft die Vollbild-Wiedergabe — nichts hochgeladen, später erneut.")
    return tl, tl_dict, status


def _vorschau(ch: Charge, session, tl_dict: dict, snap: dict, name: str, cfg: dict, status: str) -> list[str]:
    breite, hoehe = tl_dict.get("width"), tl_dict.get("height")
    vq = R.video_quality(breite, hoehe, cfg)
    zeilen = [f"Projekt: {session.project_name}",
              f"Timeline: {name}",
              f"Länge: {K.timecode(snap['laenge'], snap['fps'], '00:00:00:00')} ({snap['laenge']} Frames @ {snap['fps']:g} fps)",
              f"Format: {breite}×{hoehe} — Upload in Timeline-Auflösung" + (f", Bitrate-Grenze {vq} kbit/s" if vq else ""),
              f"Replay-Titel: {R.titel(name)}.mp4 (landet zuerst lose in „Your Work“)",
              f"Replay-Ordner: {R.replay_ordner(ch)} (Einsortieren danach im Chrome)",
              f"Render-Datei: {R.replay_dir(ch) / 'renders'}",
              "Hinweis: Der Upload wechselt kurz die aktive Timeline; danach sind Timeline, Seite und Bin des Users zurück."]
    if status == "unklar":
        zeilen.append("Wiedergabe nicht prüfbar (Bildschirmaufnahme-Recht?) — während des Uploads bitte nicht abspielen.")
    frueher = [e for e in R.lade_uploads(ch) if e.get("timeline") == name]
    if frueher:
        zeilen.append(f"Achtung: '{name}' wurde schon am {frueher[-1].get('hochgeladen_am')} hochgeladen — ein neuer "
                      f"Upload wird ein weiteres Video.")
    offen = R.nicht_einsortiert(ch)
    if offen:
        zeilen.append("Noch nicht einsortiert: " + ", ".join(str(e.get("titel")) for e in offen))
    return zeilen


def _hochladen(ch: Charge, session, tl, tl_dict: dict, snap: dict, name: str, cfg: dict) -> int:
    if not cfg.get("geprueft_am"):
        raise AutoCutError("replay.geprueft_am ist leer — Live-Test fehlt (Spec Abschnitt 4); nichts hochgeladen.")
    resolve, projekt, mp = session.resolve, session.project, session.media_pool
    seite = resolve.GetCurrentPage()
    ordner = mp.GetCurrentFolder()
    ordner_id = ordner.GetUniqueId() if ordner else None
    t = R.titel(name)
    preset = str(cfg.get("quickexport_preset") or "Replay")
    renders = R.replay_dir(ch) / "renders"
    ch.assert_writable(renders / f"{t}.mp4")
    renders.mkdir(parents=True, exist_ok=True)
    snap_pfad = R.replay_dir(ch) / "schnappschuesse" / f"{t}.json"
    ch.assert_writable(snap_pfad)
    snap_pfad.parent.mkdir(parents=True, exist_ok=True)
    snap_pfad.write_text(json.dumps(dict(snap, marker=tl_dict.get("markers") or {}), ensure_ascii=False, indent=1),
                         encoding="utf-8")
    einstellungen = {"TargetDir": str(renders), "CustomName": t, "EnableUpload": True}
    vq = R.video_quality(tl_dict.get("width"), tl_dict.get("height"), cfg)
    if vq:
        einstellungen["VideoQuality"] = vq
    start = time.monotonic()
    try:
        if not projekt.SetCurrentTimeline(tl):
            raise AutoCutError(f"Timeline '{name}' ließ sich nicht aktivieren — nichts hochgeladen.")
        time.sleep(2)      # wie im Liefer-Render-Rezept: direkt nach dem Wechsel liefert Resolve sonst leer
        erg = projekt.RenderWithQuickExport(preset, einstellungen) or {}
    finally:
        session.restore_user_timeline()
        if seite and resolve.GetCurrentPage() != seite:
            resolve.OpenPage(seite)
        if ordner_id and mp.GetCurrentFolder().GetUniqueId() != ordner_id:
            for f in session.all_folders():
                if f.GetUniqueId() == ordner_id:
                    mp.SetCurrentFolder(f)
                    break
    dauer = round(time.monotonic() - start, 1)
    status = str(erg.get("JobStatus") or "")
    dateien = sorted(renders.glob(f"{t}.*"), key=lambda p: p.stat().st_mtime)
    eintrag = {"titel": t, "timeline": name, "projekt": session.project_name, "hochgeladen_am": R.jetzt(),
               "weg": "quickexport", "preset": preset, "breite": tl_dict.get("width"), "hoehe": tl_dict.get("height"),
               "video_quality": vq, "datei": str(dateien[-1]) if dateien else None, "frames": snap["laenge"],
               "fps": snap["fps"], "upload_status": status, "dauer_s": dauer, "schnappschuss": str(snap_pfad),
               "replay_ordner": R.replay_ordner(ch), "einsortiert_am": None, "rueckgabe": erg}
    R.speichere_upload(ch, eintrag)
    zeilen = [f"Replay-Upload „{t}.mp4“ aus Timeline „{name}“ (Projekt {session.project_name}): "
              f"{status or 'kein Status'} nach {dauer} s",
              f"Replay-Ordner (Einsortieren im Chrome): {eintrag['replay_ordner']}",
              f"Upload-Log: {R.replay_dir(ch) / R.UPLOADS}"]
    append_protokoll(ch, "Replay-Upload", zeilen)
    print("\n".join(zeilen))
    if status != UPLOAD_OK:
        print(f"FEHLER: Upload nicht bestätigt ({erg}). Anmeldung prüfen: Resolve → Einstellungen → System → "
              f"Internet-Konten → Dropbox. Neuer Versuch nur nach neuem OK.", file=sys.stderr)
        return 1
    return 0


def schritt_hochladen(ch: Charge, args) -> int:
    cfg = _cfg(ch)
    name = args.timeline or letzte_timeline(ch)
    session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
    tl, tl_dict, status = _pruefen(ch, session, name, args.project, cfg)
    snap = K.snapshot_from_readback(tl_dict, session.project_name)
    print("\n".join(_vorschau(ch, session, tl_dict, snap, name, cfg, status)))
    if not args.hochladen:
        print("\nVorschau — nichts hochgeladen. Hochladen erst nach OK im Chat: dieselbe Zeile mit --hochladen.")
        return 0
    return _hochladen(ch, session, tl, tl_dict, snap, name, cfg)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Review in Dropbox Replay.")
    ap.add_argument("pfad", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    sub = ap.add_subparsers(dest="schritt", required=True)
    h = sub.add_parser("hochladen", help="Vorschau; mit --hochladen Upload nach OK des Users")
    h.add_argument("--project", required=True, help="Name des offenen, freigegebenen Resolve-Projekts")
    h.add_argument("--timeline", help="exakter Timeline-Name (Standard: zuletzt gebaute AutoCut-Timeline)")
    h.add_argument("--hochladen", action="store_true", help="wirklich hochladen (nur nach OK im Chat)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open_basis(args.pfad)
        return schritt_hochladen(ch, args)
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
