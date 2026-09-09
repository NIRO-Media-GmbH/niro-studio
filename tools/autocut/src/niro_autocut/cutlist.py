"""Cutlist: was Claude aus dem Cutter-Plan macht — und die harte Prüfung vor dem Bau.

Datei: <Charge>/_intern/autocut/cutlist.json (Aufbau siehe prompts/cutlist.md).
Dieses Modul schreibt nur dorthin, wo `Cutlist.save` aufgerufen wird; die Prüfung
`verify_cutlist` liest ausschließlich (Clip-Dateien und Proxys nur per Existenz-Test).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .align import find_quote, segments_of, words_between
from .charge import AutoCutError
from .plan import STEM_RE, TC_RE, parse_mmss

TYPEN = ("oton", "vo", "bild", "grafik")

# Scribe-Annotationen im Wortstrom („(übersprechen 00:01:31)", „[lacht]") sind keine Wörter.
_ANNOTATION = re.compile(r"\(.*\)|\[.*\]")


# --------------------------------------------------------------------------- #
# Hilfen für das Einlesen
# --------------------------------------------------------------------------- #

def _check_keys(d: object, wo: str, allowed: set[str], required: set[str]) -> dict:
    """JSON-Objekt gegen erlaubte/erforderliche Felder prüfen — Tippfehler sofort melden."""
    if not isinstance(d, dict):
        raise AutoCutError(f"{wo}: erwartet ein JSON-Objekt, gefunden {type(d).__name__}.")
    unknown = sorted(set(d) - allowed)
    if unknown:
        raise AutoCutError(f"{wo}: unbekannte Felder {unknown} — erlaubt sind {sorted(allowed)}.")
    missing = sorted(required - set(d))
    if missing:
        raise AutoCutError(f"{wo}: Pflichtfelder fehlen: {missing}.")
    return d


def _float(d: dict, key: str, wo: str) -> float:
    try:
        return float(d[key])
    except (TypeError, ValueError):
        raise AutoCutError(f"{wo}: Feld '{key}' muss eine Zahl sein, gefunden {d[key]!r}.") from None


def _opt_float(d: dict, key: str, wo: str) -> float | None:
    return None if d.get(key) is None else _float(d, key, wo)


def _opt_str(d: dict, key: str) -> str | None:
    v = d.get(key)
    return None if v is None else str(v)


def _tc(s: float) -> str:
    """Sekunden → „mm:ss.z" (Lesehilfe neben dem Sekundenwert, passend zu den Plan-Timecodes)."""
    m, sec = divmod(max(0.0, float(s)), 60)
    return f"{int(m):02d}:{sec:04.1f}"


def _iv(a: float, b: float) -> str:
    return f"{a:.2f}–{b:.2f}s ({_tc(a)}–{_tc(b)})"


# --------------------------------------------------------------------------- #
# Modell
# --------------------------------------------------------------------------- #

@dataclass
class Cut:
    """Ein Teilschnitt: Sekunden im Quellclip (Anfang erstes Wort, Ende letztes Wort) + gesprochener Text."""
    in_s: float
    out_s: float
    text: str = ""
    hart_in: bool = False      # True: kein Vorlauf-Handle (Plan „In hart")
    hart_out: bool = False     # True: kein Nachlauf-Handle (Plan „Out HART")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Cut") -> "Cut":
        _check_keys(d, wo, {"in_s", "out_s", "text", "hart_in", "hart_out"}, {"in_s", "out_s"})
        return cls(in_s=_float(d, "in_s", wo), out_s=_float(d, "out_s", wo), text=str(d.get("text") or ""),
                   hart_in=bool(d.get("hart_in", False)), hart_out=bool(d.get("hart_out", False)))


@dataclass
class Beat:
    """Eine Zeile des Cutter-Plans. typ: oton (Interview-Schnitt) | vo | bild | grafik (Platzhalter)."""
    nr: str
    szene: str
    typ: str
    person: str | None = None
    rolle: str | None = None
    clip: str | None = None              # voller Pfad des FX3-Originals (aus dem Transkript-Index)
    cuts: list[Cut] = field(default_factory=list)
    pause_after_s: float | None = None   # nur setzen, wenn der Plan etwas anderes als die Standardpause verlangt
    platzhalter_s: float | None = None   # Dauer der Lücke bei vo/bild/grafik (Plan-Schätzung „~x s")
    text: str | None = None              # VO-Text
    bild_hinweis: str = ""
    kommentar: str = ""
    caption: str | None = None
    plan_dauer_s: float | None = None    # Plan-Schätzung „~x s" (Plausibilitätsprüfung)
    sound: str = ""

    def dauer_s(self) -> float:
        if self.typ == "oton":
            return sum(c.out_s - c.in_s for c in self.cuts)
        return float(self.platzhalter_s or 0.0)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Beat") -> "Beat":
        allowed = {"nr", "szene", "typ", "person", "rolle", "clip", "cuts", "pause_after_s", "platzhalter_s",
                   "text", "bild_hinweis", "kommentar", "caption", "plan_dauer_s", "sound"}
        _check_keys(d, wo, allowed, {"nr", "szene", "typ"})
        wo = f"Beat #{d['nr']}"
        raw_cuts = d.get("cuts") or []
        if not isinstance(raw_cuts, list):
            raise AutoCutError(f"{wo}: 'cuts' muss eine Liste sein.")
        cuts = [Cut.from_dict(c, f"{wo} Cut {i}") for i, c in enumerate(raw_cuts, 1)]
        return cls(nr=str(d["nr"]), szene=str(d["szene"]), typ=str(d["typ"]).strip().lower(),
                   person=_opt_str(d, "person"), rolle=_opt_str(d, "rolle"), clip=_opt_str(d, "clip"), cuts=cuts,
                   pause_after_s=_opt_float(d, "pause_after_s", wo), platzhalter_s=_opt_float(d, "platzhalter_s", wo),
                   text=_opt_str(d, "text"), bild_hinweis=str(d.get("bild_hinweis") or ""),
                   kommentar=str(d.get("kommentar") or ""), caption=_opt_str(d, "caption"),
                   plan_dauer_s=_opt_float(d, "plan_dauer_s", wo), sound=str(d.get("sound") or ""))


@dataclass
class Sperre:
    """Gesperrter Bereich eines Clips (Kunden-Tabu aus „**Verboten:**"); Handles dürfen nicht hineinragen."""
    clip: str
    von_s: float
    bis_s: float
    grund: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Sperre") -> "Sperre":
        _check_keys(d, wo, {"clip", "von_s", "bis_s", "grund"}, {"clip", "von_s", "bis_s"})
        return cls(clip=str(d["clip"]), von_s=_float(d, "von_s", wo), bis_s=_float(d, "bis_s", wo),
                   grund=str(d.get("grund") or ""))


@dataclass
class Cutlist:
    video: str                    # Dateiname des Cutter-Plans (video-N-*.md)
    ziel_laenge_s: float | None
    fps: float
    format: str                   # "16:9" | "9:16"
    pause_s: float                # Standardlücke zwischen Beats
    beats: list[Beat]
    sperren: list[Sperre] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)   # z. B. Textsperren ohne Zeit — landen im Bericht

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Cutlist":
        allowed = {"video", "ziel_laenge_s", "fps", "format", "pause_s", "beats", "sperren", "hinweise"}
        _check_keys(d, "Cutlist", allowed, {"video", "fps", "beats"})
        if not isinstance(d["beats"], list):
            raise AutoCutError("Cutlist: 'beats' muss eine Liste sein.")
        beats = [Beat.from_dict(b, f"Beat {i}") for i, b in enumerate(d["beats"], 1)]
        sperren = [Sperre.from_dict(s, f"Sperre {i}") for i, s in enumerate(d.get("sperren") or [], 1)]
        hinweise = [str(h) for h in (d.get("hinweise") or [])]
        return cls(video=str(d["video"]), ziel_laenge_s=_opt_float(d, "ziel_laenge_s", "Cutlist"),
                   fps=_float(d, "fps", "Cutlist"), format=str(d.get("format") or "16:9"),
                   pause_s=1.0 if d.get("pause_s") is None else _float(d, "pause_s", "Cutlist"),
                   beats=beats, sperren=sperren, hinweise=hinweise)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Cutlist":
        p = Path(path)
        if not p.is_file():
            raise AutoCutError(f"Cutlist fehlt: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AutoCutError(f"Cutlist {p} ist kein gültiges JSON: {e}") from e
        try:
            return cls.from_dict(data)
        except AutoCutError as e:
            raise AutoCutError(f"{p}: {e}") from e


@dataclass
class VerifyResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings)}


# --------------------------------------------------------------------------- #
# Kennzahlen
# --------------------------------------------------------------------------- #

def cutlist_hash(path: str | Path) -> str:
    """SHA-256 der Datei — `autocut_build.py` verweigert bei geänderter, ungeprüfter Cutlist."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def total_length_s(cl: Cutlist, cfg: dict) -> float:
    """Cuts + Platzhalter + Pausen zwischen den Beats (keine Pause nach dem letzten Beat)."""
    pause_default = cl.pause_s if cl.pause_s is not None else float(cfg.get("pause_s", 1.0))
    total = 0.0
    for i, b in enumerate(cl.beats):
        total += b.dauer_s()
        if i < len(cl.beats) - 1:
            total += b.pause_after_s if b.pause_after_s is not None else pause_default
    return total


# --------------------------------------------------------------------------- #
# Prüfung
# --------------------------------------------------------------------------- #

def _overlaps(a0: float, a1: float, b0: float, b1: float) -> bool:
    return a0 < b1 and b0 < a1


def _speech_words(words: list[dict]) -> list[dict]:
    """Nur echte Wörter: keine Scribe-Sonderelemente (`type` ≠ word), keine Leer- oder Klammer-Tokens."""
    out = []
    for w in words:
        t = w.get("type")
        if t is not None and t != "word":
            continue
        text = str(w.get("text", "")).strip()
        if not text or _ANNOTATION.fullmatch(text):
            continue
        out.append(w)
    return out


def _file_problems(clip: str) -> list[str]:
    """Original und Proxy müssen da sein (Bau verknüpft den Proxy). Nur Existenz-Tests, nichts wird geöffnet."""
    from .media import proxy_for  # lokal: hält cutlist.py ohne niro_transcribe importierbar
    p = Path(clip)
    if not p.is_file():
        return [f"Clip-Datei nicht gefunden: {p} — ist das NAS gemountet?"]
    if proxy_for(p) is None:
        return [f"kein Proxy für {p.name} (erwartet {p.parent / 'Proxy' / (p.stem + '.mov')} oder .mp4) — "
                f"Proxy erzeugen, sonst kann der Bau keinen Proxy verknüpfen"]
    return []


def verify_cutlist(cl: Cutlist, charge, words_by_clip: dict[str, list[dict]], durations: dict[str, float],
                   cfg: dict, sync: dict | None = None) -> VerifyResult:
    """Harte Prüfung vor dem Bau (Spec 3.4). Fehler stoppen, Warnungen landen im Bericht.

    charge: Charge oder None. Mit Charge werden Original- und Proxy-Datei jedes Clips geprüft
    (nur Existenz); ohne Charge (Tests) entfällt das.
    words_by_clip: Schlüssel = Clip-Pfad wie im Transkript-Index (`rec["path"]`), Wert = Cache-Wörter.
    durations: Clip-Dauer in Sekunden je Pfad (media.json, Index oder ffprobe).
    sync: Inhalt von sync.json (`{"paare": [...]}`) oder None → Abdeckung nicht geprüft.
    """
    r = VerifyResult()
    if not cl.beats:
        r.errors.append("Cutlist enthält keine Beats.")
        return r
    if not cl.fps or cl.fps <= 0:
        r.errors.append(f"Ungültige Bildrate fps={cl.fps} — Wert aus media.json (format.fps) übernehmen.")
        return r
    if cl.pause_s is None or cl.pause_s < 0:
        r.errors.append(f"pause_s={cl.pause_s} ist ungültig (≥ 0 erwartet).")
    fps = float(cl.fps)
    h_in = cfg["handle_in_frames"] / fps
    h_out = cfg["handle_out_frames"] / fps
    lo, hi = cfg["duration_tolerance"]
    min_score = float(cfg["align_min_score"])

    for i, s in enumerate(cl.sperren, 1):
        tag = f"Sperre {i} ({s.grund or 'ohne Grund'})"
        if s.clip not in words_by_clip:
            r.errors.append(f"{tag}: Clip {s.clip} hat kein Transkript oder ist nicht in der Charge — Pfad muss "
                            f"exakt dem Index-Eintrag entsprechen, sonst schützt die Sperre nichts.")
        if s.von_s < 0 or s.bis_s <= s.von_s:
            r.errors.append(f"{tag}: ungültiges Intervall {s.von_s:g}–{s.bis_s:g}s.")

    seen_nr: set[str] = set()
    file_cache: dict[str, list[str]] = {}
    for b in cl.beats:
        tag = f"Beat #{b.nr} ({b.szene})"
        if b.nr in seen_nr:
            r.warnings.append(f"{tag}: Nummer doppelt vergeben — Marker heißen dann gleich.")
        seen_nr.add(b.nr)
        if b.pause_after_s is not None and b.pause_after_s < 0:
            r.errors.append(f"{tag}: pause_after_s={b.pause_after_s:g} ist ungültig (≥ 0 erwartet).")
        if b.typ not in TYPEN:
            r.errors.append(f"{tag}: unbekannter Typ '{b.typ}' — erlaubt: {', '.join(TYPEN)}.")
            continue
        if b.typ != "oton":
            if not b.platzhalter_s or b.platzhalter_s <= 0:
                r.errors.append(f"{tag}: platzhalter_s fehlt (Plan-Schätzung „~x s“ übernehmen).")
            continue
        if not b.clip or not b.cuts:
            r.errors.append(f"{tag}: clip oder cuts fehlen.")
            continue
        words = words_by_clip.get(b.clip)
        if words is None:
            r.errors.append(f"{tag}: Clip {b.clip} hat kein Transkript oder ist nicht in der Charge "
                            f"(Pfad muss exakt dem Index-Eintrag entsprechen).")
            continue
        if charge is not None:
            if b.clip not in file_cache:
                file_cache[b.clip] = _file_problems(b.clip)
            for prob in file_cache[b.clip]:
                r.errors.append(f"{tag}: {prob}")
        dur = durations.get(b.clip)
        speech = _speech_words(words)
        ordered = sorted(b.cuts, key=lambda c: c.in_s)
        for prev, nxt in zip(ordered, ordered[1:]):
            if nxt.in_s < prev.out_s:
                r.warnings.append(f"{tag}: Cuts {_iv(prev.in_s, prev.out_s)} und {_iv(nxt.in_s, nxt.out_s)} "
                                  f"überschneiden sich — Absicht?")
        paare = [p for p in (sync or {}).get("paare", []) if p.get("ref") == b.clip and p.get("ok")]
        for c in b.cuts:
            if c.in_s < 0 or c.out_s <= c.in_s:
                r.errors.append(f"{tag}: ungültiges Intervall {c.in_s:g}–{c.out_s:g}.")
                continue
            if dur is not None and c.out_s > dur + 0.05:
                r.errors.append(f"{tag}: out {c.out_s:.2f}s liegt hinter dem Clip-Ende {dur:.2f}s.")
                continue
            inside = words_between(speech, c.in_s, c.out_s)
            if not inside:
                r.errors.append(f"{tag}: kein Transkript-Wort in {_iv(c.in_s, c.out_s)} — Zeiten oder Clip prüfen.")
                continue
            if not c.text.strip():
                r.errors.append(f"{tag}: Cut {_iv(c.in_s, c.out_s)} ohne Text — jeder Cut braucht den gesprochenen "
                                f"Wortlaut, sonst ist keine Prüfung gegen das Transkript möglich.")
            else:
                m = find_quote(inside, c.text, min_score=min_score)
                if m is None:
                    got = " ".join(w["text"] for w in inside)[:160]
                    r.errors.append(f"{tag}: Text stimmt nicht mit dem Transkript in {_iv(c.in_s, c.out_s)} "
                                    f"überein (Score < {min_score:g}). Dort steht: „{got}…“")
                else:
                    vorn = " ".join(w["text"] for w in inside[:m.start_idx])
                    hinten = " ".join(w["text"] for w in inside[m.end_idx + 1:])
                    if vorn or hinten:
                        teile = []
                        if vorn:
                            teile.append(f"vorn „{vorn}“")
                        if hinten:
                            teile.append(f"hinten „{hinten}“")
                        r.warnings.append(f"{tag}: Intervall {_iv(c.in_s, c.out_s)} enthält Wörter, die nicht im "
                                          f"Text stehen — {' / '.join(teile)}. in_s/out_s enger setzen oder Text ergänzen.")
            a0 = max(0.0, c.in_s - (0.0 if c.hart_in else h_in))
            a1 = c.out_s + (0.0 if c.hart_out else h_out)
            for s in cl.sperren:
                if s.clip == b.clip and _overlaps(a0, a1, s.von_s, s.bis_s):
                    r.errors.append(f"{tag}: Cut {_iv(c.in_s, c.out_s)} überschneidet (inkl. Handles) die Sperre "
                                    f"{_iv(s.von_s, s.bis_s)} ({s.grund}).")
            if sync is not None:
                covered = any(p["overlap_ref"][0] <= a0 and a1 <= p["overlap_ref"][1] for p in paare)
                if not covered:
                    r.warnings.append(f"{tag}: keine a7-Abdeckung für {_iv(c.in_s, c.out_s)} (V2 bleibt leer).")
        if b.plan_dauer_s:
            d = b.dauer_s()
            if not (lo * b.plan_dauer_s <= d <= hi * b.plan_dauer_s):
                r.warnings.append(f"{tag}: Dauer {d:.1f}s weicht stark von der Plan-Schätzung ~{b.plan_dauer_s:g}s ab.")

    if cl.ziel_laenge_s:
        total = total_length_s(cl, cfg)
        if abs(total - cl.ziel_laenge_s) / cl.ziel_laenge_s > cfg["target_length_warn"]:
            r.warnings.append(f"Gesamtlänge {total:.0f}s ({_tc(total)}) weicht von der Ziellänge {cl.ziel_laenge_s:.0f}s "
                              f"({_tc(cl.ziel_laenge_s)}) um mehr als {int(cfg['target_length_warn'] * 100)} % ab.")
    return r


# --------------------------------------------------------------------------- #
# Entwurf aus dem Cutter-Plan (scripts/autocut_cutlist_draft.py)
# --------------------------------------------------------------------------- #

_VO_PREFIX = re.compile(r"^\s*[*_]*\s*VO\s*[*_]*\s*:?\s*", re.I)
_QUOTE_CHARS = "„“”\"‚‘’«»"
_QUELLE_RE = re.compile(r"^\s*(?P<person>[^·(]+?)\s*(?:\((?P<rolle>[^)]*)\))?\s*(?:·|$)")
# Kommentar-Muster für harte Kanten: „In hart", „In NACH …", „harter Schnitt davor" → hart_in;
# „Out HART", „Out VOR …", „Harter Schnitt danach" → hart_out.
_HART_IN_RE = re.compile(r"\bIn\s+hart\b|\bhart(?:er|es|em)?\s+In\b|\bIn\s+NACH\b|\bharte[rs]?\s+Schnitt\s+davor\b", re.I)
_HART_OUT_RE = re.compile(r"\bOut\s+hart\b|\bhart(?:er|es|em)?\s+Out\b|\bOut\s+VOR\b|\bharte[rs]?\s+Schnitt\s+danach\b", re.I)
# Nur bei diesen Hinweisen werden „[…]"-Fragmente zu getrennten Cuts (sonst durchgehende Passage):
_EXPLIZIT_TEILSCHNITT_RE = re.compile(r"jumpcut|mittig\s+trimmen|zwischenruf|kurzfassung\s+fest|\d{1,2}:\d{2}\s*\+\s*\d{1,2}:\d{2}", re.I)
SPERRE_MIN_SCORE = 0.7   # Zitat-Sperren großzügiger suchen als Cuts — ein Zuviel an Sperre ist die sichere Richtung
_BARE_NUM_RE = re.compile(r"(?<![\d:])(\d{4})(?![\d:])")
_QUOTED_RE = re.compile(r"[„“\"‚‘]([^„“”\"‚‘’]{6,}?)[“”\"‘’]")
_PAREN_RE = re.compile(r"\([^)]*\)")
_LEER = {"", "—", "–", "-", "—.", "n/a", "keine"}
_TAIL_NUM_RE = re.compile(r"(\d{4,})(?:_\d+)?$")


def _clean_quote(s: str) -> str:
    return (s or "").strip().strip(_QUOTE_CHARS).strip()


def _vo_text(oton: str) -> str:
    return _clean_quote(_VO_PREFIX.sub("", oton or ""))


def _person_rolle(quelle: str) -> tuple[str | None, str | None]:
    """„Sandra (Fachkrankenschwester Notfallpflege) · S1/…" → („Sandra", „Fachkrankenschwester …"); „(s. o.)" → None."""
    m = _QUELLE_RE.match(quelle or "")
    if not m:
        return None, None
    person = m.group("person").strip().strip("*_ ") or None
    rolle = (m.group("rolle") or "").strip() or None
    if rolle and re.fullmatch(r"s\.\s*o\.?", rolle, re.I):
        rolle = None
    return person, rolle


class _ClipIndex:
    """Stem („FX3_9557") oder nackte Nummer („9557", Plan-Kurzform; Timecodes = FX3) → Index-Eintrag."""

    def __init__(self, index: list[dict]):
        self.by_stem: dict[str, list[dict]] = {}
        self.by_num: dict[str, list[dict]] = {}
        self.name_by_path: dict[str, str] = {}
        for rec in index:
            stem = Path(rec["name"]).stem
            self.by_stem.setdefault(stem.lower(), []).append(rec)
            m = _TAIL_NUM_RE.search(stem)
            if m:
                self.by_num.setdefault(m.group(1), []).append(rec)
            self.name_by_path[rec["path"]] = rec["name"]

    def resolve(self, token: str) -> tuple[str | None, str | None]:
        """(Pfad, None) oder (None, Problem)."""
        recs = self.by_stem.get(token.lower())
        if recs is None and token.isdigit():
            recs = [r for r in self.by_num.get(token, []) if r.get("kamera_rolle", "ton") == "ton"]
        if not recs:
            return None, f"Clip {token} nicht im Transkript-Index"
        if len(recs) > 1:
            return None, f"Clip {token} mehrdeutig: " + ", ".join(r["name"] for r in recs)
        return recs[0]["path"], None


def _answer_span(utts: list[dict], t: float) -> tuple[float, float] | None:
    """Antwort zum Plan-Zeitpunkt t (mm:ss, abgerundet): bevorzugt die Utterance, die zwischen t−1 s
    und t+5 s BEGINNT (der Plan nennt den Anfang der Aussage; die enthaltende Utterance ist oft noch
    die Frage), sonst die, die t enthält. Verlängert um direkt folgende Utterances desselben Sprechers."""
    if not utts:
        return None
    starting = [(float(u["von_s"]), k) for k, u in enumerate(utts) if t - 1.0 <= float(u["von_s"]) <= t + 5.0]
    if starting:
        i = min(starting)[1]
    else:
        i = next((k for k, u in enumerate(utts) if float(u["von_s"]) <= t <= float(u["bis_s"])), None)
        if i is None:
            return None
    j = i
    while j + 1 < len(utts) and utts[j + 1].get("speaker") == utts[i].get("speaker") \
            and float(utts[j + 1]["von_s"]) - float(utts[j]["bis_s"]) < 2.0:
        j += 1
    return float(utts[i]["von_s"]), float(utts[j]["bis_s"])


def _sperren_from_verboten(text: str, idx: _ClipIndex, index: list[dict], words_by_clip: dict, durations: dict,
                           utterances: list[dict] | None) -> tuple[list[Sperre], list[str], list[str]]:
    """„**Verboten:**"-Zeile → (Sperren, Hinweise für Textsperren, offene Punkte)."""
    sperren: list[Sperre] = []
    hinweise: list[str] = []
    offen: list[str] = []
    utt_by_name = {u["name"]: u.get("utterances", []) for u in (utterances or [])}
    for raw in re.split(r";|\n", text or ""):
        entry = raw.strip().rstrip(".").strip()
        if not entry:
            continue
        core = _PAREN_RE.sub("", entry)                     # Klammern sind Anmerkungen, keine Sperrzeiten
        tokens = [m.group(1) for m in STEM_RE.finditer(core)] or _BARE_NUM_RE.findall(core)
        if not tokens:
            qm = _QUOTED_RE.search(entry)
            name = re.split(r"[„“\"‚‘]", entry)[0].strip().rstrip(":").strip()
            cands = [r for r in index if r.get("kamera_rolle", "ton") == "ton" and name
                     and name.lower() in (r.get("person") or "").lower()]
            hits = []
            if qm and cands:
                for rec in cands:
                    m = find_quote(words_by_clip.get(rec["path"], []), qm.group(1), min_score=SPERRE_MIN_SCORE)
                    if m is not None:
                        hits.append(Sperre(rec["path"], round(max(0.0, m.start_s - 0.5), 2), round(m.end_s + 0.5, 2), entry))
            if hits:
                sperren.extend(hits)
            else:
                hinweise.append(f"Textsperre ohne Zeit (nicht automatisch prüfbar): {entry}")
            continue
        path, prob = idx.resolve(tokens[0])
        if prob:
            offen.append(f"Sperre „{entry}“: {prob} — Clip-Pfad von Hand eintragen.")
            continue
        times = [(parse_mmss(m.group(1)), parse_mmss(m.group(2)) if m.group(2) else None) for m in TC_RE.finditer(core)]
        if not times:
            offen.append(f"Sperre „{entry}“: keine Zeitangabe — von_s/bis_s von Hand setzen (Clip: {Path(path).name}).")
            continue
        ab = re.search(r"\bab\b", core, re.I) is not None
        for von, bis in times:
            if bis is not None:
                sperren.append(Sperre(path, von, bis, entry))
            elif ab:
                dur = durations.get(path)
                if dur:
                    sperren.append(Sperre(path, von, round(float(dur), 2), entry))
                else:
                    offen.append(f"Sperre „{entry}“: „ab {_tc(von)}“ ohne bekannte Clip-Dauer — bis_s = Clip-Ende eintragen.")
            else:
                span = _answer_span(utt_by_name.get(idx.name_by_path.get(path, ""), []), von)
                if span:
                    sperren.append(Sperre(path, round(span[0], 2), round(span[1], 2), entry))
                else:
                    offen.append(f"Sperre „{entry}“: Zeitpunkt {_tc(von)} ohne Ende und keine passende Utterance — "
                                 f"von_s/bis_s von Hand setzen (Clip: {Path(path).name}).")
    return sperren, hinweise, offen


def draft_from_plan(plan, index: list[dict], words_by_clip: dict[str, list[dict]], durations: dict[str, float],
                    cfg: dict, fps: float, fmt: str, utterances: list[dict] | None = None) -> tuple[Cutlist, list[str]]:
    """Cutter-Plan → Cutlist-Entwurf. Rückgabe (Cutlist, offene Punkte).

    O-Ton-Zeilen: Clip aus dem ersten Timecode-Hinweis der Quelle, Zitat per `find_quote` nahe dem
    mm:ss-Hinweis aufgelöst („[…]" → mehrere Cuts), „In hart"/„Out HART" aus dem Kommentar.
    VO/Bild/Grafik: Platzhalter = Plan-Schätzung. Sperren aus „**Verboten:**". Der Entwurf ist
    ungeprüft — Claude liest jeden Beat gegen den Plan und lässt autocut_verify.py laufen.
    """
    idx = _ClipIndex(index)
    min_score = float(cfg["align_min_score"])
    beats: list[Beat] = []
    offen: list[str] = []
    rolle_von: dict[str, str] = {}
    for row in plan.rows:
        caption = None if (row.caption or "").strip() in _LEER else row.caption.strip()
        b = Beat(nr=row.nr, szene=row.szene, typ=row.typ, bild_hinweis=(row.bild or "").strip(),
                 kommentar=(row.kommentar or "").strip(), caption=caption, plan_dauer_s=row.plan_dauer_s,
                 sound="" if (row.sound or "").strip() in _LEER else row.sound.strip())
        tag = f"#{row.nr} ({row.szene})"
        if row.typ != "oton":
            if row.typ == "vo":
                b.text = _vo_text(row.oton) or None
            if row.plan_dauer_s:
                b.platzhalter_s = float(row.plan_dauer_s)
            else:
                offen.append(f"{tag}: keine Plan-Schätzung „~x s“ — platzhalter_s von Hand setzen.")
            beats.append(b)
            continue
        b.person, b.rolle = _person_rolle(row.quelle)
        if b.person and b.rolle:
            rolle_von[b.person] = b.rolle
        elif b.person and not b.rolle:
            b.rolle = rolle_von.get(b.person)
        if not row.tc_hints:
            offen.append(f"{tag}: kein Clip-Stem in der Quelle „{row.quelle}“ — clip und cuts von Hand setzen.")
            beats.append(b)
            continue
        hint = row.tc_hints[0]
        path, prob = idx.resolve(hint["stem"])
        if prob:
            offen.append(f"{tag}: {prob} — clip und cuts von Hand setzen.")
            beats.append(b)
            continue
        b.clip = path
        words = words_by_clip.get(path)
        if not words:
            offen.append(f"{tag}: kein Transkript für {Path(path).name} — cuts von Hand setzen.")
            beats.append(b)
            continue
        m = find_quote(words, row.oton, near_s=hint["von_s"], min_score=min_score)
        if m is None:
            offen.append(f"{tag}: Zitat in {Path(path).name} nahe {_tc(hint['von_s'])} nicht gefunden (Score < {min_score:g}) — "
                         f"autocut_find_quote.py --all nutzen und cuts von Hand setzen.")
            beats.append(b)
            continue
        segs = segments_of(m)
        if len(segs) > 1 and not _EXPLIZIT_TEILSCHNITT_RE.search(f"{row.kommentar or ''} {row.quelle or ''}"):
            # Cutter-Standard (David): „[…]" kürzt das Zitat nur in der PDF — die Passage läuft durchgehend.
            segs = [(segs[0][0], segs[-1][1], " […] ".join(t for _, _, t in segs))]
        b.cuts = [Cut(round(s0, 3), round(s1, 3), txt) for s0, s1, txt in segs]
        for k, c in enumerate(b.cuts):          # innere Jumpcut-Grenzen hart: kein Handle in die Auslassung
            c.hart_in = k > 0
            c.hart_out = k < len(b.cuts) - 1
        if _HART_IN_RE.search(row.kommentar or ""):
            b.cuts[0].hart_in = True
        if _HART_OUT_RE.search(row.kommentar or ""):
            b.cuts[-1].hart_out = True
        if m.flags:
            offen.append(f"{tag}: Treffer mit Hinweis {m.flags} — Zeiten {_iv(m.start_s, m.end_s)} gegen den Plan prüfen.")
        if len(row.tc_hints) > 1:
            offen.append(f"{tag}: Quelle nennt mehrere Zeitbereiche — Cuts gegen den Plan prüfen.")
        beats.append(b)
    sperren, hinweise, s_offen = _sperren_from_verboten(plan.verboten_text, idx, index, words_by_clip, durations,
                                                        utterances)
    offen.extend(s_offen)
    cl = Cutlist(video=Path(plan.file).name, ziel_laenge_s=plan.ziel_laenge_s, fps=float(fps), format=fmt,
                 pause_s=float(cfg.get("pause_s", 1.0)), beats=beats, sperren=sperren, hinweise=hinweise)
    return cl, offen
