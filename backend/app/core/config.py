from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = 'Nexus AI'
    DEBUG: bool = True
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ANTHROPIC_API_KEY: str
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    CHROMA_DIR: str = "./chroma_data"
    WHISPER_MODEL :str = "base"
    
    class Config:
        env_file = '.env'
        
@lru_cache()
def get_settings() -> Settings:
    return Settings()
    