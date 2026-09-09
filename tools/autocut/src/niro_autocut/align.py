"""Wörtliche Zitate gegen Wort-Zeitstempel (Scribe) ausrichten.

Dünne Hülle um die geprüfte Alignment-Engine `quote_align.py` (Fitting-Alignment
auf Token-Ebene mit Alias-, Levenshtein- und Kölner-Phonetik-Ähnlichkeit, Take-Wahl
über den mm:ss-Hinweis, „[…]"-Fragmente als Segmente). Diese Datei stellt die im
Umsetzungsplan festgelegte API bereit, gegen die `cutlist.py` und die CLI
`autocut_find_quote.py` programmiert sind:

    normalize(tok)                      einzelnes Token vereinheitlichen
    split_fragments(quote)              Zitat an „[…]" in Fragmente teilen
    Match                               Treffer (Wortindizes, Sekunden, Score, Text, Sprecher)
    find_span(words, fragment, …)       Kandidaten für EIN Fragment, beste zuerst
    find_quote(words, quote, …)         ganzes Zitat: Anfang 1. Fragment … Ende letztes Fragment
    words_between(words, start_s, end_s)
    segments_of(match)                  Teilschnitte eines „[…]"-Zitats: (in_s, out_s, text)

Eingabe sind Wort-Dicts `{"text", "start", "end", "speaker"}` (NIRO-Cache-Format);
Indizes in `Match` beziehen sich immer auf die übergebene Liste.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from . import quote_align as qa

# Zahlwörter/Symbole, die `normalize` auf eine kanonische Form zieht (nur für
# Einzeltoken-Vergleiche; die Engine normalisiert intern über `quote_align.norm_tokens`).
NUM_WORDS = {"hundert": "100", "einhundert": "100", "zehn": "10", "zwölf": "12", "zwanzig": "20",
             "dreißig": "30", "vierzig": "40", "fünfzig": "50", "sechzig": "60", "siebzig": "70",
             "achtzig": "80", "neunzig": "90", "vierundzwanzig": "24", "prozent": "%"}

_ANNOTATION = re.compile(r"\(.*\)|\[.*\]")   # „(übersprechen 00:01:31)", „[lacht]"

# Die Engine schreibt Ziffern als Zahlwörter aus („100" → „einhundert"); gesprochen wird
# fast immer „hundert"/„tausend". Aliasse wirken symmetrisch auf Zitat und Transkript.
DEFAULT_ALIASES: dict[str, str] = {"einhundert": "hundert", "eintausend": "tausend"}


def normalize(tok: str) -> str:
    """Einzelnes Token vereinheitlichen: NFC, Kleinschreibung, ß→ss, nur Buchstaben/Ziffern/%."""
    t = unicodedata.normalize("NFC", tok or "").lower().strip()
    t = t.replace("ß", "ss")
    t = "".join(ch for ch in t if ch.isalnum() or ch == "%")
    return NUM_WORDS.get(t, t)


def split_fragments(quote: str) -> list[str]:
    """Anführungszeichen, Regieanweisungen „(lacht)" und redaktionelle Klammern
    entfernen, an Auslassungszeichen „[…]" in Fragmente teilen."""
    return qa.split_quote(quote or "")


@dataclass
class Match:
    start_idx: int
    end_idx: int
    start_s: float
    end_s: float
    score: float
    text: str
    speaker: str | None
    # Zusatzinformationen der Engine (optional, brechen positionale Konstruktion nicht):
    segments: list[tuple[float, float, str]] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"start_idx": self.start_idx, "end_idx": self.end_idx, "start_s": self.start_s,
                "end_s": self.end_s, "score": self.score, "text": self.text, "speaker": self.speaker,
                "segments": [list(s) for s in self.segments], "flags": list(self.flags)}

    @classmethod
    def from_dict(cls, d: dict) -> "Match":
        return cls(int(d["start_idx"]), int(d["end_idx"]), float(d["start_s"]), float(d["end_s"]),
                   float(d["score"]), str(d.get("text", "")), d.get("speaker"),
                   [tuple(s) for s in d.get("segments", [])], list(d.get("flags", [])))


# --------------------------------------------------------------------------- #
# Wort-Dicts → Engine
# --------------------------------------------------------------------------- #

def _to_twords(words: list[dict]) -> list[qa.TWord]:
    """Wort-Dicts in Engine-Wörter wandeln. `idx` bleibt der Index in der übergebenen
    Liste; Leerwörter, Nicht-Wörter (Scribe `type`) und Klammer-Annotationen fallen weg."""
    out: list[qa.TWord] = []
    for i, w in enumerate(words):
        t = w.get("type")
        if t is not None and t != "word":
            continue
        text = str(w.get("text", "")).strip()
        if not text or _ANNOTATION.fullmatch(text):
            continue
        out.append(qa.TWord(text, float(w["start"]), float(w["end"]), w.get("speaker") or w.get("speaker_id"), i))
    return out


def _aligner(words: list[dict], aliases: dict[str, str] | None = None) -> qa.Aligner | None:
    tw = _to_twords(words)
    if not tw:
        return None
    return qa.Aligner(tw, "", {**DEFAULT_ALIASES, **(aliases or {})})


def _match_from_segments(al: qa.Aligner, words: list[dict], segs: list[qa.Segment], score: float,
                         flags: list[str] | None = None) -> Match:
    first, last = segs[0], segs[-1]
    start_idx = al.words[first.first_word].idx
    end_idx = al.words[last.last_word].idx
    speaker = words[start_idx].get("speaker") or words[start_idx].get("speaker_id")
    segments = [(float(s.start), float(s.end), s.text) for s in segs]
    text = " […] ".join(s[2] for s in segments)
    return Match(start_idx, end_idx, float(first.start), float(last.end), float(score), text, speaker,
                 segments, list(flags or []))


# --------------------------------------------------------------------------- #
# Öffentliche API
# --------------------------------------------------------------------------- #

def align_quote(words: list[dict], quote: str, near_s: float | None = None, *, min_score: float = 0.6,
                max_gap_s: float = 180.0, top: int = 3, window_s: float = 120.0,
                aliases: dict[str, str] | None = None) -> qa.QuoteMatch | None:
    """Rohes Engine-Ergebnis (inkl. Flags und Alternativ-Takes) für Aufrufer, die mehr
    als `Match` brauchen. Wortindizes darin sind Engine-intern; `gap_before/gap_after`
    nicht verwenden — verworfene Scribe-Annotationen („(übersprechen …)") zählen dort
    fälschlich als Stille."""
    al = _aligner(words, aliases)
    if al is None:
        return None
    return al.find(quote, near_s, window_s=window_s, min_score=min_score, max_gap_s=max_gap_s, top=top)


def find_span(words: list[dict], fragment: str, near_s: float | None = None, min_score: float = 0.6) -> list[Match]:
    """Alle Kandidaten-Takes für EIN Fragment, beste zuerst (Score, dann Nähe zu `near_s`).
    Enthält das Fragment selbst ein „[…]", zählt nur der erste Teil."""
    frags = split_fragments(fragment)
    if not frags:
        return []
    al = _aligner(words)
    if al is None:
        return []
    qm = al.find(frags[0], near_s, min_score=min_score, top=1000)
    if qm is None:
        return []
    out = [_match_from_segments(al, words, [qm.segments[0]], qm.segments[0].score, qm.flags)]
    for seg in qm.alternatives:
        out.append(_match_from_segments(al, words, [seg], seg.score))
    return out


def find_quote(words: list[dict], quote: str, near_s: float | None = None, min_score: float = 0.8,
               max_gap_s: float = 180.0) -> Match | None:
    """Ganzes Zitat auflösen: Anfang des ersten Fragments bis Ende des letzten.
    None, wenn das erste Fragment fehlt oder ein späteres Fragment nicht innerhalb
    von `max_gap_s` nach dem vorigen gefunden wird (Engine-Flag „!")."""
    al = _aligner(words)
    if al is None:
        return None
    qm = al.find(quote, near_s, min_score=min_score, max_gap_s=max_gap_s)
    if qm is None or not qm.segments or any(f.startswith("!") for f in qm.flags):
        return None
    return _match_from_segments(al, words, qm.segments, qm.score, qm.flags)


def words_between(words: list[dict], start_s: float, end_s: float) -> list[dict]:
    """Wörter, deren Mitte im Intervall [start_s, end_s] liegt."""
    return [w for w in words if start_s <= (float(w["start"]) + float(w["end"])) / 2 <= end_s]


def segments_of(match: Match) -> list[tuple[float, float, str]]:
    """Teilschnitte eines Treffers als (in_s, out_s, Transkript-Text) — bei „[…]"-Zitaten
    mehrere, sonst genau einer."""
    if match.segments:
        return list(match.segments)
    return [(match.start_s, match.end_s, match.text)]
