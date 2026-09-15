"""Vorlage (Stand 15.09.2026): Farbmanagement des Resolve-Projekts und Grade-Zustand der Timeline-Clips nur lesen (vor dem Grading).

Aufruf: tools/autocut/venv/bin/python _intern/color/skripte/grade_check.py > _intern/color/grade_check.out
Liest (schreibt nichts, wechselt keine Seite): Projektname, aktive Timeline, aktuelle Seite (ExportLUT in grading_anwenden.py
klappt nur auf „color"), Projekt-Einstellungen colorScienceMode, colorSpaceTimeline/-Output/-Input, videoDataLevels, DRTs …,
useCustomSettings der Timeline und je Clipname (erstes Item auf V1–V3) Data Level, Input Color Space, Gamma, Input LUT
(Media-Pool-Clip), Node-Anzahl, LUT in Node 1, aktive Farbversion und die lokalen/entfernten Versionsnamen.
Befund 15.09. (Referenz): colorScienceMode davinciYRGBColorManagedv2, Timeline und Input Rec.709 (Scene), Output Rec.709-A,
SDR 100, videoDataLevels Video, isAutoColorManage 0; Clips Data Level „Auto", Input Color Space „Project", 1 Node ohne LUT,
„Version 1" (lokal und entfernt) → Clips gehen unkonvertiert als S-Log3 in den Node, der CDL-Vorschlag gilt so.
Weicht das ab (anderer Input Color Space, Data Level „Video"/„Full", ACES), erst klären — Einstellungen nie per Skript ändern.
Herkunft: Taxodia-Session, Scratchpad grade_check.py
"""
import sys, json
from pathlib import Path

# ── ANPASSEN je Charge ─────────────────────────────
NAME = "<Timeline-Name>"  # Name der zu gradenden Feinschnitt-Timeline im geöffneten Projekt (exakt)
# ── Ende ANPASSEN ──────────────────────────────────

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA
r = RA.connect(); pm = r.GetProjectManager(); p = pm.GetCurrentProject()
out = {"projekt": p.GetName(), "aktiv": p.GetCurrentTimeline().GetName(), "seite": r.GetCurrentPage()}
for k in ("colorScienceMode", "colorSpaceTimeline", "colorSpaceOutput", "colorSpaceInput", "separateColorSpaceAndGamma",
          "colorVersion10Using709Primaries", "timelineWorkingLuminanceMode", "videoDataLevels", "inputDRT", "outputDRT",
          "isAutoColorManage", "useColorSpaceAwareGradingToolsForRCM"):
    out[k] = p.GetSetting(k)
tl = next(t for t in (p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)) if t and t.GetName() == NAME)
out["timeline_customsettings"] = tl.GetSetting("useCustomSettings")
s = tl.GetStartFrame()
proben = {}
for kind_idx in (1, 2, 3):
    for x in (tl.GetItemListInTrack("video", kind_idx) or []):
        key = x.GetName()
        if key in proben:
            continue
        mpi = x.GetMediaPoolItem()
        g = x.GetNodeGraph()
        proben[key] = {"spur": f"V{kind_idx}", "start": x.GetStart() - s,
                       "data_level": mpi.GetClipProperty("Data Level"), "input_color_space": mpi.GetClipProperty("Input Color Space"),
                       "gamma": mpi.GetClipProperty("Gamma"), "input_lut": mpi.GetClipProperty("Input LUT"),
                       "nodes": g.GetNumNodes() if g else None, "lut1": g.GetLUT(1) if g else None,
                       "version": x.GetCurrentVersion(), "versionen_lokal": x.GetVersionNameList(0), "versionen_remote": x.GetVersionNameList(1)}
out["clips"] = proben
luts = r.GetCurrentPage()
print(json.dumps(out, ensure_ascii=False, indent=1))
