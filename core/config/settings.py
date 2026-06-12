# core/config/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..exceptions.agent_errors import SystemConfigError


class Settings(BaseSettings):
    # --- 1. Local dataset ---
    DATA_DIR: str = Field(default="data", description="Folder containing local resource files")
    DATA_DUMP_PATH: str = Field(default="data/dump.json", description="Local task dump JSON")
    LOCAL_SUBMISSIONS_PATH: str = Field(
        default="logs/local_submissions.jsonl",
        description="Where local workflow submissions are written",
    )
    LOCAL_SKIP_MISSING_TASKS: bool = Field(
        default=True,
        description="Skip tasks whose resource files are not present locally",
    )

    # --- 2. Gemini ---
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL_NAME: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model used by agents",
    )

    # --- 3. Agent temperatures ---
    TEMP_ROUTER: float = Field(default=0.0, description="Router temperature")
    TEMP_EXTRACTOR: float = Field(default=0.1, description="Extractor temperature")
    TEMP_SYNTHESIZER: float = Field(default=0.3, description="Synthesizer temperature")

    # --- 4. System ---
    MAX_RETRIES: int = Field(default=3, description="Maximum API retries")
    MAX_TOKENS_PER_CHUNK: int = Field(default=4000, description="Chunk token limit")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


try:
    settings = Settings()
except Exception as e:
    raise SystemConfigError(f"Environment configuration error: {e}")
