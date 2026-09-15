"""Rendert lesbare Szenen-Transkripte aus transcripts_index.json + Cache.

Ausgabe: Ergebnisse/Transkripte/<Gruppe>.md + uebersicht.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CHARGE = Path(__file__).resolve().parent.parent
INDEX = CHARGE / "_intern" / "transcripts_index.json"
CACHE = CHARGE / "_intern" / "cache"
OUT = CHARGE / "Ergebnisse" / "Transkripte"
# Timeline-Offsets (alle Szenen als EIN Video, s. _intern/timeline_offsets.py)
OFFSETS = json.loads((CHARGE / "_intern" / "timeline_offsets.json").read_text(encoding="utf-8"))

# Kundenfeedback (Kurzform) aus Material/Konzept/Kundenfeedback-Szenen.md
FEEDBACK = {
    "TA4": "gut — Erwähnung als Exzellenzpartner gefällt",
    "TA6": "gut",
    "TA9": "gut, aber viel Ähm",
    "TA12": "gut — Arbeitsweise gut beschrieben",
    "TA14": "sehr gut",
    "TA21": "sehr gut, aber viel Ähm",
    "TA22": "gut",
    "TA23": "sehr gut — Zitat „…Geschäftsführern dazu raten, sich für HBL zu entscheiden…“",
    "TA24": "sehr gut — menschliche Komponente",
    "TP2": "gut",
    "TP3": "teilweise — Schnitt bei „Prozesse digitalisieren, beschleunigen…“?",
    "TP5": "gut",
    "TP6": "sehr gut",
    "S1": "gut — ggf. einfügen: „Deine Abrechnung läuft mit uns fehlerfrei und pünktlich.“",
    "S2": "grundsätzlich gut — muss noch ergänzt werden, um was es genau geht",
    "S3": "teilweise — ab 0:10 verwenden",
    "M1": "gut",
    "M2": "teilweise — ab ~0:12 verwenden",
    "M3": "gut",
    "M5": "gut",
    "M6": "gut",
    "M7": "gut",
    "M8": "gut",
    "A1": "andere Einleitung nötig; Beispiel danach ok",
    "A5": "sehr gut",
}

GROUP_TITLES = {
    "A": "Gruppe A",
    "M": "Gruppe M",
    "S": "Gruppe S",
    "TA": "Gruppe TA — Testimonial André (HiServ)",
    "TP": "Gruppe TP — Testimonial Humanus (zwei Kameraperspektiven laut Kunde)",
}

GROUP_HINWEISE = {
    "TA": "Kundenwunsch: bei André (HiServ) die Ähms rausschneiden.",
    "TP": "Kundenwunsch: prüfen, welche der zwei Kameraperspektiven besser ist.",
}


def mmss(sec: float) -> str:
    total = int(sec)
    m, s = divmod(total, 60)
    return f"{m}:{s:02d}"


def scene_key(name: str) -> tuple[str, int]:
    m = re.fullmatch(r"([A-Za-z]+)(\d+)", Path(name).stem)
    if not m:
        return (Path(name).stem, 0)
    return (m.group(1).upper(), int(m.group(2)))


# Scribe-Verhörer korrigieren (bestätigt: Sprecher sagt „HBL", vgl. Kundenzitat zu TA23;
# HWL/HRE existieren nicht, Kontext ist jeweils die Zusammenarbeit mit HBL)
KORREKTUREN = {"HRE": "HBL", "HWL": "HBL"}


def korrigiere(text: str) -> str:
    for falsch, richtig in KORREKTUREN.items():
        text = re.sub(rf"\b{falsch}\b", richtig, text)
    return text


def sentences(words: list[dict]) -> list[dict]:
    """Wortliste -> Sätze mit Startzeit und Sprecher (Mehrheit der Wörter)."""
    out: list[dict] = []
    cur: list[dict] = []
    for w in words:
        cur.append(w)
        t = w["text"].strip()
        if re.search(r"[.!?…]$", t):
            out.append(_mk_sentence(cur))
            cur = []
    if cur:
        out.append(_mk_sentence(cur))
    return out


def _mk_sentence(ws: list[dict]) -> dict:
    speakers = [w.get("speaker") for w in ws if w.get("speaker")]
    speaker = max(set(speakers), key=speakers.count) if speakers else None
    return {
        "start": ws[0]["start"],
        "text": korrigiere(" ".join(w["text"].strip() for w in ws)),
        "speaker": speaker,
    }


def render() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    by_group: dict[str, list[dict]] = {}
    for rec in index:
        grp, nr = scene_key(rec["name"])
        rec["_grp"], rec["_nr"] = grp, nr
        by_group.setdefault(rec.get("camera") or grp, []).append(rec)

    overview_rows: list[str] = []
    for grp in sorted(by_group):
        recs = sorted(by_group[grp], key=lambda r: (r["_grp"], r["_nr"]))
        lines = [
            f"# {GROUP_TITLES.get(grp, f'Gruppe {grp}')}",
            "",
            "> Timecodes = DaVinci-Gesamttimeline (alle Szenen als EIN Video,",
            "> A→M→S→TA→TP, Stoß an Stoß) — Zuordnung: `00-timeline-referenz.md`.",
            "",
        ]
        if grp in GROUP_HINWEISE:
            lines += [f"> {GROUP_HINWEISE[grp]}", ""]
        for rec in recs:
            szene = Path(rec["name"]).stem
            fb = FEEDBACK.get(szene)
            if not rec.get("ok"):
                lines += [f"## {szene} — FEHLER bei Transkription", "",
                          f"`{rec.get('error', 'unbekannt')}`", ""]
                overview_rows.append(f"| {szene} | — | — | {fb or '—'} | FEHLER |")
                continue
            cache_file = CACHE / f"{rec['fingerprint']}.scribe.json"
            t = json.loads(cache_file.read_text(encoding="utf-8"))
            off = OFFSETS[szene]
            tl = f"TL {mmss(off['start'])}–{mmss(off['end'])}"
            head = f"## {szene} · {tl}"
            if fb:
                head += f" · **Kunde: {fb}**"
            lines += [head, ""]
            sents = sentences(t.get("words", []))
            n_speakers = len({s["speaker"] for s in sents if s["speaker"]})
            prev_speaker = None
            for s in sents:
                prefix = f"[{mmss(off['start'] + s['start'])}]"
                if n_speakers > 1 and s["speaker"] != prev_speaker:
                    prefix += f" ({s['speaker']})"
                    prev_speaker = s["speaker"]
                lines.append(f"{prefix} {s['text']}")
                lines.append("")
            first = sents[0]["text"] if sents else ""
            first = (first[:60] + "…") if len(first) > 60 else first
            overview_rows.append(f"| {szene} | {mmss(off['start'])} | {mmss(off['dur'])} | {fb or '—'} | {first} |")
        (OUT / f"{grp}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        print(f"geschrieben: {OUT / f'{grp}.md'}")

    ov = [
        "# HBL Imagefilm — Szenen-Transkripte: Übersicht",
        "",
        f"Quelle: NAS `…/03_Medien/HBL Szenen/` · {len(index)} Szenen · transkribiert mit",
        "ElevenLabs Scribe (Diarisation). Volltexte je Gruppe in `A.md`, `M.md`, `S.md`, `TA.md`, `TP.md`.",
        "",
        "Kundenfeedback aus `Material/Konzept/Kundenfeedback-Szenen.md` (Juli 2026).",
        "**TL-Start = Position in der DaVinci-Gesamttimeline** (A→M→S→TA→TP,",
        "Stoß an Stoß; Details `00-timeline-referenz.md`).",
        "",
        "| Szene | TL-Start | Dauer | Kundenfeedback | Beginn |",
        "|---|---|---|---|---|",
        *overview_rows,
        "",
    ]
    (OUT / "uebersicht.md").write_text("\n".join(ov), encoding="utf-8")
    print(f"geschrieben: {OUT / 'uebersicht.md'}")


if __name__ == "__main__":
    render()
