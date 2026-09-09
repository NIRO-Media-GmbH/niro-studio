"""Charge vorbereiten: Interview-Clips prüfen (Original + Proxy per ffprobe), Timeline-Format bestimmen,
Kamerapaare je Interview-Ordner gruppieren → <Charge>/_intern/autocut/media.json (Spec 3.1).

Aufruf:
    venv/bin/python scripts/autocut_prepare.py "<Charge>" [--video video-1-x.md] [--check-resolve]

Liest Index, Plan und Mediendateien (NAS nur lesend); schreibt ausschließlich media.json.
Exit 1 bei Abbruch: Datei fehlt (NAS nicht gemountet?), Proxy passt nicht zum Original, Mischformat.

media.json:
    {"format": {"fps", "width", "height", "orientation"},
     "clips": {"<pfad>": {"original": MediaInfo, "proxy": MediaInfo|None, "proxy_path": str|None,
                          "kamera": "FX3"|"a7MK4", "rolle": "ton"|"kontext", "ordner": "<Interview-Ordner>",
                          "person": …, "fingerprint": …}},
     "ordner": {"<ordner>": {"ton": [pfade], "kontext": [pfade]}}}
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut import media as M  # noqa: E402
from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.plan import parse_plan  # noqa: E402

KAMERA_RE = [(re.compile(r"^fx3", re.I), "FX3"),
             (re.compile(r"^(a7mk4|a7m4|a7iv|a7)", re.I), "a7MK4")]
ROLLEN = ("ton", "kontext")


def kamera_from_name(name: str) -> str | None:
    """Kamera aus dem Dateinamen-Präfix: FX3_… → FX3, a7MK4_… → a7MK4, sonst None."""
    for rx, kam in KAMERA_RE:
        if rx.match(name):
            return kam
    return None


def kamera_for(rec: dict) -> str | None:
    """Kamera eines Index-Eintrags: Feld „kamera“, sonst Dateiname."""
    k = rec.get("kamera")
    if isinstance(k, str) and k.strip():
        return kamera_from_name(k.strip()) or k.strip()
    return kamera_from_name(rec.get("name") or Path(rec["path"]).name)


def rolle_for(rec: dict, kamera: str | None) -> str:
    """Rolle aus dem Index (kamera_rolle); fehlt sie: FX3 → ton, a7MK4 → kontext; sonst Fehler."""
    r = rec.get("kamera_rolle")
    if r in ROLLEN:
        return r
    if kamera == "FX3":
        return "ton"
    if kamera == "a7MK4":
        return "kontext"
    raise AutoCutError(f"{rec.get('name')}: keine Kamerarolle im Index und Kamera nicht am Namen erkennbar — "
                       f"bitte kamera_rolle (ton/kontext) im Transkript-Index nachtragen.")


def build_media(charge: Charge, probe=M.ffprobe, proxy_finder=M.proxy_for) -> tuple[dict, list[str]]:
    """Interview-Clips aus dem Index prüfen und media.json-Struktur aufbauen.

    Gibt (media, warnungen) zurück; harte Fehler (fehlende Datei, Proxy-Abweichung, Mischformat,
    unbekannte Rolle) werden gesammelt und als ein AutoCutError mit vollständiger Liste geworfen.
    """
    interviews = [r for r in charge.load_index() if r.get("kategorie") == "Interviews"]
    if not interviews:
        raise AutoCutError(f"Keine Interview-Clips im Transkript-Index ({charge.intern / 'transcripts_index.json'}).")
    fehler: list[str] = []
    warnungen: list[str] = []
    clips: dict[str, dict] = {}
    ordner: dict[str, dict[str, list[str]]] = {}
    for rec in interviews:
        path = rec["path"]
        name = rec.get("name") or Path(path).name
        try:
            info = probe(path)
        except AutoCutError as e:
            fehler.append(f"{name}: {str(e).splitlines()[0]}")
            continue
        proxy = proxy_finder(path)
        pinfo = None
        if proxy is None:
            warnungen.append(f"{name}: kein Proxy unter {Path(path).parent / M.PROXY_DIR} — Resolve nutzt das Original.")
        else:
            try:
                pinfo = probe(proxy)
            except AutoCutError as e:
                fehler.append(f"{name}: Proxy nicht lesbar — {str(e).splitlines()[0]}")
                continue
            for prob in M.check_proxy_match(info, pinfo):
                fehler.append(f"{name}: {prob} ({proxy.name})")
        kamera = kamera_for(rec)
        try:
            rolle = rolle_for(rec, kamera)
        except AutoCutError as e:
            fehler.append(str(e))
            continue
        if kamera is None:
            kamera = "unbekannt"
            warnungen.append(f"{name}: Kamera nicht am Dateinamen erkennbar (Rolle {rolle} aus dem Index).")
        folder = Path(path).parent.name
        fp = rec.get("fingerprint")
        if not fp:
            fp = M.fingerprint(path)
            warnungen.append(f"{name}: kein Fingerprint im Index, neu berechnet.")
        clips[path] = {"original": info.to_dict(), "proxy": pinfo.to_dict() if pinfo else None,
                       "proxy_path": str(proxy) if proxy else None, "kamera": kamera, "rolle": rolle,
                       "ordner": folder, "person": rec.get("person"), "fingerprint": fp}
        ordner.setdefault(folder, {"ton": [], "kontext": []})[rolle].append(path)
    if fehler:
        raise AutoCutError("Vorbereitung abgebrochen, media.json nicht geschrieben:\n  - " + "\n  - ".join(fehler))

    # Format: erste Ton-Datei bestimmt; Mischformate → Abbruch
    ton_paths = [p for grp in ordner.values() for p in grp["ton"]]
    if not ton_paths:
        raise AutoCutError("Kein Interview-Clip mit Rolle „ton“ — ohne Ton-Kamera kein Rohschnitt. "
                           "kamera_rolle im Transkript-Index prüfen.")
    fmt = M.timeline_format(M.MediaInfo.from_dict(clips[ton_paths[0]]["original"]))
    misch: list[str] = []
    for path, c in clips.items():
        f = M.timeline_format(M.MediaInfo.from_dict(c["original"]))
        nm = Path(path).name
        if abs(f["fps"] - fmt["fps"]) > 0.01:
            misch.append(f"{nm}: {f['fps']} fps statt {fmt['fps']}")
        elif f["orientation"] != fmt["orientation"]:
            misch.append(f"{nm}: {f['orientation']} statt {fmt['orientation']}")
        elif (f["width"], f["height"]) != (fmt["width"], fmt["height"]):
            msg = f"{nm}: {f['width']}×{f['height']} statt {fmt['width']}×{fmt['height']}"
            if c["rolle"] == "ton":
                misch.append(msg)
            else:
                warnungen.append(msg + " (Kontext-Kamera, wird in der Timeline skaliert)")
    if misch:
        raise AutoCutError("Mischformate im Interview-Material, media.json nicht geschrieben:\n  - "
                           + "\n  - ".join(misch))
    for folder, grp in ordner.items():
        if not grp["kontext"]:
            warnungen.append(f"{folder}: nur Ton-Kamera, kein a7-Clip — V2 bleibt dort leer.")
        if not grp["ton"]:
            warnungen.append(f"{folder}: nur Kontext-Kamera, kein FX3-Clip — Ordner ohne O-Ton-Quelle.")
    return {"format": fmt, "clips": clips, "ordner": ordner}, warnungen


def print_overview(media: dict, warnungen: list[str]) -> None:
    fmt = media["format"]
    print(f"Format: {fmt['width']}×{fmt['height']} {fmt['orientation']} @ {fmt['fps']} fps")
    print(f"Clips: {len(media['clips'])} in {len(media['ordner'])} Interview-Ordnern")
    for folder, grp in media["ordner"].items():
        ton = ", ".join(Path(p).name for p in grp["ton"]) or "—"
        kon = ", ".join(Path(p).name for p in grp["kontext"]) or "—"
        print(f"  {folder}\n    Ton:     {ton}\n    Kontext: {kon}")
    ohne_proxy = [Path(p).name for p, c in media["clips"].items() if not c["proxy_path"]]
    print(f"Proxies: {len(media['clips']) - len(ohne_proxy)}/{len(media['clips'])} gefunden und geprüft")
    for w in warnungen:
        print(f"WARNUNG: {w}")


def check_resolve() -> None:
    """Optional: Erreichbarkeit von Resolve (nur Lesen: Projektname). Nutzt resolve_api aus Task 8."""
    try:
        from niro_autocut.resolve_api import connect  # noqa: WPS433
    except ImportError:
        print("Resolve-Prüfung übersprungen: niro_autocut.resolve_api noch nicht vorhanden.")
        return
    resolve = connect()
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject() if pm else None
    if project is None:
        raise AutoCutError("Resolve läuft, aber kein Projekt ist geöffnet.")
    print(f"Resolve erreichbar, offenes Projekt: {project.GetName()}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AutoCut: Charge vorbereiten (media.json).")
    ap.add_argument("charge", help="Pfad zur Charge (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--video", help="Cutter-Plan (video-N-*.md), nötig bei mehreren Plänen")
    ap.add_argument("--check-resolve", action="store_true", help="zusätzlich Resolve-Erreichbarkeit prüfen")
    args = ap.parse_args(argv)
    try:
        ch = Charge.open(args.charge)
        plan_path = ch.resolve_plan(args.video)
        plan = parse_plan(plan_path)
        print(f"Charge: {ch.root}\nPlan:   {plan_path.name} ({len(plan.rows)} Zeilen"
              + (f", Ziel {plan.ziel_laenge_s:.0f} s" if plan.ziel_laenge_s else "") + ")")
        media, warnungen = build_media(ch)
        if plan.format_hint and plan.format_hint != media["format"]["orientation"]:
            warnungen.append(f"Plan nennt {plan.format_hint}, Material ist {media['format']['orientation']} "
                             f"— das Material bestimmt das Timeline-Format (Spec).")
        print_overview(media, warnungen)
        out = ch.write_json("media.json", media)
        print(f"Geschrieben: {out}")
        if args.check_resolve:
            check_resolve()
    except AutoCutError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
