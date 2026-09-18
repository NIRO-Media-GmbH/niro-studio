"""LaunchAgent de.niro.review: Server bei Anmeldung starten, bei Absturz neu starten. Spec „LaunchAgent"."""
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path

from .ablage import ReviewFehler, repo_wurzel

ETIKETT = "de.niro.review"
UMGEBUNG_SCHLUESSEL = ("NIRO_STUDIO_NAS", "NIRO_REVIEW_ROOT", "NIRO_REVIEW_CACHE", "NIRO_STUDIO_REPO")
PATH_STANDARD = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"


def plist_pfad() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{ETIKETT}.plist"


def log_pfad() -> Path:
    return Path.home() / "Library" / "Logs" / "NIRO Review" / "server.log"


def plist_inhalt(python: str, skript: str, repo: str, port: int, log: str, umgebung: dict) -> bytes:
    d = {"Label": ETIKETT, "ProgramArguments": [python, skript, "server", "--port", str(port)],
         "RunAtLoad": True, "KeepAlive": True, "WorkingDirectory": repo,
         "StandardOutPath": log, "StandardErrorPath": log, "ProcessType": "Background",
         "EnvironmentVariables": {"PATH": PATH_STANDARD, **umgebung}}
    return plistlib.dumps(d)


def _ziel() -> str:
    return f"gui/{os.getuid()}"


def installieren(port: int = 4711, launchctl=subprocess.run) -> Path:
    repo = repo_wurzel()
    skript = repo / "tools" / "review" / "review.py"
    if not skript.is_file():
        raise ReviewFehler(f"Einstieg fehlt: {skript}", 2)
    umgebung = {k: os.environ[k] for k in UMGEBUNG_SCHLUESSEL if os.environ.get(k)}
    plist = plist_pfad()
    log = log_pfad()
    log.parent.mkdir(parents=True, exist_ok=True)
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plist_inhalt(sys.executable, str(skript), str(repo), port, str(log), umgebung))
    launchctl(["launchctl", "bootout", f"{_ziel()}/{ETIKETT}"], capture_output=True, text=True)
    r = launchctl(["launchctl", "bootstrap", _ziel(), str(plist)], capture_output=True, text=True)
    if r.returncode != 0:
        raise ReviewFehler(f"launchctl bootstrap scheitert ({r.returncode}): {(r.stderr or r.stdout or '').strip()}", 1)
    return plist


def deinstallieren(launchctl=subprocess.run) -> bool:
    launchctl(["launchctl", "bootout", f"{_ziel()}/{ETIKETT}"], capture_output=True, text=True)
    plist = plist_pfad()
    if plist.exists():
        plist.unlink()
        return True
    return False
