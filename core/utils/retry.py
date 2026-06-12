# core/utils/retry.py
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .logger import agent_logger


def log_retry_attempt(retry_state):
    agent_logger.warning(
        f"Dang thu lai lan {retry_state.attempt_number} do loi: {retry_state.outcome.exception()}"
    )


def llm_retry():
    """Retry wrapper for LLM calls."""
    return retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=log_retry_attempt,
        reraise=True,
    )
