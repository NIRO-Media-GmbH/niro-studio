import pytest
from niro_transcribe.config import Config


def test_load_reads_key_from_env():
    cfg = Config.load({"ELEVENLABS_API_KEY": "abc123"})
    assert cfg.elevenlabs_api_key == "abc123"
    assert cfg.whisper_model == "large-v3"  # Default


def test_load_custom_whisper_model():
    cfg = Config.load({"ELEVENLABS_API_KEY": "x", "NIRO_WHISPER_MODEL": "medium"})
    assert cfg.whisper_model == "medium"


def test_load_missing_key_raises():
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        Config.load({})
