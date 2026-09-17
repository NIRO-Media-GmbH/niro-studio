"""Tagesstand eines Macs: Hinweise (Spec 2.5) und Markdown mit festen Überschriften (Spec 2.7)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from chargen_stand import ChargenStand
from gedaechtnis_stand import Notiz
from git_stand import Branch, GitStand
from sitzungen_stand import Sitzung, SitzungenStand

VIELE_FEHLER_AB = 5


@dataclass
class Tagesstand:
    mac: str
    tag: date
    stand: datetime
    repo: str
    git: GitStand
    chargen: ChargenStand
    sitzungen: SitzungenStand
    notizen: list[Notiz]
    fehler: list[str] = field(default_factory=list)


def hinweise(t: Tagesstand) -> list[str]:
    h = []
    mit_protokoll = set(t.chargen.je_charge_alle)
    for s in t.sitzungen.sitzungen:
        for c in s.chargen:
            if c not in mit_protokoll:
                h.append(f"Protokoll fehlt: {c} — Sitzung „{s.titel}“ ({s.von}–{s.bis})")
    for s in t.sitzungen.sitzungen:
        if s.schluss_offen:
            h.append(f"Ohne Schlussbericht: „{s.titel}“ ({s.von}–{s.bis})")
    for s in t.sitzungen.sitzungen:
        if s.fehler_anzahl >= VIELE_FEHLER_AB:
            h.append(f"Viele Tool-Fehler: „{s.titel}“ ({s.fehler_anzahl})")
    for b in t.git.branches:
        if b.vor:
            h.append(f"Ungepusht: {b.name} (+{b.vor})")
    for w in t.git.worktrees:
        if not w.ist_haupt and w.gruppen:
            h.append(f"Worktree mit Änderungen: {w.pfad} ({w.branch})")
    return h


def _abschnitt(z: list[str], titel: str, zeilen: list[str]) -> None:
    z.append(titel)
    z.extend(zeilen if zeilen else ["- keine"])


def _vorsprung(b: Branch) -> str:
    return "ohne origin/main" if b.vor is None else f"+{b.vor} / −{b.hinter}"


def _branchzusatz(b: Branch) -> str:
    return f", Worktree {b.worktree}" if b.worktree else ""


def _anfuehren(text: str) -> str:
    return f"„{text}“"


def _mit_rest(beispiele: list[str], rest: int) -> str:
    return ", ".join(beispiele) + (f" (+{rest})" if rest > 0 else "")


def _sitzung(s: Sitzung) -> list[str]:
    n_auftraege = len(s.auftraege) + s.weitere_auftraege
    z = [f"### {s.von}–{s.bis} · {s.titel} · {s.branch or '–'} · {n_auftraege} Aufträge · {s.fehler_anzahl} Tool-Fehler",
         f"- Ordner: {s.ordner or '–'} · Sitzung {s.kennung}"]
    if s.auftraege:
        auftraege = " ".join(f"{i}. {_anfuehren(a)}" for i, a in enumerate(s.auftraege, 1))
        z.append(f"- Aufträge: {auftraege}" + (f" (+{s.weitere_auftraege} weitere)" if s.weitere_auftraege else ""))
    if s.schluss_offen:
        z.append("- Schlussbericht: ohne Schlussbericht" + (f" — letzte Antwort: {_anfuehren(s.schluss)}" if s.schluss else ""))
    else:
        z.append(f"- Schlussbericht: {_anfuehren(s.schluss)}")
    if s.fehler:
        z.append("- Tool-Fehler: " + " · ".join(_anfuehren(f) for f in s.fehler))
    if s.dateien:
        z.append(f"- Dateien: {_mit_rest(s.dateien, s.weitere_dateien)}")
    if s.werkzeuge:
        z.append("- Werkzeuge: " + ", ".join(f"{name} {n}" for name, n in s.werkzeuge))
    if s.chargen:
        z.append("- Chargen: " + ", ".join(s.chargen))
    return z


def _worktree_name(pfad: str, repo: str, ist_haupt: bool) -> str:
    if ist_haupt:
        return "Hauptordner"
    return pfad[len(repo) + 1:] if pfad.startswith(repo + "/") else pfad


def rendern(t: Tagesstand) -> str:
    z: list[str] = []
    z.append(f"# Tagesstand {t.mac} — {t.tag.isoformat()}")
    z.append(f"Stand: {t.stand.strftime('%Y-%m-%d %H:%M')} · Repo {t.repo} · HEAD {t.git.head_branch} {t.git.head_hash}"
             f" · Sitzungen {len(t.sitzungen.sitzungen)} · Commits {t.git.commits_gesamt}")
    z.append("")
    z.append("## Git")
    _abschnitt(z, "### Auf main", [f"- {c.zeit} {c.hash} {c.betreff}" for c in t.git.auf_main])
    ungepusht: list[str] = []
    ohne: list[str] = []
    for b in t.git.branches:
        if b.commits_heute:
            ungepusht.append(f"- {b.name} ({_vorsprung(b)}, letzter Commit {b.letzter}{_branchzusatz(b)})")
            ungepusht.extend(f"  - {c.zeit} {c.hash} {c.betreff}" for c in b.commits_heute)
        else:
            ohne.append(f"- {b.name}: {_vorsprung(b)}, letzter Commit {b.letzter}{_branchzusatz(b)}")
    _abschnitt(z, "### Ungepusht", ungepusht)
    _abschnitt(z, "### Branches ohne Commits heute", ohne)
    for w in t.git.worktrees:
        zeilen = [f"- {g.pfad}: {g.geaendert} geändert, {g.neu} neu, {g.geloescht} gelöscht, jüngste {g.juengste or '–'}"
                  f" — {_mit_rest(g.beispiele, g.weitere)}" for g in w.gruppen]
        _abschnitt(z, f"### Unversioniert ({_worktree_name(w.pfad, t.repo, w.ist_haupt)}, {w.branch})", zeilen)
    z.append(f"Stashes: {t.git.stashes}")
    z.append("")
    z.append("## Chargen")
    eintraege = [f"- {_anfuehren(u)} — in {n} Chargen" for u, n in t.chargen.sammel]
    for charge, ueberschriften in t.chargen.je_charge.items():
        eintraege.append(f"- {charge}")
        eintraege.extend(f"  - {u}" for u in ueberschriften)
    _abschnitt(z, "### Protokoll-Einträge", eintraege)
    lieferungen = [f"- {l.charge}: {l.anzahl} Dateien — {_mit_rest(l.beispiele, l.anzahl - len(l.beispiele))}"
                   for l in t.chargen.lieferungen]
    if lieferungen:
        lieferungen.append("(Änderungszeiten bleiben beim Abgleich erhalten; Dateien können vom anderen Mac stammen.)")
    _abschnitt(z, "### Neue Dateien unter Ergebnisse/", lieferungen)
    z.append("")
    sitzungen: list[str] = []
    for s in t.sitzungen.sitzungen:
        sitzungen.extend(_sitzung(s))
    _abschnitt(z, "## Sitzungen", sitzungen)
    z.append("")
    _abschnitt(z, "## Gedächtnis", [f"- {n.name}: {n.beschreibung}" for n in t.notizen])
    z.append("")
    alle_fehler = t.fehler + t.git.fehler + t.chargen.fehler + t.sitzungen.fehler
    _abschnitt(z, "## Hinweise", [f"- {h}" for h in hinweise(t)] + [f"- Fehler: {f}" for f in alle_fehler])
    return "\n".join(z) + "\n"
