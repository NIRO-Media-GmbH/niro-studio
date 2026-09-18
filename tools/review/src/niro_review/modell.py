"""Datenmodell: video.json / version.json, Versionsnummern, Zustände, Zähler, Titel aus Dateinamen, Sortierung,
Index für die Oberfläche. Kommentar-Regeln liegen in kommentare.py. Spec „Datenmodell"."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from .ablage import finde_kind, jetzt, json_lesen, json_schreiben, nfc, review_wurzel

VERSION_MUSTER = re.compile(r"^V(\d+)$")
_KLAMMER_CLAUDE = re.compile(r"\s*[\(\[]\s*claude[^\)\]]*[\)\]]\s*$", re.IGNORECASE)
_VERSIONSMARKE = re.compile(r"\s*(?:[–\-_]\s*)?(?:entwurf\s*)?v\d+\s*$", re.IGNORECASE)
_NUMMER = re.compile(r"(?<!\d)(\d{1,3})(?!\d)")


def KOMMENTARE_LEER() -> dict:
    return {"naechste_id": 1, "kommentare": []}


def titel_aus_dateiname(name: str) -> str:
    """Endung weg, Versionsmarken am Ende weg („ – Entwurf v1“, „_V6“, „ V2“, „(Claude 2026-09-17)“)."""
    stamm = nfc(Path(name).stem).strip()
    t = stamm
    for _ in range(3):
        t = _KLAMMER_CLAUDE.sub("", t)
        t = _VERSIONSMARKE.sub("", t)
    t = t.strip(" -–_")
    return t or stamm


def sortierung_aus_titel(titel: str) -> str:
    m = _NUMMER.search(nfc(titel)[:40])
    return m.group(1) if m else nfc(titel)


def sortier_schluessel(video: dict):
    s = str(video.get("sortierung") or video.get("titel") or "")
    titel = nfc(str(video.get("titel") or "")).lower()
    if s.isdigit():
        return (0, int(s), titel)
    return (1, 0, nfc(s).lower(), titel)


def video_ordner(kunde: str, projekt: str, titel: str, wurzel: Optional[Path] = None) -> Path:
    w = wurzel if wurzel is not None else review_wurzel()
    return finde_kind(finde_kind(finde_kind(w, kunde), projekt), titel)


def video_lesen(ordner: Path) -> Optional[dict]:
    daten = json_lesen(ordner / "video.json")
    return daten if isinstance(daten, dict) and daten.get("titel") else None


def video_schreiben(ordner: Path, daten: dict) -> None:
    json_schreiben(ordner / "video.json", daten)


def video_anlegen(ordner: Path, kunde: str, projekt: str, titel: str, charge: Optional[str],
                  sortierung: Optional[str] = None) -> dict:
    daten = {"titel": nfc(titel), "kunde": nfc(kunde), "projekt": nfc(projekt), "charge": charge,
             "sortierung": sortierung or sortierung_aus_titel(titel), "angelegt": jetzt(), "freigegeben": None}
    video_schreiben(ordner, daten)
    return daten


def version_ordner(ordner: Path, nr: int) -> Path:
    return ordner / f"V{int(nr)}"


def versionsnummern(ordner: Path) -> list:
    out = []
    try:
        for kind in ordner.iterdir():
            m = VERSION_MUSTER.match(kind.name)
            if m and (kind / "version.json").is_file():
                out.append(int(m.group(1)))
    except (FileNotFoundError, NotADirectoryError):
        pass
    return sorted(out)


def naechste_version(ordner: Path) -> int:
    n = versionsnummern(ordner)
    return (n[-1] + 1) if n else 1


def version_lesen(ordner: Path, nr: int) -> Optional[dict]:
    daten = json_lesen(version_ordner(ordner, nr) / "version.json")
    return daten if isinstance(daten, dict) else None


def version_schreiben(ordner: Path, nr: int, daten: dict) -> None:
    json_schreiben(version_ordner(ordner, nr) / "version.json", daten)


def zustand(video: dict, neueste: Optional[dict]) -> str:
    if video.get("freigegeben"):
        return "freigegeben"
    if neueste is None:
        return "leer"
    if neueste.get("abgeschlossen"):
        return "bei-claude"
    return "review-offen"


def zaehler(kommentare: Optional[dict], geholt_am: Optional[str]) -> dict:
    ks = (kommentare or {}).get("kommentare") or []
    offen = sum(1 for k in ks if k.get("status") in ("offen", "rueckfrage"))
    neu = sum(1 for k in ks if not geholt_am or (k.get("angelegt") or "") > geholt_am)
    return {"offen": offen, "neu": neu, "gesamt": len(ks)}


def _media(kunde: str, projekt: str, ordnername: str, nr: int, datei: str) -> str:
    return "/media/" + "/".join(quote(nfc(t), safe="") for t in (kunde, projekt, ordnername)) + f"/V{nr}/{datei}"


def _kinder(ordner: Path) -> list:
    try:
        return sorted((k for k in ordner.iterdir() if k.is_dir() and not k.name.startswith((".", "_"))),
                      key=lambda p: nfc(p.name).lower())
    except (FileNotFoundError, NotADirectoryError):
        return []


def _video_eintrag(kunde: str, projekt: str, ordner: Path, video: dict) -> dict:
    nrs = versionsnummern(ordner)
    neueste = version_lesen(ordner, nrs[-1]) if nrs else None
    komm = json_lesen(version_ordner(ordner, nrs[-1]) / "kommentare.json", {}) if nrs else {}
    z = zaehler(komm if isinstance(komm, dict) else {}, (neueste or {}).get("geholt_am"))
    return {"titel": video["titel"], "ordner": nfc(ordner.name), "kunde": kunde, "projekt": projekt,
            "sortierung": video.get("sortierung") or video["titel"], "charge": video.get("charge"),
            "zustand": zustand(video, neueste), "versionen": nrs, "neueste": nrs[-1] if nrs else None,
            "angelegt": (neueste or {}).get("angelegt") or video.get("angelegt"),
            "notiz": (neueste or {}).get("notiz") or "", "von": (neueste or {}).get("von"),
            "offen": z["offen"], "neu": z["neu"], "gesamt": z["gesamt"], "freigegeben": video.get("freigegeben"),
            "vorschau": _media(kunde, projekt, ordner.name, nrs[-1], "thumb.jpg") if nrs else None}


def index_bauen(wurzel: Path) -> dict:
    kunden = []
    for k in _kinder(wurzel):
        projekte = []
        for p in _kinder(k):
            videos = []
            for v in _kinder(p):
                video = video_lesen(v)
                if video:
                    videos.append(_video_eintrag(nfc(k.name), nfc(p.name), v, video))
            if not videos:
                continue
            videos.sort(key=sortier_schluessel)
            projekte.append({"name": nfc(p.name), "videos": videos,
                             "offen": sum(v["offen"] for v in videos),
                             "neu": sum(v["neu"] for v in videos),
                             "bei_claude": sum(1 for v in videos if v["zustand"] == "bei-claude"),
                             "review_offen": sum(1 for v in videos if v["zustand"] == "review-offen")})
        if projekte:
            kunden.append({"name": nfc(k.name), "projekte": projekte})
    return {"kunden": kunden}


def video_detail(ordner: Path) -> Optional[dict]:
    video = video_lesen(ordner)
    if not video:
        return None
    versionen = []
    for nr in versionsnummern(ordner):
        v = version_lesen(ordner, nr) or {"nr": nr}
        komm = json_lesen(version_ordner(ordner, nr) / "kommentare.json", None)
        v = dict(v)
        v["nr"] = nr
        v["kommentare"] = (komm or {}).get("kommentare") or [] if isinstance(komm, dict) else []
        v["video_url"] = _media(video["kunde"], video["projekt"], ordner.name, nr, "video.mp4")
        v["vorschau"] = _media(video["kunde"], video["projekt"], ordner.name, nr, "thumb.jpg")
        versionen.append(v)
    neueste = versionen[-1] if versionen else None
    return {"video": video, "ordner": nfc(ordner.name), "versionen": versionen, "zustand": zustand(video, neueste)}
