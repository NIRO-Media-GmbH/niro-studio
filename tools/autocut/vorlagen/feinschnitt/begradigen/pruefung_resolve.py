"""Vorlage (Stand 15.09.2026): Begradigung in Resolve selbst prüfen — eigene Prüf-Timeline + Quick Export.

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/pruefung_resolve.py aufbauen|export|loeschen
        (Schritt ist Pflicht; Abweichung vom Original: dort galt ohne Argument „aufbauen")
aufbauen: eigene Timeline NAME — je Interview-Clip N Frames ohne und N Frames mit Transform (parameter.json), beide mit
          Grade (CDL + LC-709 aus ../color/grading_vorschlag.json über ../color/grading_anwenden.py), dazu PUNCH_CLIP mit
          Punch-in-Werten; Timeline und Bin des Users danach zurück (auch bei Fehler).
export:   Prüf-Timeline kurz aktivieren, Quick Export „ProRes 422 HQ" nach pruefung/pruefung_render.mov, danach Timeline und
          Bin des Users zurück; schreibt pruefung/plan.json (Reihenfolge der Stücke).
loeschen: eigene Prüf-Timeline löschen (nur wenn sie nicht aktiv ist) und speichern.
Eingaben: proben.json (proben_waehlen.py, je Clip die zweite Probezeit), parameter.json, ../autocut/probe.json.
Ausgaben: pruefung/zustand.json (Timeline-Name + Bin-ID des Users), pruefung_render.mov, plan.json.
Ablauf: aufbauen → export → pruefung_auswerten.py → loeschen → aufraeumen_begradigen.py → Render lokal löschen.
Schutz: nur im freigegebenen Projekt PROJEKT, nur die eigene Timeline; Clips kommen per Dedupe aus dem Media Pool
(fehlende werden in BIN_PFAD importiert). Transform, CDL und LUT werden nur auf den eigenen Prüf-Items gesetzt.
Befund (15.09.): Senkrechte vorher −2,5° bis +1,6°, nachher gerade (bis +0,3° bei Setups mit Architekturkanten), keine
schwarzen Ränder.
Herkunft: Taxodia-Charge, _intern/begradigen/pruefung_resolve.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
sys.path.insert(0, str(HIER.parent / "color"))
sys.path.insert(0, str(HIER.parent / "color" / "skripte"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402
import grading_anwenden as GA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # in dieser Session freigegebenes Resolve-Projekt (Name exakt wie in Resolve)
NAME = "Claude Begradigung-Prüfung <JJJJ-MM-TT>"  # eigene Prüf-Timeline (darf noch nicht existieren)
BIN_PFAD = ["AutoCut", "<video-kurz>"]  # eigener Media-Pool-Bin für fehlende Importe (Bin des AutoCut-Laufs)
PUNCH_CLIP = None  # Clip-Stamm des Punch-in-Stücks (z. B. "FX3_0001") für ein drittes Prüfstück; None = kein Punch-in
FPS = 25  # Framerate der eigenen Timeline = Projekt-/Feinschnitt-Framerate (feinschnitt_bauen.FPS)
W, H = 3840, 2160  # Auflösung der eigenen Timeline in px = Feinschnitt-Timeline
# ── Ende ANPASSEN ──────────────────────────────────

AUS = HIER / "pruefung"
N = 10


def plan() -> list[dict]:
    proben = json.loads((HIER / "proben.json").read_text())
    par = json.loads((HIER / "parameter.json").read_text())
    stuecke = []
    for clip, zeiten in sorted(proben.items()):
        stem = Path(clip).stem
        src = round(zeiten[1] * FPS)
        for art in ("ohne", "mit") + (("punch",) if stem == PUNCH_CLIP else ()):
            props = {} if art == "ohne" else par[stem]["resolve" if art == "mit" else "resolve_punch_in"]
            stuecke.append({"clip": clip, "stem": stem, "art": art, "src": src, "rec": len(stuecke) * N, "props": props})
    return stuecke


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("aufbauen", "export", "loeschen"):
        raise SystemExit("Schritt fehlt: aufbauen | export | loeschen — nichts geschrieben.")
    s = RA.ResolveSession(RA.connect(), probe=json.loads((HIER.parent / "autocut" / "probe.json").read_text()))
    if s.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    proj, mp = s.project, s.media_pool
    AUS.mkdir(exist_ok=True)
    zustand = AUS / "zustand.json"
    if cmd == "aufbauen":
        if s.find_timeline(NAME):
            raise SystemExit("Prüf-Timeline existiert schon.")
        user_tl, user_bin = proj.GetCurrentTimeline(), mp.GetCurrentFolder()
        zustand.write_text(json.dumps({"user_timeline": user_tl.GetName(), "user_bin_id": user_bin.GetUniqueId()}, ensure_ascii=False))
        stuecke = plan()
        vorschlag = json.loads((HIER.parent / "color" / "grading_vorschlag.json").read_text())
        try:
            folder = s.ensure_bin(BIN_PFAD)
            media = s.import_media(sorted({x["clip"] for x in stuecke}), folder)
            tl = s.create_timeline(NAME, float(FPS), W, H, "01:00:00:00")
            start = int(tl.GetStartFrame())
            items = [Item("V1", x["clip"], x["src"], x["src"] + N, x["rec"], x["rec"] + N, True, x["art"], "pruef", True) for x in stuecke]
            added = s.append_items(tl, items, media, start)
            erg = []
            for x, it in zip(stuecke, added):
                ok_t = bool(it.SetProperties(x["props"])) if x["props"] else True
                _, w = GA.cdl_fuer(vorschlag, it.GetName())
                ok_c = bool(it.SetCDL(GA.resolve_cdl(w))) and bool(it.GetNodeGraph().SetLUT(1, GA.LUT_REL))
                erg.append((x["stem"], x["art"], ok_t, ok_c))
            print(json.dumps({"timeline": NAME, "stuecke": erg}, ensure_ascii=False))
        finally:
            user = s.find_timeline(json.loads(zustand.read_text())["user_timeline"])
            proj.SetCurrentTimeline(user)
            ordner = next((f for f in s.all_folders() if f.GetUniqueId() == json.loads(zustand.read_text())["user_bin_id"]), None)
            if ordner is not None:
                mp.SetCurrentFolder(ordner)
            print("zurück:", proj.GetCurrentTimeline().GetName(), mp.GetCurrentFolder().GetName())
    elif cmd == "export":
        z = json.loads(zustand.read_text())
        user_tl, user_bin = proj.GetCurrentTimeline(), mp.GetCurrentFolder()
        try:
            proj.SetCurrentTimeline(s.find_timeline(NAME))
            time.sleep(1.0)
            print("Quick Export:", proj.RenderWithQuickExport("ProRes 422 HQ", {"TargetDir": str(AUS), "CustomName": "pruefung_render",
                                                                                "EnableUpload": False}), flush=True)
        finally:
            proj.SetCurrentTimeline(user_tl)
            if user_bin is not None:
                mp.SetCurrentFolder(user_bin)
            print("zurück:", proj.GetCurrentTimeline().GetName(), mp.GetCurrentFolder().GetName(), "| Zustand beim Aufbau:", z)
        (AUS / "plan.json").write_text(json.dumps(plan(), ensure_ascii=False, indent=1))
    elif cmd == "loeschen":
        tl = s.find_timeline(NAME)
        if tl is not None and proj.GetCurrentTimeline().GetName() != NAME:
            print("gelöscht:", mp.DeleteTimelines([tl]), s.save_project())


if __name__ == "__main__":
    main()
