#!/usr/bin/env python3
"""quote_align.py — Wörtliche Schnittplan-Zitate gegen Scribe-Wortzeitstempel ausrichten.

Verfahren
  1. Transkript-Wörter → normalisierte Subtokens (jedes Subtoken behält start/end
     seines Ursprungsworts).  Zitat → Fragmente (Split an „[…]") → Subtokens.
  2. Pro Fragment ein "fitting alignment" (global im Zitat, lokal im Transkript,
     Smith-Waterman-Variante auf Token-Ebene) mit graduierter Token-Ähnlichkeit:
     exakt 1.0 · Alias-Tabelle (Verhörer) · Levenshtein-Ähnlichkeit (rapidfuzz)
     · Kölner Phonetik als Rettungsanker.  Lücken kosten, Fehlwörter kosten.
  3. Alle lokalen Maxima der letzten DP-Zeile = Kandidaten-Takes; Auswahl über
     Score und Nähe zum mm:ss-Hinweis aus dem Plan.
  4. Ergebnis: wortgenaue start/end (Sekunden), Score 0..1, Anker-Qualität für
     erstes/letztes Wort, Segmente (für „[…]"-Zitate = mehrere Timeline-Clips),
     Alternativ-Takes, Sprecher im Fenster, Stille davor/danach (Cut-Spielraum).

Abhängigkeit: rapidfuzz (MIT).  Python ≥ 3.11.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rapidfuzz.distance import Levenshtein

# --------------------------------------------------------------------------- #
# 1. Transkript
# --------------------------------------------------------------------------- #

@dataclass
class TWord:
    text: str
    start: float
    end: float
    speaker: str | None
    idx: int            # Index im Original-Wortarray (für Rückverweise)


def load_scribe_words(path: str | Path) -> list[TWord]:
    """Liest Roh-Scribe (words[].type == 'word', speaker_id) ODER das
    NIRO-Cache-Format (kein type, speaker).  spacing/audio_event und
    Klammer-Annotationen fliegen raus."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[TWord] = []
    for i, w in enumerate(d["words"]):
        t = w.get("type")
        if t is not None and t != "word":
            continue
        text = str(w.get("text", "")).strip()
        if not text or re.fullmatch(r"\(.*\)", text):   # „(übersprechen 00:01:31)“ u. ä. (Scribe v1)
            continue
        out.append(TWord(str(w["text"]), float(w["start"]), float(w["end"]),
                         w.get("speaker_id") or w.get("speaker"), i))
    return out


# --------------------------------------------------------------------------- #
# 2. Normalisierung
# --------------------------------------------------------------------------- #

FILLER = {"äh", "ähm", "ähh", "hm", "hmm", "mhm", "mmh", "ehm", "em"}
CONTRACTIONS = {"n": "ein", "ne": "eine", "nen": "einen", "nem": "einem",
                "ner": "einer", "s": "es", "was": "etwas"}   # nur mit Apostroph
SYMBOLS = {"%": " prozent ", "€": " euro ", "&": " und ", "§": " paragraph ",
           "+": " plus ", "m²": " quadratmeter ", "km/h": " kmh "}
_UNITS = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben",
          "acht", "neun", "zehn", "elf", "zwölf", "dreizehn", "vierzehn",
          "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
_TENS = [None, None, "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig",
         "siebzig", "achtzig", "neunzig"]


def _lt100(n: int) -> str:
    if n < 20:
        return _UNITS[n]
    t, u = divmod(n, 10)
    if u == 0:
        return _TENS[t]
    return ("ein" if u == 1 else _UNITS[u]) + "und" + _TENS[t]


def _lt1000(n: int) -> str:
    h, r = divmod(n, 100)
    s = ("ein" if h == 1 else _UNITS[h]) + "hundert" if h else ""
    return s + (_lt100(r) if r else "")


def de_number(n: int) -> str:
    """Kardinalzahl als deutsches Zahlwort (0..999999). 1100–1999 mit Rest als
    Jahreszahl-Form („neunzehnhunderteinunddreißig")."""
    if n == 0:
        return "null"
    if 1100 <= n <= 1999 and n % 100:
        return _lt100(n // 100) + "hundert" + _lt100(n % 100)
    t, r = divmod(n, 1000)
    s = (("ein" if t == 1 else _lt1000(t)) + "tausend") if t else ""
    return s + (_lt1000(r) if r else "")


def _numbers_to_words(tok: str) -> str:
    """'53.000' → 'dreiundfünfzigtausend', '2,5' → 'zwei komma fünf', '50' → 'fünfzig'."""
    m = re.fullmatch(r"(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?", tok)
    if not m:
        return tok
    whole = int(m.group(1).replace(".", ""))
    if whole > 999_999:
        return tok
    s = de_number(whole)
    if m.group(2):
        s += " komma " + " ".join(de_number(int(c)) for c in m.group(2))
    return s


def norm_tokens(text: str, aliases: dict[str, str] | None = None) -> list[str]:
    """Text → Liste normalisierter Subtokens.  Beide Seiten (Plan & ASR) laufen
    durch dieselbe Funktion, damit Varianten symmetrisch verschwinden."""
    s = unicodedata.normalize("NFC", text)
    s = s.replace("’", "'").replace("‘", "'").replace("`", "'").replace("´", "'")
    for k, v in SYMBOLS.items():
        s = s.replace(k, v)
    s = re.sub(r"[-–—/]+", " ", s)               # Bindestrich-/Schrägstrich-Split
    out: list[str] = []
    for raw in s.split():
        raw = raw.lower()
        # Apostroph-Verkürzungen: 'n → ein, 's → es …
        m = re.fullmatch(r"'?([a-zäöüß]+)'?", raw.strip(".,;:!?\"„“”‚()[]"))
        if raw.startswith("'") and m and m.group(1) in CONTRACTIONS:
            raw = CONTRACTIONS[m.group(1)]
        raw = _numbers_to_words(raw.strip(".,;:!?\"„“”‚()[]"))
        for piece in raw.split():
            piece = re.sub(r"[^a-z0-9äöüß]+", "", piece)
            if not piece or piece in FILLER:
                continue
            if aliases:
                piece = aliases.get(piece, piece)
            out.append(piece)
    return out


# Kölner Phonetik (Postel 1969) — für deutsche Verhörer wie Craiss/Kreis/Greis.
def koelner(word: str) -> str:
    w = word.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "s")
    w = re.sub(r"[^a-z]", "", w)
    if not w:
        return ""
    codes = []
    n = len(w)
    for i, c in enumerate(w):
        prev = w[i - 1] if i > 0 else ""
        nxt = w[i + 1] if i + 1 < n else ""
        if c in "aeijouy":
            code = "0"
        elif c == "h":
            code = "-"
        elif c == "b":
            code = "1"
        elif c == "p":
            code = "3" if nxt == "h" else "1"
        elif c in "dt":
            code = "8" if nxt in "csz" and nxt else "2"
        elif c in "fvw":
            code = "3"
        elif c in "gkq":
            code = "4"
        elif c == "c":
            if i == 0:
                code = "4" if nxt in "ahkloqrux" and nxt else "8"
            elif prev in "sz":
                code = "8"
            else:
                code = "4" if nxt in "ahkoqux" and nxt else "8"
        elif c == "x":
            code = "8" if prev in "ckq" and prev else "48"
        elif c == "l":
            code = "5"
        elif c in "mn":
            code = "6"
        elif c == "r":
            code = "7"
        elif c in "sz":
            code = "8"
        else:
            code = ""
        codes.append(code)
    raw = "".join(codes).replace("-", "")
    collapsed = re.sub(r"(.)\1+", r"\1", raw)
    return collapsed[:1] + collapsed[1:].replace("0", "")


@lru_cache(maxsize=1 << 18)
def token_sim(a: str, b: str) -> float:
    """Graduierte Token-Ähnlichkeit 0..1 (symmetrisch, gecacht)."""
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la < 3 or lb < 3:
        return 0.0
    s = Levenshtein.normalized_similarity(a, b)
    if s >= 0.75:
        return s
    if la >= 4 and lb >= 4 and s >= 0.4 and koelner(a) == koelner(b):
        return 0.8
    return 0.0


# --------------------------------------------------------------------------- #
# 3. Alignment
# --------------------------------------------------------------------------- #

GAP_QUOTE = 0.6      # Zitatwort ohne Gegenstück (ASR hat's verschluckt / Plan-Zusatz)
GAP_TRANS = 0.4      # Transkriptwort innerhalb des Zitats (Stottern, Einschub)
MISMATCH = 0.5       # Diagonale ohne Ähnlichkeit


@dataclass
class Segment:
    start: float
    end: float
    score: float          # normiert auf Zitatlänge, ≤ 1
    exact: float          # Anteil exakt getroffener Zitat-Tokens
    first_word: int       # Index in words[] (TWord)
    last_word: int
    start_anchor: str     # 'exact' | 'fuzzy' | 'gap' (erstes Zitatwort)
    end_anchor: str
    text: str             # Transkript-Wortlaut des Fensters


@dataclass
class QuoteMatch:
    file: str
    start: float
    end: float
    score: float
    exact: float
    segments: list[Segment]
    alternatives: list[Segment]     # weitere Takes des ERSTEN Fragments
    speakers: set[str]
    gap_before: float               # Stille vor erstem Wort (Cut-Spielraum)
    gap_after: float
    flags: list[str] = field(default_factory=list)

    def ok(self, min_score: float = 0.6) -> bool:
        return self.score >= min_score and not any(f.startswith("!") for f in self.flags)


class Aligner:
    def __init__(self, words: list[TWord], file: str = "", aliases: dict[str, str] | None = None):
        self.words = words
        self.file = file
        self.aliases = aliases or {}
        self.tok: list[str] = []
        self.tok_word: list[int] = []      # Subtoken → Index in words
        for wi, w in enumerate(words):
            for t in norm_tokens(w.text, self.aliases):
                self.tok.append(t)
                self.tok_word.append(wi)
        self.word_first_tok = {}
        for ti, wi in enumerate(self.tok_word):
            self.word_first_tok.setdefault(wi, ti)

    # -- Kern: fitting alignment eines Fragment-Tokenvektors in tok[lo:hi] ------
    def _align(self, q: list[str], lo: int, hi: int) -> list[tuple[float, int, int, list[str]]]:
        """Liefert Kandidaten (score, tok_start, tok_end_inclusive, ops[]) — alle
        lokalen Maxima der letzten DP-Zeile, absteigend nach Score."""
        h = self.tok[lo:hi]
        m, n = len(q), len(h)
        if m == 0 or n == 0:
            return []
        NEG = -1e9
        # H[i][j]: bestes Alignment q[:i] mit Ende in h[j-1] (oder Lücke); freier Start in h
        H = [[0.0] * (n + 1)] + [[NEG] * (n + 1) for _ in range(m)]
        D = [[0] * (n + 1) for _ in range(m + 1)]      # 1=diag 2=up(gap q) 3=left(gap h)
        for i in range(1, m + 1):
            qi = q[i - 1]
            Hi, Hp, Di = H[i], H[i - 1], D[i]
            Hi[0] = -i * GAP_QUOTE
            Di[0] = 2
            for j in range(1, n + 1):
                sim = token_sim(qi, h[j - 1])
                diag = Hp[j - 1] + (sim if sim > 0 else -MISMATCH)
                up = Hp[j] - GAP_QUOTE
                left = Hi[j - 1] - GAP_TRANS
                if diag >= up and diag >= left:
                    Hi[j], Di[j] = diag, 1
                elif up >= left:
                    Hi[j], Di[j] = up, 2
                else:
                    Hi[j], Di[j] = left, 3
        last = H[m]
        peaks = [j for j in range(1, n + 1)
                 if last[j] >= (last[j - 1] if j > 1 else NEG)
                 and last[j] > (last[j + 1] if j < n else NEG)
                 and D[m][j] == 1]
        cands = []
        for j_end in peaks:
            i, j, ops = m, j_end, []
            while i > 0:
                d = D[i][j]
                if d == 1:
                    ops.append(("M", i - 1, j - 1)); i -= 1; j -= 1
                elif d == 2:
                    ops.append(("Q", i - 1, None)); i -= 1
                else:
                    ops.append(("H", None, j - 1)); j -= 1
            ops.reverse()
            matched = [op for op in ops if op[0] == "M"]
            if not matched:
                continue
            cands.append((last[j_end] / m, lo + matched[0][2], lo + matched[-1][2], ops))
        cands.sort(key=lambda c: -c[0])
        kept: list = []
        for c in cands:                      # überlappende Spannen → nur den besten
            if all(c[2] < k[1] or c[1] > k[2] for k in kept):
                kept.append(c)
        return kept

    def _segment(self, q: list[str], cand) -> Segment:
        score, ts, te, ops = cand
        # exakte Treffer zählen (ops tragen fragment-lokale h-Indizes → +Offset)
        off = ts - next(op[2] for op in ops if op[0] == "M")
        ex = 0
        for op in ops:
            if op[0] == "M" and q[op[1]] == self.tok[op[2] + off]:
                ex += 1
        def anchor(op):
            if op[0] != "M":
                return "gap"
            return "exact" if q[op[1]] == self.tok[op[2] + off] else "fuzzy"
        first_op = ops[0]
        last_op = ops[-1]
        wf, wl = self.tok_word[ts], self.tok_word[te]
        return Segment(self.words[wf].start, self.words[wl].end, round(score, 3),
                       round(ex / max(1, len(q)), 3), wf, wl, anchor(first_op), anchor(last_op),
                       " ".join(w.text for w in self.words[wf:wl + 1]))

    def _tok_range_for_time(self, t0: float, t1: float) -> tuple[int, int]:
        lo = next((ti for ti, wi in enumerate(self.tok_word) if self.words[wi].end >= t0), len(self.tok))
        hi = next((ti for ti in range(len(self.tok) - 1, -1, -1) if self.words[self.tok_word[ti]].start <= t1), -1) + 1
        return lo, max(lo, hi)

    # -- öffentlich -------------------------------------------------------------
    def find(self, quote: str, hint_s: float | None = None, *, window_s: float = 120.0,
             min_score: float = 0.6, max_gap_s: float = 90.0, top: int = 3) -> QuoteMatch | None:
        frags = split_quote(quote)
        qtoks = [norm_tokens(f, self.aliases) for f in frags]
        qtoks = [q for q in qtoks if q]
        if not qtoks:
            return None
        flags: list[str] = []

        # Fragment 1: erst im Hint-Fenster, sonst ganze Datei
        cands = []
        if hint_s is not None:
            lo, hi = self._tok_range_for_time(hint_s - window_s, hint_s + window_s)
            cands = [c for c in self._align(qtoks[0], lo, hi) if c[0] >= min_score]
        if not cands:
            cands = [c for c in self._align(qtoks[0], 0, len(self.tok)) if c[0] >= min_score]
            if hint_s is not None and cands:
                flags.append("hint-fenster verfehlt (Treffer außerhalb ±%.0f s)" % window_s)
        if not cands:
            return None
        # Take-Wahl: bester Score; bei Gleichstand (≥ best-0.1) Nähe zum Hint
        best = cands[0][0]
        pool = [c for c in cands if c[0] >= best - 0.1]
        if hint_s is not None:
            pool.sort(key=lambda c: abs(self.words[self.tok_word[c[1]]].start - hint_s))
        elif len(pool) > 1:
            flags.append("mehrdeutig: %d Takes mit ähnlichem Score, kein Timecode-Hinweis" % len(pool))
        chosen = pool[0]
        segs = [self._segment(qtoks[0], chosen)]
        alts = [self._segment(qtoks[0], c) for c in cands if c is not chosen][:top]

        # weitere Fragmente: jeweils NACH dem vorigen Segment, max. max_gap_s später
        for q in qtoks[1:]:
            prev = segs[-1]
            lo = self.word_first_tok[prev.last_word] + 1
            _, hi = self._tok_range_for_time(prev.end, prev.end + max_gap_s)
            c2 = [c for c in self._align(q, lo, hi) if c[0] >= min_score]
            if not c2:
                flags.append("! Fragment nicht gefunden: „%s…“" % " ".join(q[:5]))
                continue
            c2.sort(key=lambda c: (-round(c[0], 1), c[1]))   # gleich gut → frühester
            segs.append(self._segment(q, c2[0]))

        first, last = segs[0], segs[-1]
        wf, wl = first.first_word, last.last_word
        speakers = {w.speaker for w in self.words[wf:wl + 1] if w.speaker}
        gap_before = self.words[wf].start - (self.words[wf - 1].end if wf > 0 else 0.0)
        gap_after = (self.words[wl + 1].start if wl + 1 < len(self.words) else self.words[wl].end + 5) - self.words[wl].end
        score = sum(s.score * 1 for s in segs) / len(segs)
        if first.start_anchor == "gap":
            flags.append("Zitatanfang nicht im Transkript – Start auf nächstes Treffer-Wort gesetzt")
        if last.end_anchor == "gap":
            flags.append("Zitatende nicht im Transkript – Ende auf letztes Treffer-Wort gesetzt")
        if len(speakers) > 1:
            flags.append("mehrere Sprecher im Fenster: %s" % sorted(speakers))
        return QuoteMatch(self.file, first.start, last.end, round(score, 3),
                          round(sum(s.exact for s in segs) / len(segs), 3), segs, alts,
                          speakers, round(gap_before, 3), round(gap_after, 3), flags)


# --------------------------------------------------------------------------- #
# 4. Plan-Seite: Zitat säubern / Fragmente
# --------------------------------------------------------------------------- #

_OMISSION = re.compile(r"\[\s*(?:…|\.{3}|\. \. \.)\s*\]|\(\s*(?:…|\.{3})\s*\)")
# Einfache Anführungszeichen nur an Wortgrenzen entfernen — außer dem Apostroph vor einer Kurzform („'ne“, „’n“,
# „'s“ …): Scribe schreibt ihn mit, und norm_tokens macht auf beiden Seiten erst mit ihm „eine“, „ein“, „es“ daraus.
_KURZFORM = "|".join(sorted(CONTRACTIONS, key=len, reverse=True))
_EINFACHE_ANF = re.compile(r"(?<![a-zäöüßA-ZÄÖÜ])[‚‘’'](?!(?i:%s)(?![a-zäöüßA-ZÄÖÜ]))|[‚‘’'](?![a-zäöüßA-ZÄÖÜ])"
                           % _KURZFORM)


def split_quote(quote: str) -> list[str]:
    """Anführungszeichen, Regieanweisungen, redaktionelle Klammern entfernen;
    an Auslassungszeichen „[…]" in Fragmente teilen."""
    q = quote.strip()
    q = re.sub(r"\*\([^)]*\)\*", " ", q)              # *(nicht im Transkript)*
    q = _OMISSION.sub("\x00", q)
    q = re.sub(r"\[[^\]]*\]", " ", q)                   # [redaktionell] → weg
    q = re.sub(r"\([^)]*\)", " ", q)                    # (lacht) → weg
    q = re.sub(r"[„“”\"«»]", " ", q)                    # doppelte Anführungszeichen
    q = _EINFACHE_ANF.sub(" ", q)                       # einfache nur an Wortgrenzen, Kurzformen bleiben
    q = q.replace("…", " ")                             # freies „…" = Pause, kein Split
    return [f for f in (p.strip() for p in q.split("\x00")) if f]


def mmss(t: str) -> float:
    m, s = t.replace(",", ".").split(":")
    return int(m) * 60 + float(s)


def fmt(sec: float) -> str:
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:04.1f}"


# NIRO-Plan-Zeile: | # | Szene | „Zitat" | Person · Ordner/FX3_0856 · 09:14–09:18 | …
SRC = re.compile(r"((?:FX3|a7MK4|A7|C\d{4})[A-Za-z0-9_]*\d)\s*·\s*≈?(\d+:\d\d(?:,\d)?)\s*[–-]\s*≈?(\d+:\d\d(?:,\d)?)")


def iter_plan_rows(md_path: str | Path):
    for ln, line in enumerate(Path(md_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|") or line.count("|") < 6:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or "„" not in cells[2]:
            continue
        m = SRC.search(cells[3])
        if not m:
            continue
        yield ln, cells[2], m.group(1), mmss(m.group(2)), mmss(m.group(3))
