from niro_transcribe.cache import file_hash, TranscriptCache


def test_file_hash_stable(tmp_path):
    f = tmp_path / "a.wav"
    f.write_bytes(b"audio-bytes")
    h1 = file_hash(f)
    h2 = file_hash(f)
    assert h1 == h2 and len(h1) == 64


def test_cache_roundtrip(tmp_path):
    cache = TranscriptCache(tmp_path / "cache")
    assert cache.load("hash1", "scribe") is None
    cache.save("hash1", "scribe", {"text": "hallo"})
    assert cache.load("hash1", "scribe") == {"text": "hallo"}
    # andere Engine -> getrennt
    assert cache.load("hash1", "whisper") is None
