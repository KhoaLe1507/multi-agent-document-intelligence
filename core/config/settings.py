# core/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from ..exceptions.agent_errors import SystemConfigError

class Settings(BaseSettings):
    # --- 1. Cấu hình Server Cuộc Thi ---
    COMPETITION_API_KEY: str = Field(..., description="API Key của hệ thống thi")
    BASE_URL: str = Field(..., description="URL của DataProvider API")
    
    # --- 2. Cấu hình OpenAI ---
    OPENAI_API_KEY: str = Field(..., description="API Key của OpenAI")
    GPT_MODEL_NAME: str = Field(default="gpt-4o-2024-08-06", description="Phiên bản model 4o chuẩn nhất hiện tại")
    
    # --- 3. Cấu hình "Nhiệt độ" (Temperature) cho từng Agent ---
    TEMP_ROUTER: float = Field(default=0.0, description="Router cần tính logic tuyệt đối")
    TEMP_EXTRACTOR: float = Field(default=0.1, description="Extractor cần bám sát văn bản, ít ảo giác")
    TEMP_SYNTHESIZER: float = Field(default=0.3, description="Synthesizer cần chút linh hoạt để viết văn mượt mà")

    # --- 4. Cấu hình Hệ thống ---
    MAX_RETRIES: int = Field(default=3, description="Số lần thử lại tối đa khi API sập")
    MAX_TOKENS_PER_CHUNK: int = Field(default=4000, description="Giới hạn token cho mỗi mảnh dữ liệu")

    # Load từ file .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

try:
    # Khởi tạo instance duy nhất (Singleton pattern) để dùng chung toàn project
    settings = Settings()
except Exception as e:
    raise SystemConfigError(f"❌ Lỗi cấu hình môi trường: Bỏ quên biến nào trong file .env rồi? Chi tiết: {e}")