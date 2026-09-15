"""Vorlage (Stand 15.09.2026): Probezeiten je Interview-Clip für linien_messen.py und pruefung_resolve.py wählen.

Aufruf: tools/autocut/venv/bin/python _intern/begradigen/proben_waehlen.py
Eingaben: Feinschnitt-Plan über ../feinschnitt_bauen.py (fb.lade/fb.plan: Interview-Items aus V1 + V2_voll, fb.FPS).
Je Clip 4 Zeitpunkte (Sekunden im Quellclip), gleichmäßig verteilt über die Mitten der genutzten Items.
Schreibt _intern/begradigen/proben.json {Clip-Pfad: [s0, s1, s2, s3]} (linien_messen.py nutzt alle vier,
pruefung_resolve.py die zweite). Nichts in Resolve. Eigener Schritt, weil linien_messen.py im transcribe-venv läuft
(cv2 mit LSD), das feinschnitt_bauen.py nicht laden kann (dort fehlt rapidfuzz).
Herkunft: Taxodia-Session, inline im Session-Transkript (15.09.2026, kein eigenes Skript)
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HIER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)

# ── ANPASSEN je Charge ─────────────────────────────
# keine eigenen Werte: Clips und Framerate kommen aus feinschnitt_bauen.py (fb.lade, fb.plan, fb.FPS)
# ── Ende ANPASSEN ──────────────────────────────────


def main() -> None:
    t, shots = fb.lade()
    p, _ = fb.plan(t, shots)
    clips: dict[str, list] = {}
    for it in p["V1"] + p["V2_voll"]:
        clips.setdefault(it.clip, []).append(it)
    out = {}
    for clip, items in clips.items():
        mitten = sorted({(i.src_in_f + i.src_out_f) / 2 / fb.FPS for i in items})
        out[clip] = [round(mitten[round(q * (len(mitten) - 1) / 3)], 3) for q in range(4)]
    (HIER / "proben.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1)[:600])


if __name__ == "__main__":
    main()
