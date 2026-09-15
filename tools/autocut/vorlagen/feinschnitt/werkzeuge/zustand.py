"""Vorlage (Stand 15.09.2026): Musikspuren A2/A3 einer Timeline lesen — Positionen, Quell-In, Pegel, Fades (Readback).

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/zustand.py
Ausgabe: Projekt, aktive Timeline; je Item auf A2/A3: Record-Start und Dauer [Frames ab Timeline-Start], Left-Offset,
         GetSourceStartFrame, AudioVolume [dB], Fades [Frames], Clipname (12 Zeichen); Anzahl Items auf V2, Timeline-Ende.
Nur lesend (keine Projektprüfung). Die Timeline wird per Name gesucht und muss nicht aktiv sein.
Zweck: Readback nach dem Musik-Bau oder nach einem Abbruch (fehlt ein eigenes Item?), Vergleich mit dem Musik-Plan.
Gemessen (Resolve 21.1): Quell-In immer per GetLeftOffset() prüfen — GetSourceStartFrame() liegt bei 50p-Video in einer
25p-Timeline oft 1 Frame darunter. SetProperty("AudioVolume") und SetFades wirken auch auf nicht aktiver Timeline.

Herkunft: Taxodia-Charge, Session-Scratchpad zustand.py
"""
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
name = "<Timeline-Name>"  # exakter Name der zu lesenden Timeline (z. B. die Feinschnitt-Timeline dieser Session)
# ── Ende ANPASSEN ──────────────────────────────────

r = RA.connect()
p = r.GetProjectManager().GetCurrentProject()
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == name)
s = tl.GetStartFrame()
print("Projekt:", p.GetName(), "| aktiv:", p.GetCurrentTimeline().GetName())
for idx in (2, 3):
    for x in tl.GetItemListInTrack("audio", idx) or []:
        print(f"A{idx} start {x.GetStart()-s} dauer {x.GetDuration()} left {x.GetLeftOffset()} srcStart {x.GetSourceStartFrame()} vol {x.GetProperty('AudioVolume')} fades {x.GetFades()} {x.GetName()[:12]}")
print("V2:", len(tl.GetItemListInTrack("video", 2) or []), "Ende:", tl.GetEndFrame() - s)
