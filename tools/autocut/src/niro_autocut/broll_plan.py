"""B-Roll-Plan (Stufe 3): was Claude je Beat auf V3 legen will — und die harte Prüfung davor (Spec 5).

Datei: <Charge>/_intern/autocut/broll_plan.json
    {"video": "video-1-….md",
     "beats": [{"beat_nr": "4", "items": [{"clip": "<Pfad oder Kurzreferenz>", "in_s": 3.0, "out_s": 5.5,
                                           "start_offset_s": 0.0, "grund": "…",
                                           "abweichung": false, "abweichung_grund": ""}]}]}
    (die nackte Beat-Liste aus der Spec wird ebenfalls gelesen; ``video`` bleibt dann leer)

Eingaben der Prüfung: der Plan, ``timeline.json`` (Beat-Positionen aus Stufe 1, Frames relativ zum
Timeline-Anfang), ``broll_index.json`` (Stufe 2), die Cutlist (Typ, Person, Plan-Kommentar, Sperren) und der
``broll:``-Block der Config (Startprofil). Jede Regel ist eine eigene Prüffunktion mit einer eigenen Meldung.
Fehler stoppen den Bau, Warnungen landen im Bericht.

``clip`` darf der volle Pfad aus dem Index sein oder eine Kurzreferenz „Standort 1/Allgemein/FX3_9634.MP4",
„Allgemein/FX3_9634.MP4" oder „FX3_9634.MP4" (eindeutig im Index); ``verify_broll_plan`` ersetzt
Kurzreferenzen durch den vollen Pfad, damit ``build_v3_items`` und der Media-Pool denselben Schlüssel sehen.

Dieses Modul schreibt nur dort, wo ``BrollPlan.save`` aufgerufen wird; es liest keine Dateien außer in
``check_files`` (Existenz-Tests von Original und Proxy) und ``load_profile`` (tools/autocut/profile/).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from .charge import TOOL_ROOT, AutoCutError
from .cutlist import Beat, Cutlist, VerifyResult
from .media import proxy_for, seconds_to_frames
from .timeline_model import MARKER_COLORS, Item, MarkerSpec

PROFILE_DIR = TOOL_ROOT / "profile"
EPS = 0.05                       # Toleranz für Sekundenvergleiche (etwa ein Frame bei 25 fps)
PLACEHOLDER_GAP_WARN_S = 0.5     # Platzhalter gilt als gefüllt, wenn höchstens so viel Lücke bleibt
LOW_QUALITY = 3                  # Abschnitts-Qualität darunter → Warnung
_FAST_CUTS = re.compile(r"schnelle\s+(cuts|schnitte)", re.IGNORECASE)
_NUR_STANDORT = re.compile(r"\bnur\s+S\s?(\d)\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Hilfen
# --------------------------------------------------------------------------- #

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


def _float(d: dict, key: str, wo: str) -> float:
    try:
        return float(d[key])
    except (TypeError, ValueError):
        raise AutoCutError(f"{wo}: Feld '{key}' muss eine Zahl sein, gefunden {d[key]!r}.") from None


def _s(x: float) -> str:
    """Sekunden deutsch mit einer Nachkommastelle (Meldungen, Bericht)."""
    return f"{float(x):.1f}".replace(".", ",") + " s"


def _mmss(frames: int, fps: float) -> str:
    total = int(round(frames / fps)) if fps else 0
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"


def _name(clip: str) -> str:
    return Path(clip).name


# --------------------------------------------------------------------------- #
# Modell
# --------------------------------------------------------------------------- #

@dataclass
class BrollItem:
    """Ein B-Roll-Stück: Quellbereich [in_s, out_s) im Clip, Beginn relativ zum Beat-Anfang."""
    clip: str
    in_s: float
    out_s: float
    start_offset_s: float
    grund: str = ""
    abweichung: bool = False          # weicht von der Bild-Spalte des Plans ab
    abweichung_grund: str = ""

    def dauer_s(self) -> float:
        return self.out_s - self.in_s

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Item") -> "BrollItem":
        _check_keys(d, wo, {"clip", "in_s", "out_s", "start_offset_s", "grund", "abweichung", "abweichung_grund"},
                    {"clip", "in_s", "out_s", "start_offset_s"})
        return cls(clip=str(d["clip"]), in_s=_float(d, "in_s", wo), out_s=_float(d, "out_s", wo),
                   start_offset_s=_float(d, "start_offset_s", wo), grund=str(d.get("grund") or ""),
                   abweichung=bool(d.get("abweichung", False)), abweichung_grund=str(d.get("abweichung_grund") or ""))


@dataclass
class BrollBeat:
    beat_nr: str
    items: list[BrollItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, wo: str = "Beat") -> "BrollBeat":
        _check_keys(d, wo, {"beat_nr", "items"}, {"beat_nr"})
        wo = f"Beat #{d['beat_nr']}"
        raw = d.get("items") or []
        if not isinstance(raw, list):
            raise AutoCutError(f"{wo}: 'items' muss eine Liste sein.")
        return cls(beat_nr=str(d["beat_nr"]), items=[BrollItem.from_dict(x, f"{wo} Item {i}") for i, x in enumerate(raw, 1)])


@dataclass
class BrollPlan:
    video: str
    beats: list[BrollBeat] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d) -> "BrollPlan":
        if isinstance(d, list):                       # Spec-Form: nackte Beat-Liste
            d = {"video": "", "beats": d}
        _check_keys(d, "B-Roll-Plan", {"video", "beats"}, {"beats"})
        if not isinstance(d["beats"], list):
            raise AutoCutError("B-Roll-Plan: 'beats' muss eine Liste sein.")
        return cls(video=str(d.get("video") or ""),
                   beats=[BrollBeat.from_dict(b, f"Beat {i}") for i, b in enumerate(d["beats"], 1)])

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "BrollPlan":
        p = Path(path)
        if not p.is_file():
            raise AutoCutError(f"B-Roll-Plan fehlt: {p} — zuerst nach prompts/place-broll.md erstellen.")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise AutoCutError(f"B-Roll-Plan {p} ist kein gültiges JSON: {e}") from e
        try:
            return cls.from_dict(data)
        except AutoCutError as e:
            raise AutoCutError(f"{p}: {e}") from e

    def all_items(self) -> list[tuple[BrollBeat, BrollItem]]:
        return [(b, it) for b in self.beats for it in b.items]


# --------------------------------------------------------------------------- #
# Index-Zugriff
# --------------------------------------------------------------------------- #

def _index_by_path(index: dict) -> dict[str, dict]:
    return {str(c["path"]): c for c in (index.get("clips") or []) if c.get("path")}


def _datei(c: dict) -> str:
    return str(c.get("datei") or _name(str(c.get("path", ""))))


def clip_ref(c: dict) -> str:
    """Kurzreferenz „Standort/Ordner/Datei" eines Index-Eintrags (Teile ohne Wert entfallen)."""
    parts = [str(c.get("standort") or ""), str(c.get("ordner") or ""), _datei(c)]
    return "/".join(p for p in parts if p)


def resolve_clip_ref(ref: str, index: dict) -> tuple[str | None, str]:
    """Pfad oder Kurzreferenz auf den vollen Index-Pfad abbilden → (Pfad, "") oder (None, Fehlermeldung)."""
    clips = index.get("clips") or []
    ref = str(ref).strip()
    by_path = _index_by_path(index)
    if ref in by_path:
        return ref, ""
    parts = [p for p in ref.strip("/").split("/") if p]
    if not parts:
        return None, "Clip-Referenz ist leer."
    cands = [c for c in clips if _datei(c) == parts[-1]]
    if not cands:
        cands = [c for c in clips if _datei(c).lower() == parts[-1].lower()]
    if len(parts) >= 2:
        cands = [c for c in cands if str(c.get("ordner") or "") == parts[-2]]
    if len(parts) >= 3:
        cands = [c for c in cands if str(c.get("standort") or "") == parts[-3]]
    if not cands:
        return None, (f"Clip „{ref}“ ist nicht im Index (broll_index.json) — Referenz prüfen oder Clip indexieren "
                      f"(autocut_index_broll.py).")
    if len(cands) > 1:
        return None, (f"Clip „{ref}“ ist mehrdeutig: " + ", ".join(clip_ref(c) for c in cands)
                      + " — Standort/Ordner mit angeben (z. B. „" + clip_ref(cands[0]) + "“).")
    return str(cands[0]["path"]), ""


def normalize_clip_refs(bp: BrollPlan, index: dict) -> list[str]:
    """Kurzreferenzen im Plan durch volle Pfade ersetzen (in place); liefert Fehlermeldungen je Item."""
    errors = []
    for b, it in bp.all_items():
        path, err = resolve_clip_ref(it.clip, index)
        if path is None:
            errors.append(f"Beat #{b.beat_nr}: {err}")
        else:
            it.clip = path
    return errors


def _laeufe(c: dict) -> list[tuple[float, float]] | None:
    """Die ungeschnittenen stabilen Läufe des Clips (``stabil_quelle.laeufe``, Stufe 2b seit Schluss-Review I3/M1)
    als ``(von_s, bis_s)``; None, wenn der Index sie nicht trägt (Stufe 2b davor) — dann gilt der Rückfall über die
    an Abschnittsgrenzen zusammengelegten Stücke. Eine leere Liste ist eine Aussage („nichts stabil"), kein
    Rückfall."""
    laeufe = (c.get("stabil_quelle") or {}).get("laeufe")
    return None if laeufe is None else [(float(x), float(z)) for x, z, *_ in laeufe]


def _lauf_nr(laeufe: list[tuple[float, float]], von_s: float, bis_s: float) -> int | None:
    """Nummer des Laufs, in dem das Stück ``[von_s, bis_s]`` liegt (±``EPS``); None, wenn in keinem. Liegt es in der
    Toleranz in zwei Läufen (sie berühren sich, das Stück ist kürzer als ``EPS``), zählt der, den es wirklich
    überdeckt."""
    passend = [i for i, (x, z) in enumerate(laeufe) if x - EPS <= von_s and bis_s <= z + EPS]
    return max(passend, key=lambda i: min(bis_s, laeufe[i][1]) - max(von_s, laeufe[i][0]), default=None)


def _merge_an_abschnittsgrenzen(stuecke: list[tuple]) -> list[tuple[float, float]]:
    """Stücke ``(von_s, bis_s, startet_an_grenze, endet_an_grenze[, lauf])`` zusammenlegen — aber nur, wenn sich zwei
    Stücke an einer ECHTEN Abschnittsgrenze berühren (Review-Fund B1): das vordere endet an der ``bis_s`` seines
    EIGENEN Abschnitts, das hintere beginnt an der ``von_s`` seines EIGENEN Abschnitts, und beide Zahlen liegen
    innerhalb ``EPS`` beieinander. Ein Lauf, der INNERHALB eines Abschnitts an einer Bewegungsspitze endet (z. B.
    durch ein einzelnes unruhiges Fenster geteilt), trifft die Nachbarzahl bei der Standardkonfiguration
    (``fenster_s`` = 2 · ``schritt_s``) oft rein arithmetisch — genau das darf nicht als durchgehend stabil zählen.
    Ein Stück, das schon der ganze Abschnitt ist (z. B. ein ``verwendbar``-Abschnitt), hat ``startet_an_grenze``/
    ``endet_an_grenze`` immer wahr und legt sich wie bisher mit jedem berührenden Nachbarn zusammen.

    ``lauf`` (Schluss-Review I3/M1) ist die Nummer des ungeschnittenen Laufs aus ``stabil_quelle.laeufe``, zu dem
    ein stabiles Stück gehört, oder None — für einen ganzen Abschnitt und für einen Index ohne ``laeufe``. Zwei
    Stücke mit Nummer legen sich nur bei GLEICHER Nummer zusammen: so bleibt ein echter Sprung zwischen zwei Läufen
    ein Sprung, auch wenn er genau auf einer Abschnittsgrenze liegt. Ohne ``laeufe`` (alle Nummern None) kann die
    Regel das nicht sehen und überbrückt einen solchen Sprung (M1) — das bleibt der Rückfall für Indexe von vorher."""
    merged: list[list] = []          # [von_s, bis_s, endet_an_grenze, lauf des letzten Stücks]
    for von, bis, startet_an_grenze, endet_an_grenze, *rest in sorted(stuecke, key=lambda s: s[:4]):
        lauf = rest[0] if rest else None
        if (merged and merged[-1][2] and startet_an_grenze and von <= merged[-1][1] + EPS
                and (lauf is None or merged[-1][3] is None or lauf == merged[-1][3])):
            merged[-1][1] = max(merged[-1][1], bis)
            merged[-1][2] = endet_an_grenze
            merged[-1][3] = lauf
        else:
            merged.append([von, bis, endet_an_grenze, lauf])
    return [(von, bis) for von, bis, _, _ in merged]


def _usable_spans(c: dict, stabil: bool = False) -> list[tuple[float, float]]:
    """Verwendbare Abschnitte, an Abschnittsgrenzen zusammengelegt (ein Item darf über eine Inhaltsgrenze laufen,
    solange kein unbrauchbarer Abschnitt dazwischen liegt).

    ``stabil=True`` (nur Plan v2, Spec 2026-09-23) nimmt zusätzlich die gemessenen ``stabil``-Bereiche der
    Abschnitte auf, die das Modell verworfen hat — aber nur, wenn der Abschnitt den Schlüssel ``maengel`` trägt
    (Review-Fund I3): dieselbe Vorbedingung wie ``compact_index_v2()`` für die Rettung. Ohne den Schlüssel (alter
    Cache vor Spec 2026-09-23) ist der Verwerfungsgrund unbekannt — könnte ein Inhalts-Mangel sein, den die
    Messung nicht widerlegen kann —, also bleibt der Abschnitt gesperrt. Ob ein GESPERRTER Mangel im gemessenen
    Bereich liegt, prüft ``verify_layout()`` ohnehin getrennt je Abschnitt; hier geht es nur um die Frage, wo
    überhaupt brauchbares Material liegen könnte.

    Trägt ``stabil_quelle`` die ungeschnittenen Läufe (Schluss-Review I3/M1), legen sich stabile Stücke nur
    zusammen, wenn sie zum SELBEN Lauf gehören — dann auch über eine Abschnittsgrenze (Lauf 12–18 s, Stücke 12–13
    und 13–18 s → 12–18 s); Stücke verschiedener Läufe nie, auch nicht genau an einer Abschnittsgrenze. Ein Stück,
    das in keinem Lauf liegt (uneinheitlicher Datensatz), zählt nicht. Ohne ``laeufe`` gilt der Rückfall: Stücke
    legen sich an einer echten, gemeinsamen Abschnittsgrenze zusammen (FX3_8641: 0–2 s + 2–4,8 s → 0–4,8 s), zwei
    Stücke desselben Abschnitts nie (Review-Fund B1), siehe ``_merge_an_abschnittsgrenzen()``. Ohne den Parameter
    (Plan v1) ist das Ergebnis unverändert — ``verwendbar``-Abschnitte legen sich weiter bei jeder
    Berührung/Überschneidung zusammen."""
    stuecke: list[tuple] = [(float(a["von_s"]), float(a["bis_s"]), True, True)
                            for a in (c.get("abschnitte") or []) if a.get("verwendbar")]
    if stabil:
        laeufe = _laeufe(c)
        for a in (c.get("abschnitte") or []):
            if a.get("verwendbar") or "maengel" not in a:
                continue
            a_von, a_bis = float(a["von_s"]), float(a["bis_s"])
            for x, z, *_ in (a.get("stabil") or []):
                x, z = float(x), float(z)
                lauf = None if laeufe is None else _lauf_nr(laeufe, x, z)
                if laeufe is not None and lauf is None:
                    continue
                stuecke.append((x, z, abs(x - a_von) <= EPS, abs(z - a_bis) <= EPS, lauf))
    return _merge_an_abschnittsgrenzen(stuecke)


def _section_quality(c: dict, in_s: float, out_s: float) -> int | None:
    """Niedrigste Qualität der Abschnitte, die das Intervall berühren."""
    qs = [int(a["qualitaet"]) for a in (c.get("abschnitte") or [])
          if a.get("qualitaet") is not None and float(a["von_s"]) < out_s - EPS and float(a["bis_s"]) > in_s + EPS]
    return min(qs) if qs else None


def _standort_nr(standort: str | None) -> int | None:
    m = re.search(r"\d+", str(standort or ""))
    return int(m.group()) if m else None


def length_bounds(beat: Beat | None, cfg: dict) -> tuple[float, float, str]:
    """Erlaubte Item-Länge je Beat: O-Ton → min/max, Platzhalter → Montage, Plan „Schnelle Cuts" → schnelle Cuts."""
    text = f"{beat.kommentar} {beat.bild_hinweis}" if beat else ""
    if _FAST_CUTS.search(text):
        lo, hi = cfg["fast_cuts_len_s"]
        return float(lo), float(hi), "Schnelle Cuts"
    if beat is not None and beat.typ != "oton":
        lo, hi = cfg["montage_len_s"]
        return float(lo), float(hi), "Montage"
    return float(cfg["min_len_s"]), float(cfg["max_len_s"]), "O-Ton"


# --------------------------------------------------------------------------- #
# Prüfung
# --------------------------------------------------------------------------- #

def verify_broll_plan(bp: BrollPlan, tp_dict: dict, index: dict, cl: Cutlist, cfg_broll: dict, fps: float) -> VerifyResult:
    """Harte Prüfung des B-Roll-Plans (Spec 5). Fehler stoppen den Bau, Warnungen landen im Bericht.

    tp_dict: ``TimelinePlan.to_dict()`` bzw. Inhalt von timeline.json (``beats`` mit nr/typ/rec_in_f/rec_out_f/person).
    index: Inhalt von broll_index.json (``clips``). cl: Cutlist (Typ, Kommentar, Sperren je Beat).
    cfg_broll: ``broll:``-Block der Config bzw. des Profils. Kurzreferenzen in ``clip`` werden auf volle Pfade gesetzt.
    """
    r = VerifyResult()
    fps = float(fps or tp_dict.get("fps") or 0)
    if fps <= 0:
        r.errors.append("Bildrate fehlt (fps ≤ 0) — timeline.json/media.json prüfen.")
        return r
    if not bp.beats:
        r.errors.append("B-Roll-Plan enthält keine Beats.")
        return r
    for key in ("first_appearance_visible_s", "min_len_s", "max_len_s", "montage_len_s", "fast_cuts_len_s",
                "max_coverage", "tail_free_s", "tail_free_min_beat_s", "forbidden_maengel"):
        if key not in cfg_broll:
            r.errors.append(f"Config: broll.{key} fehlt — defaults.yaml oder profile/default.yaml prüfen.")
    if r.errors:
        return r

    r.errors += normalize_clip_refs(bp, index)
    by_path = _index_by_path(index)
    tp_beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    cl_beats = {b.nr: b for b in cl.beats}
    forbidden = set(cfg_broll["forbidden_maengel"])
    visible = float(cfg_broll["first_appearance_visible_s"])
    tail_free, tail_min = float(cfg_broll["tail_free_s"]), float(cfg_broll["tail_free_min_beat_s"])
    max_cov = float(cfg_broll["max_coverage"])

    # erstes Auftreten je Person (Timeline-Reihenfolge der O-Ton-Beats)
    first_beat_of: dict[str, str] = {}
    for b in sorted(tp_beats.values(), key=lambda x: int(x["rec_in_f"])):
        if b.get("typ") == "oton" and b.get("person") and b["person"] not in first_beat_of:
            first_beat_of[b["person"]] = str(b["nr"])

    seen_nr: set[str] = set()
    uses: dict[str, list[str]] = {}
    ordered: list[tuple[int, str, BrollItem]] = []     # (Timeline-Frame, Beat-Nr, Item) für die Ordner-Folge
    for pb in bp.beats:
        nr = pb.beat_nr
        tag = f"Beat #{nr}"
        if nr in seen_nr:
            r.errors.append(f"{tag} kommt im B-Roll-Plan mehrfach vor — Items in einem Eintrag zusammenfassen.")
            continue
        seen_nr.add(nr)
        tb, cb = tp_beats.get(nr), cl_beats.get(nr)
        if tb is None or cb is None:
            r.errors.append(f"{tag} gibt es nicht in der Timeline/Cutlist — Nummern aus cutlist.json verwenden.")
            continue
        beat_dauer = (int(tb["rec_out_f"]) - int(tb["rec_in_f"])) / fps
        typ = str(tb.get("typ") or cb.typ)
        person = tb.get("person") or cb.person
        lo, hi, regel = length_bounds(cb, cfg_broll)
        nur = {int(m) for m in _NUR_STANDORT.findall(f"{cb.kommentar} {cb.bild_hinweis}")}
        placed: list[tuple[float, float]] = []

        for i, it in enumerate(pb.items, 1):
            itag = f"{tag} Item {i} ({_name(it.clip)} {it.in_s:g}–{it.out_s:g}s)"
            c = by_path.get(it.clip)
            if c is None:
                continue                                   # Fehler steht schon aus normalize_clip_refs
            uses.setdefault(it.clip, []).append(nr)
            dauer = it.dauer_s()
            # --- Zeiten im Clip
            if it.out_s <= it.in_s or it.in_s < 0:
                r.errors.append(f"{itag}: ungültiges Intervall (out_s muss größer als in_s ≥ 0 sein).")
                continue
            clip_dauer = c.get("dauer_s")
            if clip_dauer is not None and it.out_s > float(clip_dauer) + EPS:
                r.errors.append(f"{itag}: liegt außerhalb des Clips (0–{_s(clip_dauer)}).")
            # --- verwendbarer Abschnitt
            spans = _usable_spans(c)
            if not any(a - EPS <= it.in_s and it.out_s <= z + EPS for a, z in spans):
                liste = ", ".join(f"{a:g}–{z:g}s" for a, z in spans) or "keiner"
                r.errors.append(f"{itag}: liegt in keinem als verwendbar markierten Abschnitt (verwendbar: {liste}).")
            # --- Mängel
            maengel = set(c.get("maengel") or [])
            if (c.get("personen") or {}).get("blick_in_kamera"):
                maengel.add("Blick in Kamera")
            for m in sorted(maengel & forbidden):
                r.errors.append(f"{itag}: Clip hat den Mangel „{m}“ — gesperrt für B-Roll.")
            q = _section_quality(c, it.in_s, it.out_s)
            if q is not None and q < LOW_QUALITY:
                r.warnings.append(f"{itag}: Abschnitt mit Qualität {q} — Bild im Proxy prüfen.")
            # --- Länge
            if dauer < lo - EPS:
                r.errors.append(f"{itag}: {_s(dauer)} ist zu kurz — {regel}: {_s(lo)}–{_s(hi)}.")
            elif dauer > hi + EPS:
                r.errors.append(f"{itag}: {_s(dauer)} ist zu lang — {regel}: {_s(lo)}–{_s(hi)}.")
            # --- Lage im Beat
            start, ende = it.start_offset_s, it.start_offset_s + dauer
            if start < 0:
                r.errors.append(f"{itag}: start_offset_s {start:g} ist negativ.")
            if ende > beat_dauer + EPS:
                r.errors.append(f"{itag}: ragt über das Beat-Ende hinaus (endet bei {_s(ende)}, Beat dauert {_s(beat_dauer)}).")
            # --- Sprecher beim ersten Auftritt sichtbar
            if typ == "oton" and person and first_beat_of.get(person) == nr and start < visible - EPS:
                r.errors.append(f"{itag}: Sprecher {person} tritt hier zum ersten Mal auf und muss mindestens "
                                f"{_s(visible)} sichtbar sein, bevor B-Roll kommt (Item beginnt bei {_s(start)}).")
            # --- lange O-Ton-Beats enden mit Sprecher im Bild
            if typ == "oton" and beat_dauer >= tail_min - EPS and ende > beat_dauer - tail_free + EPS:
                r.errors.append(f"{itag}: Beat dauert {_s(beat_dauer)} — die letzten {_s(tail_free)} müssen frei bleiben "
                                f"(Sprecher im Bild); Item endet bei {_s(ende)}.")
            # --- Standort-Regel des Plans („Nur S1!")
            snr = _standort_nr(c.get("standort"))
            if nur and snr is not None and snr not in nur:
                r.errors.append(f"{itag}: Plan verlangt „Nur S{'/S'.join(str(n) for n in sorted(nur))}“, "
                                f"der Clip liegt in {c.get('standort')}.")
            # --- Sperren der Cutlist
            for sp in cl.sperren:
                if sp.clip == it.clip and it.in_s < sp.bis_s and sp.von_s < it.out_s:
                    r.errors.append(f"{itag}: überschneidet die Sperre {sp.von_s:g}–{sp.bis_s:g}s ({sp.grund or 'ohne Grund'}).")
            # --- Begründungen
            if it.abweichung and not it.abweichung_grund.strip():
                r.errors.append(f"{itag}: abweichung=true ohne abweichung_grund — Abweichung von der Bild-Spalte nur mit Begründung.")
            if not it.grund.strip():
                r.warnings.append(f"{itag}: ohne grund — kurz begründen, warum dieses Bild zur Aussage passt.")
            placed.append((start, ende))
            ordered.append((int(tb["rec_in_f"]) + int(round(start * fps)), nr, it))

        # --- Überschneidung innerhalb des Beats
        placed.sort()
        for (a0, a1), (b0, b1) in zip(placed, placed[1:]):
            if b0 < a1 - EPS:
                r.errors.append(f"{tag}: Items {_s(a0)}–{_s(a1)} und {_s(b0)}–{_s(b1)} überschneiden sich auf V3.")
        # --- Abdeckung / Füllung
        covered = 0.0
        cur_end = 0.0
        for a0, a1 in placed:
            a0c, a1c = max(a0, cur_end), min(a1, beat_dauer)
            if a1c > a0c:
                covered += a1c - a0c
                cur_end = a1c
        if typ == "oton":
            if beat_dauer > 0 and covered / beat_dauer > max_cov + 0.005:
                r.errors.append(f"{tag}: O-Ton zu {covered / beat_dauer * 100:.0f} % mit B-Roll abgedeckt "
                                f"(höchstens {max_cov * 100:.0f} %).")
        else:
            if not pb.items:
                r.warnings.append(f"{tag} ({typ}, {_s(beat_dauer)}): Platzhalter hat keine B-Roll — die Lücke bleibt leer.")
            elif beat_dauer - covered > PLACEHOLDER_GAP_WARN_S:
                r.warnings.append(f"{tag} ({typ}): Platzhalter {_s(beat_dauer)} nur zu {_s(covered)} gefüllt — "
                                  f"{_s(beat_dauer - covered)} Lücke.")

    # --- Wiederholung im ganzen Plan
    for clip, beats in uses.items():
        if len(beats) > 1:
            r.errors.append(f"Clip {_name(clip)} wird zweimal verwendet (Beats #{', #'.join(beats)}) — kein Clip doppelt im Video.")
    # --- gleicher Motiv-Ordner direkt nacheinander (Timeline-Reihenfolge)
    ordered.sort(key=lambda x: x[0])
    for (_, nr_a, a), (_, nr_b, b) in zip(ordered, ordered[1:]):
        oa, ob = by_path[a.clip].get("ordner"), by_path[b.clip].get("ordner")
        if oa and oa == ob:
            wo = f"Beat #{nr_a}" if nr_a == nr_b else f"Beats #{nr_a}→#{nr_b}"
            r.warnings.append(f"{wo}: {_name(a.clip)} und {_name(b.clip)} kommen direkt nacheinander aus Ordner „{oa}“.")
    return r


def check_files(bp: BrollPlan, index: dict) -> list[str]:
    """Original und Proxy jedes Clips müssen da sein (nur Existenz-Tests; NAS wird nur gelesen)."""
    probs = []
    by_path = _index_by_path(index)
    for clip in sorted({it.clip for _, it in bp.all_items()}):
        p = Path(clip)
        if not p.is_file():
            probs.append(f"Clip-Datei nicht gefunden: {p} — ist das NAS gemountet?")
            continue
        proxy = (by_path.get(clip) or {}).get("proxy")
        if not (proxy and Path(proxy).is_file()) and proxy_for(p) is None:
            probs.append(f"kein Proxy für {p.name} (erwartet {p.parent / 'Proxy' / (p.stem + '.mov')} oder .mp4).")
    return probs


# --------------------------------------------------------------------------- #
# V3-Items und Marker
# --------------------------------------------------------------------------- #

def build_v3_items(bp: BrollPlan, tp_dict: dict, fps: float,
                   clip_fps: dict[str, float] | None = None) -> tuple[list[Item], list[MarkerSpec]]:
    """Plan → V3-Items (nur Bild) und gelbe Marker „B-Roll abweichend" (frame relativ zum Timeline-Anfang).

    rec_in_f = Beat-Anfang + start_offset_s; Länge aus out_s − in_s; ragt die Rundung über das Beat-Ende,
    wird um die überschüssigen Frames gekürzt. Marker weichen belegten Frames (Beat-Marker) aus.

    B-Roll-Clips haben oft eine andere Bildrate als die Timeline (MEK: 25/50/100 fps). Quellframes
    (startFrame/endFrame) rechnen deshalb mit der Clip-Bildrate aus ``clip_fps`` (Pfad oder Dateiname →
    fps; fehlt der Eintrag, gilt die Timeline-Bildrate); Record-Frames bleiben Timeline-Frames.
    """
    fps = float(fps)
    clip_fps = clip_fps or {}

    def _cfps(clip: str) -> float:
        for key in (clip, Path(clip).name):
            v = clip_fps.get(key)
            if v:
                return float(v)
        return fps
    tp_beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    taken = {int(m["frame"]) for m in (tp_dict.get("markers") or []) if isinstance(m, dict) and "frame" in m}
    items: list[Item] = []
    markers: list[MarkerSpec] = []
    for pb in bp.beats:
        tb = tp_beats.get(pb.beat_nr)
        if tb is None:
            raise AutoCutError(f"Beat #{pb.beat_nr} gibt es nicht in timeline.json — erst autocut_place_broll.py --verify-only.")
        beat_in, beat_out = int(tb["rec_in_f"]), int(tb["rec_out_f"])
        prev_out = beat_in
        for it in sorted(pb.items, key=lambda x: x.start_offset_s):
            rec_in = beat_in + seconds_to_frames(it.start_offset_s, fps)
            if rec_in < prev_out:           # Rundung (z. B. Offsets 1,75/3,5/5,25 s) darf keinen Vorgänger überlappen
                rec_in = prev_out           # → am Vorgänger einrasten, Resolve würde sonst verschieben/kürzen
            n = seconds_to_frames(it.dauer_s(), fps)
            if rec_in + n > beat_out:
                n = beat_out - rec_in
            if n <= 0:
                raise AutoCutError(f"Beat #{pb.beat_nr}: {_name(it.clip)} {it.in_s:g}–{it.out_s:g}s ergibt keine Frames "
                                   f"innerhalb des Beats.")
            cfps = _cfps(it.clip)
            src_in = seconds_to_frames(it.in_s, cfps)
            src_n = int(round(n * cfps / fps))          # n Timeline-Frames entsprechen n·(cfps/fps) Quellframes
            items.append(Item("V3", it.clip, src_in, src_in + src_n, rec_in, rec_in + n, True, pb.beat_nr, "broll", True))
            prev_out = rec_in + n
            if it.abweichung:
                frame = rec_in
                while frame in taken:
                    frame += 1
                taken.add(frame)
                markers.append(MarkerSpec(frame, f"B-Roll abweichend #{pb.beat_nr}",
                                          f"{_name(it.clip)} {it.in_s:g}–{it.out_s:g}s: {it.abweichung_grund}",
                                          MARKER_COLORS["broll"], max(1, n)))
    items.sort(key=lambda i: i.rec_in_f)
    return items, markers


# --------------------------------------------------------------------------- #
# Kompakter Index für den Prompt
# --------------------------------------------------------------------------- #

def compact_index(index: dict) -> list[dict]:
    """Kurzform je Clip für die Session: Referenz, Datei, Ordner, Standort, Dauer, Kurzbeschreibung, Einstellung,
    Bewegung, Tempo, verwendbare Abschnitte, Tags, Mängel, Eignung, Qualität. Sortiert nach Standort/Ordner/Datei."""
    out = []
    for c in index.get("clips") or []:
        abschnitte = [{"von_s": a["von_s"], "bis_s": a["bis_s"], "kurz": a.get("beschreibung", ""), "q": a.get("qualitaet")}
                      for a in (c.get("abschnitte") or []) if a.get("verwendbar")]
        out.append({"ref": clip_ref(c), "datei": _datei(c), "ordner": c.get("ordner") or "", "standort": c.get("standort"),
                    "dauer_s": c.get("dauer_s"), "kurz": c.get("beschreibung_kurz", ""),
                    "einstellung": c.get("einstellung"), "bewegung": c.get("kamerabewegung"), "tempo": c.get("tempo"),
                    "verwendbar": bool(abschnitte), "abschnitte": abschnitte,
                    "tags": list(c.get("tags") or []), "maengel": list(c.get("maengel") or []),
                    "eignung": list(c.get("eignung") or []), "qualitaet": c.get("qualitaet_gesamt")})
    out.sort(key=lambda x: (str(x["standort"] or ""), x["ordner"], x["datei"]))
    return out


# --------------------------------------------------------------------------- #
# Profil
# --------------------------------------------------------------------------- #

def load_profile(name: str = "default") -> tuple[str, dict]:
    """Schnitt-Profil aus tools/autocut/profile/<name>.md (Prosa) und <name>.yaml (broll-Werte) laden."""
    md, yml = PROFILE_DIR / f"{name}.md", PROFILE_DIR / f"{name}.yaml"
    if not md.is_file() or not yml.is_file():
        raise AutoCutError(f"Profil „{name}“ fehlt — erwartet {md} und {yml}.")
    data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    cfg = data.get("broll") if isinstance(data, dict) and isinstance(data.get("broll"), dict) else data
    if not isinstance(cfg, dict):
        raise AutoCutError(f"Profil {yml}: erwartet einen broll:-Block mit Werten.")
    return md.read_text(encoding="utf-8"), dict(cfg)


# --------------------------------------------------------------------------- #
# Bericht
# --------------------------------------------------------------------------- #

def _md(s) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def render_broll_plan_md(bp: BrollPlan, index: dict, tp_dict: dict, cl: Cutlist | None = None,
                         warnings: list[str] | None = None, build: dict | None = None) -> str:
    """Markdown-Bericht: je Beat die gewählten Clips (Position, Quelle, Bereich, Grund, Abweichung), danach
    Kennzahlen, Warnungen und die Bau-Angaben (Ergebnisse/Rohschnitt/<video>-broll.md)."""
    fps = float(tp_dict.get("fps") or (cl.fps if cl else 25))
    by_path = _index_by_path(index)
    tp_beats = {str(b["nr"]): b for b in (tp_dict.get("beats") or [])}
    cl_beats = {b.nr: b for b in cl.beats} if cl else {}
    video = bp.video or (cl.video if cl else "")
    lines = [f"# B-Roll-Plan — {video}", ""]
    if build:
        lines.append(f"Timeline: **{build.get('timeline', '–')}** · V3-Items: {build.get('items', '–')} · "
                     f"Marker: {build.get('markers', '–')} · Startframe: {build.get('start_frame', '–')}")
        lines.append("")
    lines += ["| Beat | Szene | Position | Clip | Bereich | Start | Dauer | Grund | Abweichung |",
              "|---|---|---|---|---|---|---|---|---|"]
    n_items, total, ordner = 0, 0.0, set()
    for pb in bp.beats:
        tb, cb = tp_beats.get(pb.beat_nr), cl_beats.get(pb.beat_nr)
        szene = f"{cb.szene} ({cb.typ})" if cb else (tb.get("typ") if tb else "")
        if not pb.items:
            pos = _mmss(int(tb["rec_in_f"]), fps) if tb else "–"
            lines.append(f"| {pb.beat_nr} | {_md(szene)} | {pos} | – | – | – | – | keine B-Roll | |")
            continue
        for it in sorted(pb.items, key=lambda x: x.start_offset_s):
            c = by_path.get(it.clip, {})
            pos = _mmss(int(tb["rec_in_f"]) + int(round(it.start_offset_s * fps)), fps) if tb else "–"
            quelle = clip_ref(c) if c else _name(it.clip)
            abw = f"JA: {_md(it.abweichung_grund)}" if it.abweichung else ""
            lines.append(f"| {pb.beat_nr} | {_md(szene)} | {pos} | {_md(quelle)} | {it.in_s:g}–{it.out_s:g} s | "
                         f"+{it.start_offset_s:g} s | {_s(it.dauer_s())} | {_md(it.grund)} | {abw} |")
            n_items += 1
            total += it.dauer_s()
            if c.get("ordner"):
                ordner.add(c["ordner"])
    lines += ["", f"**Kennzahlen:** {n_items} B-Roll-Items in {sum(1 for b in bp.beats if b.items)} von {len(bp.beats)} "
                  f"geplanten Beats · {_s(total)} B-Roll gesamt · {len(ordner)} Motiv-Ordner · "
                  f"{sum(1 for _, it in bp.all_items() if it.abweichung)} Abweichungen von der Bild-Spalte", ""]
    if warnings:
        lines += ["## Warnungen", ""] + [f"- {_md(w)}" for w in warnings] + [""]
    if build and build.get("warnings"):
        lines += ["## Hinweise aus dem Bau", ""] + [f"- {_md(w)}" for w in build["warnings"]] + [""]
    return "\n".join(lines)
