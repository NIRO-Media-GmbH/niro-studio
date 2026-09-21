"""Index-Nachlauf je Abschnitt (Spec v2 Abschnitt 2): Einstellung, Perspektive, Brennweitenklasse, Bewegungsrichtung,
Hauptmotiv aus einem kompakten Abschnittsbogen (Frames aus dem Cache, keine neue Extraktion) plus lokalem dHash.

Cache: derselbe Clip-Datensatz ``_intern/autocut/broll_index/<fingerprint>.json`` — ``abschnitte[i]`` werden um die neuen
Felder ergänzt, ``nachlauf`` hält Modell/Effort/Usage/Zeit. ``broll_index.json`` wird danach neu geschrieben.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from PIL import Image, ImageDraw

from .broll_index import API_ATTEMPTS, CACHE_DIR, RETRY_ERRORS, _font, _image_block, _make_client
from .charge import TOOL_ROOT, AutoCutError
from .telemetrie import abschnitt_werte, finden, laden as telemetrie_laden

PROMPT_FILE = TOOL_ROOT / "prompts" / "index-sections.md"
EINSTELLUNG5 = ["Totale", "Halbtotale", "Halbnah", "Nah", "Detail"]
HOEHE = ["Augenhöhe", "Aufsicht", "Untersicht", "Vogelperspektive"]
ANSICHT = ["frontal", "seitlich", "schräg", "Rückansicht", "ohne Person"]
BRENNWEITE = ["weit", "normal", "tele"]
RICHTUNG = ["keine", "nach links", "nach rechts", "auf Kamera zu", "von Kamera weg", "gemischt"]
FIELDS = ("einstellung", "perspektive_hoehe", "perspektive_ansicht", "brennweite", "bewegungsrichtung", "hauptmotiv")
ENUMS = {"einstellung": EINSTELLUNG5, "perspektive_hoehe": HOEHE, "perspektive_ansicht": ANSICHT,
         "brennweite": BRENNWEITE, "bewegungsrichtung": RICHTUNG}
REPAIR_ATTEMPTS = 1     # Schema-Verstoß: genau eine Nachfrage mit Fehlerliste, dann Fehler (kein Dauerbeschuss der API)
SECTION_SCHEMA: dict = {
    "type": "object",
    "properties": {"abschnitte": {"type": "array", "items": {"type": "object", "properties": {
        "nr": {"type": "integer"},
        "einstellung": {"type": "string", "enum": EINSTELLUNG5},
        "perspektive_hoehe": {"type": "string", "enum": HOEHE},
        "perspektive_ansicht": {"type": "string", "enum": ANSICHT},
        "brennweite": {"type": "string", "enum": BRENNWEITE},
        "bewegungsrichtung": {"type": "string", "enum": RICHTUNG},
        "hauptmotiv": {"type": "string", "description": "höchstens 6 Wörter"}},
        "required": ["nr", "einstellung", "perspektive_hoehe", "perspektive_ansicht", "brennweite", "bewegungsrichtung", "hauptmotiv"],
        "additionalProperties": False}}},
    "required": ["abschnitte"], "additionalProperties": False}
PAD = 8
KOSTEN = {"texttoken_je_clip": 600, "ausgabetoken_je_clip": 400, "usd_je_mtok_eingabe": 5.0, "usd_je_mtok_ausgabe": 25.0,
          "eur_je_usd": 0.92}


# --- Frames aus dem Cache -------------------------------------------------------

def frames_in_cache(charge, rec: dict) -> list[tuple[Path, float]]:
    """Alle Frames des Erst-Index für diesen Clip (Ordner <stem>.<fp12>), Zeit aus dem Dateinamen (Hundertstel)."""
    stem = Path(str(rec.get("path") or rec.get("datei") or "")).stem
    fp = str(rec.get("fingerprint") or "")
    d = Path(charge.work) / "frames" / f"{stem}.{fp[:12]}"
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob(f"{stem}_*.jpg")):
        tail = p.stem.rsplit("_", 1)[-1]
        if tail.isdigit():
            out.append((p, int(tail) / 100.0))
    return sorted(out, key=lambda x: x[1])


def _nearest(frames: list[tuple[Path, float]], t: float, taken: set[Path]) -> tuple[Path, float] | None:
    cands = [f for f in frames if f[0] not in taken] or frames
    return min(cands, key=lambda f: abs(f[1] - t)) if cands else None


def pick_section_frames(frames: list[tuple[Path, float]], von_s: float, bis_s: float, per_section: int = 2) -> list[tuple[Path, float]]:
    """Kachel a = Frame nächst von_s+0,5, Kachel b = Mitte; Abschnitte unter 1,5 s bekommen nur die Mitte."""
    inside = [f for f in frames if von_s - 0.01 <= f[1] <= bis_s + 0.01] or frames
    if not inside:
        return []
    if bis_s - von_s < 1.5 or per_section == 1:
        f = _nearest(inside, (von_s + bis_s) / 2, set())
        return [f] if f else []
    out: list[tuple[Path, float]] = []
    taken: set[Path] = set()
    for t in (von_s + 0.5, (von_s + bis_s) / 2)[:per_section]:
        f = _nearest(inside, t, taken)
        if f and f[0] not in taken:
            out.append(f)
            taken.add(f[0])
    return sorted(out, key=lambda f: f[1])


def section_sheet(groups: list[list[tuple[Path, float]]], out_path: str | Path, tile_px: int = 480, portrait: bool = False) -> Path:
    """Abschnittsbogen: eine Zeile je Abschnitt, zwei Spalten (a, b); Beschriftung „A<n>·a" links oben in jeder Kachel."""
    if not groups:
        raise AutoCutError("Abschnittsbogen ohne Abschnitte.")
    w, h = (int(tile_px * 9 / 16), int(tile_px)) if portrait else (int(tile_px), int(tile_px * 9 / 16))
    cols = max(1, max(len(g) for g in groups))
    rows = len(groups)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * PAD, rows * h + (rows + 1) * PAD), (16, 16, 16))
    draw = ImageDraw.Draw(sheet)
    font = _font(22)
    for r, g in enumerate(groups):
        for c, (p, t) in enumerate(g):
            x, y = PAD + c * (w + PAD), PAD + r * (h + PAD)
            with Image.open(p) as im:
                sheet.paste(im.convert("RGB").resize((w, h)), (x, y))
            label = f"A{r + 1}·{'ab'[c] if c < 2 else c + 1}  {t:.1f}s"
            _, _, tw, th = font.getbbox(label)
            draw.rectangle([x, y, x + tw + 14, y + th + 8], fill=(0, 0, 0))
            draw.text((x + 7, y + 3), label, fill=(255, 255, 255), font=font)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "JPEG", quality=85)
    return out


def dhash(path: str | Path) -> str:
    """Difference-Hash 8×8 (64 Bit) des Bildes als 16 Hex-Zeichen — nahezu gleiche Kadragen liegen nah beieinander."""
    with Image.open(path) as im:
        g = im.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    px = list(g.tobytes())      # "L"-Bild: ein Byte je Pixel, gleiche Werte wie getdata() ohne dessen Deprecation
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (1 if px[row * 9 + col] > px[row * 9 + col + 1] else 0)
    return f"{bits:016x}"


def hamming(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


# --- Claude -----------------------------------------------------------------------

def telemetrie_text(tele: dict | None, abschnitte: list[dict], fenster_s: float = 2.0) -> str:
    """Kontextzeile für den Abschnittsbogen aus der gemessenen Kamera-Telemetrie; leer ohne Daten.

    ``fenster_s`` muss dasselbe sein, das ``telemetrie_anwenden`` später für denselben Clip verwendet
    (Charge-Override aus ``cfg["telemetrie"]["fenster_s"]``) — sonst zeigt der Hinweis an Claude eine
    andere Bewegungsart, als der Code hinterher tatsächlich in ``bewegungsart`` schreibt."""
    if not tele or tele.get("quelle") in (None, "keine"):
        return ""
    teile = []
    if tele.get("kb_mm"):
        teile.append(f"KB {tele['kb_mm']:g} mm = {tele.get('brennweitenklasse')}")
    if tele.get("pitch_grad") is not None:
        teile.append(f"Pitch {tele['pitch_grad']:g}° = {tele.get('perspektive_hoehe')}")
    if tele.get("haltung"):
        teile.append(f"Haltung {tele['haltung']}")
    arten = [abschnitt_werte(tele, float(a.get("von_s", 0)), float(a.get("bis_s", 0)), fenster_s)["bewegungsart"]
             for a in abschnitte]
    if any(arten):
        teile.append("Bewegungsart je Abschnitt: " + ", ".join(f"A{i} {x or '?'}" for i, x in enumerate(arten, 1)))
    if not teile:
        return ""
    praefix = "Kamera-Telemetrie (gemessen; brennweite und perspektive_hoehe setzt das Schnittprogramm daraus fest): "
    return praefix + " · ".join(teile)


def section_meta_text(rec: dict, tele: dict | None = None, fenster_s: float = 2.0) -> str:
    lines = [f"Clip: {rec.get('datei') or Path(str(rec.get('path', ''))).name}",
             f"Motiv-Ordner: {rec.get('ordner') or '(keiner)'} · Standort: {rec.get('standort') or '(unbekannt)'}",
             f"Kamerabewegung laut Erst-Index: {rec.get('kamerabewegung') or '?'}"]
    t = telemetrie_text(tele, rec.get("abschnitte") or [], fenster_s)
    if t:
        lines.append(t)
    lines.append("")
    for i, a in enumerate(rec.get("abschnitte") or [], 1):
        lines.append(f"Abschnitt {i} = Zeile A{i}: {a.get('von_s')}–{a.get('bis_s')} s — {a.get('beschreibung') or ''}")
    n = len(rec.get("abschnitte") or [])
    lines += ["", f"Antworte mit GENAU {n} Einträgen in abschnitte (nr 1 bis {n}, Reihenfolge wie oben) — auch wenn Abschnitte "
                  f"gleich aussehen, dann dieselben Werte wiederholen. Ein einzelner Eintrag für mehrere Abschnitte ist falsch."]
    return "\n".join(lines)


_TELE_FELDER = (("brennweite", "brennweitenklasse"), ("perspektive_hoehe", "perspektive_hoehe"))


def _tele_felder(tele: dict | None) -> dict[str, str]:
    """Abschnittsfeld → Metadatenklasse, die ``telemetrie_anwenden`` setzt (Brennweite, Pitch); leer ohne Telemetrie."""
    if not tele or tele.get("quelle") in (None, "keine"):
        return {}
    return {feld: tele[k] for feld, k in _TELE_FELDER if tele.get(k)}


def telemetrie_anwenden(rec: dict, tele: dict | None, fenster_s: float = 2.0) -> tuple[dict, bool]:
    """Metadatenklassen in die Abschnitte: brennweite/perspektive_hoehe überschreiben (``felder_quelle`` je Feld „rtmd":
    Brennweite und Pitch stammen immer aus den Metadaten, auch wenn die Bewegung optisch gemessen wurde),
    bewegungsart/haltung ergänzen. Claudes Originalwert je überschriebenem Feld bleibt im Abschnitt unter ``claude``:
    stammt das Feld laut ``felder_quelle`` schon aus der Telemetrie, bleibt ein vorhandenes ``claude[feld]`` stehen
    (der aktuelle Wert ist dann der Telemetrie-Wert), sonst ist der aktuelle Wert Claudes und wird gesichert.
    Idempotent. Liefert (Datensatz, geändert?); ohne Telemetrie unverändert."""
    if not tele or tele.get("quelle") in (None, "keine"):
        return rec, False
    felder = _tele_felder(tele)
    schon = rec.get("felder_quelle") or {}
    quelle: dict[str, str] = {}
    neu = []
    geaendert = False
    for a in rec.get("abschnitte") or []:
        b = dict(a)
        claude = dict(b.get("claude") or {})
        for feld, wert in felder.items():
            if feld not in b:
                continue
            quelle[feld] = "rtmd"
            if feld not in schon:
                claude[feld] = b[feld]
            geaendert |= b.get(feld) != wert
            b[feld] = wert
        if claude:
            geaendert |= b.get("claude") != claude
            b["claude"] = claude
        w = abschnitt_werte(tele, float(b.get("von_s", 0)), float(b.get("bis_s", 0)), fenster_s)
        for k in ("bewegungsart", "haltung"):
            if w.get(k) is not None:
                geaendert |= b.get(k) != w[k]
                b[k] = w[k]
        neu.append(b)
    out = {**rec, "abschnitte": neu}
    if quelle:
        geaendert |= rec.get("felder_quelle") != quelle
        out["felder_quelle"] = quelle
    return out, geaendert


def _cache_schreiben(charge, rec: dict) -> None:
    """Clip-Datensatz atomar in den Cache (ohne ``_``-Schlüssel). Je Schreiber ein eindeutiger ``.part``-Name
    (pid + Thread-Id): läuft auch bei Cache-Treffern, zwei Schreiber desselben Clips kollidieren sonst im selben .part."""
    cache_dir = Path(charge.autocut) / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{rec['fingerprint']}.json"
    charge.assert_writable(cache_file)
    persist = {k: v for k, v in rec.items() if not k.startswith("_")}
    part = cache_file.with_name(f"{cache_file.name}.{os.getpid()}-{threading.get_ident()}.part")
    part.write_text(json.dumps(persist, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(part, cache_file)


def validate_sections(data: dict, n: int) -> list[str]:
    from .broll_index import _validate
    probs: list[str] = []
    _validate(SECTION_SCHEMA, data, "Antwort", probs)
    abs_ = data.get("abschnitte") if isinstance(data, dict) else None
    if isinstance(abs_, list) and len(abs_) != n:
        probs.append(f"abschnitte: {len(abs_)} Einträge, Clip hat {n} Abschnitte")
    elif isinstance(abs_, list) and [a.get("nr") for a in abs_ if isinstance(a, dict)] != list(range(1, n + 1)):
        probs.append("abschnitte: nr muss 1..n in Reihenfolge sein")
    return probs


def normalize_sections(data):
    """Schreibweise der Enum-Felder angleichen und Strings trimmen (Live 04.09.: „auf Kamera Zu“, „von Kamera Weg“ kamen
    als Schema-Verstoß zurück, obwohl nur Groß-/Kleinschreibung abwich). Unbekannte Werte bleiben stehen und fallen in
    ``validate_sections`` auf; alles außer ``abschnitte`` bleibt unverändert (auch ``_usage``)."""
    if not isinstance(data, dict) or not isinstance(data.get("abschnitte"), list):
        return data
    out = []
    for a in data["abschnitte"]:
        if not isinstance(a, dict):
            out.append(a)
            continue
        b = dict(a)
        for k, v in b.items():
            if isinstance(v, str):
                v = v.strip()
                if k in ENUMS:
                    v = next((e for e in ENUMS[k] if e.casefold() == v.casefold()), v)
                b[k] = v
        out.append(b)
    return {**data, "abschnitte": out}


def repair_hint(probs: list[str], n: int) -> str:
    """Zusatz an den Aufgabentext für die Nachfrage nach einem Schema-Verstoß."""
    return ("\n\nDeine vorige Antwort verletzt das Schema: " + "; ".join(probs[:6]) + ". "
            f"Antworte erneut mit GENAU {n} Einträgen in abschnitte (nr 1 bis {n}, Reihenfolge wie oben), "
            "Werte exakt aus den Listen in der angegebenen Schreibweise, keine weiteren Felder.")


def _add_usage(total: dict, u: dict | None) -> None:
    for k in total:
        total[k] += int((u or {}).get(k, 0) or 0)


def describe_sections(client, sheet: Path, meta_text: str, cfg: dict, system_prompt: str) -> dict:
    content = [{"type": "text", "text": "Abschnittsbogen:"}, _image_block(Path(sheet)), {"type": "text", "text": meta_text}]
    max_tokens = int(cfg.get("max_tokens", 2500))
    resp = None
    for attempt in range(API_ATTEMPTS):
        try:
            resp = client.messages.create(
                model=cfg["model"], max_tokens=max_tokens,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": SECTION_SCHEMA}, "effort": cfg.get("effort", "medium")})
            break
        except RETRY_ERRORS as e:
            if attempt == API_ATTEMPTS - 1:
                raise AutoCutError(f"Nachlauf-Anfrage nach {API_ATTEMPTS} Versuchen fehlgeschlagen: {e}") from e
            time.sleep(3 * 2 ** attempt + random.uniform(0, 1))
        except anthropic.APIStatusError as e:
            raise AutoCutError(f"Nachlauf-Anfrage abgewiesen (HTTP {e.status_code}): {getattr(e, 'message', e)}") from e
    stop = getattr(resp, "stop_reason", None)
    if stop == "refusal":
        raise AutoCutError("Claude hat die Abschnittsbeschreibung abgelehnt.")
    if stop == "max_tokens":
        raise AutoCutError(f"Antwort abgeschnitten (max_tokens {max_tokens}) — index_sections.max_tokens erhöhen.")
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), None)
    if text is None:
        raise AutoCutError(f"keine Textantwort (stop_reason={stop}).")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise AutoCutError(f"Nachlauf-Antwort ist kein gültiges JSON: {e}") from e
    u = resp.usage
    data["_usage"] = {"input": int(getattr(u, "input_tokens", 0) or 0), "output": int(getattr(u, "output_tokens", 0) or 0),
                      "cache_read": int(getattr(u, "cache_read_input_tokens", 0) or 0),
                      "cache_write": int(getattr(u, "cache_creation_input_tokens", 0) or 0)}
    return data


def load_system_prompt() -> str:
    if not PROMPT_FILE.is_file():
        raise AutoCutError(f"System-Prompt fehlt: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


# --- je Clip / gesamt ------------------------------------------------------------------

def needs_sections(rec: dict, max_sections: int = 5) -> bool:
    """True, wenn einem der ersten ``max_sections`` Abschnitte eines der Nachlauf-Felder fehlt.

    Nur die ersten ``max_sections`` zählen — mehr indiziert ``index_sections_clip`` ohnehin nicht,
    sonst gälte ein Clip mit mehr Abschnitten für immer als offen (Dauerbeschuss der API)."""
    abs_ = (rec.get("abschnitte") or [])[:max_sections]
    return not abs_ or any(any(k not in a for k in FIELDS) or not a.get("setup_hash") for a in abs_)


def index_sections_clip(charge, rec: dict, client, cfg: dict, system_prompt: str, force: bool = False,
                        describe=describe_sections, telemetrie: dict | None = None) -> dict:
    """Einen Clip nachindexieren: Cache-Treffer (``_cache`` True) oder Bogen → Claude → dHash → Cache-Datei mergen.

    Abschnitte ohne Frame im Fenster ``[von_s, bis_s]`` bekommen den nächstgelegenen Frame als Ersatz
    (``pick_section_frames`` fällt selbst darauf zurück); liegt dessen Zeit mehr als 1,0 s außerhalb des
    Fensters, landet eine Warnung in ``warnungen`` und die tatsächlich genutzten Frame-Zeiten in ``frame_s``.

    ``telemetrie`` = Datensatz des Clips aus ``telemetrie.json`` (``finden``) oder None: gibt dem Abschnittsbogen eine
    Kontextzeile und wird nach der Antwort per ``telemetrie_anwenden`` eingetragen (Fensterlänge aus
    ``cfg["telemetrie"]["fenster_s"]``). Im API-Pfad hält ``claude`` je Abschnitt die frischen Modellwerte der
    überschriebenen Felder. Auch ein Cache-Treffer wird neu in den Cache geschrieben, wenn die Telemetrie etwas ändert.
    """
    scfg = cfg["index_sections"]
    icfg = cfg["index"]
    fenster_s = float((cfg.get("telemetrie") or {}).get("fenster_s", 2.0))
    max_sections = int(scfg.get("max_sections", 5))
    if not force and not needs_sections(rec, max_sections):
        neu, geaendert = telemetrie_anwenden(rec, telemetrie, fenster_s)
        if geaendert:
            _cache_schreiben(charge, neu)
        return {**neu, "_cache": True}
    abs_ = rec.get("abschnitte") or []
    if not abs_:
        raise AutoCutError("Clip ohne Abschnitte im Erst-Index — Nachlauf nicht möglich.")
    if len(abs_) > max_sections:
        abs_ = abs_[:max_sections]
    frames = frames_in_cache(charge, rec)
    if not frames:
        raise AutoCutError("keine Frames im Cache (work/frames) — Erst-Index für diesen Clip mit --force wiederholen.")
    groups = [pick_section_frames(frames, float(a["von_s"]), float(a["bis_s"]), int(scfg.get("per_section", 2))) for a in abs_]
    stem, fp = Path(str(rec["path"])).stem, str(rec["fingerprint"])
    sheet = section_sheet(groups, Path(charge.work) / "sheets" / f"{stem}.{fp[:12]}_A.jpg", int(scfg.get("tile_px", 480)),
                          portrait=str(rec.get("orientierung") or "") == "9:16")
    call_cfg = {"model": icfg["model"], "effort": scfg.get("effort", icfg.get("effort", "medium")),
                "max_tokens": scfg.get("max_tokens", 2500)}
    meta_text = section_meta_text({**rec, "abschnitte": abs_}, telemetrie, fenster_s)
    usage = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    reparaturen = 0
    data = normalize_sections(describe(client, sheet, meta_text, call_cfg, system_prompt))
    _add_usage(usage, data.pop("_usage", {}))
    probs = validate_sections(data, len(abs_))
    while probs and reparaturen < REPAIR_ATTEMPTS:
        # Schema-Verstoß (Live 04.09.: 24 Clips „1 Einträge, Clip hat 3 Abschnitte“) — einmal mit Fehlerliste nachfragen,
        # bevor der bezahlte Clip als Fehler verbucht wird. Beide Anfragen zählen in der Usage.
        reparaturen += 1
        data = normalize_sections(describe(client, sheet, meta_text + repair_hint(probs, len(abs_)), call_cfg, system_prompt))
        _add_usage(usage, data.pop("_usage", {}))
        probs = validate_sections(data, len(abs_))
    if probs:
        raise AutoCutError(f"Antwort verletzt das Schema (auch nach {reparaturen} Nachfrage): " + "; ".join(probs[:6]))
    warnungen = list(rec.get("warnungen") or [])
    # brennweite/perspektive_hoehe kommen hier frisch aus der Modellantwort: ``claude`` daraus neu setzen (ein altes gilt
    # nicht mehr) — für die Felder, die die Telemetrie jetzt überschreibt oder felder_quelle aus einem früheren Lauf führt
    ueberschrieben = [f for f, _ in _TELE_FELDER if f in _tele_felder(telemetrie) or f in (rec.get("felder_quelle") or {})]
    merged = []
    for i, (a, s, g) in enumerate(zip(rec.get("abschnitte") or [], data["abschnitte"], groups), 1):
        mid = g[-1][0] if g else None
        entry = {**{k: v for k, v in a.items() if k != "claude"}, **{k: s[k] for k in FIELDS},
                 "setup_hash": dhash(mid) if mid else ""}
        if ueberschrieben:
            entry["claude"] = {f: s[f] for f in ueberschrieben}
        if g:
            t = g[-1][1]
            von_s, bis_s = float(a["von_s"]), float(a["bis_s"])
            distanz = max(0.0, von_s - t, t - bis_s)      # 0, wenn t im Fenster liegt
            if distanz > 1.0:
                warnungen.append(f"Abschnitt {i}: kein Frame im Cache, nächster Frame bei {t:.1f} s")
                entry["frame_s"] = [ft for _, ft in g]
        merged.append(entry)
    merged += list((rec.get("abschnitte") or [])[len(merged):])      # über max_sections hinaus: unverändert
    out = {**rec, "abschnitte": merged, "abschnittsbogen": str(sheet), "warnungen": warnungen,
           "nachlauf": {"modell": call_cfg["model"], "effort": call_cfg["effort"], "usage": usage, "reparaturen": reparaturen,
                        "indiziert_am": _dt.datetime.now().isoformat(timespec="seconds")}}
    out, _ = telemetrie_anwenden(out, telemetrie, fenster_s)
    _cache_schreiben(charge, out)
    return {**out, "_cache": False}


def estimate_sections_cost(recs: list[dict], tile_px: int = 480, per_section: int = 2, max_sections: int = 5) -> str:
    k = KOSTEN
    w = per_section * tile_px + (per_section + 1) * PAD
    total_in = 0.0
    for r in recs:
        n = max(1, min(max_sections, len(r.get("abschnitte") or [])))
        h = n * int(tile_px * 9 / 16) + (n + 1) * PAD
        total_in += (-(-w // 28)) * (-(-h // 28)) + k["texttoken_je_clip"]
    usd = total_in / 1e6 * k["usd_je_mtok_eingabe"] + len(recs) * k["ausgabetoken_je_clip"] / 1e6 * k["usd_je_mtok_ausgabe"]
    eur = usd * k["eur_je_usd"]
    return f"{len(recs)} Clips ≈ {eur * 0.7:.1f}–{eur * 1.3:.1f} € (Opus 5; Abschnittsbögen ~{int(total_in / max(1, len(recs)))} Token je Clip)".replace(".", ",")


def index_sections(charge, index: dict, cfg: dict, limit: int | None = None, parallel: int = 4, force: bool = False) -> dict:
    """Alle Clips des Index nachindexieren (Cache je Clip), broll_index.json neu schreiben; Fehler je Clip sammeln."""
    clips = list(index.get("clips") or [])
    todo = clips[:limit] if limit else clips
    client = _make_client(cfg["index"])
    prompt = load_system_prompt()
    results: dict[str, dict] = {}
    errors: list[str] = []
    hits = 0
    reparaturen = 0
    usage_sum = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    tele = telemetrie_laden(Path(charge.autocut))
    mit_tele = 0
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel)))
    try:
        futs = {}
        for c in todo:
            t = finden(tele, str(c["path"]))
            mit_tele += int(t is not None and t.get("quelle") not in (None, "keine"))     # nur Datensätze mit Daten
            futs[ex.submit(index_sections_clip, charge, c, client, cfg, prompt, force, telemetrie=t)] = c
        for i, fut in enumerate(as_completed(futs), 1):
            c = futs[fut]
            name = Path(str(c["path"])).name
            try:
                rec = fut.result()
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"[{i}/{len(todo)}] FEHLER {name}: {e}", flush=True)
                continue
            if rec.pop("_cache", False):
                hits += 1
                tag = "Cache"
            else:
                tag = "API  "
                nl = rec.get("nachlauf") or {}
                _add_usage(usage_sum, nl.get("usage"))
                reparaturen += int(nl.get("reparaturen", 0) or 0)
            results[str(c["path"])] = rec
            first = (rec.get("abschnitte") or [{}])[0]
            print(f"[{i}/{len(todo)}] {tag} {name}: {first.get('einstellung', '?')} / {first.get('perspektive_ansicht', '?')} / "
                  f"{first.get('brennweite', '?')}", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    new_clips = [results.get(str(c["path"]), c) for c in clips]
    nachlauf = {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"), "anzahl": len(results),
                "cache_treffer": hits, "usage_summe": usage_sum, "reparaturen": reparaturen, "fehler": errors,
                "mit_telemetrie": mit_tele}
    out = {**index, "clips": new_clips, "nachlauf": nachlauf}
    charge.write_json("broll_index.json", out)
    return {"anzahl": len(results), "cache_treffer": hits, "fehler": errors, "usage_summe": usage_sum,
            "reparaturen": reparaturen, "uebersprungen": len(clips) - len(todo), "mit_telemetrie": mit_tele}
