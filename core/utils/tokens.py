# core/utils/tokens.py
from ..config.settings import settings
from .logger import agent_logger


def count_tokens(text: str, model: str = settings.GEMINI_MODEL_NAME) -> int:
    """Estimate token count for Gemini-oriented local chunking."""
    return max(1, len(text) // 4)


def truncate_text(text: str, max_tokens: int = settings.MAX_TOKENS_PER_CHUNK) -> str:
    """Trim text using the same approximate Gemini token heuristic."""
    estimated_tokens = count_tokens(text)

    if estimated_tokens <= max_tokens:
        return text

    agent_logger.warning(
        f"Van ban qua dai (~{estimated_tokens} tokens). Dang cat xuong con ~{max_tokens} tokens."
    )
    return text[: max_tokens * 4]
