# core/utils/tokens.py
import tiktoken
from ..config.settings import settings
from .logger import agent_logger

def count_tokens(text: str, model: str = settings.GPT_MODEL_NAME) -> int:
    """Đếm chính xác số lượng token của chuỗi văn bản đối với model đang dùng."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Nếu model quá mới, tiktoken chưa cập nhật kịp thì fallback về o200k_base của gpt-4o
        encoding = tiktoken.get_encoding("o200k_base") 
    
    return len(encoding.encode(text))

def truncate_text(text: str, max_tokens: int = settings.MAX_TOKENS_PER_CHUNK) -> str:
    """Cắt xén văn bản nếu nó vượt quá giới hạn token cho phép (tránh lỗi API)."""
    encoding = tiktoken.get_encoding("o200k_base")
    encoded_text = encoding.encode(text)
    
    if len(encoded_text) <= max_tokens:
        return text
        
    agent_logger.warning(f"Văn bản quá dài ({len(encoded_text)} tokens). Đang cắt xuống còn {max_tokens} tokens.")
    return encoding.decode(encoded_text[:max_tokens])