"""Aus der geprüften Cutlist die konkreten Timeline-Items berechnen — frame-genau, ohne Resolve.

Eingaben: ``Cutlist`` (Task 5), ``media.json`` (Format + Frame-Zahlen, Task 6), ``sync.json``
(FX3×a7-Paare, Task 6), Wörter je Clip (Scribe-Cache) und die Config (Handles, Pause).
Ausgabe: ``TimelinePlan`` — Items je Spur (V1/A1 = FX3, V2 = a7 mit Sync-Versatz), ein Marker
je Beat, Beat-Positionen und die Gesamtlänge.

Konventionen:
- Alle ``rec_*``-Frames sind RELATIV zum Timeline-Anfang (0 = erster Frame); ``resolve_api`` addiert
  den Startframe der Timeline. ``src_*``-Frames sind Frames im Quellclip ab 0.
- Intervalle sind halboffen: ``[in_f, out_f)``; die Dauer ist ``out_f - in_f``.
- Handles (Vor-/Nachlauf) kommen aus ``handle_in_frames``/``handle_out_frames``; ``hart_in``/``hart_out``
  setzen sie auf 0. Sie werden begrenzt, damit kein Wort eines anderen Sprechers hineinragt (Spec 3.3).
- V2 = a7 nur Bild (kein A2 mehr, Spec v2 Abschnitt 1). Es gibt V2 nur, wenn ein ok-Sync-Paar den
  kompletten Bereich inklusive Handles abdeckt und der versetzte Bereich im a7-Clip liegt; sonst ein
  roter Marker „V2 fehlt“. Ragt ein Nachlauf über das FX3-Clip-Ende hinaus, zählt für die Abdeckung
  das Clip-Ende (das Item endet ohnehin dort).
- Teilschnitte eines Beats liegen lückenlos aneinander; nach jedem Beat außer dem letzten folgt
  ``pause_after_s`` (sonst ``Cutlist.pause_s``); Platzhalter-Beats (vo/bild/grafik) sind reine Lücken.
- Resolve erlaubt nur einen Marker pro Frame — Warnmarker weichen auf den nächsten freien Frame aus.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field

from .charge import AutoCutError
from .cutlist import TYPEN, Beat, Cutlist
from .media import seconds_to_frames
from .sync import a7_for_cut

MARKER_COLORS = {"oton": "Blue", "vo": "Yellow", "bild": "Green", "grafik": "Purple", "warnung": "Red", "broll": "Yellow",
                 "szene": "Cyan"}

# Scribe-Annotationen im Wortstrom („(übersprechen 00:01:31)“, „[lacht]“) sind keine Wörter.
_ANNOTATION = re.compile(r"\(.*\)|\[.*\]")


# --------------------------------------------------------------------------- #
# Modell
# --------------------------------------------------------------------------- #

@dataclass
class Item:
    """Ein Clip-Stück auf einer Spur. Frames halboffen [in, out); rec_* relativ zum Timeline-Anfang."""
    track: str                 # "V1" | "A1" | "V2" | "V3"
    clip: str                  # voller Pfad des Originals (Media-Pool-Schlüssel)
    src_in_f: int
    src_out_f: int
    rec_in_f: int
    rec_out_f: int
    enabled: bool = True
    beat_nr: str = ""
    kind: str = "oton"         # "oton" | "broll"
    video_only: bool = False   # True: nur Bild (V3-B-Roll), kein Ton mitnehmen
    tempo: int = 1             # Zeitraffer-Faktor (B-Roll, spätere Aufgabe); 1 = normal

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class MarkerSpec:
    """Timeline-Marker; frame relativ zum Timeline-Anfang, Farbe = Resolve-Farbname."""
    frame: int
    name: str
    note: str
    color: str
    duration: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MarkerSpec":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class BeatPos:
    """Lage eines Beats auf der Timeline (ohne die nachfolgende Pause)."""
    nr: str
    typ: str
    rec_in_f: int
    rec_out_f: int
    clip: str | None = None
    person: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BeatPos":
        return cls(**{k: d[k] for k in cls.__dataclass_fields__ if k in d})


@dataclass
class TimelinePlan:
    fps: float
    width: int
    height: int
    items: list[Item] = field(default_factory=list)
    markers: list[MarkerSpec] = field(default_factory=list)
    beats: list[BeatPos] = field(default_factory=list)
    total_frames: int = 0      # Ende des letzten Beats (ohne Pause danach) = Länge der Timeline

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TimelinePlan":
        return cls(fps=float(d["fps"]), width=int(d["width"]), height=int(d["height"]),
                   items=[Item.from_dict(x) for x in d.get("items", [])],
                   markers=[MarkerSpec.from_dict(x) for x in d.get("markers", [])],
                   beats=[BeatPos.from_dict(x) for x in d.get("beats", [])],
                   total_frames=int(d.get("total_frames", 0)))


# --------------------------------------------------------------------------- #
# Wörter und Handles
# --------------------------------------------------------------------------- #

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


def _speaker_of(w: dict) -> str | None:
    return w.get("speaker") or w.get("speaker_id")


def clamp_handles(words: list[dict], in_s: float, out_s: float, h_in_s: float, h_out_s: float,
                  speaker: str | None) -> tuple[float, float]:
    """Vorlauf/Nachlauf so begrenzen, dass kein Wort eines anderen Sprechers hineinragt.

    Liefert (Anfang, Ende) in Sekunden: ``in_s - h_in_s`` bzw. ``out_s + h_out_s``, gekürzt auf das Ende
    des letzten fremden Worts vor dem In-Punkt bzw. den Anfang des ersten fremden Worts nach dem
    Out-Punkt. Ragt ein fremdes Wort über den In-/Out-Punkt selbst, entfällt der Handle ganz.
    Ohne bekannten ``speaker`` zählt jedes angrenzende Wort als fremd (konservativ). Nie unter 0.
    """
    a, b = in_s - h_in_s, out_s + h_out_s
    for w in _speech_words(words):
        if speaker and _speaker_of(w) == speaker:
            continue
        ws, we = float(w["start"]), float(w["end"])
        if ws < in_s and we > a:       # fremdes Wort ragt in den Vorlauf (oder über den In-Punkt)
            a = min(we, in_s)
        if we > out_s and ws < b:      # fremdes Wort ragt in den Nachlauf (oder über den Out-Punkt)
            b = max(ws, out_s)
    return round(max(0.0, a), 3), round(b, 3)


def _speaker_at(words: list[dict], in_s: float, out_s: float) -> str | None:
    """Häufigster Sprecher der Wörter, deren Mitte in [in_s, out_s] liegt; None ohne Wörter."""
    inside = [_speaker_of(w) for w in _speech_words(words)
              if in_s <= (float(w["start"]) + float(w["end"])) / 2 <= out_s]
    counts = Counter(s for s in inside if s)
    return counts.most_common(1)[0][0] if counts else None


# --------------------------------------------------------------------------- #
# Marker
# --------------------------------------------------------------------------- #

def _note(b: Beat) -> str:
    """Marker-Notiz: Sprecher, O-Ton-/VO-Text, Bild-Hinweis, Caption, Kommentar, Sound (Spec 3.5, Punkt 5)."""
    parts = []
    if b.person:
        parts.append(f"{b.person} · {b.rolle}" if b.rolle else b.person)
    if b.typ == "oton" and b.cuts:
        texte = [c.text.strip() for c in b.cuts if c.text and c.text.strip()]
        if texte:
            parts.append("O-Ton: " + " […] ".join(texte))
    if b.text:
        parts.append("Text: " + b.text)
    if b.bild_hinweis:
        parts.append("Bild: " + b.bild_hinweis)
    if b.caption:
        parts.append("Caption: " + b.caption)
    if b.kommentar:
        parts.append("Kommentar: " + b.kommentar)
    if b.sound:
        parts.append("Sound: " + b.sound)
    return "\n".join(parts)


def _free_frame(taken: set[int], frame: int) -> int:
    """Nächster Frame ab ``frame``, auf dem noch kein Marker liegt (Resolve: ein Marker pro Frame)."""
    while frame in taken:
        frame += 1
    return frame


# --------------------------------------------------------------------------- #
# Aufbau
# --------------------------------------------------------------------------- #

def _clip_frames(media: dict, clip: str, tag: str) -> int:
    rec = (media.get("clips") or {}).get(clip)
    if not rec or not rec.get("original") or rec["original"].get("nb_frames") is None:
        raise AutoCutError(f"{tag}: Clip {clip} steht nicht in media.json — autocut_prepare.py erneut ausführen "
                           f"(oder der Clip gehört nicht zu den Interviews der Charge).")
    return int(rec["original"]["nb_frames"])


def build_timeline_plan(cl: Cutlist, media: dict, sync: dict, words_by_clip: dict, cfg: dict) -> TimelinePlan:
    """Beats der Cutlist in Items, Marker und Beat-Positionen übersetzen (siehe Modul-Doku).

    Erwartet eine Cutlist, die ``verify_cutlist`` bestanden hat; grobe Verstöße (unbekannter Typ, fehlender
    Clip, leerer Platzhalter) werden trotzdem als ``AutoCutError`` gemeldet, nie stillschweigend überbrückt.
    """
    fmt = media.get("format") if isinstance(media, dict) else None
    if not isinstance(fmt, dict) or any(fmt.get(k) is None for k in ("fps", "width", "height")):
        raise AutoCutError("media.json: Abschnitt 'format' (fps, width, height) fehlt oder ist unvollständig — "
                           "autocut_prepare.py erneut ausführen.")
    fps = float(fmt["fps"])
    if fps <= 0:
        raise AutoCutError("media.json: Bildrate fehlt oder ist 0 — autocut_prepare.py erneut ausführen.")
    tp = TimelinePlan(fps=fps, width=int(fmt["width"]), height=int(fmt["height"]))
    for key in ("handle_in_frames", "handle_out_frames"):
        if cfg.get(key) is None:
            raise AutoCutError(f"Config: '{key}' fehlt — Wert in defaults.yaml (oder config.yaml der Charge) eintragen.")
    h_in, h_out = float(cfg["handle_in_frames"]) / fps, float(cfg["handle_out_frames"]) / fps
    taken: set[int] = set()
    pos = 0
    for i, b in enumerate(cl.beats):
        tag = f"Beat #{b.nr} ({b.szene})"
        label = f"#{b.nr} {b.szene}"
        beat_start = pos
        warn: list[MarkerSpec] = []
        if b.typ not in TYPEN:
            raise AutoCutError(f"{tag}: unbekannter Typ '{b.typ}' — erlaubt sind {', '.join(TYPEN)}.")
        if b.typ == "oton":
            if not b.clip or not b.cuts:
                raise AutoCutError(f"{tag}: clip oder cuts fehlen — erst autocut_verify.py ausführen.")
            words = words_by_clip.get(b.clip, [])
            clip_f = _clip_frames(media, b.clip, tag)
            for c in b.cuts:
                spk = _speaker_at(words, c.in_s, c.out_s)
                a, z = clamp_handles(words, c.in_s, c.out_s, 0.0 if c.hart_in else h_in,
                                     0.0 if c.hart_out else h_out, spk)
                s_in = max(0, seconds_to_frames(a, fps))
                s_out = min(seconds_to_frames(z, fps), clip_f)
                n = s_out - s_in
                if n <= 0:
                    raise AutoCutError(f"{tag}: Schnitt {c.in_s:.2f}–{c.out_s:.2f}s ergibt keine Frames "
                                       f"(Clip-Ende bei {clip_f} Frames).")
                tp.items.append(Item("V1", b.clip, s_in, s_out, pos, pos + n, True, b.nr, "oton"))
                tp.items.append(Item("A1", b.clip, s_in, s_out, pos, pos + n, True, b.nr, "oton"))
                # Abdeckung gegen den tatsächlich gesetzten Bereich prüfen: ragt der Nachlauf über das
                # FX3-Clip-Ende, endet das Item dort — mehr muss das a7-Paar nicht abdecken.
                z_chk = min(z, round(clip_f / fps, 3))
                pair = a7_for_cut(sync, b.clip, a, z_chk)
                grund = ""
                if pair is None:
                    grund = f"Kein ok-Sync-Paar deckt {a:.2f}–{z_chk:.2f}s (inkl. Handles) ab."
                else:
                    off = int(pair["offset_frames"])
                    a7_f = _clip_frames(media, pair["other"], tag)
                    if s_in + off < 0 or s_out + off > a7_f:
                        grund = (f"Versatz {off:+d} Frames schiebt den Bereich aus dem a7-Clip "
                                 f"({s_in + off}–{s_out + off} von 0–{a7_f}).")
                    else:
                        tp.items.append(Item("V2", pair["other"], s_in + off, s_out + off, pos, pos + n, True, b.nr, "oton"))
                if grund:
                    warn.append(MarkerSpec(pos, f"V2 fehlt {label}", f"Keine a7-Abdeckung für diesen Schnitt. {grund}",
                                           MARKER_COLORS["warnung"], n))
                pos += n
        else:
            if not b.platzhalter_s or float(b.platzhalter_s) <= 0:
                raise AutoCutError(f"{tag}: platzhalter_s fehlt — Plan-Schätzung „~x s“ eintragen, "
                                   f"dann autocut_verify.py ausführen.")
            pos += seconds_to_frames(float(b.platzhalter_s), fps)
        tp.beats.append(BeatPos(b.nr, b.typ, beat_start, pos, b.clip, b.person))
        frame = _free_frame(taken, beat_start)
        taken.add(frame)
        tp.markers.append(MarkerSpec(frame, label, _note(b), MARKER_COLORS.get(b.typ, "Blue")))
        for m in warn:
            m.frame = _free_frame(taken, m.frame)
            taken.add(m.frame)
            tp.markers.append(m)
        if i < len(cl.beats) - 1:
            pause = b.pause_after_s if b.pause_after_s is not None else cl.pause_s
            pos += seconds_to_frames(float(pause), fps)
    tp.total_frames = pos      # Ende des letzten Beats; nach dem letzten Beat gibt es keine Pause
    return tp
