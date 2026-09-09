"""Cutter-Plan (Markdown-Tabelle des Schnittplan-Workflows) lesen — nur lesend.

Der Plan liegt unter <Charge>/Ergebnisse/O-Ton-Pläne/video-N-*.md und hat in allen
Studio-Projekten denselben Aufbau: Kopf mit „## Ziel & Story" (Ziellänge, Format),
„## Material" (mit **Verboten:**-Zeile) und die Ablauf-Tabelle mit acht Spalten
„# | Szene | O-Ton | Quelle | Bild | Sound | Caption | Kommentar".
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .charge import AutoCutError

# Datei-Stems der Kameras: FX3_9557, a7MK4_0001, DJI_0402, C0001 (Sony-Standard), optional _1-Suffix.
STEM_PATTERN = r"\b((?:FX3|a7MK4|DJI|C)_?[0-9]{3,}(?:_[0-9]+)?)\b"
# Zeitangabe mm:ss oder h:mm:ss, optional als Bereich „03:37–03:39" (auch mit Leerzeichen um den Strich).
TC_PATTERN = (r"(?<![\d:])(\d{1,2}:\d{2}(?::\d{2})?)"
              r"(?:\s*[–\-]\s*(\d{1,2}:\d{2}(?::\d{2})?))?(?![\d:])")
STEM_RE = re.compile(STEM_PATTERN)
TC_RE = re.compile(TC_PATTERN)
# Ein Durchlauf über Stems und Zeitangaben in Textreihenfolge: Gruppe 1 = Stem, 2/3 = von/bis.
TOKEN_RE = re.compile(STEM_PATTERN + "|" + TC_PATTERN)
# Plan-Schätzung „~3 s", „≈ 2,5 s", „~1–2 s" (Bereich → oberer Wert).
DAUER_RE = re.compile(r"[~≈]\s*(\d+(?:[.,]\d+)?)(?:\s*[–\-]\s*(\d+(?:[.,]\d+)?))?\s*s\b")
# „Ziellänge ≈ 3:05", „Ziellänge 2:40–3:05", „Ziellänge 90–120 s", „Ziellänge: 60 s" (Bereich → oberer Wert).
ZIEL_RE = re.compile(
    r"Ziell(?:ä|ae|a)nge[^0-9\n]{0,8}"
    r"(?:(\d{1,2}):(\d{2})(?:\s*[–\-]\s*(\d{1,2}):(\d{2}))?"
    r"|(\d{2,3})(?:\s*[–\-]\s*(\d{2,3}))?\s*(?:s|sek)\b)")
FORMAT_RE = re.compile(r"\b(16:9|9:16)\b")
VO_RE = re.compile(r"VO\b", re.I)
# Kein O-Ton: leere Zelle, nur ein Strich, Strich mit Zusatz „— (KEIN O-Ton …)" oder Text „kein O-Ton".
KEIN_OTON_RE = re.compile(r"^(?:[—–-](?:\s|\(|$)|\(?\s*keine?n?\s+o-?ton)", re.I)
HEADER_FIRST_CELLS = ("#", "Nr", "Nr.")
_PIPE_PLACEHOLDER = "\x00"


@dataclass
class PlanRow:
    nr: str
    szene: str
    oton: str
    quelle: str
    bild: str
    sound: str
    caption: str
    kommentar: str
    typ: str
    plan_dauer_s: float | None
    tc_hints: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PlanRow":
        return cls(nr=str(d["nr"]), szene=d.get("szene", ""), oton=d.get("oton", ""), quelle=d.get("quelle", ""),
                   bild=d.get("bild", ""), sound=d.get("sound", ""), caption=d.get("caption", ""),
                   kommentar=d.get("kommentar", ""), typ=d["typ"], plan_dauer_s=d.get("plan_dauer_s"),
                   tc_hints=[dict(h) for h in d.get("tc_hints", [])])


@dataclass
class Plan:
    file: str
    titel: str
    ziel_laenge_s: float | None
    format_hint: str | None
    rows: list[PlanRow]
    verboten_text: str
    material_text: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Plan":
        return cls(file=d["file"], titel=d.get("titel", ""), ziel_laenge_s=d.get("ziel_laenge_s"),
                   format_hint=d.get("format_hint"), rows=[PlanRow.from_dict(r) for r in d.get("rows", [])],
                   verboten_text=d.get("verboten_text", ""), material_text=d.get("material_text", ""))


def parse_mmss(s: str) -> float:
    """„03:37" → 217.0, „1:02:03" → 3723.0."""
    parts = [int(x) for x in s.strip().split(":")]
    if len(parts) == 2:
        return float(parts[0] * 60 + parts[1])
    if len(parts) == 3:
        return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
    raise ValueError(f"Keine Zeitangabe mm:ss oder h:mm:ss: {s!r}")


def parse_plan_dauer(kommentar: str) -> float | None:
    """Plan-Schätzung „~3 s" aus dem Kommentar; bei „~1–2 s" der obere Wert; None ohne Angabe."""
    m = DAUER_RE.search(kommentar or "")
    if not m:
        return None
    wert = m.group(2) or m.group(1)
    return float(wert.replace(",", "."))


def parse_ziel_laenge(text: str) -> float | None:
    """Ziellänge in Sekunden aus dem Plankopf; bei einem Bereich der obere Wert; None ohne Angabe."""
    m = ZIEL_RE.search(text or "")
    if not m:
        return None
    if m.group(1):
        mm, ss = (m.group(3), m.group(4)) if m.group(3) else (m.group(1), m.group(2))
        return float(int(mm) * 60 + int(ss))
    return float(m.group(6) or m.group(5))


def parse_tc_hints(text: str) -> list[dict]:
    """Findet Datei-Stems und mm:ss(–mm:ss)-Angaben; jede Zeitangabe gehört zum zuletzt genannten Stem.

    Zeitangaben vor dem ersten Stem werden verworfen (kein Bezug). Ergebnis:
    [{"stem": "FX3_9557", "von_s": 217.0, "bis_s": 219.0 | None}, …]
    """
    hints: list[dict] = []
    stem: str | None = None
    for m in TOKEN_RE.finditer(text or ""):
        if m.group(1):
            stem = m.group(1)
            continue
        if stem is None:
            continue
        bis = parse_mmss(m.group(3)) if m.group(3) else None
        hints.append({"stem": stem, "von_s": parse_mmss(m.group(2)), "bis_s": bis})
    return hints


def classify_row(oton: str, quelle: str, bild: str) -> str:
    """Zeilentyp: „vo" (Erzähler), „oton" (Interview-Zitat), „grafik" (Motion/Endcard) oder „bild" (B-Roll)."""
    # Markdown-Hervorhebung („*kein O-Ton*", „_VO_") nur für die Einstufung abstreifen.
    o = (oton or "").strip().strip("*_ ")
    q = (quelle or "").strip().strip("*_ ")
    if VO_RE.match(o) or VO_RE.match(q):
        return "vo"
    if not o or KEIN_OTON_RE.match(o):
        b = (bild or "").lower()
        if any(k in b for k in ("grafik", "endcard", "motion")):
            return "grafik"
        return "bild"
    return "oton"


def _split_row(line: str) -> list[str]:
    """Tabellenzeile in Zellen zerlegen; escaped „\\|" bleibt Zellinhalt."""
    inner = line.strip().strip("|").replace("\\|", _PIPE_PLACEHOLDER)
    return [c.replace(_PIPE_PLACEHOLDER, "|").strip() for c in inner.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


def _parse_rows(text: str) -> list[PlanRow]:
    """Erste Tabelle, deren Kopf mit „#"/„Nr" beginnt; endet an der ersten Nicht-Tabellenzeile."""
    rows: list[PlanRow] = []
    header_found = False
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            if header_found and rows:
                break
            header_found = False
            continue
        cells = _split_row(line)
        if not header_found:
            if cells and cells[0] in HEADER_FIRST_CELLS:
                header_found = True
            continue
        if _is_separator(cells) or len(cells) < 4:
            continue
        cells = (cells + [""] * 8)[:8]
        nr, szene, oton, quelle, bild, sound, caption, kommentar = cells
        if not nr:
            continue
        rows.append(PlanRow(nr=nr, szene=szene, oton=oton, quelle=quelle, bild=bild, sound=sound,
                            caption=caption, kommentar=kommentar, typ=classify_row(oton, quelle, bild),
                            plan_dauer_s=parse_plan_dauer(kommentar), tc_hints=parse_tc_hints(quelle)))
    return rows


def parse_plan(path: str | Path) -> Plan:
    """Cutter-Plan lesen. Fehlt die Ablauf-Tabelle, AutoCutError mit Pfad."""
    p = Path(path)
    if not p.is_file():
        raise AutoCutError(f"Cutter-Plan nicht gefunden: {p}")
    text = p.read_text(encoding="utf-8")
    titel = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), p.stem)
    mf = FORMAT_RE.search(text)
    fmt = mf.group(1) if mf else None
    mv = re.search(r"\*\*Verboten:\*\*\s*(.+?)(?=\n\n|\n\*\*|\n## |\Z)", text, re.S)
    verboten = mv.group(1).strip() if mv else ""
    mm = re.search(r"^## Material[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    material = mm.group(1).strip() if mm else ""
    rows = _parse_rows(text)
    if not rows:
        raise AutoCutError(f"Keine Ablauf-Tabelle im Plan gefunden: {p}\nErwartet wird eine Markdown-Tabelle "
                           f"mit dem Kopf „# | Szene | O-Ton | Quelle | Bild | Sound | Caption | Kommentar“.")
    return Plan(file=str(p), titel=titel, ziel_laenge_s=parse_ziel_laenge(text), format_hint=fmt, rows=rows,
                verboten_text=verboten, material_text=material)
