"""Gyroflow-Stabilisierung für B-Roll (Spec 2026-09-22): Projektdatei je genutzter Quelldatei neben die Mediendatei,
angewendet per OFX im Schnitt. Kein Render, keine zweite Medienhaltung.

Das Glättungs-Preset kommt aus der Telemetrie (``haltung``), nicht aus einem Festwert. Gyroflows eigener Zoom wird über
``max_zoom`` (Prozent, 100 = kein Beschnitt) so gedeckelt, dass der Brennweitenregel ihre ``digitalzoom_faktor``
garantiert bleiben — deshalb braucht es keine Rückkopplung zwischen beiden Beschnitten.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
from pathlib import Path

from .charge import AutoCutError
from .media import fingerprint

CLI_STANDARD = "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
HALTUNG_VORSICHTIG = "stativ"   # Rückfall ohne Telemetrie: wenig glätten, wenig Rand nehmen


def pruefe_deckel(cfg: dict) -> None:
    """Bricht ab, wenn ein ``max_zoom`` der Brennweitenregel ihren Sollzoom nehmen würde.

    ``max_zoom`` ≤ ``digitalzoom_max`` / ``digitalzoom_faktor`` × 100. Wer ``digitalzoom_*`` ändert, muss ``max_zoom``
    mitziehen — sonst stecken beide Beschnitte zusammen über ``digitalzoom_max``."""
    tele = cfg.get("telemetrie") or {}
    faktor, obergrenze = tele.get("digitalzoom_faktor"), tele.get("digitalzoom_max")
    if not faktor or not obergrenze:
        raise AutoCutError("telemetrie.digitalzoom_faktor und telemetrie.digitalzoom_max fehlen in der Config.")
    grenze = float(obergrenze) / float(faktor) * 100.0
    for haltung, wert in ((cfg.get("gyroflow") or {}).get("max_zoom") or {}).items():
        if float(wert) > grenze + 1e-9:
            raise AutoCutError(
                f"gyroflow.max_zoom[{haltung}] = {wert} überschreitet {grenze:.0f} "
                f"(= digitalzoom_max {obergrenze} / digitalzoom_faktor {faktor} × 100).\n"
                f"Entweder max_zoom senken oder telemetrie.digitalzoom_max anheben.")


def preset_fuer(rec: dict, cfg: dict) -> dict:
    """Telemetrie-Datensatz → Gyroflow-Preset. Ohne ``haltung`` gilt die vorsichtigste Stufe."""
    gf = cfg.get("gyroflow") or {}
    haltung = rec.get("haltung") or HALTUNG_VORSICHTIG
    glaettung = (gf.get("glaettung") or {}).get(haltung)
    max_zoom = (gf.get("max_zoom") or {}).get(haltung)
    if glaettung is None or max_zoom is None:
        raise AutoCutError(f"gyroflow.glaettung/max_zoom kennen die Haltung {haltung!r} nicht.")
    return {"version": 2,
            "stabilization": {"smoothing_params": [{"name": "smoothness", "value": float(glaettung)}],
                              "max_zoom": float(max_zoom)}}


def preset_hash(preset: dict) -> str:
    """12 Hex-Zeichen über den Preset-Inhalt; hängt nicht an der Schlüsselreihenfolge."""
    return hashlib.sha1(json.dumps(preset, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def sidecar_pfad(video: str | Path, erlaubte_pfade: set[str]) -> Path:
    """Pfad der ``.gyroflow``-Datei neben der Mediendatei — die einzige Stelle, an der außerhalb der Chargen-Ordner
    geschrieben wird.

    Enge Regel statt aufgeweichtem ``Charge.assert_writable``: geschrieben wird nur neben eine **existierende**
    Mediendatei, die unter genau diesem Pfad in ``telemetrie.json`` geführt ist. Die Endung ist immer ``.gyroflow``,
    der Stamm entspricht dem der Mediendatei — damit wird ein Überschreiben von Material garantiert ausgeschlossen."""
    p = Path(video).expanduser().resolve()
    if str(p) not in {str(Path(e).expanduser().resolve()) for e in erlaubte_pfade}:
        raise AutoCutError(f"Sidecar verweigert: {p} ist nicht in telemetrie.json geführt.")
    if not p.is_file():
        raise AutoCutError(f"Sidecar verweigert: {p} nicht gefunden. Ist das NAS gemountet?")
    if p.suffix.lower() == ".gyroflow":
        raise AutoCutError(f"Sidecar verweigert: {p} ist bereits eine .gyroflow-Datei, nicht eine Mediendatei.")
    return p.with_suffix(".gyroflow")


CACHE_DIR = "gyroflow"


def _cli_aufrufen(cli: str, video: Path, preset: dict, zeitlimit: float) -> None:
    """Gyroflow headless: Projektdatei schreiben, nicht rendern. Wirft AutoCutError mit der Fehlerausgabe."""
    befehl = [cli, str(video), "--export-project", "2", "--preset", json.dumps(preset), "-f"]
    try:
        erg = subprocess.run(befehl, capture_output=True, text=True, timeout=zeitlimit)
    except OSError as e:
        raise AutoCutError(f"Gyroflow-CLI konnte nicht gestartet werden: {cli}\n{type(e).__name__}: {e}\n"
                           f"Pfad in defaults.yaml unter gyroflow.cli prüfen.")
    except subprocess.TimeoutExpired:
        raise AutoCutError(f"Gyroflow hat {video.name} nach {zeitlimit:.0f}s nicht beendet "
                           f"(gyroflow.zeitueberschreitung_s). Liegt die Datei auf einem langsamen Laufwerk?")
    if erg.returncode != 0:
        raise AutoCutError((erg.stderr or erg.stdout or "").strip() or f"Gyroflow endete mit Code {erg.returncode}.")


def clip_export(ch, video, rec: dict, cfg: dict, erlaubte_pfade: set[str],
                force: bool = False) -> tuple[dict, bool]:
    """Sidecar je Quelldatei erzeugen; gibt den Datensatz und zurück, ob er aus dem Cache kam.

    Ein Fehler an einem Clip beendet den Lauf nicht — er landet als ``fehler`` im Datensatz, wie in der Telemetrie."""
    gf = cfg.get("gyroflow") or {}
    video = Path(video)
    preset = preset_fuer(rec, cfg)
    ph = preset_hash(preset)
    fp = fingerprint(video)
    cache = Path(ch.autocut) / CACHE_DIR / f"{fp}.json"

    if cache.exists() and not force:
        try:
            alt = json.loads(cache.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            alt = None
        if isinstance(alt, dict) and not alt.get("fehler") and alt.get("preset_hash") == ph \
                and alt.get("sidecar") and Path(alt["sidecar"]).is_file():
            alt["path"], alt["clip"] = str(video), video.stem
            return alt, True

    datensatz = {"path": str(video), "clip": video.stem, "sidecar": None, "kamera": rec.get("kamera"),
                 "haltung": rec.get("haltung"), "preset_hash": ph, "fingerprint": fp,
                 "exportiert_am": _dt.datetime.now().isoformat(timespec="seconds"),
                 "zoom_ist": None, "zoom_gedeckelt": None, "fehler": None}
    try:
        ziel = sidecar_pfad(video, erlaubte_pfade)
        _cli_aufrufen(gf.get("cli") or CLI_STANDARD, video, preset, float(gf.get("zeitueberschreitung_s") or 300))
        if not ziel.is_file():
            raise AutoCutError(f"Gyroflow meldete Erfolg, aber {ziel.name} fehlt.")
        datensatz["sidecar"] = str(ziel)
    except AutoCutError as e:
        datensatz["fehler"] = str(e)

    ch.assert_writable(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    teil = cache.with_name(f"{cache.name}.{os.getpid()}.part")
    teil.write_text(json.dumps(datensatz, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(teil, cache)
    return datensatz, False


def zoom_ist_lesen(projekt: dict, max_zoom: float) -> tuple[float, bool]:
    """Tatsächlich verbrauchter Zoom als Faktor ≥ 1,0 und ob der Deckel griff.

    Gyroflow rechnet in Prozent (100 = kein Beschnitt). Ohne dekodierte Werte gilt der Deckel als Obergrenze — der
    Haushalt hält dadurch ohnehin, der Bericht nennt den Wert dann als Obergrenze statt als Messwert."""
    deckel = float(max_zoom) / 100.0
    werte = (projekt.get("gyro_source") or {}).get("adaptive_zoom_fovs_dekodiert")
    if not werte:
        return deckel, True
    wert = max(float(w) for w in werte)
    return wert, wert >= deckel - 1e-9
