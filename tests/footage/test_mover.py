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


def test_moves_sony_style_sidecar(tmp_path):
    """Sony-Sidecar C0001M01.XML wird neben dem verschobenen Clip abgelegt."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "C0001.MP4"
    _clip(src)
    (src_dir / "C0001M01.XML").write_bytes(b"<meta/>")
    dst = tmp_path / "sortiert" / "C0001.MP4"
    execute_move(Move(str(src), str(dst)))
    assert dst.exists() and not src.exists()
    assert (dst.parent / "C0001M01.XML").exists()
    assert not (src_dir / "C0001M01.XML").exists()


def test_never_overwrites_existing_sidecar_target(tmp_path):
    """Wenn Sidecar-Ziel bereits existiert, darf nichts verschoben werden."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = src_dir / "x.mp4"
    _clip(src)
    sc_src = src_dir / "xM01.XML"
    sc_src.write_bytes(b"<sc/>")
    dst_dir = tmp_path / "sortiert"
    dst_dir.mkdir()
    dst = dst_dir / "x.mp4"
    # Sidecar-Ziel bereits belegt
    (dst_dir / "xM01.XML").write_bytes(b"<existing/>")
    with pytest.raises(FileExistsError):
        execute_move(Move(str(src), str(dst)))
    # Quelle und Sidecar-Quelle müssen unangetastet sein
    assert src.exists()
    assert sc_src.exists()


def test_execute_plan_logs_and_undo_restores(tmp_path):
    src = tmp_path / "footage" / "clip.mp4"; src.parent.mkdir(); _clip(src)
    (tmp_path / "footage" / "clip.xml").write_bytes(b"<m/>")
    dst = tmp_path / "sortiert" / "V1" / "clip.mp4"
    log = tmp_path / "move_log.jsonl"
    execute_plan(MovePlan(moves=[Move(str(src), str(dst))]), log, discovered_srcs=[str(src)])
    assert dst.exists() and not src.exists()
    assert len(log.read_text().strip().splitlines()) == 1
    undo(log)
    assert src.exists() and not dst.exists()
    assert (src.parent / "clip.xml").exists()


def test_execute_plan_refuses_incomplete_manifest(tmp_path):
    footage = tmp_path / "footage"
    footage.mkdir()
    a = footage / "a.mp4"; _clip(a)
    b = footage / "b.mp4"; _clip(b)
    dst_a = tmp_path / "sortiert" / "a.mp4"
    plan = MovePlan(moves=[Move(str(a), str(dst_a))])
    log = tmp_path / "move_log.jsonl"
    with pytest.raises(ValueError):
        execute_plan(plan, log, discovered_srcs=[str(a), str(b)])
    # a.mp4 must NOT have been moved
    assert a.exists()
    assert not dst_a.exists()
    # no log file content written
    assert not log.exists() or log.read_text().strip() == ""
