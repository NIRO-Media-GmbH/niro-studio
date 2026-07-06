# Footage-Sortierer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mechanische Bausteine bauen, mit denen Claude in der Session Roh-MP4s per transkribiertem Ton nach einem Konzept-Script sortiert und anschließend sicher (geprüft, umkehrbar) verschiebt.

**Architecture:** Neues Subpackage `src/niro_transcribe/footage/`. Claude bleibt das „Brain" (Klassifikation/Zuordnung in der Session per `prompts/sort-footage.md`); Code liefert nur die mechanischen, deterministischen Teile: Clips finden → Audio extrahieren (ffmpeg) → ElevenLabs Scribe (gecacht) → Verschiebe-Manifest validieren → geprüft verschieben mit Undo-Log. Wiederverwendet `cache.py`, `transcribe/elevenlabs.py`, `config.py`, `models.py`.

**Tech Stack:** Python ≥3.11, `requests` (vorhanden), ffmpeg (System-Binary), pytest. Keine neuen Python-Dependencies.

## Global Constraints

- **Nur ElevenLabs Scribe mit Diarisation** (`diarize=True`), **kein Whisper** — bei der Materialmenge zu langsam.
- **Kein Footage geht verloren:** nie löschen; jeder gefundene Clip tauct im Manifest genau einmal auf; Nicht-Zuordenbares → `sortiert/_nicht_zugeordnet/`.
- **Verschieben, nie umbenennen** der Dateien (Originalname bleibt); Zielstruktur entsteht über Ordner.
- **Geprüftes Verschieben:** kein Überschreiben; same-filesystem → atomares `os.rename`; cross-filesystem → copy + sha256-Vergleich + erst dann Quelle entfernen; jede Bewegung ins Log (JSONL) für Undo. **XML-Sidecar wandert mit der MP4 mit.**
- **Cache-Key = Clip-Fingerprint** (`sha256("name:size:mtime_ns")`) — billig und stabil für unveränderliches Rohmaterial (kein Voll-Hash von 300 GB).
- Sprache im Code: englische Bezeichner, knappe deutsche Fehlermeldungen — wie im bestehenden Code.
- Einziger externer Key: `ELEVENLABS_API_KEY`. ffmpeg muss im PATH sein.

---

### Task 1: Clip-Discovery

**Files:**
- Create: `src/niro_transcribe/footage/__init__.py`
- Create: `src/niro_transcribe/footage/discover.py`
- Test: `tests/footage/test_discover.py`

**Interfaces:**
- Consumes: nichts.
- Produces:
  - `class Clip` (frozen dataclass): `path: Path`, `camera: str`, `sidecar: Path | None`
  - `def discover_clips(footage_root: str | Path) -> list[Clip]` — findet rekursiv alle `.mp4`/`.mov` (case-insensitiv); `camera` = erster Pfadteil unter `footage_root`; `sidecar` = gleichnamige `.xml` (case-insensitiv) im selben Ordner, sonst `None`. Ergebnis sortiert nach `(camera, path.name)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_discover.py
from pathlib import Path
from niro_transcribe.footage.discover import discover_clips, Clip


def test_discover_finds_clips_with_camera_and_sidecar(tmp_path):
    cam_a = tmp_path / "Kamera-A FX3 1"
    cam_a.mkdir()
    (cam_a / "FX3_0001.MP4").write_bytes(b"x")
    (cam_a / "FX3_0001.XML").write_bytes(b"<meta/>")
    (cam_a / "FX3_0002.MP4").write_bytes(b"x")  # kein Sidecar
    cam_b = tmp_path / "Kamera-B A7iv"
    cam_b.mkdir()
    (cam_b / "a7_0001.mov").write_bytes(b"x")
    (cam_b / "notes.txt").write_bytes(b"ignore me")

    clips = discover_clips(tmp_path)

    assert [c.path.name for c in clips] == ["FX3_0001.MP4", "FX3_0002.MP4", "a7_0001.mov"]
    assert clips[0].camera == "Kamera-A FX3 1"
    assert clips[0].sidecar is not None and clips[0].sidecar.name == "FX3_0001.XML"
    assert clips[1].sidecar is None
    assert clips[2].camera == "Kamera-B A7iv"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && source .env && python -m pytest tests/footage/test_discover.py -v`
Expected: FAIL — `ModuleNotFoundError: niro_transcribe.footage`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/__init__.py
```

```python
# src/niro_transcribe/footage/discover.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

VIDEO_SUFFIXES = {".mp4", ".mov"}


@dataclass(frozen=True)
class Clip:
    path: Path
    camera: str
    sidecar: Path | None


def _find_sidecar(video: Path) -> Path | None:
    for cand in video.parent.iterdir():
        if cand.suffix.lower() == ".xml" and cand.stem == video.stem:
            return cand
    return None


def discover_clips(footage_root: str | Path) -> list[Clip]:
    root = Path(footage_root)
    clips: list[Clip] = []
    for video in root.rglob("*"):
        if not video.is_file() or video.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        rel = video.relative_to(root)
        camera = rel.parts[0] if len(rel.parts) > 1 else ""
        clips.append(Clip(path=video, camera=camera, sidecar=_find_sidecar(video)))
    clips.sort(key=lambda c: (c.camera, c.path.name))
    return clips
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_discover.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/__init__.py src/niro_transcribe/footage/discover.py tests/footage/test_discover.py
git commit -m "feat(footage): clip discovery with camera + sidecar detection"
```

---

### Task 2: Audio-Extraktion (ffmpeg)

**Files:**
- Create: `src/niro_transcribe/footage/audio.py`
- Test: `tests/footage/test_audio.py`

**Interfaces:**
- Consumes: nichts.
- Produces:
  - `def extract_audio(video_path: str | Path, out_dir: str | Path) -> Path` — ruft ffmpeg auf, schreibt `<out_dir>/<stem>.wav` (16 kHz, mono, PCM), gibt den Pfad zurück. Wirft `RuntimeError` mit deutscher Meldung, wenn ffmpeg fehlt oder fehlschlägt.

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_audio.py
import shutil
import subprocess
from pathlib import Path

import pytest

from niro_transcribe.footage.audio import extract_audio

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg fehlt")


def _make_tiny_mp4(path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.5",
         "-f", "lavfi", "-i", "testsrc=duration=0.5:size=128x128:rate=10",
         "-shortest", str(path)],
        check=True, capture_output=True,
    )


def test_extract_audio_produces_wav(tmp_path):
    mp4 = tmp_path / "clip.mp4"
    _make_tiny_mp4(mp4)
    out = extract_audio(mp4, tmp_path / "work")
    assert out.exists()
    assert out.suffix == ".wav"
    assert out.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_audio.py -v`
Expected: FAIL — `ImportError`/`ModuleNotFoundError` für `extract_audio`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/audio.py
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def extract_audio(video_path: str | Path, out_dir: str | Path) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg nicht gefunden (im PATH installieren, z. B. brew install ffmpeg)")
    video = Path(video_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{video.stem}.wav"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn",
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not target.exists():
        raise RuntimeError(f"ffmpeg-Audioextraktion fehlgeschlagen für {video.name}: {proc.stderr[-500:]}")
    return target
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_audio.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/audio.py tests/footage/test_audio.py
git commit -m "feat(footage): ffmpeg audio extraction to 16k mono wav"
```

---

### Task 3: Gecachte Transkription pro Clip

**Files:**
- Create: `src/niro_transcribe/footage/transcribe_clips.py`
- Test: `tests/footage/test_transcribe_clips.py`

**Interfaces:**
- Consumes: `Clip` (Task 1); `extract_audio` (Task 2); `TranscriptCache` (`cache.py`); `transcribe_scribe` (`transcribe/elevenlabs.py`); `Transcript` (`models.py`).
- Produces:
  - `def clip_fingerprint(path: str | Path) -> str` — `sha256` von `"<name>:<size>:<mtime_ns>"`.
  - `def transcribe_clip(clip: Clip, *, cache: TranscriptCache, api_key: str, work_dir: str | Path, diarize: bool = True, extractor=extract_audio, transcriber=transcribe_scribe) -> Transcript` — bei Cache-Treffer (`engine="scribe"`) direkt aus Cache; sonst Audio extrahieren, transkribieren, `source_file` auf `clip.path.name` setzen, cachen. `extractor`/`transcriber` injizierbar für Tests.

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_transcribe_clips.py
from pathlib import Path

from niro_transcribe.cache import TranscriptCache
from niro_transcribe.footage.discover import Clip
from niro_transcribe.footage.transcribe_clips import clip_fingerprint, transcribe_clip
from niro_transcribe.models import Transcript, Word


def test_fingerprint_stable_and_content_independent(tmp_path):
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"abc")
    fp1 = clip_fingerprint(f)
    fp2 = clip_fingerprint(f)
    assert fp1 == fp2 and len(fp1) == 64


def test_transcribe_clip_uses_cache_on_second_call(tmp_path):
    mp4 = tmp_path / "clip.mp4"
    mp4.write_bytes(b"video-bytes")
    clip = Clip(path=mp4, camera="Kamera-A", sidecar=None)
    cache = TranscriptCache(tmp_path / "cache")
    calls = {"extract": 0, "transcribe": 0}

    def fake_extract(video, out_dir):
        calls["extract"] += 1
        p = Path(out_dir) / "clip.wav"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"wav")
        return p

    def fake_transcribe(audio, api_key, *, diarize=True):
        calls["transcribe"] += 1
        return Transcript(source_file=Path(audio).name, engine="scribe", text="hallo welt",
                          words=[Word("hallo", 0.0, 0.4, "speaker_0")])

    t1 = transcribe_clip(clip, cache=cache, api_key="k", work_dir=tmp_path / "work",
                         extractor=fake_extract, transcriber=fake_transcribe)
    t2 = transcribe_clip(clip, cache=cache, api_key="k", work_dir=tmp_path / "work",
                         extractor=fake_extract, transcriber=fake_transcribe)

    assert t1.text == "hallo welt" and t2.text == "hallo welt"
    assert t1.source_file == "clip.mp4"  # nicht "clip.wav"
    assert calls["transcribe"] == 1  # zweiter Aufruf aus Cache
    assert calls["extract"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_transcribe_clips.py -v`
Expected: FAIL — `ModuleNotFoundError` für `transcribe_clips`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/transcribe_clips.py
from __future__ import annotations

import hashlib
from pathlib import Path

from ..cache import TranscriptCache
from ..models import Transcript
from ..transcribe.elevenlabs import transcribe_scribe
from .audio import extract_audio


def clip_fingerprint(path: str | Path) -> str:
    p = Path(path)
    st = p.stat()
    return hashlib.sha256(f"{p.name}:{st.st_size}:{st.st_mtime_ns}".encode("utf-8")).hexdigest()


def transcribe_clip(clip, *, cache: TranscriptCache, api_key: str, work_dir,
                    diarize: bool = True, extractor=extract_audio,
                    transcriber=transcribe_scribe) -> Transcript:
    fp = clip_fingerprint(clip.path)
    cached = cache.load(fp, "scribe")
    if cached is not None:
        return Transcript.from_dict(cached)
    audio = extractor(clip.path, work_dir)
    transcript = transcriber(audio, api_key, diarize=diarize)
    transcript.source_file = clip.path.name
    cache.save(fp, "scribe", transcript.to_dict())
    return transcript
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_transcribe_clips.py -v`
Expected: PASS (2 Tests)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/transcribe_clips.py tests/footage/test_transcribe_clips.py
git commit -m "feat(footage): cached per-clip Scribe transcription with fingerprint key"
```

---

### Task 4: Verschiebe-Manifest (Modell + Validierung)

**Files:**
- Create: `src/niro_transcribe/footage/move_plan.py`
- Test: `tests/footage/test_move_plan.py`

**Interfaces:**
- Consumes: nichts.
- Produces:
  - `class Move` (dataclass): `src: str`, `dst: str` (beide absolute Pfade; `dst` = voller Ziel-Dateipfad).
  - `class MovePlan` (dataclass): `moves: list[Move]`; `save(path)`, `load(path) -> MovePlan` (JSON), `validate(discovered_srcs: list[str]) -> list[str]` — gibt Problem-Strings zurück (leer = ok). Prüft: jede `discovered_src` genau einmal als `move.src`; keine unbekannte `src`; `src` eindeutig; `dst` eindeutig. Das ist die Vollständigkeits-Bilanz „jeder Clip genau einmal".

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_move_plan.py
from niro_transcribe.footage.move_plan import Move, MovePlan


def test_validate_ok_when_every_clip_mapped_once():
    discovered = ["/f/a.mp4", "/f/b.mp4"]
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/a.mp4"),
                           Move("/f/b.mp4", "/s/_nicht_zugeordnet/b.mp4")])
    assert plan.validate(discovered) == []


def test_validate_flags_missing_duplicate_and_unknown():
    discovered = ["/f/a.mp4", "/f/b.mp4"]
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/x/a.mp4"),
                           Move("/f/a.mp4", "/s/y/a.mp4"),   # duplicate src + dup name ok? dst unique
                           Move("/f/c.mp4", "/s/x/a.mp4")])  # unknown src + duplicate dst
    problems = plan.validate(discovered)
    assert any("b.mp4" in p and "fehlt" in p for p in problems)      # b nicht abgedeckt
    assert any("/f/a.mp4" in p and "mehrfach" in p for p in problems)  # a doppelt
    assert any("/f/c.mp4" in p and "unbekannt" in p for p in problems)  # c nicht discovered
    assert any("/s/x/a.mp4" in p and "Ziel" in p for p in problems)   # dst kollidiert


def test_save_and_load_roundtrip(tmp_path):
    plan = MovePlan(moves=[Move("/f/a.mp4", "/s/V1/01/a.mp4")])
    p = tmp_path / "manifest.json"
    plan.save(p)
    loaded = MovePlan.load(p)
    assert loaded.moves == plan.moves
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_move_plan.py -v`
Expected: FAIL — `ModuleNotFoundError` für `move_plan`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/move_plan.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Move:
    src: str
    dst: str


@dataclass
class MovePlan:
    moves: list[Move]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps({"moves": [asdict(m) for m in self.moves]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "MovePlan":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(moves=[Move(**m) for m in data["moves"]])

    def validate(self, discovered_srcs: list[str]) -> list[str]:
        problems: list[str] = []
        discovered = set(discovered_srcs)
        srcs = [m.src for m in self.moves]
        seen: set[str] = set()
        for s in srcs:
            if s in seen:
                problems.append(f"Quelle mehrfach im Manifest: {s}")
            seen.add(s)
            if s not in discovered:
                problems.append(f"Quelle unbekannt (nicht im Footage gefunden): {s}")
        for d in sorted(discovered - seen):
            problems.append(f"Quelle fehlt im Manifest (würde verloren gehen): {d}")
        dsts: set[str] = set()
        for m in self.moves:
            if m.dst in dsts:
                problems.append(f"Ziel kollidiert (zwei Clips auf denselben Pfad): {m.dst}")
            dsts.add(m.dst)
        return problems
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_move_plan.py -v`
Expected: PASS (3 Tests)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/move_plan.py tests/footage/test_move_plan.py
git commit -m "feat(footage): move manifest model with completeness validation"
```

---

### Task 5: Sicheres Verschieben mit Log & Undo

**Files:**
- Create: `src/niro_transcribe/footage/mover.py`
- Test: `tests/footage/test_mover.py`

**Interfaces:**
- Consumes: `Move`, `MovePlan` (Task 4); `file_hash` (`cache.py`).
- Produces:
  - `class MoveResult` (dataclass): `src: str`, `dst: str`, `method: str`, `size: int`, `sidecar_src: str | None`, `sidecar_dst: str | None`.
  - `def execute_move(move: Move, *, dry_run: bool = False, force_copy: bool = False) -> MoveResult` — prüft Quelle existiert, Ziel existiert NICHT (kein Überschreiben), legt Ziel-Ordner an; same-filesystem → `os.rename`, sonst copy2 + sha256-Vergleich + Quelle entfernen (`force_copy` erzwingt den Copy-Pfad für Tests); verschiebt XML-Sidecar mit (gleicher Stem). Gibt `MoveResult` zurück.
  - `def execute_plan(plan: MovePlan, log_path: str | Path, *, dry_run: bool = False) -> list[MoveResult]` — führt Moves aus, hängt je Move eine JSONL-Zeile ans Log; bricht bei erstem Fehler ab (nichts Halbfertiges).
  - `def undo(log_path: str | Path) -> None` — liest Log rückwärts, bewegt jedes `dst` (+ Sidecar) zurück nach `src`.

- [ ] **Step 1: Write the failing test**

```python
# tests/footage/test_mover.py
import json
from pathlib import Path

import pytest

from niro_transcribe.footage.move_plan import Move, MovePlan
from niro_transcribe.footage.mover import execute_move, execute_plan, undo


def _clip(path: Path, data=b"video"):
    path.write_bytes(data)


def test_rename_move_with_sidecar(tmp_path):
    src = tmp_path / "src" / "clip.mp4"
    src.parent.mkdir()
    _clip(src)
    (tmp_path / "src" / "clip.xml").write_bytes(b"<m/>")
    dst = tmp_path / "sortiert" / "V1" / "01" / "clip.mp4"
    res = execute_move(Move(str(src), str(dst)))
    assert dst.exists() and not src.exists()
    assert (dst.parent / "clip.xml").exists()
    assert res.method == "rename"


def test_never_overwrites_existing_target(tmp_path):
    src = tmp_path / "clip.mp4"; _clip(src)
    dst = tmp_path / "out" / "clip.mp4"; dst.parent.mkdir(); _clip(dst, b"other")
    with pytest.raises(FileExistsError):
        execute_move(Move(str(src), str(dst)))
    assert src.exists()  # Quelle unangetastet


def test_copy_path_verifies_checksum(tmp_path):
    src = tmp_path / "clip.mp4"; _clip(src, b"payload-123")
    dst = tmp_path / "out" / "clip.mp4"
    res = execute_move(Move(str(src), str(dst)), force_copy=True)
    assert dst.read_bytes() == b"payload-123" and not src.exists()
    assert res.method == "copy"


def test_execute_plan_logs_and_undo_restores(tmp_path):
    src = tmp_path / "footage" / "clip.mp4"; src.parent.mkdir(); _clip(src)
    (tmp_path / "footage" / "clip.xml").write_bytes(b"<m/>")
    dst = tmp_path / "sortiert" / "V1" / "clip.mp4"
    log = tmp_path / "move_log.jsonl"
    execute_plan(MovePlan(moves=[Move(str(src), str(dst))]), log)
    assert dst.exists() and not src.exists()
    assert len(log.read_text().strip().splitlines()) == 1
    undo(log)
    assert src.exists() and not dst.exists()
    assert (src.parent / "clip.xml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_mover.py -v`
Expected: FAIL — `ModuleNotFoundError` für `mover`

- [ ] **Step 3: Write minimal implementation**

```python
# src/niro_transcribe/footage/mover.py
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path

from ..cache import file_hash
from .move_plan import Move, MovePlan


@dataclass
class MoveResult:
    src: str
    dst: str
    method: str
    size: int
    sidecar_src: str | None
    sidecar_dst: str | None


def _sidecar(video: Path) -> Path | None:
    for cand in video.parent.iterdir() if video.parent.exists() else []:
        if cand.suffix.lower() == ".xml" and cand.stem == video.stem:
            return cand
    return None


def _existing_ancestor(p: Path) -> Path:
    p = p.parent
    while not p.exists():
        p = p.parent
    return p


def _same_filesystem(src: Path, dst: Path) -> bool:
    return os.stat(src).st_dev == os.stat(_existing_ancestor(dst)).st_dev


def _move_one(src: Path, dst: Path, *, force_copy: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(f"Ziel existiert bereits, wird nicht überschrieben: {dst}")
    if not force_copy and _same_filesystem(src, dst):
        os.rename(src, dst)
        return "rename"
    before = file_hash(src)
    shutil.copy2(src, dst)
    if file_hash(dst) != before:
        dst.unlink(missing_ok=True)
        raise RuntimeError(f"Prüfsumme nach Kopie abweichend: {src} -> {dst}")
    src.unlink()
    return "copy"


def execute_move(move: Move, *, dry_run: bool = False, force_copy: bool = False) -> MoveResult:
    src = Path(move.src)
    dst = Path(move.dst)
    if not src.exists():
        raise FileNotFoundError(f"Quelle fehlt: {src}")
    sc_src = _sidecar(src)
    sc_dst = (dst.parent / f"{dst.stem}{sc_src.suffix}") if sc_src else None
    size = src.stat().st_size
    if dry_run:
        method = "rename" if (not force_copy and _same_filesystem(src, dst)) else "copy"
        return MoveResult(str(src), str(dst), method, size,
                          str(sc_src) if sc_src else None, str(sc_dst) if sc_dst else None)
    method = _move_one(src, dst, force_copy=force_copy)
    if sc_src and sc_dst:
        _move_one(sc_src, sc_dst, force_copy=force_copy)
    return MoveResult(str(src), str(dst), method, size,
                      str(sc_src) if sc_src else None, str(sc_dst) if sc_dst else None)


def execute_plan(plan: MovePlan, log_path: str | Path, *, dry_run: bool = False) -> list[MoveResult]:
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    results: list[MoveResult] = []
    with open(log, "a", encoding="utf-8") as fh:
        for move in plan.moves:
            res = execute_move(move, dry_run=dry_run)
            results.append(res)
            if not dry_run:
                fh.write(json.dumps(asdict(res), ensure_ascii=False) + "\n")
                fh.flush()
    return results


def undo(log_path: str | Path) -> None:
    lines = Path(log_path).read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        r = json.loads(line)
        _move_one(Path(r["dst"]), Path(r["src"]), force_copy=False)
        if r.get("sidecar_dst") and r.get("sidecar_src"):
            _move_one(Path(r["sidecar_dst"]), Path(r["sidecar_src"]), force_copy=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage/test_mover.py -v`
Expected: PASS (4 Tests)

- [ ] **Step 5: Commit**

```bash
git add src/niro_transcribe/footage/mover.py tests/footage/test_mover.py
git commit -m "feat(footage): safe move with checksum, sidecar, JSONL log and undo"
```

---

### Task 6: In-Session-Prompt (das „Brain")

**Files:**
- Create: `prompts/sort-footage.md`
- Test: keiner (Doku/Prompt) — Deliverable ist der Prompt selbst.

**Interfaces:**
- Consumes: die Bausteine aus Task 1–5 (nur als Beschreibung, wie Claude sie in der Session orchestriert).
- Produces: `prompts/sort-footage.md`.

- [ ] **Step 1: Prompt schreiben**

Erstelle `prompts/sort-footage.md` mit exakt diesem Inhalt:

```markdown
# Prompt — Footage sortieren (in der Session, Claude = Brain)

Ziel: Roh-MP4s anhand des Konzept-Scripts sortieren. Zuordnung über den
transkribierten **Ton**, nicht über Dateinamen. Kein Footage geht verloren.

## Eingaben
- `footage_root` (SSD): enthält Kamera-Ordner mit MP4/MOV (+ XML-Sidecars).
- Konzept-Script (PDF/Sheet): Spalten u. a. Video-Nr, Videotitel, Szenen-Nr,
  `Sprechtext/Inhalt`. Script in strukturierte Szenen parsen:
  je Video eine geordnete Liste (Hook A/B/C, Szene 1..N) mit Soll-Sprechtext.

## Ablauf
1. `discover_clips(footage_root)` → alle Clips (mit Kamera + Sidecar).
2. Pro Clip `transcribe_clip(...)` (Scribe, Diarisation, gecacht). Ergebnis:
   Wörter mit `speaker`-Label und Zeiten.
3. **Sprecher bestimmen:** der Kameramann/Interviewer spricht auch — er zählt
   NIE. Interviewten-Sprecher pro Clip identifizieren (größter Redeanteil bzw.
   der, der die Konzept-/Antwortinhalte spricht). Nur dessen Wörter nutzen.
4. **Klassifizieren** (pro Clip):
   - **Gescripteter Satz:** Ton matcht ~wörtlich eine `Sprechtext`-Zeile, die
     als echter Sprech-Satz gedreht wurde → Ziel
     `sortiert/<Videotitel>/NN_<Szene>_<Kurztext>/<Kamera>/<Originaldatei>`.
     NN = Script-Reihenfolge (Hook A/B/C zuerst, dann Szene 1..N). Multi-Cam:
     mehrere Kameras desselben Satzes → alle in denselben Szenen-Ordner,
     nach `<Kamera>/` getrennt. Takes (Wiederholungen) → derselbe Ordner.
     Enthält ein Clip ausnahmsweise MEHRERE Sätze: Primärsatz-Regel — Clip in
     den Ordner des ersten Satzes; die weiteren Sätze mit von–bis im Plan
     vermerken. Keine Datei duplizieren.
   - **Freies Interview:** Script-Zeile ist „Frage an … Sie erzählt, dass …"
     (Antwort frei) → NICHT einer Szene zuordnen, sondern nach Person:
     `sortiert/Interviews/<Name>/<Originaldatei>`. Name aus dem Transkript
     (Selbstvorstellung / im Clip genannter Name). Kein Name → `Interviews/_ohne_Namen/`
     und im Plan markieren.
   - **B-Roll / kein O-Ton:** kein verwertbarer Interviewten-Sprech, nur
     Ambiente/Kameramann, oder „Hook C – bildlicher Einstieg ohne Text" →
     `sortiert/B-Roll/<Originaldatei>`.
   - **Unsicher:** nicht sicher zuordenbar → `sortiert/_nicht_zugeordnet/<Originaldatei>`.
5. **Zuordnungsplan** schreiben (`zuordnungsplan.md`, menschенlesbar): pro
   Video/Szene die Clips (Kamera, Take, von–bis, Match-Sicherheit), dann
   Interviews-nach-Person, B-Roll, `_nicht_zugeordnet`. Ganz oben die
   **Bilanz**: Anzahl gefundener Clips == Summe aller Ziele.
6. **Manifest** schreiben (`manifest.json`, `MovePlan`): je Clip genau ein
   `{src, dst}`. `MovePlan.validate(discovered_srcs)` MUSS `[]` liefern, bevor
   irgendetwas bewegt wird.
7. **Review-Gate:** David prüft `zuordnungsplan.md` im Chat. NICHTS wurde bewegt.
8. **Erst nach „go":** `execute_plan(plan, log_path)` (same-fs → atomarer
   rename). Danach Bilanz aus dem Log bestätigen. Bei Bedarf `undo(log_path)`.

## Regeln
- Original-Dateinamen NIE ändern. Struktur entsteht nur über Ordner.
- Im Zweifel `_nicht_zugeordnet/` statt raten. Lieber melden als verlieren.
- Nur ElevenLabs Scribe, kein Whisper.
```

- [ ] **Step 2: Commit**

```bash
git add prompts/sort-footage.md
git commit -m "docs(footage): in-session sorting prompt (the brain)"
```

---

### Task 7: Betriebs-Doku (WORKFLOW) & Setup-Hinweis

**Files:**
- Create: `WORKFLOW-Footage.md`
- Modify: `SETUP.md` (ffmpeg-Hinweis ergänzen)
- Test: keiner (Doku).

**Interfaces:**
- Consumes: alles vorige.
- Produces: Betriebsanleitung für den 3-Phasen-Lauf.

- [ ] **Step 1: WORKFLOW-Footage.md schreiben**

Erstelle `WORKFLOW-Footage.md`:

```markdown
# Workflow — Footage sortieren (pro Dreh, Claude in der Session)

Voraussetzung: `.env` (ELEVENLABS_API_KEY) geladen, ffmpeg im PATH, SSD gemountet.

Konvention: Rohmaterial auf der SSD unter `<Projekt>/01_Footage/<Kamera>/…`;
Ausgabe → `<Projekt>/sortiert/`. Arbeitsdateien (Cache, Plan, Manifest, Log,
Script-Kopie) im Repo unter `projects/<Name>/`.

1. **Finden.** `discover_clips(footage_root)` → Clip-Liste (Kamera + Sidecar).
2. **Transkribieren.** Pro Clip `transcribe_clip(...)` (Scribe + Diarisation,
   gecacht in `projects/<Name>/cache/`). Audio wird per ffmpeg extrahiert.
3. **Script lesen & zuordnen.** Nach `prompts/sort-footage.md`: Sprecher
   bestimmen (Kameramann raus), klassifizieren (gescriptet → Szene, frei →
   Person, Rest → B-Roll, unsicher → `_nicht_zugeordnet`).
4. **Plan + Manifest.** `zuordnungsplan.md` (Review) und `manifest.json`
   (`MovePlan`). `validate()` muss leer sein.
5. **Review.** David prüft `zuordnungsplan.md`. Bis hier nichts bewegt.
6. **Verschieben (nach „go").** `execute_plan(plan, log)` → `_verschiebe_log.md`
   (JSONL). Bilanz prüfen. Rückgängig via `undo(log)`.
```

- [ ] **Step 2: SETUP.md um ffmpeg ergänzen**

Füge in `SETUP.md` eine Zeile hinzu (unter die bestehenden Schritte):

```markdown
- ffmpeg installieren (für den Footage-Sortierer): `brew install ffmpeg`
```

- [ ] **Step 3: Volle Test-Suite laufen lassen**

Run: `cd "/Users/jansantos/NIRO Transcribe" && python -m pytest tests/footage -v`
Expected: PASS (alle Footage-Tests grün)

- [ ] **Step 4: Commit**

```bash
git add WORKFLOW-Footage.md SETUP.md
git commit -m "docs(footage): operating workflow and ffmpeg setup note"
```

---

## Nach der Implementierung — der echte Lauf (LohiBW Recruiting)

Kein Code-Task, sondern die Anwendung durch Claude in der Session:
- `footage_root = /Volumes/NIRO-SSD-02/Lohi Backup/01_Footage`
- Ausgabe `= /Volumes/NIRO-SSD-02/Lohi Backup/sortiert`
- Script = das LohiBW-Sheet-PDF, Arbeitsordner `projects/LohiBW Recruiting/`.
- Ablauf strikt: Phase 1 (finden+transkribieren, 135 Clips) → Plan → **Davids Review** → Phase 3 (verschieben) → Bilanz.
```
