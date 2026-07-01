from __future__ import annotations

from .models import VideoPlan, InterviewMeta, Statement
from .timefmt import fmt_time


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_video_plan(plan: VideoPlan) -> str:
    lines: list[str] = []
    lines.append(f"# {plan.titel}\n")
    lines.append(
        f"*Framework: {plan.framework} — {plan.framework_begruendung} · "
        f"geschätzte Länge: {fmt_time(plan.geschaetzte_laenge_sek)}*\n"
    )
    lines.append("| # | Person | Bereich | Quelldatei | von–bis | Wortlaut | Warum hier |")
    lines.append("|---|--------|---------|------------|---------|----------|------------|")
    for sel in sorted(plan.statements, key=lambda s: s.position):
        s = sel.statement
        lines.append(
            f"| {sel.position} | {_md_escape(s.person)} | {_md_escape(s.bereich)} | "
            f"`{_md_escape(s.quelldatei)}` | {s.von_bis()} | {_md_escape(s.text)} | "
            f"{_md_escape(sel.begruendung)} |"
        )
    lines.append("")
    lines.append("## Roter Faden\n")
    lines.append(plan.roter_faden)
    lines.append("")
    return "\n".join(lines)


def render_overview(
    plans: list[VideoPlan], metas: list[InterviewMeta], unused: list[Statement]
) -> str:
    lines: list[str] = []
    lines.append("# Gesamt-Übersicht\n")

    lines.append("## Erkannte Datei-Interpretationen\n")
    lines.append("| Quelldatei | Typ | Bereich | Name |")
    lines.append("|------------|-----|---------|------|")
    for m in metas:
        lines.append(
            f"| `{_md_escape(m.quelldatei)}` | {_md_escape(m.typ)} | "
            f"{_md_escape(m.bereich)} | {_md_escape(m.name)} |"
        )
    lines.append("")

    lines.append("## Personen je Video\n")
    for p in plans:
        personen = sorted({sel.statement.person for sel in p.statements})
        lines.append(f"- **{p.titel}**: {', '.join(personen)}")
    lines.append("")

    lines.append("## Ungenutzte starke Aussagen\n")
    if not unused:
        lines.append("_keine_")
    for s in unused:
        lines.append(f"- `{_md_escape(s.quelldatei)}` {s.von_bis()} — {_md_escape(s.text)}")
    lines.append("")
    return "\n".join(lines)
