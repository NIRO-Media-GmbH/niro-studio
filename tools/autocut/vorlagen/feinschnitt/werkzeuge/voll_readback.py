"""Vorlage (Stand 15.09.2026): Voll-Readback der Feinschnitt-Timeline gegen den Plan aus feinschnitt_bauen.py.

Aufruf:  tools/autocut/venv/bin/python _intern/werkzeuge/voll_readback.py
Liest    _intern/feinschnitt_bauen.py per importlib (lade(), plan(tl, shots) → Spuren "V1"–"V4", "A1"; MUSIK_PLAN mit
         (Spur, Datei, Quell-In, Record-In, Record-Out, …)) und die Timeline NAME in Resolve.
Ausgabe: Fehler im Plan; je Spur V1–V4 und A1–A3 Anzahl Items und ob die Positionen (Record-Start, Dauer) exakt dem Plan
         entsprechen; Musik-Quell-In (Left-Offset) = Plan; Anzahl Marker, Timeline-Ende, Voice Isolation A1, aktive Timeline;
         V3-Tempo (Items mit 50 % bzw. 100 %).
Nur lesend (keine Projektprüfung). Positionen ab Timeline-Start; Quell-In per GetLeftOffset (nicht GetSourceStartFrame).

Herkunft: Taxodia-Charge, Session-Scratchpad voll_readback.py
"""
import sys, json, importlib.util
from pathlib import Path

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

HIER = Path(__file__).resolve().parent

# ── ANPASSEN je Charge ─────────────────────────────
NAME = "<Timeline-Name>"  # exakter Name der Feinschnitt-Timeline (von feinschnitt_bauen.py angelegt)
# ── Ende ANPASSEN ──────────────────────────────────

spec = importlib.util.spec_from_file_location("fb", HIER.parent / "feinschnitt_bauen.py")
fb = importlib.util.module_from_spec(spec); spec.loader.exec_module(fb)
tlj, shots = fb.lade(); p, fehler = fb.plan(tlj, shots)
r = RA.connect(); pr = r.GetProjectManager().GetCurrentProject()
tl = next(t for t in (pr.GetTimelineByIndex(i) for i in range(1, pr.GetTimelineCount() + 1)) if t and t.GetName() == NAME)
s = tl.GetStartFrame()
ist = {}
for kind, n in (("video", 4), ("audio", 3)):
    for i in range(1, n + 1):
        ist[f"{kind[0].upper()}{i}"] = sorted((x.GetStart() - s, x.GetDuration(), x.GetLeftOffset()) for x in (tl.GetItemListInTrack(kind, i) or []))
soll = {k: sorted((it.rec_in_f, it.rec_out_f - it.rec_in_f) for it in p[k]) for k in ("V1", "V2", "V3", "V4", "A1")}
for spur in ("A2", "A3"):
    soll[spur] = sorted((ri, ro - ri) for sp, d, si, ri, ro, *_ in fb.MUSIK_PLAN if sp == spur)
print("Fehler im Plan:", fehler)
for k in ist:
    print(k, len(ist[k]), "Positionen = Plan:", [(a, d) for a, d, _ in ist[k]] == soll[k])
musik_src = {(sp, ri): si for sp, d, si, ri, ro, *_ in fb.MUSIK_PLAN}
print("Musik-Quell-In = Plan:", all(musik_src[(k, a)] == o for k in ("A2", "A3") for a, d, o in ist[k]))
print("Marker:", len(tl.GetMarkers() or {}), "| Ende:", tl.GetEndFrame() - s, "| VI:", tl.GetVoiceIsolationState(1), "| aktiv:", pr.GetCurrentTimeline().GetName())
sp = [x.GetSpeed().get("Percentage") for x in sorted(tl.GetItemListInTrack("video", 3), key=lambda y: y.GetStart())]
print("V3 50 %:", sum(1 for v in sp if abs(v - 50) < 0.1), "| 100 %:", sum(1 for v in sp if abs(v - 100) < 0.1))
