# core/utils/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..exceptions.agent_errors import LLMCommunicationError
from .logger import agent_logger

def log_retry_attempt(retry_state):
    """Hàm in ra thông báo mỗi khi hệ thống phải thử lại."""
    agent_logger.warning(
        f"⚠️ Đang thử lại lần {retry_state.attempt_number} do lỗi: {retry_state.outcome.exception()}"
    )

def llm_retry():
    """
    Decorator chuẩn công nghiệp để bọc các hàm gọi OpenAI.
    - Thử tối đa 4 lần.
    - Thời gian chờ tăng dần theo lũy thừa: 2s -> 4s -> 8s.
    """
    return retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception), # Bắt mọi lỗi Exception từ thư viện OpenAI
        before_sleep=log_retry_attempt,
        reraise=True # Vẫn văng lỗi nếu thử 4 lần đều thất bại
    )