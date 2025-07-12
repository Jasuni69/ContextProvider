from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str = ""
    secret_key: str
    chroma_persist_directory: str = "./chroma_db"
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = ["csv", "txt", "pdf"]
    
    class Config:
        env_file = ".env"


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_directory, exist_ok=True) 