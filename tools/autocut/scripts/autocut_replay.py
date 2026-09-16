"""Review in Dropbox Replay: Timeline hochladen (mit Vorschau), Einsortieren vermerken, Kommentare holen
(Spec docs/superpowers/specs/2026-09-16-autocut-replay-design.md, Plan docs/superpowers/plans/2026-09-16-autocut-replay.md).

Aufruf:
    venv/bin/python scripts/autocut_replay.py "<Charge>" hochladen --project "<offenes Projekt>" [--timeline "<Name>"] [--hochladen]
    venv/bin/python scripts/autocut_replay.py "<Charge>" einsortiert --titel "<Titel>" [--ordner "<Replay-Pfad>"]
    venv/bin/python scripts/autocut_replay.py "<Charge>" kommentare [--timeline "<Name>"] [--aus-json "<Datei>"] [--warten <s>]
    venv/bin/python scripts/autocut_replay.py "<Projekt-Ordner>" finden --titel "<Replay-Titel>"

hochladen ohne --hochladen = Vorschau (Resolve nur lesend). Mit --hochladen (nur nach OK des Users im Chat): Quick Export
„Replay" mit Upload für die ganze Timeline, danach Timeline, Seite und Media-Pool-Bin des Users zurück; schreibt
_intern/replay/uploads.json, _intern/replay/schnappschuesse/<Titel>.json, _intern/replay/renders/ und das Protokoll.
Exit 0 = Vorschau ok bzw. „Upload Completed", 1 = Upload nicht bestätigt, 2 = Voraussetzung fehlt.
einsortiert vermerkt das Einsortieren in Replay (macht Claude im Chrome). kommentare liest die Replay-Kommentare
(Marker mit replay.dropbox_marker) der hochgeladenen Timeline nur lesend oder übernimmt die Chrome-Lesung (--aus-json)
und schreibt Material/Feedback/<Upload-Datum> Replay <Titel>/kommentare.json + .md; Exit 0 = neue Kommentare,
1 = keine neuen, 2 = Voraussetzung. finden ordnet einen Replay-Titel über die Upload-Logs der Chargen zu;
Exit 0 = gefunden (JSON), 1 = nicht von AutoCut hochgeladen.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut import readback as RB  # noqa: E402
from niro_autocut import replay as R  # noqa: E402
from niro_autocut import replay_kommentare as KO  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import wiedergabe as W  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll, letzte_timeline  # noqa: E402

UPLOAD_OK = "Upload Completed"
WARTE_TAKT_S = 30


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
        # Jeder Wiederherstellungsschritt einzeln über RA._safe (nie werfend): ein API-Fehler (echtes Resolve) darf
        # weder einen ursprünglichen Fehler aus dem try-Block verdecken noch die übrigen Schritte verhindern.
        session.restore_user_timeline()
        aktuelle_seite = RA._safe(resolve.GetCurrentPage, seite)
        if seite and aktuelle_seite != seite:
            RA._safe(resolve.OpenPage, None, seite)
        aktueller_ordner_id = RA._safe(lambda: mp.GetCurrentFolder().GetUniqueId(), ordner_id)
        if ordner_id and aktueller_ordner_id != ordner_id:
            for f in RA._safe(session.all_folders, []) or []:
                if RA._safe(f.GetUniqueId, None) == ordner_id:
                    RA._safe(mp.SetCurrentFolder, None, f)
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


def schritt_einsortiert(ch: Charge, args) -> int:
    ordner = args.ordner or R.replay_ordner(ch)
    e = R.setze_einsortiert(ch, args.titel, ordner)
    append_protokoll(ch, "Replay einsortiert", [f"„{e['titel']}.mp4“ liegt in Replay unter {ordner}"])
    print(f"Vermerkt: {e['titel']} → {ordner} ({e['einsortiert_am']})")
    return 0


def schritt_finden(args) -> int:
    projekt = Path(args.pfad).expanduser().resolve()
    if not projekt.is_dir():
        raise AutoCutError(f"Projekt-Ordner nicht gefunden: {projekt}")
    treffer = R.finde_upload(projekt, args.titel)
    if treffer is None:
        print(f"Kein Upload mit Titel '{args.titel}' in den Chargen von {projekt} — nicht von AutoCut hochgeladen, "
              f"nicht anfassen.")
        return 1
    charge, e = treffer
    print(json.dumps({"charge": str(charge), "timeline": e.get("timeline"), "projekt": e.get("projekt"),
                      "hochgeladen_am": e.get("hochgeladen_am")}, ensure_ascii=False))
    return 0


def schritt_kommentare(ch: Charge, args) -> int:
    cfg = _cfg(ch)
    eintrag = R.upload_eintrag(ch, timeline=args.timeline)
    sp = Path(str(eintrag.get("schnappschuss") or ""))
    if not sp.is_file():
        raise AutoCutError(f"Upload-Schnappschuss fehlt: {sp}")
    snap_upload = json.loads(sp.read_text(encoding="utf-8"))
    fps, start_tc = float(snap_upload["fps"]), str(snap_upload["start_timecode"])
    snap_jetzt = None
    if args.aus_json:
        p = Path(args.aus_json).expanduser()
        if not p.is_file():
            raise AutoCutError(f"--aus-json nicht gefunden: {p}")
        kommentare, weg = KO.aus_json(json.loads(p.read_text(encoding="utf-8")), fps), "chrome"
    else:
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
        tl = session.find_timeline(eintrag["timeline"])
        if tl is None:
            raise AutoCutError(f"Timeline '{eintrag['timeline']}' ist nicht im offenen Projekt '{session.project_name}' — "
                               f"Projekt '{eintrag.get('projekt')}' öffnen (nur lesen) oder Kommentare im Chrome lesen "
                               f"(--aus-json).")
        warten = int(cfg.get("sync_warten_s") or 0) if args.warten is None else int(args.warten)
        merkmal = cfg.get("dropbox_marker") or {}
        ende = time.monotonic() + max(0, warten)
        while True:
            tl_dict = session.read_timeline(tl)
            kommentare = KO.aus_markern(tl_dict["markers"], merkmal, snap_upload.get("marker"))
            if kommentare or time.monotonic() >= ende:
                break
            time.sleep(WARTE_TAKT_S)
        snap_jetzt = K.snapshot_from_readback(tl_dict, session.project_name)
        weg = "api"
    for k in kommentare:
        k["tc"] = K.timecode(k["frame"], fps, start_tc)
        k["clips"] = KO.clips_an(snap_upload, k["frame"])
    aenderungen = KO.vergleiche(snap_upload, snap_jetzt) if snap_jetzt is not None else None
    if aenderungen:
        for k in kommentare:
            k["frame_aktuell"] = KO.frame_im_stand(k["clips"], snap_jetzt)
    bau = RB.laden(ch, eintrag["timeline"])
    ordner = R.feedback_ordner(ch, eintrag)
    vorher_pfad = ordner / "kommentare.json"
    vorher = json.loads(vorher_pfad.read_text(encoding="utf-8")) if vorher_pfad.exists() else None
    zeit = R.jetzt()
    n_neu = KO.markiere_neu(kommentare, vorher, zeit)
    n_fremd = KO.markiere_fremde(kommentare, list(cfg.get("eigene_autoren") or []))
    doc = {"titel": eintrag["titel"], "timeline": eintrag["timeline"], "projekt": eintrag.get("projekt"),
           "hochgeladen_am": eintrag.get("hochgeladen_am"), "replay_ordner": eintrag.get("replay_ordner"),
           "lese_weg": weg, "gelesen_am": zeit, "anzahl": len(kommentare), "neu": n_neu, "fremd": n_fremd,
           "veraendert_seit_upload": None if aenderungen is None else bool(aenderungen),
           "aenderungen": aenderungen or [],
           "seit_bau_veraendert": None if bau is None else bool(KO.vergleiche(bau, snap_upload)),
           "kommentare": kommentare}
    for dateiname, inhalt in (("kommentare.json", json.dumps(doc, ensure_ascii=False, indent=1)),
                              ("kommentare.md", KO.kommentare_md(doc))):
        ziel = ordner / dateiname
        ch.assert_writable(ziel)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(inhalt, encoding="utf-8")
    stand = ("nicht geprüft (Chrome)" if aenderungen is None else "verändert — Stellen über Clips" if aenderungen
             else "unverändert")
    seit_bau = ("unbekannt (kein Bau-Readback)" if bau is None else "von Hand geändert" if doc["seit_bau_veraendert"]
                else "unverändert")
    zeilen = [f"Replay-Kommentare „{eintrag['titel']}“ ({weg}): {len(kommentare)} gesamt, {n_neu} neu, "
              f"{n_fremd} von fremden Autoren",
              f"Stand seit Upload: {stand}; seit Bau: {seit_bau}",
              f"Datei: {ordner / 'kommentare.md'}"]
    append_protokoll(ch, "Replay-Kommentare", zeilen)
    print("\n".join(zeilen))
    return 0 if n_neu else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Review in Dropbox Replay (hochladen, einsortiert, kommentare, finden).")
    ap.add_argument("pfad", help="Chargen-Ordner (bei „finden“: Projekt-Ordner projects/<Kunde>/<Projekt>)")
    sub = ap.add_subparsers(dest="schritt", required=True)
    h = sub.add_parser("hochladen", help="Vorschau; mit --hochladen Upload nach OK des Users")
    h.add_argument("--project", required=True, help="Name des offenen, freigegebenen Resolve-Projekts")
    h.add_argument("--timeline", help="exakter Timeline-Name (Standard: zuletzt gebaute AutoCut-Timeline)")
    h.add_argument("--hochladen", action="store_true", help="wirklich hochladen (nur nach OK im Chat)")
    e = sub.add_parser("einsortiert", help="Einsortieren in Replay vermerken")
    e.add_argument("--titel", required=True, help="Replay-Titel ohne .mp4")
    e.add_argument("--ordner", help="Replay-Pfad (Standard aus replay.ordner)")
    k = sub.add_parser("kommentare", help="Replay-Kommentare holen")
    k.add_argument("--timeline", help="hochgeladene Timeline (Standard: jüngster Upload)")
    k.add_argument("--aus-json", help="Chrome-Lesung statt Resolve")
    k.add_argument("--warten", type=int, help="Sekunden, die bei 0 Kommentaren nachgelesen wird (Standard replay.sync_warten_s)")
    f = sub.add_parser("finden", help="Replay-Titel → Charge und Timeline")
    f.add_argument("--titel", required=True, help="Replay-Titel, mit oder ohne .mp4")
    args = ap.parse_args(argv)
    try:
        if args.schritt == "finden":
            return schritt_finden(args)
        ch = Charge.open_basis(args.pfad)
        schritte = {"hochladen": schritt_hochladen, "einsortiert": schritt_einsortiert, "kommentare": schritt_kommentare}
        return schritte[args.schritt](ch, args)
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
