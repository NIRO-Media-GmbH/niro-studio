"""Vorlage (Stand 15.09.2026): Echter Schreibtest an einem unsichtbaren eigenen Item — SetProperty, SetProperties, Readback, zurück.

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/schreibtest2.py
Ablauf:  ZoomX des Test-Items lesen → SetProperty(ZoomX, +0,002) + Readback → SetProperties({ZoomX, ZoomY}: +0,002) + Readback
         → beide auf den Ausgangswert zurück + Readback; zuletzt GetClipColor (nur lesen).
Ändert kurz ein Item: nur im freigegebenen Projekt PROJEKT (assert), nie während der Wiedergabe (werkzeuge/fenster.swift).
Ein deaktiviertes (nicht sichtbares) eigenes Item wählen, z. B. ein deaktiviertes Stück der Zweitkamera auf V2.
Stolpersteine: Das Zurücksetzen schreibt ZoomY = ZoomX-Ausgangswert → nur an Items mit ZoomX = ZoomY testen. Bricht das
Skript mittendrin ab, den Zoom des Items per Readback prüfen. START = -1 ist der Platzhalter: kein Item → Abbruch vor dem Schreiben.
Nie ein Ergebnis als gesetzt protokollieren ohne True plus Readback (15.09.: Schreibsperre ohne Wiedergabe beobachtet).

Herkunft: Taxodia-Charge, Session-Scratchpad schreibtest2.py
"""
import sys, time
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
PROJEKT = "<Resolve-Projekt>"  # Name des offenen Resolve-Projekts = Schreibfreigabe des Users in dieser Session
NAME = "<Timeline-Name>"  # exakter Name der eigenen Timeline mit dem Test-Item
SPUR = 2  # Videospur des Test-Items (V2 = Zweitkamera, dort liegen im Feinschnitt-Aufbau deaktivierte Stücke)
START = -1  # Record-Start des Test-Items [Frames ab Timeline-Start]; -1 = Platzhalter (bricht ab)
# ── Ende ANPASSEN ──────────────────────────────────

r = RA.connect(); p = r.GetProjectManager().GetCurrentProject()
assert p.GetName() == PROJEKT, p.GetName()
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == NAME)
s = tl.GetStartFrame()
x = next(i for i in tl.GetItemListInTrack("video", SPUR) if i.GetStart() - s == START)  # deaktiviertes Stück (nicht sichtbar)
z = float(x.GetProperty("ZoomX"))
print("vorher", z, "| SetProperty(+0.002):", x.SetProperty("ZoomX", z + 0.002), "| readback", x.GetProperty("ZoomX"))
print("SetProperties dict:", x.SetProperties({"ZoomX": z + 0.002, "ZoomY": z + 0.002}), "| readback", x.GetProperty("ZoomX"))
print("zurück:", x.SetProperties({"ZoomX": z, "ZoomY": z}), x.GetProperty("ZoomX"))
print("Farbe-Test (harmlos, gleiche Farbe):", x.GetClipColor())
