"""Vorlage (Stand 15.09.2026): Render-Formate, Codecs und Presets lesen (Vorbereitung eines Kontroll-Renders, z. B. Ton als WAV).

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/render_formate.py
Ausgabe: aktive Timeline, Render läuft?, aktuelles Format/Codec und Render-Modus, Formate wav/mp4/quicktime/mov/wave
         (sonst die ersten 12), Codecs für „wav"/„WAV"/„Wave", die letzten 8 Render-Presets.
Nur lesend. Vor einem eigenen Render-Test die Deliver-Einstellungen des Users sichern: SaveAsNewRenderPreset(<Sicherung>)
→ SetRenderSettings/AddRenderJob/StartRendering → auf GetRenderJobStatus == Complete warten → Job löschen,
LoadRenderPreset(<Sicherung>) + DeleteRenderPreset(<Sicherung>).
Gemessen (Resolve 21.1): Tonspuren, die per AddTrack("audio", "stereo") erst nach dem ersten Anhängen entstehen, rendern
stumm (−180 dB); Bus-Zuweisung ist per API weder lesbar noch setzbar → nach nachträglich angelegten Tonspuren immer einen
kurzen Ton-Render zur Kontrolle machen.

Herkunft: Taxodia-Charge, Session-Scratchpad render_formate.py
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
print("aktiv:", p.GetCurrentTimeline().GetName(), "| Rendering:", p.IsRenderingInProgress())
print("aktuelles Format/Codec:", p.GetCurrentRenderFormatAndCodec(), "| Modus:", p.GetCurrentRenderMode())
f = p.GetRenderFormats()
print("Formate:", {k: v for k, v in f.items() if k.lower() in ("wav", "mp4", "quicktime", "mov", "wave")} or list(f.items())[:12])
for fmt in ("wav", "WAV", "Wave"):
    try:
        c = p.GetRenderCodecs(fmt)
        if c: print("Codecs", fmt, c)
    except Exception as e:
        pass
print("Presets:", (p.GetRenderPresetList() or [])[-8:])
