"""Vorlage (Stand 15.09.2026): Schreibsperre prüfen — nimmt Resolve gerade Item-Schreibaufrufe an? (ändert keine Werte)

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/schreibtest.py
Ablauf:  Seite und aktive Timeline; je Teststelle (Videospur, Record-Start) das Item suchen, aktiv/deaktiviert und ZoomX
         lesen und denselben Wert per SetProperty zurückschreiben → True = Schreiben geht, False = gesperrt;
         „nicht gefunden", wenn dort kein Item beginnt. Zuletzt Sperrstatus der Spuren V2 und V1.
Schreibt formal (gleicher Wert): nur im freigegebenen Projekt PROJEKT (assert), nie während der Wiedergabe
(werkzeuge/fenster.swift). Leere TESTSTELLEN → nur Sperrstatus.
Gemessen 15.09. (Resolve 21.1): Resolve lehnte zeitweise jede Item-Schreibaktion ab (SetProperty/SetProperties = False auf
allen Items, auch nach 1 min) — ohne Wiedergabe; Ursache unbestätigt (der User hatte ein Media-Pool-Audio im
Source-Viewer/Inspector offen). Deshalb nie ein Ergebnis als gesetzt protokollieren ohne True plus Readback; Nachsetzen
nur mit Prüfung, dass der Wert inzwischen nicht von Hand geändert wurde.

Herkunft: Taxodia-Charge, Session-Scratchpad schreibtest.py
"""
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts = Schreibfreigabe des Users in dieser Session
NAME = "<Timeline-Name>"  # exakter Name der eigenen Timeline mit den Teststellen
TESTSTELLEN = [  # (Videospur, Record-Start [Frames ab Timeline-Start]) eigener Items — sichtbare und deaktivierte mischen
    # (2, 2812),
]
# ── Ende ANPASSEN ──────────────────────────────────

r = RA.connect(); p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == PROJEKT, p.GetName()
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == NAME)
s = tl.GetStartFrame()
print("Seite:", r.GetCurrentPage(), "| aktiv:", p.GetCurrentTimeline().GetName())
for spur, start in TESTSTELLEN:
    x = next((i for i in tl.GetItemListInTrack("video", spur) if i.GetStart() - s == start), None)
    if x is None:
        print(f"V{spur}@{start}: nicht gefunden"); continue
    z = float(x.GetProperty("ZoomX"))
    print(f"V{spur}@{start} {x.GetName()[:24]} aktiv={x.GetClipEnabled()} Zoom {z:.4f} → SetProperty(ZoomX, gleich): {x.SetProperty('ZoomX', z)}")
print("Spur V2 gesperrt:", tl.GetIsTrackLocked("video", 2), "| V1:", tl.GetIsTrackLocked("video", 1))
