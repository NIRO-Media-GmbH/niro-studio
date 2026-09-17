"""Quelle Git (Spec 2.1): Commits des Tages auf main und je Branch, Vorsprung zu origin/main, unversionierte
Änderungen je Worktree, Stashes. Dazu die Sicherung der unversionierten Änderungen als Patch (Spec 2.6)."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from umgebung import tagesgrenzen

TRENNER = "\x1f"
BEISPIELE_MAX = 8
PATCH_DATEI_MAX = 1024 * 1024
PATCH_GESAMT_MAX = 5 * 1024 * 1024


class GitFehler(Exception):
    pass


@dataclass
class Commit:
    zeit: str
    hash: str
    betreff: str


@dataclass
class Branch:
    name: str
    vor: int | None
    hinter: int | None
    letzter: str
    worktree: str | None
    commits_heute: list[Commit] = field(default_factory=list)


@dataclass
class Gruppe:
    pfad: str
    geaendert: int = 0
    neu: int = 0
    geloescht: int = 0
    juengste: str = ""
    beispiele: list[str] = field(default_factory=list)
    weitere: int = 0


@dataclass
class Worktree:
    pfad: str
    branch: str
    ist_haupt: bool
    gruppen: list[Gruppe] = field(default_factory=list)


@dataclass
class GitStand:
    head_branch: str = ""
    head_hash: str = ""
    auf_main: list[Commit] = field(default_factory=list)
    branches: list[Branch] = field(default_factory=list)
    worktrees: list[Worktree] = field(default_factory=list)
    stashes: int = 0
    fehler: list[str] = field(default_factory=list)

    @property
    def commits_gesamt(self) -> int:
        return len(self.auf_main) + sum(len(b.commits_heute) for b in self.branches)


def git(ordner: Path, *args: str, ok_rc: tuple[int, ...] = (0,)) -> str:
    try:
        aus = subprocess.run(["git", "-C", str(ordner), *args], capture_output=True, text=True,
                             errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise GitFehler(f"git {' '.join(args[:2])}: {e}") from e
    if aus.returncode not in ok_rc:
        raise GitFehler(f"git {' '.join(args[:2])}: rc {aus.returncode} {aus.stderr.strip()[:200]}")
    return aus.stdout


def _gleich(a: str, b: str) -> bool:
    return os.path.realpath(a) == os.path.realpath(b)


def _commits(repo: Path, tag: date, bereich: str) -> list[Commit]:
    anfang, ende = tagesgrenzen(tag)
    aus = git(repo, "log", bereich, f"--since={anfang.isoformat()}", f"--until={ende.isoformat()}",
              f"--format=%h{TRENNER}%ct{TRENNER}%s")
    commits = []
    for zeile in aus.splitlines():
        teile = zeile.split(TRENNER, 2)
        if len(teile) != 3 or not teile[1].isdigit():
            continue
        zeit = datetime.fromtimestamp(int(teile[1])).strftime("%H:%M")
        commits.append(Commit(zeit=zeit, hash=teile[0], betreff=teile[2]))
    return commits


def worktrees_lesen(repo: Path) -> list[tuple[str, str]]:
    """(Pfad, Branch) je Worktree aus `git worktree list --porcelain`; Hauptordner zuerst."""
    ergebnis: list[tuple[str, str]] = []
    pfad, branch = None, "(detached)"
    for zeile in git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if zeile.startswith("worktree "):
            pfad, branch = zeile[len("worktree "):], "(detached)"
        elif zeile.startswith("branch "):
            branch = zeile[len("branch "):]
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
        elif zeile == "" and pfad is not None:
            ergebnis.append((pfad, branch))
            pfad = None
    return ergebnis


def gruppen_lesen(ordner: Path) -> list[Gruppe]:
    """`git status --porcelain -uall -z`, gruppiert nach den ersten zwei Pfadteilen (Wurzeldateien einzeln)."""
    eintraege = git(ordner, "status", "--porcelain", "-uall", "-z").split("\0")
    gruppen: dict[str, Gruppe] = {}
    zeiten: dict[str, float] = {}
    i = 0
    while i < len(eintraege):
        eintrag = eintraege[i]
        i += 1
        if len(eintrag) < 4:
            continue
        xy, pfad = eintrag[:2], eintrag[3:]
        if xy[0] in "RC":
            i += 1  # bei Umbenennen/Kopie folgt der alte Pfad als eigener Eintrag
        teile = pfad.split("/")
        schluessel = "/".join(teile[:2]) + ("/" if len(teile) > 2 else "")
        g = gruppen.setdefault(schluessel, Gruppe(pfad=schluessel))
        if xy == "??" or "A" in xy:
            g.neu += 1
        elif "D" in xy:
            g.geloescht += 1
        else:
            g.geaendert += 1
        if len(g.beispiele) < BEISPIELE_MAX:
            g.beispiele.append(pfad)
        else:
            g.weitere += 1
        try:
            zeiten[schluessel] = max(zeiten.get(schluessel, 0.0), os.path.getmtime(ordner / pfad))
        except OSError:
            pass
    for schluessel, g in gruppen.items():
        if schluessel in zeiten:
            g.juengste = datetime.fromtimestamp(zeiten[schluessel]).strftime("%Y-%m-%d %H:%M")
    return sorted(gruppen.values(), key=lambda g: g.pfad)


def git_stand(repo: Path, tag: date) -> GitStand:
    stand = GitStand()
    try:
        stand.head_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        stand.head_hash = git(repo, "rev-parse", "--short", "HEAD").strip()
    except GitFehler as e:
        stand.fehler.append(str(e))
        return stand
    try:
        origin_da = bool(git(repo, "rev-parse", "--verify", "-q", "origin/main", ok_rc=(0, 1)).strip())
    except GitFehler as e:
        stand.fehler.append(str(e))
        origin_da = False
    if origin_da:
        try:
            stand.auf_main = _commits(repo, tag, "origin/main")
        except GitFehler as e:
            stand.fehler.append(str(e))
    worktrees: list[tuple[str, str]] = []
    try:
        worktrees = worktrees_lesen(repo)
    except GitFehler as e:
        stand.fehler.append(str(e))
    wt_je_branch = {b: p for p, b in worktrees if not _gleich(p, str(repo))}
    try:
        for zeile in git(repo, "for-each-ref", "refs/heads", "--format=%(refname:short)\t%(committerdate:unix)").splitlines():
            name, _, unix = zeile.partition("\t")
            if not name:
                continue
            letzter = datetime.fromtimestamp(int(unix)).strftime("%Y-%m-%d") if unix.strip().isdigit() else ""
            vor = hinter = None
            if origin_da:
                zaehler = git(repo, "rev-list", "--left-right", "--count", f"origin/main...{name}").split()
                if len(zaehler) == 2:
                    hinter, vor = int(zaehler[0]), int(zaehler[1])
                commits = _commits(repo, tag, f"origin/main..{name}")
            else:
                commits = _commits(repo, tag, name)
            stand.branches.append(Branch(name=name, vor=vor, hinter=hinter, letzter=letzter,
                                         worktree=wt_je_branch.get(name), commits_heute=commits))
    except GitFehler as e:
        stand.fehler.append(str(e))
    for pfad, branch in worktrees:
        try:
            gruppen = gruppen_lesen(Path(pfad))
        except GitFehler as e:
            stand.fehler.append(f"Worktree {pfad}: {e}")
            continue
        stand.worktrees.append(Worktree(pfad=pfad, branch=branch, ist_haupt=_gleich(pfad, str(repo)), gruppen=gruppen))
    try:
        stand.stashes = len(git(repo, "stash", "list").splitlines())
    except GitFehler as e:
        stand.fehler.append(str(e))
    return stand


def sicherung(repo: Path, mac: str, jetzt: datetime) -> str:
    """Patch aller Worktrees: `git diff HEAD` plus je unversionierter Textdatei (≤ 1 MB, kein NUL in den ersten 8 KB)
    ein `git diff --no-index`. Gesamt höchstens 5 MB, danach nur noch Namen. Hauptordner zuerst."""
    zeilen = [f"# Sicherung {mac} {jetzt.strftime('%Y-%m-%d %H:%M')}"]
    try:
        worktrees = worktrees_lesen(repo)
    except GitFehler as e:
        return "\n".join(zeilen + [f"# Fehler: {e}"]) + "\n"
    worktrees.sort(key=lambda pb: not _gleich(pb[0], str(repo)))
    groesse = 0
    abgebrochen = False
    aenderungen = False
    for pfad, branch in worktrees:
        ordner = Path(pfad)
        teile: list[str] = []
        try:
            diff = git(ordner, "diff", "HEAD", "--", ".")
        except GitFehler:
            diff = ""
        if diff.strip():
            teile.append(diff)
            groesse += len(diff.encode("utf-8", "replace"))
        try:
            neue = [n for n in git(ordner, "ls-files", "--others", "--exclude-standard", "-z").split("\0") if n]
        except GitFehler:
            neue = []
        for name in neue:
            datei = ordner / name
            try:
                gross = datei.stat().st_size > PATCH_DATEI_MAX
                with open(datei, "rb") as fh:
                    binaer = b"\0" in fh.read(8192)
            except OSError:
                continue
            if gross or binaer:
                teile.append(f"# nicht gesichert (groß oder binär): {name}\n")
                continue
            if groesse > PATCH_GESAMT_MAX:
                if not abgebrochen:
                    abgebrochen = True
                    teile.append("# Abbruch: 5 MB erreicht — weitere Dateien nur als Namen\n")
                teile.append(f"# nicht gesichert (Abbruch): {name}\n")
                continue
            try:
                d = git(ordner, "diff", "--no-index", "--", "/dev/null", name, ok_rc=(0, 1))
            except GitFehler as e:
                teile.append(f"# Fehler bei {name}: {e}\n")
                continue
            teile.append(d)
            groesse += len(d.encode("utf-8", "replace"))
        if teile:
            aenderungen = True
            zeilen.append(f"# Worktree: {pfad} ({branch})")
            zeilen.extend(t.rstrip("\n") for t in teile)
    if not aenderungen:
        zeilen.append("# keine unversionierten Änderungen")
    return "\n".join(zeilen) + "\n"
