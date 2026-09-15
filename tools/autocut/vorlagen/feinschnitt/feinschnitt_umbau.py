"""Vorlage (Stand 15.09.2026): bestehende Feinschnitt-Timeline für Handarbeit umbauen — nur V2 und V4 ersetzen.

Aufruf: tools/autocut/venv/bin/python _intern/feinschnitt_umbau.py [--ausfuehren]
- V2: a7 wieder durchgehend unter jedem FX3-Stück wie im Rohschnitt, an den bisherigen A-Abschnitten geteilt. Nur diese Stücke
  sind aktiv, der Rest ist deaktiviert → sichtbares Bild unverändert, Wechsel per Roll-Edit verschiebbar.
- V4: die Grafikdatei in je einen Clip pro Grafik-Element zerlegt, vollständig transparente Bereiche herausgeschnitten.
Nur für Timelines im alten Aufbau nötig (V2 nur in den A-Abschnitten, V4 ein Clip über die ganze Länge): feinschnitt_bauen.py
baut V2 durchgehend und V4 je Element inzwischen selbst — dann meldet dieses Skript „Bereits umgebaut".
Vorher Readback: V1/V2/V4 müssen dem Stand nach dem Bau entsprechen, sonst hat der User schon geändert → nichts schreiben.
Ohne --ausfuehren nur Prüfung. Ersetzt nur eigene Items dieser Session; Media-Pool-Items kommen aus den vorhandenen Items
(keine Bin-Navigation). Während der Wiedergabe liefert DeleteClips False → dann Abbruch vor jeder Änderung an der Spur.
Eingaben: Plan aus feinschnitt_bauen.py im selben Ordner (dessen ANPASSEN-Block gefüllt, PROJEKT = Freigabe),
_intern/autocut/probe.json. Schreibt _intern/autocut/feinschnitt_umbau.json.
Herkunft: Taxodia-Charge, _intern/feinschnitt_umbau.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
TIMELINE = "<Timeline-Name>"  # gebaute Feinschnitt-Timeline „AutoCut <video-kurz> JJJJ-MM-TT HHMM Feinschnitt" (feinschnitt.json → "timeline")
# ── Ende ANPASSEN ──────────────────────────────────

HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)


def main() -> None:
    if "<" in TIMELINE:
        raise SystemExit("ANPASSEN-Block in feinschnitt_umbau.py füllen: TIMELINE (Name steht in _intern/autocut/feinschnitt.json unter \"timeline\").")
    tl_json, shots = fb.lade()
    p, fehler = fb.plan(tl_json, shots)
    if fehler:
        raise SystemExit("Plan fehlerhaft:\n  " + "\n  ".join(fehler))
    fb.bericht(p)
    session = RA.ResolveSession(RA.connect(), probe=json.loads((fb.AC / "probe.json").read_text()))
    if session.project_name != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{session.project_name}' ≠ Freigabe '{fb.PROJEKT}' — nichts geschrieben.")
    proj, mp = session.project, session.media_pool
    tl = session.find_timeline(TIMELINE)
    if tl is None:
        raise SystemExit("Feinschnitt-Timeline nicht gefunden.")
    start = int(tl.GetStartFrame())

    def lies(idx: int) -> list[tuple]:
        return sorted(((int(x.GetStart()) - start, int(x.GetDuration()), int(x.GetLeftOffset()), bool(x.GetClipEnabled()), x)
                       for x in (tl.GetItemListInTrack("video", idx) or [])), key=lambda t: t[0])

    v1, v2, v4 = lies(1), lies(2), lies(4)
    soll_v1 = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f) for i in p["V1"])
    soll_v2_alt = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f, i.src_in_f) for i in p["V2"])
    soll_v2_neu = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f, i.src_in_f, i.enabled) for i in p["V2_voll"])
    soll_v4_neu = sorted((i.rec_in_f, i.rec_out_f - i.rec_in_f, i.src_in_f) for i in p["V4"])
    if [(a, d, o, e) for a, d, o, e, _ in v2] == soll_v2_neu and [(a, d, o) for a, d, o, _, _ in v4] == soll_v4_neu:
        raise SystemExit("Bereits umgebaut — nichts zu tun.")
    abw = []
    if [(a, d) for a, d, *_ in v1] != soll_v1:
        abw.append("V1 weicht vom Bau ab")
    if [(a, d, o) for a, d, o, e, _ in v2] != soll_v2_alt or not all(e for *_, e, _ in v2):
        abw.append("V2 weicht vom Bau ab")
    if [(a, d) for a, d, *_ in v4] != [(0, fb.ENDE)]:
        abw.append("V4 weicht vom Bau ab")
    if abw:
        raise SystemExit(f"Timeline wurde inzwischen geändert ({'; '.join(abw)}) — nichts geschrieben, erst mit dem User abstimmen.")
    media = {}
    for _, _, _, _, x in v2 + v4:
        mpi = x.GetMediaPoolItem()
        media[mpi.GetClipProperty("File Path")] = mpi
    fehlend = [c for c in {i.clip for i in p["V2_voll"] + p["V4"]} if not any(RA._norm(c) == RA._norm(k) for k in media)]
    if fehlend:
        raise SystemExit(f"Media-Pool-Items fehlen für {fehlend} — nichts geschrieben.")
    print(f"Prüfung ok: V2 {len(v2)} → {len(p['V2_voll'])} Stücke ({sum(not i.enabled for i in p['V2_voll'])} deaktiviert), "
          f"V4 1 → {len(p['V4'])} Clips")
    if "--ausfuehren" not in sys.argv:
        return
    out = {"projekt": session.project_name, "timeline": TIMELINE}
    user_tl = proj.GetCurrentTimeline()
    bin_vorher = mp.GetCurrentFolder()
    out["aktiv_vorher"] = user_tl.GetName() if user_tl else None
    out["bin_vorher"] = bin_vorher.GetName() if bin_vorher else None
    gewechselt = user_tl is None or user_tl.GetName() != TIMELINE
    try:
        if gewechselt:  # DeleteClips wirkt nur auf der aktiven Timeline
            proj.SetCurrentTimeline(tl)
        if not tl.DeleteClips([t[4] for t in v2], False):
            raise SystemExit("DeleteClips V2 abgelehnt (Wiedergabe läuft?) — nichts verändert.")
        session.append_items(tl, p["V2_voll"], media, start)
        out["v2_umgebaut"] = True
        if not tl.DeleteClips([t[4] for t in v4], False):
            raise SystemExit("DeleteClips V4 abgelehnt (Wiedergabe läuft?) — V2 ist umgebaut, V4 unverändert.")
        session.append_items(tl, p["V4"], media, start)
        out["v4_umgebaut"] = True
    finally:
        if gewechselt and user_tl is not None:
            proj.SetCurrentTimeline(user_tl)
        if bin_vorher is not None:
            mp.SetCurrentFolder(bin_vorher)
        out["gespeichert"] = session.save_project()
        v1n, v2n, v4n = lies(1), lies(2), lies(4)
        out["v1_unveraendert"] = [(a, d) for a, d, *_ in v1n] == soll_v1
        out["v2_identisch"] = [(a, d, o, e) for a, d, o, e, _ in v2n] == soll_v2_neu
        out["v4_identisch"] = [(a, d, o) for a, d, o, _, _ in v4n] == soll_v4_neu
        out["v2"] = {"stuecke": len(v2n), "aktiv": sum(e for *_, e, _ in v2n)}
        out["v4_clips"] = len(v4n)
        out["audio"] = {f"A{i}": len(tl.GetItemListInTrack("audio", i) or []) for i in (1, 2, 3)}
        out["v3"] = len(tl.GetItemListInTrack("video", 3) or [])
        out["ende"] = int(tl.GetEndFrame()) - start
        out["aktiv_nachher"] = proj.GetCurrentTimeline().GetName()
        out["bin_nachher"] = mp.GetCurrentFolder().GetName() if mp.GetCurrentFolder() else None
        out["warnungen"] = session.warnings
        (fb.AC / "feinschnitt_umbau.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
