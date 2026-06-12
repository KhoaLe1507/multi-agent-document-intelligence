# core/exceptions/agent_errors.py


class BaseSystemError(Exception):
    """Base class for OCR Multi-Agents system errors."""


class SystemConfigError(BaseSystemError):
    """Raised when required runtime configuration is missing or invalid."""


class DataProviderError(BaseSystemError):
    """Raised when local data loading or submission persistence fails."""


class LLMCommunicationError(BaseSystemError):
    """Raised when the configured LLM API times out, rate-limits, or fails."""


class ParsingError(BaseSystemError):
    """Raised when a PDF, Excel, image, or text file cannot be parsed."""
