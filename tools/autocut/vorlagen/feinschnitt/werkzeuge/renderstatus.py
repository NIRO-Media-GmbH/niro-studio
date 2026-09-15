"""Vorlage (Stand 15.09.2026): Render- und Sperrstatus lesen — läuft ein Render, welche Jobs, welche Spuren sind gesperrt?

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/renderstatus.py
Ausgabe: IsRenderingInProgress; Anzahl Render-Jobs und die letzten 5 (Timeline, Zielordner, Dateiname, Status);
         Timecode der aktiven Timeline; Sperrstatus V1–V4 und A1–A5 der aktiven Timeline.
Nur lesend. Vor Render-Tests und schreibenden Läufen: rendert Resolve gerade, nichts starten; eigene Test-Jobs danach
wieder löschen (Job-Liste des Users bleibt sonst voll). Bricht ab, wenn keine Timeline aktiv ist.
Gemessen (Resolve 21.1): direkt nach StartRendering liefert IsRenderingInProgress noch False → bei eigenen Jobs auf
GetRenderJobStatus == Complete warten, nicht auf IsRenderingInProgress.

Herkunft: Taxodia-Charge, Session-Scratchpad renderstatus.py
"""
import sys
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
# (keine chargen-spezifischen Werte)
# ── Ende ANPASSEN ──────────────────────────────────

r = RA.connect(); p = r.GetProjectManager().GetCurrentProject()
print("Rendering läuft:", p.IsRenderingInProgress())
jobs = p.GetRenderJobList() or []
print("Render-Jobs:", len(jobs))
for j in jobs[-5:]:
    jid = j.get("JobId")
    print("  ", j.get("TimelineName"), j.get("TargetDir"), j.get("OutputFilename"), "|", p.GetRenderJobStatus(jid) if jid else "")
tl = p.GetCurrentTimeline(); s = tl.GetStartFrame()
print("TC:", tl.GetCurrentTimecode())
print("Spuren gesperrt:", {f"V{i}": tl.GetIsTrackLocked("video", i) for i in range(1, 5)}, {f"A{i}": tl.GetIsTrackLocked("audio", i) for i in range(1, 6)})
