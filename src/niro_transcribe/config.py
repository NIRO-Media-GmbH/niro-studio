from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    elevenlabs_api_key: str
    whisper_model: str = "large-v3"

    @classmethod
    def load(cls, env: dict | None = None) -> "Config":
        env = env if env is not None else dict(os.environ)
        key = env.get("ELEVENLABS_API_KEY", "").strip()
        if not key:
            raise ValueError("ELEVENLABS_API_KEY fehlt (siehe .env.example)")
        return cls(
            elevenlabs_api_key=key,
            whisper_model=env.get("NIRO_WHISPER_MODEL", "large-v3").strip() or "large-v3",
        )
