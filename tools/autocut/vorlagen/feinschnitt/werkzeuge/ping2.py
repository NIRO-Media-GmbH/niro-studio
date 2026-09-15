"""Vorlage (Stand 15.09.2026): Einzeiliger Status — Antwortzeit, Projekt, aktive Timeline, Timecode des Playheads, Seite.

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/ping2.py
Ausgabe: „Antwort nach x s | Projekt … | aktiv … | TC … | Seite …"
Nur lesend. Zweimal kurz nacheinander aufrufen: wandert der TC, spielt der User ab (oder scrubbt) → nichts schreiben;
Vollbild-Wiedergabe zusätzlich mit werkzeuge/fenster.swift prüfen. Eine schnelle Antwort heißt nicht, dass Schreibaufrufe
angenommen werden (15.09.: Schreibsperre ohne Wiedergabe beobachtet) → werkzeuge/schreibtest.py.
Läuft extern über das AutoCut-venv, nicht in der MCP-Sandbox (run_script: import gesperrt). Bricht ab, wenn keine
Timeline aktiv ist.

Herkunft: Taxodia-Charge, Session-Scratchpad ping2.py
"""
import sys, time
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
# (keine chargen-spezifischen Werte)
# ── Ende ANPASSEN ──────────────────────────────────

t = time.time()
r = RA.connect(); p = r.GetProjectManager().GetCurrentProject()
tl = p.GetCurrentTimeline()
print(f"Antwort nach {time.time()-t:.2f} s | Projekt {p.GetName()} | aktiv {tl.GetName()} | TC {tl.GetCurrentTimecode()} | Seite {r.GetCurrentPage()}")
