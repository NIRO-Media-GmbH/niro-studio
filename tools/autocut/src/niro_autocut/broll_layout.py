"""B-Roll-Layout v2 (Spec v2 Abschnitt 3): Sprecher-Fenster → Strecken → Szenen → Shots über die ganze Timeline.

Plan-Datei <Charge>/_intern/autocut/broll_plan.json (version 2):
    {"version": 2, "video": "…", "fenster": [{"beat_nr", "offset_s", "dauer_s" | "voll", "grund"}],
     "strecken": [{"nr", "szenen": [{"ordner", "ausnahme", "grund", "shots": [{"clip", "in_s", "out_s", "tempo", "grund",
                                                                              "abweichung", "abweichung_grund"}]}]}]}
Fenster liegen nur an O-Ton-Beats; Strecken sind die Lücken dazwischen (über Pausen, Platzhalter, Beat-Grenzen hinweg);
Szenen füllen Strecken lückenlos; tempo 2/4 = echtes Konformieren (Timeline-Dauer = (out−in)·tempo).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import telemetrie as TM
from .broll_plan import (_index_by_path, _merge_an_abschnittsgrenzen, _section_quality, _standort_nr, _usable_spans,
                         clip_ref, resolve_clip_ref)
from .charge import AutoCutError
from .cutlist import Beat, Cutlist, VerifyResult
from .media import seconds_to_frames
from .timeline_model import MARKER_COLORS, Item, MarkerSpec

PLAN_VERSION = 2
TEMPI = (1, 2, 4)
EPS = 0.05
_FAST_CUTS = re.compile(r"schnelle\s+(cuts|schnitte)", re.IGNORECASE)
_NUR_STANDORT = re.compile(r"\bnur\s+S\s?(\d)\b", re.IGNORECASE)
_MONTAGE_WORTE = ("wechselschnitt", "montage")


def _check_keys(d: object, wo: str, allowed: set[str], required: set[str]) -> dict:
    if not isinstance(d, dict):
        raise AutoCutError(f"{wo}: erwartet ein JSON-Objekt, gefunden {type(d).__name__}.")
    unknown = sorted(set(d) - allowed)
    if unknown:
        raise AutoCutError(f"{wo}: unbekannte Felder {unknown} — erlaubt sind {sorted(allowed)}.")
    missing = sorted(required - set(d))
    if missing:
        raise AutoCutError(f"{wo}: Pflichtfelder fehlen: {missing}.")
    return d


def _f(d: dict, key: str, wo: str, default=None) -> float | None:
    if key not in d or d[key] is None:
        return default
    try:
        return float(d[key])
    except (TypeError, ValueError):
        raise AutoCutError(f"{wo}: Feld '{key}' muss eine Zahl sein, gefunden {d[key]!r}.") from None


def _int(d: dict, key: str, wo: str, default=None) -> int | None:
    if key not in d or d[key] is None:
        return default
    try:
        return int(d[key])
    except (TypeError, ValueError):
        raise AutoCutError(f"{wo}: Feld '{key}' muss eine ganze Zahl sein, gefunden {d[key]!r}.") from None


def _s(x: float) -> str:
    return f"{float(x):.1f}".replace(".", ",") + " s"


# --------------------------------------------------------------------------- #
# Modell
# --------------------------------------------------------------------------- #

@dataclass
class Fenster:
    beat_nr: str
    offset_s: float = 0.0
    dauer_s: float | None = None
    voll: bool = False
    grund: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Fenster") -> "Fenster":
        _check_keys(d, wo, {"beat_nr", "offset_s", "dauer_s", "voll", "grund"}, {"beat_nr"})
        voll = bool(d.get("voll", False))
        dauer = _f(d, "dauer_s", wo)
        if not voll and dauer is None:
            raise AutoCutError(f"{wo} (Beat #{d['beat_nr']}): dauer_s fehlt (oder voll: true).")
        return cls(beat_nr=str(d["beat_nr"]), offset_s=_f(d, "offset_s", wo, 0.0), dauer_s=dauer, voll=voll, grund=str(d.get("grund") or ""))


@dataclass
class Shot:
    clip: str
    in_s: float
    out_s: float
    tempo: int = 1
    grund: str = ""
    abweichung: bool = False
    abweichung_grund: str = ""

    def dauer_tl_s(self) -> float:
        return (self.out_s - self.in_s) * self.tempo

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Shot") -> "Shot":
        _check_keys(d, wo, {"clip", "in_s", "out_s", "tempo", "grund", "abweichung", "abweichung_grund"}, {"clip", "in_s", "out_s"})
        tempo = _int(d, "tempo", wo, 1)
        if tempo not in TEMPI:
            raise AutoCutError(f"{wo}: tempo {tempo} ist ungültig — erlaubt {TEMPI}.")
        return cls(clip=str(d["clip"]), in_s=_f(d, "in_s", wo), out_s=_f(d, "out_s", wo), tempo=tempo, grund=str(d.get("grund") or ""),
                   abweichung=bool(d.get("abweichung", False)), abweichung_grund=str(d.get("abweichung_grund") or ""))


@dataclass
class Szene:
    ordner: str
    shots: list[Shot] = field(default_factory=list)
    ausnahme: str = ""
    grund: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Szene") -> "Szene":
        _check_keys(d, wo, {"ordner", "shots", "ausnahme", "grund"}, {"ordner", "shots"})
        if not isinstance(d["shots"], list):
            raise AutoCutError(f"{wo}: 'shots' muss eine Liste sein.")
        return cls(ordner=str(d["ordner"]), shots=[Shot.from_dict(s, f"{wo} Shot {i}") for i, s in enumerate(d["shots"], 1)],
                   ausnahme=str(d.get("ausnahme") or ""), grund=str(d.get("grund") or ""))


@dataclass
class Strecke:
    nr: int
    szenen: list[Szene] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Strecke") -> "Strecke":
        _check_keys(d, wo, {"nr", "szenen", "von_s", "bis_s"}, {"nr", "szenen"})   # von_s/bis_s nur zur Lesbarkeit
        nr = _int(d, "nr", wo)
        wo = f"Strecke {nr}"
        return cls(nr=nr, szenen=[Szene.from_dict(s, f"{wo} Szene {i}") for i, s in enumerate(d["szenen"], 1)])


@dataclass
class LayoutPlan:
    video: str
    fenster: list[Fenster] = field(default_factory=list)
    strecken: list[Strecke] = field(default_factory=list)
    version: int = PLAN_VERSION

    def to_dict(self) -> dict:
        return {"version": self.version, "video": self.video, "fenster": [f.to_dict() for f in self.fenster],
                "strecken": [s.to_dict() for s in self.strecken]}

    @classmethod
    def from_dict(cls, d) -> "LayoutPlan":
        if isinstance(d, dict) and "beats" in d and "strecken" not in d:
            raise AutoCutError("B-Roll-Plan im alten Format (beats) — Plan v2 mit fenster/strecken schreiben; "
                               "Strecken liefert `autocut_place_broll.py --raster`.")
        _check_keys(d, "B-Roll-Plan", {"version", "video", "fenster", "strecken"}, {"strecken"})
        if _int(d, "version", "B-Roll-Plan", PLAN_VERSION) != PLAN_VERSION:
            raise AutoCutError(f"B-Roll-Plan: version {d.get('version')} wird nicht unterstützt (erwartet {PLAN_VERSION}).")
        return cls(video=str(d.get("video") or ""), fenster=[Fenster.from_dict(f, f"Fenster {i}") for i, f in enumerate(d.get("fenster") or [], 1)],
                   strecken=[Strecke.from_dict(s, f"Strecke {i}") for i, s in enumerate(d["strecken"], 1)])

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "LayoutPlan":
        p = Path(path)
        if not p.is_file():
            raise AutoCutError(f"B-Roll-Plan fehlt: {p} — nach prompts/place-broll.md erstellen.")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AutoCutError(f"B-Roll-Plan {p} ist kein gültiges JSON: {e}") from e
        try:
            return cls.from_dict(data)
        except AutoCutError as e:
            raise AutoCutError(f"{p}: {e}") from e

    def all_shots(self) -> list[tuple[Strecke, Szene, Shot]]:
        return [(st, sz, sh) for st in self.strecken for sz in st.szenen for sh in sz.shots]


# --------------------------------------------------------------------------- #
# Fenster und Strecken
# --------------------------------------------------------------------------- #

def _beats_sorted(tp_dict: dict) -> list[dict]:
    return sorted((b for b in (tp_dict.get("beats") or [])), key=lambda b: int(b["rec_in_f"]))


def beat_at(tp_dict: dict, f: int) -> dict | None:
    """Beat unter Frame f; in einer Pause der vorige Beat; vor dem ersten Beat None."""
    last = None
    for b in _beats_sorted(tp_dict):
        if int(b["rec_in_f"]) <= f < int(b["rec_out_f"]):
            return b
        if int(b["rec_in_f"]) > f:
            break
        last = b
    return last


def is_full_face_beat(beat: Beat, beat_dauer_s: float, cfg: dict, is_first: bool) -> bool:
    text = f"{beat.szene} {beat.bild_hinweis} {beat.kommentar}".lower()
    if is_first or beat_dauer_s < float(cfg["full_face_beat_max_s"]) - EPS:
        return True
    return any(str(k).lower() in text for k in cfg.get("full_face_keywords") or [])


def default_windows(tp_dict: dict, cl: Cutlist, cfg: dict) -> list[Fenster]:
    """Standardfenster je O-Ton-Beat: Ganz-Gesicht (voll) oder 2,5 s beim ersten Auftritt der Person, sonst 2,0 s."""
    fps = float(tp_dict["fps"])
    cl_beats = {b.nr: b for b in cl.beats}
    first_seen: set[str] = set()
    out: list[Fenster] = []
    beats = _beats_sorted(tp_dict)
    for i, tb in enumerate(beats):
        if tb.get("typ") != "oton":
            continue
        cb = cl_beats.get(str(tb["nr"]))
        dauer = (int(tb["rec_out_f"]) - int(tb["rec_in_f"])) / fps
        person = str(tb.get("person") or (cb.person if cb else "") or "")
        if cb is not None and is_full_face_beat(cb, dauer, cfg, is_first=(i == 0)):
            out.append(Fenster(str(tb["nr"]), 0.0, None, True, "Ganz-Gesicht (Hook/Schlüsselwort/kurzer Beat)"))
        elif person not in first_seen:
            out.append(Fenster(str(tb["nr"]), 0.0, float(cfg["window_first_s"]), False, f"erster Auftritt {person}"))
        else:
            out.append(Fenster(str(tb["nr"]), 0.0, float(cfg["window_s"]), False, "Sprecher-Fenster"))
        first_seen.add(person)
    return out


def effective_windows(plan: LayoutPlan | None, tp_dict: dict, cl: Cutlist, cfg: dict) -> list[Fenster]:
    """Plan-Fenster ersetzen die Standardfenster ihres Beats; Beats ohne Plan-Eintrag behalten den Standard.

    Anschließend rückt `adjust_short_stretches()` zu kurze Strecken vor einem Standardfenster zurecht — Plan-Fenster
    (`own`) bleiben dabei unverändert, das ist Claudes Verantwortung; bleibt dort eine Strecke zu kurz, meldet
    `raster()` das als Fehler.
    """
    fps = float(tp_dict["fps"])
    defaults = default_windows(tp_dict, cl, cfg)
    if plan is None or not plan.fenster:
        return adjust_short_stretches(defaults, tp_dict, cfg, fps)
    own = frozenset(f.beat_nr for f in plan.fenster)
    merged = [f for f in defaults if f.beat_nr not in own] + list(plan.fenster)
    return adjust_short_stretches(merged, tp_dict, cfg, fps, protect=own)


def window_frames(windows: list[Fenster], tp_dict: dict, fps: float, cfg: dict) -> tuple[list[dict], list[str]]:
    """Fenster in Frames; Fehler: kein O-Ton-Beat, außerhalb 1,5–4,0 s, ragt über das Beat-Ende, Überschneidung."""
    beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    lo, hi = float(cfg["window_min_s"]), float(cfg["window_max_s"])
    out, errs = [], []
    for w in windows:
        tb = beats.get(w.beat_nr)
        if tb is None:
            errs.append(f"Fenster Beat #{w.beat_nr}: Beat gibt es nicht in timeline.json.")
            continue
        if tb.get("typ") != "oton":
            errs.append(f"Fenster Beat #{w.beat_nr}: nur O-Ton-Beats haben Sprecher-Fenster (Typ {tb.get('typ')}).")
            continue
        b_in, b_out = int(tb["rec_in_f"]), int(tb["rec_out_f"])
        if w.voll:
            out.append({"beat_nr": w.beat_nr, "a_f": b_in, "b_f": b_out, "voll": True})
            continue
        if w.dauer_s is None or w.dauer_s < lo - EPS or w.dauer_s > hi + EPS:
            errs.append(f"Fenster Beat #{w.beat_nr}: {w.dauer_s} s außerhalb {_s(lo)}–{_s(hi)} (oder voll: true).")
            continue
        a = b_in + seconds_to_frames(w.offset_s, fps)
        b = a + seconds_to_frames(w.dauer_s, fps)
        if a < b_in or b > b_out:
            errs.append(f"Fenster Beat #{w.beat_nr}: {w.offset_s:g}+{w.dauer_s:g} s ragt über das Beat-Ende "
                        f"(Beat dauert {_s((b_out - b_in) / fps)}).")
            continue
        out.append({"beat_nr": w.beat_nr, "a_f": a, "b_f": b, "voll": False})
    out.sort(key=lambda x: x["a_f"])
    for p, q in zip(out, out[1:]):
        if q["a_f"] < p["b_f"]:
            errs.append(f"Fenster Beat #{p['beat_nr']} und #{q['beat_nr']} überschneiden sich.")
    return out, errs


def _window_positions(windows: list[Fenster], tp_dict: dict, fps: float) -> list[tuple[int, int]]:
    """a_f/b_f je Fenster, ungeprüft und in derselben Reihenfolge wie `windows` (siehe window_frames() für die
    geprüfte Variante, deren Ausgabe nach a_f sortiert ist und die Zuordnung zum Ursprungs-Fenster verliert)."""
    beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    out = []
    for w in windows:
        tb = beats[w.beat_nr]
        b_in, b_out = int(tb["rec_in_f"]), int(tb["rec_out_f"])
        if w.voll:
            out.append((b_in, b_out))
        else:
            a = b_in + seconds_to_frames(w.offset_s, fps)
            out.append((a, a + seconds_to_frames(w.dauer_s, fps)))
    return out


def adjust_short_stretches(windows: list[Fenster], tp_dict: dict, cfg: dict, fps: float,
                           protect: frozenset[str] = frozenset()) -> list[Fenster]:
    """Verschiebt Standardfenster nach hinten, wenn die Strecke davor sonst kürzer als der kürzeste Shot
    (`cfg["shot_len_s"][0]`) und damit unfüllbar wäre — typisch nach einem Ganz-Gesicht-Beat (`voll`), dessen Fenster
    bis ans Beat-Ende reicht, gefolgt vom Standardfenster des nächsten O-Ton-Beats bei offset_s 0.

    Nur Fenster mit `beat_nr` NICHT in `protect` (= aus dem Plan, siehe effective_windows()) werden verschoben; eine
    dort verbleibende zu kurze Strecke ist Claudes Verantwortung und wird von raster() als Fehler gemeldet. Reicht
    ein Verschieben nicht (das Fenster würde über das Beat-Ende ragen), wird das Fenster stattdessen auf `voll`
    gesetzt. Bei bereits ungültigen Fenstern (siehe window_frames()) wird nichts verändert.
    """
    min_len_s = float(cfg["shot_len_s"][0])
    beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    result = list(windows)
    for _ in range(len(result) + 1):           # höchstens eine Verschiebung je Fenster, dann neu einsortieren
        _, errs = window_frames(result, tp_dict, fps, cfg)
        if errs:
            return result                       # ungültige Fenster — nichts anfassen, window_frames() meldet es
        frames = _window_positions(result, tp_dict, fps)
        reihenfolge = sorted(range(len(result)), key=lambda i: frames[i][0])
        pos, verschoben = 0, False
        for i in reihenfolge:
            a_f, b_f = frames[i]
            w = result[i]
            strecke_s = (a_f - pos) / fps
            if a_f > pos and strecke_s < min_len_s - EPS and w.beat_nr not in protect and not w.voll:
                verschieb_s = min_len_s - strecke_s
                tb = beats[w.beat_nr]
                b_in, b_out = int(tb["rec_in_f"]), int(tb["rec_out_f"])
                neuer_offset_s = round(w.offset_s + verschieb_s, 3)
                neues_a = b_in + seconds_to_frames(neuer_offset_s, fps)
                dauer_f = seconds_to_frames(w.dauer_s, fps)
                praefix = f"{w.grund} — " if w.grund else ""
                if neues_a + dauer_f > b_out:
                    result[i] = Fenster(w.beat_nr, 0.0, None, True,
                                        f"{praefix}auf „voll“ gesetzt, weil ein Verschieben über das Beat-Ende "
                                        f"ragen würde (Strecke davor sonst {_s(strecke_s)} statt {_s(min_len_s)}).")
                else:
                    result[i] = Fenster(w.beat_nr, neuer_offset_s, w.dauer_s, False,
                                        f"{praefix}Fenster um {_s(verschieb_s)} verschoben, damit die Strecke davor "
                                        f"{_s(min_len_s)} hat.")
                verschoben = True
                break                            # Positionen können sich verschoben haben — von vorn prüfen
            pos = max(pos, b_f)
        if not verschoben:
            break
    return result


def stretches(win_frames: list[dict], total_frames: int) -> list[dict]:
    out, pos, nr = [], 0, 0
    for w in sorted(win_frames, key=lambda x: x["a_f"]):
        if w["a_f"] > pos:
            nr += 1
            out.append({"nr": nr, "von_f": pos, "bis_f": int(w["a_f"])})
        pos = max(pos, int(w["b_f"]))
    if total_frames > pos:
        nr += 1
        out.append({"nr": nr, "von_f": pos, "bis_f": int(total_frames)})
    return out


def face_share(win_frames: list[dict], total_frames: int) -> float:
    return sum(int(w["b_f"]) - int(w["a_f"]) for w in win_frames) / float(total_frames) if total_frames else 0.0


# --------------------------------------------------------------------------- #
# Raster (für Claude)
# --------------------------------------------------------------------------- #

def raster(tp_dict: dict, cl: Cutlist, cfg: dict, plan: LayoutPlan | None = None) -> dict:
    fps = float(tp_dict["fps"])
    total = int(tp_dict["total_frames"])
    wins = effective_windows(plan, tp_dict, cl, cfg)
    wf, errs = window_frames(wins, tp_dict, fps, cfg)
    cl_beats = {b.nr: b for b in cl.beats}
    min_len_s = float(cfg["shot_len_s"][0])
    by_a = {w["a_f"]: w for w in wf}    # Fenster, das direkt NACH einer Strecke beginnt
    by_b = {w["b_f"]: w for w in wf}    # Fenster, das direkt VOR einer Strecke endet
    out_st = []
    for st in stretches(wf, total):
        dauer_s = (st["bis_f"] - st["von_f"]) / fps
        if dauer_s < min_len_s - EPS:
            # adjust_short_stretches() konnte das nicht selbst beheben: entweder ist das folgende Fenster ein
            # Plan-Fenster (Claudes Verantwortung), oder es gibt keins mehr (Strecke am Timeline-Ende).
            next_w, prev_w = by_a.get(st["bis_f"]), by_b.get(st["von_f"])
            abhilfen = []
            if next_w is not None:
                abhilfen.append(f"Fenster Beat #{next_w['beat_nr']} per offset_s nach hinten schieben")
            if prev_w is not None and prev_w["voll"]:
                abhilfen.append(f"Beat #{prev_w['beat_nr']} statt voll eine dauer_s geben")
            errs.append(f"Strecke {st['nr']} ist {_s(dauer_s)} kurz — {' oder '.join(abhilfen) or 'Fenster anpassen'}.")
        beats = []
        for tb in _beats_sorted(tp_dict):
            if int(tb["rec_in_f"]) < st["bis_f"] and int(tb["rec_out_f"]) > st["von_f"]:
                cb = cl_beats.get(str(tb["nr"]))
                beats.append({"nr": str(tb["nr"]), "typ": tb.get("typ"), "person": tb.get("person"), "szene": cb.szene if cb else "",
                              "von_s": round(max(int(tb["rec_in_f"]), st["von_f"]) / fps, 2), "bis_s": round(min(int(tb["rec_out_f"]), st["bis_f"]) / fps, 2),
                              "bild": cb.bild_hinweis if cb else "", "kommentar": cb.kommentar if cb else "",
                              "text": (cb.text or " ".join(c.text for c in cb.cuts)) if cb else ""})
        hinweise = [f"#{b['nr']} {b['szene']}: {b['bild']}" + (f" — {b['kommentar']}" if b["kommentar"] else "") for b in beats if b["bild"] or b["kommentar"]]
        out_st.append({**st, "von_s": round(st["von_f"] / fps, 2), "bis_s": round(st["bis_f"] / fps, 2),
                       "dauer_s": round((st["bis_f"] - st["von_f"]) / fps, 2), "beats": beats, "hinweise": hinweise})
    share = face_share(wf, total)
    lo_h, hi_h = (float(x) for x in cfg["face_share_hard"])
    if share < lo_h - 1e-9 or share > hi_h + 1e-9:
        errs.append(f"Gesichtsanteil {share * 100:.1f} % außerhalb {lo_h * 100:.0f}–{hi_h * 100:.0f} % — Fenster "
                    f"kürzen/verlängern (dauer_s) oder voll-Beats eine dauer_s geben.")
    return {"fps": fps, "total_frames": total, "gesamt_s": round(total / fps, 2), "fenster": wf,
            "fenster_plan": [w.to_dict() for w in wins], "fehler": errs, "strecken": out_st,
            "gesicht_anteil": round(share, 4), "ziel_gesicht": list(cfg["face_share"])}


def render_raster_md(r: dict, cl: Cutlist, tp_dict: dict) -> str:
    fps = float(r["fps"])
    lines = [f"# Raster — {cl.video}", "",
             f"Gesamt {r['gesamt_s']} s · Gesicht {r['gesicht_anteil'] * 100:.1f} % (Ziel {int(r['ziel_gesicht'][0] * 100)}–{int(r['ziel_gesicht'][1] * 100)} %) · "
             f"{len(r['fenster'])} Fenster · {len(r['strecken'])} Strecken", ""]
    if r["fehler"]:
        lines += ["## Fehler in den Fenstern", ""] + [f"- {e}" for e in r["fehler"]] + [""]
    lines += ["## Fenster (Sprecher sichtbar)", "", "| Beat | von | bis | Dauer | voll |", "|---|---|---|---|---|"]
    for w in r["fenster"]:
        lines.append(f"| #{w['beat_nr']} | {w['a_f'] / fps:.2f} s | {w['b_f'] / fps:.2f} s | {(w['b_f'] - w['a_f']) / fps:.2f} s | {'ja' if w['voll'] else ''} |")
    lines += ["", "## Strecken (mit B-Roll lückenlos zu füllen)", ""]
    for st in r["strecken"]:
        lines.append(f"### Strecke {st['nr']}: {st['von_s']} – {st['bis_s']} s ({st['dauer_s']} s)")
        for b in st["beats"]:
            lines.append(f"- #{b['nr']} {b['szene']} ({b['typ']}{', ' + b['person'] if b['person'] else ''}) {b['von_s']}–{b['bis_s']} s: "
                         f"{b['text'][:160]}")
        for h in st["hinweise"]:
            lines.append(f"  - Hinweis: {h}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Platzierung
# --------------------------------------------------------------------------- #

def length_bounds_v2(beat: Beat | None, cfg: dict, tempo: int = 1) -> tuple[float, float, str]:
    text = f"{beat.kommentar} {beat.bild_hinweis}" if beat else ""
    if _FAST_CUTS.search(text):
        lo, hi = cfg["fast_cuts_len_s"]
        return float(lo), float(hi), "Schnelle Cuts"
    if beat is not None and beat.typ != "oton":
        lo, hi = cfg["montage_len_s"]
        return float(lo), float(hi), "Montage"
    lo, hi = cfg["shot_len_s"]
    if tempo > 1:
        hi = max(float(hi), float(cfg.get("shot_len_slow_max_s", hi)))
    return float(lo), float(hi), "O-Ton"


def section_for(clip: dict, t_s: float) -> dict | None:
    for a in clip.get("abschnitte") or []:
        if float(a["von_s"]) - EPS <= t_s <= float(a["bis_s"]) + EPS:
            return a
    return None


def _perspektive(a: dict | None) -> str:
    return f"{(a or {}).get('perspektive_hoehe', '?')}/{(a or {}).get('perspektive_ansicht', '?')}"


def place_shots(plan: LayoutPlan, tp_dict: dict, index: dict, cfg: dict, fps: float,
                strecken_frames: list[dict] | None = None, cl: Cutlist | None = None) -> tuple[list[dict], list[str]]:
    fps = float(fps)
    by_path = _index_by_path(index)
    if strecken_frames is None:
        wins = effective_windows(plan, tp_dict, cl, cfg) if cl is not None else list(plan.fenster)
        wf, werrs = window_frames(wins, tp_dict, fps, cfg)
        strecken_frames = stretches(wf, int(tp_dict["total_frames"]))
    st_by_nr = {s["nr"]: s for s in strecken_frames}
    errs: list[str] = []
    placed: list[dict] = []
    for st in plan.strecken:
        frames = st_by_nr.get(st.nr)
        if frames is None:
            errs.append(f"Strecke {st.nr}: unbekannt — Nummern aus `--raster` übernehmen ({sorted(st_by_nr)}).")
            continue
        pos, ende = int(frames["von_f"]), int(frames["bis_f"])
        shots = [(i, j, sz, sh) for i, sz in enumerate(st.szenen, 1) for j, sh in enumerate(sz.shots, 1)]
        if not shots:
            errs.append(f"Strecke {st.nr} ({frames['von_f'] / fps:.2f}–{frames['bis_f'] / fps:.2f} s) ist leer — Schwarz.")
            continue
        strecke_start = len(placed)
        for k, (i, j, sz, sh) in enumerate(shots):
            path, err = resolve_clip_ref(sh.clip, index)
            if path is None:
                errs.append(f"Strecke {st.nr} Szene {i} Shot {j}: {err}")
                continue
            c = by_path[path]
            cfps = float(c.get("fps") or fps)
            if sh.tempo > 1 and abs(cfps - sh.tempo * fps) > 0.01:
                errs.append(f"Strecke {st.nr} Szene {i} Shot {j} ({c['datei']}): tempo {sh.tempo} braucht {sh.tempo * fps:g} fps, "
                            f"der Clip hat {cfps:g} fps.")
                continue
            n_tl = seconds_to_frames(sh.out_s - sh.in_s, fps) * sh.tempo
            last = k == len(shots) - 1
            if last:
                n_tl = ende - pos
            elif pos + n_tl > ende:
                errs.append(f"Strecke {st.nr}: Shot {j} in Szene {i} ({c['datei']}) ragt über das Streckenende ({ende / fps:.2f} s) — "
                            f"Shots kürzen oder einen weglassen.")
                break
            rest = n_tl
            r = rest % sh.tempo if last and sh.tempo > 1 else 0
            n_tl -= n_tl % sh.tempo
            if n_tl <= 0:
                errs.append(f"Strecke {st.nr}: für den letzten Shot ({c['datei']}) bleibt keine Zeit — vorherige Shots kürzen.")
                break
            if r > 0:
                # Reststrecke (rest) ist kein Vielfaches von tempo: die überzähligen r Frames bekommt der nächste
                # vorherige Shot mit tempo 1 in derselben Strecke (der läuft in Timeline-Frames = Quell-Frames,
                # kann also beliebig um r verlängert werden); alle dazwischenliegenden Shots rücken um r auf.
                donor_idx = next((idx_ for idx_ in range(len(placed) - 1, strecke_start - 1, -1) if placed[idx_]["tempo"] == 1), None)
                if donor_idx is None:
                    errs.append(f"Strecke {st.nr}: die Reststrecke ({rest} Frames) ist kein Vielfaches von tempo {sh.tempo} und kein "
                                f"Shot mit tempo 1 kann den Rest aufnehmen — Strecke mit einem tempo-1-Shot beenden.")
                    break
                donor = placed[donor_idx]
                donor_c = by_path[donor["clip"]]
                donor_cfps = float(donor_c.get("fps") or fps)
                donor_n_tl = donor["rec_out_f"] - donor["rec_in_f"] + r
                donor["rec_out_f"] += r
                donor_src_n = int(round(donor_n_tl * donor_cfps / fps))
                donor["src_out_f"] = donor["src_in_f"] + donor_src_n
                donor["out_s"] = round(donor["in_s"] + donor_src_n / donor_cfps, 3)
                donor["roh_out_f"] = donor["rec_out_f"]
                for nxt in placed[donor_idx + 1:]:
                    nxt["rec_in_f"] += r
                    nxt["rec_out_f"] += r
                    nxt["roh_out_f"] += r
                pos += r
            src_n = n_tl if sh.tempo > 1 else int(round(n_tl * cfps / fps))
            src_in = seconds_to_frames(sh.in_s, cfps)
            out_s = round(sh.in_s + src_n / cfps, 3)
            mid = section_for(c, (sh.in_s + out_s) / 2)
            placed.append({"strecke": st.nr, "szene_i": i, "shot_i": j, "clip": path, "name": c["datei"],
                           "ordner": f"{c.get('standort') or ''}/{c.get('ordner') or ''}".strip("/"), "standort": c.get("standort"),
                           "in_s": sh.in_s, "out_s": out_s, "out_s_plan": sh.out_s, "tempo": sh.tempo, "clip_fps": cfps,
                           "rec_in_f": pos, "rec_out_f": pos + n_tl,
                           "src_in_f": src_in, "src_out_f": src_in + src_n, "roh_out_f": pos + n_tl // sh.tempo, "letzter": last,
                           "grund": sh.grund, "abweichung": sh.abweichung, "abweichung_grund": sh.abweichung_grund,
                           "ausnahme": sz.ausnahme, "szene_ordner": sz.ordner, "szene_grund": sz.grund,
                           "einstellung": (mid or {}).get("einstellung"), "perspektive": _perspektive(mid),
                           "brennweite": (mid or {}).get("brennweite"), "setup_hash": (mid or {}).get("setup_hash") or "",
                           "q": (mid or {}).get("qualitaet"), "nachlauf_fehlt": mid is None or any(k not in mid for k in ("einstellung", "perspektive_hoehe", "perspektive_ansicht", "brennweite"))})
            pos += n_tl
    return placed, errs


def _quellbereich_s(p: dict, fps: float) -> tuple[float, float]:
    """Der Quellbereich (Sekunden im Clip), den ein platzierter Shot wirklich nutzt: die Quellframes aus
    ``place_shots`` (``src_in_f``/``src_out_f``), geteilt durch die Bildrate des Clips.

    Bewusst nicht ``TM.genutzter_quellbereich_s()``: die kennt nur das boolesche ``langsam`` (Faktor 0,5) und
    trifft damit allein ``tempo`` 2 (``clip_fps`` = 2 × ``ziel_fps``). Bei ``tempo`` 4 — 100-fps-Clip in 25 fps,
    ``place_shots`` setzt dort ``src_n = n_tl`` — liefert sie den doppelten Bereich: ein Shot, der 0,0–1,0 s
    nutzt, würde als 0,0–2,0 s geprüft, und eine Zoomfahrt, die in der Timeline nie zu sehen ist, käme als
    harter Fehler zurück. Der Helfer selbst bleibt unverändert; er hat andere Aufrufer (Vorlage 6d).
    """
    cfps = float(p.get("clip_fps") or fps)
    return p["src_in_f"] / cfps, p["src_out_f"] / cfps


def _kb_am_schnitt(p: dict, tele: list[dict] | None, fps: float, seite: str) -> float | None:
    """Scheinbare KB-Brennweite am Anfang bzw. Ende eines platzierten Shots; None ohne Verlauf.
    Bei Zeitlupe zählt der tatsächlich genutzte Quellbereich (wie 6d)."""
    if not tele:
        return None
    rec = TM.finden(tele, p["clip"])
    if not rec:
        return None
    von, bis = _quellbereich_s(p, fps)
    return TM.kb_am(rec, bis if seite == "ende" else von, seite=seite)


def _hat_abschnitts_maengel(c: dict) -> bool:
    """True, wenn mindestens ein Abschnitt den Schlüssel ``maengel`` trägt (Index ab Spec 2026-09-23).
    Eine leere Liste ist eine Aussage („hier ist nichts"), ein fehlender Schlüssel ist keine."""
    return any("maengel" in a for a in (c.get("abschnitte") or []))


def _abschnitte_im_bereich(c: dict, von_s: float, bis_s: float) -> list[dict]:
    """Abschnitte, die das Intervall wirklich überlappen — ein Shot über eine echte Abschnittsgrenze muss beide
    erfüllen, aber reines Berühren an der Grenze zählt nicht (Review-Fund I1): ein Shot, der exakt dort beginnt,
    wo ein Nachbarabschnitt endet, erbt dessen Mängel sonst fälschlich (FX3_8636). Inward-Toleranz wie
    ``_section_quality`` in ``broll_plan.py``."""
    return [a for a in (c.get("abschnitte") or [])
            if float(a["von_s"]) < bis_s - EPS and float(a["bis_s"]) > von_s + EPS]


def _stabil_bereiche(c: dict) -> list[tuple[float, float]]:
    """Gemessene stabile Bereiche aller Abschnitte, NUR an echten Abschnittsgrenzen zusammengelegt (Review-Fund
    I2, korrigiert durch B1): Stufe 2b schneidet jeden Lauf an der Abschnittsgrenze, ein Shot darf über die
    Grenze laufen, wenn beide Seiten dort stabil sind (FX3_8641: 0–2 s + 2–4,8 s → 0–4,8 s). Zwei Stücke
    DESSELBEN Abschnitts, die sich an einer Bewegungsspitze innerhalb des Abschnitts nur zufällig berühren,
    legen sich NICHT zusammen — siehe ``_merge_an_abschnittsgrenzen()`` in ``broll_plan.py``, dieselbe Regel wie
    in ``_usable_spans()``."""
    stuecke = []
    for a in (c.get("abschnitte") or []):
        a_von, a_bis = float(a["von_s"]), float(a["bis_s"])
        stuecke += [(float(x), float(z), abs(float(x) - a_von) <= EPS, abs(float(z) - a_bis) <= EPS)
                   for x, z, *_ in (a.get("stabil") or [])]
    return _merge_an_abschnittsgrenzen(stuecke)


def _in_stabil(c: dict, von_s: float, bis_s: float) -> bool:
    """Liegt der genutzte Quellbereich ganz in einem gemessenen, an Abschnittsgrenzen zusammengelegten stabilen
    Bereich?"""
    return any(x - EPS <= von_s and bis_s <= z + EPS for x, z in _stabil_bereiche(c))


def verify_layout(plan: LayoutPlan, tp_dict: dict, index: dict, cl: Cutlist, cfg: dict, fps: float,
                  tele: list[dict] | None = None) -> VerifyResult:
    """Harte Prüfung nach Spec v2 Abschnitt 3.3."""
    r = VerifyResult()
    fps = float(fps or tp_dict.get("fps") or 0)
    if fps <= 0:
        r.errors.append("Bildrate fehlt (fps ≤ 0) — timeline.json prüfen.")
        return r
    for key in ("face_share", "face_share_hard", "window_first_s", "window_s", "window_min_s", "window_max_s", "full_face_beat_max_s",
                "full_face_keywords", "shot_len_s", "shot_len_slow_max_s", "montage_len_s", "fast_cuts_len_s", "scene_min_shots",
                "scene_short_stretch_s", "setup_hash_min_distance", "max_exceptions_warn", "forbidden_maengel"):
        if key not in cfg:
            r.errors.append(f"Config: broll.{key} fehlt — profile/default.yaml (v2) prüfen.")
    # Der telemetrie:-Block liegt in defaults.yaml neben broll:, nicht darunter — das Skript mischt ihn dazu.
    # Fehlt er oder eine seiner Schwellen, fielen die drei Telemetrie-Regeln still auf Code-Defaults zurück
    # (genau die Fehlerklasse, die in diesem Zweig schon einmal zugeschlagen hat: eine Kalibrierung bliebe
    # wirkungslos, ohne dass es jemand merkt). Fehlende Telemetrie-DATEN bleiben erlaubt, ein fehlender
    # CONFIG-Block nicht.
    tcfg = cfg.get("telemetrie")
    if not isinstance(tcfg, dict):
        r.errors.append("Config: telemetrie fehlt — defaults.yaml prüfen (der Block liegt neben broll:, nicht darunter).")
    else:
        for key in ("brennweite_gleich_max", "bewegung_rand_s", "bewegung_spitze_faktor", "ruhig_max_px", "fenster_s"):
            if key not in tcfg:
                r.errors.append(f"Config: telemetrie.{key} fehlt — defaults.yaml prüfen.")
    if r.errors:
        return r
    total = int(tp_dict["total_frames"])
    wins = effective_windows(plan, tp_dict, cl, cfg)
    wf, werrs = window_frames(wins, tp_dict, fps, cfg)
    r.errors += werrs
    share = face_share(wf, total)
    lo_h, hi_h = cfg["face_share_hard"]
    lo, hi = cfg["face_share"]
    if share < float(lo_h) - 1e-9 or share > float(hi_h) + 1e-9:
        r.errors.append(f"Gesichtsanteil {share * 100:.1f} % außerhalb {float(lo_h) * 100:.0f}–{float(hi_h) * 100:.0f} % — Fenster anpassen.")
    elif share < float(lo) - 1e-9 or share > float(hi) + 1e-9:
        r.warnings.append(f"Gesichtsanteil {share * 100:.1f} % außerhalb des Ziels {float(lo) * 100:.0f}–{float(hi) * 100:.0f} %.")
    st_frames = stretches(wf, total)
    placed, perrs = place_shots(plan, tp_dict, index, cfg, fps, strecken_frames=st_frames)
    r.errors += perrs
    planned = {st.nr for st in plan.strecken}
    for s in st_frames:
        if s["nr"] not in planned:
            r.errors.append(f"Strecke {s['nr']} ({s['von_f'] / fps:.2f}–{s['bis_f'] / fps:.2f} s) fehlt im Plan — leer = Schwarz.")
    by_path = _index_by_path(index)
    cl_beats = {b.nr: b for b in cl.beats}
    forbidden = set(cfg["forbidden_maengel"])
    uses: dict[str, list[str]] = {}
    n_exc = 0
    ohne_datensatz = 0          # Shots, für die 3b/3c gar nicht laufen konnten (Fix-Welle, Fund I2)
    alte_schwellen = 0          # Shots, für die 3b/3c übersprungen wurden (Fix-Welle, Fund I4)
    ohne_abschnitts_maengel = 0     # Clips aus einem Index vor Spec 2026-09-23 (Sperre bleibt clip-weit)
    hash_heute = TM.config_hash(tcfg)
    for p in placed:
        tag = f"Strecke {p['strecke']} Szene {p['szene_i']} Shot {p['shot_i']} ({p['name']} {p['in_s']:g}–{p['out_s']:g}s)"
        c = by_path[p["clip"]]
        uses.setdefault(p["clip"], []).append(f"Strecke {p['strecke']}")
        if p["nachlauf_fehlt"]:
            r.errors.append(f"{tag}: Abschnittsfelder fehlen (Einstellung/Perspektive/Brennweite) — erst autocut_index_sections.py (Nachlauf).")
        if p["out_s"] <= p["in_s"] or p["in_s"] < 0:
            r.errors.append(f"{tag}: ungültiges Intervall.")
            continue
        if c.get("dauer_s") is not None and p["out_s"] > float(c["dauer_s"]) + EPS:
            r.errors.append(f"{tag}: liegt außerhalb des Clips (0–{_s(c['dauer_s'])}).")
        # Stabile Bereiche aus einer Messung mit anderen Schwellen zählen nicht — dann verhält sich der Clip
        # wie ohne Telemetrie (Spec 2026-09-23, Randfälle).
        frisch = _stabil_frisch(c, hash_heute)
        spans = _usable_spans(c, stabil=frisch)
        if not any(a - EPS <= p["in_s"] and p["out_s"] <= z + EPS for a, z in spans):
            r.errors.append(f"{tag}: liegt in keinem verwendbaren Abschnitt und in keinem gemessenen stabilen Bereich "
                            f"(erlaubt: {', '.join(f'{a:g}–{z:g}s' for a, z in spans) or 'nichts'}).")
        q_von, q_bis = _quellbereich_s(p, fps)
        stabil_ok = frisch and _in_stabil(c, q_von, q_bis)
        if _hat_abschnitts_maengel(c):
            # Sperre je Abschnitt: der Index verortet den Mangel, der Prüfer darf ihn nicht auf den Clip weiten.
            # „Wackler" entfällt im gemessenen stabilen Bereich — das ist das Überstimmen aus Spec 2026-09-23.
            for a in _abschnitte_im_bereich(c, p["in_s"], p["out_s"]):
                sperrend = set(a.get("maengel") or []) & forbidden
                if stabil_ok:
                    sperrend -= {"Wackler"}
                for m in sorted(sperrend):
                    r.errors.append(f"{tag}: Abschnitt {float(a['von_s']):g}–{float(a['bis_s']):g}s hat den Mangel "
                                    f"„{m}“ — gesperrt.")
        else:
            ohne_abschnitts_maengel += 1
            maengel = set(c.get("maengel") or [])
            if (c.get("personen") or {}).get("blick_in_kamera"):
                maengel.add("Blick in Kamera")
            for m in sorted(maengel & forbidden):
                r.errors.append(f"{tag}: Clip hat den Mangel „{m}“ — gesperrt.")
        if p["q"] is not None and int(p["q"]) < 3:
            r.warnings.append(f"{tag}: Abschnitt mit Qualität {p['q']} — Bild prüfen.")
        beat = beat_at(tp_dict, p["rec_in_f"])
        cb = cl_beats.get(str(beat["nr"])) if beat else None
        lo_l, hi_l, regel = length_bounds_v2(cb, cfg, p["tempo"])
        dauer = (p["rec_out_f"] - p["rec_in_f"]) / fps
        toleranz = 0.5 if p["letzter"] else 0.0
        if dauer < lo_l - EPS:
            r.errors.append(f"{tag}: {_s(dauer)} zu kurz — {regel}: {_s(lo_l)}–{_s(hi_l)}.")
        elif dauer > hi_l + toleranz + EPS:
            hinweis = " (letzter Shot darf bis 0,5 s länger sein)" if p["letzter"] else ""
            r.errors.append(f"{tag}: {_s(dauer)} zu lang — {regel}: {_s(lo_l)}–{_s(hi_l)}{hinweis}.")
        nur = {int(m) for m in _NUR_STANDORT.findall(f"{cb.kommentar} {cb.bild_hinweis}")} if cb else set()
        snr = _standort_nr(c.get("standort"))
        if nur and snr is not None and snr not in nur:
            r.errors.append(f"{tag}: Plan verlangt „Nur S{'/S'.join(str(n) for n in sorted(nur))}“, Clip liegt in {c.get('standort')}.")
        for sp in cl.sperren:
            if sp.clip == p["clip"] and p["in_s"] < sp.bis_s and sp.von_s < p["out_s"]:
                r.errors.append(f"{tag}: überschneidet die Sperre {sp.von_s:g}–{sp.bis_s:g}s ({sp.grund or 'ohne Grund'}).")
        if p["abweichung"] and not p["abweichung_grund"].strip():
            r.errors.append(f"{tag}: abweichung=true ohne abweichung_grund.")
        rec = TM.finden(tele, p["clip"]) if tele else None
        if rec is not None and rec.get("fehler"):
            rec = None          # Messfehler: zooms und fenster sind leer, beide Regeln würden still durchwinken
        if rec is None:
            # Kein verwertbarer Datensatz — Teil-Lauf der Telemetrie, Material von NAS auf SSD gewandert
            # (finden() fällt auf den Dateinamen zurück und schweigt bei Mehrdeutigkeit) oder telemetrie.json
            # unlesbar (laden() gibt dann []). Bisher entfielen 3b und 3c hier spurlos: der einzige Zähler
            # zählte Schnittpaare und nannte nur die Brennweitenregel (Fix-Welle, Fund I2).
            ohne_datensatz += 1
        # Mit anderen Schwellen gemessen: `zoom_schnell_proz_s` und Verwandte stehen NICHT in
        # TM.OHNE_MESSWIRKUNG, das Urteil „schnell" und die Fenster-Reihe stammen also aus den Schwellen zur
        # Messzeit. 3b und 3c würden dann Fehler melden, die die heutige Konfiguration gar nicht erzeugt — beide
        # entfallen für diesen Shot und werden gezählt (Fix-Welle, Fund I4; Entscheidung des Users, bewusst
        # genauer als die Spec, die pauschal alle drei Regeln übersprang). Regel 3a läuft weiter: sie liest
        # `kb_verlauf`, also Rohdaten, und `brennweite_gleich_max` steht in OHNE_MESSWIRKUNG.
        veraltet = rec is not None and rec.get("config_hash") != hash_heute
        if veraltet:
            alte_schwellen += 1
        if rec is not None and not veraltet:
            # außerhalb der abweichung-Bedingung: Regel 3c rechnet auf denselben Grenzen weiter
            von, bis = _quellbereich_s(p, fps)
            if not p["abweichung"]:
                for z in TM.zooms_im_bereich(rec, von, bis):
                    r.errors.append(f"{tag}: schneller Zoom im genutzten Bereich ({z['von_mm']:g} → {z['bis_mm']:g} mm, "
                                    f"Spitze {z['tempo_max']:.0f} %/s) — anderen Bereich wählen oder `abweichung` mit Grund.")
            rand = float(tcfg["bewegung_rand_s"])
            faktor = float(tcfg["bewegung_spitze_faktor"])
            ruhig = float(tcfg["ruhig_max_px"])
            fen_s = float(rec.get("fenster_s") or tcfg["fenster_s"])
            # Der geweitete Bereich ist nur lückenlos, solange schritt_s (1,0) <= 2 × bewegung_rand_s (1,0) gilt —
            # aktuell exakt der Grenzfall. Ein kleineres bewegung_rand_s als schritt_s / 2 ließe zwischen zwei
            # Fenster-Startzeiten stille Lücken, in denen eine Spitze nie geprüft würde.
            for t_s, bw in TM.bewegung_spitzen(rec, von - rand, bis + rand):
                if min(abs(t_s - von), abs(t_s - bis)) > rand:
                    continue
                grund_px = TM.bewegung_grundniveau(rec, t_s)
                if grund_px is None:
                    continue
                # Untergrenze bei ruhig_max_px: VORLÄUFIGER SOCKEL OHNE EIGENEN BELEG, von der wackeln-Schwelle
                # geborgt. ruhig_max_px ist überall sonst eine Schwelle für `wackeln` (Zittern), hier steht ihr
                # aber `bewegung` (Schwenkweg) gegenüber — zwei verschiedene Größen. Auf bewegtem Material greift
                # der Sockel deshalb kaum; er wirkt praktisch nur auf Stativmaterial, wo er den rein
                # multiplikativen Vergleich davor bewahrt, schon bei winzigen Ausreißern zu feuern (Fix-Runde 1
                # zu Task 5), und den Fall Grundniveau exakt 0,0 abfängt (der Faktor wäre unendlich).
                # Wer das kalibriert, muss das wissen: der Wert 0,15 ist hier nicht hergeleitet.
                basis = max(grund_px, ruhig)
                if bw >= faktor * basis:
                    schnittgrenze = von if abs(t_s - von) <= abs(t_s - bis) else bis
                    r.warnings.append(f"{tag}: Schnittgrenze bei {schnittgrenze:g} s im Clip liegt in einer Bewegungsspitze — "
                                      f"gemessen im Fenster {t_s:g}–{t_s + fen_s:g} s (Bewegung {bw:g} gegen Basis "
                                      f"{basis:g}, Sockel ruhig_max_px {ruhig:g}) — Hinweis, Schwellen unkalibriert.")
            # Spec 2026-09-23: der Abschnitt ist verwendbar, der genutzte Bereich aber nicht als ruhig gemessen.
            # Bewusst nur eine Warnung — ein gewollter Schwenk ist nicht ruhig und bleibt erlaubt. Nur in einem
            # verwendbar-Abschnitt (Review-Fund I2): ein bereits verworfener Abschnitt ohne stabilen Bereich hat
            # schon den Lage-Fehler und braucht diese zusätzliche Warnung nicht.
            if (frisch and not stabil_ok
                    and any(a.get("verwendbar") for a in _abschnitte_im_bereich(c, p["in_s"], p["out_s"]))):
                bw = TM.bewegung_max_im_bereich(rec, von, bis, fen_s)
                bw_txt = "–" if bw is None else f"{bw:.1f}".replace(".", ",")
                r.warnings.append(f"{tag}: Bereich nicht als stabil gemessen (Bewegung max {bw_txt}) — "
                                  f"für einen ruhigen Einsetzer einen `stabil`-Bereich wählen.")
        if not p["grund"].strip():
            r.warnings.append(f"{tag}: ohne grund.")
        if p["tempo"] == 4:
            r.warnings.append(f"{tag}: tempo 4 — nur für bewusst langsame Momente.")
    for clip, wo in uses.items():
        if len(wo) > 1:
            r.errors.append(f"Clip {Path(clip).name} wird zweimal verwendet ({', '.join(wo)}) — kein Clip doppelt im Video.")
    # Szenen: ≥ 3 Shots aus einem Ordner, sonst Ausnahme
    min_shots = int(cfg["scene_min_shots"])
    short = float(cfg["scene_short_stretch_s"])
    st_len = {s["nr"]: (s["bis_f"] - s["von_f"]) / fps for s in st_frames}
    for st in plan.strecken:
        for i, sz in enumerate(st.szenen, 1):
            tag = f"Strecke {st.nr} Szene {i} ({sz.ordner})"
            if sz.ausnahme.strip():
                n_exc += 1
                continue
            if len(sz.shots) < min_shots and st_len.get(st.nr, 99) >= short:
                r.errors.append(f"{tag}: nur {len(sz.shots)} Shots — eine Szene braucht mindestens {min_shots} Shots aus einem Ordner "
                                f"(oder `ausnahme` mit Grund).")
            ordner = {p["ordner"] for p in placed if p["strecke"] == st.nr and p["szene_i"] == i}
            if len(ordner) > 1:
                r.errors.append(f"{tag}: Shots aus verschiedenen Ordnern ({', '.join(sorted(ordner))}) — Szene = ein Ordner, sonst `ausnahme`.")
            einst = [p["einstellung"] for p in placed if p["strecke"] == st.nr and p["szene_i"] == i]
            if len(einst) >= 2 and len(set(einst)) == 1:
                r.warnings.append(f"{tag}: alle Shots in Einstellung {einst[0]} — Einstellungswechsel fehlt.")
    if n_exc > int(cfg["max_exceptions_warn"]):
        r.warnings.append(f"{n_exc} Ausnahmen von der Szenen-Regel — mehr als {cfg['max_exceptions_warn']}.")
    # Cut-Flow zwischen zwei B-Roll-Shots, die in der Timeline WIRKLICH aneinanderstoßen (a endet exakt dort, wo
    # b beginnt) — nicht zwischen irgendwelchen zwei Shots derselben Strecke. Die frühere Annahme, B-Roll-Shots
    # stießen innerhalb einer Strecke immer lückenlos aneinander und nur zwischen zwei Strecken liege ein
    # Sprecher-Fenster, war falsch: an echten Daten (Charge MEK, Abnahme 23.09.) lagen 8 von 24 Lücken INNERHALB
    # einer Strecke (1,0–1,48 s), mit A-Roll dazwischen — die beiden Shots bilden dort gar keinen Schnitt, also darf
    # keine der drei Regeln (Brennweite, Dublette, Setup-Hash) sie vergleichen. Echte Nachbarschaft in der Timeline
    # (rec_out_f == rec_in_f) schließt „gleiche Strecke" automatisch ein — der alte Streckenvergleich entfällt.
    seq = sorted(placed, key=lambda p: p["rec_in_f"])
    min_dist = int(cfg["setup_hash_min_distance"])
    grenze = float(tcfg["brennweite_gleich_max"])
    ungeprueft = 0
    for a, b in zip(seq, seq[1:]):
        if a["rec_out_f"] != b["rec_in_f"] or a["nachlauf_fehlt"] or b["nachlauf_fehlt"]:
            continue
        kb_a, kb_b = _kb_am_schnitt(a, tele, fps, "ende"), _kb_am_schnitt(b, tele, fps, "anfang")
        gleiche_kb = None
        if kb_a is not None and kb_b is not None:
            # NICHT selbst rechnen: brennweite_abstand() rundet auf vier Stellen, damit 60/50 genau 0,2 ergibt
            # (float: 1.2 - 1 = 0.19999999999999996 wäre sonst fälschlich „gleich")
            gleiche_kb = TM.gleiche_brennweite(kb_a, kb_b, grenze)
            if gleiche_kb:
                r.errors.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} schneiden dieselbe KB-Brennweite "
                                f"({kb_a:g} → {kb_b:g} mm, Abstand {TM.brennweite_abstand(kb_a, kb_b):.0%}) — anderen Shot wählen.")
        else:
            ungeprueft += 1
        # Shot-Doppel nur noch als Rückfall auf die Klassen, wenn mindestens eine KB-Brennweite fehlt. Sind beide
        # bekannt und gleich, hat Regel 3a dasselbe Paar eine Zeile darüber schon gemeldet (mit anderem
        # Abhilfetext) — die Dublettenbedingung ist dann eine echte Teilmenge und kann nichts beitragen; sind
        # beide bekannt und verschieden, sind es ohnehin zwei Setups (Fix-Welle, Fund M1).
        if gleiche_kb is None and a["einstellung"] == b["einstellung"] and a["perspektive"] == b["perspektive"] \
                and a["brennweite"] == b["brennweite"]:
            r.errors.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} haben dieselbe Einstellung ({a['einstellung']}) "
                            f"und Perspektive ({a['perspektive']}) bei gleicher Brennweite — anderer Shot.")
        if a["setup_hash"] and b["setup_hash"] and _hamming(a["setup_hash"], b["setup_hash"]) < min_dist:
            r.warnings.append(f"Strecke {a['strecke']}: {a['name']} → {b['name']} sehen fast gleich aus (Setup-Abstand "
                              f"{_hamming(a['setup_hash'], b['setup_hash'])}).")
    if ohne_abschnitts_maengel:
        r.warnings.append(f"{ohne_abschnitts_maengel} von {len(placed)} Shots aus Clips ohne Abschnitts-Mängel — "
                          f"die Sperre greift dort clip-weit wie vor der Umstellung; "
                          f"autocut_index_broll.py --force holt die Verortung nach.")
    # Review-Fund I4 (Spec, Fehler und Randfälle + Konfiguration): stabil_quelle verortet, mit welchen Schwellen
    # ein Abschnitts stabil-Bereich abgeleitet wurde. Zwei getrennte Fälle je genutztem Clip (nicht je Shot —
    # ein Clip zählt nur einmal): der Config-Hash passt nicht mehr (ruhig_max_px/fenster_s geändert — dieselbe
    # Prüfung wie 3b/3c, Meldung über HINWEIS_SCHWELLEN), oder der Hash passt, aber bewegung_max/stabil_min_s
    # weichen ab (beide in OHNE_MESSWIRKUNG, ändern also den Hash nicht, machen stabil aber trotzdem veraltet —
    # kostenlos aus dem Cache behebbar, deshalb nur ein Hinweis, keine Sperre).
    stabil_ignoriert = 0
    andere_stabil_schwellen = 0
    for clip in uses:
        c_clip = by_path[clip]
        sq = c_clip.get("stabil_quelle")
        if not sq:
            continue
        if not _stabil_frisch(c_clip, hash_heute):
            stabil_ignoriert += 1
        elif (float(sq.get("bewegung_max", tcfg["bewegung_max"])) != float(tcfg["bewegung_max"])
              or float(sq.get("stabil_min_s", tcfg["stabil_min_s"])) != float(tcfg["stabil_min_s"])):
            andere_stabil_schwellen += 1
    if stabil_ignoriert:
        r.warnings.append(f"{stabil_ignoriert} {'Clip' if stabil_ignoriert == 1 else 'Clips'}: stabile Bereiche "
                          f"{TM.HINWEIS_SCHWELLEN} — keine Rettung, keine Bewegungs-Warnung dort; "
                          f"autocut_index_sections.py neu laufen lassen.")
    if andere_stabil_schwellen:
        r.warnings.append(f"{andere_stabil_schwellen} {'Clip' if andere_stabil_schwellen == 1 else 'Clips'} mit "
                          f"anderen Stabil-Schwellen abgeleitet — autocut_index_sections.py erneut laufen lassen.")
    # Eine Meldung je Sachverhalt (Fix-Welle, Fund I2): ohne jede Telemetrie sind „Schnitte ohne
    # Brennweitenverlauf" und „Shots ohne Datensatz" dieselbe Aussage — sie entfallen dann zugunsten einer
    # einzigen Meldung, die alle drei Regeln und die Zahl der Shots nennt.
    if not tele:
        r.warnings.append(f"keine Telemetrie — Brennweiten-, Zoom- und Bewegungsregel für alle {len(placed)} Shots "
                          f"nicht geprüft; autocut_telemetrie.py laufen lassen.")
    else:
        if ungeprueft:
            r.warnings.append(f"{ungeprueft} Schnitte ohne Brennweitenverlauf — Brennweitenregel dort nicht geprüft "
                              f"(Datensatz fehlt oder stammt von vor der Umstellung).")
        if ohne_datensatz:
            r.warnings.append(f"{ohne_datensatz} von {len(placed)} Shots ohne verwertbaren Telemetrie-Datensatz — "
                              f"Zoom- und Bewegungsregel dort nicht geprüft (Telemetrie nur teilweise gelaufen, Clip "
                              f"verschoben oder telemetrie.json unlesbar).")
        if alte_schwellen:
            r.warnings.append(f"{alte_schwellen} von {len(placed)} Shots mit anderen Schwellen gemessen — Zoom- und "
                              f"Bewegungsregel dort übersprungen, die Urteile stammen aus den Schwellen zur Messzeit; "
                              f"autocut_telemetrie.py neu laufen lassen. Die Brennweitenregel gilt weiter (Rohdaten).")
        # veraltete Datensätze der genutzten Clips melden, wie es die Vorlagen 3a/6d tun
        for hinweis in TM.telemetrie_hinweise([TM.finden(tele, p["clip"]) for p in seq], tcfg):
            if alte_schwellen and TM.HINWEIS_SCHWELLEN in hinweis:
                continue        # derselbe Sachverhalt — oben schon mit Shots und übersprungenen Regeln genannt
            r.warnings.append(hinweis)
    return r


def _hamming(a: str, b: str) -> int:
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 64


# --------------------------------------------------------------------------- #
# V3-Items, kompakter Index, Bericht
# --------------------------------------------------------------------------- #

def build_v3_items_v2(placed: list[dict], fps: float) -> tuple[list[Item], list[MarkerSpec]]:
    """Items für die roh-Timeline (tempo-Items enden bei roh_out_f) + Cyan-Marker je Szene + gelbe Marker je Abweichung."""
    items, markers = [], []
    taken: set[int] = set()
    seen_scene: set[tuple[int, int]] = set()
    for p in sorted(placed, key=lambda x: x["rec_in_f"]):
        items.append(Item("V3", p["clip"], int(p["src_in_f"]), int(p["src_out_f"]), int(p["rec_in_f"]), int(p["roh_out_f"]), True,
                          str(p["strecke"]), "broll", True, tempo=int(p["tempo"])))
        key = (p["strecke"], p["szene_i"])
        if key not in seen_scene:
            seen_scene.add(key)
            n = sum(1 for q in placed if (q["strecke"], q["szene_i"]) == key)
            frame = int(p["rec_in_f"])
            while frame in taken:
                frame += 1
            taken.add(frame)
            markers.append(MarkerSpec(frame, f"Szene {p['strecke']}.{p['szene_i']} · {p['szene_ordner']} · {n} Shots",
                                      (p["szene_grund"] or "") + (f"\nAusnahme: {p['ausnahme']}" if p["ausnahme"] else ""), MARKER_COLORS["szene"]))
        if p["abweichung"]:
            frame = int(p["rec_in_f"]) + 1
            while frame in taken:
                frame += 1
            taken.add(frame)
            markers.append(MarkerSpec(frame, f"B-Roll abweichend Strecke {p['strecke']}", f"{p['name']} {p['in_s']:g}–{p['out_s']:g}s: {p['abweichung_grund']}",
                                      MARKER_COLORS["broll"], max(1, int(p["rec_out_f"] - p["rec_in_f"]))))
    return items, markers


def _stabil_frisch(c: dict, hash_heute: str) -> bool:
    """Stammen die stabilen Bereiche des Clips aus einer Messung mit den heutigen Schwellen? Sonst zählen sie
    nicht — dieselbe Regel, die 3b und 3c seit dem 22.09. für veraltete Datensätze anwenden (Spec 2026-09-23)."""
    return bool(hash_heute) and (c.get("stabil_quelle") or {}).get("config_hash") == hash_heute


def stabil_quelle_veraltet(index: dict, cfg: dict) -> int:
    """Clips im Index, deren ``stabil_quelle`` einen anderen Config-Hash trägt als die heutige ``telemetrie:``-
    Config (Review-Fund I4, Spec „Fehler und Randfälle") — für den ``--compact``-Bericht in
    ``autocut_place_broll.py``, der nicht wie ``verify_layout()`` auf einen konkreten Plan eingeschränkt ist,
    sondern den ganzen Index zusammenfasst."""
    hash_heute = TM.config_hash(cfg["telemetrie"])
    return sum(1 for c in index.get("clips") or [] if c.get("stabil_quelle") and not _stabil_frisch(c, hash_heute))


def _abschnitt_kompakt(a: dict) -> dict:
    return {"von_s": a["von_s"], "bis_s": a["bis_s"], "kurz": a.get("beschreibung", ""), "q": a.get("qualitaet"),
            "einstellung": a.get("einstellung"), "perspektive": _perspektive(a), "brennweite": a.get("brennweite"),
            "richtung": a.get("bewegungsrichtung"), "motiv": a.get("hauptmotiv"),
            # gemessen (Spec 2026-09-22): die Auswahl plant auf diesen Werten, nicht auf den Klassen
            "brennweite_mm": a.get("brennweite_mm"), "zoom": a.get("zoom"),
            "bewegungsart": a.get("bewegungsart"), "haltung": a.get("haltung"),
            "bewegung_spitzen": a.get("bewegung_spitzen") or [],
            # Spec 2026-09-23: Mängel dieses Abschnitts und die gemessenen ruhigen Bereiche darin
            "maengel": list(a.get("maengel") or []), "stabil": [list(s) for s in (a.get("stabil") or [])]}


def compact_index_v2(index: dict, cfg: dict) -> list[dict]:
    """Kompakter Index für die Planung. Neben den verwendbaren Abschnitten enthält er die vom Modell verworfenen,
    für die die Messung einen stabilen Bereich ausweist und kein gesperrter Mangel bleibt (Spec 2026-09-23) —
    markiert mit ``gerettet`` und ``trotz`` (die übrigen, nicht sperrenden Mängel). „Wackler" zählt bei geretteten
    Abschnitten nicht als Mangel: sie werden ausschließlich über ihre stabilen Bereiche angeboten, und die sind
    per Definition unter ``ruhig_max_px`` gemessen. Ein Abschnitt ohne ``maengel``-Schlüssel (Index vor der
    Umstellung) wird nie gerettet — dort ist der Grund des Verwerfens nicht bekannt."""
    forbidden = set(cfg["forbidden_maengel"])
    hash_heute = TM.config_hash(cfg["telemetrie"])
    out = []
    for c in index.get("clips") or []:
        frisch = _stabil_frisch(c, hash_heute)
        abschnitte = []
        for a in c.get("abschnitte") or []:
            if a.get("verwendbar"):
                abschnitte.append(_abschnitt_kompakt(a))
                continue
            if not frisch or "maengel" not in a or not (a.get("stabil") or []):
                continue
            uebrig = [m for m in (a.get("maengel") or []) if m != "Wackler"]
            if set(uebrig) & forbidden:
                continue
            abschnitte.append({**_abschnitt_kompakt(a), "gerettet": True, "trotz": uebrig})
        out.append({"ref": clip_ref(c), "datei": c.get("datei"), "ordner": c.get("ordner") or "", "standort": c.get("standort"),
                    "dauer_s": c.get("dauer_s"), "fps": c.get("fps"), "kurz": c.get("beschreibung_kurz", ""),
                    "bewegung": c.get("kamerabewegung"), "tempo": c.get("tempo"), "verwendbar": bool(abschnitte), "abschnitte": abschnitte,
                    "tags": list(c.get("tags") or []), "maengel": list(c.get("maengel") or []), "eignung": list(c.get("eignung") or []),
                    "qualitaet": c.get("qualitaet_gesamt")})
    out.sort(key=lambda x: (str(x["standort"] or ""), x["ordner"], str(x["datei"])))
    return out


def _md(s) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def render_layout_md(plan: LayoutPlan, placed: list[dict], r: dict, index: dict, cl: Cutlist, warnings: list[str] | None = None,
                     build: dict | None = None, tele: list[dict] | None = None) -> str:
    fps = float(r["fps"])
    lines = [f"# B-Roll-Layout — {plan.video or cl.video}", ""]
    if build:
        lines += [f"Timeline: **{build.get('timeline', '–')}** · V3-Items: {build.get('items', '–')} · Marker: {build.get('markers', '–')}", ""]
    lines += [f"**Anteile:** Gesicht {r['gesicht_anteil'] * 100:.1f} % (Ziel {int(r['ziel_gesicht'][0] * 100)}–{int(r['ziel_gesicht'][1] * 100)} %) · "
              f"B-Roll {(1 - r['gesicht_anteil']) * 100:.1f} % · Schwarz 0,0 s · {len(placed)} Shots · "
              f"{len({(p['strecke'], p['szene_i']) for p in placed})} Szenen · {sum(1 for p in placed if p['tempo'] > 1)} Zeitlupen · "
              f"{sum(1 for p in placed if p['abweichung'])} Abweichungen · {len({p['ausnahme'] for p in placed if p['ausnahme']})} Ausnahmen", ""]
    for st in r["strecken"]:
        rows = [p for p in placed if p["strecke"] == st["nr"]]
        lines += [f"## Strecke {st['nr']}: {st['von_s']}–{st['bis_s']} s ({st['dauer_s']} s) · Beats {', '.join('#' + b['nr'] for b in st['beats'])}", "",
                  "| Szene | Position | Clip | Bereich | Tempo | Länge | Einstellung | Perspektive | Brennweite | KB | Grund | Abweichung |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for p in rows:
            kb = _kb_am_schnitt(p, tele, fps, "anfang")
            kb_txt = "–" if kb is None else f"{kb:g} mm".replace(".", ",")
            lines.append(f"| {p['szene_i']} {_md(p['szene_ordner'])}{' (Ausnahme)' if p['ausnahme'] else ''} | {p['rec_in_f'] / fps:.2f} s | {_md(p['name'])} | "
                         f"{p['in_s']:g}–{p['out_s']:g} s | {p['tempo']}× | {_s((p['rec_out_f'] - p['rec_in_f']) / fps)} | {_md(p['einstellung'])} | "
                         f"{_md(p['perspektive'])} | {_md(p['brennweite'])} | {kb_txt} | {_md(p['grund'])} | {('JA: ' + _md(p['abweichung_grund'])) if p['abweichung'] else ''} |")
        lines.append("")
    lines += ["## Fenster", "", "| Beat | von | bis | Dauer |", "|---|---|---|---|"]
    for w in r["fenster"]:
        lines.append(f"| #{w['beat_nr']} | {w['a_f'] / fps:.2f} s | {w['b_f'] / fps:.2f} s | {(w['b_f'] - w['a_f']) / fps:.2f} s{' (voll)' if w['voll'] else ''} |")
    lines.append("")
    if warnings:
        lines += ["## Warnungen", ""] + [f"- {_md(w)}" for w in warnings] + [""]
    if build and build.get("warnings"):
        lines += ["## Hinweise aus dem Bau", ""] + [f"- {_md(w)}" for w in build["warnings"]] + [""]
    return "\n".join(lines)
