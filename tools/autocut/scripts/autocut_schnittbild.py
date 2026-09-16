"""AutoCut Schnittbild: Filmstreifen, Pegel, Wörter und Schnitte eines Zeitbereichs als PNG — für unklare In/Outs am
Rohclip (Stufe 1) oder für eine Stelle im Export (Kantenprüfung). Spec 2026-09-16.

Aufruf:
    venv/bin/python scripts/autocut_schnittbild.py "<Charge>" --clip <Dateiname|Pfad> --von <s|mm:ss.s> --bis <s|mm:ss.s>
    venv/bin/python scripts/autocut_schnittbild.py "<Charge>" --render "<Datei>" (--tc HH:MM:SS:FF | --frame <N>)
                                                   [--fenster 1.5] [--readback "<json>"]
    gemeinsam: [--frames 10] [--ausgabe "<png>"]

Rohclip: Eintrag im Transkript-Index der Charge (Pfad über path_map), Bild und Ton aus dem Proxy (sonst Original),
Wörter aus dem Scribe-Cache. Export: Schnitte und Wörter aus _intern/autocut/kanten_readback.json (oder --readback);
--frame zählt ab Timeline-Start. Schreibt nur das PNG (Standard _intern/autocut/work/schnittbild/) und druckt den Pfad.
Exit 0 ok, 2 Fehler.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import kanten as K  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.media import proxy_for  # noqa: E402
from niro_autocut.schnittbild import zeichne  # noqa: E402


def _nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s))


def sekunden(text: str) -> float:
    """„12.5" → 12.5 · „01:02,5" → 62.5 · „1:02:03.5" → 3723.5."""
    teile = str(text).strip().split(":")
    try:
        werte = [float(t.replace(",", ".")) for t in teile]
    except ValueError as e:
        raise AutoCutError(f"Zeitangabe nicht lesbar: {text!r} (Sekunden oder mm:ss.s)") from e
    if not 1 <= len(werte) <= 3:
        raise AutoCutError(f"Zeitangabe nicht lesbar: {text!r} (Sekunden oder mm:ss.s)")
    s = 0.0
    for w in werte:
        s = s * 60 + w
    return s


def clip_bild(ch: Charge, args) -> Path:
    """Schnittbild eines Rohclips aus dem Transkript-Index (Proxy bevorzugt) mit Scribe-Wörtern."""
    gesucht = _nfc(args.clip)
    eintraege = [e for e in ch.load_index() if e.get("path")
                 and gesucht in (_nfc(e.get("name", "")), _nfc(e["path"]), _nfc(Path(e["path"]).name))]
    if not eintraege:
        raise AutoCutError(f"Clip '{args.clip}' steht nicht im Transkript-Index der Charge.")
    if len(eintraege) > 1:
        raise AutoCutError(f"Clip '{args.clip}' ist mehrdeutig ({len(eintraege)} Einträge) — vollen Pfad angeben.")
    e = eintraege[0]
    original = Path(ch.map_path(e["path"]))
    quelle = proxy_for(original) or original
    if not quelle.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {quelle}\nIst das NAS gemountet? Sonst path_map in config.yaml setzen.")
    von, bis = sekunden(args.von), sekunden(args.bis)
    woerter = []
    if e.get("fingerprint"):
        woerter = (ch.cache_transcript(e["fingerprint"]) or {}).get("words") or []
    ziel = (Path(args.ausgabe).expanduser() if args.ausgabe
            else ch.work / "schnittbild" / f"{Path(e['path']).stem}_{von:.2f}-{bis:.2f}.png")
    ch.assert_writable(ziel)
    beschriftung = " · ".join(str(v) for v in (e.get("person"), e.get("kamera"),
                                               "Proxy" if quelle != original else "Original") if v)
    return zeichne(quelle, von, bis, ziel, woerter=woerter, frames=args.frames, beschriftung=beschriftung)


def export_bild(ch: Charge, args) -> Path:
    """Schnittbild einer Stelle im Export mit Schnitten und Wörtern aus dem Schnappschuss."""
    render = Path(args.render).expanduser()
    if not render.is_file():
        raise AutoCutError(f"Export nicht gefunden: {render}")
    snap_pfad = Path(args.readback).expanduser() if args.readback else ch.autocut / "kanten_readback.json"
    if not snap_pfad.is_file():
        raise AutoCutError(f"Schnappschuss fehlt: {snap_pfad} — erst scripts/autocut_kanten.py laufen lassen oder "
                           f"--readback angeben.")
    snap = json.loads(snap_pfad.read_text(encoding="utf-8"))
    fps = float(snap["fps"])
    if args.tc:
        frame = K.tc_to_frame(args.tc, fps, snap["start_timecode"])
    elif args.frame is not None:
        frame = int(args.frame)
    else:
        raise AutoCutError("Im Export-Modus --tc oder --frame angeben.")
    if not 0 <= frame < int(snap["laenge"]):
        raise AutoCutError(f"Frame {frame} liegt außerhalb der Timeline (0–{int(snap['laenge']) - 1}).")
    tc = K.timecode(frame, fps, snap["start_timecode"])
    mitte = frame / fps
    von, bis = max(0.0, mitte - args.fenster), min(snap["laenge"] / fps, mitte + args.fenster)
    ziel = (Path(args.ausgabe).expanduser() if args.ausgabe
            else ch.work / "schnittbild" / f"export_{tc.replace(':', '-')}.png")
    ch.assert_writable(ziel)
    return zeichne(render, von, bis, ziel, woerter=K.export_woerter(snap, K.Transkripte(ch), von, bis),
                   bild_schnitte=[f / fps for f in K.schnitte(snap, "bild")],
                   ton_schnitte=[f / fps for f in K.schnitte(snap, "ton")],
                   marken=[(mitte, tc)], frames=args.frames, beschriftung=str(snap.get("timeline")),
                   tc_start=snap["start_timecode"], fps=fps)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Schnittbild (Filmstreifen, Pegel, Wörter, Schnitte) als PNG.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    modus = ap.add_mutually_exclusive_group(required=True)
    modus.add_argument("--clip", help="Rohclip: Dateiname oder Pfad aus dem Transkript-Index")
    modus.add_argument("--render", help="Export-Datei der Timeline")
    ap.add_argument("--von", help="Clip-Modus: Anfang (Sekunden oder mm:ss.s)")
    ap.add_argument("--bis", help="Clip-Modus: Ende (Sekunden oder mm:ss.s)")
    ap.add_argument("--tc", help="Export-Modus: Timecode HH:MM:SS:FF")
    ap.add_argument("--frame", type=int, help="Export-Modus: Frame ab Timeline-Start")
    ap.add_argument("--fenster", type=float, default=1.5, help="Export-Modus: Sekunden vor und nach der Stelle")
    ap.add_argument("--readback", help="Export-Modus: Schnappschuss (Standard _intern/autocut/kanten_readback.json)")
    ap.add_argument("--frames", type=int, default=10, help="Bilder im Filmstreifen")
    ap.add_argument("--ausgabe", help="PNG-Pfad (in den AutoCut-Schreibbereichen der Charge)")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        if args.clip:
            if not args.von or not args.bis:
                raise AutoCutError("Im Clip-Modus --von und --bis angeben.")
            ziel = clip_bild(ch, args)
        else:
            ziel = export_bild(ch, args)
        print(ziel)
        return 0
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
