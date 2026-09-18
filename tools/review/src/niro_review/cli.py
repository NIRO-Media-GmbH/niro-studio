"""CLI von NIRO Review (Aufruf über tools/review/review.py). Befehle und Exit-Codes: Spec „Befehle"."""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from . import WERKZEUG_VERSION, ablage, kommentare as km, launchagent, medien, modell
from .ablage import ReviewFehler, jetzt, nfc

PORT = 4711


def link(kunde: str, projekt: str, titel: Optional[str] = None, port: int = PORT) -> str:
    teile = [kunde, projekt] + ([titel] if titel else [])
    return f"http://localhost:{port}/#/" + "/".join(quote(nfc(t), safe="") for t in teile)


def _nas_pruefen() -> None:
    if not ablage.nas_verbunden():
        raise ReviewFehler(f"NAS nicht verbunden: {ablage.review_wurzel().parent} fehlt.", 2)


def _quelle_rel(datei: Path) -> str:
    try:
        return str(datei.resolve().relative_to(ablage.repo_wurzel().resolve()))
    except ValueError:
        return str(datei.resolve())


def _umsetzung_lesen(pfad: Optional[str]) -> Optional[dict]:
    if not pfad:
        return None
    daten = ablage.json_lesen(Path(pfad))
    if daten is None:
        raise ReviewFehler(f"Umsetzung fehlt: {pfad}")
    return daten


def version_anlegen(kunde: str, projekt: str, charge: Optional[str], titel: str, datei: Path, nr: Optional[int] = None,
                    notiz: str = "", sortierung: Optional[str] = None, basis: Optional[int] = None,
                    trotzdem: bool = False, umsetzung: Optional[dict] = None) -> dict:
    """Version anlegen: prüfen, Review-Kopie in den Cache, Vorschaubild, aufs NAS, version.json zuletzt."""
    datei = Path(datei)
    if not datei.is_file():
        raise ReviewFehler(f"Datei fehlt: {datei}")
    wurzel = ablage.review_wurzel()
    ordner = modell.video_ordner(kunde, projekt, titel, wurzel)
    video = modell.video_lesen(ordner)
    nr = int(nr) if nr else modell.naechste_version(ordner)
    if nr < 1:
        raise ReviewFehler("Versionsnummer muss ≥ 1 sein.")
    vo = modell.version_ordner(ordner, nr)
    if modell.version_lesen(ordner, nr) or vo.exists():
        raise ReviewFehler(f"V{nr} von „{titel}“ existiert — nächste freie: V{modell.naechste_version(ordner)}.")
    basis_nr = basis if basis else (nr - 1 if nr > 1 else None)
    basis_daten = None
    if umsetzung is not None:
        if basis_nr is None or not modell.version_lesen(ordner, basis_nr):
            raise ReviewFehler(f"--umsetzung braucht eine Basisversion (V{basis_nr or '?'} fehlt).")
        basis_daten = km.laden(modell.version_ordner(ordner, basis_nr))
        basis_fps = float((modell.version_lesen(ordner, basis_nr) or {}).get("fps") or 25.0)
        km.umsetzung_anwenden(copy.deepcopy(basis_daten), umsetzung, basis_fps)  # nur prüfen — alles oder nichts
    info = medien.info_aus_probe(medien.ffprobe(datei), datei.stat().st_size)
    weg = medien.entscheidung(info)
    if weg == "alpha" and not trotzdem:
        raise ReviewFehler("Alpha-Overlay ohne Bild darunter — erst als Komposit rendern (oder --trotzdem).")
    cache_v = ablage.cache_wurzel() / nfc(kunde) / nfc(projekt) / nfc(titel) / f"V{nr}"
    cache_v.mkdir(parents=True, exist_ok=True)
    cache_video, cache_thumb = cache_v / "video.mp4", cache_v / "thumb.jpg"
    encoder = None
    if weg == "kopie":
        shutil.copy2(datei, cache_video)
    else:
        encoder = medien.umkodieren(datei, cache_video, info)
        info = medien.info_aus_probe(medien.ffprobe(cache_video), cache_video.stat().st_size)
    medien.vorschaubild(cache_video, cache_thumb, info.dauer_s)
    if video is None:
        video = modell.video_anlegen(ordner, kunde, projekt, titel, charge, sortierung)
    vo.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(cache_video, vo / "video.mp4")
        shutil.copy2(cache_thumb, vo / "thumb.jpg")
        if (vo / "video.mp4").stat().st_size != cache_video.stat().st_size:
            raise ReviewFehler("Kopie aufs NAS unvollständig (Größe weicht ab).", 2)
        km.speichern(vo, modell.KOMMENTARE_LEER())
        version = {"nr": nr, "angelegt": jetzt(), "von": ablage.mac_name(), "quelle": _quelle_rel(datei),
                   "dauer_s": round(info.dauer_s, 3), "fps": info.fps, "frames": info.frames, "breite": info.breite,
                   "hoehe": info.hoehe, "groesse": cache_video.stat().st_size, "umkodiert": weg != "kopie",
                   "encoder": encoder, "notiz": notiz or "", "basis": basis_nr, "abgeschlossen": None, "geholt_am": None}
        modell.version_schreiben(ordner, nr, version)
    except BaseException:
        shutil.rmtree(vo, ignore_errors=True)
        raise
    if umsetzung is not None and basis_daten is not None:
        km.umsetzung_anwenden(basis_daten, umsetzung, basis_fps)
        km.speichern(modell.version_ordner(ordner, basis_nr), basis_daten)
    return {"titel": nfc(titel), "nr": nr, "weg": "Kopie" if weg == "kopie" else f"umkodiert ({encoder})",
            "ordner": ordner, "version": version}


def cmd_hinzufuegen(args) -> int:
    _nas_pruefen()
    medien.werkzeuge_pruefen()
    ziel = ablage.ziel_aufloesen(args.charge)
    if ziel.charge is None:
        raise ReviewFehler("hinzufuegen braucht die Charge: projects/<Kunde>/<Projekt>/<Charge>.")
    kunde, projekt = args.kunde or ziel.kunde, args.projekt or ziel.projekt
    if bool(args.datei) == bool(args.ordner):
        raise ReviewFehler("Genau eines von --datei oder --ordner angeben.")
    if args.umsetzung and args.ordner:
        raise ReviewFehler("--umsetzung geht nur mit --datei.")
    umsetzung = _umsetzung_lesen(args.umsetzung)
    if args.datei:
        dateien = [Path(args.datei)]
    else:
        quelle = Path(args.ordner)
        if not quelle.is_dir():
            raise ReviewFehler(f"Ordner fehlt: {quelle}")
        dateien = sorted(p for p in quelle.glob(args.muster) if p.is_file() and not p.name.startswith("."))
        if not dateien:
            raise ReviewFehler(f"Keine Dateien in „{quelle}“ ({args.muster}).")
    fehler = 0
    letzter_titel = None
    for datei in dateien:
        titel = args.video if (args.video and args.datei) else modell.titel_aus_dateiname(datei.name)
        try:
            e = version_anlegen(kunde, projekt, ziel.charge, titel, datei, args.nr, args.notiz, args.sortierung,
                                args.basis, args.trotzdem, umsetzung)
        except ReviewFehler as ex:
            if args.datei:
                raise
            fehler += 1
            print(f"✗ {datei.name}: {ex}", file=sys.stderr)
            continue
        v = e["version"]
        print(f"✓ {e['titel']} V{e['nr']} ({e['weg']}, {v['dauer_s']:.2f} s, {v['breite']}×{v['hoehe']}, {v['fps']:g} fps)")
        letzter_titel = e["titel"]
    print(link(kunde, projekt, letzter_titel if len(dateien) == 1 else None, args.port))
    return 1 if fehler else 0


def _videos_finden(ziel: ablage.Ziel, titel: Optional[str]) -> list:
    wurzel = ablage.review_wurzel()
    projekt_ordner = ablage.finde_kind(ablage.finde_kind(wurzel, ziel.kunde), ziel.projekt)
    if not projekt_ordner.is_dir():
        raise ReviewFehler(f"Kein Review-Projekt {ziel.kunde}/{ziel.projekt} unter {wurzel}.")
    out = []
    for vo in sorted(projekt_ordner.iterdir()):
        video = modell.video_lesen(vo)
        if not video or (titel and nfc(video["titel"]) != nfc(titel)):
            continue
        if ziel.charge and video.get("charge") and nfc(video["charge"]) != nfc(ziel.charge) and not titel:
            continue
        out.append((vo, video))
    if not out:
        raise ReviewFehler(f"Kein passendes Video in {ziel.kunde}/{ziel.projekt}" + (f" („{titel}“)." if titel else "."))
    return sorted(out, key=lambda t: modell.sortier_schluessel(t[1]))


def _ein_video(args):
    ziel = ablage.ziel_aufloesen(args.charge)
    if not args.video:
        raise ReviewFehler("--video „<Titel>“ fehlt.")
    vo, video = _videos_finden(ziel, args.video)[0]
    return vo, video


def cmd_kommentare(args) -> int:
    _nas_pruefen()
    ziel = ablage.ziel_aufloesen(args.charge)
    neue_gesamt = exportiert = 0
    for vo, video in _videos_finden(ziel, args.video):
        nrs = modell.versionsnummern(vo)
        if not nrs:
            print(f"· {video['titel']}: keine Version")
            continue
        nr = args.nr or nrs[-1]
        version = modell.version_lesen(vo, nr)
        if not version:
            raise ReviewFehler(f"V{nr} von „{video['titel']}“ fehlt.")
        daten = km.laden(modell.version_ordner(vo, nr))
        geholt_vorher = version.get("geholt_am")
        neue = [k for k in km.sortiert(daten["kommentare"]) if km.ist_neu(k, geholt_vorher)]
        stand = "abgeschlossen" if version.get("abgeschlossen") else "noch offen"
        if not neue and not args.alle:
            print(f"· {video['titel']} V{nr}: keine neuen Kommentare ({len(daten['kommentare'])} bekannt, {stand})")
            continue
        charge_rel = video.get("charge") or ziel.charge
        if not charge_rel:
            raise ReviewFehler(f"„{video['titel']}“ hat keine Charge — Aufruf mit projects/<Kunde>/<Projekt>/<Charge>.")
        ziel_ordner = ablage.repo_wurzel() / charge_rel / "Material" / "Feedback" / f"{ablage.heute()} Review {video['titel']} V{nr}"
        md = km.export_md(video, version, daten, geholt_vorher, ablage.datum_de(ablage.heute()))
        js = km.export_json(video, version, daten, geholt_vorher)
        ablage.atomar_schreiben(ziel_ordner / "kommentare.md", md)
        ablage.json_schreiben(ziel_ordner / "kommentare.json", js)
        version["geholt_am"] = jetzt()
        modell.version_schreiben(vo, nr, version)
        neue_gesamt += len(neue)
        exportiert += 1
        print(f"✓ {video['titel']} V{nr}: {len(neue)} neu, {len(daten['kommentare'])} gesamt, {stand} → {ziel_ordner}")
        fps = float(version.get("fps") or 25.0)
        for k in neue:
            tc = medien.timecode(k["frame"], fps) if k.get("frame") is not None else "allgemein"
            bis = f"–{medien.timecode(k['bis_frame'], fps)}" if k.get("bis_frame") is not None else ""
            print(f"    {k['id']} {tc}{bis} {k.get('autor')}: {k.get('text')}")
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=1))
    return 0 if neue_gesamt or (args.alle and exportiert) else 1


def cmd_umsetzung(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    version = modell.version_lesen(vo, args.nr)
    if not version:
        raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
    umsetzung = _umsetzung_lesen(args.datei)
    daten = km.laden(modell.version_ordner(vo, args.nr))
    ids = km.umsetzung_anwenden(daten, umsetzung, float(version.get("fps") or 25.0))
    km.speichern(modell.version_ordner(vo, args.nr), daten)
    print(f"✓ {video['titel']} V{args.nr}: {', '.join(ids)} eingetragen")
    return 0


def cmd_antworten(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    if not modell.version_lesen(vo, args.nr):
        raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
    daten = km.laden(modell.version_ordner(vo, args.nr))
    km.antworten(daten, args.kommentar, args.autor, args.text)
    km.speichern(modell.version_ordner(vo, args.nr), daten)
    print(f"✓ {video['titel']} V{args.nr} {args.kommentar}: Antwort eingetragen")
    return 0


def cmd_status(args) -> int:
    _nas_pruefen()
    index = modell.index_bauen(ablage.review_wurzel())
    ziel = ablage.ziel_aufloesen(args.charge) if args.charge else None
    zeilen = []
    for kunde in index["kunden"]:
        for projekt in kunde["projekte"]:
            if ziel and (kunde["name"] != ziel.kunde or projekt["name"] != ziel.projekt):
                continue
            for v in projekt["videos"]:
                if ziel and ziel.charge and v.get("charge") and nfc(v["charge"]) != nfc(ziel.charge):
                    continue
                zeilen.append(f"{kunde['name']}/{projekt['name']} · {v['titel']} · V{v['neueste']} · {v['zustand']} · "
                              f"{v['offen']} offen ({v['neu']} neu) · {link(kunde['name'], projekt['name'], v['titel'], args.port)}")
    print("\n".join(zeilen) if zeilen else "Keine Videos.")
    return 0


def cmd_entfernen(args) -> int:
    _nas_pruefen()
    vo, video = _ein_video(args)
    korb = ablage.review_wurzel() / "_papierkorb"
    korb.mkdir(parents=True, exist_ok=True)
    stempel = jetzt().replace(":", "-")
    if args.nr:
        quelle = modell.version_ordner(vo, args.nr)
        if not quelle.is_dir():
            raise ReviewFehler(f"V{args.nr} von „{video['titel']}“ fehlt.")
        ziel = korb / f"{stempel} {video['kunde']} {video['projekt']} {video['titel']} V{args.nr}"
    else:
        quelle = vo
        ziel = korb / f"{stempel} {video['kunde']} {video['projekt']} {video['titel']}"
    shutil.move(str(quelle), str(ziel))
    print(f"✓ nach {ziel} verschoben")
    return 0


def cmd_server(args) -> int:
    from . import server
    server.starten(args.port)
    return 0


def cmd_installieren(args) -> int:
    plist = launchagent.installieren(args.port)
    print(f"✓ LaunchAgent {launchagent.ETIKETT} installiert ({plist}) — http://localhost:{args.port} · Log {launchagent.log_pfad()}")
    return 0


def cmd_deinstallieren(args) -> int:
    war_da = launchagent.deinstallieren()
    print("✓ LaunchAgent entfernt" if war_da else "· kein LaunchAgent vorhanden")
    return 0


def cmd_oeffnen(args) -> int:
    url = f"http://localhost:{args.port}/"
    if args.ziel:
        teile = [t for t in nfc(args.ziel).split("/") if t]
        if teile and teile[0] == "projects":
            teile = teile[1:]
        if len(teile) >= 2:
            url = link(teile[0], teile[1], teile[2] if len(teile) > 2 else None, args.port)
    subprocess.run(["open", url], check=False)
    print(url)
    return 0


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="review.py", description=f"NIRO Review {WERKZEUG_VERSION} — lokales Review-Werkzeug")
    sub = p.add_subparsers(dest="befehl", required=True)

    def port(sp):
        sp.add_argument("--port", type=int, default=PORT)

    a = sub.add_parser("hinzufuegen", help="Version eines Videos ablegen")
    a.add_argument("charge")
    a.add_argument("--datei")
    a.add_argument("--ordner")
    a.add_argument("--muster", default="*.mp4")
    a.add_argument("--video", help="Titel (sonst aus dem Dateinamen)")
    a.add_argument("--version", dest="nr", type=int)
    a.add_argument("--notiz", default="")
    a.add_argument("--umsetzung", help="umsetzung.json für die Basisversion")
    a.add_argument("--basis", type=int)
    a.add_argument("--sortierung")
    a.add_argument("--kunde")
    a.add_argument("--projekt")
    a.add_argument("--trotzdem", action="store_true", help="auch Alpha-Dateien annehmen")
    port(a)
    k = sub.add_parser("kommentare", help="Kommentare holen und in die Charge exportieren")
    k.add_argument("charge")
    k.add_argument("--video")
    k.add_argument("--version", dest="nr", type=int)
    k.add_argument("--alle", action="store_true")
    k.add_argument("--json", action="store_true")
    u = sub.add_parser("umsetzung", help="Status/Antwort je Kommentar eintragen")
    u.add_argument("charge")
    u.add_argument("--video", required=True)
    u.add_argument("--version", dest="nr", type=int, required=True)
    u.add_argument("--datei", required=True)
    an = sub.add_parser("antworten", help="Antwort in einen Kommentar-Thread")
    an.add_argument("charge")
    an.add_argument("--video", required=True)
    an.add_argument("--version", dest="nr", type=int, required=True)
    an.add_argument("--kommentar", required=True)
    an.add_argument("--text", required=True)
    an.add_argument("--autor", default="Claude")
    s = sub.add_parser("status", help="Übersicht")
    s.add_argument("charge", nargs="?")
    port(s)
    e = sub.add_parser("entfernen", help="Video oder Version in den Papierkorb")
    e.add_argument("charge")
    e.add_argument("--video", required=True)
    e.add_argument("--version", dest="nr", type=int)
    sv = sub.add_parser("server", help="Server im Vordergrund")
    port(sv)
    i = sub.add_parser("installieren", help="LaunchAgent anlegen und laden")
    port(i)
    sub.add_parser("deinstallieren", help="LaunchAgent entladen und entfernen")
    o = sub.add_parser("oeffnen", help="Browser öffnen")
    o.add_argument("ziel", nargs="?")
    port(o)
    return p


BEFEHLE = {"hinzufuegen": cmd_hinzufuegen, "kommentare": cmd_kommentare, "umsetzung": cmd_umsetzung,
           "antworten": cmd_antworten, "status": cmd_status, "entfernen": cmd_entfernen, "server": cmd_server,
           "installieren": cmd_installieren, "deinstallieren": cmd_deinstallieren, "oeffnen": cmd_oeffnen}


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        return BEFEHLE[args.befehl](args)
    except ReviewFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return e.code
