from __future__ import annotations

from .models import Statement, Transcript


def verify_statement(stmt: Statement, transcript: Transcript, *, min_overlap_words: int = 1) -> list[str]:
    problems: list[str] = []
    if stmt.von < 0:
        problems.append(f"von ({stmt.von}) ist negativ")
    if stmt.von >= stmt.bis:
        problems.append(f"von ({stmt.von}) liegt nicht vor bis ({stmt.bis})")
    duration = transcript.duration()
    if stmt.bis > duration + 0.5:
        problems.append(f"bis ({stmt.bis}) überschreitet die Transkript-Dauer ({duration})")

    overlap = 0
    for w in transcript.words:
        mid = (w.start + w.end) / 2
        if stmt.von <= mid <= stmt.bis:
            overlap += 1
    if overlap < min_overlap_words:
        if overlap == 0:
            problems.append("kein Transkript-Wort liegt im Intervall [von, bis]")
        else:
            problems.append(
                f"nur {overlap} Transkript-Wort(e) im Intervall [von, bis], "
                f"mindestens {min_overlap_words} erwartet"
            )

    return problems
