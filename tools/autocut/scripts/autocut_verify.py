"""Cutlist hart prüfen (Spec 3.4) — Pflicht vor autocut_build.py.

Aufruf:
    venv/bin/python scripts/autocut_verify.py "<Charge>"

Liest  <Charge>/_intern/autocut/cutlist.json, media.json (optional), sync.json (optional),
       Transkript-Index + Cache der Charge; Clip-Dateien und Proxys nur per Existenz-Test.
Schreibt <Charge>/_intern/autocut/verify.json  {"cutlist_hash", "ok", "errors", "warnings", …}.
Exit 0 = OK (Warnungen erlaubt), Exit 1 = Fehler (Cutlist korrigieren und erneut prüfen).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.cutlist import Cutlist, cutlist_hash, total_length_s, verify_cutlist  # noqa: E402


def _mmss(s: float) -> str:
    m, sec = divmod(int(round(s)), 60)
    return f"{m:02d}:{sec:02d}"


def collect_inputs(ch: Charge, cl: Cutlist) -> tuple[dict[str, list[dict]], dict[str, float]]:
    """Wörter und Dauern je Clip-Pfad aus Index + Cache; Dauer aus media.json, sonst Index, sonst ffprobe."""
    media = ch.read_json("media.json") or {}
    clips = media.get("clips") or {}
    used = {b.clip for b in cl.beats if b.clip} | {s.clip for s in cl.sperren}
    words: dict[str, list[dict]] = {}
    durations: dict[str, float] = {}
    for rec in ch.load_index():
        path = rec["path"]
        cached = ch.cache_transcript(rec["fingerprint"])
        if cached and cached.get("words") is not None:
            words[path] = cached["words"]
        dur = None
        m = clips.get(path)
        if m and m.get("original"):
            dur = m["original"].get("duration_s")
        if dur is None:
            dur = rec.get("duration_s")
        if dur is None and path in used:
            mapped = ch.map_path(path)
            if Path(mapped).is_file():
                from niro_autocut.media import ffprobe
                dur = ffprobe(mapped).duration_s
        if dur is not None:
            durations[path] = float(dur)
    return words, durations


def main() -> None:
    ap = argparse.ArgumentParser(description="Cutlist hart prüfen; schreibt verify.json in _intern/autocut.")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    a = ap.parse_args()

    ch = Charge.open(a.charge)
    cpath = ch.autocut / "cutlist.json"
    if not cpath.exists():
        raise AutoCutError(f"{cpath} fehlt — Cutlist zuerst nach prompts/cutlist.md erstellen.")
    cl = Cutlist.load(cpath)
    words, durations = collect_inputs(ch, cl)
    sync = ch.read_json("sync.json")
    res = verify_cutlist(cl, ch, words, durations, ch.config, sync=sync)
    if sync is None:
        res.warnings.append("sync.json fehlt — a7-Abdeckung nicht geprüft (erst autocut_sync.py laufen lassen, "
                            "sonst bleibt V2 leer).")

    for h in cl.hinweise:
        print("HINWEIS:", h)
    for e in res.errors:
        print("FEHLER:", e)
    for w in res.warnings:
        print("WARNUNG:", w)

    typen = Counter(b.typ for b in cl.beats)
    total = total_length_s(cl, ch.config)
    ziel = f" (Ziel {_mmss(cl.ziel_laenge_s)})" if cl.ziel_laenge_s else ""
    print(f"Cutlist {cl.video}: {len(cl.beats)} Beats ("
          + ", ".join(f"{t} {n}" for t, n in sorted(typen.items())) + f"), {len(cl.sperren)} Sperren, "
          f"Gesamtlänge {_mmss(total)}{ziel}")
    ch.write_json("verify.json", {
        "cutlist_hash": cutlist_hash(cpath), "ok": res.ok, "errors": res.errors, "warnings": res.warnings,
        "video": cl.video, "geprueft_am": _dt.datetime.now().isoformat(timespec="seconds"),
        "n_beats": len(cl.beats), "gesamtlaenge_s": round(total, 2), "ziel_laenge_s": cl.ziel_laenge_s,
        "hinweise": list(cl.hinweise)})
    print(f"{'OK' if res.ok else 'NICHT OK'} — {len(res.errors)} Fehler, {len(res.warnings)} Warnungen "
          f"→ {ch.autocut / 'verify.json'}")
    sys.exit(0 if res.ok else 1)


if __name__ == "__main__":
    try:
        main()
    except AutoCutError as e:
        sys.exit(f"FEHLER: {e}")
