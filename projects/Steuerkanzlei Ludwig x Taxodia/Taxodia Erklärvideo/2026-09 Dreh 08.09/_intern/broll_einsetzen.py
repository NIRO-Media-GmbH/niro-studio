"""B-Roll aus der User-Auswahl in die Kurzfassung setzen (Taxodia, 15.09.2026).

Aufruf:  tools/autocut/venv/bin/python _intern/broll_einsetzen.py            → Probelauf (nur rechnen und prüfen)
         tools/autocut/venv/bin/python _intern/broll_einsetzen.py --bauen    → V3 in Resolve füllen + Readback

Quelle:  _intern/autocut/broll_auswahl.json (Timeline „B-Roll Auswahl" des Users, per _intern/broll_auswahl.py gelesen)
Ziel:    V3 der roh-Timeline aus _intern/autocut/build.json (eigene Timeline dieser Session), Projekt „Taxodia 09.26".

User-Regel 15.09.: nur die Bereiche aus der Auswahl verwenden — kürzen ja, nie verlängern. Jeder Shot wird hier
höchstens einmal benutzt, Tempo 100 % wie in der Auswahl (50p-Clips in der 25p-Timeline in Echtzeit).
Platzierung (Claude, 15.09.): Kaltstart, Bauchbinden-Momente, Beweis-Aussagen und beide CTAs bleiben Gesicht;
B-Roll deckt Titel, Innenschnitte (#12, #16, #19) und passende Motive laut Bild-Vorschlag. Wer im B-Roll
selbst spricht, liegt möglichst nicht unter seinem eigenen O-Ton (Lippen).
"""
from __future__ import annotations

import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/Users/jansantos/NIRO Studio/tools/autocut/src")
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item, MarkerSpec  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"
PROJEKT = "Taxodia 09.26"
FPS = 25

# (Shot-Nr aus der Auswahl, Versatz im Shot [Frames], Länge [Frames], Record-In [Frames], Beat, Inhalt)
PLAN = [
    (10, 0, 54, 345, "4", "Flammann geht zur Kanzlei-Tür mit Ludwig-Logo"),
    (11, 0, 32, 399, "4", "Ludwig begrüßt Flammann an der Tür, Handschlag"),
    (12, 34, 39, 431, "4", "beide gehen am Logo „Steuerkanzlei Ludwig“ vorbei ins Haus"),
    (13, 25, 44, 580, "5", "Ludwig führt Flammann ins Büro"),
    (14, 0, 69, 624, "5", "Ludwig setzt sich an den Schreibtisch, Flammann kommt dazu"),
    (4, 0, 75, 1128, "7", "Hein am Arbeitsplatz, seitlich weit, tippt und schreibt"),
    (3, 0, 46, 1203, "7", "Detail: Heins Hände tippen am Laptop"),
    (8, 0, 82, 1249, "7", "Hein am Arbeitsplatz von hinten, Fahrt"),
    (23, 0, 120, 1862, "9", "Laptop mit Taxodia-Lernplattform, Schärfe auf Flammann"),
    (21, 0, 136, 1982, "9", "Hein und Flammann im Gespräch am Tisch"),
    (5, 0, 34, 2352, "10", "Detail: Hände blättern im Gesetzbuch"),
    (6, 0, 62, 2386, "10", "Aufsicht: Hein blättert im Gesetzbuch"),
    (1, 0, 40, 2761, "11", "Hein von hinten vor den Monitoren"),
    (7, 0, 78, 2801, "11", "Hein nah, liest am Bildschirm"),
    (2, 0, 56, 2879, "11", "Hein tippt am Laptop, Fahrt"),
    (22, 0, 49, 3222, "12", "Detail: Laptop mit Taxodia-Lernplattform"),
    (27, 0, 51, 3271, "12", "Hein und Flammann am Laptop, Hein zeigt"),
    (26, 0, 88, 3322, "12", "Detail: Hand an der Maus"),
    (15, 0, 62, 3706, "13", "Ludwig und Flammann im Gespräch am Schreibtisch"),
    (9, 0, 75, 4162, "15", "Hein telefoniert am Arbeitsplatz"),
    (17, 0, 100, 4237, "16", "Ludwig und Flammann am Monitor, Fahrt"),
    (18, 0, 134, 4337, "16", "Monitor nah: Kursplan mit Häkchen und Farben — BLUR"),
    (29, 0, 84, 4471, "16", "Flammann telefoniert im Sessel, weit"),
    (19, 0, 77, 4700, "16", "Ludwig am Schreibtisch greift zum Telefon"),
    (20, 0, 57, 4777, "16", "Ludwig telefoniert"),
    (30, 0, 50, 4906, "17", "Flammann telefoniert im Sessel, nah"),
    (16, 0, 119, 4956, "18", "Flammann zeigt Ludwig etwas am Monitor"),
    (25, 0, 67, 5208, "19", "Hein und Flammann nah am Laptop"),
    (28, 0, 58, 5275, "19", "Hein und Flammann am Laptop, Fahrt"),
    (24, 85, 63, 5333, "19", "Hein und Flammann am Laptop, weit"),
]
MARKER = [  # (Shot-Nr, Farbe, Name, Notiz)
    (18, "Red", "BLUR Monitor C0255", "Heins echter Kursplan: Name „Hein, Jan-Philipp“, URL, Lesezeichenleiste und "
                                     "„Dozentin: Heike Becker“ blurren (Datenschutz)."),
    (23, "Yellow", "Prüfen: Name auf Laptop", "C0261: Dozentenprofil „Karin Thomas, Dipl.-Finanzwirtin (FH)“ lesbar — "
                                              "mit Taxodia klären oder blurren."),
    (22, "Yellow", "Prüfen: Name auf Laptop", "C0260: Dozentenprofil „Karin Thomas“ lesbar — mit Taxodia klären oder blurren."),
]


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
    prev = None
    for nr, off, n, rec, beat, inhalt in sorted(PLAN, key=lambda p: p[3]):
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
        prev = rec + n
    return zeilen, fehler


def bericht(zeilen: list[dict], tl: dict) -> None:
    ende = max(i["rec_out_f"] for i in tl["items"])
    gesamt = sum(z["dauer_f"] for z in zeilen)
    print(f"{len(zeilen)} Shots, {gesamt / FPS:.1f} s B-Roll = {100 * gesamt / ende:.0f} % der Timeline ({tc(ende)})")
    for z in zeilen:
        print(f"  #{z['beat']:<3} {tc(z['rec_in_f'])}–{tc(z['rec_out_f'])}  S{z['shot']:02d} {z['clip']} "
              f"{z['left_offset_f'] / FPS:7.2f}–{(z['left_offset_f'] + z['dauer_f']) / FPS:7.2f}s  {z['inhalt']}")


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
    try:
        folder = session.ensure_bin(["AutoCut", "video-1-taxodia-weg"])
        media = session.import_media(sorted({z["datei"] for z in zeilen}), folder)
        items = [Item("V3", z["datei"], z["src_in_f"], z["src_out_f"], z["rec_in_f"], z["rec_out_f"], True, z["beat"],
                      "broll", True) for z in zeilen]
        session.append_items(ziel, items, media, start)
        by_shot = {z["shot"]: z for z in zeilen}
        # MarkerSpec(frame, name, note, color, duration) — am 15.09. zuerst mit vertauschter Reihenfolge gebaut,
        # die drei Marker dann per MCP nachgesetzt.
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
                    "left_offset_f": int(it.GetLeftOffset())})
    soll = sorted((z["datei"], z["rec_in_f"], z["dauer_f"], z["left_offset_f"]) for z in zeilen)
    ist_t = sorted((i["datei"], i["rec_in_f"], i["dauer_f"], i["left_offset_f"]) for i in ist)
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
