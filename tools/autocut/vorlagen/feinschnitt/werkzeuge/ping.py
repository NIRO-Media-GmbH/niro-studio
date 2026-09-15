"""Vorlage (Stand 15.09.2026): Antwortet Resolve? Verbindung, Projektname und aktive Timeline mit Laufzeiten lesen.

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/ping.py
Ausgabe: Sekunden bis zur Verbindung, Projektname, aktive Timeline — jeweils mit Laufzeit, sofort ausgegeben (flush),
         damit man sieht, an welchem Schritt es hängt.
Nur lesend. Vor schreibenden Läufen und nach Abbrüchen: hängt ein Schritt, ist Resolve beschäftigt (Render, Analyse,
Wiedergabe) → nichts schreiben. Läuft extern über das AutoCut-venv, nicht in der MCP-Sandbox (run_script: import gesperrt).
Gemessen 15.09. (Resolve 21.1): während der Wiedergabe hing run_script (MCP) schon bei project.GetName(), das externe
venv-Python las normal weiter. GetCurrentProject() kann kurz None liefern, obwohl ein Projekt offen ist (Resolve beschäftigt)
→ kurz warten und erneut fragen, nie selbst ein Projekt laden.

Herkunft: Taxodia-Charge, Session-Scratchpad ping.py
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
r = RA.connect()
print("verbunden", round(time.time() - t, 1), "s", flush=True)
p = r.GetProjectManager().GetCurrentProject()
print("Projekt:", p.GetName(), round(time.time() - t, 1), "s", flush=True)
cur = p.GetCurrentTimeline()
print("aktiv:", cur.GetName() if cur else None, round(time.time() - t, 1), "s", flush=True)
