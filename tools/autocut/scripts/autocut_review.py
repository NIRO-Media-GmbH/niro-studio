"""Review-Ablage nach jedem Bau (Pflicht seit 18.09.2026): Timeline aus dem offenen Resolve-Projekt über die Render-Queue
rendern (MP4/H.265, lange Kante ≤ 1920 px, ganze Timeline) und als Version in NIRO Review ablegen (tools/review,
Ablauf tools/review/WORKFLOW-Review.md). Ersetzt das Replay-Angebot nach Rohschnitt, B-Roll, Finalisieren und Feinschnitt.

Aufruf (autocut-venv):
    venv/bin/python scripts/autocut_review.py "<Charge>" --project "<offenes Projekt>" [--timeline "<Name>" …]
        [--video "<Titel>"] [--notiz "…"] [--version N] [--umsetzung <umsetzung.json>] [--codec H265|H264] [--vorschau]
    venv/bin/python scripts/autocut_review.py "<Charge>" --datei "<fertiger Render>" [--video "<Titel>"] [--notiz "…"] …

Ohne --timeline nimmt es die zuletzt gebaute Timeline (feinschnitt.json, finalize.json, build.json). --vorschau prüft nur
(Resolve nur lesend) und zeigt Titel, Version, Format, Zielpfad. --datei legt einen vorhandenen Render ab, ohne Resolve.
Render: <Charge>/Ergebnisse/Export/Review/<Timeline>.mp4. Video-Titel (ein Titel über alle Stufen desselben Videos):
--video, sonst aus dem Timeline-Namen ohne Präfix/Zeitstempel/„(roh)“/Stufenwort. Notiz: Stufe · Timeline · Projekt · --notiz.
Version: ohne --version die nächste freie des Videos im Review (die Vorschau nennt sie); eine Versionsmarke im
Timeline-Namen („…_V3“) ist die Resolve-Zählung und zählt dafür nicht.
Exit 0 = abgelegt, 1 = Eingabe/Freigabe/Timeline, 2 = Voraussetzung (Resolve, NAS, ffmpeg, Render gescheitert).
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

HIER = Path(__file__).resolve()
sys.path.insert(0, str(HIER.parents[1] / "src"))
sys.path.insert(0, str(HIER.parents[2] / "review" / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import review_render as RR  # noqa: E402
from niro_autocut import wiedergabe as W  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll, letzte_timeline  # noqa: E402
from niro_review import ablage as RV_ABLAGE  # noqa: E402
from niro_review import cli as RV  # noqa: E402
from niro_review import modell as RV_MODELL  # noqa: E402
from niro_review.ablage import ReviewFehler  # noqa: E402


class Voraussetzung(AutoCutError):
    """Exit 2: NAS, Resolve, ffmpeg oder ein gescheiterter Render — nichts am Werkzeugaufruf falsch."""


def charge_oeffnen(root: str) -> Charge:
    ch = Charge.open_basis(root)
    return dataclasses.replace(ch, zusatz_schreibbereiche=(*ch.zusatz_schreibbereiche, ch.root / "Ergebnisse" / "Export" / "Review"))


def charge_rel(ch: Charge) -> str:
    return RV_ABLAGE.ziel_aufloesen(str(ch.root)).charge or ""


def _umsetzung(pfad: str | None) -> dict | None:
    if not pfad:
        return None
    daten = RV_ABLAGE.json_lesen(Path(pfad))
    if not isinstance(daten, dict):
        raise AutoCutError(f"--umsetzung: {pfad} fehlt oder ist kein JSON-Objekt.")
    return daten


def naechste_nummern(ch: Charge, titel: list[str]) -> list[int]:
    """Nummern, die die Ablage ohne --version vergibt (version_anlegen): die nächste freie Version des Videos im
    Review, bei mehreren Timelines desselben Titels fortlaufend. Die Versionsmarke im Timeline-Namen zählt nicht."""
    out, weiter = [], {}
    for t in titel:
        if t not in weiter:
            weiter[t] = RV_MODELL.naechste_version(RV_MODELL.video_ordner(ch.kunde, ch.projekt, t))
        out.append(weiter[t])
        weiter[t] += 1
    return out


def _version_text(nr: int | None, naechste: int) -> str:
    return f"V{nr}" if nr else f"V{naechste} (nächste Version)"


def ablegen(ch: Charge, titel: str, datei: Path, notiz: str, nr: int | None, umsetzung: dict | None) -> dict:
    """Version in NIRO Review anlegen (Kopie/Umkodierung, Vorschaubild, NAS) — Exit-Codes der Review-CLI übernehmen."""
    try:
        return RV.version_anlegen(ch.kunde, ch.projekt, charge_rel(ch), titel, datei, nr, notiz, None, None, False, umsetzung)
    except ReviewFehler as e:
        raise (Voraussetzung if e.code == 2 else AutoCutError)(f"Review-Ablage: {e}") from e


def _pruefen_resolve(session, project: str, namen: list[str]):
    if session.project_name != project:
        raise AutoCutError(f"Offen ist das Projekt '{session.project_name}', freigegeben wurde '{project}'. "
                           f"Nichts gerendert — Projekt öffnen oder --project anpassen.")
    if session.project.IsRenderingInProgress():
        raise Voraussetzung("Resolve rendert gerade — nichts gestartet, später erneut.")
    status = W.status(W.fenster_ausgabe())
    if status == "spielt_ab":
        raise AutoCutError("In Resolve läuft die Vollbild-Wiedergabe — nichts gerendert, später erneut.")
    tls, dicts = {}, {}
    for name in namen:
        tl = session.find_timeline(name)
        if tl is None:
            raise AutoCutError(f"Timeline '{name}' ist nicht im offenen Projekt '{session.project_name}'.")
        marken = tl.GetMarkInOut() or {}
        if any(marken.values()):
            raise AutoCutError(f"Timeline '{name}' hat In/Out-Marken ({marken}) — in Resolve entfernen (der Queue-Render löscht "
                               f"sie sonst, gerendert wird immer die ganze Timeline).")
        tls[name] = tl
        dicts[name] = session.read_timeline(tl)
    return tls, dicts, status


def _zeile_vorschau(ch: Charge, name: str, d: dict, titel: str, stufe: str, nr, naechste: int, ziel: Path) -> str:
    snap = K.snapshot_from_readback(d, d.get("name") or "")
    b, h = RR.zielformat(d.get("width"), d.get("height"))
    return (f"· „{name}“ → Review „{titel}“ {_version_text(nr, naechste)} · Stufe „{stufe}“ · "
            f"{K.timecode(snap['laenge'], snap['fps'], '00:00:00:00')} "
            f"({snap['laenge']} Frames @ {snap['fps']:g} fps) · {d.get('width')}×{d.get('height')} → {b}×{h} · "
            f"{ziel / (RR.render_dateiname(name) + '.mp4')}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Review-Ablage nach dem Bau: Queue-Render + NIRO Review")
    ap.add_argument("charge")
    ap.add_argument("--project", help="Name des offenen, freigegebenen Resolve-Projekts (Pflicht ohne --datei)")
    ap.add_argument("--timeline", action="append", help="Timeline (mehrfach möglich; Standard: zuletzt gebaute)")
    ap.add_argument("--datei", help="fertiger Render statt Resolve")
    ap.add_argument("--video", help="Review-Titel (Standard: aus dem Timeline-Namen)")
    ap.add_argument("--notiz", default="", help="Zusatz zur Notiz der Version")
    ap.add_argument("--version", dest="nr", type=int, help="Versionsnummer (Standard: nächste)")
    ap.add_argument("--umsetzung", help="umsetzung.json für die Vorversion (nur bei genau einer Timeline/Datei)")
    ap.add_argument("--codec", default="H265", choices=["H265", "H264"])
    ap.add_argument("--vorschau", action="store_true", help="nur prüfen und zeigen, nichts rendern/ablegen")
    args = ap.parse_args(argv)
    try:
        ch = charge_oeffnen(args.charge)
        umsetzung = _umsetzung(args.umsetzung)
        if not RV_ABLAGE.nas_verbunden():
            raise Voraussetzung(f"NAS nicht verbunden ({RV_ABLAGE.review_wurzel().parent}) — Review-Ablage nicht möglich.")
        if args.datei:
            datei = Path(args.datei).expanduser()
            if not datei.is_file():
                raise AutoCutError(f"Datei fehlt: {datei}")
            titel = args.video or RR.titel_aus_timeline(datei.stem)
            notiz = RR.notiz_bauen(RR.stufe_aus_timeline(datei.stem), datei.stem, "Datei", args.notiz)
            if args.vorschau:
                print(f"· {datei.name} → Review „{titel}“ {_version_text(args.nr, naechste_nummern(ch, [titel])[0])} "
                      f"— Vorschau, nichts abgelegt.")
                return 0
            e = ablegen(ch, titel, datei, notiz, args.nr, umsetzung)
            link = RV.link(ch.kunde, ch.projekt, e["titel"])
            zeilen = [f"„{datei.name}“ → Review „{e['titel']}“ V{e['nr']} ({e['weg']}, {e['version']['breite']}×{e['version']['hoehe']}, "
                      f"{e['version']['dauer_s']:.2f} s) · {link}"]
            append_protokoll(ch, "Review-Ablage", zeilen)
            print("\n".join(zeilen))
            return 0
        if not args.project:
            raise AutoCutError("--project „<offenes Projekt>“ fehlt (Freigabe des Users für dieses Projekt).")
        namen = args.timeline or [letzte_timeline(ch)]
        if umsetzung is not None and len(namen) != 1:
            raise AutoCutError("--umsetzung geht nur mit genau einer Timeline.")
        if args.video and len(namen) != 1:
            raise AutoCutError("--video geht nur mit genau einer Timeline (sonst Titel aus den Timeline-Namen).")
        try:
            session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
        except AutoCutError as e:
            raise Voraussetzung(str(e)) from e
        tls, dicts, status = _pruefen_resolve(session, args.project, namen)
        ziel = ch.root / "Ergebnisse" / "Export" / "Review"
        titel = {n: (args.video or RR.titel_aus_timeline(n)) for n in namen}
        stufen = {n: RR.stufe_aus_timeline(n) for n in namen}
        naechste = dict(zip(namen, naechste_nummern(ch, [titel[n] for n in namen])))
        print(f"Resolve {session.version}, Projekt '{session.project_name}'")
        for n in namen:
            print(_zeile_vorschau(ch, n, dicts[n], titel[n], stufen[n], args.nr, naechste[n], ziel))
        if status == "unklar":
            print("Wiedergabe nicht prüfbar (Bildschirmaufnahme-Recht?) — während des Renders bitte nicht abspielen.")
        if args.vorschau:
            print("Vorschau — nichts gerendert, nichts abgelegt.")
            return 0
        ch.assert_writable(ziel / "x.mp4")
        ziel.mkdir(parents=True, exist_ok=True)
        user_tl = session.project.GetCurrentTimeline()
        if not RR.playhead_ruhig(user_tl):
            raise AutoCutError("Der User spielt seit einer Minute ab — nichts gerendert, später erneut.")
        user_tc = user_tl.GetCurrentTimecode() if user_tl else None
        mp = session.media_pool
        ordner = mp.GetCurrentFolder()
        ordner_id = ordner.GetUniqueId() if ordner else None
        formate = {n: RR.zielformat(dicts[n].get("width"), dicts[n].get("height")) for n in namen}
        try:
            bericht = RR.queue_rendern(session.resolve, session.project, tls, ziel, formate, args.codec)
        finally:
            session.restore_user_timeline()
            if user_tl is not None and user_tc:
                RA._safe(user_tl.SetCurrentTimecode, None, user_tc)
            aktueller = RA._safe(lambda: mp.GetCurrentFolder().GetUniqueId(), ordner_id)
            if ordner_id and aktueller != ordner_id:
                for f in RA._safe(session.all_folders, []) or []:
                    if RA._safe(f.GetUniqueId, None) == ordner_id:
                        RA._safe(mp.SetCurrentFolder, None, f)
                        break
        if bericht.get("gestoppt"):
            raise Voraussetzung(f"Render abgebrochen: {bericht['gestoppt']} (Jobs: {bericht.get('jobs')}).")
        fehler = [n for n, s in bericht["jobs"].items() if s.get("JobStatus") != "Complete"]
        if fehler:
            raise Voraussetzung(f"Render nicht vollständig: {[(n, bericht['jobs'][n]) for n in fehler]}")
        zeilen = [f"Render über die Render-Queue (mp4/{args.codec}, {bericht.get('sekunden')} s, Deliver-Preset zurückgesetzt: "
                  f"{bericht.get('preset_geladen')})"]
        for n in namen:
            datei = ziel / f"{RR.render_dateiname(n)}.mp4"
            if not datei.is_file():
                raise Voraussetzung(f"Render fehlt: {datei}")
            snap = K.snapshot_from_readback(dicts[n], session.project_name)
            frames = RR.frames_zaehlen(datei)
            warnung = ""
            if frames is not None and abs(frames - snap["laenge"]) > 1:
                warnung = f" ⚠️ {frames} Frames im Render, {snap['laenge']} in der Timeline"
            e = ablegen(ch, titel[n], datei, RR.notiz_bauen(stufen[n], n, session.project_name, args.notiz), args.nr, umsetzung)
            link = RV.link(ch.kunde, ch.projekt, e["titel"])
            zeilen.append(f"„{n}“ → Review „{e['titel']}“ V{e['nr']} ({e['weg']}, {e['version']['breite']}×{e['version']['hoehe']}, "
                          f"{e['version']['dauer_s']:.2f} s){warnung} · {link}")
        append_protokoll(ch, "Review-Ablage", zeilen)
        print("\n".join(zeilen))
        return 0
    except Voraussetzung as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
