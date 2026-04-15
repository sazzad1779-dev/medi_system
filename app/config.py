import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Prescription Extraction System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    
    # File storage
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./tmp"
    MAX_FILE_SIZE_MB: int = 10

    # VLM service
    VLM_PROVIDER: str = "local" # local, gemini, dashscope, openai
    VLLM_BASE_URL: str = "http://localhost:8001/v1"
    VLLM_MODEL_NAME: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    VLLM_API_KEY: Optional[str] = None
    VLLM_TIMEOUT_SECONDS: int = 60
    VLLM_MAX_TOKENS: int = 2000
    VLLM_TEMPERATURE: float = 0.0

    # Cloud fallback
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    CLOUD_FALLBACK_ENABLED: bool = False

    # Embedding Service
    EMBEDDING_PROVIDER: str = "local"  # local, gemini, jina
    GEMINI_API_KEY: Optional[str] = None
    JINA_API_KEY: Optional[str] = None
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 3072

    # Confidence thresholds
    CLOUD_FALLBACK_THRESHOLD: float = 0.70
    HUMAN_REVIEW_THRESHOLD: float = 0.60
    DOCTOR_MATCH_MIN_CONFIDENCE: float = 0.65
    MEDICINE_MATCH_MIN_CONFIDENCE: float = 0.75

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
