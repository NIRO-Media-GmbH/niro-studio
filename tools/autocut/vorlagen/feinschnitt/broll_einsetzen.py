"""Vorlage (Stand 15.09.2026): B-Roll aus der Auswahl-Timeline des Users auf V3 der eigenen roh-Timeline setzen.

Aufruf:  tools/autocut/venv/bin/python _intern/broll_einsetzen.py            → Probelauf (nur rechnen und prüfen)
         tools/autocut/venv/bin/python _intern/broll_einsetzen.py --bauen    → V3 in Resolve füllen + Readback
         danach: tools/autocut/venv/bin/python tools/autocut/scripts/autocut_readback.py "<Charge>" --timeline "<Name>"  → Bau-Readback (Replay-Runde)

Quelle:  _intern/autocut/broll_auswahl.json (Auswahl-Timeline des Users, per _intern/broll_auswahl.py gelesen),
         _intern/autocut/timeline.json (Beats, Timeline-Ende), _intern/autocut/probe.json (endFrame-Semantik).
Ziel:    V3 der roh-Timeline aus _intern/autocut/build.json (eigene Timeline dieser Session), Projekt PROJEKT.
Schreibt _intern/autocut/broll_einsatz.json (nur mit --bauen: Plan, Readback, Spuren, Marker, aktive Timeline/Bin)
         → Eingabe für _intern/grafik_review.py.

User-Regel 15.09.: nur die Bereiche aus der Auswahl verwenden — kürzen ja, nie verlängern. Jeder Shot wird hier
höchstens einmal benutzt, Tempo 100 % wie in der Auswahl (50p-Clips in der 25p-Timeline in Echtzeit).
Platzierung (Claude, 15.09.): Kaltstart, Bauchbinden-Momente, Beweis-Aussagen und CTAs bleiben Gesicht;
B-Roll deckt Titel, Innenschnitte und passende Motive laut Bild-Vorschlag. Wer im B-Roll
selbst spricht, liegt möglichst nicht unter seinem eigenen O-Ton (Lippen).
Prüfung (Probelauf): Versatz + Länge innerhalb der Auswahl, keine Überlappung, nicht über das Timeline-Ende, Beat bekannt,
jeder Shot höchstens einmal — bei Fehlern Exit 1, nichts geschrieben.
Brennweite (Spec 2026-09-21, _intern/autocut/telemetrie.json): nie zweimal dieselbe KB-Brennweite direkt hintereinander,
sonst digitaler Zoom auf einen der beiden Shots (gesetzt beim Bau); schnelle Zooms im genutzten Bereich = Hinweis.
Schutz (--bauen): Projektname = Freigabe, Ziel-Timeline per Unique-ID + Name, V3 muss leer sein (kein doppeltes Einsetzen);
Timeline und Bin des Users werden wiederhergestellt; Readback gegen den Plan + Innerhalb-Prüfung.
Gemessen (Resolve 21.1): startFrame/endFrame in Quellframes (50p: 2 × n) setzen n Timeline-Frames, Offsets im Readback
exakt; 30 Clips auf V3 in einem AppendToTimeline über das externe venv ok; AddMarker geht auch auf nicht aktiver Timeline.

Nicht auf hochgeladene Timelines anwenden (`_intern/replay/uploads.json`) — dort neue Version bauen.

Herkunft: Taxodia-Charge, _intern/broll_einsetzen.py
"""
from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut import telemetrie as TM  # noqa: E402
from niro_autocut.charge import load_config  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
TELE = TM.laden(AC)  # _intern/autocut/telemetrie.json (autocut_telemetrie.py); leer = Brennweitenregel nicht geprüft
TCFG = load_config(CH)["telemetrie"]

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts = Schreibfreigabe des Users in dieser Session
BIN = ["AutoCut", "<Video-Kurzname>"]  # eigener Media-Pool-Bin (build.json → „bin", an „/" getrennt)
FPS = 25  # Timeline-Bildrate [fps], ganzzahlig; Standard (15.09.)

# (Shot-Nr aus der Auswahl, Versatz im Shot [Frames], Länge [Frames], Record-In [Frames], Beat, Inhalt[, zoom])
# 7. Spalte optional: Zahl = digitaler Zoom des Shots fest (1.0 = keiner); weggelassen = Automatik der Brennweitenregel
# (telemetrie.brennweite_gleich_max, digitalzoom_faktor, digitalzoom_max); unter 1.0 (Rand würde sichtbar) oder über
# digitalzoom_max = Plan-Fehler. Ein hier erzwungener Zoom gehört in 6d als 8. Spalte in BROLL (6d rechnet sonst neu).
PLAN = [  # Frames = Timeline-Frames; Versatz + Länge ≤ Dauer des Shots in der Auswahl; Beat = nr aus timeline.json
    # (10, 0, 54, 345, "4", "Person A geht zur Tür (Motiv laut Standbild)"),
    # (11, 0, 40, 399, "4", "Detail Hände", 1.0),   # … ohne digitalen Zoom, auch wenn die Brennweite gleich ist
]
MARKER = [  # (Shot-Nr, Farbe, Name, Notiz) — Bildschirme mit lesbaren Namen/URLs: Red „BLUR …“ bzw. Yellow „Prüfen: …“
    # (18, "Red", "BLUR Monitor C0001", "Lesbare Namen, URL und Lesezeichenleiste blurren (Datenschutz)."),
]
# ── Ende ANPASSEN ──────────────────────────────────


def tc(f: int) -> str:
    return f"{f // FPS // 60:02d}:{f // FPS % 60:02d}:{f % FPS:02d}"


def laden():
    auswahl = json.loads((AC / "broll_auswahl.json").read_text())
    shots = {s["nr"]: s for s in auswahl["shots"]}
    tl = json.loads((AC / "timeline.json").read_text())
    build = json.loads((AC / "build.json").read_text())
    return auswahl, shots, tl, build


def pruefen(shots: dict, tl: dict) -> tuple[list[dict], list[str]]:
    fehler, zeilen = [], []
    ende = max(i["rec_out_f"] for i in tl["items"])
    beats = {b["nr"]: b for b in tl["beats"]}
    benutzt = Counter(p[0] for p in PLAN)
    for nr, n in benutzt.items():
        if n > 1:
            fehler.append(f"S{nr:02d} mehrfach benutzt ({n}×)")
    prev, folge = None, []  # folge: Eingabe der Brennweitenregel (TM.brennweitenfolge)
    for nr, off, n, rec, beat, inhalt, *rest in sorted(PLAN, key=lambda p: p[3]):
        s = shots[nr]
        if off < 0 or n <= 0 or off + n > s["dauer_f"]:
            fehler.append(f"S{nr:02d}: Versatz {off} + Länge {n} liegt außerhalb der Auswahl ({s['dauer_f']} Frames) — verlängert!")
        if prev and rec < prev:
            fehler.append(f"S{nr:02d} überlappt den Vorgänger (Record {rec} < {prev})")
        if rec + n > ende:
            fehler.append(f"S{nr:02d} ragt über das Timeline-Ende ({ende})")
        if beat not in beats:
            fehler.append(f"S{nr:02d}: Beat #{beat} unbekannt")
        faktor = s["clip_fps"] / FPS
        left = s["left_offset_f"] + off
        zeilen.append({"shot": nr, "clip": s["clip"], "datei": s["datei"], "beat": beat, "inhalt": inhalt,
                       "rec_in_f": rec, "rec_out_f": rec + n, "left_offset_f": left, "dauer_f": n,
                       "src_in_f": int(round(left * faktor)), "src_out_f": int(round((left + n) * faktor)),
                       "auswahl_f": [s["left_offset_f"], s["left_offset_f"] + s["dauer_f"]]})
        # genutzter Quellbereich in s (Tempo 100 %) → Brennweite am Schnitt (KB am Quell-In/-Out, auch in
        # broll_einsatz.json) und schnelle Zooms
        tele_rec = TM.finden(TELE, s["datei"])
        bereich = TM.genutzter_quellbereich_s(zeilen[-1]["src_in_f"], n, s["clip_fps"], False, FPS)
        zeilen[-1]["zoom_hinweise"] = TM.zoom_hinweise(f"S{nr:02d}", tele_rec, *bereich, cfg=TCFG)
        zeilen[-1]["kb_anfang"] = TM.kb_am(tele_rec, bereich[0], seite="anfang")
        zeilen[-1]["kb_ende"] = TM.kb_am(tele_rec, bereich[1], seite="ende")
        folge.append({"id": f"S{nr:02d}", "rec_in": rec, "rec_out": rec + n, "zoom_erzwungen": rest[0] if rest else None,
                      "kb_anfang": zeilen[-1]["kb_anfang"], "kb_ende": zeilen[-1]["kb_ende"]})
        prev = rec + n
    for z, e in zip(zeilen, TM.brennweitenfolge(folge, TCFG)):
        z["zoom"], z["zoom_hinweis"] = e["zoom"], e["hinweis"]
        if e["fehler"]:
            fehler.append(e["fehler"])
    return zeilen, fehler


def bericht(zeilen: list[dict], tl: dict) -> None:
    ende = max(i["rec_out_f"] for i in tl["items"])
    gesamt = sum(z["dauer_f"] for z in zeilen)
    print(f"{len(zeilen)} Shots, {gesamt / FPS:.1f} s B-Roll = {100 * gesamt / ende:.0f} % der Timeline ({tc(ende)})")
    for z in zeilen:
        # Brennweite am Quell-In → -Out des genutzten Bereichs wie in 6d („KB –" = unbekannt)
        kb = "KB –" if z.get("kb_anfang") is None else f"KB {z['kb_anfang']:g} → {z['kb_ende']:g} mm".replace(".", ",")
        print(f"  #{z['beat']:<3} {tc(z['rec_in_f'])}–{tc(z['rec_out_f'])}  S{z['shot']:02d} {z['clip']} "
              f"{z['left_offset_f'] / FPS:7.2f}–{(z['left_offset_f'] + z['dauer_f']) / FPS:7.2f}s  {z['inhalt']}  {kb}"
              + (f"  Zoom {z['zoom']:g}×".replace(".", ",") if z.get("zoom", 1.0) != 1.0 else ""))
    # ohne telemetrie.json eine Zeile; sonst alte oder mit anderen Schwellen gemessene Datensätze der genutzten Clips
    hinweise = (TM.telemetrie_hinweise([TM.finden(TELE, z["datei"]) for z in zeilen], TCFG) if TELE
                else [TM.OHNE_TELEMETRIE])
    for z in zeilen:
        hinweise += z.get("zoom_hinweise", []) + ([z["zoom_hinweis"]] if z.get("zoom_hinweis") else [])
    for h in hinweise:
        print(f"  Hinweis: {h}")


def bauen(zeilen: list[dict], build: dict) -> dict:
    probe = json.loads((AC / "probe.json").read_text())
    session = RA.ResolveSession(RA.connect(), probe=probe)
    if session.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{session.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    proj, mp = session.project, session.media_pool
    ziel = next((t for t in session.list_timelines() if t.GetUniqueId() == build["timeline_id"]), None)
    if ziel is None or ziel.GetName() != build["timeline"]:
        raise SystemExit(f"Ziel-Timeline '{build['timeline']}' nicht gefunden — nichts geschrieben.")
    if ziel.GetItemListInTrack("video", 3):
        raise SystemExit("V3 der Ziel-Timeline ist nicht leer — nichts geschrieben (kein doppeltes Einsetzen).")
    user_folder = mp.GetCurrentFolder()
    start = int(ziel.GetStartFrame())
    zoom_gesetzt: dict[str, bool] = {}
    try:
        folder = session.ensure_bin(BIN)
        media = session.import_media(sorted({z["datei"] for z in zeilen}), folder)
        items = [Item("V3", z["datei"], z["src_in_f"], z["src_out_f"], z["rec_in_f"], z["rec_out_f"], True, z["beat"],
                      "broll", True) for z in zeilen]
        session.append_items(ziel, items, media, start)
        # Digitaler Zoom der Brennweitenregel (Spec 2026-09-21): auf die Bildmitte, Pan/Tilt bleiben 0
        v3 = {int(x.GetStart()) - start: x for x in (ziel.GetItemListInTrack("video", 3) or [])}
        for z in zeilen:
            if z["zoom"] != 1.0 and z["rec_in_f"] in v3:
                gesetzt = [bool(RA._safe(v3[z["rec_in_f"]].SetProperty, False, k, float(z["zoom"])))
                           for k in ("ZoomX", "ZoomY")]
                zoom_gesetzt[f"S{z['shot']:02d}"] = all(gesetzt)
        by_shot = {z["shot"]: z for z in zeilen}
        # MarkerSpec(frame, name, note, color, duration) — Reihenfolge beachten: einmal vertauscht gebaut,
        # die Marker mussten danach per MCP nachgesetzt werden.
        session.add_markers(ziel, [MarkerSpec(by_shot[nr]["rec_in_f"], name, notiz, farbe, by_shot[nr]["dauer_f"])
                                   for nr, farbe, name, notiz in MARKER], start)
    finally:
        session.restore_user_timeline()
        if user_folder is not None:
            mp.SetCurrentFolder(user_folder)
    gespeichert = session.save_project()
    # Readback
    ist = []
    for it in ziel.GetItemListInTrack("video", 3) or []:
        ist.append({"datei": unicodedata.normalize("NFC", it.GetMediaPoolItem().GetClipProperty("File Path")),
                    "rec_in_f": int(it.GetStart()) - start, "dauer_f": int(it.GetDuration()),
                    "left_offset_f": int(it.GetLeftOffset()), "zoom": RA._safe(it.GetProperty, None, "ZoomX")})
    soll = sorted((z["datei"], z["rec_in_f"], z["dauer_f"], z["left_offset_f"]) for z in zeilen)
    ist_t = sorted((i["datei"], i["rec_in_f"], i["dauer_f"], i["left_offset_f"]) for i in ist)
    zoom_ist = {i["rec_in_f"]: i["zoom"] for i in ist}   # über den Record-In gepaart wie in 6d → Liste {shot, soll, ist}
    zoom_abweichungen = TM.zoom_abweichungen(zeilen, zoom_ist)
    ausserhalb = [z for z in zeilen if not (z["auswahl_f"][0] <= z["left_offset_f"]
                                             and z["left_offset_f"] + z["dauer_f"] <= z["auswahl_f"][1])]
    spuren = {k: len(ziel.GetItemListInTrack(k[0], k[1]) or []) for k in (("video", 1), ("video", 2), ("video", 3), ("audio", 1))}
    marker = Counter(v["color"] for v in (ziel.GetMarkers() or {}).values())
    cur = proj.GetCurrentTimeline()
    cf = mp.GetCurrentFolder()
    ergebnis = {
        "projekt": session.project_name, "timeline": ziel.GetName(), "timeline_id": build["timeline_id"],
        "v3_soll": len(soll), "v3_ist": len(ist), "identisch": soll == ist_t, "ausserhalb_auswahl": len(ausserhalb),
        "spuren": {f"{k[0][0].upper()}{k[1]}": v for k, v in spuren.items()}, "marker": dict(marker),
        "aktive_timeline": cur.GetName() if cur else None, "aktiver_bin": cf.GetName() if cf else None,
        "gespeichert": gespeichert, "warnungen": session.warnings, "plan": zeilen, "readback": ist,
        "zoom_gesetzt": zoom_gesetzt, "zoom_abweichungen": zoom_abweichungen,
    }
    (AC / "broll_einsatz.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1), encoding="utf-8")
    return ergebnis


if __name__ == "__main__":
    auswahl, shots, tl, build = laden()
    zeilen, fehler = pruefen(shots, tl)
    bericht(zeilen, tl)
    if fehler:
        print("\nFEHLER:\n  " + "\n  ".join(fehler))
        sys.exit(1)
    print(f"\nPrüfung ok: alle Shots innerhalb der Auswahl, keine Überlappung, jeder Shot höchstens einmal. "
          f"Ziel: '{build['timeline']}'")
    if "--bauen" in sys.argv:
        e = bauen(zeilen, build)
        print({k: v for k, v in e.items() if k not in ("plan", "readback")})
