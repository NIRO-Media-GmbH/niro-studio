"""WLC — Transkription der geänderten Final-Cuts (29.07.2026) + Timing-Diff.

Transkribiert die 4 neuen Schnittfassungen aus `Material/Fertige Video nach
änderungen/` (ElevenLabs Scribe, Wort-Timestamps, Cache in _intern/cache),
schreibt Wort-SRTs (0-basiert!) und vergleicht gegen die alten Wort-SRTs der
Replay-Fassungen, um pro Overlay-Element den Zeit-Versatz zu bestimmen.
"""
from __future__ import annotations

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

TOOL = Path("/Users/jansantos/NIRO Studio/tools/transcribe")
sys.path.insert(0, str(TOOL / "src"))

import os
for line in (TOOL / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip, find_sidecar
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip

PROJECT = Path("/Users/jansantos/NIRO Studio/projects/WLC/Recruiting/2026-07 Erster Dreh")
NEW_DIR = PROJECT / "Material" / "Fertige Video nach änderungen"
SRT_OUT = PROJECT / "Material" / "Transkript Fertige Videos" / "Nach Änderungen 2026-07-29"

VIDEOS = {
    "1.4": "1.4 Fachkraft Lager - Wenn du seit Jahren den selben Gang läufst.mp4",
    "1.5": "1.5 Fachkraft Lager - 30 Meter hoch. Und wir wachsen weiter..mp4",
    "1.6": "1.6 Employer-Brand - Alles Lager. Alles hier..mp4",
    "V7": "Video 7.mp4",
}
OLD_SRT = {
    "1.4": PROJECT / "Material" / "Transkript Fertige Videos" / "1.4.srt",
    "1.5": PROJECT / "Material" / "Transkript Fertige Videos" / "1.5.srt",
    "V7": Path("/Users/jansantos/Downloads/WLC Transkripte/Video 7.srt"),
}
# Overlay-Elemente mit ALTEN Timings (aus Protokoll / gebauten Comps)
ELEMENTS = {
    "1.4": [
        ("Hook zweistufig", 0.1, 5.6),
        ("Splash MARVIN/Gruppenleiter", 7.6, 11.8),
        ("Zeitstrahl Werdegang (Stationen 8.96/10.04/18.36/20.48)", 8.96, 21.5),
        ("Card WEITERENTWICKLUNG", 21.8, 27.8),
    ],
    "1.5": [
        ("Hook zweizeilig", 3.3, 7.8),
        ("Splash", 8.6, 13.0),
        ("FTS-Card", 22.0, 25.2),
        ("Skew-Bar Würth-Gruppe", 39.6, 42.8),
        ("Improve-Card", 54.9, 60.0),
    ],
    "V7": [
        ("Hook 1.300 €", 0.3, 8.2),
        ("Berufe-Board (Chips 8.4–21.9)", 8.4, 21.9),
        ("Sina-Splash", 22.9, 26.0),
        ("Flash-Card IMMER JEMAND DA", 49.9, 52.2),
        ("Benefits-Board", 52.6, 70.8),
        ("Closer EIN GEILES UNTERNEHMEN", 73.9, 77.0),
        ("WILLKOMMEN IM TEAM", 82.6, 85.5),
    ],
}


def fmt(t: float) -> str:
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s, ms = s + 1, 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(words: list[dict], path: Path) -> None:
    lines = []
    for i, w in enumerate(words, 1):
        lines += [str(i), f"{fmt(w['start'])} --> {fmt(w['end'])}", w["text"].strip(), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_srt(path: Path) -> list[dict]:
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8", errors="replace")):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) >= 3 and "-->" in lines[1]:
            m = re.match(
                r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1]
            )
            if not m:
                continue
            g = [int(x) for x in m.groups()]
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
            for tok in " ".join(lines[2:]).split():
                cues.append({"text": tok, "start": start, "end": end})
    # Premiere-Timeline-Offset (01:00:00:00) entfernen
    if cues and cues[0]["start"] >= 3500:
        for c in cues:
            c["start"] -= 3600
            c["end"] -= 3600
    return cues


def norm(t: str) -> str:
    return re.sub(r"[^\wäöüß]", "", t.lower())


def diff(old: list[dict], new: list[dict]):
    a = [norm(w["text"]) for w in old]
    b = [norm(w["text"]) for w in new]
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    segs, removed, added = [], [], []
    prev_a = prev_b = 0
    for bl in sm.get_matching_blocks():
        if not bl.size:
            continue
        if bl.a > prev_a:
            removed.append((old[prev_a]["start"], old[bl.a - 1]["end"],
                            " ".join(w["text"] for w in old[prev_a:bl.a])))
        if bl.b > prev_b:
            added.append((new[prev_b]["start"], new[bl.b - 1]["end"],
                          " ".join(w["text"] for w in new[prev_b:bl.b])))
        off_start = new[bl.b]["start"] - old[bl.a]["start"]
        off_end = (new[bl.b + bl.size - 1]["start"] - old[bl.a + bl.size - 1]["start"])
        segs.append({"old_from": old[bl.a]["start"], "old_to": old[bl.a + bl.size - 1]["end"],
                     "off_start": off_start, "off_end": off_end, "n": bl.size})
        prev_a, prev_b = bl.a + bl.size, bl.b + bl.size
    if prev_a < len(old):
        removed.append((old[prev_a]["start"], old[-1]["end"],
                        " ".join(w["text"] for w in old[prev_a:])))
    if prev_b < len(new):
        added.append((new[prev_b]["start"], new[-1]["end"],
                      " ".join(w["text"] for w in new[prev_b:])))
    return segs, removed, added


def offset_at(segs, t: float):
    """Versatz für alten Zeitpunkt t: Segment das t enthält, sonst letztes davor."""
    last = None
    for s in segs:
        if s["old_from"] - 0.3 <= t <= s["old_to"] + 0.3:
            frac = 0.0 if s["old_to"] == s["old_from"] else (t - s["old_from"]) / (s["old_to"] - s["old_from"])
            return s["off_start"] + frac * (s["off_end"] - s["off_start"])
        if s["old_from"] > t:
            break
        last = s
    return last["off_end"] if last else None


def main() -> None:
    intern = PROJECT / "_intern"
    cache = TranscriptCache(intern / "cache")
    work = intern / "work"
    work.mkdir(exist_ok=True)
    SRT_OUT.mkdir(parents=True, exist_ok=True)
    api_key = os.environ["ELEVENLABS_API_KEY"]

    all_words: dict[str, dict] = {}
    for key, fname in VIDEOS.items():
        p = NEW_DIR / fname
        clip = Clip(path=p, camera=f"FinalCut-v2/{key}", sidecar=find_sidecar(p))
        t = transcribe_clip(clip, cache=cache, api_key=api_key, work_dir=work)
        words = [w.to_dict() for w in t.words]
        all_words[key] = {"file": fname, "n_words": len(words),
                          "speech_end": round(t.duration(), 2), "words": words}
        write_srt(words, SRT_OUT / (Path(fname).stem + ".srt"))
        print(f"OK {key}: {len(words)} Wörter, Sprache bis {t.duration():.1f}s", flush=True)
        wav = work / f"{p.stem}.wav"
        if wav.exists():
            wav.unlink()

    (intern / "final_cuts_v2_words.json").write_text(
        json.dumps(all_words, ensure_ascii=False, indent=1), encoding="utf-8")

    report = {}
    for key, old_path in OLD_SRT.items():
        if not old_path.exists():
            print(f"!! {key}: alte SRT fehlt ({old_path})", flush=True)
            continue
        old = parse_srt(old_path)
        new = all_words[key]["words"]
        segs, removed, added, = diff(old, new)
        print(f"\n===== {key} — Timing-Diff (alt → neu) =====")
        for s in segs:
            if s["n"] < 3:
                continue
            print(f"  alt {s['old_from']:6.1f}–{s['old_to']:6.1f}s  Versatz "
                  f"{s['off_start']:+.2f}s → {s['off_end']:+.2f}s  ({s['n']} Wörter)")
        for fr, to, txt in removed:
            print(f"  ENTFERNT alt {fr:.1f}–{to:.1f}s: „{txt[:90]}“")
        for fr, to, txt in added:
            print(f"  NEU      neu {fr:.1f}–{to:.1f}s: „{txt[:90]}“")
        el_out = []
        print(f"  --- Overlay-Elemente {key} ---")
        for name, a, b in ELEMENTS.get(key, []):
            oa, ob = offset_at(segs, a), offset_at(segs, b)
            if oa is None:
                line = f"  {name}: alt {a:.1f}–{b:.1f}s → Versatz unbekannt (vor erstem Match)"
                el_out.append({"element": name, "old": [a, b], "new": None})
            else:
                na, nb = a + oa, b + (ob if ob is not None else oa)
                flag = " ⚠️ uneinheitlich" if ob is not None and abs(ob - oa) > 0.25 else ""
                line = f"  {name}: alt {a:.1f}–{b:.1f}s → neu {na:.1f}–{nb:.1f}s ({oa:+.2f}s){flag}"
                el_out.append({"element": name, "old": [a, b], "new": [round(na, 2), round(nb, 2)],
                               "offset_start": round(oa, 2),
                               "offset_end": round(ob, 2) if ob is not None else None})
            print(line)
        report[key] = {"segments": segs, "removed": removed, "added": added,
                       "elements": el_out}

    (intern / "retiming_v2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nFERTIG → _intern/final_cuts_v2_words.json, _intern/retiming_v2.json, "
          f"SRTs in {SRT_OUT}", flush=True)


if __name__ == "__main__":
    main()
