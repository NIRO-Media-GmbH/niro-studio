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
