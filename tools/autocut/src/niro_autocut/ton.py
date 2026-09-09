"""True-Peak-Messung je A1-Item (ffmpeg ebur128), Gain auf das Ziel in dBTP, ton.json (Spec v2 Abschnitt 1).

Gemessen wird das Original im Schnittbereich inklusive Handles (src_in_f..src_out_f), Ergebnis in dBFS
(True Peak, Maximum beider Kanäle). gain_db = ziel_dbtp − tpk, begrenzt auf max_gain_db; Stille → 0 dB.
Cache je (Pfad, src_in_f, src_out_f) in <Charge>/_intern/autocut/work/ton_cache.json.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

from .charge import AutoCutError
from .media import _which
from .timeline_model import Item

_TPK_RE = re.compile(r"True peak:\s*\n\s*Peak:\s*(-?[0-9.]+|-inf)\s*dBFS", re.IGNORECASE)


def parse_true_peak(text: str) -> float | None:
    """„True peak: / Peak: −15.2 dBFS" aus der ebur128-Zusammenfassung; None, wenn nicht vorhanden."""
    m = _TPK_RE.search(text or "")
    if not m:
        return None
    v = m.group(1)
    return -math.inf if v == "-inf" else float(v)


def measure_true_peak(path: str | Path, in_s: float, dur_s: float) -> float:
    """True Peak (dBFS) des ersten Audiostreams im Bereich [in_s, in_s + dur_s) — lesend, keine Ausgabedatei."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {p}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-hide_banner", "-nostats", "-ss", f"{max(0.0, in_s):.3f}", "-t", f"{max(0.04, dur_s):.3f}",
           "-i", str(p), "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise AutoCutError(f"Pegelmessung fehlgeschlagen für {p.name}: {r.stderr[-300:]}")
    tpk = parse_true_peak(r.stderr)
    if tpk is None:
        raise AutoCutError(f"Pegelmessung ohne True-Peak-Wert für {p.name} (ffmpeg ohne ebur128?): {r.stderr[-200:]}")
    return tpk


def db_to_lin(db: float) -> float:
    return 10.0 ** (float(db) / 20.0)


def lin_to_db(lin: float) -> float:
    return 20.0 * math.log10(max(float(lin), 1e-12))


def gain_db_for(tpk_dbfs: float, cfg_ton: dict) -> tuple[float, str]:
    """Gain in dB auf ziel_dbtp; begrenzt auf max_gain_db; Warnung bei Clipping-Verdacht oder Stille."""
    ziel = float(cfg_ton["ziel_dbtp"])
    max_gain = float(cfg_ton["max_gain_db"])
    if tpk_dbfs is None or tpk_dbfs < float(cfg_ton["silence_dbtp"]):
        return 0.0, f"Stille (True Peak {tpk_dbfs} dBFS) — Gain bleibt 0 dB."
    gain = round(ziel - float(tpk_dbfs), 2)
    warn = ""
    if tpk_dbfs > float(cfg_ton["clip_warn_dbtp"]):
        warn = f"Clipping-Verdacht: True Peak {tpk_dbfs:.1f} dBFS im Original."
    if gain > max_gain:
        warn = (warn + " " if warn else "") + f"Gain {gain:.1f} dB auf {max_gain:.0f} dB begrenzt (Resolve-Maximum)."
        gain = max_gain
    return gain, warn


def _key(it: Item) -> str:
    return f"{it.clip}|{int(it.src_in_f)}|{int(it.src_out_f)}"


def measure_a1_items(items: list[Item], fps: float, cfg_ton: dict, cache: dict, measure=measure_true_peak,
                      map_path=None) -> list[dict]:
    """Je A1-Item (Reihenfolge der Timeline) True Peak aus dem Cache oder per ``measure``; liefert die ton.json-Einträge.

    Nicht endliche oder extrem niedrige Messwerte (digitale Stille, z. B. ``-math.inf``) werden auf
    ``-120.0`` dBFS gekappt — sowohl im Cache-Eintrag als auch im zurückgegebenen Eintrag —, damit
    ``json.dumps`` kein nicht-standardkonformes ``-Infinity`` schreibt. Die „Stille"-Regel in
    ``gain_db_for`` greift trotzdem, da ``-120.0`` unter jedem sinnvollen ``silence_dbtp`` liegt.
    """
    out: list[dict] = []
    for it in sorted((i for i in items if i.track == "A1"), key=lambda i: i.rec_in_f):
        k = _key(it)
        rec = cache.get(k)
        if not rec or rec.get("tpk_dbfs") is None:
            in_s, dur_s = it.src_in_f / fps, (it.src_out_f - it.src_in_f) / fps
            src = map_path(it.clip) if map_path else it.clip
            rec = {"tpk_dbfs": measure(src, round(in_s, 3), round(dur_s, 3))}
            cache[k] = rec
        tpk = rec["tpk_dbfs"]
        if tpk is not None and (not math.isfinite(tpk) or tpk < -120.0):
            tpk = -120.0
            rec["tpk_dbfs"] = tpk
        gain_db, warn = gain_db_for(tpk, cfg_ton)
        out.append({"clip": it.clip, "name": Path(it.clip).name, "src_in_f": int(it.src_in_f), "src_out_f": int(it.src_out_f),
                    "rec_in_f": int(it.rec_in_f), "dauer_f": int(it.rec_out_f - it.rec_in_f),
                    "tpk_dbfs": tpk, "gain_db": gain_db, "gain_lin": round(db_to_lin(gain_db), 5),
                    "warnung": warn})
    return out


def build_ton(charge, tp_dict: dict, cfg_ton: dict, measure=measure_true_peak) -> dict:
    """ton.json für den Timeline-Plan schreiben (A1-Items); Cache unter work/ton_cache.json.

    Der Cache wird auch dann geschrieben, wenn die Messschleife für ein Item scheitert (NAS-Aussetzer,
    ffmpeg-Fehler) — bereits gemessene Items gehen so nicht verloren. Der Fehler wird danach weitergereicht.
    """
    fps = float(tp_dict["fps"])
    items = [Item.from_dict(d) for d in (tp_dict.get("items") or [])]
    cache_file = charge.work / "ton_cache.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    charge.assert_writable(cache_file)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        entries = measure_a1_items(items, fps, cfg_ton, cache, measure, map_path=charge.map_path)
    finally:
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {"ziel_dbtp": float(cfg_ton["ziel_dbtp"]), "max_gain_db": float(cfg_ton["max_gain_db"]),
           "anzahl": len(entries), "warnungen": [f"{e['name']} {e['src_in_f']}–{e['src_out_f']}: {e['warnung']}"
                                                  for e in entries if e["warnung"]], "items": entries}
    charge.write_json("ton.json", out)
    return out
