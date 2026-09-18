"""Ablage: Wurzeln (Repo, NAS, Review, Cache), Chargen-Pfad → Kunde/Projekt, NFC-sicheres Nachschlagen, atomares
Schreiben, Pfadsicherheit, Mac-Name, Zeitstempel. Spec „Ablage"."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

NAS_STANDARD = "/Volumes/NIRO NAS/NIRO Productions/01_Projekte/02_NIRO Productions/08_Claude Tools/NIRO Studio"


class ReviewFehler(Exception):
    """Fehler mit Exit-Code: 1 = Eingabe, 2 = Voraussetzung fehlt (NAS, ffmpeg)."""

    def __init__(self, text: str, code: int = 1):
        super().__init__(text)
        self.code = code


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", str(s))


def repo_wurzel() -> Path:
    env = os.environ.get("NIRO_STUDIO_REPO")
    return Path(env) if env else Path(__file__).resolve().parents[4]


def nas_wurzel() -> Path:
    return Path(os.environ.get("NIRO_STUDIO_NAS") or NAS_STANDARD)


def review_wurzel() -> Path:
    env = os.environ.get("NIRO_REVIEW_ROOT")
    return Path(env) if env else nas_wurzel() / "review"


def nas_verbunden() -> bool:
    return review_wurzel().parent.is_dir()


def cache_wurzel() -> Path:
    env = os.environ.get("NIRO_REVIEW_CACHE")
    return Path(env) if env else Path.home() / "Library" / "Caches" / "NIRO Review"


@dataclass(frozen=True)
class Ziel:
    kunde: str
    projekt: str
    charge: Optional[str]  # „projects/<Kunde>/<Projekt>/<Charge>“ oder None (nur Kunde/Projekt)


def ziel_aufloesen(angabe: str, repo: Optional[Path] = None) -> Ziel:
    """Chargenpfad (relativ ab Studio-Wurzel, mit oder ohne „projects/“, oder absolut) oder „<Kunde>/<Projekt>“."""
    repo = repo or repo_wurzel()
    text = nfc(angabe).strip().rstrip("/")
    p = Path(text)
    if p.is_absolute():
        try:
            rel = p.resolve().relative_to((repo / "projects").resolve())
        except ValueError:
            raise ReviewFehler(f"„{angabe}“ liegt nicht unter {repo / 'projects'}.")
        teile = [nfc(t) for t in rel.parts]
    else:
        teile = [nfc(t) for t in text.split("/") if t]
        if teile and teile[0] == "projects":
            teile = teile[1:]
    if len(teile) == 2:
        return Ziel(teile[0], teile[1], None)
    if len(teile) == 3:
        return Ziel(teile[0], teile[1], "projects/" + "/".join(teile))
    raise ReviewFehler(f"„{angabe}“: erwartet projects/<Kunde>/<Projekt>/<Charge> oder <Kunde>/<Projekt>.")


def finde_kind(eltern: Path, name: str) -> Path:
    """Vorhandenes Kind (Ordner oder Datei) unabhängig von NFC/NFD finden, sonst NFC-Pfad (nicht angelegt)."""
    ziel = nfc(name)
    try:
        for kind in eltern.iterdir():
            if nfc(kind.name) == ziel:
                return kind
    except (FileNotFoundError, NotADirectoryError):
        pass
    return eltern / ziel


def atomar_schreiben(pfad: Path, text: str) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(pfad.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, pfad)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def json_lesen(pfad: Path, standard=None):
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, NotADirectoryError):
        return standard
    except json.JSONDecodeError as e:
        raise ReviewFehler(f"{pfad}: kein gültiges JSON ({e}).", 2)


def json_schreiben(pfad: Path, daten) -> None:
    atomar_schreiben(pfad, json.dumps(daten, ensure_ascii=False, indent=1) + "\n")


def name_ok(s: str) -> bool:
    """Ein Ordner- oder Titelsegment: nicht leer, kein Trenner, nicht „.“/„..“, nicht versteckt."""
    s = nfc(s) if s is not None else ""
    return bool(s) and "/" not in s and "\\" not in s and s not in (".", "..") and not s.startswith(".")


def sicherer_pfad(wurzel: Path, rel: str) -> Optional[Path]:
    """Relativer Pfad (schon URL-dekodiert) unter wurzel, NFD-tolerant — None bei „..“, „.“, absolut oder leer."""
    rel = nfc(rel or "")
    if not rel or rel.startswith("/") or "\\" in rel:
        return None
    teile = [t for t in rel.split("/") if t]
    if not teile or any(t in ("..", ".") for t in teile):
        return None
    ziel = wurzel
    for t in teile:
        ziel = finde_kind(ziel, t)
    try:
        ziel.resolve().relative_to(wurzel.resolve())
    except ValueError:
        return None
    return ziel


def mac_name() -> str:
    try:
        out = subprocess.run(["git", "config", "niro.mac"], capture_output=True, text=True, cwd=str(repo_wurzel()))
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return platform.node().split(".")[0] or "Mac"


def jetzt() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def heute() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def datum_de(iso: str) -> str:
    return f"{iso[8:10]}.{iso[5:7]}.{iso[0:4]}" if iso and len(iso) >= 10 else "—"
