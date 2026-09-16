"""Charge (projects/<Kunde>/<Projekt>/<Charge>) öffnen, Config laden, Schreibbereiche absichern."""
from __future__ import annotations

import datetime as _dt
import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

TOOL_ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_FILE = TOOL_ROOT / "defaults.yaml"


class AutoCutError(Exception):
    """Fehler mit deutscher, handlungsleitender Meldung."""


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def map_path(path: str | Path, path_map: dict | None) -> str:
    """Pfad über die längste passende Präfix-Zuordnung umschreiben (Ordnergrenze, NFC-normalisiert); sonst unverändert.

    Schlüssel = Präfix in den Arbeitsdateien (z. B. NAS), Wert = Präfix, unter dem die Dateien jetzt liegen (z. B. SSD).
    """
    s = unicodedata.normalize("NFC", str(path))
    best: tuple[str, str] | None = None
    for src, dst in (path_map or {}).items():
        a = unicodedata.normalize("NFC", str(src)).rstrip("/")
        if not a:
            continue
        if s == a or s.startswith(a + "/"):
            if best is None or len(a) > len(best[0]):
                best = (a, unicodedata.normalize("NFC", str(dst)).rstrip("/"))
    if best is None:
        return str(path)
    return best[1] + s[len(best[0]):]


def load_config(charge_root: str | Path) -> dict:
    cfg = yaml.safe_load(DEFAULTS_FILE.read_text(encoding="utf-8")) or {}
    local = Path(charge_root) / "_intern" / "autocut" / "config.yaml"
    if local.exists():
        cfg = _deep_merge(cfg, yaml.safe_load(local.read_text(encoding="utf-8")) or {})
    return cfg


@dataclass
class Charge:
    root: Path
    intern: Path
    autocut: Path
    work: Path
    ergebnisse: Path
    plaene: Path
    protokoll: Path
    config: dict = field(default_factory=dict)
    zusatz_schreibbereiche: tuple[Path, ...] = ()

    @classmethod
    def open(cls, root: str | Path) -> "Charge":
        root = Path(root).expanduser().resolve()
        plaene = root / "Ergebnisse" / "O-Ton-Pläne"
        if not plaene.is_dir():
            raise AutoCutError(
                f"Keine Charge gefunden: {root}\nErwartet wird der Ordner Ergebnisse/O-Ton-Pläne "
                f"mit einem Cutter-Plan (video-N-*.md). Erst den Schnittplan-Workflow ausführen.")
        intern = root / "_intern"
        if not (intern / "utterances.json").exists():
            raise AutoCutError(f"{intern / 'utterances.json'} fehlt — bitte zuerst "
                               f"tools/transcribe/scripts/build_utterances.py für diese Charge ausführen.")
        ch = cls(root=root, intern=intern, autocut=intern / "autocut", work=intern / "autocut" / "work",
                 ergebnisse=root / "Ergebnisse" / "Rohschnitt", plaene=plaene, protokoll=root / "Protokoll.md",
                 config=load_config(root))
        for d in (ch.autocut, ch.work, ch.ergebnisse):
            d.mkdir(parents=True, exist_ok=True)
        return ch

    @classmethod
    def open_basis(cls, root: str | Path) -> "Charge":
        """Leichte Charge für Replay und Bau-Readback: keine Schnittplan-Daten nötig (auch Hand-Chargen).

        Der Ordner muss unter projects/<Kunde>/<Projekt>/ liegen. Schreibbereiche: _intern/autocut/**,
        Ergebnisse/Rohschnitt/**, _intern/replay/**, Material/Feedback/** und das Protokoll. Legt nichts an."""
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise AutoCutError(f"Chargen-Ordner nicht gefunden: {root}")
        if len(root.parents) < 3 or root.parents[2].name != "projects":
            raise AutoCutError(f"{root} liegt nicht unter projects/<Kunde>/<Projekt>/<Charge> — Chargen-Ordner angeben.")
        intern = root / "_intern"
        return cls(root=root, intern=intern, autocut=intern / "autocut", work=intern / "autocut" / "work",
                   ergebnisse=root / "Ergebnisse" / "Rohschnitt", plaene=root / "Ergebnisse" / "O-Ton-Pläne",
                   protokoll=root / "Protokoll.md", config=load_config(root),
                   zusatz_schreibbereiche=(intern / "replay", root / "Material" / "Feedback"))

    @property
    def kunde(self) -> str:
        return self.root.parents[1].name

    @property
    def projekt(self) -> str:
        return self.root.parent.name

    # --- Schreibschutz -------------------------------------------------
    def assert_writable(self, path: str | Path) -> None:
        p = Path(path).resolve()
        allowed = (self.autocut.resolve(), self.ergebnisse.resolve(), *(z.resolve() for z in self.zusatz_schreibbereiche))
        if p == self.protokoll.resolve():
            return
        if not any(str(p).startswith(str(a) + "/") or p == a for a in allowed):
            raise AutoCutError(f"Schreiben verweigert: {p}\nAutoCut schreibt nur unter "
                               + ", ".join(str(a) for a in allowed) + " sowie ans Protokoll.")

    def map_path(self, path: str | Path) -> str:
        """Zugriffspfad laut ``path_map`` der Config (Arbeitsdateien behalten die Originalpfade)."""
        pm = self.config.get("path_map")
        valid = pm is None or (isinstance(pm, dict) and all(isinstance(v, str) and v.strip() for v in pm.values()))
        if not valid:
            raise AutoCutError("path_map in config.yaml muss ein Mapping Präfix → Präfix aus Zeichenketten sein "
                               "(kein leerer Wert).")
        return map_path(path, pm or {})

    # --- Eingaben ------------------------------------------------------
    def plan_files(self) -> list[Path]:
        return sorted(p for p in self.plaene.glob("video-*.md") if p.is_file())

    def resolve_plan(self, name: str | None) -> Path:
        plans = self.plan_files()
        if name:
            for p in plans:
                if p.name == name or p.stem == name:
                    return p
            raise AutoCutError(f"Plan '{name}' nicht gefunden in {self.plaene}. Vorhanden: "
                               + ", ".join(p.name for p in plans))
        if len(plans) == 1:
            return plans[0]
        if not plans:
            raise AutoCutError(f"Kein Cutter-Plan (video-*.md) in {self.plaene}.")
        raise AutoCutError("Mehrere Pläne vorhanden, bitte mit --video wählen: "
                           + ", ".join(p.name for p in plans))

    def load_index(self) -> list[dict]:
        p = self.intern / "transcripts_index.json"
        if not p.exists():
            raise AutoCutError(f"{p} fehlt — Transkript-Index der Charge nicht vorhanden.")
        return json.loads(p.read_text(encoding="utf-8"))

    def load_utterances(self) -> list[dict]:
        return json.loads((self.intern / "utterances.json").read_text(encoding="utf-8"))

    def cache_transcript(self, fingerprint: str) -> dict | None:
        p = self.intern / "cache" / f"{fingerprint}.scribe.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    # --- Arbeitsdateien -------------------------------------------------
    def read_json(self, name: str) -> Any | None:
        p = self.autocut / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def write_json(self, name: str, data: Any) -> Path:
        p = self.autocut / name
        self.assert_writable(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return p


def letzte_timeline(ch: Charge) -> str:
    """Schlüssel ``timeline`` der zuletzt geschriebenen Datei aus feinschnitt.json, finalize.json (ok), build.json."""
    kandidaten = []
    for datei in ("feinschnitt.json", "finalize.json", "build.json"):
        d = ch.read_json(datei)
        if not isinstance(d, dict) or not d.get("timeline"):
            continue
        if datei == "finalize.json" and d.get("status") != "ok":
            continue
        kandidaten.append(((ch.autocut / datei).stat().st_mtime, str(d["timeline"])))
    if not kandidaten:
        raise AutoCutError(f"Keine gebaute AutoCut-Timeline in {ch.autocut} (feinschnitt.json, finalize.json, "
                           f"build.json) — --timeline angeben.")
    return max(kandidaten)[1]


def append_protokoll(charge: Charge, titel: str, zeilen: list[str]) -> None:
    charge.assert_writable(charge.protokoll)
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = [f"\n## {stamp} — AutoCut: {titel}\n"] + [f"- {z}" for z in zeilen] + [""]
    existing = charge.protokoll.read_text(encoding="utf-8") if charge.protokoll.exists() else "# Protokoll\n"
    charge.protokoll.write_text(existing.rstrip("\n") + "\n" + "\n".join(block), encoding="utf-8")
