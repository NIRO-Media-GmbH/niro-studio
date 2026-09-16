"""Vorlage (Stand 15.09.2026): Grafikebene (Remotion, ProRes 4444 Alpha) als einen Clip auf V4 der eigenen Timeline setzen.

Aufruf: tools/autocut/venv/bin/python _intern/grafik_einsetzen.py <Render.mov>          → Probelauf: nur ffprobe des Renders
                                                                                          (Frames, pix_fmt, Größe, Bildrate), kein Resolve
        tools/autocut/venv/bin/python _intern/grafik_einsetzen.py <Render.mov> --bauen  → V4 setzen + Readback
        (Abweichung vom Original: dort schrieb der Aufruf ohne Flag sofort, --probe war der Probelauf.)

Ziel: roh-Timeline aus _intern/autocut/build.json (eigene Timeline dieser Session, per Unique-ID), Projekt PROJEKT.
Legt bei Bedarf Spur V4 „Grafik" an, importiert den Render in den eigenen Bin BIN
(Dedupe per Pfad) und setzt ihn ab Frame 0 (nur Bild). Stellt Timeline und Bin des Users wieder her, speichert,
prüft per Readback (Start, Dauer, Offset, Alpha-Modus). Schreibt _intern/autocut/grafik_einsatz.json.
Schutz: Projektname = Freigabe, V4 muss leer sein (kein doppeltes Einsetzen); Readback-Abweichung beim Anhängen bricht ab.
Gemessen (Resolve 21.1): ProRes 4444 aus Remotion (yuva444p) bekommt beim Import automatisch Alpha mode „Straight" und
deckt ohne weitere Einstellung; SetTrackName ist nur auf der aktiven Timeline zuverlässig.
Für den Aufbau zur Handarbeit (je Grafik-Element ein Clip, transparente Bereiche raus) baut feinschnitt_bauen.py V4 neu.

Nicht auf hochgeladene Timelines anwenden (`_intern/replay/uploads.json`) — dort neue Version bauen.

Herkunft: Taxodia-Charge, _intern/grafik_einsetzen.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import unicodedata
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402
from niro_autocut.timeline_model import Item  # noqa: E402

CH = Path(__file__).resolve().parent.parent
AC = CH / "_intern" / "autocut"

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts = Schreibfreigabe des Users in dieser Session
BIN = ["AutoCut", "<Video-Kurzname>"]  # eigener Media-Pool-Bin (build.json → „bin", an „/" getrennt)
# ── Ende ANPASSEN ──────────────────────────────────


def frames_of(pfad: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets,pix_fmt,width,height,r_frame_rate", "-of", "json", str(pfad)],
                       capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    print(f"Render: {s}")
    return int(s["nb_read_packets"])


def main() -> None:
    render = Path(sys.argv[1]).resolve()
    n = frames_of(render)
    if "--bauen" not in sys.argv:
        print("Probelauf — nichts geschrieben. V4 setzen mit --bauen.")
        return
    build = json.loads((AC / "build.json").read_text())
    probe = json.loads((AC / "probe.json").read_text())
    session = RA.ResolveSession(RA.connect(), probe=probe)
    if session.project_name != PROJEKT:
        raise SystemExit(f"Offenes Projekt '{session.project_name}' ≠ Freigabe '{PROJEKT}' — nichts geschrieben.")
    proj, mp = session.project, session.media_pool
    ziel = next((t for t in session.list_timelines() if t.GetUniqueId() == build["timeline_id"]), None)
    if ziel is None:
        raise SystemExit("Ziel-Timeline nicht gefunden — nichts geschrieben.")
    if int(ziel.GetTrackCount("video")) >= 4 and ziel.GetItemListInTrack("video", 4):
        raise SystemExit("V4 ist schon belegt — nichts geschrieben (kein doppeltes Einsetzen).")
    user_folder = mp.GetCurrentFolder()
    start = int(ziel.GetStartFrame())
    try:
        while int(ziel.GetTrackCount("video")) < 4:
            if not ziel.AddTrack("video"):
                raise SystemExit("Videospur V4 konnte nicht angelegt werden.")
        folder = session.ensure_bin(BIN)
        media = session.import_media([str(render)], folder)
        session.append_items(ziel, [Item("V4", str(render), 0, n, 0, n, True, "grafik", "grafik", True)], media, start)
        name_ok = bool(ziel.SetTrackName("video", 4, "Grafik"))  # nur auf der aktiven Timeline zuverlässig
    finally:
        session.restore_user_timeline()
        if user_folder is not None:
            mp.SetCurrentFolder(user_folder)
    gespeichert = session.save_project()
    v4 = ziel.GetItemListInTrack("video", 4) or []
    it = v4[0] if v4 else None
    mpi = it.GetMediaPoolItem() if it else None
    out = {
        "projekt": session.project_name, "timeline": ziel.GetName(), "render": str(render), "render_frames": n,
        "v4_items": len(v4), "start": (int(it.GetStart()) - start) if it else None, "dauer": int(it.GetDuration()) if it else None,
        "offset": int(it.GetLeftOffset()) if it else None,
        "alpha_modus": mpi.GetClipProperty("Alpha mode") if mpi else None,
        "datei": unicodedata.normalize("NFC", mpi.GetClipProperty("File Path")) if mpi else None,
        "spurname": ziel.GetTrackName("video", 4), "spurname_gesetzt": name_ok,
        "timeline_ende": int(ziel.GetEndFrame()) - start,
        "spuren": {f"V{i}": len(ziel.GetItemListInTrack("video", i) or []) for i in range(1, int(ziel.GetTrackCount("video")) + 1)},
        "aktive_timeline": proj.GetCurrentTimeline().GetName() if proj.GetCurrentTimeline() else None,
        "aktiver_bin": mp.GetCurrentFolder().GetName() if mp.GetCurrentFolder() else None,
        "gespeichert": gespeichert, "warnungen": session.warnings,
    }
    (AC / "grafik_einsatz.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
