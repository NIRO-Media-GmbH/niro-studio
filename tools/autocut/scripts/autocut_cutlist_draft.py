"""Cutlist-Entwurf aus dem Cutter-Plan erzeugen — Startpunkt für prompts/cutlist.md.

Aufruf:
    venv/bin/python scripts/autocut_cutlist_draft.py "<Charge>" [--video video-1-x.md] [--force]

Liest  Plan (Ergebnisse/O-Ton-Pläne/video-N-*.md), Transkript-Index + Cache, utterances.json,
       media.json (Bildrate/Format; fehlt sie: ffprobe des ersten O-Ton-Clips, sonst 25 fps + Hinweis).
Schreibt <Charge>/_intern/autocut/cutlist.json — nur wenn noch keine da ist (sonst --force).
Der Entwurf ist NICHT geprüft: danach jeden Beat gegen den Plan lesen, offene Punkte erledigen,
autocut_verify.py laufen lassen. Exit 0 auch bei offenen Punkten (die Liste steht in der Ausgabe).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from niro_autocut.charge import AutoCutError, Charge  # noqa: E402
from niro_autocut.cutlist import draft_from_plan  # noqa: E402
from niro_autocut.plan import parse_plan  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Cutlist-Entwurf aus dem Cutter-Plan schreiben (ungeprüft).")
    ap.add_argument("charge", help="Chargen-Ordner (projects/<Kunde>/<Projekt>/<Charge>)")
    ap.add_argument("--video", help="Plan-Datei, wenn mehrere video-*.md vorhanden sind")
    ap.add_argument("--force", action="store_true", help="vorhandene cutlist.json überschreiben")
    a = ap.parse_args()

    ch = Charge.open(a.charge)
    target = ch.autocut / "cutlist.json"
    if target.exists() and not a.force:
        raise AutoCutError(f"{target} existiert bereits — mit --force überschreiben oder die Datei direkt bearbeiten.")
    plan = parse_plan(ch.resolve_plan(a.video))
    index = ch.load_index()
    words = {}
    durations = {}
    media = ch.read_json("media.json") or {}
    clips = media.get("clips") or {}
    for rec in index:
        cached = ch.cache_transcript(rec["fingerprint"])
        if cached and cached.get("words"):
            words[rec["path"]] = cached["words"]
        m = clips.get(rec["path"])
        dur = (m or {}).get("original", {}).get("duration_s") if m else None
        if dur is None:
            dur = rec.get("duration_s")
        if dur is not None:
            durations[rec["path"]] = float(dur)

    offen_kopf: list[str] = []
    fmt_info = media.get("format") or {}
    fps = fmt_info.get("fps")
    fmt = fmt_info.get("orientation")
    if not fps:
        first = next((r["path"] for r in index if r.get("kamera_rolle", "ton") == "ton" and Path(r["path"]).is_file()), None)
        if first:
            from niro_autocut.media import ffprobe, timeline_format
            tf = timeline_format(ffprobe(first))
            fps, fmt = tf["fps"], fmt or tf["orientation"]
        else:
            fps = 25.0
            offen_kopf.append("Bildrate nicht aus media.json/ffprobe ermittelbar — fps=25 angenommen, "
                              "nach autocut_prepare.py prüfen.")
    if not fmt:
        fmt = plan.format_hint or "16:9"
    if plan.format_hint and fmt != plan.format_hint:
        offen_kopf.append(f"Plan verlangt {plan.format_hint}, Material ist {fmt} — Material gilt, im Bericht nennen.")

    cl, offen = draft_from_plan(plan, index, words, durations, ch.config, float(fps), fmt, ch.load_utterances())
    ch.assert_writable(target)
    cl.save(target)
    offen = offen_kopf + offen
    n_cuts = sum(len(b.cuts) for b in cl.beats)
    n_oton = sum(1 for b in cl.beats if b.typ == "oton")
    n_fertig = sum(1 for b in cl.beats if b.typ == "oton" and b.cuts)
    print(f"Entwurf geschrieben: {target}")
    print(f"{len(cl.beats)} Beats aus {Path(plan.file).name}; O-Töne {n_fertig}/{n_oton} aufgelöst ({n_cuts} Cuts); "
          f"{len(cl.sperren)} Sperren; {len(cl.hinweise)} Hinweise")
    for h in cl.hinweise:
        print("HINWEIS:", h)
    for o in offen:
        print("OFFEN:", o)
    print("Nächster Schritt: jeden Beat gegen den Plan lesen (prompts/cutlist.md), dann "
          f"venv/bin/python scripts/autocut_verify.py \"{ch.root}\"")


if __name__ == "__main__":
    try:
        main()
    except AutoCutError as e:
        sys.exit(f"FEHLER: {e}")
