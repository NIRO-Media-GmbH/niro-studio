from niro_transcribe.project import Project


def test_open_creates_dirs(tmp_path):
    proj = Project.open(tmp_path)
    assert proj.audio_dir.is_dir()
    assert proj.cache_dir.is_dir()
    assert proj.output_dir.is_dir()
    assert proj.skript_pdf == tmp_path / "skript.pdf"
    assert proj.briefs_yaml == tmp_path / "briefs.yaml"


def test_audio_files_sorted_wav_only(tmp_path):
    proj = Project.open(tmp_path)
    (proj.audio_dir / "b.wav").write_bytes(b"1")
    (proj.audio_dir / "a.WAV").write_bytes(b"1")
    (proj.audio_dir / "notes.txt").write_text("x")
    names = [p.name for p in proj.audio_files()]
    assert names == ["a.WAV", "b.wav"]
