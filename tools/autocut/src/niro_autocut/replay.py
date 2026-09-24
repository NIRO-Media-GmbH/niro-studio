"""Review in Dropbox Replay (Spec docs/superpowers/specs/2026-09-16-autocut-replay-design.md): Replay-Titel,
Versionsnamen, Replay-Ordner, Bitrate-Grenze und das Upload-Log ``<Charge>/_intern/replay/uploads.json``.

Reine Logik ohne Resolve; das Hochladen selbst steht in ``scripts/autocut_replay.py``.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import unicodedata
from pathlib import Path

from .charge import AutoCutError, Charge

UPLOADS = "uploads.json"
UPLOAD_OK = "Upload Completed"     # erwarteter JobStatus eines erfolgreichen Quick-Export-Uploads
_UNSICHER = re.compile(r'[/\\:*?"<>|]+')
_VERSION = (re.compile(r"^(.*_V)(\d+)$"), re.compile(r"^(.* V)(\d+)$"))


def jetzt() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def replay_dir(ch: Charge) -> Path:
    return ch.intern / "replay"


def titel(timeline: str) -> str:
    """Timeline-Name → Replay-Titel und Dateiname (Replay zeigt ihn mit „.mp4"): ohne / \\ : * ? " < > |."""
    t = _UNSICHER.sub("-", str(timeline)).strip()
    if not t:
        raise AutoCutError(f"Aus dem Timeline-Namen {timeline!r} entsteht kein Dateiname.")
    return t


def naechste_version(name: str) -> str:
    """Kundenschema „…_V3" → „…_V4"; „… V2" → „… V3"; sonst „<Name> V2" (Spec Abschnitt 3).

    Roh-Timelines (Name endet auf „ (roh)") werden nie umbenannt: AutoCutError. Der Bau-Readback und
    ``build.json`` hängen am Namen zur Bauzeit — nach ``SetName`` findet ``readback.laden`` bzw.
    ``autocut_finalize.py`` die roh-Timeline nicht mehr. Der Neubau (Stufe 1, Schritt 8) erzeugt selbst
    einen neuen Namen mit Uhrzeit; versioniert wird erst die End-Timeline nach dem Finalisieren.
    """
    if name.endswith(" (roh)"):
        raise AutoCutError(f"„{name}“ ist eine Roh-Timeline (Name endet auf „ (roh)“) — Roh-Timelines nie "
                           f"umbenennen: für eine neue Version den Neubau (Stufe 1, Schritt 8) nutzen; versioniert "
                           f"wird erst die End-Timeline nach dem Finalisieren.")
    for muster in _VERSION:
        m = muster.match(name)
        if m:
            return f"{m.group(1)}{int(m.group(2)) + 1}"
    return f"{name} V2"


def replay_ordner(ch: Charge) -> str:
    """Replay-Pfad aus ``replay.ordner`` mit Kunde und Projekt der Charge, z. B. „Autocut/Kunde/Projekt"."""
    teile = (ch.config.get("replay") or {}).get("ordner") or ["Autocut", "{kunde}", "{projekt}"]
    return "/".join(str(t).format(kunde=ch.kunde, projekt=ch.projekt) for t in teile)


def video_quality(breite, hoehe, cfg: dict) -> int:
    """Bitrate-Grenze (kbit/s) für den Quick Export: nur bei Timelines über 1920 px; 0 = automatisch."""
    if max(int(breite or 0), int(hoehe or 0)) > 1920:
        return int(cfg.get("video_quality_ueber_1080p") or 0)
    return 0


def lade_uploads(ch: Charge) -> list[dict]:
    p = replay_dir(ch) / UPLOADS
    if not p.exists():
        return []
    try:
        daten = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AutoCutError(f"{p} ist kaputt (kein gültiges JSON: {exc}) — Datei prüfen, nicht von Hand ändern.") from exc
    if not isinstance(daten, list):
        raise AutoCutError(f"{p} ist keine Liste — Datei prüfen (nicht von Hand überschreiben).")
    return daten


def _schreibe_uploads(ch: Charge, eintraege: list[dict]) -> Path:
    p = replay_dir(ch) / UPLOADS
    ch.assert_writable(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(eintraege, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def speichere_upload(ch: Charge, eintrag: dict) -> Path:
    return _schreibe_uploads(ch, lade_uploads(ch) + [dict(eintrag)])


def _nfc(text) -> str:
    """Titelvergleich in NFC: abgetippte Titel (Replay-Seite im Chrome) können eine andere Unicode-Form haben."""
    return unicodedata.normalize("NFC", str(text or ""))


def upload_eintrag(ch: Charge, timeline: str | None = None, titel_: str | None = None) -> dict:
    """Jüngster **erfolgreicher** Upload (optional zu Timeline oder Titel, Titel NFC-normalisiert); AutoCutError, wenn
    keiner passt.

    Gescheiterte Uploads (``upload_status`` ≠ ``UPLOAD_OK``) zählen nicht — sonst würde z. B. ``kommentare`` ohne
    ``--timeline`` nach einem gescheiterten Upload die falsche (nie tatsächlich hochgeladene) Timeline lesen.
    """
    eintraege = [e for e in lade_uploads(ch) if e.get("upload_status") == UPLOAD_OK
                 and (timeline is None or e.get("timeline") == timeline)
                 and (titel_ is None or _nfc(e.get("titel")) == _nfc(titel_))]
    if not eintraege:
        wofuer = f" für '{timeline or titel_}'" if (timeline or titel_) else ""
        raise AutoCutError(f"Kein erfolgreicher Upload{wofuer} in {replay_dir(ch) / UPLOADS} — "
                           f"erst 'autocut_replay.py ... hochladen'.")
    return max(eintraege, key=lambda e: str(e.get("hochgeladen_am") or ""))


def setze_einsortiert(ch: Charge, titel_: str, ordner: str, zeit: str | None = None) -> dict:
    """Einsortieren in Replay vermerken (jüngster **erfolgreicher** Eintrag mit diesem Titel, NFC-normalisiert)."""
    eintraege = lade_uploads(ch)
    passend = [i for i, e in enumerate(eintraege)
               if _nfc(e.get("titel")) == _nfc(titel_) and e.get("upload_status") == UPLOAD_OK]
    if not passend:
        raise AutoCutError(f"Kein erfolgreicher Upload mit Titel '{titel_}' in {replay_dir(ch) / UPLOADS}.")
    i = max(passend, key=lambda j: str(eintraege[j].get("hochgeladen_am") or ""))
    eintraege[i]["replay_ordner"] = ordner
    eintraege[i]["einsortiert_am"] = zeit or jetzt()
    _schreibe_uploads(ch, eintraege)
    return eintraege[i]


def nicht_einsortiert(ch: Charge) -> list[dict]:
    return [e for e in lade_uploads(ch) if e.get("upload_status") == UPLOAD_OK and not e.get("einsortiert_am")]


def ist_hochgeladen(charge_root, timeline: str) -> bool:
    """Steht die Timeline im Upload-Log der Charge? (Finalisieren behält sie dann.) Kaputtes oder falsch geformtes
    Log (kein gültiges JSON bzw. keine Liste) → True (im Zweifel schützen). Zählt jeden Eintrag, auch gescheiterte
    Uploads: die Timeline war trotzdem schon einmal Ziel eines Uploads und soll im Zweifel erhalten bleiben."""
    p = Path(charge_root) / "_intern" / "replay" / UPLOADS
    if not p.exists():
        return False
    try:
        daten = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    if not isinstance(daten, list):
        return True
    return any(isinstance(e, dict) and e.get("timeline") == timeline for e in daten)


def finde_upload(projekt_ordner, replay_titel: str) -> tuple[Path, dict] | None:
    """Replay-Titel (mit oder ohne „.mp4") → (Chargen-Ordner, jüngster **erfolgreicher** Upload) über alle Chargen
    des Projekts. ``projekt_ordner`` muss ein Projekt-Ordner sein (``projects/<Kunde>/<Projekt>``), keine Charge —
    sonst AutoCutError. Der Titelvergleich ist NFC-normalisiert (Unicode-Form aus dem Chrome kann abweichen)."""
    projekt_ordner = Path(projekt_ordner)
    if (projekt_ordner / "_intern" / "replay" / UPLOADS).exists():
        raise AutoCutError(f"{projekt_ordner} ist ein Chargen-Ordner (enthält selbst _intern/replay/{UPLOADS}) — "
                           f"Projekt-Ordner angeben (projects/<Kunde>/<Projekt>).")
    t = _nfc(replay_titel[:-4] if replay_titel.lower().endswith(".mp4") else replay_titel)
    treffer = []
    for p in sorted(projekt_ordner.glob(f"*/_intern/replay/{UPLOADS}")):
        try:
            daten = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AutoCutError(f"{p} ist kaputt (kein gültiges JSON: {exc}) — Datei prüfen, nicht von Hand ändern.") from exc
        for e in daten:
            if isinstance(e, dict) and e.get("upload_status") == UPLOAD_OK and _nfc(e.get("titel")) == t:
                treffer.append((str(e.get("hochgeladen_am") or ""), p.parents[2], e))
    if not treffer:
        return None
    _, charge, e = max(treffer, key=lambda x: x[0])
    return charge, e


def feedback_ordner(ch: Charge, eintrag: dict) -> Path:
    """``Material/Feedback/<Upload-Datum> Replay <Titel>/``."""
    datum = str(eintrag.get("hochgeladen_am") or jetzt())[:10]
    return ch.root / "Material" / "Feedback" / f"{datum} Replay {eintrag['titel']}"
