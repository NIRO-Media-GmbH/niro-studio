"""Setzer — Social-Reels, Dreh 18./19.08.2026 (iPhone, hochkant 9:16).

Kein Konzept vorhanden: der Schnittplan wird aus dem Material selbst gebaut.
Deshalb wird ALLES mit Sprache transkribiert — inkl. der Clips aus
"00 Discarded", weil dort Alternativ-Takes zum selben Thema liegen
(Nummernkreis 4874–4899 verzahnt sich mit Ordner 01).

Umfang dieses Laufs: Video 01 (Fleischkäse vs. Leberkäse) + Discarded-Takes
im selben Nummernkreis + freistehende Hook-/Schluss-Clips.

Originale auf der SSD werden NUR GELESEN.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

for line in (TOOL / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip, find_sidecar
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip

ROH = Path(
    "/Volumes/NIRO-SSD-03/Setzer/03_Dreh 2026.08.18/Rohmaterial iPhone"
)
PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Setzer/Social-Reels/2026-08 Dreh 18.08"
)

# Discarded-Takes, deren Nummer in den Dreh-Block von Video 01 fällt
DISCARDED_V01 = {
    "IMG_4874", "IMG_4876", "IMG_4880", "IMG_4881", "IMG_4882",
    "IMG_4885", "IMG_4886", "IMG_4887", "IMG_4894", "IMG_4895",
    "IMG_4896", "IMG_4899",
}


def sammeln() -> list[tuple[Path, str]]:
    """(Pfad, Kategorie) — Proxys und Mac-Ressourcedateien bleiben draußen."""
    out: list[tuple[Path, str]] = []

    v01 = ROH / "01 - Unterschied Fleischkäse vs. Leberkäse"
    for p in sorted(v01.glob("*.MOV")):
        if p.name.startswith("._"):
            continue
        out.append((p, "01-Freigegeben"))

    disc = ROH / "00 Discarded"
    for p in sorted(disc.glob("*.MOV")):
        if p.name.startswith("._") or p.stem not in DISCARDED_V01:
            continue
        out.append((p, "00-Discarded"))

    for p in sorted(ROH.glob("*.MOV")):
        if p.name.startswith("._"):
            continue
        out.append((p, "Frei/Hook"))

    return out


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(parents=True, exist_ok=True)
    index_path = intern / "transcripts_index.json"
    api_key = os.environ["ELEVENLABS_API_KEY"]

    clips = sammeln()

    index = []
    done = set()
    if index_path.exists():
        index = json.loads(index_path.read_text())
        done = {r["path"] for r in index if r.get("ok")}

    for i, (p, kategorie) in enumerate(clips, 1):
        if str(p) in done:
            print(f"{i}/{len(clips)} SKIP {p.name}", flush=True)
            continue
        clip = Clip(path=p, camera=kategorie, sidecar=find_sidecar(p))
        rec = {
            "name": p.name,
            "path": str(p),
            "kategorie": kategorie,
            "kamera": "iPhone",
            "kamera_rolle": "ton",
            "fingerprint": clip_fingerprint(p),
        }
        try:
            t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
            speakers = sorted({w.speaker for w in t.words if w.speaker})
            rec.update({
                "ok": True,
                "duration_s": round(t.duration(), 1),
                "n_words": len(t.words),
                "speakers": speakers,
                "text": t.text,
            })
            print(f"{i}/{len(clips)} OK   {kategorie}/{p.name} "
                  f"({rec['n_words']} W, {rec['duration_s']}s)", flush=True)
        except Exception as e:
            rec.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            print(f"{i}/{len(clips)} FEHLER {p.name}: {rec['error']}", flush=True)

        index = [r for r in index if r["path"] != str(p)] + [rec]
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))

    ok = sum(1 for r in index if r.get("ok"))
    print(f"\nFERTIG: {ok}/{len(clips)} Clips -> {index_path}")


if __name__ == "__main__":
    main()
