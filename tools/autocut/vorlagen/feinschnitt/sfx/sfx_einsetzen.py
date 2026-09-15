"""Vorlage (Stand 15.09.2026): SFX-Plan (sfx_plan.json) in den Feinschnitt setzen und mit den Grafik-Clips verknüpfen.

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_einsetzen.py [--ausfuehren]
- Grafik-Clips auf V4 werden über ihren Quellbereich (Left-Offset = Frame der Grafikdatei) dem Element zugeordnet. Hat der
  User einen Grafik-Clip verschoben, wandern die SFX dieses Elements um dieselbe Differenz mit.
- SFX-Dateien bevorzugt aus den Bins des Users: vorhandene Media-Pool-Items per Dateipfad wiederverwenden (pfad_nas, nur lesen);
  nur fehlende in den eigenen Bin EIGENER_BIN importieren. In den User-Bins nichts verändern (offline Bins verknüpft der User neu).
- Spuren A4 „SFX 1" / A5 „SFX 2" (nur anlegen, wenn sie fehlen und leer sind), Pegel + Fades je Platzierung,
  jede SFX mit ihrem Grafik-Clip verknüpft (SetClipsLinked), damit sie beim Verschieben mitgehen.
Ohne --ausfuehren nur Prüfung: Plan (Elemente bekannt, Dateien vorhanden, keine Überlappung je Spur), Projekt = Freigabe
feinschnitt_bauen.PROJEKT, Timeline TIMELINE vorhanden, V4-Zuordnung eindeutig, A4/A5 leer. Bin und Timeline des Users werden
wiederhergestellt. Vorher sfx_vorpruefung.py, danach sfx_readback.py und (bei neu angelegten Spuren) sfx_ton_render.py.
Bericht: sfx_einsatz.json — projekt, timeline, aktiv (beim Start aktive Timeline), versatz {element: Frames, nur verschobene},
  sfx_aus_user_bin, sfx_neu_importiert, spuren_neu_angelegt, spurnamen {Spurindex: gesetzt}, gesetzt [je SFX: spur, start, element,
  sfx, pegel, fades, verknuepft, linked_readback], gespeichert, bin_nachher, timeline_nachher, warnungen.
Gemessenes Resolve-Verhalten (21.1, Messung 15.09.):
- Per AddTrack NACHTRÄGLICH angelegte Tonspuren (Timeline hat schon Clips) haben keinen Bus-Ausgang → stumm (Render −180 dB); die
  Bus-Zuweisung ist per API weder lesbar noch setzbar. feinschnitt_bauen.py legt A4/A5 deshalb schon beim Bau an. Legt dieses Skript
  Spuren an, weist der User sie in Resolve zu (Fairlight → Bus Assign → Main 1); danach sfx_ton_render.py.
- SetClipsLinked nimmt je Link-Gruppe nur einen Clip pro Spur auf: liegen mehrere SFX eines Elements auf derselben Spur, ersetzt jeder
  neue Link den vorigen, obwohl die Rückgabe True ist und linked_readback direkt danach 1 meldet (15.09.: 19 von 39 SFX verknüpft,
  je Grafik eine). Tatsächliche Links zeigt sfx_readback.py; nicht verknüpfte SFX folgen verschobenen Grafik-Clips nur beim erneuten
  Einsetzen über die Left-Offset-Zuordnung.
- Resolve lehnte zeitweise jede Item-Schreibaktion ab (Rückgabe False), während ein Media-Pool-Audio im Source-Viewer/Inspector offen
  war → nichts als gesetzt werten ohne True plus Readback; nicht schreiben, während der User abspielt.
Setzt 25 fps voraus (Quell-In = round(src_in_s · 25)); die Clip-FPS der SFX im Media Pool prüft sfx_vorpruefung.py.
Herkunft: Taxodia-Charge, _intern/sfx/sfx_einsetzen.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
TIMELINE = "<Timeline-Name>"  # Feinschnitt-Timeline in Resolve, exakter Name (Muster „AutoCut <video-kurz> JJJJ-MM-TT HHMM Feinschnitt")
EIGENER_BIN = ["AutoCut", "<video-kurz>", "SFX"]  # eigener Bin nur für SFX, die in keinem Bin des Users liegen (VIDEO_KURZ wie feinschnitt_bauen)
# ── Ende ANPASSEN ──────────────────────────────────

RA.TRACK_INDEX.update({"A3": 3, "A4": 4, "A5": 5})
HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)
SPURNAMEN = {4: "SFX 1", 5: "SFX 2"}  # Standard (15.09.): A4 „SFX 1", Überlappungen auf A5 „SFX 2"


def main() -> None:
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    platz = plan["platzierungen"] if isinstance(plan, dict) else plan
    tl_json, shots = fb.lade()
    p, fehler = fb.plan(tl_json, shots)
    elemente = {i.beat_nr: (i.rec_in_f, i.rec_out_f) for i in p["V4"]}
    probleme = []
    for e in platz:
        if e["element"] not in elemente:
            probleme.append(f"Element {e['element']} unbekannt")
        if not os.path.exists(e["pfad_nas"]):
            probleme.append(f"Datei fehlt: {e['pfad_nas']}")
    for spur in ("A4", "A5"):
        belegt = sorted((e["rec_frame"], e["rec_frame"] + e["dauer_frames"]) for e in platz if e["spur"] == spur)
        for (a0, a1), (b0, b1) in zip(belegt, belegt[1:]):
            if b0 < a1:
                probleme.append(f"{spur}: Überlappung {a0}–{a1} / {b0}–{b1}")
    if probleme:
        raise SystemExit("Plan fehlerhaft:\n  " + "\n  ".join(probleme))
    s = RA.ResolveSession(RA.connect(), probe=json.loads((fb.AC / "probe.json").read_text()))
    if s.project_name != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{s.project_name}' ≠ Freigabe '{fb.PROJEKT}' — nichts geschrieben.")
    proj, mp = s.project, s.media_pool
    tl = s.find_timeline(TIMELINE)
    if tl is None:
        raise SystemExit(f"Timeline '{TIMELINE}' nicht gefunden (ANPASSEN-Block prüfen) — nichts geschrieben.")
    start = int(tl.GetStartFrame())
    # V4-Clips ↔ Elemente über den Quellbereich; Verschiebung durch den User übernehmen
    v4 = tl.GetItemListInTrack("video", 4) or []
    zuordnung, versatz = {}, {}
    for eid, (a, b) in elemente.items():
        kand = [x for x in v4 if x.GetLeftOffset() < b and a < x.GetLeftOffset() + x.GetDuration()]
        if len(kand) != 1:
            probleme.append(f"Grafik-Clip für {eid} nicht eindeutig ({len(kand)})")
            continue
        x = kand[0]
        zuordnung[eid] = x
        versatz[eid] = (int(x.GetStart()) - start) - int(x.GetLeftOffset())  # 0, solange nicht verschoben
    belegt = {i: [(int(x.GetStart()) - start, int(x.GetStart()) - start + int(x.GetDuration()))
                  for x in (tl.GetItemListInTrack("audio", i) or [])] for i in (4, 5) if i <= int(tl.GetTrackCount("audio"))}
    if any(belegt.get(i) for i in (4, 5)):
        probleme.append(f"A4/A5 sind nicht leer: {belegt} — nichts geschrieben (erst abstimmen)")
    if probleme:
        raise SystemExit("\n".join(probleme))
    items = []
    for e in platz:
        rec = int(e["rec_frame"]) + versatz[e["element"]]
        src = int(round(float(e["src_in_s"]) * 25))
        items.append((e, Item(e["spur"], e["pfad_nas"], src, src + int(e["dauer_frames"]), rec, rec + int(e["dauer_frames"]),
                              True, e["element"], "sfx", False)))
    verschoben = {k: v for k, v in versatz.items() if v}
    print(f"{len(items)} SFX · A4 {sum(1 for e, _ in items if e['spur'] == 'A4')} · A5 {sum(1 for e, _ in items if e['spur'] == 'A5')}"
          f" · Grafik-Clips vom User verschoben: {verschoben or 'keine'}")
    if "--ausfuehren" not in sys.argv:
        return
    bin_vorher = mp.GetCurrentFolder()
    out = {"projekt": s.project_name, "timeline": TIMELINE, "aktiv": proj.GetCurrentTimeline().GetName(), "versatz": verschoben}
    try:
        # SFX bevorzugt aus den Bins des Users: vorhandene Media-Pool-Items per Dateipfad wiederverwenden,
        # eigener Bin nur, falls eine Datei dort fehlt.
        pfade = sorted({it.clip for _, it in items})
        index = s._path_index()
        media = {pf: index[RA._norm(s.map_path(pf))] for pf in pfade if RA._norm(s.map_path(pf)) in index}
        fehlend = [pf for pf in pfade if pf not in media]
        out["sfx_aus_user_bin"], out["sfx_neu_importiert"] = len(media), len(fehlend)
        if fehlend:
            media.update(s.import_media(fehlend, s.ensure_bin(EIGENER_BIN)))
        # Nachträglich angelegte Tonspuren sind ohne Bus-Ausgang stumm (Messung 15.09.) → melden, User weist den Bus zu
        spuren_vorher = int(tl.GetTrackCount("audio"))
        while int(tl.GetTrackCount("audio")) < 5:
            if not tl.AddTrack("audio", "stereo"):
                raise SystemExit("Audiospur konnte nicht angelegt werden.")
        out["spuren_neu_angelegt"] = int(tl.GetTrackCount("audio")) - spuren_vorher
        out["spurnamen"] = {i: bool(tl.SetTrackName("audio", i, n)) for i, n in SPURNAMEN.items()}
        gesetzt = []
        for spur in ("A4", "A5"):
            teil = [(e, it) for e, it in items if e["spur"] == spur]
            if not teil:
                continue
            neu = s.append_items(tl, [it for _, it in teil], media, start)
            for (e, it), x in zip(teil, neu):
                v = bool(x.SetProperties({"AudioVolume": float(e["gain_db"])}))
                f = bool(x.SetFades({"FadeIn": int(e.get("fade_in_f", 0)), "FadeOut": int(e.get("fade_out_f", 0))}))
                link = bool(tl.SetClipsLinked([zuordnung[e["element"]], x], True))
                gesetzt.append({"spur": spur, "start": int(x.GetStart()) - start, "element": e["element"], "sfx": e["sfx_name"],
                                "pegel": v, "fades": f, "verknuepft": link, "linked_readback": len(x.GetLinkedItems() or [])})
        out["gesetzt"] = gesetzt
    finally:
        if bin_vorher is not None:
            mp.SetCurrentFolder(bin_vorher)
        s.restore_user_timeline()  # append_items aktiviert TIMELINE; die beim Start aktive Timeline des Users zurückholen
        out["gespeichert"] = s.save_project()
        out["bin_nachher"] = mp.GetCurrentFolder().GetName() if mp.GetCurrentFolder() else None
        out["timeline_nachher"] = proj.GetCurrentTimeline().GetName() if proj.GetCurrentTimeline() else None
        out["warnungen"] = s.warnings
        (HIER / "sfx_einsatz.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        ok = [g for g in out.get("gesetzt", []) if g["pegel"] and g["fades"] and g["verknuepft"]]
        print(json.dumps({k: v for k, v in out.items() if k != "gesetzt"}, ensure_ascii=False), f"| gesetzt {len(out.get('gesetzt', []))}, vollständig ok {len(ok)}")
        if out.get("spuren_neu_angelegt"):
            print("ACHTUNG: A4/A5 wurden nachträglich angelegt und sind vermutlich stumm — User weist in Resolve den Bus zu "
                  "(Fairlight → Bus Assign → Main 1), danach sfx_ton_render.py.")


if __name__ == "__main__":
    main()
