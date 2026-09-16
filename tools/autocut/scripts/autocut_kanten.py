"""AutoCut Kantenprüfung: Schnitte einer Timeline am fertigen Export messen — Schwarzbild, Schnipsel, Knackser,
Tonloch, Wort angeschnitten (Spec docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md).

Aufruf:
    venv/bin/python scripts/autocut_kanten.py "<Charge>" [--timeline "<Name>"] [--render "<Datei>"]
                                              [--readback "<json>"] [--ohne-bilder] [--ohne-export]

Ohne --readback wird die Timeline im offenen Resolve-Projekt NUR GELESEN. Der Export entsteht vorher per Review-Render
(tools/resolve/WORKFLOW-Resolve.md) oder durch den User; Standard ist die neueste Datei in Ergebnisse/Export, deren
Name mit dem Timeline-Namen beginnt. --ohne-export prüft nur die Wortkanten (Quellton der Rohclips, kein Export nötig)
— z. B. direkt nach Handänderungen. Schreibt _intern/autocut/kanten_readback.json, kanten.json,
work/kanten/<fingerprint>.npz, work/schnittbild/kante_*.png, Ergebnisse/Rohschnitt/<video>-kanten.md und das Protokoll.
Exit 0 = keine Befunde, 1 = Befunde, 2 = Voraussetzung fehlt oder Fehler.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut import kanten_bericht as KB  # noqa: E402
from niro_autocut import kanten_medien as KM  # noqa: E402
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge, append_protokoll, letzte_timeline  # noqa: E402
from niro_autocut.media import proxy_for  # noqa: E402
from niro_autocut.schnittbild import pegel_db, zeichne  # noqa: E402

FENSTER_S = 1.5
VIDEO_ENDUNGEN = {".mov", ".mp4", ".mxf", ".m4v"}


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s))


timeline_name = letzte_timeline      # gemeinsame Regel (charge.py); Name bleibt für Aufrufer und Tests


def export_datei(ch: Charge, name: str) -> Path:
    """Neueste Videodatei in Ergebnisse/Export, deren Name mit dem Timeline-Namen beginnt."""
    ordner = ch.root / "Ergebnisse" / "Export"
    treffer = [p for p in ordner.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_ENDUNGEN
               and _nfc(p.name).startswith(_nfc(name))] if ordner.is_dir() else []
    if not treffer:
        raise AutoCutError(f"Kein Export für '{name}' in {ordner} — Review-Render (tools/resolve/WORKFLOW-Resolve.md) "
                           f"oder --render angeben.")
    return max(treffer, key=lambda p: p.stat().st_mtime)


def schnappschuss_lesen(ch: Charge, name: str) -> dict:
    """Timeline im offenen Resolve-Projekt nur lesen → Schnappschuss."""
    try:
        session = RA.ResolveSession(RA.connect(), path_map=ch.config.get("path_map"))
    except AutoCutError as e:
        raise AutoCutError(f"{e}\nOhne Resolve: --readback <kanten_readback.json> angeben.") from e
    tl = session.find_timeline(name)
    if tl is None:
        raise AutoCutError(f"Timeline '{name}' ist nicht im offenen Projekt '{session.project_name}' — das Projekt in "
                           f"Resolve öffnen (wird nur gelesen) oder --readback angeben.")
    return K.snapshot_from_readback(session.read_timeline(tl), session.project_name)


def video_kurz(ch: Charge) -> str:
    """Kurzname für den Bericht: ``video`` aus build.json, sonst der einzige Plan, sonst „video"."""
    build = ch.read_json("build.json") or {}
    if build.get("video"):
        return Path(str(build["video"])).stem
    plaene = ch.plan_files()
    return plaene[0].stem if len(plaene) == 1 else "video"


def quelle(ch: Charge, transkripte: K.Transkripte, datei) -> Path | None:
    """Rohclip eines Timeline-Items über den Transkript-Index (path_map), Proxy bevorzugt; None, wenn nicht erreichbar."""
    e = transkripte.eintrag(datei)
    if e is None:
        return None
    original = Path(ch.map_path(e["path"]))
    q = proxy_for(original) or original
    return q if q.is_file() else None


def pegel_funktion(ch: Charge, transkripte: K.Transkripte):
    """``pegel(datei, von_s, bis_s)`` für ``kanten.wort_befunde``: 10-ms-RMS des Rohclips oder None."""
    def pegel(datei, von_s, bis_s):
        q = quelle(ch, transkripte, datei)
        return None if q is None else pegel_db(q, von_s, bis_s)
    return pegel


def bilder(ch: Charge, snap: dict, render: Path | None, erg: dict) -> None:
    """Je Befund ein Schnittbild (±1,5 s) nach _intern/autocut/work/schnittbild/ — Wortkanten am Rohclip (zeigt auch
    den weggeschnittenen Teil), alle anderen Befunde am Export."""
    fps = float(snap["fps"])
    ende = snap["laenge"] / fps
    b_s = [f / fps for f in K.schnitte(snap, "bild")]
    t_s = [f / fps for f in K.schnitte(snap, "ton")]
    transkripte = K.Transkripte(ch)
    for x in erg["befunde"]:
        ziel = ch.work / "schnittbild" / (f"kante_{x['nr']:03d}_{K.DATEINAME_ART[x['art']]}_"
                                          f"{x['timecode'].replace(':', '-')}.png")
        ch.assert_writable(ziel)
        x["bild"] = None
        try:
            if x["art"] == "Wort angeschnitten":
                q = quelle(ch, transkripte, x["datei"])
                if q is None:
                    raise AutoCutError(f"Rohclip von {x['clip']} nicht erreichbar")
                t = x["quell_s"]
                zeichne(q, max(0.0, t - FENSTER_S), t + FENSTER_S, ziel, woerter=transkripte.woerter(x["datei"]) or [],
                        ton_schnitte=[t], marken=[(t, f"{x['nr']} {x['seite']}-Kante")],
                        beschriftung=f"Befund {x['nr']}: „{x['wort']}“ · Rohclip {x['clip']} · Timeline {x['timecode']} · "
                                     f"behalten {'rechts' if x['seite'] == 'in' else 'links'} der Kante")
            elif render is not None:
                mitte = (x["frame"] + x["frames"] / 2) / fps
                von, bis = max(0.0, mitte - FENSTER_S), min(ende, mitte + FENSTER_S)
                zeichne(render, von, bis, ziel, woerter=K.export_woerter(snap, transkripte, von, bis),
                        bild_schnitte=b_s, ton_schnitte=t_s, marken=[(x["frame"] / fps, f"{x['nr']} {x['art']}")],
                        beschriftung=f"Befund {x['nr']}: {x['art']} · {x['timecode']}",
                        tc_start=snap["start_timecode"], fps=fps)
            else:
                continue
            x["bild"] = str(ziel)
        except AutoCutError as e:
            erg["warnungen"].append(f"Bild zu Befund {x['nr']}: {e}")


def pruefen(ch: Charge, snap: dict, render: Path | None, ohne_bilder: bool) -> dict:
    """Export gegen Schnappschuss prüfen, messen, Befunde bilden (mit Bildern, außer ``ohne_bilder``).
    Ohne ``render`` nur die Wortkanten."""
    cfg = dict(ch.config.get("kanten") or {})
    transkripte = K.Transkripte(ch)
    pegel = pegel_funktion(ch, transkripte)
    if render is None:
        erg = K.pruefe(snap, None, None, KM.SR, transkripte, cfg, pegel)
        erg.update({"export": None, "parameter": cfg,
                    "schnappschuss": {"quelle": snap["quelle"], "gelesen_am": snap["gelesen_am"],
                                      "projekt": snap["projekt"]}})
        if not ohne_bilder:
            bilder(ch, snap, None, erg)
        return erg
    info = KM.export_info(render)
    if abs(info["fps"] - float(snap["fps"])) > 0.01 or info["frames"] != int(snap["laenge"]):
        raise AutoCutError(f"Export ist nicht aktuell: {render.name} hat {info['frames']} Frames @ {info['fps']} fps, "
                           f"die Timeline '{snap['timeline']}' {snap['laenge']} Frames @ {snap['fps']} fps — "
                           f"neu exportieren.")
    bild = KM.bild_metriken(render, ch.work / "kanten", n_erwartet=int(snap["laenge"]))
    if bild["mittel"].size != int(snap["laenge"]):
        raise AutoCutError(f"ffmpeg las {bild['mittel'].size} Frames statt {snap['laenge']} aus {render.name}.")
    audio = KM.ton_lesen(render) if info["ton"] else None
    erg = K.pruefe(snap, bild, audio, KM.SR, transkripte, cfg, pegel)
    if audio is None:
        erg["warnungen"].append("Export ohne Ton — Knackser und Tonlöcher nicht geprüft.")
    erg.update({"export": info, "parameter": cfg,
                "schnappschuss": {"quelle": snap["quelle"], "gelesen_am": snap["gelesen_am"],
                                  "projekt": snap["projekt"]}})
    if not ohne_bilder:
        bilder(ch, snap, render, erg)
    return erg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Kantenprüfung am fertigen Export (Resolve nur lesend).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--timeline", help="exakter Timeline-Name (Standard: zuletzt gebaute AutoCut-Timeline)")
    ap.add_argument("--render", help="Export-Datei (Standard: neueste in Ergebnisse/Export mit dem Timeline-Namen)")
    ap.add_argument("--readback", help="gespeicherter Schnappschuss statt Resolve (kanten_readback.json)")
    ap.add_argument("--ohne-bilder", action="store_true", help="keine Schnittbilder zu den Befunden")
    ap.add_argument("--ohne-export", action="store_true", help="nur Wortkanten am Quellton prüfen (kein Export nötig)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        if args.readback:
            p = Path(args.readback).expanduser()
            if not p.is_file():
                raise AutoCutError(f"--readback nicht gefunden: {p}")
            snap = json.loads(p.read_text(encoding="utf-8"))
            name = args.timeline or str(snap.get("timeline"))
            if snap.get("timeline") != name:
                raise AutoCutError(f"Schnappschuss {p.name} gehört zu '{snap.get('timeline')}', geprüft werden soll "
                                   f"'{name}'.")
        else:
            name = args.timeline or timeline_name(ch)
            snap = schnappschuss_lesen(ch, name)
        ch.write_json("kanten_readback.json", snap)
        if args.ohne_export:
            render = None
        else:
            render = Path(args.render).expanduser() if args.render else export_datei(ch, name)
            if not render.is_file():
                raise AutoCutError(f"Export nicht gefunden: {render}")
        print(f"Timeline '{name}' (Schnappschuss {snap['quelle']}, {snap['laenge']} Frames) · "
              f"{'nur Wortkanten' if render is None else 'Export ' + render.name} — messe …", file=sys.stderr)
        erg = pruefen(ch, snap, render, args.ohne_bilder)
        ch.write_json("kanten.json", erg)
        bericht = ch.ergebnisse / f"{video_kurz(ch)}-kanten.md"
        ch.assert_writable(bericht)
        bericht.write_text(KB.bericht(erg), encoding="utf-8")
        n, z, um = len(erg["befunde"]), erg["zaehlung"], erg["umfang"]
        wo = "ohne Export (nur Wortkanten)" if render is None else f"am Export {render.name}"
        zeilen = [f"Kantenprüfung „{name}“ {wo}: {n} Befunde ("
                  + ", ".join(f"{a} {z[a]}" for a in K.ARTEN) + f"), {len(erg['hinweise'])} Grafik-Übergänge als Hinweis",
                  f"Umfang: {um['bild_schnitte']} Bild-Schnitte, {um['ton_schnitte']} Ton-Schnitte, "
                  f"{um['mit_transkript']} Tonclips mit Transkript, {um['ohne_quelle']} ohne erreichbaren Rohclip; "
                  f"Schnappschuss {snap['quelle']} "
                  f"({snap['gelesen_am']})",
                  f"Bericht: {bericht}"]
        zeilen += [f"Warnung: {w}" for w in erg["warnungen"][:5]]
        append_protokoll(ch, "Kantenprüfung", zeilen)
        print("\n".join(zeilen))
        return 1 if n else 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
