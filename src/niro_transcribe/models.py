from __future__ import annotations

from dataclasses import dataclass, field
from .timefmt import fmt_time


@dataclass
class Word:
    text: str
    start: float
    end: float
    speaker: str | None = None

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end, "speaker": self.speaker}

    @classmethod
    def from_dict(cls, d: dict) -> "Word":
        return cls(text=d["text"], start=d["start"], end=d["end"], speaker=d.get("speaker"))


@dataclass
class Transcript:
    source_file: str
    engine: str
    text: str
    words: list[Word] = field(default_factory=list)
    language: str = "de"

    def duration(self) -> float:
        return self.words[-1].end if self.words else 0.0

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "engine": self.engine,
            "text": self.text,
            "words": [w.to_dict() for w in self.words],
            "language": self.language,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Transcript":
        return cls(
            source_file=d["source_file"],
            engine=d["engine"],
            text=d["text"],
            words=[Word.from_dict(w) for w in d.get("words", [])],
            language=d.get("language", "de"),
        )


@dataclass
class InterviewMeta:
    quelldatei: str
    typ: str
    bereich: str
    name: str


@dataclass
class Statement:
    id: str
    quelldatei: str
    person: str
    bereich: str
    von: float
    bis: float
    text: str
    thema: str

    def von_bis(self) -> str:
        return f"{fmt_time(self.von)}–{fmt_time(self.bis)}"

    def to_dict(self) -> dict:
        return {
            "id": self.id, "quelldatei": self.quelldatei, "person": self.person,
            "bereich": self.bereich, "von": self.von, "bis": self.bis,
            "text": self.text, "thema": self.thema,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Statement":
        return cls(
            id=d["id"], quelldatei=d["quelldatei"], person=d["person"],
            bereich=d["bereich"], von=d["von"], bis=d["bis"],
            text=d["text"], thema=d["thema"],
        )


@dataclass
class VideoBrief:
    titel: str
    fokus: str
    person: str
    ziel_laenge_sek: int | None = None
    dramaturgie: str | None = None
    tonalitaet: str | None = None


@dataclass
class GlobalConfig:
    wiederverwendung: str = "exklusiv"
    anzahl_videos: int | None = None


@dataclass
class SelectedStatement:
    statement: Statement
    begruendung: str
    position: int


@dataclass
class VideoPlan:
    titel: str
    framework: str
    framework_begruendung: str
    geschaetzte_laenge_sek: int
    statements: list[SelectedStatement]
    roter_faden: str
