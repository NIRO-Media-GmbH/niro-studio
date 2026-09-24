"""B-Roll-Index: Szenenwechsel und Frames aus den Proxies, Kontaktbögen mit eingebrannten Kachelnummern,
Claude-Vision mit Structured Output, Cache pro Clip (Fingerprint des Originals).

Ablauf je Clip (``index_clip``):
  1. Fingerprint des Originals → Cache-Treffer unter ``_intern/autocut/broll_index/<fp>.json``?
  2. ffprobe (Proxy und Original), Szenenwechsel per ffmpeg ``select='gt(scene,T)'`` im Proxy
  3. Frame-Raster (``frame_times``) → Einzelbilder (``extract_frames``) → Kontaktbögen (``contact_sheets``)
  4. Claude (``describe_clip``): Bilder zuerst, je mit Label „Kontaktbogen n:", danach Metadaten + Kachel-Tabelle;
     System-Prompt aus ``prompts/index-clip.md`` mit ``cache_control`` (≥ 1024 Token, Cache-Treffer im ``usage``)
  5. Antwort gegen ``CLIP_SCHEMA`` geprüft, Datensatz atomar in den Cache geschrieben

NAS wird nur gelesen; Frames und Bögen liegen unter ``<Charge>/_intern/autocut/work``.
"""
from __future__ import annotations

import base64
import datetime as _dt
import json
import os
import random
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import dotenv_values
from PIL import Image, ImageDraw, ImageFont

from .charge import TOOL_ROOT, AutoCutError
from .media import PROXY_DIR, _assert_not_nas, _which, check_proxy_match, ffprobe, fingerprint, is_portrait, proxy_for

VIDEO_EXTS = {".mp4", ".mov"}
CACHE_DIR = "broll_index"
MAX_IMAGES_PER_REQUEST = 20     # API-Grenze je Anfrage; bei frames_max 24 und Gitter 4x3 sind es höchstens 2 Bögen
API_ATTEMPTS = 4                # eigene Wiederholungen zusätzlich zu max_retries=5 des SDK
MAX_TOKENS_CAP = 16000          # Obergrenze für die automatische Verdopplung bei abgeschnittener Antwort
PROMPT_FILE = TOOL_ROOT / "prompts" / "index-clip.md"
ENV_FILE = TOOL_ROOT / ".env"
FONT_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
                   "/System/Library/Fonts/Helvetica.ttc")
LABEL_PX = 26

# Feste Wertelisten (Spec 4). broll.forbidden_maengel in defaults.yaml muss eine Teilmenge von MAENGEL sein.
MAENGEL = ["Unschärfe", "Wackler", "Blick in Kamera", "Mikro im Bild", "Crew im Bild", "Logo/Marke",
           "Überbelichtung", "Unterbelichtung", "zu kurz", "Anschnitt"]
EIGNUNG = ["Opener", "Detail", "Übergang", "Emotion", "Beweis", "Team", "Ort", "Arbeit"]
EINSTELLUNG = ["Totale", "Halbtotale", "Halbnah", "Nah", "Detail", "gemischt"]
KAMERABEWEGUNG = ["statisch", "Schwenk", "Fahrt", "Handkamera", "Gimbal", "Drohne", "Zoom", "gemischt"]
TEMPO = ["ruhig", "mittel", "schnell"]
SCORE = [1, 2, 3, 4, 5]

# Kostenannahmen für estimate_cost (Opus 5, Stand 09/2026): 4x3-Bogen à 640x360 ≈ 3.700 Bildtoken,
# adaptives Denken zählt zu den Ausgabetoken; Cache-Lesen des System-Prompts ist vernachlässigbar.
KOSTEN = {"bildtoken_je_bogen": 3700, "boegen_je_clip": 2, "texttoken_je_clip": 400, "ausgabetoken_je_clip": 1000,
          "usd_je_mtok_eingabe": 5.0, "usd_je_mtok_ausgabe": 25.0, "eur_je_usd": 0.92}

# Schema-Regeln für Structured Outputs: additionalProperties false, alle Felder required,
# keine minimum/maximum/minLength/maxLength/pattern/format, Scores als Enum.
CLIP_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "beschreibung_kurz": {"type": "string", "description": "höchstens 12 Wörter"},
        "beschreibung": {"type": "string", "description": "2–4 Sätze, nur Sichtbares"},
        "motive": {"type": "array", "items": {"type": "string"}},
        "personen": {"type": "object", "properties": {
            "anzahl": {"type": "integer"},
            "beschreibung": {"type": "string", "description": "Rolle und Merkmale, keine Namen"},
            "gesicht_erkennbar": {"type": "boolean"},
            "blick_in_kamera": {"type": "boolean"}},
            "required": ["anzahl", "beschreibung", "gesicht_erkennbar", "blick_in_kamera"],
            "additionalProperties": False},
        "einstellung": {"type": "string", "enum": EINSTELLUNG},
        "kamerabewegung": {"type": "string", "enum": KAMERABEWEGUNG},
        "tempo": {"type": "string", "enum": TEMPO},
        "stimmung": {"type": "string"},
        "licht": {"type": "string"},
        "abschnitte": {"type": "array", "items": {"type": "object", "properties": {
            "von_s": {"type": "number"}, "bis_s": {"type": "number"},
            "beschreibung": {"type": "string"},
            "qualitaet": {"type": "integer", "enum": SCORE},
            # Mängel je Abschnitt (Spec 2026-09-23): die clip-weite Liste bleibt die Vereinigung, die Sperre
            # in verify_layout() liest aber diese hier — ein Mangel in einer Sekunde darf keinen Clip kosten.
            "maengel": {"type": "array", "items": {"type": "string", "enum": MAENGEL}},
            "verwendbar": {"type": "boolean"}},
            "required": ["von_s", "bis_s", "beschreibung", "qualitaet", "maengel", "verwendbar"],
            "additionalProperties": False}},
        "maengel": {"type": "array", "items": {"type": "string", "enum": MAENGEL}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "eignung": {"type": "array", "items": {"type": "string", "enum": EIGNUNG}},
        "qualitaet_gesamt": {"type": "integer", "enum": SCORE},
    },
    "required": ["beschreibung_kurz", "beschreibung", "motive", "personen", "einstellung", "kamerabewegung", "tempo",
                 "stimmung", "licht", "abschnitte", "maengel", "tags", "eignung", "qualitaet_gesamt"],
    "additionalProperties": False,
}

# Fehler, bei denen eine Wiederholung mit Backoff sinnvoll ist (Ratelimit, Netz, Überlast, 5xx).
RETRY_ERRORS = (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError,
                anthropic.OverloadedError, anthropic.ServiceUnavailableError, anthropic.DeadlineExceededError)


# --- Clips finden -------------------------------------------------------------

def broll_roots(index_records: list[dict], extra_roots: list[str | Path] | None = None) -> list[dict]:
    """B-Roll-Wurzeln ``<Footage>/Sortiert/B-Roll`` aus den Interview-Pfaden des Transkript-Index (+ Extra-Wurzeln).

    Ergebnis je Wurzel: ``{"root", "standort", "vorhanden"}``; Standort aus dem Ordner über ``Sortiert``
    („Standort 1"), sonst None. Extra-Wurzeln (Mavic, Actioncam) haben keinen Standort.
    """
    roots: dict[Path, str | None] = {}
    for rec in index_records:
        p = Path(rec["path"])
        for anc in p.parents:
            if anc.name == "Sortiert":
                parent = anc.parent.name
                roots.setdefault(anc / "B-Roll", parent if parent.lower().startswith("standort") else None)
                break
    for extra in extra_roots or []:
        roots.setdefault(Path(extra).expanduser(), None)
    return [{"root": str(r), "standort": s, "vorhanden": r.is_dir()} for r, s in sorted(roots.items())]


def discover_broll(index_records: list[dict], extra_roots: list[str | Path] | None = None) -> list[dict]:
    """Alle Videodateien unter den B-Roll-Wurzeln: ``{"path", "ordner", "standort"}``.

    Rekursiv ``*.MP4/*.MOV``; ``Proxy``-Ordner, AppleDouble-Dateien (``._x``) und Sidecars (XML) bleiben außen vor.
    ``ordner`` ist der Motiv-Pfad relativ zur Wurzel („Flur", „Flur/Detail", "" in der Wurzel), Leerzeichen an den
    Rändern der Ordnernamen werden entfernt (auf dem NAS gibt es „Notaufnahme ").
    """
    clips: list[dict] = []
    for r in broll_roots(index_records, extra_roots):
        if not r["vorhanden"]:
            continue
        root = Path(r["root"])
        for f in sorted(root.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in VIDEO_EXTS or f.name.startswith("._"):
                continue
            rel_dirs = f.relative_to(root).parts[:-1]
            if PROXY_DIR in rel_dirs:
                continue
            clips.append({"path": str(f), "ordner": "/".join(part.strip() for part in rel_dirs), "standort": r["standort"]})
    return clips


# --- Szenen, Frames, Kontaktbögen --------------------------------------------------

def scene_cuts(proxy: Path, threshold: float) -> list[float]:
    """Zeitpunkte (s) der Szenenwechsel per ffmpeg ``select='gt(scene,T)',showinfo`` — sortiert, ohne Dubletten."""
    proxy = Path(proxy)
    if not proxy.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {proxy}\nIst das NAS gemountet?")
    cmd = [_which("ffmpeg"), "-hide_banner", "-nostats", "-i", str(proxy), "-an", "-sn",
           "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise AutoCutError(f"Szenenerkennung fehlgeschlagen für {proxy.name}: {r.stderr[-300:]}")
    return sorted({round(float(m), 2) for m in re.findall(r"pts_time:\s*([0-9.]+)", r.stderr)})


def frame_times(duration_s: float, cuts: list[float], cfg: dict) -> list[float]:
    """Frame-Raster: je Abschnitt Anfang+0,5 s, Mitte, Ende−0,5 s plus alle ``frame_interval_s``;
    mindestens ``frames_min`` (gleichmäßig aufgefüllt), höchstens ``frames_max`` (gleichmäßig ausgedünnt)."""
    if not duration_s or duration_s <= 0:
        raise AutoCutError(f"Ungültige Clipdauer {duration_s} s — Datei defekt oder ffprobe ohne Dauer.")
    fmin, fmax, step = int(cfg["frames_min"]), int(cfg["frames_max"]), float(cfg["frame_interval_s"])
    bounds = [0.0] + sorted(c for c in cuts if 0.5 < c < duration_s - 0.5) + [float(duration_s)]
    times: list[float] = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 1.0:
            times.append((a + b) / 2)
            continue
        times += [a + 0.5, (a + b) / 2, b - 0.5]
        t = a + step
        while t < b - 0.5:
            times.append(t)
            t += step
    times = sorted({round(t, 2) for t in times if 0.0 <= t <= duration_s})
    if len(times) < fmin:
        raster = duration_s / (fmin + 1)
        times = sorted(set(times) | {round(raster * (i + 1), 2) for i in range(fmin)})
    if len(times) > fmax:
        idx = [round(i * (len(times) - 1) / max(fmax - 1, 1)) for i in range(fmax)]
        times = [times[i] for i in idx]
    return times


def extract_frames(proxy: Path, times: list[float], out_dir: Path, tile_px: int, portrait: bool) -> list[tuple[Path, float]]:
    """Einzelbilder als JPEG: Breite ``tile_px`` (Hochkant: Höhe ``tile_px``), gecacht im out_dir.
    Zeiten hinter dem Clip-Ende liefern kein Bild und werden stillschweigend übersprungen."""
    proxy, out_dir = Path(proxy), Path(out_dir)
    if not proxy.is_file():
        raise AutoCutError(f"Datei nicht gefunden: {proxy}\nIst das NAS gemountet?")
    _assert_not_nas(out_dir, "Frame-Extraktion")
    out_dir.mkdir(parents=True, exist_ok=True)
    scale = f"scale=-2:{int(tile_px)}" if portrait else f"scale={int(tile_px)}:-2"
    ffmpeg = _which("ffmpeg")
    frames: list[tuple[Path, float]] = []
    for t in times:
        out = out_dir / f"{proxy.stem}_{int(round(t * 100)):07d}.jpg"
        if not out.exists():
            cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(proxy),
                   "-frames:v", "1", "-vf", scale, "-q:v", "3", str(out)]
            subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if out.exists() and out.stat().st_size == 0:
            out.unlink()
        if out.exists():
            frames.append((out, t))
    return frames


def _font(size: int = LABEL_PX):
    for p in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def tile_label(nr: int, t: float) -> str:
    """Kachelbeschriftung „3 · 00:04.9" (Nummer, mm:ss.s; kaufmännisch gerundet)."""
    mins = int(t // 60)
    secs = round(t - mins * 60 + 1e-9, 1)
    if secs >= 60:
        mins, secs = mins + 1, 0.0
    return f"{nr} · {mins:02d}:{secs:04.1f}"


def contact_sheets(frames: list[tuple[Path, float]], grid: tuple[int, int], out_prefix: Path,
                   pad_px: int = 8) -> list[Path]:
    """Kontaktbögen ``<prefix>_1.jpg, _2.jpg …``: Gitter cols×rows, dunkler Grund, ``pad_px`` Steg innen und außen,
    je Kachel links oben Kachelnummer + Zeitstempel eingebrannt (fortlaufend über alle Bögen)."""
    cols, rows = int(grid[0]), int(grid[1])
    per = cols * rows
    if not frames:
        return []
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(frames[0][0]) as first:
        w, h = first.size
    font = _font()
    sheets: list[Path] = []
    for n in range(0, len(frames), per):
        chunk = frames[n:n + per]
        r = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * w + (cols + 1) * pad_px, r * h + (r + 1) * pad_px), (16, 16, 16))
        draw = ImageDraw.Draw(sheet)
        for i, (p, t) in enumerate(chunk):
            x = pad_px + (i % cols) * (w + pad_px)
            y = pad_px + (i // cols) * (h + pad_px)
            with Image.open(p) as im:
                tile = im.convert("RGB")
                if tile.size != (w, h):
                    tile = tile.resize((w, h))
                sheet.paste(tile, (x, y))
            label = tile_label(n + i + 1, t)
            _, _, tw, th = font.getbbox(label)
            draw.rectangle([x, y, x + tw + 16, y + th + 10], fill=(0, 0, 0))
            draw.text((x + 8, y + 4), label, fill=(255, 255, 255), font=font)
        out = out_prefix.with_name(f"{out_prefix.name}_{n // per + 1}.jpg")
        sheet.save(out, "JPEG", quality=85)
        sheets.append(out)
    return sheets


# --- Claude ---------------------------------------------------------------------

def _image_block(path: Path) -> dict:
    data = base64.standard_b64encode(Path(path).read_bytes()).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}}


def _meta_text(meta: dict) -> str:
    cuts = meta.get("cuts") or []
    lines = [f"Clip: {meta.get('name', '?')}",
             f"Motiv-Ordner (Name des Teams beim Sortieren): {meta.get('ordner') or '(keiner)'}",
             f"Standort: {meta.get('standort') or '(unbekannt)'}",
             f"Dauer: {meta.get('dauer_s')} s",
             f"Orientierung: {meta.get('orientierung')}",
             "Automatisch erkannte Szenenwechsel (s): " + (", ".join(str(c) for c in cuts) if cuts else "keine"),
             "",
             "Kacheln (Nr = Sekunde im Clip), fortlaufend über alle Kontaktbögen, je Bogen links oben nach rechts unten:"]
    lines += [f"Kachel {k['nr']} = {k['s']} s" for k in meta.get("kacheln") or []]
    lines += ["", "Zeiten in abschnitte ausschließlich aus dieser Tabelle und den Szenenwechseln ableiten; "
                  "der erste Abschnitt beginnt bei 0, der letzte endet bei der Clip-Dauer."]
    return "\n".join(lines)


_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


def _validate(schema: dict, value, path: str, probs: list[str]) -> None:
    t = schema.get("type")
    if t:
        ok = isinstance(value, _TYPES[t]) and not (t in ("integer", "number") and isinstance(value, bool))
        if not ok:
            probs.append(f"{path}: erwartet {t}, erhalten {type(value).__name__}")
            return
    if "enum" in schema and value not in schema["enum"]:
        probs.append(f"{path}: „{value}“ nicht in {schema['enum']}")
    if t == "object":
        for k in schema.get("required", []):
            if k not in value:
                probs.append(f"{path}.{k} fehlt")
        for k, v in value.items():
            if k in schema.get("properties", {}):
                _validate(schema["properties"][k], v, f"{path}.{k}", probs)
            elif schema.get("additionalProperties") is False and not k.startswith("_"):
                probs.append(f"{path}.{k} unbekannt")
    elif t == "array":
        for i, v in enumerate(value):
            _validate(schema["items"], v, f"{path}[{i}]", probs)


def validate_clip_record(data: dict) -> list[str]:
    """Modellantwort gegen CLIP_SCHEMA prüfen (Typen, Pflichtfelder, Enums) plus Sinnregeln:
    Abschnitte mit bis_s > von_s ≥ 0, Personenzahl ≥ 0. Leere Liste = in Ordnung."""
    probs: list[str] = []
    _validate(CLIP_SCHEMA, data, "Antwort", probs)
    for i, a in enumerate(data.get("abschnitte") or []):
        if isinstance(a, dict) and isinstance(a.get("von_s"), (int, float)) and isinstance(a.get("bis_s"), (int, float)):
            if a["von_s"] < 0:
                probs.append(f"abschnitte[{i}]: von_s {a['von_s']} < 0")
            if a["bis_s"] <= a["von_s"]:
                probs.append(f"abschnitte[{i}]: bis_s {a['bis_s']} liegt nicht nach von_s {a['von_s']}")
    personen = data.get("personen")
    if isinstance(personen, dict) and isinstance(personen.get("anzahl"), int) and personen["anzahl"] < 0:
        probs.append("personen.anzahl < 0")
    return probs


def _create_message(client, cfg: dict, system_prompt: str, content: list[dict], max_tokens: int, name: str):
    """Ein API-Aufruf mit Backoff bei Ratelimit/Netz/Überlast; andere HTTP-Fehler sofort als AutoCutError."""
    for attempt in range(API_ATTEMPTS):
        try:
            return client.messages.create(
                model=cfg["model"], max_tokens=max_tokens,
                system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": content}],
                output_config={"format": {"type": "json_schema", "schema": CLIP_SCHEMA}, "effort": cfg.get("effort", "medium")},
            )
        except RETRY_ERRORS as e:
            if attempt == API_ATTEMPTS - 1:
                raise AutoCutError(f"Claude-Anfrage für {name} nach {API_ATTEMPTS} Versuchen fehlgeschlagen: {e}") from e
            time.sleep(3 * 2 ** attempt + random.uniform(0, 1))
        except anthropic.APIStatusError as e:
            raise AutoCutError(f"Claude-Anfrage für {name} abgewiesen (HTTP {e.status_code}, {type(e).__name__}): "
                               f"{getattr(e, 'message', e)}") from e
    raise AutoCutError(f"Claude-Anfrage für {name} ohne Antwort.")


def describe_clip(client, sheets: list[Path], meta: dict, cfg: dict, system_prompt: str) -> dict:
    """Ein Clip = eine Anfrage: Kontaktbögen (je „Kontaktbogen n:" + Bild), dann Metadaten + Kachel-Tabelle.
    Structured Output nach CLIP_SCHEMA, System-Prompt mit Cache-Marke, Backoff bei Ratelimit/Netz/Überlast.
    Denk-Token zählen gegen max_tokens: bei Abschneiden wird einmal mit doppeltem Budget wiederholt.
    Ergebnis: geprüfte Antwort plus ``_usage`` {input, output, cache_read, cache_write}."""
    name = meta.get("name", "?")
    if len(sheets) > MAX_IMAGES_PER_REQUEST:
        raise AutoCutError(f"{name}: {len(sheets)} Kontaktbögen — höchstens {MAX_IMAGES_PER_REQUEST} Bilder je Anfrage. "
                           f"index.frames_max verkleinern oder index.grid vergrößern.")
    content: list[dict] = []
    for i, s in enumerate(sheets, 1):
        content.append({"type": "text", "text": f"Kontaktbogen {i}:"})
        content.append(_image_block(Path(s)))
    content.append({"type": "text", "text": _meta_text(meta)})
    max_tokens = int(cfg.get("max_tokens", 4000))
    resp = _create_message(client, cfg, system_prompt, content, max_tokens, name)
    if getattr(resp, "stop_reason", None) == "max_tokens" and max_tokens < MAX_TOKENS_CAP:
        max_tokens = min(max_tokens * 2, MAX_TOKENS_CAP)
        resp = _create_message(client, cfg, system_prompt, content, max_tokens, name)
    stop = getattr(resp, "stop_reason", None)
    if stop == "refusal":
        det = getattr(resp, "stop_details", None)
        raise AutoCutError(f"{name}: Claude hat die Beschreibung abgelehnt (Kategorie {getattr(det, 'category', None)}: "
                           f"{getattr(det, 'explanation', '') or 'ohne Begründung'}). Clip von Hand beschreiben.")
    if stop == "max_tokens":
        raise AutoCutError(f"{name}: Antwort auch mit max_tokens={max_tokens} abgeschnitten — "
                           f"index.max_tokens in der Config erhöhen oder index.effort senken.")
    text = next((b.text for b in resp.content if getattr(b, "type", "") == "text"), None)
    if text is None:
        raise AutoCutError(f"{name}: keine Textantwort von Claude (stop_reason={stop}).")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise AutoCutError(f"{name}: Antwort ist kein gültiges JSON: {e}") from e
    probs = validate_clip_record(data)
    if probs:
        raise AutoCutError(f"{name}: Antwort verletzt das Schema: " + "; ".join(probs[:8]))
    u = resp.usage
    data["_usage"] = {"input": int(getattr(u, "input_tokens", 0) or 0),
                      "output": int(getattr(u, "output_tokens", 0) or 0),
                      "cache_read": int(getattr(u, "cache_read_input_tokens", 0) or 0),
                      "cache_write": int(getattr(u, "cache_creation_input_tokens", 0) or 0)}
    return data


def load_system_prompt() -> str:
    if not PROMPT_FILE.is_file():
        raise AutoCutError(f"System-Prompt fehlt: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def _make_client(cfg_index: dict) -> anthropic.Anthropic:
    """Anthropic-Client mit max_retries=5; Schlüssel aus der Umgebung oder tools/autocut/.env (ohne die Umgebung zu ändern)."""
    key = os.environ.get("ANTHROPIC_API_KEY") or dotenv_values(ENV_FILE).get("ANTHROPIC_API_KEY")
    if not key:
        raise AutoCutError(f"ANTHROPIC_API_KEY fehlt — in {ENV_FILE} eintragen (scripts/setup_env.py) "
                           f"oder als Umgebungsvariable setzen.")
    return anthropic.Anthropic(api_key=key, max_retries=5)


# --- Index je Clip und gesamt --------------------------------------------------------

def cached_record(charge, path: str | Path) -> dict | None:
    """Cache-Eintrag des Clips (Fingerprint des Originals) oder None."""
    p = charge.autocut / CACHE_DIR / f"{fingerprint(path)}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def index_clip(charge, clip: dict, client, cfg: dict, system_prompt: str | None = None, force: bool = False) -> dict:
    """Einen Clip indexieren: Cache-Treffer (``_cache`` True) oder Proxy → Frames → Bögen → Claude → Cache.

    ``cfg`` ist die ganze Charge-Config (``cfg["index"]`` wird genutzt). Der Datensatz enthält Datei, Proxy, Fingerprint,
    Ordner, Standort, Dauer/fps/Orientierung, Szenenwechsel, Kachel-Tabelle, Kontaktbogen-Pfade, Warnungen,
    Modell/Effort/Usage und die Modellantwort. ``force`` fragt trotz Cache neu an (z. B. nach Prompt-Änderung).
    """
    icfg = cfg["index"]
    path = Path(clip["path"])
    fp = fingerprint(path)                       # AutoCutError, wenn die Datei fehlt (NAS nicht gemountet)
    cache_dir = charge.autocut / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{fp}.json"
    if cache_file.exists() and not force:
        rec = json.loads(cache_file.read_text(encoding="utf-8"))
        # Pfad, Ordner und Standort kommen aus der aktuellen Suche: der Fingerprint hängt nicht am Pfad,
        # ein nachträglich umsortierter Clip trüge sonst den alten Motiv-Ordner aus dem Cache.
        rec["path"], rec["datei"] = str(path), path.name
        for k in ("ordner", "standort"):
            if k in clip:
                rec[k] = clip[k]
        rec["_cache"] = True
        return rec

    warnungen: list[str] = []
    proxy = proxy_for(path)
    src = proxy or path
    if proxy is None:
        warnungen.append("Kein Proxy neben dem Original — Original wird gelesen (langsam, volle Auflösung).")
    info = ffprobe(src)
    orig = info if proxy is None else ffprobe(path)
    if proxy is not None:
        warnungen += [f"Proxy passt nicht zum Original: {p}" for p in check_proxy_match(orig, info)]
    dauer = round(orig.duration_s if orig.duration_s > 0 else info.duration_s, 2)
    raster_dauer = min(dauer, round(info.duration_s, 2)) if info.duration_s > 0 else dauer
    cuts = scene_cuts(src, float(icfg["scene_threshold"]))
    times = frame_times(raster_dauer, cuts, icfg)
    portrait = is_portrait(info)
    key = f"{path.stem}.{fp[:12]}"               # Dateinamen der Kameras wiederholen sich über Standorte hinweg
    frames = extract_frames(src, times, charge.work / "frames" / key, int(icfg["tile_px"]), portrait)
    if not frames:
        raise AutoCutError(f"{path.name}: keine Frames aus {src.name} extrahiert — Datei defekt oder Proxy leer?")
    sheets = contact_sheets(frames, (int(icfg["grid"][0]), int(icfg["grid"][1])), charge.work / "sheets" / key,
                            pad_px=int(icfg.get("pad_px", 8)))
    kacheln = [{"nr": i, "s": t} for i, (_, t) in enumerate(frames, 1)]
    meta = {"name": path.name, "ordner": clip.get("ordner", ""), "standort": clip.get("standort"), "dauer_s": dauer,
            "orientierung": "9:16" if portrait else "16:9", "cuts": cuts, "kacheln": kacheln}
    data = describe_clip(client, sheets, meta, icfg, system_prompt or load_system_prompt())
    usage = data.pop("_usage")
    ende = max((float(a["bis_s"]) for a in data["abschnitte"]), default=0.0)
    if abs(ende - dauer) > 1.0:
        warnungen.append(f"Abschnitte enden bei {ende} s, der Clip dauert {dauer} s — Zeiten prüfen.")
    rec = {"path": str(path), "datei": path.name, "proxy": str(proxy) if proxy else None, "fingerprint": fp,
           "ordner": meta["ordner"], "standort": meta["standort"], "dauer_s": dauer, "fps": info.fps,
           "orientierung": meta["orientierung"], "szenenwechsel_s": cuts, "kacheln": kacheln,
           "kontaktboegen": [str(s) for s in sheets], "warnungen": warnungen,
           "modell": icfg["model"], "effort": icfg.get("effort", "medium"), "usage": usage,
           "indiziert_am": _dt.datetime.now().isoformat(timespec="seconds"), **data}
    charge.assert_writable(cache_file)
    part = cache_file.with_name(cache_file.name + ".part")   # atomar: halbe Datei darf nie als Cache-Treffer gelten
    part.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(part, cache_file)
    return {**rec, "_cache": False}


def estimate_cost(n_clips: int) -> str:
    k = KOSTEN
    eingabe = (k["bildtoken_je_bogen"] * k["boegen_je_clip"] + k["texttoken_je_clip"]) / 1e6 * k["usd_je_mtok_eingabe"]
    ausgabe = k["ausgabetoken_je_clip"] / 1e6 * k["usd_je_mtok_ausgabe"]
    je_clip = (eingabe + ausgabe) * k["eur_je_usd"]
    von, bis = n_clips * je_clip * 0.7, n_clips * je_clip * 1.3
    stellen = 2 if bis < 10 else 0
    return (f"{n_clips} Clips × ~{je_clip:.3f} € ≈ {von:.{stellen}f}–{bis:.{stellen}f} € "
            f"(Opus 5: ~{k['boegen_je_clip']} Kontaktbögen à ~{k['bildtoken_je_bogen']} Bildtoken + "
            f"~{k['ausgabetoken_je_clip']} Ausgabetoken je Clip; Cache-Treffer kosten nichts)").replace(".", ",")


def index_broll(charge, clips: list[dict], cfg: dict, limit: int | None = None, parallel: int = 4,
                force: bool = False) -> dict:
    """Clips (in Reihenfolge, optional die ersten ``limit``) parallel indexieren, Fortschritt ausgeben,
    Ergebnis nach ``_intern/autocut/broll_index.json`` schreiben. Fehler je Clip werden gesammelt, nicht geworfen;
    Ctrl-C bricht ab — der Cache behält alle fertigen Clips, ein neuer Lauf setzt fort."""
    icfg = cfg["index"]
    todo = list(clips[:limit]) if limit else list(clips)
    client = _make_client(icfg)
    system_prompt = load_system_prompt()
    results: dict[str, dict] = {}
    errors: list[str] = []
    hits = 0
    usage_sum = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    ex = ThreadPoolExecutor(max_workers=max(1, int(parallel)))
    try:
        futs = {ex.submit(index_clip, charge, c, client, cfg, system_prompt, force): c for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            c = futs[fut]
            name = Path(c["path"]).name
            try:
                rec = fut.result()
            except AutoCutError as e:
                errors.append(f"{name}: {e}")
                print(f"[{i}/{len(todo)}] FEHLER {name}: {e}", flush=True)
                continue
            except Exception as e:  # ein defekter Clip darf den Lauf nicht beenden
                errors.append(f"{name}: unerwarteter Fehler {type(e).__name__}: {e}")
                print(f"[{i}/{len(todo)}] FEHLER {name}: {type(e).__name__}: {e}", flush=True)
                continue
            if rec.pop("_cache", False):
                hits += 1
                tag = "Cache"
            else:
                tag = "API  "
                for k in usage_sum:
                    usage_sum[k] += int((rec.get("usage") or {}).get(k, 0))
            results[c["path"]] = rec
            print(f"[{i}/{len(todo)}] {tag} {name}: {rec.get('beschreibung_kurz', '')}", flush=True)
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    # Teil- oder Testlauf (--limit, Fehler einzelner Clips) ergänzt den vorhandenen Index, statt ihn zu ersetzen: für jeden
    # noch gefundenen Clip gilt das Ergebnis dieses Laufs, sonst der Eintrag aus dem vorigen broll_index.json. Clips, die
    # unter den Wurzeln nicht mehr liegen, fallen heraus. (Live 04.09.: --limit 5 nach 461 Clips hätte die Datei auf
    # 5 Einträge gekürzt — --compact/--raster/verify hätten bis zum nächsten Volllauf auf 5 Clips gearbeitet.)
    alt = (charge.read_json("broll_index.json") if hasattr(charge, "read_json") else None) or {}
    alt_by_path = {str(c["path"]): c for c in (alt.get("clips") or []) if isinstance(c, dict) and c.get("path")}
    merged = [results[c["path"]] if c["path"] in results else alt_by_path[c["path"]]
              for c in clips if c["path"] in results or c["path"] in alt_by_path]
    out = {"erstellt_am": _dt.datetime.now().isoformat(timespec="seconds"), "modell": icfg["model"],
           "effort": icfg.get("effort", "medium"), "anzahl": len(results), "clips_gesamt": len(merged), "cache_treffer": hits,
           "usage_summe": usage_sum, "fehler": errors, "clips": merged}
    charge.write_json("broll_index.json", out)
    return out


# --- Bericht ------------------------------------------------------------------------

def _md(s) -> str:
    return str(s or "").replace("|", "/").replace("\n", " ").strip()


def _dauer(d) -> str:
    return f"{float(d):.1f} s".replace(".", ",") if isinstance(d, (int, float)) else "–"


def render_broll_index_md(index: dict) -> str:
    """Markdown-Bericht: je Standort und Motiv-Ordner eine Tabelle mit einer Zeile pro Clip, danach die Fehler."""
    clips = index.get("clips", [])
    fehler = index.get("fehler", [])
    lines = ["# B-Roll-Index", "",
             f"Stand: {index.get('erstellt_am', '–')} · Modell: {index.get('modell', '–')} · "
             f"Clips: {index.get('anzahl', len(clips))} · Fehler: {len(fehler)}", ""]
    groups: dict[str, dict[str, list[dict]]] = {}
    for c in clips:
        groups.setdefault(c.get("standort") or "Ohne Standort", {}).setdefault(c.get("ordner") or "(Wurzel)", []).append(c)
    for standort in sorted(groups, key=lambda s: (s == "Ohne Standort", s)):
        lines += [f"## {standort}", ""]
        for ordner in sorted(groups[standort]):
            rows = groups[standort][ordner]
            lines += [f"### {ordner} ({len(rows)} Clips)", "",
                      "| Datei | Dauer | Einstellung | Kamera | Kurzbeschreibung | Q | Abschn. | Mängel | Eignung |",
                      "|---|---|---|---|---|---|---|---|---|"]
            for c in sorted(rows, key=lambda c: c.get("datei", "")):
                abschnitte = c.get("abschnitte") or []
                verwendbar = sum(1 for a in abschnitte if a.get("verwendbar"))
                lines.append(f"| {_md(c.get('datei'))} | {_dauer(c.get('dauer_s'))} | {_md(c.get('einstellung'))} | "
                             f"{_md(c.get('kamerabewegung'))} | {_md(c.get('beschreibung_kurz'))} | "
                             f"{c.get('qualitaet_gesamt', '')} | {verwendbar}/{len(abschnitte)} | "
                             f"{_md(', '.join(c.get('maengel') or [])) or '–'} | {_md(', '.join(c.get('eignung') or [])) or '–'} |")
            lines.append("")
    if fehler:
        lines += ["## Fehler", ""] + [f"- {_md(f)}" for f in fehler] + [""]
    return "\n".join(lines)
