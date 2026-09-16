"""AutoCut Kantenprüfung: Schnitte einer Timeline am fertigen Export messen — Schwarzbild, Schnipsel, Knackser,
Tonloch, Wort angeschnitten (Spec docs/superpowers/specs/2026-09-16-autocut-kantenpruefung-design.md).

Aufruf:
    venv/bin/python scripts/autocut_kanten.py "<Charge>" [--timeline "<Name>"] [--render "<Datei>"]
                                              [--readback "<json>"] [--ohne-bilder]

Ohne --readback wird die Timeline im offenen Resolve-Projekt NUR GELESEN. Der Export entsteht vorher per Review-Render
(tools/resolve/WORKFLOW-Resolve.md) oder durch den User; Standard ist die neueste Datei in Ergebnisse/Export, deren
Name mit dem Timeline-Namen beginnt. Schreibt _intern/autocut/kanten_readback.json, kanten.json,
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
from niro_autocut.charge import AutoCutError, Charge, append_protokoll  # noqa: E402
from niro_autocut.schnittbild import zeichne  # noqa: E402

FENSTER_S = 1.5
VIDEO_ENDUNGEN = {".mov", ".mp4", ".mxf", ".m4v"}


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s))


def timeline_name(ch: Charge) -> str:
    """Schlüssel ``timeline`` der zuletzt geschriebenen Datei aus feinschnitt.json, finalize.json (ok), build.json."""
    kandidaten = []
    for datei in ("feinschnitt.json", "finalize.json", "build.json"):
        d = ch.read_json(datei)
        if not isinstance(d, dict) or not d.get("timeline"):
            continue
        if datei == "finalize.json" and d.get("status") != "ok":
            continue
        kandidaten.append(((ch.autocut / datei).stat().st_mtime, str(d["timeline"])))
    if not kandidaten:
        raise AutoCutError(f"Keine gebaute AutoCut-Timeline in {ch.autocut} (feinschnitt.json, finalize.json, "
                           f"build.json) — --timeline angeben.")
    return max(kandidaten)[1]


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


def bilder(ch: Charge, snap: dict, render: Path, erg: dict) -> None:
    """Je Befund ein Schnittbild (±1,5 s) nach _intern/autocut/work/schnittbild/."""
    fps = float(snap["fps"])
    ende = snap["laenge"] / fps
    b_s = [f / fps for f in K.schnitte(snap, "bild")]
    t_s = [f / fps for f in K.schnitte(snap, "ton")]
    transkripte = K.Transkripte(ch)
    for x in erg["befunde"]:
        mitte = (x["frame"] + x["frames"] / 2) / fps
        von, bis = max(0.0, mitte - FENSTER_S), min(ende, mitte + FENSTER_S)
        ziel = ch.work / "schnittbild" / (f"kante_{x['nr']:03d}_{K.DATEINAME_ART[x['art']]}_"
                                          f"{x['timecode'].replace(':', '-')}.png")
        ch.assert_writable(ziel)
        try:
            zeichne(render, von, bis, ziel, woerter=K.export_woerter(snap, transkripte, von, bis),
                    bild_schnitte=b_s, ton_schnitte=t_s, marken=[(x["frame"] / fps, f"{x['nr']} {x['art']}")],
                    beschriftung=f"Befund {x['nr']}: {x['art']} · {x['timecode']}",
                    tc_start=snap["start_timecode"], fps=fps)
            x["bild"] = str(ziel)
        except AutoCutError as e:
            x["bild"] = None
            erg["warnungen"].append(f"Bild zu Befund {x['nr']}: {e}")


def pruefen(ch: Charge, snap: dict, render: Path, ohne_bilder: bool) -> dict:
    """Export gegen Schnappschuss prüfen, messen, Befunde bilden (mit Bildern, außer ``ohne_bilder``)."""
    info = KM.export_info(render)
    if abs(info["fps"] - float(snap["fps"])) > 0.01 or info["frames"] != int(snap["laenge"]):
        raise AutoCutError(f"Export ist nicht aktuell: {render.name} hat {info['frames']} Frames @ {info['fps']} fps, "
                           f"die Timeline '{snap['timeline']}' {snap['laenge']} Frames @ {snap['fps']} fps — "
                           f"neu exportieren.")
    cfg = dict(ch.config.get("kanten") or {})
    bild = KM.bild_metriken(render, ch.work / "kanten", n_erwartet=int(snap["laenge"]))
    if bild["mittel"].size != int(snap["laenge"]):
        raise AutoCutError(f"ffmpeg las {bild['mittel'].size} Frames statt {snap['laenge']} aus {render.name}.")
    audio = KM.ton_lesen(render) if info["ton"] else None
    erg = K.pruefe(snap, bild, audio, KM.SR, K.Transkripte(ch), cfg)
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
        render = Path(args.render).expanduser() if args.render else export_datei(ch, name)
        if not render.is_file():
            raise AutoCutError(f"Export nicht gefunden: {render}")
        print(f"Timeline '{name}' (Schnappschuss {snap['quelle']}, {snap['laenge']} Frames) · Export {render.name} "
              f"— messe …", file=sys.stderr)
        erg = pruefen(ch, snap, render, args.ohne_bilder)
        ch.write_json("kanten.json", erg)
        bericht = ch.ergebnisse / f"{video_kurz(ch)}-kanten.md"
        ch.assert_writable(bericht)
        bericht.write_text(KB.bericht(erg), encoding="utf-8")
        n, z, um = len(erg["befunde"]), erg["zaehlung"], erg["umfang"]
        zeilen = [f"Kantenprüfung „{name}“ am Export {render.name}: {n} Befunde ("
                  + ", ".join(f"{a} {z[a]}" for a in K.ARTEN) + f"), {len(erg['hinweise'])} Grafik-Übergänge als Hinweis",
                  f"Umfang: {um['bild_schnitte']} Bild-Schnitte, {um['ton_schnitte']} Ton-Schnitte, "
                  f"{um['mit_transkript']} Tonclips mit Transkript; Schnappschuss {snap['quelle']} "
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
