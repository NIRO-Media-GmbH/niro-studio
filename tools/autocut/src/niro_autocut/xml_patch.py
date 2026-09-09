"""FCP7-XML (xmeml) aus Resolve lesen, Clip-Pegel und Zeitlupe setzen, zurücklesen — ohne Resolve.

Resolve schreibt Clip-Pegel als Filter „Audio Levels" (effectid audiolevels, Parameter level = linearer Faktor,
valuemin 1e-05, valuemax 31.6228); belegt am Export einer User-Timeline (04.09.). Zeitlupe als Filter „Time Remap"
(speed in Prozent) plus angepasstem <end> — ob Resolve beim Import <end> oder den Filter nutzt, misst
scripts/resolve_probe_xml.py. Zuordnung der Clipitems über Medienart, Spur-Index (Reihenfolge der <track>), <start>
(Frames relativ zum Sequenzanfang) und Dateiname. Alles außerhalb der gepatchten Clipitems bleibt semantisch
unverändert; leere Elemente werden in Resolves eigener Form (<tag/>, ohne Leerzeichen vor />) geschrieben.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .charge import AutoCutError

LEVEL_MIN, LEVEL_MAX = "1e-05", "31.6228"
DOCTYPE = "<!DOCTYPE xmeml>"


def load_xml(path: str | Path) -> ET.ElementTree:
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"XML nicht gefunden: {p}")
    try:
        tree = ET.parse(str(p))
    except ET.ParseError as e:
        raise AutoCutError(f"XML nicht lesbar ({p.name}): {e}") from e
    if tree.getroot().tag != "xmeml":
        raise AutoCutError(f"{p.name} ist kein FCP7-XML (Wurzel <{tree.getroot().tag}>, erwartet <xmeml>).")
    return tree


def save_xml(tree: ET.ElementTree, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # ET.tostring schreibt leere Elemente als "<tag />" (mit Leerzeichen); Resolve selbst schreibt "<tag/>".
    # Ohne Normalisierung würden dadurch unberührte Stellen des Dokuments (z. B. <file .../>, leere <track/>) verändert.
    body = ET.tostring(tree.getroot(), encoding="unicode").replace(" />", "/>")
    p.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n{DOCTYPE}\n{body}\n', encoding="utf-8")
    return p


def _tracks(tree: ET.ElementTree, media: str) -> list[ET.Element]:
    if media not in ("video", "audio"):
        raise AutoCutError(f"Medienart '{media}' unbekannt (video/audio).")
    seq = tree.getroot().find("sequence")
    node = seq.find(f"media/{media}") if seq is not None else None
    return list(node.findall("track")) if node is not None else []


def track_clipitems(tree: ET.ElementTree, media: str) -> list[tuple[int, ET.Element]]:
    """(Spur-Index ab 1, clipitem) in Dokumentreihenfolge."""
    out: list[tuple[int, ET.Element]] = []
    for i, tr in enumerate(_tracks(tree, media), 1):
        out += [(i, ci) for ci in tr.findall("clipitem")]
    return out


def clip_start(ci: ET.Element) -> int:
    return int(float(ci.findtext("start") or 0))


def clip_name(ci: ET.Element) -> str:
    return (ci.findtext("name") or "").strip()


def find_clipitem(tree: ET.ElementTree, media: str, track_index: int, start: int, name: str | None = None) -> ET.Element | None:
    for i, ci in track_clipitems(tree, media):
        if i == int(track_index) and clip_start(ci) == int(start) and (name is None or clip_name(ci) == name):
            return ci
    return None


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    e = ET.SubElement(parent, tag)
    if text is not None:
        e.text = str(text)
    return e


def _effect_filter(ci: ET.Element, effectid: str) -> ET.Element | None:
    for f in ci.findall("filter"):
        eff = f.find("effect")
        if eff is not None and (eff.findtext("effectid") or "").strip() == effectid:
            return f
    return None


def _param(filter_el: ET.Element, parameterid: str) -> ET.Element | None:
    """<parameter> mit gegebener <parameterid> im Filter suchen (oder None)."""
    for par in filter_el.findall("effect/parameter"):
        if (par.findtext("parameterid") or "").strip() == parameterid:
            return par
    return None


_NACH_FILTERN = ("link", "comments", "sourcetrack")


def _new_filter(ci: ET.Element) -> ET.Element:
    """Neuen <filter> anlegen; start/end wie bei echten Resolve-Filtern (0 .. Clip-Dauer), nicht -1/-1.

    Landet hinter vorhandenen <filter>-Elementen, aber vor <link>/<comments>/<sourcetrack> — genau Resolves eigene
    Reihenfolge. ET.SubElement() würde stattdessen ans Ende anhängen und diese Elemente vor den neuen Filter
    schieben; ob Resolve das beim Import noch akzeptiert, ist ungeprüft, also wird die Reihenfolge nicht angetastet.
    """
    kinder = list(ci)
    pos = next((i for i, k in enumerate(kinder) if k.tag in _NACH_FILTERN), len(kinder))
    f = ET.Element("filter")
    ci.insert(pos, f)
    _sub(f, "enabled", "TRUE")
    _sub(f, "start", "0")
    _sub(f, "end", ci.findtext("duration") or "-1")
    return f


def set_audio_level(ci: ET.Element, level_lin: float) -> None:
    """Filter „Audio Levels" setzen (vorhandenen Level-Wert ersetzen, sonst Filter anlegen)."""
    f = _effect_filter(ci, "audiolevels")
    if f is None:
        f = _new_filter(ci)
        eff = _sub(f, "effect")
        _sub(eff, "name", "Audio Levels")
        _sub(eff, "effectid", "audiolevels")
        _sub(eff, "effecttype", "audiolevels")
        _sub(eff, "mediatype", "audio")
        _sub(eff, "effectcategory", "audiolevels")
        par = _sub(eff, "parameter")
        _sub(par, "name", "Level")
        _sub(par, "parameterid", "level")
        _sub(par, "value", "1")
        _sub(par, "valuemin", LEVEL_MIN)
        _sub(par, "valuemax", LEVEL_MAX)
    par = _param(f, "level")
    if par is None:
        raise AutoCutError(f"Clipitem {clip_name(ci)}: Audio-Levels-Filter ohne Parameter 'level'.")
    par.find("value").text = f"{float(level_lin):g}"


def get_audio_level(ci: ET.Element) -> float | None:
    f = _effect_filter(ci, "audiolevels")
    if f is None:
        return None
    par = _param(f, "level")
    if par is None:
        return None
    val = par.findtext("value")
    if not val:
        raise AutoCutError(f"Clipitem {clip_name(ci)}: Audio-Levels-Parameter 'level' ohne Wert.")
    return float(val)


def set_speed(ci: ET.Element, tempo: int, end: int) -> None:
    """Filter „Time Remap" (konstante Geschwindigkeit 100/tempo %) und <end> setzen; <in>/<out> bleiben."""
    if int(tempo) < 1:
        raise AutoCutError(f"tempo {tempo} ungültig (≥ 1).")
    f = _effect_filter(ci, "timeremap")
    if f is None:
        f = _new_filter(ci)
        eff = _sub(f, "effect")
        _sub(eff, "name", "Time Remap")
        _sub(eff, "effectid", "timeremap")
        _sub(eff, "effectcategory", "motion")
        _sub(eff, "effecttype", "motion")
        _sub(eff, "mediatype", "video")
        for pid, lo, hi, val in (("variablespeed", "0", "1", "0"), ("speed", "-100000", "100000", "100"),
                                 ("reverse", None, None, "FALSE"), ("frameblending", None, None, "FALSE")):
            par = _sub(eff, "parameter")
            _sub(par, "parameterid", pid)
            _sub(par, "name", pid)
            if lo is not None:
                _sub(par, "valuemin", lo)
                _sub(par, "valuemax", hi)
            _sub(par, "value", val)
    par = _param(f, "speed")
    if par is None:
        raise AutoCutError(f"Clipitem {clip_name(ci)}: Time-Remap-Filter ohne Parameter 'speed'.")
    par.find("value").text = f"{100.0 / int(tempo):g}"
    end_el = ci.find("end")
    if end_el is None:
        end_el = ET.Element("end")
        start_el = ci.find("start")
        ci.insert(list(ci).index(start_el) + 1, end_el)
    end_el.text = str(int(end))


def get_speed(ci: ET.Element) -> float | None:
    f = _effect_filter(ci, "timeremap")
    if f is None:
        return None
    par = _param(f, "speed")
    if par is None:
        return None
    val = par.findtext("value")
    if not val:
        raise AutoCutError(f"Clipitem {clip_name(ci)}: Time-Remap-Parameter 'speed' ohne Wert.")
    return float(val)


def apply_patches(tree: ET.ElementTree, levels: list[dict], speeds: list[dict]) -> dict:
    """Pegel (audio) und Zeitlupen (video) setzen; nicht gefundene Clipitems werden gemeldet, nicht erraten."""
    rep = {"levels_set": 0, "speeds_set": 0, "missing": []}
    for lv in levels:
        ci = find_clipitem(tree, "audio", int(lv["track"]), int(lv["start"]), lv.get("name"))
        if ci is None:
            rep["missing"].append(f"audio Spur {lv['track']} Start {lv['start']} ({lv.get('name', '?')})")
            continue
        set_audio_level(ci, float(lv["level"]))
        rep["levels_set"] += 1
    for sp in speeds:
        ci = find_clipitem(tree, "video", int(sp["track"]), int(sp["start"]), sp.get("name"))
        if ci is None:
            rep["missing"].append(f"video Spur {sp['track']} Start {sp['start']} ({sp.get('name', '?')})")
            continue
        set_speed(ci, int(sp["tempo"]), int(sp["end"]))
        rep["speeds_set"] += 1
    return rep


def read_levels(tree: ET.ElementTree, track_index: int = 1) -> list[dict]:
    out = []
    for i, ci in track_clipitems(tree, "audio"):
        if i == track_index:
            lv = get_audio_level(ci)
            out.append({"start": clip_start(ci), "name": clip_name(ci), "level": 1.0 if lv is None else lv})
    return out


def read_speeds(tree: ET.ElementTree, track_index: int = 3) -> list[dict]:
    out = []
    for i, ci in track_clipitems(tree, "video"):
        if i == track_index:
            sp = get_speed(ci)
            if sp is not None:
                out.append({"start": clip_start(ci), "name": clip_name(ci), "speed": sp,
                            "end": int(float(ci.findtext("end") or 0))})
    return out
