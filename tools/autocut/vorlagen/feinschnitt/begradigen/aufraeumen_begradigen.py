"""Vorlage (Stand 15.09.2026): Eigene Kalibrier-/Prüf-Timelines und das Rasterbild der Begradigung in Resolve wieder löschen.

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/aufraeumen_begradigen.py               → Probelauf: nur auflisten
        tools/autocut/venv/bin/python _intern/begradigen/aufraeumen_begradigen.py --ausfuehren  → löschen + speichern
        (Abweichung vom Original: dort löschte der Aufruf ohne Flag sofort.)
Nach kalibrierung_resolve.py und pruefung_resolve.py (deren loeschen-Schritte entfernen nur Timelines, nicht raster.png):
- löscht nur Timelines mit exakt den Namen aus EIGENE; bricht ab, wenn eine davon gerade aktiv ist (erst „zurueck")
- löscht im eigenen Bin BIN_PFAD nur Clips „raster.png", deren Dateipfad …/begradigen/kalibrierung/raster.png ist
  (Pfad NFC-normalisiert: Resolve liefert Pfade mit Umlauten teils zerlegt/NFD)
- meldet übrige „Claude …"-Timelines und die aktive Timeline, speichert.
Schutz: nur im freigegebenen Projekt PROJEKT. Danach lokal löschen (Shell, im Ordner _intern/begradigen):
  rm -f kalibrierung/kalibrierung_render.mov pruefung/pruefung_render.mov; find kalibrierung pruefung -name "*.png" ! -name "raster.png" -delete
Herkunft: Taxodia-Session, Scratchpad aufraeumen_begradigen.py
"""
import sys
import unicodedata
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # in dieser Session freigegebenes Resolve-Projekt (Name exakt wie in Resolve)
EIGENE = [  # exakte Namen der eigenen Timelines: kalibrierung_resolve.NAME/NAME_ALT, pruefung_resolve.NAME
    # "Claude Transform-Kalibrierung JJJJ-MM-TT", "Claude Begradigung-Prüfung JJJJ-MM-TT",
]
BIN_PFAD = ["AutoCut", "<video-kurz>"]  # eigener Bin mit raster.png (wie kalibrierung_resolve.BIN_PFAD)
# ── Ende ANPASSEN ──────────────────────────────────


def main() -> None:
    r = RA.connect(); pm = r.GetProjectManager(); p = pm.GetCurrentProject()
    if p is None or p.GetName() != PROJEKT:
        raise SystemExit(f"Offenes Projekt ≠ Freigabe '{PROJEKT}' — nichts gelöscht.")
    mp = p.GetMediaPool()
    aktiv = p.GetCurrentTimeline().GetName()
    tls = [t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() in EIGENE]
    if aktiv in EIGENE:
        raise SystemExit(f"Eigene Prüf-Timeline ist aktiv ({aktiv}) — nichts gelöscht.")
    ausfuehren = "--ausfuehren" in sys.argv
    # eigenes Rasterbild im eigenen Bin
    f = mp.GetRootFolder()
    for teil in BIN_PFAD:
        f = next((s for s in (f.GetSubFolderList() or []) if s.GetName() == teil), None) if f else None
    raster = [c for c in ((f.GetClipList() or []) if f else []) if c.GetName() == "raster.png" and "begradigen/kalibrierung/raster.png" in unicodedata.normalize("NFC", c.GetClipProperty("File Path") or "")]
    if not ausfuehren:
        print("Probelauf — würde löschen: Timelines", [t.GetName() for t in tls], "| raster.png:", len(raster),
              "| Bin gefunden:", f is not None, "— Löschen mit --ausfuehren.")
        return
    print("Timelines löschen:", [t.GetName() for t in tls], mp.DeleteTimelines(tls) if tls else None)
    print("raster.png löschen:", len(raster), mp.DeleteClips(raster) if raster else None)
    print("übrig:", [t.GetName() for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName().startswith("Claude ")], "| aktiv:", p.GetCurrentTimeline().GetName(), "| gespeichert:", pm.SaveProject())


if __name__ == "__main__":
    main()
