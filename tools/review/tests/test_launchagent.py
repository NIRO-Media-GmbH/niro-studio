from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path

import pytest

from niro_review import launchagent
from niro_review.ablage import ReviewFehler


def test_plist_inhalt():
    roh = launchagent.plist_inhalt("/usr/bin/python3", "/repo/tools/review/review.py", "/repo", 4711, "/log/server.log",
                                   {"NIRO_STUDIO_NAS": "/Volumes/X"})
    d = plistlib.loads(roh)
    assert d["Label"] == "de.niro.review"
    assert d["ProgramArguments"] == ["/usr/bin/python3", "/repo/tools/review/review.py", "server", "--port", "4711"]
    assert d["RunAtLoad"] is True and d["KeepAlive"] is True and d["WorkingDirectory"] == "/repo"
    assert d["StandardOutPath"] == "/log/server.log" and d["StandardErrorPath"] == "/log/server.log"
    assert d["EnvironmentVariables"]["NIRO_STUDIO_NAS"] == "/Volumes/X" and "PATH" in d["EnvironmentVariables"]


def test_installieren_und_deinstallieren(tmp_path, monkeypatch, wurzeln):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    einstieg = wurzeln["repo"] / "tools" / "review" / "review.py"
    einstieg.parent.mkdir(parents=True)
    einstieg.write_text("# Einstieg", encoding="utf-8")
    aufrufe = []

    def launchctl(cmd, **kw):
        aufrufe.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    plist = launchagent.installieren(4711, launchctl=launchctl)
    assert plist == tmp_path / "Library" / "LaunchAgents" / "de.niro.review.plist" and plist.is_file()
    d = plistlib.loads(plist.read_bytes())
    assert d["ProgramArguments"][1] == str(wurzeln["repo"] / "tools" / "review" / "review.py")
    assert d["EnvironmentVariables"]["NIRO_STUDIO_NAS"] == str(wurzeln["nas"])
    assert (tmp_path / "Library" / "Logs" / "NIRO Review").is_dir()
    assert aufrufe[0][:2] == ["launchctl", "bootout"] and aufrufe[1][:2] == ["launchctl", "bootstrap"] and aufrufe[1][3] == str(plist)
    assert launchagent.deinstallieren(launchctl=launchctl) is True and not plist.exists()
    assert aufrufe[2][:2] == ["launchctl", "bootout"]
    assert launchagent.deinstallieren(launchctl=launchctl) is False


def test_installieren_fehler(tmp_path, monkeypatch, wurzeln):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    einstieg = wurzeln["repo"] / "tools" / "review" / "review.py"
    einstieg.parent.mkdir(parents=True)
    einstieg.write_text("# Einstieg", encoding="utf-8")

    def launchctl(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 5 if cmd[1] == "bootstrap" else 0, "", "Input/output error")

    with pytest.raises(ReviewFehler):
        launchagent.installieren(4711, launchctl=launchctl)
