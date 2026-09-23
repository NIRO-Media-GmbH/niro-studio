"""Gyroflow-Stabilisierung für B-Roll (Spec 2026-09-22): Projektdatei je genutzter Quelldatei neben die Mediendatei,
angewendet per OFX im Schnitt. Kein Render, keine zweite Medienhaltung.

Das Glättungs-Preset kommt aus der Telemetrie (``haltung``), nicht aus einem Festwert. Gyroflows eigener Zoom wird über
``max_zoom`` (Prozent, 100 = kein Beschnitt) gedeckelt — das begrenzt **nur Gyroflows Beschnitt**. Der digitale Zoom
der Brennweitenregel kommt obendrauf; die beiden sind heute nicht verrechnet (Spec 2026-09-22, Abschnitt 4).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
import unicodedata
from pathlib import Path

from .charge import AutoCutError
from .media import fingerprint

CLI_STANDARD = "/Applications/Gyroflow.app/Contents/MacOS/gyroflow"
HALTUNG_VORSICHTIG = "stativ"   # Rückfall ohne Telemetrie: wenig glätten, wenig Rand nehmen


def norm_pfad(p) -> str:
    """Einheitlicher Schlüssel für jeden Join über Medienpfade: aufgelöst **und** Unicode-NFC.

    Begründung wie ``resolve_api._norm``: macOS liefert Dateinamen teils in NFD, und ``Path.resolve()`` rechnet die
    Unicode-Form nicht um — es löst nur Mount-Aliase, ``~`` und Symlinks auf. Ohne NFC greift der Join still daneben,
    sobald ein Kunden- oder Ortsordner ein Nicht-ASCII-Zeichen trägt; sichtbar wird das als „kein Telemetrie-Eintrag"
    bei Clips, die offensichtlich Telemetrie haben. Alle Pfad-Joins rund um Gyroflow laufen über diese Funktion —
    auch der in der 6d-Vorlage (dort als ``GF.norm_pfad``)."""
    return unicodedata.normalize("NFC", str(Path(p).expanduser().resolve()))


def pruefe_deckel(cfg: dict) -> None:
    """Hält Gyroflows eigenen Beschnitt unter ``max_zoom`` ≤ ``digitalzoom_max`` / ``digitalzoom_faktor`` × 100.

    **Was das garantiert:** nur, dass Gyroflow je Haltung höchstens den hier eingetragenen Anteil vom Rand nimmt
    (Standard 1,05× bis 1,2×). Wer ``digitalzoom_*`` ändert, muss ``max_zoom`` mitziehen, sonst wird der Deckel
    stillschweigend großzügiger als gedacht.

    **Was das NICHT garantiert:** einen Gesamtzoom unter ``digitalzoom_max``. Die Brennweitenregel
    (``telemetrie.digitalzoom``) rechnet ``zoom × faktor × längere / kürzere`` und lässt bis ``digitalzoom_max``
    (1,5) zu — nicht bloß ``digitalzoom_faktor`` (1,25), wie die erste Fassung der Spec annahm. Ihr digitaler Zoom
    kommt auf Gyroflows Beschnitt obendrauf: heute im schlimmsten Fall 1,2 × 1,5 = 1,8× auf einer 4K-Quelle.
    Gyroflows Beschnitt als vorhandenen Zoom in die Brennweitenregel zu geben ist vereinbart, aber noch nicht
    umgesetzt (Spec 2026-09-22, Abschnitt 4)."""
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
                f"Die Grenze deckelt allein Gyroflows Beschnitt — der digitale Zoom der Brennweitenregel kommt "
                f"obendrauf (bis digitalzoom_max {obergrenze}).\n"
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
    p = Path(norm_pfad(video))
    if str(p) not in {norm_pfad(e) for e in erlaubte_pfade}:
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

    ``max_zoom`` kommt in Prozent (100 = kein Beschnitt) und wird hier in einen Faktor umgerechnet; dekodierte Werte
    in ``adaptive_zoom_fovs_dekodiert`` werden dagegen **schon als Faktor ≥ 1,0 erwartet**, nicht in Prozent. Diesen
    Schlüssel schreibt heute niemand — die Dekodierung ist ungeklärt (Spec Befund 1, Punkt 6), der Zweig ist der Haken
    dafür. In der Praxis greift also immer der Rückfall: Rückgabe ist dann der Deckelwert, kein Messwert, und der
    Bericht muss ihn als Obergrenze ausweisen."""
    deckel = float(max_zoom) / 100.0
    werte = (projekt.get("gyro_source") or {}).get("adaptive_zoom_fovs_dekodiert")
    if not werte:
        return deckel, True
    wert = max(float(w) for w in werte)
    return wert, wert >= deckel - 1e-9


def gyroflow_charge(ch, clips: list[dict], telemetrie: list[dict], cfg: dict, force: bool = False) -> dict:
    """Sidecars für die genutzten B-Roll-Shots; je Quelldatei einer, auch bei Mehrfachnutzung.

    Übersprungen wird mit Grund statt still: ohne Gyrospur, ohne Telemetrie-Eintrag, oder ``_stabilized`` im Namen
    (Avata-Export — nie erneut stabilisieren, wie in 6d).

    ``zoom_ist``/``zoom_gedeckelt`` kommen je erfolgreich exportiertem Clip aus dem Deckel-Rückfall von
    ``zoom_ist_lesen`` — eine echte Messung aus der Gyroflow-Projektdatei ist ohne Reverse-Engineering ihres
    internen Formats nicht mit vertretbarem Aufwand zu haben (siehe deren Docstring). Fehlerhafte und übersprungene
    Einträge bleiben bei ``None``. Läuft absichtlich sequenziell statt parallel wie ``telemetrie_charge``: der
    Cache-Tempname in ``clip_export`` enthält keine Thread-Id."""
    pruefe_deckel(cfg)
    nach_pfad = {norm_pfad(r["path"]): r for r in telemetrie if r.get("path")}
    erlaubte = set(nach_pfad)

    ergebnisse, uebersprungen, gesehen = [], [], set()
    for eintrag in clips:
        p = norm_pfad(eintrag["datei"])
        if p in gesehen:
            continue
        gesehen.add(p)
        rec = nach_pfad.get(p)
        if rec is None:
            uebersprungen.append({"datei": p, "grund": "kein Telemetrie-Eintrag"})
        elif "_stabilized" in Path(p).stem:
            uebersprungen.append({"datei": p, "grund": "Avata-Export (_stabilized)"})
        elif rec.get("quelle") != "rtmd":
            uebersprungen.append({"datei": p, "grund": "keine Gyrospur"})
        else:
            datensatz, _ = clip_export(ch, p, rec, cfg, erlaubte, force=force)
            if not datensatz.get("fehler"):
                deckel = preset_fuer(rec, cfg)["stabilization"]["max_zoom"]
                datensatz["zoom_ist"], datensatz["zoom_gedeckelt"] = zoom_ist_lesen({}, deckel)
            ergebnisse.append(datensatz)

    erg = {"clips": ergebnisse, "uebersprungen": uebersprungen,
           "stand": _dt.datetime.now().isoformat(timespec="seconds")}
    ziel = Path(ch.autocut) / "gyroflow.json"
    ch.assert_writable(ziel)
    ziel.write_text(json.dumps(erg, ensure_ascii=False, indent=1), encoding="utf-8")
    return erg
