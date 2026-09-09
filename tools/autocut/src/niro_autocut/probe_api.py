"""Auswertung der Live-Probe der Scripting-API 21.1 (Spec „Grundlage Resolve 21.1", Abschnitt 2.3/2.4).

Reine Funktionen ohne Resolve: Erwartungswerte, Toleranzen, Klassifikation der Befunde. Das Skript
scripts/resolve_probe_api.py ruft Resolve und reicht die Rohwerte hierher.
"""
from __future__ import annotations

ZIEL_DBTP = -3.0
VOLUME_SOLL_DB = 9.0
FADES_SOLL = {"FadeIn": 3, "FadeOut": 5}
FADES_INAKTIV_SOLL = {"FadeIn": 2, "FadeOut": 2}
TRANSITION_SOLL = {"type": "Cross Dissolve", "category": "simple", "position": "start", "alignment": "center",
                   "duration": 12}
ALIGN_SOLL_FRAMES = -50     # V2-Bursts liegen 50 Frames später → der relative Versatz V2−V1 muss um 50 sinken
PFLICHT = ("volume", "speed", "fades")
MESSUNGEN = ("volume", "normalize", "speed", "fades", "transition", "autoalign", "inactive", "quickexport", "alpha_import")


def expected_gain_db(tpk_dbfs: float, ziel_dbtp: float = ZIEL_DBTP) -> float:
    return round(float(ziel_dbtp) - float(tpk_dbfs), 3)


def eval_volume(set_returned: bool, ist, enabled) -> dict:
    ok = bool(set_returned) and ist is not None and abs(float(ist) - VOLUME_SOLL_DB) <= 0.05 and bool(enabled)
    return {"ok": ok, "soll": VOLUME_SOLL_DB, "ist": ist, "enabled": bool(enabled), "set_returned": bool(set_returned)}


def eval_normalize(set_returned: bool, ist, tpk_dbfs: float, modi: list, ziel_dbtp: float = ZIEL_DBTP,
                   tol_db: float = 0.5) -> dict:
    soll = expected_gain_db(tpk_dbfs, ziel_dbtp)
    diff = None if ist is None else round(float(ist) - soll, 3)
    ok = bool(set_returned) and diff is not None and abs(diff) <= tol_db
    return {"ok": ok, "modi": list(modi), "tpk_ffmpeg": tpk_dbfs, "soll": soll, "ist": ist, "diff": diff,
            "set_returned": bool(set_returned)}


def classify_speed_gap(dur_before: int, dur_after: int) -> str:
    """50 % Tempo vor einer Lücke: verdoppelt sich die Timeline-Dauer, bleibt sie, oder etwas dazwischen?"""
    if int(dur_after) >= 2 * int(dur_before) - 1:
        return "verlängert"
    if int(dur_after) == int(dur_before):
        return "behält_dauer"
    return "teilweise"


def classify_ripple(next_start_before: int, next_start_after: int, delta_expected: int) -> str:
    d = int(next_start_after) - int(next_start_before)
    if abs(d - int(delta_expected)) <= 1:
        return "verschiebt"
    if d == 0:
        return "bleibt"
    return f"anders ({d:+d})"


def source_kept(src_before: tuple, src_after: tuple) -> bool:
    """Quellbereich (GetSourceStartFrame/EndFrame) unverändert (±1 Frame, GetSourceEndFrame ist nicht frame-exakt)."""
    before = int(src_before[1]) - int(src_before[0])
    after = int(src_after[1]) - int(src_after[0])
    return abs(after - before) <= 1


def speed_percent_ok(speed, soll: float = 50.0) -> bool:
    try:
        return abs(float((speed or {}).get("Percentage")) - soll) <= 0.01
    except (TypeError, ValueError, AttributeError):
        return False


def fades_match(soll: dict, ist) -> bool:
    if not isinstance(ist, dict):
        return False
    try:
        return all(int(round(float(ist.get(k)))) == int(v) for k, v in soll.items())
    except (TypeError, ValueError):
        return False


def classify_align(v1_before: int, v1_after: int, v2_before: int, v2_after: int) -> dict:
    d1, d2 = int(v1_after) - int(v1_before), int(v2_after) - int(v2_before)
    if not d1 and not d2:
        moved = "keiner"
    elif d1 and not d2:
        moved = "V1"
    elif d2 and not d1:
        moved = "V2"
    else:
        moved = "beide"
    delta = d2 - d1
    return {"moved": moved, "delta_frames": delta, "ok": abs(delta - ALIGN_SOLL_FRAMES) <= 1}


def overall_ok(res: dict) -> bool:
    return all(bool((res.get(k) or {}).get("ok")) for k in PFLICHT)


def summary_lines(res: dict) -> list[str]:
    extra = {
        "speed": lambda v: f" gap={v.get('gap')} ripple={v.get('ripple')} source_kept={v.get('source_kept')}",
        "normalize": lambda v: f" soll={v.get('soll')} ist={v.get('ist')} diff={v.get('diff')}",
        "autoalign": lambda v: f" moved={v.get('moved')} delta={v.get('delta_frames')}",
        "quickexport": lambda v: f" status={v.get('status')} wand={v.get('wanddauer_s')}s",
        "inactive": lambda v: f" fades_on_inactive_ok={v.get('fades_on_inactive_ok')}",
        "alpha_import": lambda v: f" alpha_mode={v.get('alpha_mode')}",
    }
    lines = []
    for k in MESSUNGEN:
        v = res.get(k) or {}
        if "uebersprungen" in v:
            lines.append(f"  {k}: übersprungen — {v['uebersprungen']}")
        elif not v:
            lines.append(f"  {k}: FEHLT")
        else:
            lines.append(f"  {k}: {'ok' if v.get('ok') else 'nicht ok'}{extra.get(k, lambda v: '')(v)}")
    lines.append(f"  ok (Pflicht {', '.join(PFLICHT)}): {overall_ok(res)}")
    return lines
