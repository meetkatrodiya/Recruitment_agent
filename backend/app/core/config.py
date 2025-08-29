import os
from functools import lru_cache
from typing import Optional, List

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables from a .env file if present
load_dotenv()


@lru_cache(maxsize=1)
def get_openai_api_key() -> str:
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return api_key


@lru_cache(maxsize=1)
def get_async_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_openai_api_key())


@lru_cache(maxsize=1)
def get_openai_chat_model() -> str:
    return os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")


@lru_cache(maxsize=1)
def get_openai_temperature() -> float:
    try:
        return float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    except ValueError:
        return 0.1


@lru_cache(maxsize=1)
def get_allowed_origins() -> List[str]:
    raw = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()] 


@lru_cache(maxsize=1)
def get_max_parallel_tasks() -> int:
    """Maximum number of concurrent LLM tasks (for resume parsing/scoring)."""
    try:
        value = int(os.getenv("MAX_PARALLEL_TASKS", "4"))
        # Clamp to a sensible range
        if value < 1:
            return 1
        if value > 16:
            return 16
        return value
    except ValueError:
        return 4