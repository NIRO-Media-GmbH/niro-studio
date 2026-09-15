"""Vorlage (Stand 15.09.2026): kurzer Ton-Render der Feinschnitt-Timeline aus Resolve — prüft, ob die SFX-Spuren wirklich klingen.

Aufruf: tools/autocut/venv/bin/python _intern/sfx/sfx_ton_render.py <von_frame> <bis_frame> [--ausfuehren]
  Frames ab Timeline-Start (0 = erstes Frame). Bereich so wählen, dass mindestens ein SFX ohne Sprache und Musik darin liegt
  (sprachfreie Platzierungen: analyse/mischung_sfx.json → zusammenfassung.abstand_bett_minus_sfx_lu_sprachfrei).
Warum: Die Bus-Zuweisung einer Spur ist per API nicht lesbar; per AddTrack nachträglich angelegte Tonspuren sind ohne Bus-Ausgang
stumm (Messung 15.09.: Render −180 dB, obwohl Spur aktiviert, Clip online und Audio-Mapping nicht stumm). Nur ein Render deckt das auf.
Voraussetzungen: Projekt = Freigabe feinschnitt_bauen.PROJEKT, TIMELINE aus sfx_einsetzen.py ist die aktive Timeline (das Skript
wechselt die Timeline des Users nicht), kein laufender Render. Ohne --ausfuehren nur diese Prüfung.
Ablauf mit --ausfuehren: Deliver-Einstellungen als Preset „Claude Sicherung Deliver <Zeitstempel>“ sichern (sonst Abbruch) →
SetRenderSettings (MarkIn/MarkOut, nur Audio, 48 kHz/24 Bit, TargetDir _intern/sfx/rendertest, CustomName ton_<von>_<bis>) →
AddRenderJob → StartRendering → auf GetRenderJobStatus Complete/Failed/Cancelled warten (max. 180 s; nicht IsRenderingInProgress —
direkt nach dem Start noch False) → eigenen Job löschen, Preset laden und löschen (auch bei Fehler).
Auswertung: je SFX-Platzierung aus sfx_plan.json (+ versatz aus sfx_einsatz.json) im Bereich der Render-Peak im SFX-Fenster;
≤ STILLE_DBFS = digitale Stille → Spur ohne Bus-Ausgang: User weist in Resolve zu (Fairlight → Bus Assign → Main 1), dann erneut
rendern. Aussagekräftig sind nur Fenster ohne Sprache und Musik.
Schreibt rendertest/ton_<von>_<bis>.<Container der Deliver-Einstellung> und rendertest/ton_<von>_<bis>.json (projekt, timeline, von,
bis, status, datei, fenster [spur, rec_frame, element, sfx, render_peak_dbfs, stille]).
Herkunft: Taxodia-Charge, Session-Scratchpad ton_rendertest.py + sfx_isolationstest_render.py (Render-Schritt)
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

STUDIO = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "autocut" / "src").is_dir())
sys.path.insert(0, str(STUDIO / "tools" / "autocut" / "src"))
from niro_autocut import resolve_api as RA  # noqa: E402

# ── ANPASSEN je Charge ─────────────────────────────
# (keine eigenen Werte: Projekt aus feinschnitt_bauen.PROJEKT, Timeline aus sfx_einsetzen.TIMELINE, Bereich per Aufruf)
# ── Ende ANPASSEN ──────────────────────────────────

sys.dont_write_bytecode = True
HIER = Path(__file__).resolve().parent
ZIEL = HIER / "rendertest"
SR, SPF = 48000, 1920
STILLE_DBFS = -90.0  # Render-Peak im SFX-Fenster darunter = digitale Stille (stumme Spur: −180 dB)

spec = importlib.util.spec_from_file_location("se", HIER / "sfx_einsetzen.py")
se = importlib.util.module_from_spec(spec)
spec.loader.exec_module(se)
fb = se.fb


def rendern(p, st: int, von: int, bis: int, name: str) -> tuple[dict, Path | None]:
    """Ton-Render von–bis; Deliver-Einstellungen vorher gesichert und danach wiederhergestellt. Rückgabe (Job-Status, Datei)."""
    preset = f"Claude Sicherung Deliver {dt.datetime.now():%Y-%m-%d %H%M%S}"
    vorher = p.GetCurrentRenderFormatAndCodec()
    if not p.SaveAsNewRenderPreset(preset):
        raise SystemExit("Deliver-Einstellungen nicht gesichert — nichts verändert.")
    print("Deliver-Einstellungen gesichert:", preset, vorher)
    job, stt, datei = None, {}, None
    try:
        ok = p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": st + von, "MarkOut": st + bis, "TargetDir": str(ZIEL),
                                  "CustomName": name, "ExportVideo": False, "ExportAudio": True, "AudioSampleRate": 48000,
                                  "AudioBitDepth": 24})
        print("Einstellungen gesetzt:", ok)
        job = p.AddRenderJob()
        print("Job:", job)
        if job:
            print("StartRendering:", p.StartRendering([job], False))
            t0 = time.time()
            while time.time() - t0 < 180:
                time.sleep(1.0)
                stt = p.GetRenderJobStatus(job) or {}
                if stt.get("JobStatus") in ("Complete", "Failed", "Cancelled"):
                    break
            print("Status:", stt, f"{time.time() - t0:.1f} s")
            info = next((j for j in (p.GetRenderJobList() or []) if j.get("JobId") == job), {})
            if info.get("OutputFilename"):
                datei = Path(info.get("TargetDir") or ZIEL) / info["OutputFilename"]
    finally:
        if job:
            print("eigenen Job gelöscht:", p.DeleteRenderJob(job))
        print("Einstellungen zurück:", p.LoadRenderPreset(preset), p.GetCurrentRenderFormatAndCodec(),
              "| Preset gelöscht:", p.DeleteRenderPreset(preset))
    if datei is None or not datei.exists():
        datei = next((d for d in sorted(ZIEL.glob(f"{name}.*")) if d.suffix != ".json"), None)
    return stt, datei


def fenster_messen(datei: Path, von: int, bis: int) -> list[dict]:
    """Render-Peak je SFX-Platzierung im Bereich (Sample 0 des Renders = Timeline-Frame von)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(datei), "-map", "0:a:0", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    x = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
    plan = json.loads((HIER / "sfx_plan.json").read_text())
    platz = plan["platzierungen"] if isinstance(plan, dict) else plan
    einsatz = HIER / "sfx_einsatz.json"
    versatz = json.loads(einsatz.read_text()).get("versatz", {}) if einsatz.exists() else {}
    zeilen = []
    for pl in platz:
        f0 = int(pl["rec_frame"]) + int(versatz.get(pl["element"], 0))
        a, b = max(f0, von), min(f0 + int(pl["dauer_frames"]), bis)
        if b <= a:
            continue
        seg = x[(a - von) * SPF:(b - von) * SPF]
        pk = round(float(20 * np.log10(np.abs(seg).max() + 1e-12)), 1) if len(seg) else None
        zeilen.append({"spur": pl["spur"], "rec_frame": f0, "element": pl["element"], "sfx": pl["sfx_name"],
                       "render_peak_dbfs": pk, "stille": None if pk is None else pk <= STILLE_DBFS})
    return zeilen


def main() -> None:
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(argumente) != 2:
        raise SystemExit("Aufruf: sfx_ton_render.py <von_frame> <bis_frame> [--ausfuehren]")
    von, bis = int(argumente[0]), int(argumente[1])
    if not 0 <= von < bis:
        raise SystemExit("Bereich ungültig: 0 ≤ von < bis (Timeline-Frames ab 0).")
    r = RA.connect()
    p = r.GetProjectManager().GetCurrentProject()
    if p is None or p.GetName() != fb.PROJEKT:
        raise SystemExit(f"Offenes Projekt '{p.GetName() if p else None}' ≠ Freigabe '{fb.PROJEKT}' — nichts gerendert.")
    tl = p.GetCurrentTimeline()
    if tl is None or tl.GetName() != se.TIMELINE:
        raise SystemExit(f"Aktive Timeline '{tl.GetName() if tl else None}' ≠ '{se.TIMELINE}' — in Resolve aktivieren "
                         f"(das Skript wechselt die Timeline des Users nicht).")
    if p.IsRenderingInProgress():
        raise SystemExit("Es rendert gerade — nichts gestartet.")
    name = f"ton_{von:05d}_{bis:05d}"
    print(f"Projekt {p.GetName()} | Timeline {tl.GetName()} | Bereich {von}–{bis} ({(bis - von) / 25:.1f} s) → {ZIEL / name}.*")
    if "--ausfuehren" not in sys.argv:
        return
    ZIEL.mkdir(parents=True, exist_ok=True)
    stt, datei = rendern(p, int(tl.GetStartFrame()), von, bis, name)
    out = {"projekt": p.GetName(), "timeline": tl.GetName(), "von": von, "bis": bis, "status": stt,
           "datei": str(datei) if datei else None}
    if datei is not None and stt.get("JobStatus") == "Complete":
        out["fenster"] = fenster_messen(datei, von, bis)
        still = [z for z in out["fenster"] if z["stille"] is True]
        print(f"{len(out['fenster'])} SFX-Fenster im Bereich, digital still: {len(still)}")
        for z in out["fenster"]:
            print(f"  {z['spur']} @{z['rec_frame']} {z['element'][:22]:22s} {z['sfx'][:30]:30s} "
                  f"Render-Peak {z['render_peak_dbfs']} dBFS{'  STILLE' if z['stille'] else ''}")
    (ZIEL / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
