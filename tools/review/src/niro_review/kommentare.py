"""Kommentare einer Version: anlegen, ändern, löschen, antworten (User über den Server), Umsetzung durch Claude
(alles-oder-nichts), Sortierung, „neu seit geholt_am“, Export als kommentare.md / kommentare.json. Spec „Datenmodell“
und „Export kommentare.md“."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .ablage import ReviewFehler, datum_de, jetzt, json_lesen, json_schreiben
from .medien import frame_aus_timecode, timecode
from .modell import sterne_text

STATUS = ("offen", "umgesetzt", "rueckfrage", "erledigt")
STATUS_USER = ("offen", "erledigt")


def laden(version_ordner: Path) -> dict:
    d = json_lesen(version_ordner / "kommentare.json")
    if not isinstance(d, dict) or not isinstance(d.get("kommentare"), list):
        return {"naechste_id": 1, "kommentare": []}
    nummern = [_nummer(k.get("id")) for k in d["kommentare"] if isinstance(k, dict)]
    d["naechste_id"] = max([int(d.get("naechste_id") or 1)] + [n + 1 for n in nummern if n is not None])
    return d


def speichern(version_ordner: Path, daten: dict) -> None:
    json_schreiben(version_ordner / "kommentare.json", daten)


def _nummer(kid) -> Optional[int]:
    s = str(kid or "")
    return int(s[1:]) if s.startswith("K") and s[1:].isdigit() else None


def finden(daten: dict, kid: str) -> dict:
    for k in daten.get("kommentare") or []:
        if k.get("id") == kid:
            return k
    raise ReviewFehler(f"Kommentar {kid} unbekannt.")


def _text(text) -> str:
    t = str(text or "").strip()
    if not t:
        raise ReviewFehler("Kommentartext fehlt.")
    return t


def anlegen(daten: dict, autor: str, text: str, frame: Optional[int] = None, bis_frame: Optional[int] = None) -> dict:
    text = _text(text)
    autor = str(autor or "").strip() or "Unbekannt"
    if frame is not None:
        frame = int(frame)
        if frame < 0:
            raise ReviewFehler("Frame darf nicht negativ sein.")
    if bis_frame is not None:
        if frame is None:
            raise ReviewFehler("Bereich braucht einen Start-Frame.")
        bis_frame = int(bis_frame)
        if bis_frame <= frame:
            bis_frame = None
    n = int(daten.get("naechste_id") or 1)
    k = {"id": f"K{n}", "frame": frame, "bis_frame": bis_frame, "autor": autor, "text": text, "angelegt": jetzt(),
         "geaendert": None, "status": "offen", "antworten": [], "antwort_claude": None, "tc_neu": None, "frame_neu": None}
    daten.setdefault("kommentare", []).append(k)
    daten["naechste_id"] = n + 1
    return k


def aendern(daten: dict, kid: str, autor: str, text: Optional[str] = None, status: Optional[str] = None) -> dict:
    k = finden(daten, kid)
    if text is not None:
        if k.get("autor") != autor:
            raise ReviewFehler(f"{kid} stammt von {k.get('autor')} — nur der Autor ändert den Text.")
        k["text"] = _text(text)
        k["geaendert"] = jetzt()
    if status is not None:
        if status not in STATUS_USER:
            raise ReviewFehler(f"Status „{status}“: hier erlaubt sind offen und erledigt.")
        k["status"] = status
        k["geaendert"] = jetzt()
    return k


def loeschen(daten: dict, kid: str, autor: str) -> None:
    k = finden(daten, kid)
    if k.get("autor") != autor:
        raise ReviewFehler(f"{kid} stammt von {k.get('autor')} — nur der Autor löscht.")
    daten["kommentare"] = [x for x in daten["kommentare"] if x.get("id") != kid]


def antworten(daten: dict, kid: str, autor: str, text: str) -> dict:
    k = finden(daten, kid)
    a = {"autor": str(autor or "").strip() or "Unbekannt", "text": _text(text), "angelegt": jetzt()}
    k.setdefault("antworten", []).append(a)
    return a


def umsetzung_anwenden(daten: dict, umsetzung: dict, fps: float) -> list:
    """{"K1": {"status": …, "antwort": "…", "tc_neu": "HH:MM:SS:FF" | "frame_neu": int}} — erst alles prüfen, dann
    schreiben. Gibt die geänderten IDs in der Reihenfolge der Umsetzung zurück."""
    if not isinstance(umsetzung, dict) or not umsetzung:
        raise ReviewFehler("Umsetzung: erwartet ein JSON-Objekt {\"K1\": {...}}.")
    geplant = []
    for kid, eintrag in umsetzung.items():
        k = finden(daten, kid)  # ReviewFehler bei unbekannter ID — nichts geschrieben
        if not isinstance(eintrag, dict):
            raise ReviewFehler(f"{kid}: erwartet ein Objekt mit status/antwort/tc_neu.")
        status = eintrag.get("status")
        if status is not None and status not in STATUS:
            raise ReviewFehler(f"{kid}: Status „{status}“ unbekannt (offen, umgesetzt, rueckfrage, erledigt).")
        frame_neu = eintrag.get("frame_neu")
        if frame_neu is not None:
            frame_neu = int(frame_neu)
        elif eintrag.get("tc_neu") is not None:
            frame_neu = frame_aus_timecode(str(eintrag["tc_neu"]), fps)
        antwort = eintrag.get("antwort")
        geplant.append((k, status, str(antwort).strip() if antwort else None, frame_neu))
    for k, status, antwort, frame_neu in geplant:
        if status:
            k["status"] = status
        if antwort:
            k["antwort_claude"] = antwort
        if frame_neu is not None:
            k["frame_neu"] = frame_neu
            k["tc_neu"] = timecode(frame_neu, fps)
    return [k["id"] for k, _, _, _ in geplant]


def sortiert(kommentare: list) -> list:
    return sorted(kommentare, key=lambda k: (0, 0, _nummer(k.get("id")) or 0) if k.get("frame") is None
                  else (1, int(k["frame"]), _nummer(k.get("id")) or 0))


def ist_neu(k: dict, geholt_am: Optional[str]) -> bool:
    if not geholt_am:
        return True
    if (k.get("angelegt") or "") > geholt_am or (k.get("geaendert") or "") > geholt_am:
        return True
    return any((a.get("angelegt") or "") > geholt_am and a.get("autor") != "Claude" for a in k.get("antworten") or [])


def _zelle(text) -> str:
    return str(text or "").replace("\r", "").replace("\n", " ").replace("|", "\\|").strip()


def _antworten_text(k: dict, naechste: int, fps: float) -> str:
    teile = []
    if k.get("antwort_claude"):
        t = f"Claude: {k['antwort_claude']}"
        if k.get("frame_neu") is not None:
            t += f" → V{naechste} {timecode(k['frame_neu'], fps)}"
        teile.append(t)
    teile += [f"{a.get('autor')}: {a.get('text')}" for a in k.get("antworten") or []]
    return " / ".join(teile)


def export_md(video: dict, version: dict, daten: dict, geholt_am_vorher: Optional[str], datum: str) -> str:
    fps = float(version.get("fps") or 25.0)
    nr = int(version.get("nr") or 0)
    kopf = f"# Review-Kommentare „{video.get('titel')}“ V{nr} ({datum}"
    abg = version.get("abgeschlossen")
    if abg:
        kopf += f", abgeschlossen {datum_de(abg.get('am', ''))} {str(abg.get('am', ''))[11:16]} von {abg.get('von')}"
    kopf += ")"
    dauer = float(version.get("dauer_s") or 0)
    zeile = (f"Charge: {video.get('charge') or '—'} · {fps:g} fps · {dauer:.2f} s · {version.get('frames') or '?'} Frames · "
             f"{version.get('breite') or '?'}×{version.get('hoehe') or '?'}")
    if version.get("notiz"):
        zeile += f" · Notiz V{nr}: {_zelle(version['notiz'])}"
    zeilen = [kopf, "", zeile]
    bew = version.get("bewertung")
    if bew:
        b = f"Bewertung V{nr}: {sterne_text(bew)} von {bew.get('von')}"
        if bew.get("text"):
            b += f" — „{_zelle(bew['text'])}“"
        zeilen.append(b)
    zeilen.append("")
    ks = sortiert(daten.get("kommentare") or [])
    if not ks:
        zeilen.append("Keine Kommentare.")
        return "\n".join(zeilen) + "\n"
    zeilen += ["| Nr | ID | TC | Bereich | Kommentar | Antworten | Status | Neu |", "|---|---|---|---|---|---|---|---|"]
    for i, k in enumerate(ks, start=1):
        tc = timecode(k["frame"], fps) if k.get("frame") is not None else "—"
        bereich = f"bis {timecode(k['bis_frame'], fps)}" if k.get("bis_frame") is not None else ("—" if k.get("frame") is None else "")
        neu = "neu" if ist_neu(k, geholt_am_vorher) else ""
        zeilen.append(f"| {i} | {k['id']} | {tc} | {bereich} | {_zelle(k.get('text'))} | "
                      f"{_zelle(_antworten_text(k, nr + 1, fps))} | {k.get('status')} | {neu} |")
    zeilen += ["", "Status: offen = vom User, umgesetzt/rueckfrage = Antwort von Claude, erledigt = vom User abgehakt. "
               "„neu“ = seit dem letzten Holen angelegt, geändert oder vom User beantwortet."]
    return "\n".join(zeilen) + "\n"


def export_json(video: dict, version: dict, daten: dict, geholt_am_vorher: Optional[str]) -> dict:
    fps = float(version.get("fps") or 25.0)
    out = []
    for k in sortiert(daten.get("kommentare") or []):
        e = dict(k)
        e["tc"] = timecode(k["frame"], fps) if k.get("frame") is not None else None
        e["tc_bis"] = timecode(k["bis_frame"], fps) if k.get("bis_frame") is not None else None
        e["neu"] = ist_neu(k, geholt_am_vorher)
        out.append(e)
    return {"quelle": "niro-review", "gelesen_am": jetzt(), "titel": video.get("titel"), "kunde": video.get("kunde"),
            "projekt": video.get("projekt"), "charge": video.get("charge"), "version": int(version.get("nr") or 0),
            "fps": fps, "dauer_s": version.get("dauer_s"), "frames": version.get("frames"),
            "abgeschlossen": version.get("abgeschlossen"), "bewertung": version.get("bewertung"),
            "geholt_am_vorher": geholt_am_vorher, "kommentare": out}
