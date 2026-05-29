from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    llm_temperature: float
    llm_timeout: int
    llm_max_input_chars: int

    def is_ai_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_base_url and self.openai_model)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        openai_api_key=(os.getenv("OPENAI_API_KEY") or "").strip(),
        openai_base_url=(os.getenv("OPENAI_BASE_URL") or "").strip(),
        openai_model=(os.getenv("OPENAI_MODEL") or "").strip(),
        llm_temperature=_get_float("LLM_TEMPERATURE", 0.2),
        llm_timeout=_get_int("LLM_TIMEOUT", 30),
        llm_max_input_chars=_get_int("LLM_MAX_INPUT_CHARS", 20000),
    )
