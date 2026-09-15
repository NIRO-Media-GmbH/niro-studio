"""Setzer Video 4 — Wort-SRT + lesbares Transkript aus dem Scribe-JSON bauen.

Format der SRT wie Davids Premiere-Wort-Export (Video 6): ein Wort pro Cue,
<b>-Tags, Timecodes mit +1 h Sequenz-Offset. Korrekturen ausschließlich am
Text, nie an den Originalzeiten (Projektregel seit Video 6).
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(
    "/Users/jansantos/NIRO Studio/projects/Setzer/Social-Reels/2026-08 Dreh 18.08"
)
WORDS_JSON = PROJECT / "_intern" / "video4_scribe_words.json"
OUT_DIR = PROJECT / "Video 4 zum Transkribieren"
SRT_OUT = OUT_DIR / "04 - Fleischsalat Zutaten UT Scribe.srt"
MD_OUT = OUT_DIR / "04 - Fleischsalat Zutaten Transkript.md"

OFFSET_S = 3600.0  # Premiere-Sequenz beginnt bei 01:00:00:00
MIN_CUE_S = 0.03   # Scribe liefert vereinzelt 0-ms-Wörter — SRT braucht Dauer

# Wort-Index -> korrigierter Text. Begründungen in der Tabelle im MD.
# Die mit „David 01.09." markierten sind am Ton des Schnitts bestätigt.
KORREKTUREN = {
    13: "drin ist.",       # David 01.09.: „was da drin ist"
    29: "Lyoner,",
    61: "füllen",
    75: "den",             # David 01.09.: „frisch in den Verkauf"
    76: "Verkauf",         # David 01.09. — Scribe verhörte „Theke"
    83: "Lyoner,",
    147: "Lyoner",
    171: "verteilt",
    175: "hier",           # David 01.09.: „dass hier dann jeder"
    182: "Unhygienisch",
    221: "haften bleiben",
    252: "Filiale.",       # David 01.09. — Scribe verhörte erneut „Theke"
}


def srt_tc(t: float) -> str:
    ms = round((t + OFFSET_S) * 1000)
    h, rest = divmod(ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    data = json.loads(WORDS_JSON.read_text())
    words = data["words"]

    cues = []
    korrigiert = []
    for i, w in enumerate(words):
        text = KORREKTUREN.get(i, w["text"])
        if i in KORREKTUREN:
            korrigiert.append((i, w["start"], w["text"], text))
        start = w["start"]
        end = max(w["end"], start + MIN_CUE_S)
        cues.append((start, end, text))

    lines = []
    for n, (start, end, text) in enumerate(cues, 1):
        lines.append(f"{n}\n{srt_tc(start)} --> {srt_tc(end)}\n<b>{text}</b>\n")
    SRT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"SRT: {SRT_OUT.name}")
    print(f"  {len(cues)} Cues, {srt_tc(cues[0][0])} bis {srt_tc(cues[-1][1])}")
    print("Korrekturen (auf Originalzeiten):")
    for i, start, alt, neu in korrigiert:
        print(f"  Wort {i:3d} @ {start:6.2f}s: {alt!r} -> {neu!r}")


if __name__ == "__main__":
    main()
