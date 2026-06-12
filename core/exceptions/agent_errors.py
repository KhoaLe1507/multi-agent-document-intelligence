# core/exceptions/agent_errors.py

class BaseSystemError(Exception):
    """Class cha cho mọi lỗi trong hệ thống OCR Multi-Agents."""
    pass

class SystemConfigError(BaseSystemError):
    """Lỗi văng ra ngay khi khởi động nếu thiếu API Key hoặc sai định dạng cấu hình."""
    pass

class DataProviderError(BaseSystemError):
    """Lỗi khi giao tiếp với nguồn dữ liệu hoặc nơi lưu submission."""
    pass

class LLMCommunicationError(BaseSystemError):
    """Lỗi khi gọi OpenAI API (Timeout, Rate Limit, hoặc API sập)."""
    pass

class ParsingError(BaseSystemError):
    """Lỗi khi không thể đọc được file PDF, Excel hoặc Ảnh."""
    pass
